#!/usr/bin/env python3
"""Builds docs/index.html (one static page, all languages inside) and refreshes the awesome lists in README.md / README.pt.md.

    python3 build.py
"""
import json
import sys
from html import escape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import awesome  # noqa: E402
import miniyaml  # noqa: E402

DEFAULT = "en"
SRC_ORDER = ["docs", "spec", "code", "papers", "blog", "status"]
CARET = '<svg class="caret" viewBox="0 0 10 6" aria-hidden="true" focusable="false"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
THEME_ICONS = {
    "auto": '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="5.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 2.5a5.5 5.5 0 0 0 0 11z" fill="currentColor"/></svg>',
    "light": '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="3" fill="currentColor"/><g stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M8 1.5v1.6M8 12.9v1.6M1.5 8h1.6M12.9 8h1.6M3.4 3.4l1.1 1.1M11.5 11.5l1.1 1.1M3.4 12.6l1.1-1.1M11.5 4.5l1.1-1.1"/></g></svg>',
    "dark": '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M13 9.6A5.6 5.6 0 0 1 6.4 3a5.6 5.6 0 1 0 6.6 6.6z" fill="currentColor"/></svg>',
}


def host(url):
    return urlparse(url).netloc.removeprefix("www.")


def load_langs():
    langs = {p.stem: miniyaml.load(p) for p in sorted((ROOT / "i18n").glob("*.yml"))}
    return {k: langs[k] for k in [DEFAULT] + sorted(k for k in langs if k != DEFAULT)}


def icon(name):
    return (ROOT / "assets" / "icons" / f"{name}.svg").read_text(encoding="utf-8").strip()


def meta_item(s, tx):
    return (f'<span class="m"><span>{escape(host(s["url"]))}</span><em data-t="ui.level.{s["level"]}">{escape(tx["ui.level." + s["level"]])}</em>'
            f'<time datetime="{s["accessed"]}">{s["accessed"]}</time></span>')


def menu_item(s, tx):
    return (f'<a role="menuitem" tabindex="-1" href="{escape(s["url"])}" target="_blank" rel="noopener">'
            f'<span class="t">{escape(s["title"])}</span>{meta_item(s, tx)}</a>')


def popover(c, tx, pid):
    name = tx[f"chip.{c['id']}"]
    body = "".join(menu_item(s, tx) for s in c["sources"] if not s.get("group"))
    for g in SRC_ORDER:
        items = [s for s in c["sources"] if s.get("group") == g]
        if items:
            label = escape(tx[f"srcgroup.{g}"])
            body += (f'<div role="group" aria-label="{label}" data-al="srcgroup.{g}"><div class="pg" aria-hidden="true" data-t="srcgroup.{g}">{label}</div>'
                     f'{"".join(menu_item(s, tx) for s in items)}</div>')
    label = escape(tx["ui.menu"].replace("{name}", name))
    return f'<div class="pop" id="{pid}" role="menu" aria-label="{label}" data-menu="{c["id"]}" hidden>{body}</div>'


def chip(c, tx):
    srcs = c["sources"]
    cid, name, status = c["id"], escape(tx[f"chip.{c['id']}"]), c.get("status")
    tag = f'<em class="tag" data-t="ui.status.{status}">{escape(tx[f"ui.status.{status}"])}</em>' if status else ""
    date = max(s["accessed"] for s in srcs)
    attrs = f'data-id="{cid}" data-n="{len(srcs)}" data-date="{date}"' + (f' data-status="{status}"' if status else "")
    label = f'<span class="n" data-t="chip.{cid}">{name}</span>{tag}'
    pid = f"pop-{cid}"
    return (f'<li><button type="button" class="chip" data-kind="tree" aria-haspopup="menu" aria-expanded="false" aria-controls="{pid}" {attrs}>{label}{CARET}</button>'
            f'{popover(c, tx, pid)}</li>')


def group(g, tx):
    return (f'<div class="group"><h3 data-t="group.{g["id"]}">{escape(tx[f"group.{g["id"]}"])}</h3>'
            f'<ul class="chips">{"".join(chip(c, tx) for c in g["chips"])}</ul></div>')


def columns(groups, tx, n, cls):
    cols = [[] for _ in range(n)]
    for g in groups:
        cols[g.get("col", 0)].append(group(g, tx))
    return f'<div class="{cls}">' + "".join(f'<div class="gcol">{"".join(c)}</div>' for c in cols) + "</div>"


def where(items, tx):
    out = []
    for w in items:
        i, s = w["id"], w["source"]
        out.append(f'<div class="where-item"><span class="glyph">{icon(w["icon"])}</span>'
                   f'<a href="{escape(s["url"])}" target="_blank" rel="noopener" data-kind="link" data-id="where-{i}" data-n="1" data-date="{s["accessed"]}" '
                   f'data-host="{escape(host(s["url"]))}" data-level="{s["level"]}" data-t="where.{i}.name">{escape(tx[f"where.{i}.name"])}</a>'
                   f'<p data-t="where.{i}.desc">{escape(tx[f"where.{i}.desc"])}</p></div>')
    return f'<div class="where"><h3 data-t="ui.where">{escape(tx["ui.where"])}</h3><div class="where-grid">{"".join(out)}</div></div>'


