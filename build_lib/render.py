"""Render HTML/XML pages from Review objects using templates/ (string.Template)."""
from __future__ import annotations

import datetime
import json
import re
from pathlib import Path
from string import Template

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def _tpl(name: str) -> Template:
    return Template((TEMPLATES / name).read_text(encoding="utf-8"))


def yn(b: bool) -> str:
    return "Yes" if b else "No"


def meta_line(r) -> str:
    parts = [r.month_year, r.size, r.style]
    if r.origin:
        parts.append(r.origin)
    parts.append("Pasteurized" if r.pasteurized else "Unpasteurized")
    parts.append("Added Sugar" if r.added_sugar else "No Added Sugar")
    if r.pulp:
        parts.append("Pulp")
    parts.append("USDA Organic" if r.organic else "Not Organic")
    if r.fair_trade:
        parts.append("Fair Trade")
    parts.extend(r.extra_tags)
    return " &middot; ".join(parts)


def listing_meta_line(r) -> str:
    parts = [r.month_year, r.style]
    parts.append("Pasteurized" if r.pasteurized else "Unpasteurized")
    parts.append("Added Sugar" if r.added_sugar else "No Added Sugar")
    if r.pulp:
        parts.append("Pulp")
    if r.organic:
        parts.append("USDA Organic")
    if r.fair_trade:
        parts.append("Fair Trade")
    parts.extend(r.extra_tags)
    return " &middot; ".join(parts)


def tags_attr(r) -> str:
    tags = ["sparkling" if r.style == "Sparkling" else "still"]
    if r.organic:
        tags.append("organic")
    if r.fair_trade:
        tags.append("fair-trade")
    if not r.added_sugar:
        tags.append("no-sugar")
    if r.pasteurized:
        tags.append("pasteurized")
    if r.pulp:
        tags.append("pulp")
    return " ".join(tags)


def esc(s: str) -> str:
    """Escape a bare '&' that isn't already part of an HTML entity."""
    import re as _re
    return _re.sub(r"&(?!amp;|#\d+;|[a-zA-Z]+;)", "&amp;", s)


def fmt_score(v: float) -> str:
    return str(int(v)) if v == int(v) else str(v)


def fmt_overall(v: float) -> str:
    return f"{v:.1f}"


def render_review_paragraphs(text: str) -> str:
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    return "\n\n".join(f"<p>{p}</p>" for p in paras)


def brand_line(r, brands) -> str:
    """Link a review to its brand page, when Nate has reviewed that brand twice."""
    items = brands.get(r.brand) if brands else None
    if not items:
        return ""
    others = len(items) - 1
    word = "review" if others == 1 else "reviews"
    return (
        f'<p class="brand-line">See my other {others} {esc(r.brand)} '
        f'{word}: <a href="../brands/{brand_slug(r.brand)}.html">'
        f'all {esc(r.brand)} coconut water</a>.</p>'
    )


def render_review_page(r, ranked=None, brands=None) -> str:
    s = r.scores
    context = rank_context(r, ranked) if ranked else ""
    return _tpl("review.html").substitute(
        brand_line=brand_line(r, brands),
        rank_context=context,
        title=esc(f"{r.title_name} Review ({fmt_overall(s['overall'])}/10) — Nate Wooding"),
        og_title=esc(f"{r.title_name} Review ({fmt_overall(s['overall'])}/10)"),
        description=esc(r.description),
        slug=r.slug,
        image_file=Path(r.image).name,
        ld_name=esc(r.title_name),
        ld_brand=json.dumps(r.brand),
        ld_review_body=json.dumps(r.verdict),
        date=r.date,
        overall=fmt_overall(s["overall"]),
        h2_heading=esc(f"{r.brand} — {r.product}"),
        meta_line=meta_line(r),
        taste=fmt_score(s["taste"]),
        sweetness=fmt_score(s["sweetness"]),
        body=fmt_score(s["body"]),
        refreshment=fmt_score(s["refreshment"]),
        ethics=fmt_score(s["ethics"]),
        notes=render_review_paragraphs(esc(r.notes)),
        verdict=render_review_paragraphs(esc(r.verdict)),
    )


