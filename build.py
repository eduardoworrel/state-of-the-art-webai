#!/usr/bin/env python3
"""Builds docs/index.html (one static page, all languages inside) and refreshes the awesome lists in README.md / README.pt.md.

    python3 build.py
"""
import json
import re
import sys
import tomllib
from html import escape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import awesome  # noqa: E402
import miniyaml  # noqa: E402

DEFAULT = "en"
SITE = tomllib.loads((ROOT / "site.toml").read_text(encoding="utf-8"))
BASE = SITE["base_url"]
assert BASE.endswith("/"), "base_url in site.toml must end with a slash"
SRC_ORDER = ["docs", "spec", "code", "papers", "blog", "status"]
CARET = '<svg class="caret" viewBox="0 0 10 6" aria-hidden="true" focusable="false"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
THEME_ICONS = {
    "auto": '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="5.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 2.5a5.5 5.5 0 0 0 0 11z" fill="currentColor"/></svg>',
    "light": '<svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="3" fill="currentColor"/><g stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><path d="M8 1.5v1.6M8 12.9v1.6M1.5 8h1.6M12.9 8h1.6M3.4 3.4l1.1 1.1M11.5 11.5l1.1 1.1M3.4 12.6l1.1-1.1M11.5 4.5l1.1-1.1"/></g></svg>',
    "dark": '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M13 9.6A5.6 5.6 0 0 1 6.4 3a5.6 5.6 0 1 0 6.6 6.6z" fill="currentColor"/></svg>',
}


ALERT_ICONS = {
    "critical": '<svg class="ai" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M5.2 1h5.6L15 5.2v5.6L10.8 15H5.2L1 10.8V5.2z" fill="currentColor"/><path class="g" d="M8 4.4v4.3M8 10.6v1.1" fill="none" stroke-width="1.7" stroke-linecap="round"/></svg>',
    "warning": '<svg class="ai" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M8 1.3l7.2 12.6H.8z" fill="currentColor" stroke="currentColor" stroke-width="1" stroke-linejoin="round"/><path class="g" d="M8 5.8v3.9M8 11.4v.9" fill="none" stroke-width="1.7" stroke-linecap="round"/></svg>',
    "info": '<svg class="ai" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><circle cx="8" cy="8" r="7" fill="currentColor"/><path class="g" d="M8 7.2v4.2" fill="none" stroke-width="1.7" stroke-linecap="round"/><circle class="gf" cx="8" cy="4.7" r="1"/></svg>',
}


def short(url, n=46):
    u = url.split("://", 1)[1].removeprefix("www.")
    return u if len(u) <= n else u[: n - 22] + "…" + u[-20:]


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


def alert_title(a, tx):
    return (f'<span data-t="ui.alert.level.{a["level"]}">{escape(tx["ui.alert.level." + a["level"]])}</span> · '
            f'<span data-t="ui.alert.kind.{a["kind"]}">{escape(tx["ui.alert.kind." + a["kind"]])}</span>')


