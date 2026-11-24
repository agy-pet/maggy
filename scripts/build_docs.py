#!/usr/bin/env python3
"""Generate static per-locale landing pages and multilingual sitemap.xml.

Reads docs/index.html (English source) and scripts/locales.json, then writes:
  - docs/<slug>/index.html for each non-English locale
  - docs/sitemap.xml with hreflang alternates for all locales
  - docs/llms.txt, docs/llms-full.txt and docs/index.md for AI agents (from README.md)
  - docs/install.sh, a copy of install.sh served at the site root
and keeps the JSON-LD softwareVersion in docs/index.html equal to VERSION.
"""

from __future__ import annotations

import datetime
import html as html_lib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SOURCE_HTML = DOCS / "index.html"
LOCALES_JSON = ROOT / "scripts" / "locales.json"


def attr_escape(value: str) -> str:
    return html_lib.escape(value, quote=True)


def set_attr(tag: str, name: str, value: str) -> str:
    escaped = attr_escape(value)
    pattern = rf'(\b{re.escape(name)}=)"[^"]*"'
    if re.search(pattern, tag):
        return re.sub(pattern, rf'\1"{escaped}"', tag, count=1)
    return tag[:-1] + f' {name}="{escaped}">'


def replace_data_i18n(doc: str, msgs: dict[str, str], attr_name: str, is_html: bool) -> str:
    pattern = re.compile(
        rf'(<(?P<tag>[a-zA-Z0-9]+)\b[^>]*?\s{attr_name}="(?P<key>[^"]+)"[^>]*>)(?P<inner>.*?)(</(?P=tag)>)',
        re.DOTALL,
    )

    def _sub(match: re.Match[str]) -> str:
        open_tag, key, close_tag = match.group(1), match.group("key"), match.group(5)
        if key not in msgs:
            raise KeyError(f"Missing translation key: {key}")
        val = msgs[key] if is_html else html_lib.escape(msgs[key], quote=False)
        cleaned_open = re.sub(rf'\s{attr_name}="[^"]+"', "", open_tag)
        return f"{cleaned_open}{val}{close_tag}"

    return pattern.sub(_sub, doc)


def replace_data_i18n_attr(doc: str, msgs: dict[str, str]) -> str:
    pattern = re.compile(r'<[a-zA-Z0-9]+\b[^>]*?\sdata-i18n-attr="([^"]+)"[^>]*>')

    def _sub(match: re.Match[str]) -> str:
        tag = match.group(0)
        pairs = match.group(1)
        for pair in pairs.split(","):
            attr, key = (part.strip() for part in pair.split(":", 1))
            if key not in msgs:
                raise KeyError(f"Missing translation key: {key}")
            tag = set_attr(tag, attr, msgs[key])
        return re.sub(r'\sdata-i18n-attr="[^"]+"', "", tag)

    return pattern.sub(_sub, doc)


