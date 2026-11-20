#!/usr/bin/env python3
"""Acceptance test: the map follows the window continuously. Drives Chrome through the DevTools Protocol (no libraries), resizes the
window many times WITHOUT reloading and measures the chip font, the number of columns, the size of the map and the page scroll after each change.

    python3 scripts/test_resize.py                  # tests docs/index.html (default size mode)
    python3 scripts/test_resize.py --size normal    # another size mode
    python3 scripts/test_resize.py --url URL        # another page

Checks (Fit to screen, the default): the scale (chip font) changed with the window, and the page does not scroll in windows of 1000x600 or more.
With --size normal or large (a fixed font, may scroll) the table is printed and nothing is checked.
Exit code 1 if a check fails. Needs Chrome or Chromium (CHROME=/path/to/chrome).
"""
import argparse
import base64
import http.client
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]
SIZES = [(1920, 1080), (1440, 900), (1280, 720), (1000, 700), (1600, 1200), (2560, 900), (1000, 1200), (1366, 768), (1000, 600), (1920, 1080)]
JS = """(function(){var b=document.querySelector('.board'),c=b.querySelector('.chip'),se=document.scrollingElement,
 cols=[].filter.call(b.querySelectorAll('.cols > .col'),function(x){return x.firstElementChild}).length,r=b.getBoundingClientRect();
 return JSON.stringify({w:innerWidth,h:innerHeight,font:parseFloat(getComputedStyle(c).fontSize),cols:cols,bw:Math.round(r.width),bh:Math.round(r.height),
  bottom:Math.round(r.bottom+pageYOffset),scrollY:se.scrollHeight-se.clientHeight,scrollX:se.scrollWidth-se.clientWidth,
  notice:!!document.querySelector('.small-window:not([hidden])')})})()"""


class WS:
    """Just enough of a WebSocket client for the DevTools Protocol."""
    def __init__(self, host, port, path):
        self.s = socket.create_connection((host, port), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(1)
        if b" 101 " not in buf.split(b"\r\n")[0]:
            raise RuntimeError("websocket handshake failed")
        self.n = 0

    def send(self, obj):
        data = json.dumps(obj).encode()
        head = bytearray([0x81])
        mask = os.urandom(4)
        if len(data) < 126:
            head.append(0x80 | len(data))
        elif len(data) < 65536:
            head += bytes([0x80 | 126]) + struct.pack(">H", len(data))
        else:
            head += bytes([0x80 | 127]) + struct.pack(">Q", len(data))
        self.s.sendall(bytes(head) + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _read(self, n):
        out = b""
        while len(out) < n:
            chunk = self.s.recv(n - len(out))
            if not chunk:
                raise RuntimeError("connection closed")
            out += chunk
        return out

    def recv(self):
        payload = b""
        while True:
            b1, b2 = self._read(2)
            ln = b2 & 0x7F
            if ln == 126:
                ln = struct.unpack(">H", self._read(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", self._read(8))[0]
            payload += self._read(ln)
            if b1 & 0x80:
                return json.loads(payload.decode())

    def call(self, method, **params):
        self.n += 1
        self.send({"id": self.n, "method": method, "params": params})
        while True:
            m = self.recv()
            if m.get("id") == self.n:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result", {})


def find_chrome():
    for c in [os.environ.get("CHROME")] + CANDIDATES:
        if c and (Path(c).exists() or shutil.which(c)):
            return c
    sys.exit("Chrome not found: set CHROME=/path/to/chrome")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=(ROOT / "docs" / "index.html").as_uri())
    ap.add_argument("--size", default="", help="fit | normal | large (default: the page's own default)")
    ap.add_argument("--port", type=int, default=9333)
    ap.add_argument("--settle", type=float, default=0.7, help="seconds to wait after each resize")
    a = ap.parse_args()
    url = a.url + ("?" if "?" not in a.url else "&") + "lang=en" + (f"&size={a.size}" if a.size else "")
    tmp = tempfile.mkdtemp()
    if True:
        proc = subprocess.Popen([find_chrome(), "--headless=new", "--disable-gpu", f"--remote-debugging-port={a.port}", f"--user-data-dir={tmp}", "about:blank"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            target = None
            for _ in range(50):
                try:
                    c = http.client.HTTPConnection("127.0.0.1", a.port, timeout=2)
                    c.request("GET", "/json")
                    pages = [t for t in json.loads(c.getresponse().read()) if t.get("type") == "page"]
                    if pages:
                        target = pages[0]
                        break
                except OSError:
                    pass
                time.sleep(0.2)
            if not target:
                sys.exit("could not reach Chrome")
            ws = WS("127.0.0.1", a.port, target["webSocketDebuggerUrl"].split(str(a.port), 1)[1])
            ws.call("Page.enable")
            ws.call("Emulation.setDeviceMetricsOverride", width=SIZES[0][0], height=SIZES[0][1], deviceScaleFactor=1, mobile=False)
            ws.call("Page.navigate", url=url)
            for _ in range(60):
                if ws.call("Runtime.evaluate", expression="document.readyState === 'complete' && !!document.querySelector('.cols.js')")["result"].get("value"):
                    break
                time.sleep(0.2)
            time.sleep(a.settle)
            rows = []
            for w, h in SIZES:
                ws.call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=False)   # a resize, no reload
                time.sleep(a.settle)
                rows.append(json.loads(ws.call("Runtime.evaluate", expression=JS)["result"]["value"]))
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            shutil.rmtree(tmp, ignore_errors=True)
    print(f"{'window':>10} {'font':>6} {'cols':>4} {'board':>11} {'bottom':>6} {'scrollY':>7} {'scrollX':>7}")
    for r in rows:
        print(f"{r['w']}x{r['h']:<5} {r['font']:6.1f} {r['cols']:4d} {r['bw']}x{r['bh']:<6} {r['bottom']:6d} {r['scrollY']:7d} {r['scrollX']:7d}" + ("  small-window notice" if r["notice"] else ""))
    if a.size in ("normal", "large"):
        print("\n(fixed-font mode: measurements only)")
        sys.exit(0)
    fonts = {round(r["font"], 1) for r in rows}
    bad = []
    if len(fonts) < 4:
        bad.append(f"the scale did not follow the window: only {len(fonts)} different chip fonts in {len(rows)} sizes")
    for r in rows:
        if r["w"] >= 1000 and r["h"] >= 600 and (r["scrollY"] > 0 or r["scrollX"] > 0):
            bad.append(f"{r['w']}x{r['h']}: the page scrolls (vertical {r['scrollY']}px, horizontal {r['scrollX']}px)")
    print("\n" + ("PASS" if not bad else "FAIL\n - " + "\n - ".join(bad)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
