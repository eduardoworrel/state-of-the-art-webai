#!/usr/bin/env python3
"""Opens every source link in data/layers.yml and reports anything that is not a plain 200.
Alert evidence is opened too and reported apart: a `broken-link` or `removed` alert whose evidence now answers 200 may be obsolete.

    python3 scripts/linkcheck.py            # needs network; not part of CI (sites throttle bots)
    python3 scripts/linkcheck.py --strict   # exit 1 on dead links; redirects are reported, not failed

A redirect that only moves the page is a reason to update the url in the data (and `accessed` after re-reading it).
"""
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import miniyaml  # noqa: E402

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"  # some sites refuse unknown agents


def urls():
    out = {}
    for L in miniyaml.load(ROOT / "data" / "layers.yml")["layers"]:
        for g in L["groups"] + (L.get("panel") or {}).get("groups", []):
            for c in g["chips"]:
                for s in c["sources"]:
                    out.setdefault(s["url"], []).append(c["id"])
        for w in L.get("where", []):
            out.setdefault(w["source"]["url"], []).append("where-" + w["id"])
    return out


def evidence():
    out = []
    for L in miniyaml.load(ROOT / "data" / "layers.yml")["layers"]:
        for g in L["groups"] + (L.get("panel") or {}).get("groups", []):
            for c in g["chips"]:
                for u in (c.get("alert") or {}).get("evidence", []):
                    out.append((c["id"], c["alert"]["kind"], c["alert"]["observed"], u))
    return out


def probe(url):
    """(status, final url). Uses curl when present (some sites refuse Python's TLS fingerprint), else urllib."""
    if shutil.which("curl"):
        for extra in ([], ["-r", "0-0"]):  # a plain GET first, then a one-byte range for servers that refuse bots on full GETs
            r = subprocess.run(["curl", "-sL", "-A", UA, "-m", "25", "-o", os.devnull, "-w", "%{http_code} %{url_effective}", *extra, url], capture_output=True, text=True)
            code, _, final = r.stdout.partition(" ")
            if code == "200":
                return 200, final
        return int(code) if code.isdigit() else 0, url
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.status, r.geturl()
        except urllib.error.HTTPError as e:
            if method == "GET":
                return e.code, url
        except Exception as e:  # noqa: BLE001
            if method == "GET":
                return f"error: {e}", url
    return 0, url


def main():
    found = urls()
    with ThreadPoolExecutor(8) as ex:
        res = dict(zip(found, ex.map(probe, found)))
    throttled = {u: r for u, r in res.items() if r[0] == 429}
    dead = {u: r for u, r in res.items() if r[0] not in (200, 429)}
    moved = {u: r for u, r in res.items() if r[0] == 200 and r[1].rstrip("/") != u.rstrip("/")}
    for u, (code, final) in sorted(dead.items()):
        print(f"DEAD   {code}  {u}  (chips: {', '.join(found[u])})")
    for u, (code, final) in sorted(throttled.items()):
        print(f"RETRY  429  {u}  (rate limited, run again; chips: {', '.join(found[u])})")
    for u, (code, final) in sorted(moved.items()):
        print(f"MOVED  {u}\n       -> {final}  (chips: {', '.join(found[u])})")
    print(f"{len(res)} links: {len(res) - len(dead) - len(throttled)} answer 200, {len(dead)} dead, {len(throttled)} rate limited, {len(moved)} redirected")
    ev = evidence()
    if ev:
        with ThreadPoolExecutor(8) as ex:
            got = list(ex.map(lambda e: probe(e[3]), ev))
        print("\nalert evidence (observed answer now):")
        for (chip, kind, observed, url), (code, final) in zip(ev, got):
            note = ""
            if kind in ("broken-link", "removed") and code == 200 and url.startswith(("https://github.com/", "https://api.github.com/")) and "/issues/" not in url:
                note = "   <- answers 200 now: the alert may be obsolete"
            print(f"  {chip:14} {kind:12} observed {observed}  now {code}  {url}{note}")
    if dead and "--strict" in sys.argv:
        sys.exit(1)


if __name__ == "__main__":
    main()
