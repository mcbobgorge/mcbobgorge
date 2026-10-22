# Operating natewooding.com with any LLM

This document exists so Nate can run or automate this site with any capable
assistant — Claude, ChatGPT, a local model, or a human with a terminal — with no
dependency on the agent that built the main site. The main-site source is in GitHub;
the separate matcher source and local helper currently live outside that repo, as explained below.

Updated October 22, 2026. Start with the quick operating instructions below; the later sections are the technical reference.

Repo: `mcbobgorge/mcbobgorge` · default branch `main` · live at https://natewooding.com


## Quick start: what you actually do

For a normal review, send your notes, verdict, six scores and a product photo to your operator. They create one review file and add the photo. GitHub builds the pages; the rankings and CSV update automatically. The separate matcher needs a second data export and deployment.

The main site does not depend on Pion. Its files and publishing automation live at https://github.com/mcbobgorge/mcbobgorge. The matcher currently does depend on Pion; see the separate instructions below.

### Publish by email

Send the review from woodingnate@gmail.com to woody-8391@pionagent.com, with the photo attached. Say explicitly that you want it published. This is an operator-assisted route, not an automatic email-to-website service. Without Woody/Pion, give the same material to another assistant or human who can access the GitHub repo.

Include these labels, with your actual values (do not publish these placeholders):

```
Brand: [brand]
Product: [product]
Date tasted: [YYYY-MM-DD]
Size: [size on container]
Still or sparkling: [Still or Sparkling]
Pasteurized: [yes/no]
Added sugar: [yes/no]
Organic: [yes/no]
Fair trade: [yes/no]
Pulp: [yes/no]
Country of origin: [country, or omit if unknown]
Scores — Taste: [number] Sweetness: [number] Body: [number] Refreshment: [number] Ethics: [number] Overall: [number]
One-line summary: [your short listing description]
Notes: [your full notes]
Verdict: [your full verdict]
```

Put the scores on one line for the intake script. All six are out of ten. Overall is your score, not their average. Unknown required fields need clarification; origin is optional. The operator must preserve your prose, check the image and factual tags, build/test/preview, publish, re-export the matcher and verify both live sites. No assistant may invent tasting notes or scores.

### Publish in the GitHub browser

No terminal is needed for the main site. Log into GitHub as a repo owner or collaborator. Ask an LLM to format your supplied review using the schema later in this guide, or copy content/reviews/_template.md. Do not edit the template itself.

1. Prepare a real JPEG photo named `<slug>.jpg`. A slug is the short lowercase, hyphenated product name used in its URL. Prefer a 450 by 600 pixel portrait crop; changing a filename to .jpg does not convert an image.
2. Open https://github.com/mcbobgorge/mcbobgorge/tree/main/reviews/img. Choose Add file, then Upload files; upload the photo and commit to main.
3. Open https://github.com/mcbobgorge/mcbobgorge/tree/main/content/reviews. Choose Add file, then Create new file. Name it `<slug>.md`, paste the complete formatted review and commit to main. The image field must exactly match `reviews/img/<slug>.jpg`.
4. Open the repository's Actions tab. Wait for the latest Build and deploy run's deploy job to succeed. An IndexNow notification failure after deployment is different from a failed site build.
5. Open `https://natewooding.com/reviews/<slug>.html`. Check every score, paragraph, photo and tag. Check the listing and relevant rankings too.
6. Arrange the matcher re-export separately. GitHub's workflow does not update that app.

Upload the photo first to avoid a review build failing while its photo is missing. An image-only commit does not add a review. Do not rename an existing review slug: it changes a live link.

### Live pages and what updates them

