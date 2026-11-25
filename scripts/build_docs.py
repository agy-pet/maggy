#!/usr/bin/env python3
"""Generate static per-locale landing pages and multilingual sitemap.xml.

Reads docs/index.html (English source) and scripts/locales.json, then writes:
  - docs/<slug>/index.html for each non-English locale
  - docs/sitemap.xml with hreflang alternates for all locales
  - docs/llms.txt, docs/llms-full.txt and docs/index.md for AI agents (from README.md)
  - docs/install.sh, a stub served at the site root that runs install.sh from the
    latest GitHub release
  - docs/.well-known/agent-skills/ (index.json + SKILL.md files) from scripts/agent-skills/
and keeps the JSON-LD softwareVersion in docs/index.html equal to VERSION.
"""

from __future__ import annotations

import datetime
import hashlib
import html as html_lib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
SOURCE_HTML = DOCS / "index.html"
LOCALES_JSON = ROOT / "scripts" / "locales.json"
SKILLS_SRC = ROOT / "scripts" / "agent-skills"
SKILLS_OUT = DOCS / ".well-known" / "agent-skills"

# Served at https://agy-pet.github.io/install.sh. Only ever runs the latest release's
# installer (pinned to that release's tag); no fallback to unreleased master.
# Wrapped in main() so bash parses the whole stub before running anything when
# it's piped in.
INSTALL_STUB = """#!/usr/bin/env bash
# maggy installer: curl -fsSL https://agy-pet.github.io/install.sh | bash
# Runs install.sh from the latest release; see https://github.com/agy-pet/maggy
set -euo pipefail
main() {
    local script
    script="$(curl -fsSL https://github.com/agy-pet/maggy/releases/latest/download/install.sh)" || {
        echo "maggy: could not download the release installer; try again, or: brew install agy-pet/tap/maggy" >&2
        exit 1
    }
    bash -c "$script" maggy-install "$@"
}
main "$@"
"""


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


def strip_html(value: str) -> str:
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", "", value))).strip()


def build_faq_ld(msgs: dict[str, str], code: str) -> dict:
    entities = []
    i = 1
    while f"faq.q{i}" in msgs and f"faq.a{i}" in msgs:
        entities.append({
            "@type": "Question",
            "name": strip_html(msgs[f"faq.q{i}"]),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": strip_html(msgs[f"faq.a{i}"]),
            },
        })
        i += 1
    return {
        "@type": "FAQPage",
        "inLanguage": code,
        "mainEntity": entities,
    }


def upsert_faq_ld(doc: str, msgs: dict[str, str], code: str) -> str:
    ld_pattern = re.compile(r'(<script type="application/ld\+json">\s*)(\{.*?\})(\s*</script>)', re.DOTALL)

    def _sub(match: re.Match[str]) -> str:
        ld = json.loads(match.group(2))
        graph = ld.get("@graph")
        if graph is None:
            return match.group(0)
        graph = [n for n in graph if n.get("@type") != "FAQPage"]
        faq_node = build_faq_ld(msgs, code)
        if faq_node["mainEntity"]:
            graph.append(faq_node)
        ld["@graph"] = graph
        formatted = json.dumps(ld, ensure_ascii=False, indent=2)
        indented = "\n".join("  " + line if line else "" for line in formatted.splitlines())
        return f'{match.group(1).rstrip()}\n{indented}\n  </script>'

    return ld_pattern.sub(_sub, doc, count=1)


