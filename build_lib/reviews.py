"""Load and validate content/reviews/*.md review data files."""
from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

REQUIRED_FIELDS = [
    "brand", "product", "listing_name", "table_name", "date", "size",
    "style", "pasteurized", "added_sugar", "organic", "fair_trade", "pulp",
    "image", "description", "scores",
]
SCORE_KEYS = ["taste", "sweetness", "body", "refreshment", "ethics", "overall"]


class ValidationError(Exception):
    pass


@dataclass
class Review:
    slug: str
    brand: str
    product: str
    listing_name: str
    table_name: str
    order: int | None
    date: str
    size: str
    style: str
    pasteurized: bool
    added_sugar: bool
    organic: bool
    fair_trade: bool
    pulp: bool
    image: str
    description: str
    scores: dict
    extra_tags: list = field(default_factory=list)
    origin: str = ""
    notes: str = ""
    verdict: str = ""
    position: int = 0  # 1-based display position, assigned by load_all

    @property
    def title_name(self) -> str:
        """Brand + product, used for page titles/headings/ld+json name."""
        return f"{self.brand} {self.product}".strip()

    @property
    def month_year(self) -> str:
        y, m, _ = self.date.split("-")
        month = ["", "January", "February", "March", "April", "May", "June", "July",
                 "August", "September", "October", "November", "December"][int(m)]
        return f"{month} {y}"


def _parse_md(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^\+\+\+\n(.*?)\n\+\+\+\n(.*)$", text, re.S)
    if not m:
        raise ValidationError(f"{path.name}: missing +++ front matter block")
    front = tomllib.loads(m.group(1))
    return front, m.group(2)


def _section(body: str, name: str, next_name: str | None) -> str:
    if next_name:
        m = re.search(rf"##\s*{name}\s*\n(.*?)(?=\n##\s*{next_name})", body, re.S)
    else:
        m = re.search(rf"##\s*{name}\s*\n(.*)", body, re.S)
    if not m:
        raise ValidationError(f"missing ## {name} section")
    return m.group(1).strip()


def load_review(path: Path, require_image: bool = True) -> Review:
    slug = path.stem
    front, body = _parse_md(path)
    missing = [f for f in REQUIRED_FIELDS if f not in front]
    if missing:
        raise ValidationError(f"{slug}: missing required field(s): {', '.join(missing)}")
    scores = front["scores"]
    for key in SCORE_KEYS:
        if key not in scores:
            raise ValidationError(f"{slug}: missing score '{key}'")
        val = scores[key]
        if not (0 <= val <= 10):
            raise ValidationError(f"{slug}: score '{key}'={val} out of range 0-10")

    image_path = path.parent.parent.parent / front["image"]
    if require_image and not image_path.exists():
        raise ValidationError(f"{slug}: image file not found: {front['image']}")

    notes = _section(body, "Notes", "Verdict")
    verdict = _section(body, "Verdict", None)

    return Review(
        slug=slug,
        brand=front["brand"],
        product=front["product"],
        listing_name=front["listing_name"],
        table_name=front["table_name"],
        order=front.get("order"),
        date=front["date"],
        size=front["size"],
        style=front["style"],
        pasteurized=front["pasteurized"],
        added_sugar=front["added_sugar"],
        organic=front["organic"],
        fair_trade=front["fair_trade"],
        pulp=front["pulp"],
        image=front["image"],
        description=front["description"],
        scores=scores,
        extra_tags=front.get("extra_tags", []),
        origin=front.get("origin", ""),
        notes=notes,
        verdict=verdict,
    )


def load_all(reviews_dir: Path) -> list[Review]:
    paths = sorted(reviews_dir.glob("*.md"))
    paths = [p for p in paths if p.name != "_template.md"]
    if not paths:
        raise ValidationError(f"no review files found in {reviews_dir}")
    reviews = [load_review(p) for p in paths]

    slugs = [r.slug for r in reviews]
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        raise ValidationError(f"duplicate slug(s): {', '.join(sorted(dupes))}")

    orders = [r.order for r in reviews if r.order is not None]
    dupe_orders = {o for o in orders if orders.count(o) > 1}
    if dupe_orders:
        raise ValidationError(f"duplicate order value(s): {sorted(dupe_orders)}")

    # Newest first, by the date Nate tasted it. `order` only breaks ties
    # between reviews tasted on the same day, keeping the original sequence.
    ordered = sorted(
        reviews,
        key=lambda r: (r.date, -(r.order if r.order is not None else 10**6)),
        reverse=True,
    )
    for position, review in enumerate(ordered, start=1):
        review.position = position
    return ordered
