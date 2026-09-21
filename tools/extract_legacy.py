#!/usr/bin/env python3
"""One-off script: extract content/reviews/<slug>.md from the legacy hand-written HTML.

Run once from repo root: python3 tools/extract_legacy.py
Reads reviews/*.html, coconut-water.html, feed.xml.
Writes content/reviews/<slug>.md (TOML front matter + Notes/Verdict sections).
"""
import glob
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEWS_DIR = ROOT / "reviews"
OUT_DIR = ROOT / "content" / "reviews"

KNOWN_TAGS = {
    "Pasteurized": ("pasteurized", True),
    "Unpasteurized": ("pasteurized", False),
    "Added Sugar": ("added_sugar", True),
    "No Added Sugar": ("added_sugar", False),
    "USDA Organic": ("organic", True),
    "Not Organic": ("organic", False),
    "Fair Trade": ("fair_trade", True),
    "Pulp": ("pulp", True),
    "No Pulp": ("pulp", False),
}
STYLES = {"Still", "Sparkling"}


def slug_from_path(p):
    return Path(p).stem


def load(path):
    return open(path, encoding="utf-8").read()


def toml_escape(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def toml_str(s):
    return f'"{toml_escape(s)}"'


def toml_list(items):
    return "[" + ", ".join(toml_str(i) for i in items) + "]"


def extract_review_page(text):
    data = {}
    m = re.search(r'"datePublished":\s*"([0-9-]+)"', text)
    data["date"] = m.group(1)
    m = re.search(r'"ratingValue":\s*"([0-9.]+)"', text)
    overall = float(m.group(1))
    m = re.search(r'<img class="bottle" src="img/([^"]+)"', text)
    data["image"] = f"reviews/img/{m.group(1)}"
    m = re.search(r'<meta name="description" content="([^"]*)">', text)
    data["description"] = html.unescape(m.group(1))
    m = re.search(r"<h2>([^<]+)</h2>\s*<p>([^<]+(?:<a[^>]*>[^<]*</a>[^<]*)*)</p>", text)
    heading = html.unescape(m.group(1))
    brand, product = [s.strip() for s in heading.split("—", 1)]
    data["brand"] = brand
    data["product"] = product
    meta_line = html.unescape(re.sub(r"<[^>]+>", "", m.group(2)))
    parts = [p.strip() for p in meta_line.split("\u00b7")]
    # parts[0] = "Month YYYY", parts[1] = size, then style, then flags/tags
    data["size"] = parts[1]
    booleans = {"pasteurized": False, "added_sugar": False, "organic": False,
                "fair_trade": False, "pulp": False}
    extra_tags = []
    for p in parts[2:]:
        if p in STYLES:
            data["style"] = p
        elif p in KNOWN_TAGS:
            field, val = KNOWN_TAGS[p]
            booleans[field] = val
        else:
            extra_tags.append(p)
    data.update(booleans)
    data["extra_tags"] = extra_tags

    scores = {}
    for label, key in [("Taste", "taste"), ("Sweetness", "sweetness"), ("Body", "body"),
                        ("Refreshment", "refreshment"), ("Ethics", "ethics"), ("Overall", "overall")]:
        sm = re.search(rf"<span>{label}</span>\s*([0-9.]+)\s*/\s*10", text)
        scores[key] = float(sm.group(1))
    scores["overall"] = overall
    data["scores"] = scores

    def section(name):
        sm = re.search(rf"<h2>{name}</h2>\s*(.*?)(?=<h2>|<p style=)", text, re.S)
        block = sm.group(1)
        paras = re.findall(r"<p>(.*?)</p>", block, re.S)
        return [html.unescape(p.strip()) for p in paras]

    data["notes"] = section("Notes")
    data["verdict"] = section("Verdict")
    return data


def extract_listing(coconut_html):
    listing = {}
    order = 0
    for m in re.finditer(
        r'<div class="review-item" data-tags="([^"]*)">\s*'
        r'<div class="thumb"><img src="reviews/img/[^"]*" alt="[^"]*"></div>\s*'
        r'<div>\s*<div class="item-name"><a href="reviews/([a-z0-9-]+)\.html">([^<]*)</a></div>',
        coconut_html,
    ):
        order += 1
        slug = m.group(2)
        listing[slug] = {"listing_name": html.unescape(m.group(3)), "order": order}
    for m in re.finditer(
        r'<td class="pname"><a href="reviews/([a-z0-9-]+)\.html">([^<]*)</a></td>',
        coconut_html,
    ):
        slug = m.group(1)
        if slug in listing:
            listing[slug]["table_name"] = html.unescape(m.group(2))
    return listing


def extract_feed_descriptions(feed_xml):
    out = {}
    for m in re.finditer(
        r"<link>https://natewooding\.com/reviews/([a-z0-9-]+)\.html</link>\s*"
        r"<guid>[^<]*</guid>\s*<pubDate>[^<]*</pubDate>\s*"
        r"<description>([^<]*)</description>",
        feed_xml,
    ):
        out[m.group(1)] = html.unescape(m.group(2))
    return out


def write_md(slug, data, listing_info):
    fm_lines = ["+++"]
    fm_lines.append(f'brand = {toml_str(data["brand"])}')
    fm_lines.append(f'product = {toml_str(data["product"])}')
    fm_lines.append(f'listing_name = {toml_str(listing_info["listing_name"])}')
    fm_lines.append(f'table_name = {toml_str(listing_info.get("table_name", listing_info["listing_name"]))}')
    fm_lines.append(f'order = {listing_info["order"]}')
    fm_lines.append(f'date = {toml_str(data["date"])}')
    fm_lines.append(f'size = {toml_str(data["size"])}')
    fm_lines.append(f'style = {toml_str(data["style"])}')
    for b in ["pasteurized", "added_sugar", "organic", "fair_trade", "pulp"]:
        fm_lines.append(f'{b} = {"true" if data[b] else "false"}')
    fm_lines.append(f'extra_tags = {toml_list(data["extra_tags"])}')
    fm_lines.append(f'image = {toml_str(data["image"])}')
    fm_lines.append(f'description = {toml_str(data["description"])}')
    s = data["scores"]
    fm_lines.append(
        "scores = {{ taste = {taste}, sweetness = {sweetness}, body = {body}, "
        "refreshment = {refreshment}, ethics = {ethics}, overall = {overall} }}".format(**s)
    )
    fm_lines.append("+++")
    body = ["", "## Notes", ""]
    body.append("\n\n".join(data["notes"]))
    body.append("")
    body.append("## Verdict")
    body.append("")
    body.append("\n\n".join(data["verdict"]))
    content = "\n".join(fm_lines) + "\n" + "\n".join(body) + "\n"
    (OUT_DIR / f"{slug}.md").write_text(content, encoding="utf-8")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    coconut_html = load(ROOT / "coconut-water.html")
    listing = extract_listing(coconut_html)
    feed_desc = extract_feed_descriptions(load(ROOT / "feed.xml"))

    count = 0
    for path in sorted(glob.glob(str(REVIEWS_DIR / "*.html"))):
        slug = slug_from_path(path)
        text = load(path)
        data = extract_review_page(text)
        if slug not in listing:
            raise SystemExit(f"{slug}: not found in coconut-water.html listing")
        write_md(slug, data, listing[slug])
        count += 1
    print(f"wrote {count} review files to {OUT_DIR}")


if __name__ == "__main__":
    main()
