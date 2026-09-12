"""Shared helpers for the lemmatisation runs.

Every run_*.py script reads text/chambers.txt, tokenises it the same way,
calls one tool, and writes analysis/lemmas-<tool>.txt in the 7-column
format of tokens-example.txt (MorphGNT-style codes):

    index form normalised pos parse form-parse lemma

Raw tool output is kept in analysis/raw/<tool>.jsonl for comparison.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

from greek_normalisation.normalise import Normaliser

ROOT = Path(__file__).resolve().parent.parent.parent
TEXT = ROOT / "text" / "chambers.txt"
ANALYSIS = ROOT / "analysis"
RAW = ANALYSIS / "raw"

# punctuation that may be attached to a token in chambers.txt
PUNCT = ".,·;()«»"
PUNCT_RE = re.compile(f"^[{re.escape(PUNCT)}]+|[{re.escape(PUNCT)}]+$")

_normaliser = Normaliser()


def strip_punct(form):
    return PUNCT_RE.sub("", form)


def normalise(form):
    """greek-normalisation output for the bare word (no punctuation)."""
    bare = strip_punct(form)
    if not bare:
        return bare
    norm, _flags = _normaliser.normalise(bare)
    return norm


def tokens():
    """Yield (index, ref, form, bare, normalised) for every token in the text."""
    i = 0
    with open(TEXT, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ref, _, body = line.partition(" ")
            for form in body.split():
                bare = strip_punct(form)
                if not bare:
                    continue  # stray punctuation
                i += 1
                yield i, ref, form, bare, normalise(form)


_EDGE_RE = re.compile(f"^([{re.escape(PUNCT)}]*)(.*?)([{re.escape(PUNCT)}]*)$")


def tagger_text(toks):
    """The line as fed to the contextual taggers: punctuation kept (it
    carries clause/sentence boundaries) but separated from the words by
    spaces, since OdyCy and Stanza otherwise leave a leading '(' or '«'
    attached and lemmatise '(μόνη' as a word."""
    parts = []
    for t in toks:
        lead, core, trail = _EDGE_RE.match(t["form"]).groups()
        parts.extend(p for p in (lead, core, trail) if p)
    return " ".join(parts)


def sentences():
    """Yield (ref, [token dicts]) one line (textpart) at a time, for tools
    that want sentence context."""
    current = None
    buf = []
    for i, ref, form, bare, norm in tokens():
        if ref != current:
            if buf:
                yield current, buf
            current, buf = ref, []
        buf.append({"index": i, "ref": ref, "form": form, "bare": bare, "norm": norm})
    if buf:
        yield current, buf


# ---------------------------------------------------------------------------
# MorphGNT-style codes

# Universal POS -> MorphGNT POS
UPOS_TO_POS = {
    "NOUN": "N-", "PROPN": "N-", "VERB": "V-", "AUX": "V-", "ADJ": "A-",
    "NUM": "A-", "DET": "RA", "PRON": "RP", "ADV": "D-", "CCONJ": "C-",
    "SCONJ": "C-", "ADP": "P-", "PART": "X-", "INTJ": "I-", "PUNCT": "--",
    "X": "--",
}
PRONTYPE_TO_POS = {"Prs": "RP", "Dem": "RD", "Rel": "RR", "Int": "RI", "Ind": "RI",
                   "Art": "RA"}

TENSE = {"Pres": "P", "Imp": "I", "Fut": "F", "Aor": "A", "Perf": "X", "Pqp": "Y",
         "FutPerf": "Z"}
VOICE = {"Act": "A", "Mid": "M", "Pass": "P", "Mid,Pass": "M", "MidPass": "M"}
MOOD = {"Ind": "I", "Imp": "D", "Sub": "S", "Opt": "O"}
VERBFORM = {"Inf": "N", "Part": "P"}
CASE = {"Nom": "N", "Gen": "G", "Dat": "D", "Acc": "A", "Voc": "V"}
NUMBER = {"Sing": "S", "Plur": "P", "Dual": "D"}
GENDER = {"Masc": "M", "Fem": "F", "Neut": "N"}
DEGREE = {"Cmp": "C", "Sup": "S"}


def ud_to_pos(upos, feats, lemma=None):
    pos = UPOS_TO_POS.get(upos, "--")
    if upos == "DET" and lemma == "ὁ":
        return "RA"  # OdyCy marks the article DET + PronType=Dem
    pt = feats.get("PronType")
    if upos in ("PRON", "DET", "ADJ") and pt in PRONTYPE_TO_POS:
        # adverbs stay D- (MorphGNT tags ὅτε, πῶς etc. as D-/C-)
        pos = PRONTYPE_TO_POS[pt]
    return pos


def ud_to_parse(upos, feats):
    """Build the 8-char MorphGNT parse code from a UD feature dict."""
    person = feats.get("Person", "-")[0] if feats.get("Person") else "-"
    tense = TENSE.get(feats.get("Tense"), "-")
    voice = VOICE.get(feats.get("Voice"), "-")
    mood = MOOD.get(feats.get("Mood"), VERBFORM.get(feats.get("VerbForm"), "-"))
    case = CASE.get(feats.get("Case"), "-")
    number = NUMBER.get(feats.get("Number"), "-")
    gender = GENDER.get(feats.get("Gender"), "-")
    degree = DEGREE.get(feats.get("Degree"), "-")
    return person + tense + voice + mood + case + number + gender + degree


def parse_feats(s):
    """'Case=Nom|Number=Sing' -> dict (also accepts a dict)."""
    if not s or s == "_":
        return {}
    if isinstance(s, dict):
        return dict(s)
    out = {}
    for kv in s.split("|"):
        k, _, v = kv.partition("=")
        out[k] = v
    return out


# ---------------------------------------------------------------------------
# output

def capitalise_like(norm, lemma):
    """The example keeps capitals on proper nouns (Ἰησοῦ) but lowercases
    sentence-initial words; the normaliser lowercases everything, so put
    the capital back when the tool's lemma is capitalised."""
    if lemma and lemma[0].isupper() and norm:
        return norm[0].upper() + norm[1:]
    return norm


