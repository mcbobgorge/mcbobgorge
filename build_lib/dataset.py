"""Nate's scores as a downloadable table, plus plain statistics over them.

Everything here is arithmetic on his own numbers and flags. It states patterns;
it never explains them.
"""
import csv
import io
from statistics import mean

CRITERIA = ["taste", "sweetness", "body", "refreshment", "ethics"]
CSV_COLUMNS = [
    "slug", "brand", "product", "date", "origin", "size", "style", "pasteurized",
    "added_sugar", "organic", "fair_trade", "pulp",
    "taste", "sweetness", "body", "refreshment", "ethics", "overall", "url",
]


def csv_text(reviews) -> str:
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\n")
    w.writerow(CSV_COLUMNS)
    for r in sorted(reviews, key=lambda r: (-r.scores["overall"], r.slug)):
        flags = [r.pasteurized, r.added_sugar, r.organic, r.fair_trade, r.pulp]
        w.writerow(
            [r.slug, r.brand, r.product, r.date, r.origin, r.size, r.style]
            + ["yes" if f else "no" for f in flags]
            + [r.scores[k] for k in CRITERIA + ["overall"]]
            + [f"https://natewooding.com/reviews/{r.slug}.html"]
        )
    return out.getvalue()


def correlation(xs, ys) -> float:
    mx, my = mean(xs), mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else 0.0


def criterion_rows(reviews):
    """(criterion, average, lowest, highest, correlation with overall or None)."""
    overall = [r.scores["overall"] for r in reviews]
    rows = []
    for k in CRITERIA + ["overall"]:
        vals = [r.scores[k] for r in reviews]
        corr = None if k == "overall" else correlation(vals, overall)
        rows.append((k, mean(vals), min(vals), max(vals), corr))
    return rows


def origin_rows(reviews):
    """(country, count, average overall, best review), most-reviewed first."""
    groups = {}
    for r in reviews:
        if r.origin:
            groups.setdefault(r.origin, []).append(r)
    rows = []
    for country, items in groups.items():
        best = max(items, key=lambda r: r.scores["overall"])
        rows.append((country, len(items), mean(r.scores["overall"] for r in items), best))
    return sorted(rows, key=lambda row: (-row[1], row[0]))
