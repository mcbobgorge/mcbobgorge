"""Check the built site: no broken local links, one h1 and real metadata per page.

Usage: python3 build.py --out _site && python3 tools/check_site.py _site
Exits non-zero listing every problem, so the deploy workflow can gate on it.
"""

import re
import sys
from pathlib import Path

LINK = re.compile(r'(?:href|src)="([^"#?]+)"')
H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
TITLE = re.compile(r"<title>(.*?)</title>", re.S)
DESCRIPTION = re.compile(r'name="description" content="([^"]*)"')


def problems(root: Path):
    pages = sorted(root.rglob("*.html"))
    if not pages:
        yield "no HTML pages found — did the build run?"
        return
    for page in pages:
        html = page.read_text(encoding="utf-8")
        name = page.relative_to(root)
        for href in LINK.findall(html):
            if href.startswith(("http", "mailto:", "//")):
                continue
            target = root / href.lstrip("/") if href.startswith("/") else page.parent / href
            if not target.exists():
                yield f"{name}: broken link to {href}"
        if len(H1.findall(html)) != 1:
            yield f"{name}: expected exactly one <h1>, found {len(H1.findall(html))}"
        if not TITLE.search(html):
            yield f"{name}: no <title>"
        description = DESCRIPTION.search(html)
        if not description or len(description.group(1)) < 50:
            yield f"{name}: missing or too-short meta description"


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
    found = list(problems(root))
    for problem in found:
        print(problem)
    print(f"checked {len(list(root.rglob('*.html')))} pages, {len(found)} problem(s)")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
