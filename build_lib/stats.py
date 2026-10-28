"""The statistics page: charts and tables computed from Nate's scores at build time.

Like dataset.py, everything here is arithmetic on his own numbers and tags. It
states patterns; it never explains them. Charts are plain inline SVG, so the page
needs no script and updates whenever a review is added and the site is rebuilt.
Hovering a mark shows the reviews behind it (an SVG <title>).
"""
from __future__ import annotations

import datetime
from html import escape
from statistics import mean, median, pstdev

from dataset import CRITERIA, correlation

ALL = CRITERIA + ["overall"]
INK = "#111"
MUTED = "#666"
RULE = "#ddd"
FONT = "font-family=\"-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif\""


def f1(v: float) -> str:
    return f"{v:.1f}"


def f2(v: float) -> str:
    return f"{v:.2f}"


def name(r) -> str:
    return escape(r.table_name)


def link(r, prefix: str = "") -> str:
    return f'<a href="{prefix}reviews/{r.slug}.html">{name(r)}</a>'


def names_title(items) -> str:
    return escape("\n".join(f"{r.table_name}: {f1(r.scores['overall'])}" for r in items))


def _svg(w: int, h: int, body: str, label: str, css: str = "chart") -> str:
    return (
        f'<svg class="{css}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}" {FONT}>'
        f"{body}</svg>"
    )


# ---- headline figures -------------------------------------------------------

def headline(reviews) -> list[tuple[str, str]]:
    overall = [r.scores["overall"] for r in reviews]
    dates = sorted(r.date for r in reviews)
    return [
        ("Coconut waters scored", str(len(reviews))),
        ("Average overall", f2(mean(overall))),
        ("Median overall", f1(median(overall))),
        ("Standard deviation", f2(pstdev(overall))),
        ("Highest overall", f1(max(overall))),
        ("Lowest overall", f1(min(overall))),
        ("First tasted", _long_date(dates[0])),
        ("Latest tasted", _long_date(dates[-1])),
    ]


def _long_date(d: str) -> str:
    dt = datetime.date.fromisoformat(d)
    return f"{dt.strftime('%B')} {dt.day}, {dt.year}"


def render_headline(reviews) -> str:
    tiles = "".join(
        f'<div class="stat"><div class="stat-num">{v}</div><div class="stat-label">{k}</div></div>'
        for k, v in headline(reviews)
    )
    return f'<div class="stat-grid">{tiles}</div>'


# ---- histogram of overall scores --------------------------------------------

def overall_bins(reviews):
    """Ten one-point bins, 0-0.9 ... 9-10 (a 10 goes in the last bin)."""
    bins = [[] for _ in range(10)]
    for r in reviews:
        bins[min(int(r.scores["overall"]), 9)].append(r)
    return bins


