"""Lemmatise + tag with Dilemma (https://github.com/open-greek/dilemma).

    pip install "dilemma-nlp[onnx,tagger-onnx] @ git+https://github.com/open-greek/dilemma.git"
    python -m dilemma download

The tagger takes whole sentences (we feed it one textpart line at a time),
splits on whitespace and peels off edge punctuation as PUNCT tokens, so its
lexical tokens line up 1:1 with ours; any token that still cannot be
aligned is tagged on its own as a fallback.
"""
import sys

from dilemma.tagger import Tagger

from common import (align, capitalise_like, parse_feats, sentences,
                    tagger_text, ud_to_parse, ud_to_pos, write_output)


def main():
    tagger = Tagger(lang="grc", lemmatize=True)
    sents = list(sentences())
    texts = [tagger_text(toks) for _, toks in sents]
    print(f"tagging {len(texts)} lines", file=sys.stderr)
    tagged = tagger.tag(texts)

    rows, raw, fallback = [], [], 0
    for (ref, toks), out in zip(sents, tagged):
        for t, m in align(toks, out):
            if m is None:
                fallback += 1
                single = [x for x in tagger.tag([t["bare"]])[0] if x.get("upos") != "PUNCT"]
                m = dict(single[0], fallback="tagged alone") if single else None
            if m is None:
                rows.append((t["index"], t["form"], t["norm"], "--", "--------", "-------", "-"))
                raw.append({"index": t["index"], "ref": ref, "form": t["form"], "error": "misaligned"})
                continue
            feats = parse_feats(m.get("feats"))
            lemma = m.get("lemma") or "-"
            rows.append((t["index"], t["form"], capitalise_like(t["norm"], lemma),
                         ud_to_pos(m.get("upos"), feats, lemma), ud_to_parse(m.get("upos"), feats),
                         "-------", lemma))
            raw.append({"index": t["index"], "ref": ref, "form": t["form"], **m})
    write_output("dilemma", rows, raw)
    if fallback:
        print(f"{fallback} tokens were not aligned and were tagged alone", file=sys.stderr)


if __name__ == "__main__":
    main()