def popover(c, tx, pid):
    cid, name, a = c["id"], tx[f"chip.{c['id']}"], c.get("alert")
    srcs = c["sources"]
    date = max(s_["accessed"] for s_ in srcs)
    status = c.get("status")
    tag = f'<em class="tag" data-t="ui.status.{status}">{escape(tx[f"ui.status.{status}"])}</em>' if status else ""
    head = (f'<div class="pop-head"><div class="ph-top"><strong data-t="chip.{cid}">{escape(name)}</strong>{tag}</div>'
            f'<p class="ph-desc" data-t="desc.{cid}">{escape(tx[f"desc.{cid}"])}</p>'
            f'<p class="ph-meta" data-date="{date}" data-n="{len(srcs)}">{escape(tx["ui.reviewed.short"])} {date} · {len(srcs)} {escape(tx["ui.sources.other"].replace("{n} ", ""))}</p></div>')
    alert, evidence = "", ""
    if a:
        alert = (f'<div class="pop-alert" role="group" aria-labelledby="al-{cid}"><div class="al-title" id="al-{cid}"><span class="al" data-level="{a["level"]}">{ALERT_ICONS[a["level"]]}</span>'
                 f'<span class="sr" data-t="ui.alert">{escape(tx["ui.alert"])}: </span>{alert_title(a, tx)}</div>'
                 f'<p class="al-text" data-t="alert.{cid}">{escape(tx[f"alert.{cid}"])}</p>'
                 f'<p class="al-meta"><span data-t="ui.alert.observed">{escape(tx["ui.alert.observed"])}</span> <time datetime="{a["observed"]}">{a["observed"]}</time></p></div>')
        ev = "".join(f'<a role="menuitem" tabindex="-1" class="ev" href="{escape(u)}" target="_blank" rel="noopener">{escape(short(u))}</a>' for u in a["evidence"])
        evidence = (f'<div role="group" aria-label="{escape(tx["ui.alert.evidence"])}" data-al="ui.alert.evidence" class="ev-group">'
                    f'<div class="pg" aria-hidden="true" data-t="ui.alert.evidence">{escape(tx["ui.alert.evidence"])}</div>{ev}</div>')
    body = "".join(menu_item(s_, tx) for s_ in srcs if not s_.get("group"))
    for g in SRC_ORDER:
        items = [s_ for s_ in srcs if s_.get("group") == g]
        if items:
            label = escape(tx[f"srcgroup.{g}"])
            body += (f'<div role="group" aria-label="{label}" data-al="srcgroup.{g}"><div class="pg" aria-hidden="true" data-t="srcgroup.{g}">{label}</div>'
                     f'{"".join(menu_item(s_, tx) for s_ in items)}</div>')
    actions = (f'<div role="group" aria-label="{escape(tx["ui.actions"])}" data-al="ui.actions" class="pop-actions"><div class="pg" aria-hidden="true" data-t="ui.actions">{escape(tx["ui.actions"])}</div>'
               f'<button type="button" role="menuitem" tabindex="-1" data-act="copy-chip" data-chip="{cid}"><span data-t="ui.chip.copy">{escape(tx["ui.chip.copy"])}</span></button>'
               f'<a role="menuitem" tabindex="-1" data-suggest="{cid}" href="#" target="_blank" rel="noopener noreferrer"><span data-t="ui.suggest.chip">{escape(tx["ui.suggest.chip"])}</span></a></div>')
    label = escape(tx["ui.menu"].replace("{name}", name))
    lvl = f' data-alert="{a["level"]}"' if a else ""
    return (f'<div class="pop" id="{pid}" data-menu="{cid}"{lvl} hidden>{head}{alert}'
            f'<div role="menu" id="menu-{cid}" aria-label="{label}" data-menu-label="{cid}">{evidence}{body}{actions}</div></div>')


def chip(c, tx):
    srcs = c["sources"]
    cid, name, status, a = c["id"], escape(tx[f"chip.{c['id']}"]), c.get("status"), c.get("alert")
    tag = f'<em class="tag" data-t="ui.status.{status}">{escape(tx[f"ui.status.{status}"])}</em>' if status else ""
    date = max(s["accessed"] for s in srcs)
    attrs = f'data-id="{cid}" data-n="{len(srcs)}" data-date="{date}"' + (f' data-status="{status}"' if status else "") + (f' data-alert="{a["level"]}"' if a else "")
    mark = ""
    if a:
        mark = (f'<span class="al" data-level="{a["level"]}">{ALERT_ICONS[a["level"]]}</span>'
                f'<span class="sr"><span data-t="ui.alert">{escape(tx["ui.alert"])}</span>: {alert_title(a, tx)}. </span>')
    label = f'{mark}<span class="n" data-t="chip.{cid}">{name}</span>{tag}'
    return (f'<li><button type="button" class="chip" data-kind="tree" aria-haspopup="menu" aria-expanded="false" aria-controls="menu-{cid}" {attrs}>{label}{CARET}</button>'
            f'{popover(c, tx, "pop-" + cid)}</li>')


def shown(g):
    return [c for c in g["chips"] if c.get("featured", True)]