def render_review_item(r) -> str:
    return _tpl("review_item.html").substitute(
        tags=tags_attr(r),
        image_file=Path(r.image).name,
        alt=esc(r.listing_name),
        slug=r.slug,
        listing_name=esc(r.listing_name),
        item_meta=listing_meta_line(r),
        overall=fmt_overall(r.scores["overall"]),
        order=r.position,
        table_name=esc(r.table_name),
    )


def render_table_row(r) -> str:
    s = r.scores
    return _tpl("table_row.html").substitute(
        tags=tags_attr(r),
        slug=r.slug,
        table_name=esc(r.table_name),
        order=r.position,
        style=r.style,
        sugar=yn(r.added_sugar),
        pulp=yn(r.pulp),
        pasteurized=yn(r.pasteurized),
        organic=yn(r.organic),
        taste=fmt_score(s["taste"]),
        sweetness=fmt_score(s["sweetness"]),
        body=fmt_score(s["body"]),
        refreshment=fmt_score(s["refreshment"]),
        ethics=fmt_score(s["ethics"]),
        overall=fmt_overall(s["overall"]),
    )


def render_listing_page(reviews, narrower: str = "") -> str:
    items = "\n".join(render_review_item(r) for r in sorted(reviews, key=lambda r: r.position))
    rows = "".join(render_table_row(r) for r in sorted(reviews, key=lambda r: r.position))
    return _tpl("coconut-water.html").substitute(
        og_image=by_score(reviews)[0].image,
        review_items=items,
        table_rows=rows,
        brand_links=brand_links(brands_with_multiple(reviews), prefix="brands/"),
        narrower=narrower,
    )


def _pub_date(date_str: str) -> str:
    d = datetime.date.fromisoformat(date_str)
    dt = datetime.datetime(d.year, d.month, d.day, 12, 0, 0)
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


def render_feed(reviews) -> str:
    item_tpl = _tpl("feed_item.xml")
    ordered = sorted(reviews, key=lambda r: (r.date, r.order), reverse=True)
    items = "".join(
        item_tpl.substitute(
            title=esc(f"{r.listing_name} ({fmt_overall(r.scores['overall'])}/10)"),
            slug=r.slug,
            pub_date=_pub_date(r.date),
            description=esc(r.description),
        )
        for r in ordered
    )
    return _tpl("feed.xml").substitute(items=items)


def render_sitemap(reviews) -> str:
    url_tpl = _tpl("sitemap_url.xml")
    ordered = sorted(reviews, key=lambda r: (r.date, r.order or 0))
    urls = "".join(url_tpl.substitute(slug=r.slug, date=r.date) for r in ordered)
    brand_tpl = _tpl("sitemap_brand.xml")
    brand_urls = "".join(
        brand_tpl.substitute(brand_slug=brand_slug(b))
        for b in brands_with_multiple(reviews)
    )
    return _tpl("sitemap.xml").substitute(urls=urls + brand_urls)


def rank_context(r, ranked) -> str:
    """One generated line placing a review against Nate's own other scores."""
    names = [x.slug for x in ranked]
    i = names.index(r.slug)
    rank, total = i + 1, len(ranked)
    bits = [f"Ranked {ordinal(rank)} of {total} coconut waters I have scored"]
    if i > 0:
        above = ranked[i - 1]
        bits.append(
            f'below <a href="{above.slug}.html">{esc(above.table_name)}</a> '
            f'({fmt_overall(above.scores["overall"])})'
        )
    if i < total - 1:
        below = ranked[i + 1]
        bits.append(
            f'above <a href="{below.slug}.html">{esc(below.table_name)}</a> '
            f'({fmt_overall(below.scores["overall"])})'
        )
    return (
        " &middot; ".join(bits)
        + '. <a href="../best-coconut-water.html">See the full ranking</a>.'
    )


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def short_description(r) -> str:
    """The review's own description, minus the trailing score the table shows."""
    return re.sub(r"\s*Overall:\s*[\d.]+/10\.?\s*$", "", r.description)


