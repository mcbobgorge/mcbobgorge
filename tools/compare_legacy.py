#!/usr/bin/env python3
"""Compare freshly built pages against the pre-change committed HTML.

Run after `python3 build.py`, from repo root: python3 tools/compare_legacy.py
For each generated page, diffs it against `git show HEAD:<path>` as it was
on the publishing-pipeline branch's parent commit (the last hand-written
version), after normalising whitespace, and prints a report.
"""
import difflib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The commit before any generator changes were committed on this branch.
BASE_REF = subprocess.run(
    ["git", "merge-base", "main", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
).stdout.strip()


def normalize(text: str) -> str:
    """Collapse all whitespace runs to a single space so line-wrapping and
    indentation differences (e.g. one-line vs multi-line JSON blocks) don't
    count as content differences."""
    return re.sub(r"\s+", " ", text).strip()


def _tagwise(text: str) -> list[str]:
    return re.sub(r"(?<=>)\s*", "\n", text).split("\n")


def original(path: str) -> str | None:
    r = subprocess.run(
        ["git", "show", f"{BASE_REF}:{path}"], cwd=ROOT, capture_output=True, text=True
    )
    if r.returncode != 0:
        return None
    return r.stdout


def compare(path: str) -> None:
    orig = original(path)
    cur = (ROOT / path).read_text(encoding="utf-8")
    if orig is None:
        print(f"{path}: NEW (no original to compare)")
        return
    if normalize(orig) == normalize(cur):
        print(f"{path}: identical (after whitespace normalisation)")
        return
    o_lines = _tagwise(orig)
    c_lines = _tagwise(cur)
    sm = difflib.SequenceMatcher(a=o_lines, b=c_lines, autojunk=False)
    changed = 0
    shown = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        changed += max(i2 - i1, j2 - j1)
        if shown < 6:
            print(f"{path}: {tag}\n  orig: {' '.join(o_lines[i1:i2])[:200]}\n  new:  {' '.join(c_lines[j1:j2])[:200]}")
            shown += 1
    print(f"{path}: {changed} differing chunk-line(s) of {len(o_lines)}")


def main() -> None:
    paths = ["coconut-water.html", "feed.xml", "sitemap.xml", "index.html", "about.html", "style.css"]
    paths += [f"reviews/{p.name}" for p in sorted((ROOT / "reviews").glob("*.html"))]
    for p in paths:
        compare(p)


if __name__ == "__main__":
    main()
