"""Load and validate content/posts/*.md blog posts, and turn their bodies into HTML.

A post is TOML front matter between +++ lines, then the body in a small subset
of Markdown (see body_html). Nate writes every word; this module only formats.
"""
from __future__ import annotations

import datetime
import html
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from reviews import ValidationError

REQUIRED_FIELDS = ["title", "date"]
OPTIONAL_FIELDS = ["subtitle", "description", "image"]
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
# Posts get shared on Reddit; a phone photo straight off the camera is 3-5 MB.
MAX_IMAGE_BYTES = 1_000_000
IMAGE_LINE = re.compile(r'^!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)$')
FOOTNOTE_DEF = re.compile(r"^\[\^([\w-]+)\]:\s*(.*)$")
FOOTNOTE_REF = re.compile(r"\[\^([\w-]+)\]")


@dataclass
class Post:
    slug: str
    title: str
    date: str
    body: str
    subtitle: str = ""  # a one-line dek under the title, only if Nate wrote one
    description: str = ""
    image: str = ""  # path relative to the repo root, used for the share preview

    @property
    def long_date(self) -> str:
        d = datetime.date.fromisoformat(self.date)
        return f"{d.strftime('%B')} {d.day}, {d.year}"


def _parse_md(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^\+\+\+\n(.*?)\n\+\+\+\n(.*)$", text, re.S)
    if not m:
        raise ValidationError(f"{path.name}: missing +++ front matter block")
    try:
        front = tomllib.loads(m.group(1))
    except tomllib.TOMLDecodeError as e:
        raise ValidationError(f"{path.name}: front matter is not valid TOML: {e}") from e
    return front, m.group(2).strip()


def body_images(body: str) -> list[str]:
    """Image paths (relative to blog/) used on their own line in a post body."""
    return [m.group(2) for line in body.splitlines() if (m := IMAGE_LINE.match(line.strip()))]


def load_post(path: Path, root: Path) -> Post:
    slug = path.stem
    if not SLUG.match(slug):
        raise ValidationError(f"{path.name}: file name must be lowercase-words-with-hyphens")
    front, body = _parse_md(path)
    missing = [f for f in REQUIRED_FIELDS if not front.get(f)]
    if missing:
        raise ValidationError(f"{slug}: missing required field(s): {', '.join(missing)}")
    unknown = set(front) - set(REQUIRED_FIELDS) - set(OPTIONAL_FIELDS)
    if unknown:
        raise ValidationError(f"{slug}: unknown field(s): {', '.join(sorted(unknown))}")
    date = front["date"]
    if isinstance(date, datetime.date):
        date = date.isoformat()
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        raise ValidationError(f"{slug}: date must be YYYY-MM-DD, got {date!r}") from None
    if not body:
        raise ValidationError(f"{slug}: the post has no body text")

    images = [f"blog/{src}" for src in body_images(body) if not src.startswith("http")]
    if front.get("image"):
        images.append(front["image"])
    for rel in images:
        file = root / rel
        if not file.exists():
            raise ValidationError(f"{slug}: image file not found: {rel}")
        if file.stat().st_size > MAX_IMAGE_BYTES:
            raise ValidationError(
                f"{slug}: {rel} is {file.stat().st_size // 1000} KB; resize it to "
                f"about 1600px wide so it is under {MAX_IMAGE_BYTES // 1000} KB"
            )

    return Post(
        slug=slug,
        title=front["title"],
        date=date,
        body=body,
        subtitle=front.get("subtitle", ""),
        description=front.get("description", ""),
        image=front.get("image") or (images[0] if images else ""),
    )


def load_all(posts_dir: Path, root: Path) -> list[Post]:
    """Every post, newest first. No posts at all is fine."""
    paths = [p for p in sorted(posts_dir.glob("*.md")) if not p.name.startswith("_")]
    posts = [load_post(p, root) for p in paths]
    return sorted(posts, key=lambda p: (p.date, p.slug), reverse=True)


# --- Markdown subset -------------------------------------------------------

def _inline(text: str) -> str:
    """Escape, then links, bold and italics. Nothing else is interpreted."""
    out = html.escape(text, quote=False)
    out = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        lambda m: f'<a href="{html.escape(m.group(2))}"'
        + (' target="_blank" rel="noopener"' if m.group(2).startswith("http") else "")
        + f">{m.group(1)}</a>",
        out,
    )
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", out)
    return out


def _figure(m: re.Match, eager: bool) -> str:
    alt, src, caption = m.group(1), m.group(2), m.group(3)
    loading = "" if eager else ' loading="lazy"'
    img = f'<img class="post-img" src="{html.escape(src)}" alt="{html.escape(alt)}"{loading}>'
    if caption:
        return f"<figure>{img}<figcaption>{_inline(caption)}</figcaption></figure>"
    return f"<figure>{img}</figure>"


