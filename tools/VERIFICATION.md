# Verification: generated pages vs. the original hand-written HTML

Produced by `tools/compare_legacy.py`, which diffs every page `build.py`
writes against the pre-generator version of that file (via `git show`),
after collapsing all whitespace runs so line-wrapping/indentation never
counts as a difference. Re-run it yourself after `python3 build.py`:

```
python3 tools/compare_legacy.py
```

## Byte-identical (after whitespace normalisation)

`index.html`, `about.html`, `style.css` — copied verbatim from `templates/`.

`reviews/c2o-original.html`, `reviews/trader-joes-organic.html`,
`reviews/zico-natural.html` — these three happened to already follow the
canonical field order/wording the generator produces, so nothing changed.

## Review pages with differences (27 of 30)

All differences fall into five categories, each a deliberate normalisation
rather than a bug:

1. **`"author"` JSON-LD formatting** (~16 pages, e.g. `blue-monkey-organic`,
   `kirkland-organic`, `moon-boo-sun`, `el-mexicano-pulp`, ...). The legacy
   pages wrote this block either as one line or across three; the
   generator always uses the three-line form. Same JSON, same rendered
   page — purely a source-formatting choice.

2. **Title / og:title / ld+json `name` no longer drops "Coconut Water"**
   (`coaqua-still`, `coaqua-sparkling`, `harmless-harvest-sparkling`,
   `real-coco-pure`). The legacy titles inconsistently shortened the
   product name (sometimes dropping "Coconut Water", sometimes not, with
   no discernible rule — see `tools/extract_legacy.py` history). The
   generator always uses the full `brand + product` name for consistency;
   this matched 24 of 30 pages exactly and left these 4 with a longer
   title/heading than before.

3. **Brand name mismatch between the old H1 heading and old ld+json name**
   (`sprouts-organic`, `sprouts-pulp`, `cocochito-pulp`,
   `vita-coco-extra-coconut`, `vita-coco-farmers-organic`,
   `vita-coco-original`, `zico-pure`). The legacy pages themselves
   disagreed about the brand's full name between the visible heading
   (e.g. "Sprouts") and the JSON-LD `name` (e.g. "Sprouts Farmers
   Market"). `content/reviews/*.md` records one `brand`/`product` pair
   per review (taken from the visible heading), so the generated
   title/og/JSON-LD/alt text now agree with each other and with the page
   heading, at the cost of matching the old JSON-LD wording exactly.

4. **"Not Organic" now shown consistently** (`simple-truth-no-pulp`,
   `trader-joes-pasteurized`, `harmless-harvest-sparkling`,
   `cocochito-pulp`, `vita-coco-extra-coconut`, and a few more). 13 of 17
   non-organic legacy pages stated "Not Organic" in the meta line; 4
   omitted it. The generator always states organic status explicitly
   (matching the majority), so those 4 pages gained the words "Not
   Organic" they previously lacked.

5. **`harmless-harvest-sparkling` meta-line tag order and one extra
   tag**: the legacy page listed `Unpasteurized` last and included a
   redundant `No Pulp` (pulp is false for every drink in this dataset
   except the three explicitly "with Pulp" products); the generator puts
   pasteurization status in a fixed position and only mentions pulp when
   `pulp = true`.

None of these differences change what a reader sees as incorrect
information — they make the wording *more* internally consistent than
the hand-written original, at the cost of textually matching it.
`maui-and-sons` also lost an over-eager `&amp;` → `&` in one earlier build
iteration; that specific issue is fixed (the generator escapes bare `&`).

## `coconut-water.html` (listing + comparison table)

69 differing chunks out of 1528 tag-lines. Same five causes as above,
applied per review (image `alt` text no longer includes "Coconut Water";
meta-line tag order/", Not Organic"; brand mismatches), plus:

- `data-tags` attribute order on `.review-item` divs is not always
  identical (e.g. `"still pasteurized organic no-sugar"` vs. the
  generator's fixed `"still organic no-sugar pasteurized"` ordering). The
  legacy markup itself used inconsistent orderings across items (checked
  directly against the original file — no two orderings agree). Since
  the site's tag-filter JavaScript matches by `.includes(tag)`/word
  boundary, not by position, this has no effect on filtering behaviour.

## `feed.xml`

59 differing chunks out of 375 tag-lines, concentrated in `<description>`
text. The legacy `feed.xml` had its own hand-written blurb per item, often
worded differently from that review's own meta description (e.g. "Costco's
store brand organic coconut water..." in the feed vs. a different sentence
on the review page). The generator uses a single `description` field per
review — taken from the review page's meta description — for both the
page and the feed item, so feed wording now matches the review page
instead of having independent, drifting copy. This is an intentional
single-source-of-truth simplification, not an oversight; the `<title>`
format for each item (`"{listing_name} ({score}/10)"`) matches the legacy
feed exactly.

## `sitemap.xml`

4 differing chunks: `reviews/el-mexicano-pulp.html` and
`reviews/moon-boo-sun.html` are adjacent entries dated 2025-06-20 and
2025-06-19 respectively, but the legacy sitemap listed them in the
*wrong* chronological order (20th before 19th) — a small error in the
original file. The generator sorts sitemap entries strictly by date, so
it swaps them into correct chronological order. Every other entry in
`sitemap.xml` matches.

## Tests

`python3 -m unittest discover -s tests` — 6 tests, all passing, covering:
required-field validation, score-range validation, image-existence
validation, duplicate-order detection, and sort-by-`order` behaviour.
