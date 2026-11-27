#!/usr/bin/env python3
"""Regenerate the five edition PNG/SVGs after python3 build.py. Requires local Chrome."""
import base64, html, http.client, json, re, socket, subprocess, tempfile, time
from pathlib import Path
from scripts.test_resize import WS, find_chrome
ROOT=Path(__file__).resolve().parent
DOCS=ROOT/'docs'
KINDS=('brutal','comic','construct','deco')
W,H=1600,1000
def start():
 with socket.socket() as s:
  s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
 profile=tempfile.TemporaryDirectory()
 proc=subprocess.Popen([find_chrome(),'--headless=new','--disable-gpu','--disable-background-networking','--no-first-run','--host-resolver-rules=MAP * ~NOTFOUND',f'--remote-debugging-port={port}',f'--user-data-dir={profile.name}','about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for i in range(60):
  try:
   c=http.client.HTTPConnection('127.0.0.1',port,timeout=2);c.request('GET','/json');tab=next(x for x in json.loads(c.getresponse().read()) if x['type']=='page');c.close();break
  except (OSError, StopIteration):time.sleep(.15)
 else: raise RuntimeError('Chrome did not start')
 ws=WS('127.0.0.1',port,tab['webSocketDebuggerUrl'].split(str(port),1)[1]);ws.call('Page.enable')
 return profile,proc,ws
profile,proc,ws=start()
def evaluate(s,await_result=False):
 r=ws.call('Runtime.evaluate',expression=s,returnByValue=True,awaitPromise=await_result)
 assert 'exceptionDetails' not in r,r
 return r['result'].get('value')
def resize(w,h):
 ws.call('Emulation.setDeviceMetricsOverride',width=w,height=h,deviceScaleFactor=1.25,mobile=False);time.sleep(.22)
def nav(path,expr):
 ws.call('Page.navigate',url=path)
 for _ in range(60):
  if evaluate("document.readyState==='complete' && ("+expr+")"): break
  time.sleep(.1)
 else:raise RuntimeError(path)
 evaluate("document.fonts.ready.then(()=>true)",True)
 time.sleep(.2)
def page_state():
 return evaluate("""(()=>{const r=document.querySelector('.board').getBoundingClientRect(),fr=document.querySelector('.foot').getBoundingClientRect(),se=document.scrollingElement;return {width:innerWidth,height:innerHeight,right:r.right,bottom:r.bottom,footer:fr.bottom,sx:se.scrollWidth,sy:se.scrollHeight,controls:document.querySelectorAll('button[data-edition-size]').length,items:document.querySelectorAll('.board .chip').length,refs:document.querySelectorAll('.board [role=menuitem][href]').length}})()""")
def css_with_fonts(css):
 def emb(m):
  return 'url(data:font/woff2;base64,'+base64.b64encode((DOCS/m[1]).read_bytes()).decode()+')'
 return re.sub(r'url\((fonts/[^)]+)\)',emb,css)
def write_figure(kind,lang):
 stem=f'figure-{kind}-{lang}'
 png=DOCS/(stem+'.png')
 png.write_bytes(base64.b64decode(ws.call('Page.captureScreenshot',format='png',captureBeyondViewport=False)['data']))
 fragment=evaluate("""(()=>{const page=document.querySelector('.page').cloneNode(true);page.querySelectorAll('.top .bar,.pop,.mobile-map,.mobile-map-back').forEach(x=>x.remove());return {page:new XMLSerializer().serializeToString(page), css:[...document.querySelectorAll('style')].map(x=>x.textContent).join('\n'), bg:getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()}})()""".replace("join('\n')","join('\\n')"))
 css=css_with_fonts(fragment['css']).replace(']]>',']]]]><![CDATA[>')
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="State of the Art of WebAI">
<rect width="{W}" height="{H}" fill="{html.escape(fragment['bg'])}"/>
<foreignObject x="0" y="0" width="{W}" height="{H}">
<html xmlns="http://www.w3.org/1999/xhtml" lang="{lang}" data-edition="{kind}" data-theme="light" class="edition-figure"><head><style><![CDATA[{css}]]></style></head><body>{fragment['page']}</body></html>
</foreignObject></svg>'''
 (DOCS/(stem+'.svg')).write_text(svg)
try:
 for kind in KINDS:
  for lang in ('pt','en'):
   resize(W,H)
   nav((DOCS/'index.html').as_uri()+f'?figure=1&edicao={kind}&lang={lang}&motion=0',f'document.documentElement.dataset.edition==="{kind}"')
   st=page_state();assert st['sy']==H and st['sx']==W and st['items']==101 and st['refs']==261 and st['controls']==0,st
   write_figure(kind,lang)
  nav((DOCS/'index.html').as_uri()+f'?edicao={kind}&lang=pt&motion=0',f'document.documentElement.dataset.edition==="{kind}"')
  for w,h in ((1024,768),(1280,720),(1366,768),(1440,900),(1536,730),(1600,1000),(1920,1080)):
   resize(w,h); st=page_state()
   assert st['width']==w and st['height']==h and st['sx']==w and st['sy']==h and st['controls']==0,st
   assert 0<=h-st['footer']<=20,(kind,st)
  assert evaluate(f"[...document.querySelectorAll('[data-dl]')].every(a=>a.href.includes('figure-{kind}-pt.'))")
  print(kind,'desktop fit + themed PNG/SVG links verified',flush=True)

finally:
 proc.terminate();proc.wait(timeout=10);profile.cleanup()
