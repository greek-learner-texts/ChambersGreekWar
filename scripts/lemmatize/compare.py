"""Compare the analysis/lemmas-<tool>.txt outputs token by token.

    python compare.py                 # summary + write analysis/lemmas-compare.txt
    python compare.py --disagree 40   # also print 40 sample disagreements

analysis/lemmas-compare.txt has one line per token:
    index ref form <lemma per tool...> <pos per tool...> agree
where agree is Y when every tool that produced a lemma gave the same one.
"""
import argparse
import itertools
import random
import sys
from collections import Counter

from common import ANALYSIS, ROOT, tokens


def load(tool):
    path = ANALYSIS / f"lemmas-{tool}.txt"
    if not path.exists():
        return None
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            idx, form, norm, pos, parse, fparse, lemma = line.rstrip("\n").split(" ", 6)
            out[int(idx)] = {"form": form, "norm": norm, "pos": pos, "parse": parse, "lemma": lemma}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", default="morpheus,cltk,dilemma")
    ap.add_argument("--disagree", type=int, default=0, help="print N sample disagreements")
    args = ap.parse_args()

    tools = [t for t in args.tools.split(",") if load(t) is not None]
    data = {t: load(t) for t in tools}
    if len(tools) < 2:
        sys.exit(f"need at least two outputs, found: {tools}")
    toks = list(tokens())
    n = len(toks)

    covered = {t: sum(1 for i in range(1, n + 1) if data[t][i]["lemma"] != "-") for t in tools}
    pair_agree = Counter()
    pair_both = Counter()
    all_agree = 0
    disagreements = []
    lines = []
    for i, ref, form, bare, norm in toks:
        lemmas = {t: data[t][i]["lemma"] for t in tools}
        poss = {t: data[t][i]["pos"] for t in tools}
        present = {t: l for t, l in lemmas.items() if l != "-"}
        agree = len(set(present.values())) <= 1
        if agree and len(present) == len(tools):
            all_agree += 1
        for a, b in itertools.combinations(tools, 2):
            if lemmas[a] != "-" and lemmas[b] != "-":
                pair_both[(a, b)] += 1
                if lemmas[a] == lemmas[b]:
                    pair_agree[(a, b)] += 1
        if not agree:
            disagreements.append((i, ref, form, lemmas, poss))
        lines.append(" ".join([str(i), ref, form] + [lemmas[t] for t in tools]
                              + [poss[t] for t in tools] + ["Y" if agree else "N"]))

    out = ANALYSIS / "lemmas-compare.txt"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("# index ref form " + " ".join(f"lemma:{t}" for t in tools) + " "
                + " ".join(f"pos:{t}" for t in tools) + " agree\n")
        f.write("\n".join(lines) + "\n")

    print(f"tokens: {n}")
    for t in tools:
        print(f"  {t:9s} lemma for {covered[t]} ({covered[t] / n:.1%})")
    for (a, b), both in sorted(pair_both.items()):
        print(f"  {a} vs {b}: {pair_agree[(a, b)]}/{both} agree ({pair_agree[(a, b)] / both:.1%})")
    print(f"  all {len(tools)} agree: {all_agree} ({all_agree / n:.1%})")
    print(f"wrote {out.relative_to(ROOT)}")

    if args.disagree:
        random.seed(0)
        for i, ref, form, lemmas, poss in random.sample(disagreements, min(args.disagree, len(disagreements))):
            print(f"{i:6d} {ref} {form:20s} " + "  ".join(f"{t}={lemmas[t]}/{poss[t]}" for t in tools))


if __name__ == "__main__":
    main()
