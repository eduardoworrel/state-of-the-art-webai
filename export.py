#!/usr/bin/env python3
"""Exports the figure with headless Chrome, per language and theme: docs/figure-<lang>[-dark].png and .svg

    python3 export.py                # all languages, light and dark; PNG at 2x and SVG
    python3 export.py --no-svg       # PNG only
    CHROME=/path/to/chrome python3 export.py

The figure is the board at its classic size (3 columns, 1552 px wide), without animation. The SVG holds the same board as HTML inside a
<foreignObject>: it opens in any modern browser and works in <img>, it is not a path drawing.
"""
import argparse
import base64
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import miniyaml  # noqa: E402

CANDIDATES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]
BG = {"light": "#f0ede6", "dark": "#151412"}


def find_chrome():
    for c in [os.environ.get("CHROME")] + CANDIDATES:
        if c and (Path(c).exists() or shutil.which(c)):
            return c
    sys.exit("Chrome not found: set CHROME=/path/to/chrome")


def run(chrome, args):
    with tempfile.TemporaryDirectory() as tmp:
        return subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={tmp}/u", *args],
                              check=True, capture_output=True, text=True, timeout=180).stdout


def svg_fonts():
    """@font-face for the SVG: an SVG used as <img> cannot load external files, so the (latin) font travels inside it as a data: URI (about 45 KB)."""
    css = (ROOT / "assets" / "fonts.css").read_text(encoding="utf-8")
    keep = []
    for line in css.splitlines():
        if "Atkinson Hyperlegible Next" not in line or "latin-ext" in line:   # the board uses only the sans family; every character is in the latin range
            continue
        m = re.search(r"url\(__FONTS__/([^)]+)\)", line)
        if m:
            data = base64.b64encode((ROOT / "docs" / "fonts" / m.group(1)).read_bytes()).decode()
            line = line.replace(m.group(0), f"url(data:font/woff2;base64,{data})")
        keep.append(line)
    return "\n".join(keep) + "\n"


def svg_figure(chrome, page, lang, theme, title):
    out = run(chrome, ["--window-size=1700,1000", "--virtual-time-budget=3000", "--dump-dom", f"{page}?lang={lang}&export=1&theme={theme}&xhtml=1"])
    m = re.search(r"<textarea id=\"xhtml\" data-w=\"(\d+)\" data-h=\"(\d+)\">(.*?)</textarea>", out, re.S)
    if not m:
        sys.exit("could not read the board from the page")
    bw, bh, board = int(m.group(1)), int(m.group(2)), html.unescape(m.group(3))
    pad = 20
    W, H = bw + 2 * pad, bh + 2 * pad
    css = (svg_fonts() + (ROOT / "assets" / "style.css").read_text(encoding="utf-8")).replace("]]>", "]]&gt;")
    board = board.replace("<div ", f'<div style="--u:14.4px;width:{bw}px" ', 1) if False else board
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" data-theme="{theme}" role="img" aria-label="{html.escape(title)}">'
            f'<title>{html.escape(title)}</title><style><![CDATA[{css}\n.svgroot {{ font-family: var(--font); color: var(--ink); line-height: 1.4; }}\n.svgroot .board {{ --u: 14.4px; width: {bw}px; margin: 0; }}]]></style>'
            f'<rect width="{W}" height="{H}" fill="{BG[theme]}"/><foreignObject x="{pad}" y="{pad}" width="{bw}" height="{bh}">'
            f'<div xmlns="http://www.w3.org/1999/xhtml" class="svgroot">{board}</div></foreignObject></svg>\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=2)
    ap.add_argument("--no-svg", action="store_true")
    a = ap.parse_args()
    chrome = find_chrome()
    page = (ROOT / "docs" / "index.html").as_uri()
    for lang in sorted(p.stem for p in (ROOT / "i18n").glob("*.yml")):
        title = miniyaml.load(ROOT / "i18n" / f"{lang}.yml")["site.title"]
        for theme in ("light", "dark"):
            url = f"{page}?lang={lang}&export=1&theme={theme}"
            dom = run(chrome, ["--window-size=1600,1000", "--virtual-time-budget=3000", "--dump-dom", url])
            m = re.search(r'data-board-h="(\d+)"', dom)
            h = int(m.group(1)) + 8 if m else 1000
            stem = f"figure-{lang}" + ("" if theme == "light" else "-dark")
            run(chrome, [f"--window-size=1600,{h}", f"--force-device-scale-factor={a.scale}", "--virtual-time-budget=3000", f"--screenshot={ROOT / 'docs' / (stem + '.png')}", url])
            print("wrote", f"docs/{stem}.png", f"1600x{h}")
            if not a.no_svg:
                (ROOT / "docs" / f"{stem}.svg").write_text(svg_figure(chrome, page, lang, theme, title), encoding="utf-8")
                print("wrote", f"docs/{stem}.svg")


if __name__ == "__main__":
    main()
