"""Lemmatise with Morpheus via the Perseids morphology API.

Needs the container running:
    docker run -d --name morpheus -p 1500:1500 perseidsproject/morpheus-perseids-api:latest

Morpheus analyses forms in isolation and returns *every* possible analysis;
it does not disambiguate.  The 7-column output takes the first entry/first
inflection as a best guess; all analyses are kept in analysis/raw/morpheus.jsonl
and the per-form API responses are cached in analysis/raw/morpheus-cache.json.
"""
import json
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from common import RAW, capitalise_like, tokens, write_output

API = "http://localhost:1500/analysis/word"
CACHE = RAW / "morpheus-cache.json"

POFS = {
    "noun": "N-", "verb": "V-", "verb participle": "V-", "adjective": "A-",
    "numeral": "A-", "article": "RA", "pronoun": "RP", "adverb": "D-",
    "conjunction": "C-", "preposition": "P-", "particle": "X-",
    "exclamation": "I-", "interjection": "I-", "adverbial": "D-",
}
# refine pronoun class by lemma the way MorphGNT does
PRON = {"ὅς": "RR", "ὅστις": "RR", "ὅσος": "RR", "οἷος": "RR",
        "οὗτος": "RD", "ὅδε": "RD", "ἐκεῖνος": "RD",
        "τις": "RI", "τίς": "RI", "πότερος": "RI", "ὁπότερος": "RI"}
PERS = {"1st": "1", "2nd": "2", "3rd": "3"}
TENSE = {"present": "P", "imperfect": "I", "future": "F", "aorist": "A",
         "perfect": "X", "pluperfect": "Y", "future perfect": "Z"}
VOICE = {"active": "A", "middle": "M", "passive": "P", "mediopassive": "M",
         "mp": "M"}
MOOD = {"indicative": "I", "imperative": "D", "subjunctive": "S",
        "optative": "O", "infinitive": "N", "participle": "P"}
CASE = {"nominative": "N", "genitive": "G", "dative": "D", "accusative": "A",
        "vocative": "V"}
NUM = {"singular": "S", "plural": "P", "dual": "D"}
GEND = {"masculine": "M", "feminine": "F", "neuter": "N"}
COMP = {"comparative": "C", "superlative": "S"}


def val(d, key):
    v = d.get(key) if isinstance(d, dict) else None
    return v.get("$") if isinstance(v, dict) else None


def as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def query(word):
    q = urllib.parse.urlencode({"lang": "grc", "engine": "morpheusgrc", "word": word})
    with urllib.request.urlopen(API + "?" + q, timeout=60) as r:
        return json.load(r)


def analyses(resp):
    """Flatten the RDF response into [{lemma, pofs, ...}, ...]."""
    out = []
    body = resp.get("RDF", {}).get("Annotation", {}).get("Body")
    for b in as_list(body):
        for entry in as_list(b.get("rest", {}).get("entry")):
            d = entry.get("dict", {})
            lemma = val(d, "hdwd")
            for infl in as_list(entry.get("infl")):
                out.append({
                    "lemma": lemma,
                    "pofs": val(infl, "pofs") or val(d, "pofs"),
                    "pers": val(infl, "pers"), "tense": val(infl, "tense"),
                    "voice": val(infl, "voice"), "mood": val(infl, "mood"),
                    "case": val(infl, "case"), "num": val(infl, "num"),
                    "gend": val(infl, "gend") or val(d, "gend"),
                    "comp": val(infl, "comp"), "dial": val(infl, "dial"),
                    "stemtype": val(infl, "stemtype"),
                })
    return out


def to_row(a):
    pos = POFS.get(a["pofs"], "--")
    if pos == "RP":
        pos = PRON.get(a["lemma"], "RP")
    parse = (PERS.get(a["pers"], "-") + TENSE.get(a["tense"], "-")
             + VOICE.get(a["voice"], "-") + MOOD.get(a["mood"], "-")
             + CASE.get(a["case"], "-") + NUM.get(a["num"], "-")
             + GEND.get(a["gend"], "-") + COMP.get(a["comp"], "-"))
    return pos, parse


def candidates(bare, norm):
    """Query strings to try, in order: the bare form, then the normalised
    form (fixes grave accents / elision / final nu), then lowercased."""
    c = [bare, norm, norm.lower(), bare.lower()]
    return list(dict.fromkeys(x for x in c if x))


def main():
    toks = list(tokens())
    cache = {}
    if CACHE.exists():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    todo = sorted({c for _, _, _, bare, norm in toks for c in candidates(bare, norm)} - set(cache))
    print(f"{len(todo)} forms to query ({len(cache)} cached)", file=sys.stderr)

    def fetch(w):
        try:
            return w, analyses(query(w))
        except Exception as e:  # keep going; record the failure
            return w, {"error": str(e)}

    RAW.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as ex:
        for n, (w, res) in enumerate(ex.map(fetch, todo), 1):
            cache[w] = res
            if n % 500 == 0:
                print(f"  {n}/{len(todo)}", file=sys.stderr)
                CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")

    rows, raw = [], []
    for i, ref, form, bare, norm in toks:
        found, used = [], None
        for c in candidates(bare, norm):
            res = cache.get(c)
            if isinstance(res, list) and res:
                found, used = res, c
                break
        if found:
            a = found[0]
            pos, parse = to_row(a)
            lemma = a["lemma"]
        else:
            pos, parse, lemma = "--", "--------", None
        rows.append((i, form, capitalise_like(norm, lemma), pos, parse, "-------", lemma or "-"))
        raw.append({"index": i, "ref": ref, "form": form, "queried": used,
                    "n_analyses": len(found), "analyses": found})
    write_output("morpheus", rows, raw)
    missing = sum(1 for r in raw if not r["n_analyses"])
    print(f"{missing} tokens with no Morpheus analysis", file=sys.stderr)


if __name__ == "__main__":
    main()