def build_locale_html(template: str, loc: dict, msgs: dict[str, str], base_url: str) -> str:
    code = loc["code"]
    slug = loc["slug"]
    page_url = f"{base_url}{slug}/" if slug else base_url

    out = template
    out = re.sub(r'<html lang="[^"]+">', f'<html lang="{attr_escape(code)}">', out, count=1)
    out = re.sub(r"<title>.*?</title>", f"<title>{html_lib.escape(msgs['meta.title'], quote=False)}</title>", out, count=1, flags=re.DOTALL)

    # Meta & canonical
    meta_updates = [
        (r'(<meta name="description" content=")[^"]*(")', msgs["meta.description"]),
        (r'(<link rel="canonical" href=")[^"]*(")', page_url),
        (r'(<meta property="og:locale" content=")[^"]*(")', loc["ogLocale"]),
        (r'(<meta property="og:url" content=")[^"]*(")', page_url),
        (r'(<meta property="og:title" content=")[^"]*(")', msgs["meta.title"]),
        (r'(<meta property="og:description" content=")[^"]*(")', msgs["meta.ogDescription"]),
        (r'(<meta name="twitter:title" content=")[^"]*(")', msgs["meta.title"]),
        (r'(<meta name="twitter:description" content=")[^"]*(")', msgs["meta.description"]),
    ]
    for pat, val in meta_updates:
        out = re.sub(pat, lambda m, v=attr_escape(val): f"{m.group(1)}{v}{m.group(2)}", out, count=1)

    # JSON-LD url, description, inLanguage
    ld_pattern = re.compile(r'(<script type="application/ld\+json">\s*)(\{.*?\})(\s*</script>)', re.DOTALL)

    def _update_ld(match: re.Match[str]) -> str:
        ld = json.loads(match.group(2))
        ld["url"] = page_url
        ld["description"] = msgs["meta.ogDescription"]
        ld["inLanguage"] = code
        formatted = json.dumps(ld, ensure_ascii=False, indent=2)
        indented = "\n".join("  " + line if line else "" for line in formatted.splitlines())
        return f'{match.group(1).rstrip()}\n{indented}\n  </script>'

    out = ld_pattern.sub(_update_ld, out, count=1)

    # Inject per-locale CJK webfont into Google Fonts request when configured
    google_font = loc.get("googleFont")
    if google_font:
        out = out.replace("&display=swap", f"&family={google_font}&display=swap", 1)

    # Relative asset & legal page paths from subdirectory
    if slug:
        out = out.replace('href="apple-touch-icon.png"', 'href="../apple-touch-icon.png"')
        out = out.replace('href="favicon.ico"', 'href="../favicon.ico"')
        out = out.replace('href="favicon.svg"', 'href="../favicon.svg"')
        out = out.replace('src="favicon.svg"', 'src="../favicon.svg"')
        out = out.replace('href="style.css"', 'href="../style.css"')
        out = out.replace('src="consent.js"', 'src="../consent.js"')
        out = out.replace('src="maggy.js"', 'src="../maggy.js"')
        out = out.replace('src="appearance.js"', 'src="../appearance.js"')
        out = out.replace('href="privacy.html"', 'href="../privacy.html"')
        out = out.replace('href="terms.html"', 'href="../terms.html"')

    # Body dataset for locale & copy button strings
    body_open = (
        f'<body data-locale="{attr_escape(slug)}" '
        f'data-copy-idle="{attr_escape(msgs["copy.idle"])}" '
        f'data-copy-copied="{attr_escape(msgs["copy.copied"])}" '
        f'data-copy-fallback="{attr_escape(msgs["copy.fallback"])}">'
    )
    out = re.sub(r"<body\b[^>]*>", body_open, out, count=1)

    # Mark selected language option
    out = re.sub(r'(<option value="[^"]*") selected(>)', r"\1\2", out)
    out = out.replace(f'<option value="{slug}">', f'<option value="{slug}" selected>', 1)

    # Replace i18n attributes and text/HTML content
    out = replace_data_i18n_attr(out, msgs)
    out = replace_data_i18n(out, msgs, "data-i18n-html", is_html=True)
    out = replace_data_i18n(out, msgs, "data-i18n", is_html=False)

    # Guard against any leftover data-i18n markers
    leftovers = re.findall(r'data-i18n(?:-html|-attr)?="[^"]+"', out)
    if leftovers:
        raise RuntimeError(f"Unresolved i18n markers in {code}: {leftovers}")

    return out


def build_sitemap(locales: list[dict], base_url: str) -> str:
    today = datetime.date.today().isoformat()
    alt_lines = [f'    <xhtml:link rel="alternate" hreflang="x-default" href="{base_url}"/>']
    for loc in locales:
        url = f"{base_url}{loc['slug']}/" if loc["slug"] else base_url
        alt_lines.append(f'    <xhtml:link rel="alternate" hreflang="{loc["code"]}" href="{url}"/>')
    alt_block = "\n".join(alt_lines)

    urls = []
    for loc in locales:
        url = f"{base_url}{loc['slug']}/" if loc["slug"] else base_url
        priority = "1.0" if not loc["slug"] else "0.9"
        urls.append(
            "  <url>\n"
            f"    <loc>{url}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            "    <changefreq>weekly</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            f"{alt_block}\n"
            "  </url>"
        )

    for legal_page in ("privacy.html", "terms.html"):
        urls.append(
            "  <url>\n"
            f"    <loc>{base_url}{legal_page}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            "    <changefreq>monthly</changefreq>\n"
            "    <priority>0.3</priority>\n"
            "  </url>"
        )

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


REPO_URL = "https://github.com/agy-pet/maggy"
RAW_URL = "https://raw.githubusercontent.com/agy-pet/maggy/master/"


def sync_version(template: str, version: str) -> str:
    """Keep the JSON-LD softwareVersion in the English source in step with VERSION."""
    return re.sub(r'("softwareVersion":\s*)"[^"]*"', rf'\1"{version}"', template, count=1)