def group(g, tx):
    if not shown(g):
        return ""
    return (f'<div class="group"><h3 data-t="group.{g["id"]}">{escape(tx[f"group.{g["id"]}"])}</h3>'
            f'<ul class="chips">{"".join(chip(c, tx) for c in shown(g))}</ul></div>')


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
    body = f'<div class="groups">{"".join(group(g, tx) for g in L["groups"])}</div>'
    if L["layout"] == "rows":
        if L.get("where"):
            body += where(L["where"], tx)
        if L.get("panel"):
            p = L["panel"]
            body += (f'<section class="panel"><div class="panel-h"><h3 data-t="panel.{p["id"]}">{escape(tx[f"panel.{p["id"]}"])}</h3>'
                     f'<span class="icon">{icon(p["icon"])}</span></div><div class="groups">{"".join(group(g, tx) for g in p["groups"])}</div></section>')
    n_chips = sum(len(shown(g)) for g in L["groups"] + (L.get("panel") or {}).get("groups", []))
    return (f'<article class="card" id="layer-{i}" data-n="{L["n"]}" style="flex-grow:{n_chips + 8}"><span class="badge">{L["n"]}</span>'
            f'<div class="card-h"><h2 data-t="layer.{i}">{escape(tx[f"layer.{i}"])}</h2><span class="icon">{icon(L["icon"])}</span></div>'
            f'<div class="body">{body}</div>'
            f'<div class="decision" data-t="decision.{i}">{escape(tx[f"decision.{i}"])}</div></article>')


def menus(tx):
    t_ = lambda k: escape(tx[k])
    def item_a(attr, key, extra=""):
        return f'<a role="menuitem" tabindex="-1" {attr} target="_blank" rel="noopener noreferrer" {extra}><span data-t="{key}">{t_(key)}</span></a>'
    share = (f'<div class="pop pop-sm" id="pop-share" hidden><div role="menu" id="menu-share" aria-label="{t_("ui.share")}" data-al="ui.share">'
             f'<button type="button" role="menuitem" tabindex="-1" data-act="native" hidden><span data-t="ui.share.native">{t_("ui.share.native")}</span></button>'
             f'<button type="button" role="menuitem" tabindex="-1" data-act="copy"><span data-t="ui.share.copy">{t_("ui.share.copy")}</span></button>'
             + item_a('data-share="linkedin" href="#"', "ui.share.linkedin") + item_a('data-share="x" href="#"', "ui.share.x") + item_a('data-share="email" href="#"', "ui.share.email") + "</div></div>")
    dl = "".join(f'<a role="menuitem" tabindex="-1" data-dl="{fmt}-{th}" href="#" download>{fmt.upper()} · <span data-t="ui.theme.{th}">{t_("ui.theme." + th)}</span></a>' for fmt in ("png", "svg") for th in ("light", "dark"))
    download = f'<div class="pop pop-sm" id="pop-download" hidden><div role="menu" id="menu-download" aria-label="{t_("ui.download")}" data-al="ui.download">{dl}</div></div>'
    suggest = (f'<div class="pop pop-sm" id="pop-suggest" hidden><div role="menu" id="menu-suggest" aria-label="{t_("ui.suggest")}" data-al="ui.suggest">'
               + item_a('data-suggest="" href="#"', "ui.suggest.issue") + item_a('data-edit="" href="#"', "ui.suggest.edit") + "</div></div>")
    def block(key, kind):
        return (f'<section class="emb"><h3 data-t="ui.embed.{key}">{t_("ui.embed." + key)}</h3><pre><code data-snippet="{kind}"></code></pre>'
                f'<button type="button" class="btn sm" data-copy-snippet="{kind}"><span data-t="ui.embed.copy">{t_("ui.embed.copy")}</span></button></section>')
    embed = (f'<div class="pop pop-embed" id="pop-embed" role="dialog" aria-modal="false" aria-labelledby="embed-title" hidden>'
             f'<div class="emb-head"><h2 id="embed-title" data-t="ui.embed.title">{t_("ui.embed.title")}</h2>'
             f'<button type="button" class="btn sm" data-close-pop><span data-t="ui.embed.close">{t_("ui.embed.close")}</span></button></div>'
             + block("iframe", "iframe") + block("component", "component") + block("image", "image") + block("badge", "badge")
             + f'<p class="emb-credit" data-t="ui.embed.credit">{t_("ui.embed.credit")}</p></div>')
    return share + download + suggest + embed