def field(x):
    """One space-separated output column: never empty, never containing
    whitespace (Morpheus has lemmas like 'Δημ ́ητριος' with a stray space
    before a combining accent), NFC so accents are precomposed."""
    if x in (None, ""):
        return "-"
    s = "".join(str(x).split())
    return unicodedata.normalize("NFC", s) or "-"


def write_output(tool, rows, raw=None):
    """rows: iterable of (index, form, normalised, pos, parse, formparse, lemma).
    raw: optional iterable of JSON-serialisable dicts (one per token)."""
    ANALYSIS.mkdir(exist_ok=True)
    out = ANALYSIS / f"lemmas-{tool}.txt"
    n = 0
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(" ".join(field(x) for x in row) + "\n")
            n += 1
    if raw is not None:
        RAW.mkdir(exist_ok=True)
        with open(RAW / f"{tool}.jsonl", "w", encoding="utf-8", newline="\n") as f:
            for r in raw:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {n} tokens to {out.relative_to(ROOT)}", file=sys.stderr)
    return out


# ---------------------------------------------------------------------------
# aligning a tagger's own tokenisation with ours

_APOS = "’'ʼ"


def align_key(s):
    """Loose comparison key: strip punctuation/apostrophes, NFC (so oxia and
    tonos code points compare equal), lowercase."""
    s = strip_punct(s).strip(_APOS)
    return unicodedata.normalize("NFC", s).lower()


def align(toks, tagged, form_of=lambda t: t["form"]):
    """Pair each of our token dicts (from sentences()) with the tagger's
    token (a dict or object; form_of extracts its surface form), or None
    when the tagger's tokenisation cannot be reconciled.  Handles the tagger
    splitting one of our tokens into several pieces (the first piece's
    analysis is used and the pieces are recorded under "merged")."""
    lex = [t for t in tagged if align_key(form_of(t))]  # drop pure punctuation
    j = 0
    for t in toks:
        want = align_key(t["bare"])
        if j < len(lex) and align_key(form_of(lex[j])) == want:
            yield t, lex[j]
            j += 1
            continue
        k, acc = j, ""
        while k < len(lex) and want.startswith(acc + align_key(form_of(lex[k]))):
            acc += align_key(form_of(lex[k]))
            k += 1
        if acc == want and k > j:
            m = lex[j] if isinstance(lex[j], dict) else {"obj": lex[j]}
            yield t, dict(m, merged=[form_of(x) for x in lex[j:k]])
            j = k
        else:
            yield t, None
