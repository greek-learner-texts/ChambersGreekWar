"""Write analysis/tokens.txt: index ref form normalised (no tool involved)."""
from common import tokens, ANALYSIS

ANALYSIS.mkdir(exist_ok=True)
n = 0
with open(ANALYSIS / "tokens.txt", "w", encoding="utf-8", newline="\n") as f:
    for i, ref, form, bare, norm in tokens():
        f.write(f"{i} {ref} {form} {norm}\n")
        n = i
print(f"wrote {n} tokens")
