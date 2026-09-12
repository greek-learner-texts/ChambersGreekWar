"""Write analysis/lemmas-majority.txt: one lemma per token by majority vote
over the lemmas-<tool>.txt outputs.

    python majority.py [--tools dilemma,cltk-stanza,morpheus,cltk]

Voting: lemmas are compared NFC-normalised, case-folded and with Morpheus's
homograph digits stripped (ἤ1 == ἤ).  Ties go to the tool listed first in
--tools (default order follows the pairwise agreement rates).  POS and
parse come from the highest-priority tool that voted for the winning lemma,
so the row is internally consistent.  Vote details for every token are in
analysis/raw/majority.jsonl (winner, votes, whether it was a tie).
"""
import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict

from common import ANALYSIS, RAW, ROOT, tokens

DEFAULT_TOOLS = "dilemma,cltk-stanza,morpheus,cltk"


def load(tool):
    path = ANALYSIS / f"lemmas-{tool}.txt"
    if not path.exists():
        return None
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            idx, form, norm, pos, parse, fparse, lemma = line.rstrip("\n").split(" ", 6)
            out[int(idx)] = (norm, pos, parse, lemma)
    return out


def key(lemma):
    return unicodedata.normalize("NFC", re.sub(r"\d+$", "", lemma)).casefold()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tools", default=DEFAULT_TOOLS, help="priority order for tie-breaks")
    args = ap.parse_args()
    tools = [t for t in args.tools.split(",") if load(t) is not None]
    data = {t: load(t) for t in tools}
    if len(tools) < 2:
        sys.exit(f"need at least two outputs, found: {tools}")
    print(f"voting over {tools}", file=sys.stderr)

    rows, raw, stats = [], [], Counter()
    for i, ref, form, bare, norm in tokens():
        votes = Counter()
        voters = defaultdict(list)
        for t in tools:
            lemma = data[t][i][3]
            if lemma != "-":
                votes[key(lemma)] += 1
                voters[key(lemma)].append(t)
        if not votes:
            rows.append((i, form, norm, "--", "--------", "-------", "-"))
            raw.append({"index": i, "ref": ref, "form": form, "winner": None, "votes": {}})
            stats["none"] += 1
            continue
        top = max(votes.values())
        winners = [k for k, v in votes.items() if v == top]
        # tie-break: the candidate backed by the highest-priority tool
        best = min(winners, key=lambda k: tools.index(voters[k][0]))
        src = voters[best][0]
        tnorm, pos, parse, lemma = data[src][i]
        rows.append((i, form, tnorm, pos, parse, "-------", lemma))
        raw.append({"index": i, "ref": ref, "form": form, "winner": lemma, "source": src,
                    "votes": {t: data[t][i][3] for t in tools}, "count": top,
                    "of": sum(votes.values()), "tie": len(winners) > 1})
        stats[f"{top}/{sum(votes.values())}"] += 1
        if len(winners) > 1:
            stats["tie"] += 1

    out = ANALYSIS / "lemmas-majority.txt"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(" ".join(str(x) for x in row) + "\n")
    RAW.mkdir(exist_ok=True)
    with open(RAW / "majority.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for r in raw:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {out.relative_to(ROOT)}")
    for k, v in sorted(stats.items(), reverse=True):
        print(f"  {k:6s} {v:6d}  ({v / len(rows):.1%})")


if __name__ == "__main__":
    main()