def by_score(reviews):
    return sorted(reviews, key=lambda r: (-r.scores["overall"], r.table_name))


def render_best_page(reviews, intro: str, narrower: str = "") -> str:
    row_tpl = _tpl("rank_row.html")
    ranked = by_score(reviews)
    rows = "".join(
        row_tpl.substitute(
            rank=i,
            slug=r.slug,
            listing_name=esc(r.listing_name),
            overall=fmt_overall(r.scores["overall"]),
            taste=fmt_score(r.scores["taste"]),
            style=r.style,
            description=esc(short_description(r)),
        )
        for i, r in enumerate(ranked, start=1)
    )
    items = ",\n".join(
        "      {"
        f'"@type": "ListItem", "position": {i}, '
        f'"url": "https://natewooding.com/reviews/{r.slug}.html", '
        f'"name": {json.dumps(r.listing_name)}'
        "}"
        for i, r in enumerate(ranked, start=1)
    )
    return _tpl("best-coconut-water.html").substitute(
        og_image=ranked[0].image,
        intro=intro,
        narrower=narrower,
        rank_rows=rows,
        ld_count=len(ranked),
        ld_items=items + "\n",
    )


def render_filtered_page(spec, subset, ranked, siblings: str) -> str:
    """A ranking page restricted to one of Nate's tag fields."""
    row_tpl = _tpl("rank_row.html")
    rows = "".join(
        row_tpl.substitute(
            rank=i,
            slug=r.slug,
            listing_name=esc(r.listing_name),
            overall=fmt_overall(r.scores["overall"]),
            taste=fmt_score(r.scores["taste"]),
            style=r.style,
            description=esc(short_description(r)),
        )
        for i, r in enumerate(subset, start=1)
    )
    items = ",\n".join(
        "      {"
        f'"@type": "ListItem", "position": {i}, '
        f'"url": "https://natewooding.com/reviews/{r.slug}.html", '
        f'"name": {json.dumps(r.listing_name)}'
        "}"
        for i, r in enumerate(subset, start=1)
    )
    return _tpl("filtered-rank.html").substitute(
        slug=spec["slug"],
        h1=esc(spec["h1"]),
        description=esc(spec["description"]),
        ld_name=esc(spec["ld_name"]),
        og_image=subset[0].image,
        intro=esc(spec["intro"](subset, ranked)),
        rank_rows=rows,
        ld_count=len(subset),
        ld_items=items + "\n",
        siblings=siblings,
    )


def analytics_snippet(measurement_id: str) -> str:
    """GA4 tag, loaded async so it cannot block rendering. Empty id means no tag."""
    if not measurement_id:
        return ""
    mid = measurement_id.strip()
    if not re.fullmatch(r"G-[A-Z0-9]+", mid):
        raise ValueError(f"not a GA4 measurement id: {mid!r}")
    return (
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={mid}"></script>\n'
        "<script>window.dataLayer=window.dataLayer||[];"
        "function gtag(){dataLayer.push(arguments);}"
        'gtag("js",new Date());'
        f'gtag("config","{mid}");</script>\n'
    )


def brand_slug(brand: str) -> str:
    """URL slug for a brand name: "Trader Joe's" -> "trader-joes"."""
    s = brand.lower().replace("&", "and").replace("'", "").replace("\u2019", "")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def brands_with_multiple(reviews):
    """Brands Nate has reviewed more than once, alphabetical, each best-first."""
    groups: dict[str, list] = {}
    for r in reviews:
        groups.setdefault(r.brand, []).append(r)
    return {
        brand: sorted(items, key=lambda r: (-r.scores["overall"], r.table_name))
        for brand, items in sorted(groups.items())
        if len(items) > 1
    }