def body_html(body: str) -> str:
    """Render a post body. Blocks are separated by a blank line:

    ## Heading / ### Smaller heading   (a single # is also an h2: the title is the h1)
    ![alt text](img/photo.jpg "optional caption")   one image per line
    - item / 1. item                  lists
    > quoted text                     block quote
    ---                               a horizontal rule
    <...>                             raw HTML, passed through (e.g. a video embed)
    anything else                     a paragraph; **bold**, *italic*, [link](url)
    text[^1] ... [^1]: the note        footnotes, numbered in order and listed at the end
    """
    body, notes = _split_footnotes(body)
    out = _blocks(body)
    if notes:
        out.append(_footnotes_html(body, notes))
    return "\n".join(out)


def _split_footnotes(body: str) -> tuple[str, dict]:
    notes, kept = {}, []
    for line in body.splitlines():
        m = FOOTNOTE_DEF.match(line.strip())
        if m:
            notes[m.group(1)] = m.group(2).strip()
        else:
            kept.append(line)
    return "\n".join(kept), notes


def _ref(m: re.Match, seen: dict) -> str:
    key = m.group(1)
    seen[key] = seen.get(key, 0) + 1
    rid = f"fnref-{key}" + (f"-{seen[key]}" if seen[key] > 1 else "")
    return f'<sup class="fnref"><a href="#fn-{key}" id="{rid}">{key}</a></sup>'


def _footnotes_html(body: str, notes: dict) -> str:
    used = list(dict.fromkeys(FOOTNOTE_REF.findall(body)))
    order = used + [k for k in notes if k not in used]
    items = "".join(
        f'<li id="fn-{k}" value="{k}">{_inline(notes[k])} '
        f'<a href="#fnref-{k}" class="fnback" aria-label="Back to the text">&#8617;</a></li>'
        if k in used else f'<li id="fn-{k}" value="{k}">{_inline(notes[k])}</li>'
        for k in order if k in notes
    )
    return f'<section class="footnotes"><ol>{items}</ol></section>'


def _blocks(body: str) -> list[str]:
    _seen: dict = {}
    blocks = re.split(r"\n\s*\n", body.strip())
    out = []
    first_image = True
    for block in blocks:
        lines = [l.rstrip() for l in block.strip("\n").splitlines()]
        first = lines[0].strip()
        if first.startswith("<") and lines[-1].strip().endswith(">"):
            out.append(block.strip())
        elif m := re.match(r"^(#{1,3})\s+(.*)$", first):
            level = 3 if len(m.group(1)) == 3 else 2
            out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            if len(lines) > 1:
                out.append(f"<p>{_inline(' '.join(l.strip() for l in lines[1:]))}</p>")
        elif re.fullmatch(r"-{3,}|\*{3,}", first) and len(lines) == 1:
            out.append("<hr>")
        elif all(IMAGE_LINE.match(l.strip()) for l in lines):
            for l in lines:
                out.append(_figure(IMAGE_LINE.match(l.strip()), first_image))
                first_image = False
        elif all(re.match(r"^\s*[-*]\s+", l) for l in lines):
            items = "".join(f"<li>{_inline(re.sub(r'^\s*[-*]\s+', '', l))}</li>" for l in lines)
            out.append(f"<ul>{items}</ul>")
        elif all(re.match(r"^\s*\d+[.)]\s+", l) for l in lines):
            items = "".join(f"<li>{_inline(re.sub(r'^\s*\d+[.)]\s+', '', l))}</li>" for l in lines)
            out.append(f"<ol>{items}</ol>")
        elif all(l.lstrip().startswith(">") for l in lines):
            inner = "\n".join(re.sub(r"^\s*>\s?", "", l) for l in lines)
            out.append("<blockquote>" + "\n".join(_blocks(inner)) + "</blockquote>")
        else:
            out.append("<p>" + "<br>\n".join(_inline(l.strip()) for l in lines) + "</p>")
    return [FOOTNOTE_REF.sub(lambda m: _ref(m, _seen), b) for b in out]


def plain_text(body: str) -> str:
    """The post's words without markup, for a fallback meta description."""
    words = []
    for block in re.split(r"\n\s*\n", body.strip()):
        first = block.strip()
        if first.startswith(("<", "#", "!", "---")):
            continue
        if FOOTNOTE_DEF.match(first):
            continue
        text = FOOTNOTE_REF.sub("", block)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"[*>]|^\s*(?:-|\d+[.)])\s+", "", text, flags=re.M)
        words.extend(text.split())
    return " ".join(words)


def summary(post: Post, limit: int = 155) -> str:
    """The description, else the subtitle, else the opening words of the post itself."""
    if post.description or post.subtitle:
        return post.description or post.subtitle
    text = plain_text(post.body)
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(",;:")
    return cut + "…"
