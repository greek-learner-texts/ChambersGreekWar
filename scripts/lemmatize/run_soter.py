"""Lemmatise with Sōtēr Megas (https://huggingface.co/Zual/soter-megas), a
ByT5-base seq2seq lemmatiser distilled from LLM annotations.

    python run_soter.py                 # <tb_perseus> convention -> lemmas-soter.txt
    python run_soter.py proiel          # <tb_proiel>             -> lemmas-soter-proiel.txt
    python run_soter.py perseus 200     # only the first 200 tokens (quick check)

Lemmas only: no POS or parse, so those columns are "--"/"--------".  The
model (~2.3 GB) downloads into the HuggingFace cache on first run.

Slow on CPU (~1.3 s/token here, so a few hours for the whole text): the
model is int8-quantised (dynamic, Linear layers only), which gave output
identical to fp32 on a test sample and is ~30% faster.  Progress is
appended to analysis/raw/<tool>.partial.jsonl, and an interrupted run
resumes from there.

Each token is lemmatised separately with the input the model card
describes:
    <tb_X> s p e l l e d <sep> left context <tgt> form </tgt> right context
context being up to 8 words either side, running across textpart lines
(punctuation as separate words, see common.tagger_text), trimmed until the
input fits the model's 384-byte limit.
"""
import json
import sys
import unicodedata

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from common import RAW, capitalise_like, sentences, tagger_text, write_output

MODEL = "Zual/soter-megas"
CTX = 8
MAX_BYTES = 384
BATCH = 8


def nfc(s):
    return unicodedata.normalize("NFC", s)


def build_input(conv, words, i):
    """words: the text split into words + punctuation; i: target position."""
    for ctx in range(CTX, -1, -1):
        left = " ".join(words[max(0, i - ctx):i])
        right = " ".join(words[i + 1:i + 1 + ctx])
        s = (f"<tb_{conv}> {' '.join(words[i])} <sep> {left} "
             f"<tgt> {words[i]} </tgt> {right}")
        s = " ".join(s.split())
        if len(s.encode("utf-8")) <= MAX_BYTES:
            return s
    return s


def inputs(conv, limit):
    """Yield (token dict, ref, model input) for every token.  The context
    runs across textpart lines: cut at the line start, a line opening
    'οἱ δὲ …' has only 'οἱ' as left context and the model lemmatises the
    δέ as ὁ."""
    words, targets = [], []
    for ref, toks in sentences():
        line = nfc(tagger_text(toks)).split()
        j = 0
        for t in toks:
            bare = nfc(t["bare"])
            while line[j] != bare:  # skip the punctuation tagger_text split off
                j += 1
            targets.append((t, ref, len(words) + j))
            j += 1
        words += line
    for t, ref, i in targets[:limit or None]:
        yield t, ref, build_input(conv, words, i)


def main():
    conv = sys.argv[1] if len(sys.argv) > 1 else "perseus"
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    tool = "soter" if conv == "perseus" else f"soter-{conv}"
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL).eval()
    model = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)

    items = list(inputs(conv, limit))
    partial = RAW / f"{tool}.partial.jsonl"
    done = {}
    if partial.exists():
        # reuse a saved lemma only if the token's input is unchanged
        want = {t["index"]: inp for t, _, inp in items}
        with open(partial, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if want.get(r["index"]) == r["input"]:
                    done[r["index"]] = r
        print(f"resuming: {len(done)} tokens already done", file=sys.stderr)
    todo = [x for x in items if x[0]["index"] not in done]
    RAW.mkdir(exist_ok=True)
    with open(partial, "a", encoding="utf-8", newline="\n") as f:
        for b in range(0, len(todo), BATCH):
            batch = todo[b:b + BATCH]
            enc = tok([x[2] for x in batch], return_tensors="pt", padding=True)
            with torch.inference_mode():
                out = model.generate(**enc, max_length=48)
            for (t, ref, inp), lemma in zip(batch, tok.batch_decode(out, skip_special_tokens=True)):
                r = {"index": t["index"], "ref": ref, "form": t["form"], "input": inp,
                     "lemma": nfc(lemma.strip()) or "-"}
                done[t["index"]] = r
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()
            print(f"  {len(done)}/{len(items)} tokens", file=sys.stderr)

    rows, raw = [], []
    for t, ref, inp in items:
        r = done[t["index"]]
        rows.append((t["index"], t["form"], capitalise_like(t["norm"], r["lemma"]),
                     "--", "--------", "-------", r["lemma"]))
        raw.append(r)
    write_output(tool, rows, raw)
    if not limit:
        partial.unlink()


if __name__ == "__main__":
    main()
