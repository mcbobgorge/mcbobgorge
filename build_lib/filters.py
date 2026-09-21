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
]


def page_subset(spec, reviews):
    return by_score([r for r in reviews if spec["predicate"](r)])