- Home: https://natewooding.com/
- All Reviews, filters and comparison table: https://natewooding.com/coconut-water.html
- Full ranking, highest overall score first: https://natewooding.com/best-coconut-water.html
- Organic ranking: https://natewooding.com/best-organic-coconut-water.html
- No added sugar: https://natewooding.com/coconut-water-no-added-sugar.html
- Unpasteurized: https://natewooding.com/unpasteurized-coconut-water.html
- Thai and Vietnamese: https://natewooding.com/best-thai-coconut-water.html and https://natewooding.com/best-vietnamese-coconut-water.html
- Dataset and statistics: https://natewooding.com/coconut-water-data.html
- Public CSV: https://natewooding.com/data/ratings.csv; the older https://natewooding.com/coconut-water-scores.csv is also generated.
- Scoring explanation: https://natewooding.com/rating-guide.html
- Feed and search sitemap: https://natewooding.com/feed.xml and https://natewooding.com/sitemap.xml
- Matcher: https://match.natewooding.com/ (also https://find-coconut-water.pion.dev/).

The catalogue has 40 reviews as of this update. All rankings, brand pages, statistics and CSV rows come from the review files. The `_template.md` file is not a review. The organic, sugar, pasteurization and origin fields decide which filtered pages include a review. Brand pages appear when two reviews share the exact brand spelling. Do not edit generated HTML or CSV by hand.

### The existing publish script

Woody's current container has `~/scripts/publish_review.sh`. This helper is not in the GitHub repository and is not an email service. It assumes the site checkout is `~/site` and the matcher checkout is `~/coconut-match`.

```
~/scripts/publish_review.sh stage intake.txt prepared-photo.jpg custom-slug
```

Stage creates the review with tools/new_review.py, copies the photo, builds and runs tests/checks. It does not resize or convert the photo, preview it, or push. Prepare the JPEG beforehand; the existing crop command is:

```
ffmpeg -v quiet -y -i input.jpg -vf scale=450:600:force_original_aspect_ratio=increase,crop=450:600 -q:v 6 prepared-photo.jpg
```

Preview `_site` and inspect the proposed git changes before:

```
~/scripts/publish_review.sh push "Add Brand Product review"
```

Push reruns the tests, commits all current site changes and pushes to GitHub. It then exports matcher data, commits all changed matcher files and pushes the matcher to Pion. Because it uses `git add -A`, unrelated changes must be removed or separated first. Push does not itself rerun the site build/link checker or test the matcher. Run those checks before invoking it. If the matcher step fails after the GitHub push, the review may already be live: fix the matcher separately, do not blindly repeat the whole publish command. Watch GitHub Actions and verify both sites afterward.

### Re-export the matcher data

The matcher is a separate SvelteKit app. Its repo is the internal Pion repo `coconut-match`, currently checked out at `~/coconut-match`, with remote named `andon`. There is no confirmed GitHub matcher repo. Its source instructions are in AGENTS.md; some generic database/webhook instructions in that file are platform scaffolding, not features used by the quiz.

```
cd ~/coconut-match
python3 tools_export.py
pnpm run check
pnpm run build
# Inspect git diff, then commit only the intended generated files:
git add src/lib/reviews.json src/lib/flavour-tags.json
git commit -m "Sync matcher data after new review"
git push andon main
```

If the export changes nothing, there is no data commit to make. The exporter reads review source from `~/site` (a hardcoded path), not the live CSV. Keep that checkout current and only export approved, published reviews. It writes src/lib/reviews.json and src/lib/flavour-tags.json. Never hand-edit those generated files.

flavours.json is the separately maintained evidence map. A new review can be exported without flavour tags. Add tags only when the exact affirmative phrase appears in Nate's review; the exporter checks quoted evidence and stops on mismatches. It must never invent a flavour. The quiz links full reviews with `utm_source=match&utm_medium=quiz` so the main site's GA4 can identify referrals. It remains unlinked from the main site's navigation by Nate's direction.

Without Pion, the main site still publishes normally through GitHub. To operate the matcher independently, first obtain an export of the coconut-match source (including package/lock files, tools_export.py, flavours.json and src/). Its current deployment command is Pion-specific. A replacement static host and SvelteKit static-output configuration must be prepared and tested before switching DNS; this migration is not already implemented. Simply pushing the main GitHub repo does not move or update the matcher.