def actions_bar(tx, reviewed):
    t_ = lambda k: escape(tx[k])
    def mbtn(key, pop, extra=""):
        return (f'<button type="button" class="btn" aria-haspopup="menu" aria-expanded="false" aria-controls="menu-{pop}" data-menu-btn="{pop}" {extra}>'
                f'<span data-t="ui.{key}">{t_("ui." + key)}</span>{CARET}</button>')
    embed = (f'<button type="button" class="btn" aria-haspopup="dialog" aria-expanded="false" aria-controls="pop-embed" data-menu-btn="embed"><span data-t="ui.embed">{t_("ui.embed")}</span></button>')
    return (f'<div class="actions" role="group" aria-label="{t_("ui.actions")}" data-al="ui.actions">{mbtn("share", "share")}{embed}{mbtn("download", "download")}{mbtn("suggest", "suggest")}'
            f'<span class="reviewed"><span data-t="ui.reviewed.short">{t_("ui.reviewed.short")}</span> <time datetime="{reviewed}">{reviewed}</time></span></div>')


def render(embed=False):
    langs = load_langs()
    tx = langs[DEFAULT]
    layers = miniyaml.load(ROOT / "data" / "layers.yml")["layers"]
    cols = {k: "".join(card(L, tx) for L in layers if L["column"] == k) for k in ("left", "center", "right")}
    all_groups = [g for L in layers for g in L["groups"] + (L.get("panel") or {}).get("groups", [])]
    reviewed = max(s["accessed"] for g in all_groups for c in g["chips"] for s in c["sources"])
    buttons = "".join(f'<button type="button" data-lang="{k}" aria-pressed="{str(k == DEFAULT).lower()}">{escape(v["lang.name"])}</button>' for k, v in langs.items())
    themes = "".join(f'<button type="button" data-theme-choice="{k}" aria-pressed="{str(k == "auto").lower()}" aria-label="{escape(tx["ui.theme." + k])}" data-al="ui.theme.{k}" '
                     f'title="{escape(tx["ui.theme." + k])}" data-tl="ui.theme.{k}">{THEME_ICONS[k]}</button>' for k in ("auto", "light", "dark"))
    sizes = "".join(f'<button type="button" data-size-choice="{k}" aria-pressed="{str(k == "normal").lower()}" aria-label="{escape(tx["ui.size." + k])}" data-al="ui.size.{k}" '
                    f'title="{escape(tx["ui.size." + k])}" data-tl="ui.size.{k}"><span data-t="ui.size.{k}.short">{escape(tx["ui.size." + k + ".short"])}</span></button>' for k in ("fit", "normal", "large"))
    board = (f'<div class="board" role="group" aria-label="{escape(tx["site.title"])}">'
             f'<span class="tag-end" id="tag-model" data-t="label.model">{escape(tx["label.model"])}</span><span class="tag-end" id="tag-person" data-t="label.person">{escape(tx["label.person"])}</span>'
             f'<div class="cols"><div class="col">{cols["left"]}</div><div class="col">{cols["center"]}</div><div class="col">{cols["right"]}</div></div></div>')
    css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
    site = {"base": BASE, "repo": SITE["repo"], "branch": SITE.get("branch", "main"), "reviewed": reviewed}
    alt = "".join(f'<link rel="alternate" hreflang="{k}" href="{BASE}?lang={k}">' for k in langs)
    if embed:
        head_extra = '<meta name="robots" content="noindex">'
        header = footer = ""
        html_attr = ' class="embed"'
    else:
        html_attr = ""
        head_extra = (f'<link rel="canonical" href="{BASE}">{alt}<meta property="og:type" content="website"><meta property="og:title" content="{escape(tx["site.title"])}">'
                      f'<meta property="og:description" content="{escape(tx["site.tagline"])}"><meta property="og:url" content="{BASE}"><meta property="og:image" content="{BASE}figure-en.png">')
        header = (f'<header class="top"><div class="intro"><h1 data-t="site.title">{escape(tx["site.title"])}</h1><p data-t="site.tagline">{escape(tx["site.tagline"])}</p></div>'
                  f'<div class="tools"><div class="tools-row"><div class="seg sizes" role="group" aria-label="{escape(tx["ui.size"])}" data-al="ui.size">{sizes}</div>'
                  f'<div class="seg themes" role="group" aria-label="{escape(tx["ui.theme"])}" data-al="ui.theme">{themes}</div>'
                  f'<div class="seg langs" role="group" aria-label="{escape(tx["ui.language"])}" data-al="ui.language">{buttons}</div></div>'
                  f'{actions_bar(tx, reviewed)}</div></header>')
        footer = (f'<footer class="foot"><p data-t="ui.legend">{escape(tx["ui.legend"])}</p>'
                  f'<p><span data-t="ui.reviewed">{escape(tx["ui.reviewed"])}</span>: {reviewed}</p><p data-t="ui.license">{escape(tx["ui.license"])}</p></footer>')
    return f"""<!doctype html>
<html lang="{DEFAULT}"{html_attr}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(tx["site.title"])}</title>
<meta name="description" content="{escape(tx["site.tagline"])}">
{head_extra}
<script>
(function () {{ try {{ var q = new URLSearchParams(location.search), r = document.documentElement;
  var th = q.get("theme") || localStorage.getItem("webai-theme"); if (th === "light" || th === "dark") r.setAttribute("data-theme", th);
  if (!q.get("export")) {{ var z = q.get("size") || (q.get("fit") === "0" ? "large" : localStorage.getItem("webai-size"));
    r.classList.add("sized"); r.setAttribute("data-size", z === "fit" || z === "large" ? z : "normal"); }} }} catch (e) {{ document.documentElement.classList.add("sized"); document.documentElement.setAttribute("data-size", "normal"); }} }})();
</script>
<style>
{css}
</style>
</head>
<body>
<div class="page">
{header}
{board}
{footer}
</div>
{'' if embed else menus(tx)}
<div id="tip" role="tooltip" hidden></div>
<script>window.__I18N__ = {json.dumps(langs, ensure_ascii=False)}; window.__SITE__ = {json.dumps(site)};</script>
<script>
{(ROOT / "assets" / "app.js").read_text(encoding="utf-8")}
</script>
</body>
</html>
""", langs, reviewed