def readme_for_web(readme: str) -> str:
    """README with repo-relative links made absolute so it reads correctly off GitHub."""
    readme = re.sub(r"\]\((assets/[^)\s]+)\)", rf"]({RAW_URL}\1)", readme)
    readme = re.sub(r"\]\(#([^)\s]+)\)", rf"]({REPO_URL}#\1)", readme)
    return readme


def build_llms_txt(base_url: str, version: str, locales: list[dict]) -> str:
    """llms.txt (https://llmstxt.org): a short, link-first map of the project for AI agents."""
    lang_links = "\n".join(
        f"- [{loc['code']}]({base_url}{loc['slug']}/)" for loc in locales if loc["slug"]
    )
    return f"""# Maggy

> Maggy is an animated terminal pet and custom statusline for Antigravity CLI (`agy`). A dancing Antigravity-logo mascot sits beside the live model, context window %, quota usage bars, workspace, git branch and reasoning effort. Free and open source (MIT), macOS/Linux, Python 3 standard library only, zero telemetry. Current version: {version}. Unofficial; not affiliated with Google.

Install for a user (non-interactive, safe to run from an agent):

```bash
brew install agy-pet/tap/maggy && maggy setup
# or, without Homebrew:
curl -fsSL https://agy-pet.github.io/install.sh | bash
```

`maggy setup` only sets the `statusLine` key in `~/.gemini/antigravity-cli/settings.json` (backup at `settings.json.bak`); other settings are untouched. Verify with `maggy doctor` or `maggy status -q`. The user then restarts `agy` or runs `/statusline enable` inside it. Undo with `maggy uninstall --purge`.

Notes for agents:
- Every `maggy` subcommand is non-interactive except `maggy preview` (animates until Ctrl+C; add `--once` to print one frame) and `maggy stats web` (opens a browser; add `--no-open`).
- `maggy stats --json` prints machine-readable usage stats.
- Settings live in `~/.config/maggy/config.json`; prefer `maggy config set KEY VALUE` over editing the file.
- Custom themes are JSON files in `~/.config/maggy/themes/`; the schema is in the full docs below.

## Docs

- [Full documentation (Markdown)]({base_url}llms-full.txt): install, every command, config keys, env vars, theme JSON schema, troubleshooting
- [Landing page]({base_url}): interactive demo of the statusline and themes
- [README on GitHub]({REPO_URL}#readme): same content as the full docs, rendered

## Source

- [GitHub repository]({REPO_URL}): Python source (`statusline.py`, `mascot.py`, `cli.py`)
- [Releases]({REPO_URL}/releases)
- [Homebrew tap](https://github.com/agy-pet/homebrew-tap)
- [Antigravity CLI statusline docs](https://antigravity.google/docs/cli/statusline): the `statusLine` hook Maggy plugs into

## Optional

- [Privacy policy]({base_url}privacy.html)
- [Terms]({base_url}terms.html)
{lang_links}
"""


def build_llms_full(readme: str, base_url: str, version: str) -> str:
    header = (
        f"<!-- Maggy {version} — full docs for AI agents and LLMs. "
        f"Index: {base_url}llms.txt · Source: {REPO_URL} -->\n\n"
    )
    return header + readme_for_web(readme)


def main() -> None:
    data = json.loads(LOCALES_JSON.read_text(encoding="utf-8"))
    base_url = data["baseUrl"]
    locales = data["locales"]
    messages = data["messages"]
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    template = sync_version(SOURCE_HTML.read_text(encoding="utf-8"), version)
    if template != SOURCE_HTML.read_text(encoding="utf-8"):
        SOURCE_HTML.write_text(template, encoding="utf-8")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    full = build_llms_full(readme, base_url, version)
    (DOCS / "llms.txt").write_text(build_llms_txt(base_url, version, locales), encoding="utf-8")
    (DOCS / "llms-full.txt").write_text(full, encoding="utf-8")
    (DOCS / "index.md").write_text(full, encoding="utf-8")
    # Serve the one-line installer at https://agy-pet.github.io/install.sh
    shutil.copyfile(ROOT / "install.sh", DOCS / "install.sh")

    generated = 0
    for loc in locales:
        slug = loc["slug"]
        if not slug:
            continue
        code = loc["code"]
        rendered = build_locale_html(template, loc, messages[code], base_url)
        target_dir = DOCS / slug
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "index.html").write_text(rendered, encoding="utf-8")
        generated += 1

    (DOCS / "sitemap.xml").write_text(build_sitemap(locales, base_url), encoding="utf-8")
    print(f"Generated {generated} locale pages, sitemap.xml, llms.txt, llms-full.txt and index.md")


if __name__ == "__main__":
    main()