### Analytics: GA4 and Search Console

Nate manages the Google accounts directly. Open https://analytics.google.com/ and select the natewooding.com GA4 property. The installed measurement ID is `G-GHB7P7N0ML`, stored in content/site.toml as ga_measurement_id. The build adds it to generated pages. Clearing that setting disables the tag on the next deployment. This is not a measurement of visitors to the matcher itself.

For the weekly visitor goal, select a consistent seven-day date range and record the Users metric with the dates and the exact metric label. Do not substitute page views or a 28-day total. Use acquisition reports to compare traffic sources; matcher referrals use source match and medium quiz. Realtime can help check a visit, but consent, blockers and reporting delays mean one missing visit does not prove the site is broken.

Open https://search.google.com/search-console/ and select the verified natewooding.com property. Performance shows search clicks, impressions, click-through rate and queries, not all visitors. URL Inspection checks a specific live review and its indexing status; requesting indexing is not a guarantee. The sitemap is https://natewooding.com/sitemap.xml and is rebuilt automatically. Check the Sitemaps report before resubmitting; do not create duplicate properties to solve a reporting delay. The operator has no direct Google analytics access established; Nate can supply dated reports without sharing passwords.

### DNS at Squarespace

Squarespace manages the domain records; it is not serving the review site. In your Squarespace Domains account, open natewooding.com, then its DNS settings. Before editing, save a copy of every existing record. The following were confirmed in Nate's screenshot when configured, not freshly re-verified on October 22:

- A, host `@`, value `185.199.108.153`
- A, host `@`, value `185.199.109.153`
- A, host `@`, value `185.199.110.153`
- A, host `@`, value `185.199.111.153`
- CNAME, host `www`, value `mcbobgorge.github.io`
- CNAME, host `match`, value `apps.pion.dev`
- TXT, host `_cf-custom-hostname.match`, value `fed8038b-1db2-4185-92c4-1e3d7e3cf62f`
- Search Console verification CNAME, host `crshzriid3gt`, value `gv-wj2weodi4wc3ks.dv.googlehosted.com`

The screenshot also contained TXT `mailo._domainkey` (email DKIM) and Squarespace email-forwarding MX/SPF records. Their full values are not recorded here. Preserve them exactly; they are unrelated to review publishing and removing them can break email. Do not replace the whole DNS zone with this partial list. No ordinary review requires a DNS change.

In GitHub repository Settings, Pages, the custom domain is natewooding.com; the repo's CNAME file contains that name. The intended publishing Source is GitHub Actions. A legacy branch-source setting has previously been noted despite artifact deployments, so inspect actual settings if deployment breaks; do not switch hosting casually. Leave HTTPS enforcement enabled when available. Changing the matcher host requires the replacement host's own verification instructions, not blindly copying the current Pion TXT record. DNS and certificate changes can take time; retain the old working host until the replacement is verified.

### Copy-paste prompt for an LLM without Pion

```
Help me operate natewooding.com using GitHub, not Pion. First read
LLM_OPERATOR_GUIDE.md, README.md and any AGENTS.md in
https://github.com/mcbobgorge/mcbobgorge, plus the current review template
and .github/workflows/deploy.yml. Confirm the branch and current files.
Use GitHub's browser or a local HTTPS checkout with Python 3.11+.
Do not ask me to paste passwords or tokens into chat; use my environment's
secure login/credential mechanism. If you cannot access tools, give me
exact file contents and browser steps rather than claim you published.

Task: [insert what I want done, and whether publication is authorized]
Review material and photo: [attach my actual text, scores and image]

I alone supply tasting notes, verdicts and all six scores. Preserve them.
Never invent missing facts, origins, tasting methodology or scores.
Overall is my judgment, not an average. No prices/value claims, affiliates,
sponsored reviews or flavoured products. Keep the site barebones: white,
#111 text, system sans body, Playfair headings/scores, 900px maximum width.
Ask about missing required facts. Edit source data/templates, not generated
HTML. Never rename an existing slug. Before publishing, inspect the diff,
build with python3 build.py --out _site, run python3 -m unittest discover
-s tests and python3 tools/check_site.py _site, then preview the review,
photo, scores and links in a browser. If using GitHub browser only, let
Actions do the checks and verify the live page after deployment.
Get my approval before any live content change unless this task explicitly
authorizes that exact publication. No spending or brand/social outreach.

Commit approved files, verify the GitHub deploy job and live URLs, and
report what actually succeeded and any remaining blocker. The matcher is
separate: its coconut-match repo currently lives on Pion, not this GitHub
repo. Do not pretend to update it without its exported source and hosting
access. Explain that limitation and the separate data export needed.
```