def render_histogram(reviews) -> str:
    bins = overall_bins(reviews)
    w, h, left, right, top, bottom = 600, 230, 30, 10, 20, 34
    pw, ph = w - left - right, h - top - bottom
    peak = max(len(b) for b in bins) or 1
    step = pw / 10
    out = []
    for t in range(0, peak + 1, max(1, (peak + 4) // 5)):
        y = top + ph - ph * t / peak
        out.append(f'<line x1="{left}" x2="{w - right}" y1="{y:.1f}" y2="{y:.1f}" stroke="#eee"/>')
        out.append(f'<text x="{left - 6}" y="{y + 4:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">{t}</text>')
    for i, b in enumerate(bins):
        x = left + i * step + 3
        bh = ph * len(b) / peak
        y = top + ph - bh
        label = f"{i}&#8211;{i + 1}" if i == 9 else f"{i}&#8211;{i}.9"
        if b:
            out.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{step - 6:.1f}" height="{bh:.1f}" fill="{INK}">'
                f"<title>{len(b)} scored {i} to {i + 1 if i == 9 else f'{i}.9'}\n{names_title(b)}</title></rect>"
            )
            out.append(f'<text x="{x + (step - 6) / 2:.1f}" y="{y - 5:.1f}" font-size="11" fill="{INK}" text-anchor="middle">{len(b)}</text>')
        out.append(f'<text x="{x + (step - 6) / 2:.1f}" y="{h - bottom + 16}" font-size="11" fill="{MUTED}" text-anchor="middle">{label}</text>')
    out.append(f'<line x1="{left}" x2="{w - right}" y1="{top + ph}" y2="{top + ph}" stroke="{INK}"/>')
    out.append(f'<text x="{left + pw / 2:.1f}" y="{h - 2}" font-size="11" fill="{MUTED}" text-anchor="middle">Overall score</text>')
    return _svg(w, h, "".join(out), "Histogram of overall scores", "chart hist")


# ---- how often each criterion score is given --------------------------------

def criterion_counts(reviews, k):
    """Count of reviews at each whole score 1-10 (a score below 1 counts as 1)."""
    counts = [0] * 10
    for r in reviews:
        counts[min(max(int(r.scores[k]), 1), 10) - 1] += 1
    return counts


def render_count_table(reviews) -> str:
    head = "".join(f"<th class=\"sc\">{i}</th>" for i in range(1, 11))
    rows = []
    n = len(reviews)
    for k in CRITERIA:
        counts = criterion_counts(reviews, k)
        cells = []
        for i, c in enumerate(counts, start=1):
            share = c / n
            items = [r for r in reviews if min(max(int(r.scores[k]), 1), 10) == i]
            bg = f"rgba(17,17,17,{min(share * 2.2, 0.85):.2f})" if c else "transparent"
            fg = "#fff" if share * 2.2 > 0.45 else INK
            title = f' title="{names_title(items)}"' if items else ""
            cells.append(f'<td class="sc heat" style="background:{bg};color:{fg}"{title}>{c or ""}</td>')
        avg = mean(r.scores[k] for r in reviews)
        rows.append(f"<tr><td>{k.capitalize()}</td>{''.join(cells)}<td class=\"sc\">{f2(avg)}</td></tr>")
    return (
        '<div class="table-wrap"><table class="compare heat-table">'
        f"<thead><tr><th>Criterion</th>{head}<th class=\"sc\">Average</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


# ---- each criterion against overall ------------------------------------------

def fit(xs, ys):
    """Least-squares line (slope, intercept)."""
    mx, my = mean(xs), mean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0
    return slope, my - slope * mx


def render_scatter(reviews, k) -> str:
    w = h = 220
    left, bottom, top, right = 28, 28, 10, 10
    pw, ph = w - left - right, h - top - bottom
    sx = lambda v: left + pw * v / 10  # noqa: E731
    sy = lambda v: top + ph - ph * v / 10  # noqa: E731
    out = []
    for t in (0, 5, 10):
        out.append(f'<line x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="{top}" y2="{top + ph}" stroke="#eee"/>')
        out.append(f'<line x1="{left}" x2="{left + pw}" y1="{sy(t):.1f}" y2="{sy(t):.1f}" stroke="#eee"/>')
        out.append(f'<text x="{sx(t):.1f}" y="{h - bottom + 14}" font-size="10" fill="{MUTED}" text-anchor="middle">{t}</text>')
        out.append(f'<text x="{left - 5}" y="{sy(t) + 3:.1f}" font-size="10" fill="{MUTED}" text-anchor="end">{t}</text>')
    out.append(f'<text x="{left + pw / 2:.1f}" y="{h - 3}" font-size="10" fill="{MUTED}" text-anchor="middle">{k.capitalize()}</text>')
    xs = [r.scores[k] for r in reviews]
    ys = [r.scores["overall"] for r in reviews]
    slope, icept = fit(xs, ys)
    x0, x1 = min(xs), max(xs)
    out.append(
        f'<line x1="{sx(x0):.1f}" y1="{sy(slope * x0 + icept):.1f}" x2="{sx(x1):.1f}" y2="{sy(slope * x1 + icept):.1f}" '
        f'stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="4 3"/>'
    )
    groups = {}
    for r in reviews:
        groups.setdefault((r.scores[k], r.scores["overall"]), []).append(r)
    for (x, y), items in sorted(groups.items()):
        out.append(
            f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="{4 + (len(items) - 1) * 1.5:.1f}" fill="{INK}" fill-opacity="0.55" '
            f'stroke="#fff" stroke-width="1"><title>{k.capitalize()} {x:g}, overall {f1(y)}\n'
            f"{escape(chr(10).join(r.table_name for r in items))}</title></circle>"
        )
    return _svg(w, h, "".join(out), f"{k.capitalize()} score against overall score", "chart scatter")


def render_scatters(reviews) -> str:
    overall = [r.scores["overall"] for r in reviews]
    panels = []
    for k in CRITERIA:
        r = correlation([x.scores[k] for x in reviews], overall)
        panels.append(
            f'<figure class="panel"><figcaption>{k.capitalize()} &middot; r = {r:+.2f}</figcaption>'
            f"{render_scatter(reviews, k)}</figure>"
        )
    return f'<div class="panels">{"".join(panels)}</div>'


# ---- correlation matrix ------------------------------------------------------

def correlation_matrix(reviews):
    cols = {k: [r.scores[k] for r in reviews] for k in ALL}
    return [[correlation(cols[a], cols[b]) for b in ALL] for a in ALL]


def render_matrix(reviews) -> str:
    m = correlation_matrix(reviews)
    head = "".join(f'<th class="sc">{k.capitalize()}</th>' for k in ALL)
    rows = []
    for i, a in enumerate(ALL):
        cells = []
        for j, v in enumerate(m[i]):
            if i == j:
                cells.append('<td class="sc heat" style="color:#999">&mdash;</td>')
                continue
            shade = min(abs(v), 1) * 0.8
            fg = "#fff" if shade > 0.4 else INK
            cells.append(f'<td class="sc heat" style="background:rgba(17,17,17,{shade:.2f});color:{fg}">{v:+.2f}</td>')
        rows.append(f"<tr><td>{a.capitalize()}</td>{''.join(cells)}</tr>")
    return (
        '<div class="table-wrap"><table class="compare heat-table">'
        f"<thead><tr><th></th>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )


# ---- overall score by group (tags, origin, brand) ----------------------------

def tag_groups(reviews):
    """[(section, [(label, reviews), ...])] for every tag on a review."""
    def split(attr, labels):
        out = []
        for value, label in labels:
            items = [r for r in reviews if getattr(r, attr) is value]
            if items:
                out.append((label, items))
        return out

    yes_no = lambda yes, no: [(True, yes), (False, no)]  # noqa: E731
    style = [(s, [r for r in reviews if r.style == s]) for s in ("Still", "Sparkling")]
    return [
        ("Organic", split("organic", yes_no("USDA Organic", "Not organic"))),
        ("Added sugar", split("added_sugar", yes_no("Added sugar", "No added sugar"))),
        ("Pasteurization", split("pasteurized", yes_no("Pasteurized", "Unpasteurized") + [(None, "Unknown")])),
        ("Pulp", split("pulp", yes_no("Pulp", "No pulp"))),
        ("Fair trade", split("fair_trade", yes_no("Fair Trade", "Not fair trade"))),
        ("Style", [(s, items) for s, items in style if items]),
    ]


def origin_groups(reviews):
    groups = {}
    for r in reviews:
        groups.setdefault(r.origin or "Not recorded", []).append(r)
    known = sorted(
        ((k, v) for k, v in groups.items() if k != "Not recorded"),
        key=lambda kv: (-len(kv[1]), kv[0]),
    )
    return known + ([("Not recorded", groups["Not recorded"])] if "Not recorded" in groups else [])


def brand_groups(reviews):
    groups = {}
    for r in reviews:
        groups.setdefault(r.brand, []).append(r)
    multi = [(b, items) for b, items in groups.items() if len(items) > 1]
    return sorted(multi, key=lambda kv: (-mean(r.scores["overall"] for r in kv[1]), kv[0]))


STRIP_W, STRIP_H, STRIP_PAD = 260, 22, 8


def _strip_x(v: float) -> float:
    return STRIP_PAD + (STRIP_W - 2 * STRIP_PAD) * v / 10


def render_strip(items) -> str:
    """Every review in the group as a dot on a 0-10 line, the group average as a tick."""
    mid = STRIP_H / 2
    out = [f'<line x1="{STRIP_PAD}" x2="{STRIP_W - STRIP_PAD}" y1="{mid}" y2="{mid}" stroke="{RULE}"/>']
    for r in sorted(items, key=lambda r: r.scores["overall"]):
        out.append(
            f'<circle cx="{_strip_x(r.scores["overall"]):.1f}" cy="{mid}" r="4.5" fill="{INK}" fill-opacity="0.4">'
            f"<title>{names_title([r])}</title></circle>"
        )
    avg = mean(r.scores["overall"] for r in items)
    out.append(
        f'<line x1="{_strip_x(avg):.1f}" x2="{_strip_x(avg):.1f}" y1="2" y2="{STRIP_H - 2}" stroke="{INK}" stroke-width="2.5">'
        f"<title>Average {f2(avg)}</title></line>"
    )
    return _svg(STRIP_W, STRIP_H, "".join(out), "Overall scores in this group", "strip")


def strip_axis() -> str:
    ticks = "".join(
        f'<text x="{_strip_x(t):.1f}" y="12" font-size="10" fill="{MUTED}" text-anchor="middle">{t}</text>'
        for t in range(0, 11, 2)
    )
    return _svg(STRIP_W, 16, ticks, "Overall score axis, 0 to 10", "strip")


def render_group_table(groups, first_col: str, sections: bool = False) -> str:
    """groups: [(label, reviews)] or, with sections, [(section, [(label, reviews)])]."""
    head = (
        f"<thead><tr><th>{first_col}</th><th class=\"sc\">Reviews</th><th class=\"sc\">Average</th>"
        f"<th class=\"sc\">Median</th><th class=\"strip-col\">{strip_axis()}</th><th>Highest scored</th></tr></thead>"
    )

    def row(label, items):
        best = max(items, key=lambda r: (r.scores["overall"], r.table_name))
        overall = [r.scores["overall"] for r in items]
        return (
            f"<tr><td>{escape(label)}</td><td class=\"sc\">{len(items)}</td>"
            f"<td class=\"sc\">{f2(mean(overall))}</td><td class=\"sc\">{f1(median(overall))}</td>"
            f"<td class=\"strip-col\">{render_strip(items)}</td>"
            f"<td>{link(best)} ({f1(best.scores['overall'])})</td></tr>"
        )

    body = []
    if sections:
        for section, rows in groups:
            body.append(f'<tr class="group-head"><td colspan="6">{escape(section)}</td></tr>')
            body.extend(row(label, items) for label, items in rows)
    else:
        body.extend(row(label, items) for label, items in groups)
    return f'<div class="table-wrap"><table class="compare groups">{head}<tbody>{"".join(body)}</tbody></table></div>'


# ---- over time ---------------------------------------------------------------

def by_date(reviews):
    return sorted(reviews, key=lambda r: (r.date, -(r.order if r.order is not None else 10**6)))


def running_mean(reviews):
    out, total = [], 0.0
    for i, r in enumerate(by_date(reviews), start=1):
        total += r.scores["overall"]
        out.append((r, total / i))
    return out


def render_timeline(reviews) -> str:
    w, h, left, right, top, bottom = 760, 250, 30, 12, 12, 30
    pw, ph = w - left - right, h - top - bottom
    ordered = by_date(reviews)
    d0 = datetime.date.fromisoformat(ordered[0].date).replace(day=1)
    last = datetime.date.fromisoformat(ordered[-1].date)
    d1 = (last.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    span = (d1 - d0).days or 1
    sx = lambda d: left + pw * (datetime.date.fromisoformat(d) - d0).days / span  # noqa: E731
    sy = lambda v: top + ph - ph * v / 10  # noqa: E731
    out = []
    for t in range(0, 11, 2):
        out.append(f'<line x1="{left}" x2="{w - right}" y1="{sy(t):.1f}" y2="{sy(t):.1f}" stroke="#eee"/>')
        out.append(f'<text x="{left - 6}" y="{sy(t) + 4:.1f}" font-size="11" fill="{MUTED}" text-anchor="end">{t}</text>')
    m = d0
    while m <= d1:
        x = sx(m.isoformat())
        out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{top}" y2="{top + ph}" stroke="#eee"/>')
        if m < d1:
            nxt = (m.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
            mx = (x + sx(nxt.isoformat())) / 2
            out.append(f'<text x="{mx:.1f}" y="{h - bottom + 16}" font-size="11" fill="{MUTED}" text-anchor="middle">{m.strftime("%b %Y")}</text>')
        m = (m.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    pts = " ".join(f"{sx(r.date):.1f},{sy(avg):.1f}" for r, avg in running_mean(reviews))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{MUTED}" stroke-width="2"/>')
    groups = {}
    for r in ordered:
        groups.setdefault((r.date, r.scores["overall"]), []).append(r)
    for (d, v), items in groups.items():
        out.append(
            f'<circle cx="{sx(d):.1f}" cy="{sy(v):.1f}" r="{4.5 + (len(items) - 1) * 1.5:.1f}" fill="{INK}" fill-opacity="0.55" stroke="#fff">'
            f"<title>{_long_date(d)}\n{names_title(items)}</title></circle>"
        )
    return _svg(w, h, "".join(out), "Overall score by date tasted, with the running average")


def month_rows(reviews):
    """(month label, count, average overall, best review), oldest month first."""
    groups = {}
    for r in by_date(reviews):
        groups.setdefault(r.date[:7], []).append(r)
    rows = []
    for ym, items in groups.items():
        label = datetime.date.fromisoformat(ym + "-01").strftime("%B %Y")
        best = max(items, key=lambda r: (r.scores["overall"], r.table_name))
        rows.append((label, len(items), mean(r.scores["overall"] for r in items), best))
    return rows


def render_month_table(reviews) -> str:
    peak = max(n for _, n, _, _ in month_rows(reviews))
    rows = "".join(
        f"<tr><td>{label}</td><td class=\"nowrap\"><span class=\"bar\" style=\"width:{60 * n / peak:.0f}px\"></span> {n}</td>"
        f"<td class=\"sc\">{f2(avg)}</td><td>{link(best)} ({f1(best.scores['overall'])})</td></tr>"
        for label, n, avg, best in month_rows(reviews)
    )
    return (
        '<div class="table-wrap"><table class="compare">'
        '<thead><tr><th>Month tasted</th><th>Reviews</th><th class="sc">Average overall</th><th>Highest scored</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></div>"
    )


# ---- extremes ----------------------------------------------------------------

def extremes(reviews, k):
    """(highest value, reviews at it, lowest value, reviews at it)."""
    vals = [r.scores[k] for r in reviews]
    hi, lo = max(vals), min(vals)
    pick = lambda v: sorted((r for r in reviews if r.scores[k] == v), key=lambda r: r.table_name)  # noqa: E731
    return hi, pick(hi), lo, pick(lo)


def _who(items, limit=2) -> str:
    shown = ", ".join(link(r) for r in items[:limit])
    more = len(items) - limit
    return shown + (f" and {more} more" if more > 0 else "")


def render_extremes(reviews) -> str:
    fmt = lambda k, v: f1(v) if k == "overall" else f"{v:g}"  # noqa: E731
    rows = []
    for k in ALL:
        hi, his, lo, los = extremes(reviews, k)
        rows.append(
            f"<tr><td>{k.capitalize()}</td><td class=\"sc\">{fmt(k, hi)}</td><td>{_who(his)}</td>"
            f"<td class=\"sc\">{fmt(k, lo)}</td><td>{_who(los)}</td></tr>"
        )
    return (
        '<div class="table-wrap"><table class="compare">'
        '<thead><tr><th>Criterion</th><th class="sc">Highest</th><th>Given to</th>'
        '<th class="sc">Lowest</th><th>Given to</th></tr></thead>'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )
