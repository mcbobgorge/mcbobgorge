# natewooding.com

Read README.md, LLM_OPERATOR_GUIDE.md and PUBLISHING.md before editing.
Nate alone supplies notes, verdicts and scores; preserve his prose and never
infer missing facts. Do not add prices, affiliates or invented flavours.
Design changes require owner approval.

## Layout and conventions

- `content/reviews/*.md`: TOML front matter plus Notes / Verdict; `_template.md`
  is excluded. Add JPEG photos to `reviews/img/`. Never rename existing slugs.
- `build_lib/`: standard-library-only Python loading, validation and rendering.
- `templates/`: plain string.Template HTML/XML. Edit sources, not generated pages.
- `tools/new_review.py`: email intake; `tools/check_site.py`: output checks.
- `tests/`: unittest behaviour tests. No new dependency for ordinary site work.
- `pasteurized`: optional boolean, missing means unknown (`None`). Only explicit
  false qualifies as unpasteurized. CSV unknown is blank.

## Run and verify

Python 3.11+, no installation needed:

```sh
python3 build.py --out _site
python3 -m unittest discover -s tests
python3 tools/check_site.py _site
python3 -m http.server 8099 --directory _site
```

Inspect the diff and preview review, photo, scores, table and relevant rankings
in a browser before publishing. Build rewrites tracked generated outputs as well
as `_site` (ignored). Preserve other operators' changes.

## Deployment

Nate has authorized publishing complete reviews he supplies straight away;
other live changes (design, structure) need his approval. Push to `main` in
`mcbobgorge/mcbobgorge` triggers GitHub Actions Pages deployment; verify the job
and live pages. The old matcher (match.natewooding.com) is retired: do not
export to it or link it. See LLM_OPERATOR_GUIDE.md for operations and rollback.
