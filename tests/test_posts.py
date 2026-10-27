import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build_lib"))

import posts  # noqa: E402
import render  # noqa: E402
from reviews import ValidationError, load_all as load_reviews  # noqa: E402


def write_post(root: Path, slug: str, front: str, body: str = "Some words.") -> Path:
    path = root / "content" / "posts" / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"+++\n{front}\n+++\n\n{body}\n", encoding="utf-8")
    return path


class LoadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def load(self):
        return posts.load_all(self.root / "content" / "posts", self.root)

    def test_newest_first_and_template_skipped(self):
        write_post(self.root, "older", 'title = "Older"\ndate = "2026-01-02"')
        write_post(self.root, "newer", 'title = "Newer"\ndate = "2026-03-04"')
        write_post(self.root, "_template", 'title = "T"\ndate = "2026-12-31"')
        self.assertEqual([p.slug for p in self.load()], ["newer", "older"])

    def test_no_posts_is_fine(self):
        (self.root / "content" / "posts").mkdir(parents=True)
        self.assertEqual(self.load(), [])

    def test_missing_title_fails(self):
        write_post(self.root, "x", 'date = "2026-01-02"')
        with self.assertRaisesRegex(ValidationError, "title"):
            self.load()

    def test_bad_date_fails(self):
        write_post(self.root, "x", 'title = "X"\ndate = "Oct 2"')
        with self.assertRaisesRegex(ValidationError, "YYYY-MM-DD"):
            self.load()

    def test_unknown_field_fails(self):
        write_post(self.root, "x", 'title = "X"\ndate = "2026-01-02"\nscore = 9')
        with self.assertRaisesRegex(ValidationError, "unknown"):
            self.load()

    def test_bad_slug_fails(self):
        write_post(self.root, "Bad_Name", 'title = "X"\ndate = "2026-01-02"')
        with self.assertRaisesRegex(ValidationError, "lowercase"):
            self.load()

    def test_missing_and_oversized_images_fail(self):
        write_post(self.root, "x", 'title = "X"\ndate = "2026-01-02"', "![a](img/x-1.jpg)")
        with self.assertRaisesRegex(ValidationError, "not found"):
            self.load()
        img = self.root / "blog" / "img" / "x-1.jpg"
        img.parent.mkdir(parents=True)
        img.write_bytes(b"0" * (posts.MAX_IMAGE_BYTES + 1))
        with self.assertRaisesRegex(ValidationError, "resize"):
            self.load()
        img.write_bytes(b"0" * 10)
        self.assertEqual(self.load()[0].image, "blog/img/x-1.jpg")


class BodyTest(unittest.TestCase):
    def test_blocks(self):
        out = posts.body_html(
            "# Big\n\n### Small\n\nA *b* **c** [d](https://e.com) & <f>\nnext line\n\n"
            "- one\n- two\n\n1. first\n\n> quoted\n\n---\n\n"
            '![Alt](img/a.jpg "Cap")\n![B](img/b.jpg)\n\n<iframe src="x"></iframe>'
        )
        self.assertIn("<h2>Big</h2>", out)
        self.assertIn("<h3>Small</h3>", out)
        self.assertNotIn("<h1>", out)
        self.assertIn("<em>b</em> <strong>c</strong>", out)
        self.assertIn('<a href="https://e.com" target="_blank" rel="noopener">d</a>', out)
        self.assertIn("&amp; &lt;f&gt;<br>\nnext line", out)
        self.assertIn("<ul><li>one</li><li>two</li></ul>", out)
        self.assertIn("<ol><li>first</li></ol>", out)
        self.assertIn("<blockquote><p>quoted</p></blockquote>", out)
        self.assertIn("<hr>", out)
        self.assertIn('<img class="post-img" src="img/a.jpg" alt="Alt"><figcaption>Cap</figcaption>', out)
        self.assertIn('src="img/b.jpg" alt="B" loading="lazy">', out)
        self.assertIn('<iframe src="x"></iframe>', out)

    def test_summary_uses_the_posts_own_words(self):
        p = posts.Post("s", "T", "2026-01-02", "## Head\n\n![x](img/x.jpg)\n\n" + "word " * 60)
        s = posts.summary(p)
        self.assertTrue(s.startswith("word word"))
        self.assertLessEqual(len(s), 156)
        p.description = "Given."
        self.assertEqual(posts.summary(p), "Given.")


class SiteTest(unittest.TestCase):
    def setUp(self):
        self.reviews = load_reviews(ROOT / "content" / "reviews")
        self.post = posts.Post("a-walk", "A Walk & a Talk", "2099-01-01", "Hello there, this is a walk.")

    def test_feed_and_sitemap_include_posts(self):
        feed = render.render_feed(self.reviews, [self.post])
        first = feed.index("<item>")
        self.assertIn("https://natewooding.com/blog/a-walk.html", feed[first:first + 300])
        self.assertIn("A Walk &amp; a Talk", feed)
        self.assertIn("blog/a-walk.html</loc><lastmod>2099-01-01", render.render_sitemap(self.reviews, [self.post]))

    def test_no_posts_leaves_feed_unchanged(self):
        self.assertEqual(render.render_feed(self.reviews), render.render_feed(self.reviews, []))

    def test_home_lists_posts_and_post_page_renders(self):
        home = render.render_home_page([self.post])
        self.assertIn('href="blog/a-walk.html">A Walk &amp; a Talk</a>', home)
        self.assertIn("No posts yet", render.render_home_page([]))
        page = render.render_post_page(self.post)
        self.assertIn('<h1 class="page-title">A Walk &amp; a Talk</h1>', page)
        self.assertIn("January 1, 2099", page)
        self.assertIn('"@type": "BlogPosting"', page)
        self.assertIn("https://natewooding.com/wooding-pond.jpg", page)

    def test_every_page_has_the_three_tabs(self):
        for name in ["index.html", "post.html", "about.html", "review.html", "best-coconut-water.html", "404.html"]:
            html = (ROOT / "templates" / name).read_text(encoding="utf-8")
            nav = html[html.index("<nav>"):html.index("</nav>")]
            labels = [part.split("<")[0] for part in nav.split(">")[2::2]]
            self.assertEqual(labels, ["Blog", "About", "Coconut Water"], name)


if __name__ == "__main__":
    unittest.main()