---

## 1. Architecture in one page

A static site generated by a single Python script. No frameworks, no database,
no Node, no dependencies beyond the Python standard library (3.11+; GitHub uses 3.12).

```
content/reviews/<slug>.md   one file per review: TOML front matter + Notes + Verdict
content/site.toml           site title, url, description, intro copy, GA4 id
reviews/img/<slug>.jpg      one photo per review (committed to the repo)
build.py                    the entry point; regenerates all HTML
build_lib/reviews.py        loads and VALIDATES the data files
build_lib/render.py         turns reviews into HTML using templates/
build_lib/filters.py        defines the filtered ranking pages
templates/*.html            plain string templates (string.Template, $placeholders)
templates/rating-guide.html Nate's scoring rubric, verbatim — edit only with his words
tools/new_review.py         converts a loose text block into a data file
build_lib/dataset.py        the CSV download and the statistics on the data page
tools/check_site.py         link/metadata checker, run against the built site
tests/                      unittest suite
.github/workflows/deploy.yml  builds and publishes on every push to main
```

**The data files are the only source of truth.** Every page — the homepage, the
ranking, the per-brand pages, the filtered rankings, the RSS feed, the sitemap,
the structured data — is derived from `content/reviews/*.md`. Never hand-edit
generated HTML; it will be overwritten on the next build.

Two commands matter:

```bash
python3 build.py              # regenerate the HTML in the repo
python3 build.py --out _site  # also stage a clean publishable copy in _site/
```

Deployment is automatic: push to `main`, and the GitHub Action builds, runs the
tests, runs the link checker, and publishes. It takes roughly one to two
minutes. If any step fails, **nothing is published and the live site keeps
serving the previous version** — a failed build normally leaves the previous deployment in place. Successful deployment does not prove the content is correct.

---

## 2. The one rule that matters more than the code

**Nate writes all reviews, notes, verdicts and scores. An assistant must never
invent them.**

Do not write tasting language. Do not guess a score. Do not describe how
something tastes, smells or feels. Do not invent a verdict to fill a gap. Do not
claim anything about his tasting method or process — he has never claimed to use
the same glass every time, or any other ritual, and saying so would be a
fabrication published under his name.

What an assistant may write: statements derived arithmetically from his own
numbers and flags. Rank position, score ranges, how many products qualify for
something, which brands have multiple reviews, neighbouring scores. These are
facts about his data, not opinions about coconut water.

If a submission is missing a field, ask him. Never fill it in.

Two further standing constraints, both his decisions:

- **No prices.** No price field, no price-per-ounce, no value-for-money metric,
  anywhere. Prices vary too much by retailer and region to be honest.
- **No flavoured products.** Plain, unflavoured coconut water only. Chocolate,
  mango and coffee versions are out of scope. ("Roasted" is ambiguous — roasted
  coconuts pressed into plain water may be in scope; ask him.)

---

## 3. The schema

Front matter sits between `+++` lines and is TOML. Body sections are markdown-ish
HTML: `## Notes` and `## Verdict` are both required.

