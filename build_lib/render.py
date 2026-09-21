"""Render HTML/XML pages from Review objects using templates/ (string.Template)."""
from __future__ import annotations

import datetime
from pathlib import Path
from string import Template

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def _tpl(name: str) -> Template:
    return Template((TEMPLATES / name).read_text(encoding="utf-8"))


def yn(b: bool) -> str:
    return "Yes" if b else "No"


def meta_line(r) -> str:
    parts = [r.month_year, r.size, r.style]
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


def render_review_page(r, ranked=None) -> str:
    s = r.scores
    context = rank_context(r, ranked) if ranked else ""
    return _tpl("review.html").substitute(
        rank_context=context,
        title=esc(f"{r.title_name} Review ({fmt_overall(s['overall'])}/10) — Nate Wooding"),
        og_title=esc(f"{r.title_name} Review ({fmt_overall(s['overall'])}/10)"),
        description=esc(r.description),
        slug=r.slug,
        image_file=Path(r.image).name,
        ld_name=esc(r.title_name),
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


def render_listing_page(reviews) -> str:
    items = "\n".join(render_review_item(r) for r in sorted(reviews, key=lambda r: r.position))
    rows = "".join(render_table_row(r) for r in sorted(reviews, key=lambda r: r.position))
    return _tpl("coconut-water.html").substitute(review_items=items, table_rows=rows)


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
    ordered = sorted(reviews, key=lambda r: (r.date, r.order))
    urls = "".join(url_tpl.substitute(slug=r.slug, date=r.date) for r in ordered)
    return _tpl("sitemap.xml").substitute(urls=urls)


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


def by_score(reviews):
    return sorted(reviews, key=lambda r: (-r.scores["overall"], r.table_name))


def render_best_page(reviews, intro: str) -> str:
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
            description=esc(r.description),
        )
        for i, r in enumerate(ranked, start=1)
    )
    return _tpl("best-coconut-water.html").substitute(intro=intro, rank_rows=rows)
