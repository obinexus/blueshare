#!/usr/bin/env python3
"""Build and verify the dependency-free BlueShare static Pages bundle."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "README3.md"
SOURCE_IMAGES = ROOT / "docs" / "blog" / "images"
SOURCE_PDF = ROOT / "output" / "pdf" / "blueshare-sharing-moments-matters.pdf"
PAGE_ASSETS = ROOT / ".gitlab" / "pages"

EXPECTED_IMAGES = (
    "01-youtube-music-example.png",
    "02-windows-service-020.png",
    "03-blueshare-join-screen.png",
    "04-blueshare-media-room.png",
)


def normalize_base_path(value: str) -> str:
    value = value.strip()
    if not value or value == "/":
        return ""
    parts = value.strip("/").split("/")
    if any(
        part in {"", ".", ".."} or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", part)
        for part in parts
    ):
        raise ValueError(f"invalid Pages base path: {value!r}")
    return "/" + "/".join(parts)


def output_path(value: Path) -> Path:
    resolved = value.resolve() if value.is_absolute() else (ROOT / value).resolve()
    if resolved == ROOT or ROOT not in resolved.parents:
        raise ValueError(f"output must be a child of the repository: {resolved}")
    return resolved


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def inline_markdown(value: str) -> str:
    rendered = html.escape(value, quote=True)
    rendered = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: f'<a href="{match.group(2)}">{match.group(1)}</a>',
        rendered,
    )
    rendered = re.sub(r"`([^`]+)`", r"<code>\1</code>", rendered)
    rendered = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"(?<!\*)\*([^*]+)\*", r"<em>\1</em>", rendered)
    return rendered


def paragraph_html(lines: list[str]) -> str:
    pieces: list[str] = []
    for line in lines:
        hard_break = line.endswith("  ")
        pieces.append(line.strip())
        if hard_break:
            pieces.append("<br>")
        else:
            pieces.append(" ")
    return inline_markdown("".join(pieces).strip()).replace("&lt;br&gt;", "<br>")


def is_block_start(line: str) -> bool:
    stripped = line.strip()
    return bool(
        not stripped
        or stripped.startswith("#")
        or stripped.startswith("```")
        or stripped.startswith("![")
        or stripped.startswith(">")
        or stripped.startswith("|")
        or re.match(r"^[-*]\s+", stripped)
        or re.match(r"^\d+\.\s+", stripped)
    )


def render_markdown(markdown: str) -> tuple[str, list[tuple[str, str]]]:
    lines = markdown.splitlines()
    chunks: list[str] = []
    headings: list[tuple[str, str]] = []
    used_slugs: dict[str, int] = {}
    index = 0

    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            continue

        heading = re.match(r"^(#{1,3})\s+(.+)$", stripped)
        if heading:
            level = len(heading.group(1))
            label = re.sub(r"[*`]", "", heading.group(2))
            slug = slugify(label)
            used_slugs[slug] = used_slugs.get(slug, 0) + 1
            if used_slugs[slug] > 1:
                slug = f"{slug}-{used_slugs[slug]}"
            if level == 2:
                headings.append((slug, label))
            chunks.append(f'<h{level} id="{slug}">{inline_markdown(heading.group(2))}</h{level}>')
            index += 1
            continue

        if stripped.startswith("```"):
            language = stripped[3:].strip()
            code: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code.append(lines[index])
                index += 1
            index += 1
            class_name = f' class="language-{html.escape(language)}"' if language else ""
            chunks.append(f"<pre><code{class_name}>{html.escape(chr(10).join(code))}</code></pre>")
            continue

        image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if image:
            source_name = Path(image.group(2)).name
            if source_name not in EXPECTED_IMAGES:
                raise ValueError(f"unexpected README image: {image.group(2)}")
            chunks.append(
                '<figure>'
                f'<img src="images/{html.escape(source_name)}" alt="{html.escape(image.group(1))}" loading="lazy">'
                f'<figcaption>{html.escape(image.group(1))}</figcaption>'
                "</figure>"
            )
            index += 1
            continue

        if stripped.startswith(">"):
            quote: list[str] = []
            while index < len(lines) and lines[index].strip().startswith(">"):
                quote.append(lines[index].strip()[1:].strip())
                index += 1
            chunks.append(f"<blockquote>{inline_markdown(' '.join(quote))}</blockquote>")
            continue

        if re.match(r"^[-*]\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
            ordered = bool(re.match(r"^\d+\.\s+", stripped))
            pattern = r"^\d+\.\s+" if ordered else r"^[-*]\s+"
            items: list[str] = []
            while index < len(lines) and re.match(pattern, lines[index].strip()):
                text = re.sub(pattern, "", lines[index].strip())
                index += 1
                while index < len(lines) and lines[index].startswith("   ") and lines[index].strip():
                    text += " " + lines[index].strip()
                    index += 1
                items.append(f"<li>{inline_markdown(text)}</li>")
            tag = "ol" if ordered else "ul"
            chunks.append(f"<{tag}>{''.join(items)}</{tag}>")
            continue

        if stripped.startswith("|"):
            rows: list[list[str]] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                    rows.append(cells)
                index += 1
            if rows:
                head = "".join(f"<th>{inline_markdown(cell)}</th>" for cell in rows[0])
                body = "".join(
                    "<tr>" + "".join(f"<td>{inline_markdown(cell)}</td>" for cell in row) + "</tr>"
                    for row in rows[1:]
                )
                chunks.append(
                    f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
                )
            continue

        paragraph = [lines[index]]
        index += 1
        while index < len(lines) and not is_block_start(lines[index]):
            paragraph.append(lines[index])
            index += 1
        text = paragraph_html(paragraph)
        css_class = ' class="caption"' if paragraph[0].strip().startswith("*Figure ") else ""
        chunks.append(f"<p{css_class}>{text}</p>")

    return "\n".join(chunks), headings


def site_html(article: str, headings: list[tuple[str, str]], canonical_url: str) -> str:
    toc = "\n".join(f'<a href="#{slug}">{html.escape(label)}</a>' for slug, label in headings)
    return f"""<!doctype html>