def build_locale_html(template: str, loc: dict, locales: list[dict], msgs: dict[str, str], base_url: str) -> str:
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
        (r'(<meta property="og:url" content=")[^"]*(")', page_url),
        (r'(<meta property="og:title" content=")[^"]*(")', msgs["meta.title"]),
        (r'(<meta property="og:description" content=")[^"]*(")', msgs["meta.ogDescription"]),
        (r'(<meta property="og:image:alt" content=")[^"]*(")', msgs["meta.title"]),
        (r'(<meta name="twitter:title" content=")[^"]*(")', msgs["meta.title"]),
        (r'(<meta name="twitter:description" content=")[^"]*(")', msgs["meta.description"]),
        (r'(<meta name="twitter:image:alt" content=")[^"]*(")', msgs["meta.title"]),
    ]
    for pat, val in meta_updates:
        out = re.sub(pat, lambda m, v=attr_escape(val): f"{m.group(1)}{v}{m.group(2)}", out, count=1)

    # og:locale + og:locale:alternate for all other locales
    og_locale_lines = [f'  <meta property="og:locale" content="{attr_escape(loc["ogLocale"])}">']
    for other in locales:
        if other["code"] != code:
            og_locale_lines.append(f'  <meta property="og:locale:alternate" content="{attr_escape(other["ogLocale"])}">')
    out = re.sub(
        r'  <meta property="og:locale" content="[^"]*">(?:\n  <meta property="og:locale:alternate" content="[^"]*">)*',
        "\n".join(og_locale_lines),
        out,
        count=1,
    )

    # JSON-LD url, description, inLanguage, installUrl (supports @graph)
    ld_pattern = re.compile(r'(<script type="application/ld\+json">\s*)(\{.*?\})(\s*</script>)', re.DOTALL)

    def _update_ld(match: re.Match[str]) -> str:
        ld = json.loads(match.group(2))
        nodes = [n for n in ld.get("@graph", [ld]) if n.get("@type") != "FAQPage"]
        for node in nodes:
            node_type = node.get("@type")
            if node_type == "WebSite":
                node["url"] = page_url
                node["inLanguage"] = code
            elif node_type == "SoftwareApplication":
                node["url"] = page_url
                node["description"] = msgs["meta.ogDescription"]
                node["inLanguage"] = code
                node["installUrl"] = f"{page_url}#install"
        faq_node = build_faq_ld(msgs, code)
        if faq_node["mainEntity"]:
            nodes.append(faq_node)
        if "@graph" in ld:
            ld["@graph"] = nodes
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
        out = out.replace('href="fonts/', 'href="../fonts/')
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

    # Update crawlable language switcher label, hrefs, and aria-current
    out = re.sub(
        r'<span class="lang-current">[^<]*</span>',
        f'<span class="lang-current">{html_lib.escape(loc["label"], quote=False)}</span>',
        out,
        count=1,
    )
    prefix = "../" if slug else "./"
    lang_items = []
    for item in locales:
        href = f'{prefix}{item["slug"]}/' if item["slug"] else prefix
        current = ' aria-current="page"' if item["code"] == code else ""
        lang_items.append(
            f'          <li><a href="{attr_escape(href)}" hreflang="{attr_escape(item["code"])}" '
            f'lang="{attr_escape(item["code"])}"{current}>{html_lib.escape(item["label"], quote=False)}</a></li>'
        )
    out = re.sub(
        r'(<ul class="lang-menu">\n).*?(\n        </ul>)',
        lambda m: m.group(1) + "\n".join(lang_items) + m.group(2),
        out,
        count=1,
        flags=re.DOTALL,
    )

    # Replace i18n attributes and text/HTML content
    out = replace_data_i18n_attr(out, msgs)
    out = replace_data_i18n(out, msgs, "data-i18n-html", is_html=True)
    out = replace_data_i18n(out, msgs, "data-i18n", is_html=False)

    # Guard against any leftover data-i18n markers
    leftovers = re.findall(r'data-i18n(?:-html|-attr)?="[^"]+"', out)
    if leftovers:
        raise RuntimeError(f"Unresolved i18n markers in {code}: {leftovers}")

    return out


def git_lastmod(*paths: Path) -> str:
    """Return latest YYYY-MM-DD commit date touching any of paths, or today if unavailable."""
    today = datetime.date.today().isoformat()
    try:
        res = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", *(str(p) for p in paths)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        date = res.stdout.strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            return date
    except OSError:
        pass
    return today


