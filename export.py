#!/usr/bin/env python3
"""Exports the board as a PNG per language with headless Chrome: docs/figure-<lang>.png

    python3 export.py                # all languages, 1600 px wide, 2x
    python3 export.py --width 390    # phone width (writes docs/figure-<lang>-<width>.png)
    CHROME=/path/to/chrome python3 export.py
"""
import argparse
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


def find_chrome():
    for c in [os.environ.get("CHROME")] + CANDIDATES:
        if c and (Path(c).exists() or shutil.which(c)):
            return c
    sys.exit("Chrome not found: set CHROME=/path/to/chrome")


def run(chrome, args):
    with tempfile.TemporaryDirectory() as tmp:
        return subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={tmp}/u", *args],
                              check=True, capture_output=True, text=True, timeout=120).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--scale", type=float, default=2)
    ap.add_argument("--theme", default="light")
    a = ap.parse_args()
    chrome = find_chrome()
    page = (ROOT / "docs" / "index.html").as_uri()
    for lang in sorted(p.stem for p in (ROOT / "i18n").glob("*.yml")):
        url = f"{page}?lang={lang}&export=1&theme={a.theme}"
        dom = run(chrome, [f"--window-size={a.width},1000", "--virtual-time-budget=3000", "--dump-dom", url])
        m = re.search(r'data-board-h="(\d+)"', dom)
        h = int(m.group(1)) + 8 if m else 1000
        name = f"figure-{lang}" + ("" if a.width == 1600 else f"-{a.width}") + ("" if a.theme == "light" else f"-{a.theme}") + ".png"
        out = ROOT / "docs" / name
        run(chrome, [f"--window-size={a.width},{h}", f"--force-device-scale-factor={a.scale}", "--virtual-time-budget=3000", f"--screenshot={out}", url])
        print("wrote", out.relative_to(ROOT), f"{a.width}x{h}")


if __name__ == "__main__":
    main()