<html lang="en-GB">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#071522">
  <meta name="description" content="BlueShare - Sharing Moments Matters. A first-person guide to trusted-LAN peer topology and shared audio on Windows.">
  <meta property="og:title" content="BlueShare - Sharing Moments Matters">
  <meta property="og:description" content="A first-person BlueShare user story and Windows media-room guide by Nnamdi Michael Okpala.">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{html.escape(canonical_url)}">
  <link rel="canonical" href="{html.escape(canonical_url)}">
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="manifest" href="manifest.webmanifest">
  <link rel="stylesheet" href="assets/site.css">
  <title>BlueShare - Sharing Moments Matters</title>
</head>
<body>
  <a class="skip-link" href="#article">Skip to the article</a>
  <header class="site-header">
    <nav class="nav" aria-label="Primary navigation">
      <a class="brand" href="./"><img src="assets/favicon.svg" alt=""><span>BlueShare</span></a>
      <div class="nav-links">
        <a href="#why-i-built-blueshare">Story</a>
        <a href="#how-i-start-blueshare-on-windows">Windows guide</a>
        <a href="downloads/blueshare-sharing-moments-matters.pdf">PDF</a>
        <a href="mailto:okpalan@protonmail.com">Contact</a>
      </div>
    </nav>
  </header>
  <main>
    <section class="hero" aria-labelledby="hero-title">
      <div>
        <p class="eyebrow">OBINexus Computing - trusted LAN vertical slice</p>
        <h1 id="hero-title">BlueShare</h1>
        <p class="tagline">Sharing Moments Matters</p>
        <p class="lede">I built BlueShare so people on the same trusted network can join as named peers, understand their manual spatial relationship, and interact with one shared media room.</p>
        <div class="hero-actions">
          <a class="button" href="#article">Read the guide</a>
          <a class="button secondary" href="downloads/blueshare-sharing-moments-matters.pdf">Download the PDF</a>
        </div>
      </div>
      <aside class="status-card" aria-label="Current prototype status">
        <strong>BlueShare 0.2.0</strong>
        <p>Windows-hosted trusted-LAN service</p>
        <p>Manual coordinates in metres</p>
        <p>Shared local audio with synchronized controls</p>
        <p>By Nnamdi Michael Okpala</p>
      </aside>
    </section>
    <aside class="boundary">
      <strong>Provider boundary:</strong> BlueShare shares a YouTube Music page as a link only. It does not extract, proxy, or rebroadcast protected provider audio. Synchronized playback uses media the room is permitted to share.
    </aside>
    <div class="layout">
      <aside class="toc" aria-label="Article contents"><strong>On this page</strong>{toc}</aside>
      <article class="article" id="article">{article}</article>
    </div>
  </main>
  <footer class="site-footer">
    <p>BlueShare - Sharing Moments Matters. Nnamdi Michael Okpala, OBINexus Computing. <a href="mailto:okpalan@protonmail.com">okpalan@protonmail.com</a></p>
    <p>This static site documents the prototype. The live peer and media service runs on a trusted Windows host; static Pages hosting does not run that Python service.</p>
  </footer>
</body>
</html>
"""


def root_index(base_path: str, canonical_url: str) -> str:
    relative = f".{base_path}/" if base_path else "./"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><meta http-equiv="refresh" content="0;url={html.escape(relative)}">
<link rel="canonical" href="{html.escape(canonical_url)}"><title>Opening BlueShare</title></head>
<body><p><a href="{html.escape(relative)}">Open BlueShare - Sharing Moments Matters</a></p></body></html>
"""