```
+++
brand = "Brand Name"
product = "Full Product Name Coconut Water"
listing_name = "Brand — Short Name"
table_name = "Brand Short Name"
date = "2026-01-01"
size = "16.9 fl oz (500 mL)"
style = "Still"
origin = "Thailand"
pasteurized = true
added_sugar = false
organic = true
fair_trade = false
pulp = false
extra_tags = []
image = "reviews/img/brand-slug.jpg"
description = "One or two sentences summarizing the review."
scores = { taste = 5, sweetness = 5, body = 5, refreshment = 5, ethics = 5, overall = 5 }
+++

## Notes

One or more paragraphs, blank line between them. Inline HTML links are allowed.

## Verdict

The closing paragraph of the review page.
```

### Required fields

All of these must be present or the build fails:
`brand`, `product`, `listing_name`, `table_name`, `date`, `size`, `style`,
`pasteurized`, `added_sugar`, `organic`, `fair_trade`, `pulp`, `image`,
`description`, `scores`.

### Field reference

| Field | Type | Rules and gotchas |
|---|---|---|
| `brand` | string | **Spelling is load-bearing.** Two reviews sharing a `brand` automatically create `brands/<slug>.html`. "Vita Coco" and "VitaCoco" become two different brands. Zico and Zico Pure are deliberately both `"Zico"`. |
| `product` | string | The product name without the brand. Page titles use `brand + product`. |
| `listing_name` | string | Short label for listings, rankings and RSS. Em dash between brand and product reads best. |
| `table_name` | string | Shorter still, for the narrow comparison table column. |
| `date` | string | **`YYYY-MM-DD`, quoted.** Not a TOML date literal. Drives ordering (newest first) and the "Month Year" line. |
| `size` | string | As printed on the container, e.g. `"16.9 fl oz (500 mL)"`. |
| `style` | string | `"Still"` or `"Sparkling"`. |
| `pasteurized` | bool | `false` puts it on the unpasteurized ranking. |
| `added_sugar` | bool | `false` puts it on the no-added-sugar ranking. |
| `organic` | bool | `true` puts it on the organic ranking. |
| `fair_trade` | bool | Shown as a tag; no page of its own yet. |
| `pulp` | bool | Whether it contains pulp. |
| `origin` | string | **Optional.** Country the coconuts come from, e.g. `"Thailand"`. Only fill it when the carton, the brand, or Nate says so — never infer it from the brand. Drives the Thai and Vietnamese ranking pages and the origin table. Spell countries consistently. |
| `extra_tags` | list | Optional free-text tags, e.g. `["single-origin"]`. Use `[]` if none. |
| `image` | string | Path **relative to the repo root**, normally `reviews/img/<slug>.jpg`. The file must exist or the build fails. |
| `description` | string | One or two sentences. Used in listings, social previews and RSS. Aim for 50+ characters; the checker rejects short meta descriptions. |
| `scores` | inline table | All six keys required: `taste`, `sweetness`, `body`, `refreshment`, `ethics`, `overall`. Each **0–10**, integers or decimals. `overall` is Nate's own judgement, not a computed average — never recalculate it. |
| `order` | int | Legacy only. Breaks ties within a single date. Do not add it to new reviews. |

### Slug rules

The filename is the slug: `content/reviews/<slug>.md` becomes
`https://natewooding.com/reviews/<slug>.html`.

- lowercase, hyphen-separated, ASCII, no spaces
- derived from brand + product, e.g. `harmless-harvest-original`
- must be unique; duplicate slugs fail the build
- **never rename an existing slug** — it is a live URL that people and search
  engines have; renaming breaks it silently

---

## 4. Prompt for turning Nate's text into a data file

Give an assistant this, along with his raw submission.

