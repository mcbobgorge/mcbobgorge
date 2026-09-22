# Publishing a new coconut water review

You don't need to touch any HTML. Follow these steps:

1. **Copy the template.**
   Duplicate `content/reviews/_template.md` and rename the copy to a short
   slug for the product, e.g. `content/reviews/my-brand-still.md`. The slug
   becomes the review's URL: `reviews/my-brand-still.html`.

2. **Fill in the fields** at the top of the file, between the `+++` lines.
   Every field is explained by the `_template.md` example. A couple of notes:
   - There is no ordering to worry about: a new review goes to the top of
     the list automatically. (The `order` field you'll see in the older
     files just pins the order the site was originally published in. Leave
     it out of new ones.)
   - `date` is the review's publish date, `YYYY-MM-DD`.
   - The `scores` line takes numbers from 0 to 10.
   - Booleans (`pasteurized`, `added_sugar`, `organic`, `fair_trade`, `pulp`)
     are `true` or `false`, lowercase, no quotes.

3. **Write the review** under `## Notes` and `## Verdict`. Separate
   paragraphs with a blank line. You can use a plain HTML link if you want
   one, e.g. `<a href="https://example.com">their website</a>`.

4. **Add the photo.** Save it under `reviews/img/` (e.g.
   `reviews/img/my-brand-still.jpg`) and set the `image` field in the
   front matter to match, e.g. `image = "reviews/img/my-brand-still.jpg"`.

5. **Commit and push** the new `.md` file and the new photo.
   `git add content/reviews/my-brand-still.md reviews/img/my-brand-still.jpg`
   `git commit -m "Add My Brand Still review"`
   `git push`

That's it. Pushing to `main` triggers the GitHub Action in
`.github/workflows/deploy.yml`, which runs `python3 build.py` to regenerate
the review page, the listing page, the comparison table, the RSS feed, and
the sitemap, then publishes the result to natewooding.com.

## What your tags do

Three of the true/false fields put the review on extra pages automatically.
You don't have to do anything; just set them accurately.

- `organic = true` adds it to **The Best Organic Coconut Water**
- `added_sugar = false` adds it to **Coconut Water With No Added Sugar**
- `pasteurized = false` adds it to **Unpasteurized Coconut Water**

Each of those pages ranks its entries by overall score and opens with a
sentence built from the numbers (how many qualify, the highest and lowest).
So a new review can change that opening sentence and reshuffle the order.
That is expected.

The `brand` field works the same way: the second review of a brand creates
`brands/<brand>.html` by itself, and if a brand drops back to one review the
page disappears. Spelling matters here — "Vita Coco" and "VitaCoco" would
become two different brands.

If a tag is wrong, fix the field and push; every page that used it updates.

## Worked example

```
+++
brand = "Coco Nova"
product = "Coco Nova Pure Coconut Water"
listing_name = "Coco Nova — Pure"
table_name = "Coco Nova Pure"
date = "2026-02-14"
size = "17 fl oz (500 mL)"
style = "Still"
pasteurized = true
added_sugar = false
organic = true
fair_trade = false
pulp = false
extra_tags = ["From Concentrate"]
image = "reviews/img/coco-nova-pure.jpg"
description = "A newcomer with a clean, mild taste and a fair price."
scores = { taste = 7, sweetness = 6, body = 6, refreshment = 7, ethics = 5, overall = 6.4 }
+++

## Notes

Coco Nova showed up at the local grocery store this month, and it's
surprisingly solid for the price. Mild sweetness, clean finish, nothing
offensive.

## Verdict

A dependable everyday option. Not the best I've had, but a fine choice
if it's what's on the shelf. Overall: 6.4/10.
```

## What happens if a field is wrong

Before publishing anything, the build runs a check on every review file.
If something is missing or malformed — a required field left out, a score
outside 0–10, or a typo in `image` pointing at a photo that doesn't exist
— the build stops with a clear error
message naming the file and the problem, and the site is **not**
published. Nothing on the live site breaks; fix the file, commit again,
and the Action will retry.

## If you email the review to Woody

If you send the review to Woody via email as a plain-text block, he can
convert it directly to a review file with `tools/new_review.py`:

```
python3 tools/new_review.py < email-excerpt.txt
```

Or with a filename:

```
python3 tools/new_review.py email-excerpt.txt
```

The script expects the review in this format (order doesn't matter, field
names are case-insensitive):

```
Brand: Brand Name
Product: Product Name
Date tasted: 2026-09-18
Size: 16.9 fl oz (500 mL)
Still or sparkling: Still
Pasteurized: yes
Added sugar: no
Organic: true
Fair trade: false
Pulp: false
Scores — Taste: 7  Sweetness: 5  Body: 6  Refreshment: 8  Ethics: 4  Overall: 6.5
One-line summary: A short description for the listing and preview.
Notes: Multi-paragraph notes. Separate with a blank line.

Another paragraph here.
Verdict: Final thoughts.
```

### You don't have to be neat about it

That block is the tidy version. These all work too:

- A dash instead of a colon: `Pasteurized - yes`
- Scores with no punctuation, on their own line, in any order:
  `taste 7, sweetness 5, body 6, refreshment 8, ethics 4, overall 6.5`
- Yes/no written as yes, no, y, n, true or false

What it will *not* do is guess. A bare `16.9oz` with no `Size:` label in front
of it is an error, not an assumption — a wrong size on a published review is
worse than one question over email. If a required field is missing, the error
names the exact line to add.

One thing to know: a field label written with a dash used to be dropped
silently, which could publish the opposite of what you meant about
pasteurization. That is fixed and tested, but it is the reason the tool now
prefers to fail loudly rather than carry on.

The script will:
- Validate all required fields
- Derive the slug from brand + product (unless you pass `--slug custom-slug`)
- Generate the `.md` file in `content/reviews/`
- Check that all scores are in range (0–10) and required fields are present
- Refuse to overwrite an existing file unless you pass `--force`

You can also override the derived names:
```
python3 tools/new_review.py email.txt --listing-name "Brand — Short Form" --table-name "Brand Short"
```

After the file is written, place the photo at the path shown (e.g.
`reviews/img/goya-coconut-water.jpg`), then commit and push both files.
