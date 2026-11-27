#!/usr/bin/env python3
"""Browser smoke test for the three visual editions; optionally pass the deployed page URL."""
import http.client
import json
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from test_resize import WS, find_chrome

ROOT = Path(__file__).resolve().parent.parent
PAGE = sys.argv[1] if len(sys.argv) > 1 else (ROOT / "docs/index.html").as_uri()

def check(ws):
    def js(expression):
        response = ws.call("Runtime.evaluate", expression=expression, returnByValue=True, awaitPromise=True)
        assert "exceptionDetails" not in response, response
        return response["result"].get("value")

    def size(w, h):
        ws.call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=False)
        time.sleep(0.2)

    def navigate(url):
        ws.call("Page.navigate", url=url)
        for _ in range(60):
            if js("document.readyState === 'complete' && !!document.querySelector('.board')"):
                js("document.fonts.ready.then(()=>true)")
                return
            time.sleep(0.1)
        raise RuntimeError("The board did not load")

    def inventory():
        return js("""Array.from(document.querySelectorAll('.board .chip,[role=menuitem][href]')).map(
        e=>[e.dataset.id||'',e.dataset.status||'',e.dataset.alert||'',e.getAttribute('href')||''].join('|')).sort()""")

    def assert_source_menu(chip="open-weights"):
        result = js("""(() => {
          const button=document.querySelector('.board [data-id="__CHIP__"]');
          button.scrollIntoView({block:'nearest'});
          button.click();
          const pop=document.getElementById('pop-__CHIP__');
          const rect=pop.getBoundingClientRect(), font=parseFloat(getComputedStyle(pop).fontSize);
          const open=!pop.hidden && button.getAttribute('aria-expanded')==='true' && pop.querySelectorAll('[role=menuitem]').length>=2
            && (!document.documentElement.dataset.edition || pop.parentElement===document.body) && font>=13 && rect.left>=0 && rect.right<=innerWidth && rect.top>=0 && rect.bottom<=innerHeight;
          button.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
          return {open,closed:pop.hidden && button.getAttribute('aria-expanded')==='false',rect:rect.toJSON(),font,w:innerWidth,h:innerHeight};
        })()""".replace("__CHIP__", chip))
        assert result["open"] and result["closed"], (chip, result)

    size(1600, 1000)
    navigate(PAGE + "?lang=pt&motion=0")
    assert js("document.documentElement.dataset.edition") == "brutal"
    assert js("Array.from(document.querySelectorAll('[data-select-edition]')).map(b=>b.dataset.selectEdition)") == ["comic", "brutal"]
    baseline = inventory()
    assert len(baseline) > 350, len(baseline)
    for key in ("comic", "brutal"):
        js(f"document.querySelector('[data-select-edition={key}]').click()")
        assert js("document.documentElement.dataset.edition") == key
        assert js("new URL(location.href).searchParams.get('edicao')") == key
        assert js("getComputedStyle(document.querySelector('.chip')).fontSize") == "15px"
        assert js("document.scrollingElement.scrollHeight<=innerHeight && document.scrollingElement.scrollWidth<=innerWidth")
        assert js("document.querySelectorAll('.landscape-connections > .band').length") == 2
        assert inventory() == baseline
        assert_source_menu()
        for w, h in ((1920, 1080), (1440, 900), (1440, 820), (1366, 768), (1280, 720),
                     (1536, 730), (1000, 600), (820, 1180), (390, 844), (320, 568)):
            size(w, h)
            result = js("""(() => {
              const se=document.scrollingElement, board=document.querySelector('.board').getBoundingClientRect();
              return {w:innerWidth,h:innerHeight,scroll:[se.scrollWidth,se.scrollHeight],right:board.right,bottom:board.bottom,parts:[...document.querySelectorAll(".page,.top,.mobile-map,.mobile-map section,.foot")].map(x=>[x.className||x.dataset.mobileLane,x.getBoundingClientRect().height])};
            })()""")
            assert result["scroll"][0] <= w and result["scroll"][1] <= h, (key, result)
            assert result["right"] <= w + 1 and result["bottom"] <= h + 1, (key, result)
        assert js("""document.querySelectorAll('.mobile-map button[data-mobile-target]').length===10
          && getComputedStyle(document.querySelector('.mobile-map')).display!=='none'
          && parseFloat(getComputedStyle(document.querySelector('.mobile-map button')).fontSize)>=13
          && getComputedStyle(document.querySelector('.board')).display==='none'""")
        js("document.querySelector('[data-mobile-target=layer-expose]').click()")
        assert js("document.documentElement.dataset.editionSize==='read' && getComputedStyle(document.querySelector('.board')).display!=='none'")
        assert_source_menu("webmcp")
        js("document.querySelector('.mobile-map-back').click()")
        assert js("document.documentElement.dataset.editionSize==='fit' && scrollY===0")
        js("document.querySelector('button[data-edition-size]').click()")
        read_mode = js("[document.documentElement.dataset.editionSize,document.scrollingElement.scrollHeight,innerHeight,location.href]")
        assert read_mode[0] == "read" and read_mode[1] > read_mode[2], read_mode
        js("document.querySelector('button[data-edition-size]').click()")
        assert js("document.documentElement.dataset.editionSize==='fit' && document.scrollingElement.scrollHeight<=innerHeight")
        size(1600, 1000)
    js("document.querySelector('[data-lang=en]').click()")
    assert js("document.querySelector('.landscape-caption').textContent") == "Cross-cutting layers"
    assert js("decodeURIComponent(document.querySelector('[data-share=linkedin]').href).includes('edicao=brutal')")
    js("document.querySelector('[data-menu-btn=share]').click()")
    assert js("!document.querySelector('#pop-share').hidden")
    size(390, 844)
    assert js("document.querySelectorAll('.board > .band').length") == 2
    assert js("document.scrollingElement.scrollWidth<=innerWidth")
    assert inventory() == baseline
    size(1600, 1000)
    assert js("document.querySelectorAll('.landscape-connections > .band').length") == 2
    for former in ("rail", "sky"):
        navigate(PAGE + f"?lang=pt&edicao={former}&motion=0")
        assert js("document.documentElement.dataset.edition") == "brutal"
        assert inventory() == baseline
    navigate(PAGE + "?lang=pt&theme=dark&motion=0")
    assert js("!document.documentElement.hasAttribute('data-edition') && document.documentElement.dataset.theme==='dark'")
    assert inventory() == baseline
    navigate(PAGE + "?lang=pt&theme=dark&export=1&motion=0")
    assert js("!document.documentElement.hasAttribute('data-edition') && document.documentElement.classList.contains('export')")
    assert inventory() == baseline
    embed = (ROOT / "docs/embed/index.html").as_uri() if PAGE.startswith("file:") else PAGE.rstrip("/") + "/embed/"
    navigate(embed + "?lang=pt&theme=light&motion=0")
    assert js("document.documentElement.classList.contains('embed') && !document.documentElement.hasAttribute('data-edition')")
    assert inventory() == baseline
    assert_source_menu()

with tempfile.TemporaryDirectory() as profile:
    with socket.socket() as reserve:
        reserve.bind(("127.0.0.1", 0))
        port = reserve.getsockname()[1]
    proc = subprocess.Popen([find_chrome(), "--headless=new", "--disable-gpu", "--no-first-run",
                             "--disable-background-networking", f"--remote-debugging-port={port}",
                             f"--user-data-dir={profile}", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):
            try:
                client = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
                client.request("GET", "/json")
                tab = next(page for page in json.loads(client.getresponse().read()) if page["type"] == "page")
                client.close()
                break
            except (OSError, StopIteration):
                time.sleep(0.15)
        else:
            raise RuntimeError("Chrome didn't start")
        ws = WS("127.0.0.1", port, tab["webSocketDebuggerUrl"].split(str(port), 1)[1])
        ws.call("Page.enable")
        check(ws)
    finally:
        proc.terminate()
        proc.wait(timeout=10)
print("PASS: 2 editions, sources, languages, share, narrow layout, classic, export and embed")