> You are formatting a coconut water review for natewooding.com. Convert the
> submission below into a single data file.
>
> Output only the file contents: a TOML front matter block between `+++` lines,
> then `## Notes`, then `## Verdict`. No commentary, no code fence.
>
> Required front matter fields, in this order: brand, product, listing_name,
> table_name, date, size, style, pasteurized, added_sugar, organic, fair_trade,
> pulp, extra_tags, image, description, scores.
>
> Rules:
> - Copy his notes and verdict across **verbatim**. Preserve paragraph breaks.
>   Fix nothing but obvious typos. Do not rewrite, tighten, or improve his prose.
> - Never invent a score, a tasting note, a verdict, or a description of taste.
>   If any of the six scores or any required field is missing from the
>   submission, stop and list exactly what is missing. Do not guess or infer.
> - `date` must be `"YYYY-MM-DD"` as a quoted string.
> - All six scores are required and must be between 0 and 10. `overall` is his
>   own number, not an average — never compute it.
> - Booleans are bare `true`/`false`, not strings.
> - `image` must be `"reviews/img/<slug>.jpg"` using the slug below.
> - `description` is one or two factual sentences for listings and previews, at
>   least 50 characters. Base it only on what he wrote.
> - Never include price, cost, or value-for-money anywhere.
> - Use the exact brand spelling he used; it groups the brand pages.
>
> Slug to use: `<lowercase-hyphenated-brand-product>`
>
> Submission:
> <paste Nate's text here>

There is also a script that does this without an LLM, and it is more reliable
because it validates as it goes:

```bash
python3 tools/new_review.py submission.txt
python3 tools/new_review.py submission.txt --slug custom-slug
```

It accepts loose input: labels with colons or dashes (`Pasteurized - yes`), and
scores with or without punctuation (`taste 7, sweetness 6, body 6, ...`). It
refuses to guess at unlabelled values, and when a field is missing it names the
exact line to add. See `PUBLISHING.md` for the submission format.

---

## 5. Publishing, step by step

### With a terminal

```bash
git clone https://github.com/mcbobgorge/mcbobgorge.git
cd mcbobgorge

# 1. add the data file and the photo
#    content/reviews/<slug>.md
#    reviews/img/<slug>.jpg

# 2. build
python3 build.py --out _site

# 3. test — both must pass before pushing
python3 -m unittest discover -s tests
python3 tools/check_site.py _site

# 4. preview it and check the review, photo, scores and links
cd _site && python3 -m http.server 8099   # then open http://localhost:8099

# 5. ship
git add -A
git commit -m "Add <brand> <product> review"
git push
```

Wait one to two minutes, then confirm the deploy succeeded — the Actions tab on
GitHub, or `gh run list -R mcbobgorge/mcbobgorge --limit 2`. Then load the live
page in a browser. Browsers cache aggressively; if it looks stale, hard-refresh
or append `?x=1`.

### Without a terminal, through the GitHub website

Prefer the photo-first browser instructions in Quick start. The alternative ordering below can temporarily fail the build until both commits are present.

This works, and it is the fallback if no assistant has code access.

1. Go to `content/reviews/` in the repo, click **Add file → Create new file**.
2. Name it `<slug>.md` and paste the full file contents.
3. Commit directly to `main`.
4. Go to `reviews/img/`, click **Add file → Upload files**, upload a JPEG photo
   named exactly `<slug>.jpg`, commit.
5. Open the **Actions** tab and watch the run. Confirm the deploy job succeeded, then open the live review.

Do both commits close together. A data file whose photo is missing fails the
build until the photo lands — harmless, but nothing publishes until then.

---

## 6. Verification checklist and edge cases

The build validates a lot by itself. `python3 -m unittest discover -s tests`
and `python3 tools/check_site.py _site` between them catch:

- missing or malformed front matter, missing required fields
- a score outside 0–10, or a missing score key
- a missing `## Notes` or `## Verdict` section
- duplicate slugs
- an `image` path pointing at a file that does not exist
- broken internal links, pages without exactly one `<h1>`, missing `<title>`
- a meta description under 50 characters
- a social preview image that is off-site or missing
- filtered ranking pages disagreeing with the review data