def build_site(output: Path, base_path: str, canonical_url: str) -> Path:
    required = [SOURCE, SOURCE_PDF, PAGE_ASSETS / "site.css", PAGE_ASSETS / "favicon.svg"]
    required.extend(SOURCE_IMAGES / name for name in EXPECTED_IMAGES)
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing source assets: " + ", ".join(missing))

    base_path = normalize_base_path(base_path)
    output = output_path(output)
    if output.exists():
        shutil.rmtree(output)
    site = output / base_path.strip("/") if base_path else output
    (site / "assets").mkdir(parents=True)
    (site / "images").mkdir()
    (site / "downloads").mkdir()

    article, headings = render_markdown(SOURCE.read_text(encoding="utf-8"))
    (site / "index.html").write_text(site_html(article, headings, canonical_url), encoding="utf-8")
    shutil.copy2(PAGE_ASSETS / "site.css", site / "assets" / "site.css")
    shutil.copy2(PAGE_ASSETS / "favicon.svg", site / "assets" / "favicon.svg")
    for name in EXPECTED_IMAGES:
        shutil.copy2(SOURCE_IMAGES / name, site / "images" / name)
    shutil.copy2(SOURCE_PDF, site / "downloads" / SOURCE_PDF.name)
    shutil.copy2(SOURCE, site / "downloads" / "README3.md")

    manifest = {
        "name": "BlueShare - Sharing Moments Matters",
        "short_name": "BlueShare",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": "#061321",
        "theme_color": "#071522",
        "icons": [{"src": "assets/favicon.svg", "sizes": "any", "type": "image/svg+xml"}],
    }
    (site / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    github_run_url = "local"
    if os.environ.get("GITHUB_SERVER_URL") and os.environ.get("GITHUB_REPOSITORY") and os.environ.get("GITHUB_RUN_ID"):
        github_run_url = (
            f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}"
            f"/actions/runs/{os.environ['GITHUB_RUN_ID']}"
        )
    deployment = {
        "site": "BlueShare",
        "base_path": base_path or "/",
        "canonical_url": canonical_url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "commit": os.environ.get("CI_COMMIT_SHA") or os.environ.get("GITHUB_SHA", "local"),
        "pipeline_url": os.environ.get("CI_PIPELINE_URL") or github_run_url,
    }
    (site / "deployment.json").write_text(json.dumps(deployment, indent=2) + "\n", encoding="utf-8")
    (site / "404.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>BlueShare page not found</title><link rel="stylesheet" href="assets/site.css"><main class="hero">'
        '<div><p class="eyebrow">404</p><h1>Page not found</h1><p><a class="button" href="./">Return to BlueShare</a></p></div></main></html>\n',
        encoding="utf-8",
    )
    if base_path:
        (output / "index.html").write_text(root_index(base_path, canonical_url), encoding="utf-8")
    verify_bundle(output, base_path)
    return site


def verify_bundle(output: Path, base_path: str) -> None:
    output = output_path(output)
    base_path = normalize_base_path(base_path)
    site = output / base_path.strip("/") if base_path else output
    required = [
        output / "index.html",
        site / "index.html",
        site / "404.html",
        site / "assets" / "site.css",
        site / "assets" / "favicon.svg",
        site / "downloads" / SOURCE_PDF.name,
        site / "downloads" / "README3.md",
        site / "manifest.webmanifest",
        site / "deployment.json",
    ]
    required.extend(site / "images" / name for name in EXPECTED_IMAGES)
    missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise FileNotFoundError("incomplete Pages bundle: " + ", ".join(missing))

    page = (site / "index.html").read_text(encoding="utf-8")
    assertions = {
        "title": "BlueShare - Sharing Moments Matters" in page,
        "author": "Nnamdi Michael Okpala" in page,
        "email": "okpalan@protonmail.com" in page,
        "provider link": "https://music.youtube.com/watch?v=TgOu00Mf3kI" in page,
        "PDF link": f"downloads/{SOURCE_PDF.name}" in page,
        "source paths rewritten": "docs/blog/images/" not in page,
        "no local file links": 'href="C:\\' not in page and 'src="C:\\' not in page,
    }
    for name in EXPECTED_IMAGES:
        assertions[f"image {name}"] = f"images/{name}" in page
    failed = [label for label, passed in assertions.items() if not passed]
    if failed:
        raise ValueError("Pages verification failed: " + ", ".join(failed))

    print(f"BlueShare Pages bundle verified: {site}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("public"))
    parser.add_argument("--base-path", default="/blueshare")
    parser.add_argument("--canonical-url", default="https://www.obinexus.org/blueshare/")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        verify_bundle(args.output, args.base_path)
    else:
        site = build_site(args.output, args.base_path, args.canonical_url)
        print(f"BlueShare Pages site built: {site}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