def card(L, tx):
    i = L["id"]
    if L["layout"] == "rows":
        rows = {}
        for g in L["groups"]:
            rows.setdefault(g["row"], []).append(g)
        body = "".join(f'<div class="grow n{len(gs)}">{"".join(group(g, tx) for g in gs)}</div>' for _, gs in sorted(rows.items()))
        if L.get("where"):
            body += where(L["where"], tx)
        if L.get("panel"):
            p = L["panel"]
            body += (f'<section class="panel"><div class="panel-h"><h3 data-t="panel.{p["id"]}">{escape(tx[f"panel.{p["id"]}"])}</h3>'
                     f'<span class="icon">{icon(p["icon"])}</span></div>{columns(p["groups"], tx, 3, "cols3")}</section>')
    else:
        body = columns(L["groups"], tx, 2, "cols2")
    n_chips = sum(len(g["chips"]) for g in L["groups"] + (L.get("panel") or {}).get("groups", []))
    return (f'<article class="card" id="layer-{i}" style="flex-grow:{n_chips + 8}"><span class="badge">{L["n"]}</span>'
            f'<div class="card-h"><h2 data-t="layer.{i}">{escape(tx[f"layer.{i}"])}</h2><span class="icon">{icon(L["icon"])}</span></div>'
            f'<div class="body">{body}</div>'
            f'<div class="decision" data-t="decision.{i}">{escape(tx[f"decision.{i}"])}</div></article>')


def main():
    langs = load_langs()
    tx = langs[DEFAULT]
    layers = miniyaml.load(ROOT / "data" / "layers.yml")["layers"]
    cols = {k: "".join(card(L, tx) for L in layers if L["column"] == k) for k in ("left", "center", "right")}
    all_groups = [g for L in layers for g in L["groups"] + (L.get("panel") or {}).get("groups", [])]
    reviewed = max(s["accessed"] for g in all_groups for c in g["chips"] for s in c["sources"])
    buttons = "".join(f'<button type="button" data-lang="{k}" aria-pressed="{str(k == DEFAULT).lower()}">{escape(v["lang.name"])}</button>' for k, v in langs.items())
    themes = "".join(f'<button type="button" data-theme-choice="{k}" aria-pressed="{str(k == "auto").lower()}" aria-label="{escape(tx["ui.theme." + k])}" data-al="ui.theme.{k}" '
                     f'title="{escape(tx["ui.theme." + k])}" data-tl="ui.theme.{k}">{THEME_ICONS[k]}</button>' for k in ("auto", "light", "dark"))
    board = (f'<div class="board" role="group" aria-label="{escape(tx["site.title"])}">'
             f'<div class="turn t1"><span class="tag-end" data-t="label.model">{escape(tx["label.model"])}</span></div><div class="turn t2"></div><div class="turn t3"></div>'
             f'<div class="col left">{cols["left"]}</div><div class="col center">{cols["center"]}</div><div class="col right">{cols["right"]}</div>'
             f'<div class="turn b1"></div><div class="turn b2"></div><div class="turn b3"><span class="tag-end" data-t="label.person">{escape(tx["label.person"])}</span></div></div>')
    html = f"""<!doctype html>
<html lang="{DEFAULT}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(tx["site.title"])}</title>
<meta name="description" content="{escape(tx["site.tagline"])}">
<script>
(function () {{ try {{ var q = new URLSearchParams(location.search), r = document.documentElement;
  var th = q.get("theme") || localStorage.getItem("webai-theme"); if (th === "light" || th === "dark") r.setAttribute("data-theme", th);
  if (!q.get("export") && q.get("fit") !== "0") r.classList.add("fit"); }} catch (e) {{}} }})();
</script>
<style>
{(ROOT / "assets" / "style.css").read_text(encoding="utf-8")}
</style>
</head>
<body>
<div class="page">
<header class="top">
<div><h1 data-t="site.title">{escape(tx["site.title"])}</h1><p data-t="site.tagline">{escape(tx["site.tagline"])}</p></div>
<div class="tools"><div class="seg themes" role="group" aria-label="{escape(tx["ui.theme"])}" data-al="ui.theme">{themes}</div>
<div class="seg langs" role="group" aria-label="{escape(tx["ui.language"])}" data-al="ui.language">{buttons}</div></div>
</header>
{board}
<footer class="foot">
<p data-t="ui.legend">{escape(tx["ui.legend"])}</p>
<p><span data-t="ui.reviewed">{escape(tx["ui.reviewed"])}</span>: {reviewed}</p>
<p data-t="ui.license">{escape(tx["ui.license"])}</p>
</footer>
</div>
<div id="tip" role="tooltip" hidden></div>
<script>window.__I18N__ = {json.dumps(langs, ensure_ascii=False)};</script>
<script>
{(ROOT / "assets" / "app.js").read_text(encoding="utf-8")}
</script>
</body>
</html>
"""
    out = ROOT / "docs" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({len(html) // 1024} KB, languages: {', '.join(langs)})")
    awesome.update()


if __name__ == "__main__":
    main()