Things no check will catch, so they need human eyes:

| Edge case | What happens |
|---|---|
| Brand spelled inconsistently | Silently creates a second brand page. Grep `content/reviews/` for the brand before adding. |
| Wrong boolean | Publishes a factual error about sugar or pasteurization and silently moves the review between filtered rankings. Check against the label. |
| Slug renamed | The old URL 404s forever. Never rename. |
| `overall` recomputed as an average | Misrepresents his judgement. It is his own number. |
| Date in the future or wrong year | Silently reorders the listing, which is newest-first. |
| Photo of the wrong product | Nothing will flag it. Look at the page. |
| Photo not committed | Build fails; live site unaffected. Add the photo. |

A quick sanity check after any change:

```bash
python3 -c "
import sys; sys.path.insert(0, 'build_lib')
from reviews import load_all
from pathlib import Path
rs = load_all(Path('content/reviews'))
print(len(rs), 'reviews')
for r in sorted(rs, key=lambda r: -r.scores['overall'])[:3]:
    print(' ', r.listing_name, r.scores['overall'])
"
```

---

## 7. Design constraints for anyone changing the site

The plainness is deliberate and it is the point. It signals that the data is the
product.

- Playfair Display for headings and scores, system sans-serif for body text
- black `#111` on white, 900px maximum width
- the site name is a small `.masthead` link; the page's subject is the single
  `h1.page-title`
- no frameworks, no build tooling, no JavaScript beyond a ~15-line sort control
  and the contact-link assembler
- no gradients, no hero sections, no decorative emoji, no uppercase micro-labels
- the nav is four items: Home, Best Coconut Water, All Reviews, About. Resist
  adding more; other pages are reached by links in the body.

Analytics: GA4, id in `content/site.toml` as `ga_measurement_id`. Leave it empty
and no tag is emitted anywhere. That is the off switch.

---

## 8. Adding a new filtered ranking page

The organic, no-added-sugar, unpasteurized, Thai and Vietnamese pages are
generated from tag fields. To add another:

1. append a spec to `PAGES` in `build_lib/filters.py` (slug, h1, description,
   ld_name, a `predicate` lambda over a review, and an `intro` builder)
2. add a `<url>` line to `templates/sitemap.xml`

Publishing and the cross-links are generated from `PAGES` automatically.
Country pages are one line each: `_origin_page("Brazil", "Brazilian")`.

Intro text must be generated from his scores and flags. A ranking needs enough
entries to be worth publishing — fair trade was left out at four.

---

## 9. If something breaks

- **Deploy failed.** Read the Actions log. The failing step names the problem;
  validation errors quote the slug and field. A failed build normally leaves the previous deployment in place.
- **A page looks stale.** Browser cache. Hard-refresh or append `?x=1`.
- **A review vanished from a ranking.** Check whether a boolean or origin changed. Check the front matter.
- **Everything looks wrong after editing HTML.** Generated files are overwritten
  by `build.py`. Edit the templates or the data, never the output.
- **Rolling back.** `git revert <commit>` and push. The next build republishes
  the previous state.

- **Main site works but matcher is stale.** Check that the current site checkout was re-exported and the separate coconut-match deployment succeeded. A main-site deploy cannot update it.
- **IndexNow job is red but deploy is green.** The search notification failed after publishing. Verify the live site and retry the notification; do not treat it as proof the pages failed to deploy.
- **Domain or HTTPS fails.** Check GitHub Pages status/custom domain and the existing Squarespace records. For matcher-only failure, check the Pion route/certificate. Do not delete email or verification records or change nameservers as a first fix.
- **Google shows no fresh data.** Check the selected property, date range and tag setting; allow reporting time. Search indexing and analytics are different systems.
- **Rollback after a bad review.** Revert only the offending source commit, rebuild, test, preview and push; if matcher data changed, re-export and deploy it too. Reverting the main repo does not roll back the matcher.
