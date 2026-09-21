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