def build_sitemap(locales: list[dict], base_url: str) -> str:
    alt_lines = [f'    <xhtml:link rel="alternate" hreflang="x-default" href="{base_url}"/>']
    for loc in locales:
        url = f"{base_url}{loc['slug']}/" if loc["slug"] else base_url
        alt_lines.append(f'    <xhtml:link rel="alternate" hreflang="{loc["code"]}" href="{url}"/>')
    alt_block = "\n".join(alt_lines)

    landing_lastmod = git_lastmod(SOURCE_HTML, LOCALES_JSON)
    urls = []
    for loc in locales:
        url = f"{base_url}{loc['slug']}/" if loc["slug"] else base_url
        priority = "1.0" if not loc["slug"] else "0.9"
        urls.append(
            "  <url>\n"
            f"    <loc>{url}</loc>\n"
            f"    <lastmod>{landing_lastmod}</lastmod>\n"
            "    <changefreq>weekly</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            f"{alt_block}\n"
            "  </url>"
        )

    for legal_page in ("privacy.html", "terms.html"):
        legal_lastmod = git_lastmod(DOCS / legal_page)
        urls.append(
            "  <url>\n"
            f"    <loc>{base_url}{legal_page}</loc>\n"
            f"    <lastmod>{legal_lastmod}</lastmod>\n"
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
- Custom themes are JSON files in `~/.config/maggy/themes/<name>.json`, validated by the JSON Schema at https://agy-pet.github.io/theme.schema.json. Check one with `maggy theme list` (skipped files show the reason) and `maggy preview working --theme <name> --once`, then enable it with `maggy theme <name>`.

## Docs

- [Full documentation (Markdown)]({base_url}llms-full.txt): install, every command, config keys, env vars, theme JSON schema, troubleshooting
- [Landing page]({base_url}): interactive demo of the statusline and themes
- [Theme JSON Schema](https://agy-pet.github.io/theme.schema.json): every key a custom theme file can use, with descriptions
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


def build_agent_skills() -> int:
    """Publish scripts/agent-skills/*/SKILL.md per the Agent Skills Discovery RFC v0.2.0."""
    if SKILLS_OUT.exists():
        shutil.rmtree(SKILLS_OUT)
    skills = []
    for src in sorted(SKILLS_SRC.glob("*/SKILL.md")):
        name = src.parent.name
        body = src.read_bytes()
        front = re.match(r"---\n(.*?)\n---\n", body.decode("utf-8"), re.DOTALL)
        if not front:
            raise ValueError(f"{src}: missing frontmatter")
        meta = dict(line.split(":", 1) for line in front.group(1).splitlines() if ":" in line)
        if meta.get("name", "").strip() != name:
            raise ValueError(f"{src}: frontmatter name must be {name!r}")
        out = SKILLS_OUT / name / "SKILL.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(body)
        skills.append({
            "name": name,
            "type": "skill-md",
            "description": meta["description"].strip(),
            "url": f"/.well-known/agent-skills/{name}/SKILL.md",
            "digest": "sha256:" + hashlib.sha256(body).hexdigest(),
        })
    index = {"$schema": "https://schemas.agentskills.io/discovery/0.2.0/schema.json", "skills": skills}
    (SKILLS_OUT / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(skills)


def main() -> None:
    data = json.loads(LOCALES_JSON.read_text(encoding="utf-8"))
    base_url = data["baseUrl"]
    locales = data["locales"]
    messages = data["messages"]
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    template = sync_version(SOURCE_HTML.read_text(encoding="utf-8"), version)
    template = upsert_faq_ld(template, messages["en"], "en")
    if template != SOURCE_HTML.read_text(encoding="utf-8"):
        SOURCE_HTML.write_text(template, encoding="utf-8")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    full = build_llms_full(readme, base_url, version)
    (DOCS / "llms.txt").write_text(build_llms_txt(base_url, version, locales), encoding="utf-8")
    (DOCS / "llms-full.txt").write_text(full, encoding="utf-8")
    (DOCS / "index.md").write_text(full, encoding="utf-8")
    # https://agy-pet.github.io/install.sh is a stub that runs the latest release's installer
    (DOCS / "install.sh").write_text(INSTALL_STUB, encoding="utf-8")
    skill_count = build_agent_skills()

    generated = 0
    for loc in locales:
        slug = loc["slug"]
        if not slug:
            continue
        code = loc["code"]
        rendered = build_locale_html(template, loc, locales, messages[code], base_url)
        target_dir = DOCS / slug
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "index.html").write_text(rendered, encoding="utf-8")
        generated += 1

    (DOCS / "sitemap.xml").write_text(build_sitemap(locales, base_url), encoding="utf-8")
    print(
        f"Generated {generated} locale pages, sitemap.xml, llms.txt, llms-full.txt, index.md "
        f"and {skill_count} agent skills"
    )


if __name__ == "__main__":
    main()
