"""Print the IndexNow submission body for every URL in the built sitemap."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def payload(site_dir: Path) -> dict:
    key = (ROOT / "content" / "indexnow-key").read_text().strip()
    urls = re.findall(r"<loc>([^<]+)</loc>", (site_dir / "sitemap.xml").read_text())
    return {
        "host": "natewooding.com",
        "key": key,
        "keyLocation": f"https://natewooding.com/{key}.txt",
        "urlList": urls,
    }


if __name__ == "__main__":
    print(json.dumps(payload(ROOT / sys.argv[1])))