def badge_svg():
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="236" height="28" role="img" aria-label="State of the Art of WebAI">'
            '<title>State of the Art of WebAI</title><rect width="236" height="28" rx="6" fill="#1b1a18"/><rect x="0" width="68" height="28" rx="6" fill="#c4622d"/><rect x="40" width="28" height="28" fill="#c4622d"/>'
            '<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" font-size="12" font-weight="700" fill="#fff"><text x="12" y="18">WebAI</text>'
            '<text x="80" y="18" font-weight="600">State of the Art of WebAI</text></g></svg>\n')


def main():
    html, langs, reviewed = render(False)
    out = ROOT / "docs" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")
    (ROOT / "docs" / "embed").mkdir(exist_ok=True)
    (ROOT / "docs" / "embed" / "index.html").write_text(render(True)[0], encoding="utf-8")
    (ROOT / "docs" / "embed.js").write_text((ROOT / "assets" / "embed.js").read_text(encoding="utf-8"), encoding="utf-8")
    (ROOT / "docs" / "badge.svg").write_text(badge_svg(), encoding="utf-8")
    (ROOT / "docs" / "embed-example.html").write_text((ROOT / "assets" / "embed-example.html").read_text(encoding="utf-8"), encoding="utf-8")
    urls = [BASE] + [f"{BASE}?lang={k}" for k in langs] + [f"{BASE}embed/"]
    (ROOT / "docs" / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u.replace('&', '&amp;')}</loc><lastmod>{reviewed}</lastmod></url>\n" for u in urls) + "</urlset>\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({len(html) // 1024} KB, languages: {', '.join(langs)}), docs/embed/index.html, docs/embed.js, docs/badge.svg, docs/sitemap.xml; base {BASE}")
    awesome.update()


if __name__ == "__main__":
    main()