def brand_intro(brand: str, items, ranked) -> str:
    """A factual summary built only from Nate's own scores."""
    best, worst = items[0], items[-1]
    place = [x.slug for x in ranked].index(best.slug) + 1
    out = (
        f"I have bought and scored {len(items)} {esc(brand)} coconut waters, "
        f"listed best to worst by my overall score."
        f' My highest was <a href="../reviews/{best.slug}.html">{esc(best.table_name)}</a>'
        f' at {fmt_overall(best.scores["overall"])}/10, which places it '
        f"{ordinal(place)} of {len(ranked)} overall."
    )
    if worst.scores["overall"] != best.scores["overall"]:
        out += (
            f' My lowest was <a href="../reviews/{worst.slug}.html">{esc(worst.table_name)}</a>'
            f' at {fmt_overall(worst.scores["overall"])}/10.'
        )
    return out


def brand_links(brands, current: str | None = None, prefix: str = "") -> str:
    """Inline list of links to every brand page, for cross-referencing."""
    parts = []
    for brand, items in brands.items():
        label = f"{esc(brand)} ({len(items)})"
        if brand == current:
            parts.append(f"<strong>{label}</strong>")
        else:
            parts.append(f'<a href="{prefix}{brand_slug(brand)}.html">{label}</a>')
    return " &middot; ".join(parts)


def render_brand_page(brand: str, items, ranked, brands) -> str:
    row_tpl = _tpl("brand_row.html")
    rows = "".join(
        row_tpl.substitute(
            slug=r.slug,
            listing_name=esc(r.listing_name),
            overall=fmt_overall(r.scores["overall"]),
            description=esc(short_description(r)),
        )
        for r in items
    )
    heading = f"{brand} Coconut Water Reviews"
    description = (
        f"All {len(items)} {brand} coconut waters I have bought and scored, "
        f"best to worst, with my overall rating and a link to each full review."
    )
    return _tpl("brand.html").substitute(
        title=esc(f"{heading} \u2014 Nate Wooding"),
        og_title=esc(heading),
        heading=esc(heading),
        description=esc(description),
        brand_slug=brand_slug(brand),
        og_image=items[0].image,
        intro=brand_intro(brand, items, ranked),
        brand_rows=rows,
        brand_links=brand_links(brands, current=brand),
    )


BIRTHDATE = datetime.date(1999, 10, 2)


def age_today(today: datetime.date | None = None) -> int:
    today = today or datetime.date.today()
    had_birthday = (today.month, today.day) >= (BIRTHDATE.month, BIRTHDATE.day)
    return today.year - BIRTHDATE.year - (0 if had_birthday else 1)


def render_about_page() -> str:
    """The About page states Nate's age; the build fills it in and inline JS
    keeps a cached copy correct after his birthday."""
    return _tpl("about.html").substitute(age=age_today())


def render_data_page(reviews) -> str:
    import dataset
    crit = "".join(
        f"      <tr><td>{k.capitalize()}</td><td>{avg:.2f}</td><td>{fmt_score(lo)}</td>"
        f"<td>{fmt_score(hi)}</td><td>{'&mdash;' if c is None else f'{c:+.2f}'}</td></tr>\n"
        for k, avg, lo, hi, c in dataset.criterion_rows(reviews)
    )
    orig = "".join(
        f"      <tr><td>{esc(country)}</td><td>{n}</td><td>{avg:.2f}</td>"
        f'<td><a href="reviews/{best.slug}.html">{esc(best.table_name)}</a> '
        f"({fmt_overall(best.scores['overall'])})</td></tr>\n"
        for country, n, avg, best in dataset.origin_rows(reviews)
    )
    missing = sum(1 for r in reviews if not r.origin)
    note = "Origin is recorded where my review or the brand itself names it."
    if missing:
        note += f" {missing} of the {len(reviews)} reviews do not have one yet and are left out of this table."
    n = len(reviews)
    return _tpl("coconut-water-data.html").substitute(
        description=esc(
            f"Every score from the {n} coconut waters I have bought and scored, as a "
            "downloadable spreadsheet, with averages by criterion and by country of origin."
        ),
        og_image=by_score(reviews)[0].image,
        intro=esc(
            f"Every score from the {n} coconut waters I have bought and scored, in one place: "
            "six criteria each, out of 10, plus the tags on every review."
        ),
        criterion_rows=crit,
        origin_rows=orig,
        origin_note=esc(note),
    )
