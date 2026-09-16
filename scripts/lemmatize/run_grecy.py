"""Lemmatise + tag with a GreCy spaCy model (https://github.com/jmyerston/greCy).

    python run_grecy.py                  # grc_proiel_trf  -> lemmas-grecy.txt
    python run_grecy.py grc_perseus_trf  # another model   -> lemmas-grecy-grc_perseus_trf.txt

Installing a model: `python -m grecy install grc_proiel_trf` tries a
HuggingFace URL that no longer exists (401); the wheels are GitHub release
assets instead - pick the one matching your spaCy version:
    pip install https://github.com/jmyerston/greCy/releases/download/v3.7.5/grc_proiel_trf-3.7.5-py3-none-any.whl

Plain spaCy, no CLTK wrapper; the text is fed one textpart line at a time
with punctuation space-separated (see common.tagger_text).
"""
import sys
import warnings

import spacy

from common import (align, capitalise_like, sentences, tagger_text,
                    ud_to_parse, ud_to_pos, write_output)

DEFAULT_MODEL = "grc_proiel_trf"


def main():
    warnings.filterwarnings("ignore")
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    tool = "grecy" if model == DEFAULT_MODEL else f"grecy-{model}"
    nlp = spacy.load(model)

    rows, raw, misaligned = [], [], 0
    sents = list(sentences())
    docs = nlp.pipe(tagger_text(toks) for _, toks in sents)
    for n, ((ref, toks), doc) in enumerate(zip(sents, docs), 1):
        tagged = [{"form": t.text, "upos": t.pos_, "xpos": t.tag_, "lemma": t.lemma_,
                   "feats": t.morph.to_dict(), "deprel": t.dep_} for t in doc]
        for t, m in align(toks, tagged):
            if m is None:
                misaligned += 1
                rows.append((t["index"], t["form"], t["norm"], "--", "--------", "-------", "-"))
                raw.append({"index": t["index"], "ref": ref, "form": t["form"], "error": "misaligned"})
                continue
            feats = m["feats"]
            lemma = m.get("lemma") or "-"
            rows.append((t["index"], t["form"], capitalise_like(t["norm"], lemma),
                         ud_to_pos(m["upos"], feats, lemma), ud_to_parse(m["upos"], feats),
                         "-------", lemma))
            raw.append({"index": t["index"], "ref": ref, "form": t["form"], **m})
        if n % 50 == 0:
            print(f"  {n}/{len(sents)} lines", file=sys.stderr)
    write_output(tool, rows, raw)
    if misaligned:
        print(f"{misaligned} tokens could not be aligned", file=sys.stderr)


if __name__ == "__main__":
    main()
