"""Lemmatise + tag with CLTK (https://github.com/cltk/cltk).

    python run_cltk.py            # CLTK's default Greek pipeline: OdyCy spaCy model
    python run_cltk.py stanza     # CLTK's GreekStanzaProcess (Stanza, perseus treebank)

Both run CLTK's GreekNormalizeProcess first (as the stock pipeline does),
then the tagger; we read lemma/UPOS/feats straight off the spaCy or Stanza
document CLTK keeps on its Doc.  The embeddings/stopword/NER processes of
the stock pipeline are skipped - they add nothing for lemmatisation.

The spaCy model is `grc_odycy_joint_sm`; newer pip rejects its wheel
filename, so install it by hand:
    curl -L -o grc_odycy_joint_sm-0.7.0-py3-none-any.whl \
      https://huggingface.co/chcaa/grc_odycy_joint_sm/resolve/main/grc_odycy_joint_sm-any-py3-none-any.whl
    pip install grc_odycy_joint_sm-0.7.0-py3-none-any.whl
(check the version inside the wheel's METADATA if 0.7.0 is stale)
"""
import os
import sys

# CLTK 1.5 looks for Stanza models in ~/stanza_resources, but Stanza 1.14 on
# Windows downloads to %LOCALAPPDATA%\StanfordNLP\stanza\Cache by default;
# make Stanza use the directory CLTK expects.
os.environ.setdefault("STANZA_RESOURCES_DIR", os.path.expanduser("~/stanza_resources"))

from cltk import NLP
from cltk.alphabet.processes import GreekNormalizeProcess
from cltk.core.data_types import Pipeline
from cltk.languages.utils import get_lang

from common import (align, capitalise_like, parse_feats, sentences,
                    tagger_text, ud_to_parse, ud_to_pos, write_output)


def spacy_tokens(doc):
    for t in doc.spacy_doc:
        yield {"form": t.text, "upos": t.pos_, "xpos": t.tag_, "lemma": t.lemma_,
               "feats": t.morph.to_dict(), "deprel": t.dep_}


def stanza_tokens(doc):
    for s in doc.stanza_doc.sentences:
        for w in s.words:
            yield {"form": w.text, "upos": w.upos, "xpos": w.xpos, "lemma": w.lemma,
                   "feats": parse_feats(w.feats), "deprel": w.deprel}


def main():
    backend = sys.argv[1] if len(sys.argv) > 1 else "spacy"
    if backend == "spacy":
        from cltk.dependency.processes import GreekSpacyProcess as Tagger
        extract, tool = spacy_tokens, "cltk"
    elif backend == "stanza":
        from cltk.dependency.processes import GreekStanzaProcess as Tagger
        from cltk.dependency.stanza_wrapper import StanzaWrapper
        # CLTK would otherwise prompt on stdin before downloading the model
        StanzaWrapper.nlps["grc"] = StanzaWrapper(language="grc", interactive=False, silent=True)
        extract, tool = stanza_tokens, "cltk-stanza"
    else:
        sys.exit("backend must be spacy or stanza")

    pipeline = Pipeline(description=f"Greek lemmatisation via {backend}",
                        processes=[GreekNormalizeProcess, Tagger], language=get_lang("grc"))
    nlp = NLP(language="grc", custom_pipeline=pipeline, suppress_banner=True)

    rows, raw, misaligned = [], [], 0
    sents = list(sentences())
    for n, (ref, toks) in enumerate(sents, 1):
        doc = nlp.analyze(text=tagger_text(toks))
        for t, m in align(toks, list(extract(doc))):
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
