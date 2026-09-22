"""Filtered ranking pages, built from tag fields Nate already records.

Every word on these pages comes from his own scores and flags. Nothing here
describes how anything tastes.
"""

from render import by_score, ordinal, fmt_overall


def _positions(subset, ranked):
    index = {r.slug: i for i, r in enumerate(ranked, start=1)}
    return [index[r.slug] for r in subset]


def _range_line(subset):
    top, bottom = subset[0], subset[-1]
    if top.slug == bottom.slug:
        return f"The only one is {top.listing_name} at {fmt_overall(top.scores['overall'])}/10."
    return (
        f"The highest is {top.listing_name} at {fmt_overall(top.scores['overall'])}/10; "
        f"the lowest is {bottom.listing_name} at {fmt_overall(bottom.scores['overall'])}/10."
    )


def _placings_line(subset, ranked):
    spots = sorted(_positions(subset, ranked))
    if len(spots) > 8:
        return ""
    worded = [ordinal(n) for n in spots]
    joined = ", ".join(worded[:-1]) + f" and {worded[-1]}"
    return f" Among all {len(ranked)} they placed {joined}."


def organic_intro(subset, ranked):
    return (
        f"{len(subset)} of the {len(ranked)} coconut waters I have bought and scored are "
        "labelled organic. This page ranks just those by my overall score. "
        + _range_line(subset)
    )


def no_sugar_intro(subset, ranked):
    return (
        f"{len(subset)} of the {len(ranked)} coconut waters I have bought and scored have "
        "no added sugar. This page ranks just those by my overall score. "
        + _range_line(subset)
    )


def unpasteurized_intro(subset, ranked):
    return (
        f"{len(subset)} of the {len(ranked)} coconut waters I have bought and scored are "
        "unpasteurized. This page ranks just those by my overall score. "
        + _range_line(subset)
        + _placings_line(subset, ranked)
    )


def _origin_count_line(ranked):
    missing = sum(1 for r in ranked if not r.origin)
    if not missing:
        return ""
    return (
        f" Origin is recorded where my review or the brand itself names it; "
        f"{missing} of the {len(ranked)} reviews do not have one yet."
    )


def origin_intro(country, adjective):
    def intro(subset, ranked):
        return (
            f"I have scored {len(subset)} coconut waters from {country}. This page ranks "
            f"just the {adjective} ones by my overall score. "
            + _range_line(subset)
            + _placings_line(subset, ranked)
            + _origin_count_line(ranked)
        )
    return intro


def _origin_page(country, adjective):
    return {
        "slug": f"best-{adjective.lower()}-coconut-water",
        "h1": f"The Best {adjective} Coconut Water",
        "description": (
            f"Every coconut water from {country} that I have bought and scored, ranked best "
            "to worst by overall score, with a one-line verdict and a link to each review."
        ),
        "ld_name": f"{adjective} coconut waters I have bought and scored, ranked",
        "predicate": lambda r, c=country: r.origin == c,
        "intro": origin_intro(country, adjective),
    }


PAGES = [
    {
        "slug": "best-organic-coconut-water",
        "h1": "The Best Organic Coconut Water",
        "description": (
            "Every organic coconut water I have bought and scored, ranked best to worst by "
            "overall score, with a one-line verdict on each and a link to the full review."
        ),
        "ld_name": "Organic coconut waters I have bought and scored, ranked",
        "predicate": lambda r: r.organic,
        "intro": organic_intro,
    },
    {
        "slug": "coconut-water-no-added-sugar",
        "h1": "Coconut Water With No Added Sugar",
        "description": (
            "Every coconut water with no added sugar that I have bought and scored, ranked "
            "best to worst by overall score, with a one-line verdict and a link to each review."
        ),
        "ld_name": "Coconut waters with no added sugar that I have bought and scored, ranked",
        "predicate": lambda r: not r.added_sugar,
        "intro": no_sugar_intro,
    },
    {
        "slug": "unpasteurized-coconut-water",
        "h1": "Unpasteurized Coconut Water",
        "description": (
            "Every unpasteurized coconut water I have bought and scored, ranked by overall "
            "score, and how they placed against the pasteurized ones."
        ),
        "ld_name": "Unpasteurized coconut waters I have bought and scored, ranked",
        "predicate": lambda r: not r.pasteurized,
        "intro": unpasteurized_intro,
    },
    _origin_page("Thailand", "Thai"),
    _origin_page("Vietnam", "Vietnamese"),
]


def page_subset(spec, reviews):
    return by_score([r for r in reviews if spec["predicate"](r)])


def narrower_links():
    """The link line on the full ranking and the listing, generated so no page is missed."""
    return " ".join(f'<a href="{p["slug"]}.html">{p["h1"]}</a>.' for p in PAGES)
