#!/usr/bin/env python3
"""Submit every URL in docs/sitemap.xml to IndexNow (Bing, Yandex, Naver, Seznam...).

The key file is hosted at docs/<KEY>.txt (served at the site root);
keyLocation is passed explicitly.

Usage: python3 scripts/indexnow.py
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

KEY = "837a6a8e5b4648dc9d96db11061a8998"
DOCS = Path(__file__).resolve().parent.parent / "docs"
ENDPOINT = "https://api.indexnow.org/indexnow"


def main() -> int:
    sitemap = (DOCS / "sitemap.xml").read_text(encoding="utf-8")
    urls = re.findall(r"<loc>([^<]+)</loc>", sitemap)
    if not urls:
        print("No URLs found in sitemap.xml", file=sys.stderr)
        return 1
    base = urls[0].rstrip("/") + "/"
    payload = {
        "host": urlparse(base).netloc,
        "key": KEY,
        "keyLocation": f"{base}{KEY}.txt",
        "urlList": urls,
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"IndexNow: HTTP {resp.status} for {len(urls)} URLs")
    except urllib.error.HTTPError as e:
        print(f"IndexNow: HTTP {e.code} {e.read().decode(errors='replace')}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
