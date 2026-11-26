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
# Alert kinds the reader never sees: the source is broken, which helps whoever contributes, not whoever reads. They show with ?contribuir=1 (or ?contribute=1).
READER_HIDDEN = {"broken-link"}
SRC_ORDER = ["docs", "spec", "code", "papers", "blog", "status"]
CARET = '<svg class="caret" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><circle cx="8" cy="8" r="6.6" fill="none" stroke="currentColor" stroke-width="1.3"/><circle cx="8" cy="4.9" r="0.95" fill="currentColor"/><path d="M8 7.4v4.2" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
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
    co = " hidden data-contrib-only" if a and a["kind"] in READER_HIDDEN else ""
    if a:
        alert = (f'<div class="pop-alert"{co} role="group" aria-labelledby="al-{cid}"><div class="al-title" id="al-{cid}"><span class="al" data-level="{a["level"]}">{ALERT_ICONS[a["level"]]}</span>'
                 f'<span class="sr" data-t="ui.alert">{escape(tx["ui.alert"])}: </span>{alert_title(a, tx)}</div>'
                 f'<p class="al-text" data-t="alert.{cid}">{escape(tx[f"alert.{cid}"])}</p>'
                 f'<p class="al-meta"><span data-t="ui.alert.observed">{escape(tx["ui.alert.observed"])}</span> <time datetime="{a["observed"]}">{a["observed"]}</time></p></div>')
        ev = "".join(f'<a role="menuitem" tabindex="-1" class="ev" href="{escape(u)}" target="_blank" rel="noopener">{escape(short(u))}</a>' for u in a["evidence"])
        evidence = (f'<div{co} role="group" aria-label="{escape(tx["ui.alert.evidence"])}" data-al="ui.alert.evidence" class="ev-group">'
                    f'<div class="pg" aria-hidden="true" data-t="ui.alert.evidence">{escape(tx["ui.alert.evidence"])}</div>{ev}</div>')
    body = "".join(menu_item(s_, tx) for s_ in srcs if not s_.get("group"))
    for g in SRC_ORDER:
        items = [s_ for s_ in srcs if s_.get("group") == g]
        if items:
            label = escape(tx[f"srcgroup.{g}"])
            body += (f'<div role="group" aria-label="{label}" data-al="srcgroup.{g}"><div class="pg" aria-hidden="true" data-t="srcgroup.{g}">{label}</div>'
                     f'{"".join(menu_item(s_, tx) for s_ in items)}</div>')
    label = escape(tx["ui.menu"].replace("{name}", name))
    lvl = f' data-alert{"-c" if co else ""}="{a["level"]}"' if a else ""
    return (f'<div class="pop" id="{pid}" data-menu="{cid}"{lvl} hidden>{head}{alert}'
            f'<div role="menu" id="menu-{cid}" aria-label="{label}" data-menu-label="{cid}">{evidence}{body}</div></div>')


def chip(c, tx):
    srcs = c["sources"]
    cid, name, status, a = c["id"], escape(tx[f"chip.{c['id']}"]), c.get("status"), c.get("alert")
    tag = f'<em class="tag" data-t="ui.status.{status}">{escape(tx[f"ui.status.{status}"])}</em>' if status else ""
    date = max(s["accessed"] for s in srcs)
    co = " hidden data-contrib-only" if a and a["kind"] in READER_HIDDEN else ""
    attrs = f'data-id="{cid}" data-n="{len(srcs)}" data-date="{date}"' + (f' data-status="{status}"' if status else "") + (f' data-alert{"-c" if co else ""}="{a["level"]}"' if a else "")
    mark = ""
    if a:
        mark = (f'<span class="al"{co} data-level="{a["level"]}">{ALERT_ICONS[a["level"]]}</span>'
                f'<span class="sr"{co}><span data-t="ui.alert">{escape(tx["ui.alert"])}</span>: {alert_title(a, tx)}. </span>')
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


def where(items, tx):
    out = []
    for w in items:
        i, s = w["id"], w["source"]
        out.append(f'<div class="where-item"><span class="glyph">{icon(w["icon"])}</span>'
                   f'<a href="{escape(s["url"])}" target="_blank" rel="noopener" data-kind="link" data-id="where-{i}" data-n="1" data-date="{s["accessed"]}" '
                   f'data-host="{escape(host(s["url"]))}" data-level="{s["level"]}" data-t="where.{i}.name">{escape(tx[f"where.{i}.name"])}</a>'
                   f'<p data-t="where.{i}.desc">{escape(tx[f"where.{i}.desc"])}</p></div>')
    return f'<div class="where"><h3 data-t="ui.where">{escape(tx["ui.where"])}</h3><div class="where-grid">{"".join(out)}</div></div>'


LANES = ("build", "use", "agents")
LETTER = {"build": "A", "use": "B", "agents": "C"}
VARROW = ('<svg class="varrow" viewBox="0 0 20 32" aria-hidden="true" focusable="false"><path d="M10 3v26M4.5 9 10 3l5.5 6M4.5 23 10 29l5.5-6" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def band(layers, kind, tx):
    """A link band between two lanes (spec 0.5: group `band` accel or bridge). The chips are the groups' own: nothing is copied."""
    gs = [g for L in layers for g in L["groups"] if g.get("band") == kind and shown(g)]
    if not gs:
        return ""
    note = f'<p class="band-note" data-t="ui.band.{kind}.note">{escape(tx[f"ui.band.{kind}.note"])}</p>' if f"ui.band.{kind}.note" in tx else ""
    return (f'<section class="band" data-band="{kind}">{VARROW}<div class="band-h"><h3 data-t="ui.band.{kind}">{escape(tx[f"ui.band.{kind}"])}</h3>{note}</div>'
            f'<div class="groups">{"".join(group(g, tx) for g in gs)}</div></section>')


def n_chips_of(gs):
    return sum(len(shown(g)) for g in gs)


def card(L, tx):
    i = L["id"]
    own = [g for g in L["groups"] if not g.get("band")]
    body = f'<div class="groups">{"".join(group(g, tx) for g in own)}</div>'
    if L["layout"] == "rows" and L.get("where"):
        body += where(L["where"], tx)
    return (f'<article class="card" id="layer-{i}" data-n="{L["n"]}" style="flex-grow:{n_chips_of(own) + 8 + 3 * len(L.get("where") or [])}">'
            f'<div class="card-h"><span class="badge">{L["n"]}</span><h2 data-t="layer.{i}">{escape(tx[f"layer.{i}"])}</h2><span class="icon">{icon(L["icon"])}</span></div>'
            f'<div class="body">{body}</div>'
            f'<div class="decision" data-t="decision.{i}">{escape(tx[f"decision.{i}"])}</div></article>')


def panel_step(L, tx):
    """The limits panel of a layer, drawn beside its card as a step of the same lane."""
    p = L.get("panel")
    if not p:
        return ""
    return (f'<section class="panel step" style="flex-grow:{n_chips_of(p["groups"]) + 2}"><div class="panel-h"><h3 data-t="panel.{p["id"]}">{escape(tx[f"panel.{p["id"]}"])}</h3>'
            f'<span class="icon">{icon(p["icon"])}</span></div><div class="groups">{"".join(group(g, tx) for g in p["groups"])}</div></section>')


def lane(layers, name, tx):
    mine = sorted((L for L in layers if L["lane"] == name), key=lambda L: L["n"])
    steps = "".join(card(L, tx) + panel_step(L, tx) for L in mine)
    return (f'<section class="lane" data-lane="{name}"><div class="lane-h"><span class="lane-l" aria-hidden="true">{LETTER[name]}</span>'
            f'<h2 data-t="ui.lane.{name}">{escape(tx[f"ui.lane.{name}"])}</h2></div><div class="steps">{steps}</div></section>')


SHARE_ICON = ('<svg class="ic" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><circle cx="12" cy="3.5" r="2" fill="currentColor"/><circle cx="4" cy="8" r="2" fill="currentColor"/>'
              '<circle cx="12" cy="12.5" r="2" fill="currentColor"/><path d="M5.8 7l4.4-2.5M5.8 9l4.4 2.5" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/></svg>')


def share_button(tx):
    return (f'<button type="button" class="btn share" aria-haspopup="dialog" aria-expanded="false" aria-controls="pop-share" data-menu-btn="share">'
            f'{SHARE_ICON}<span data-t="ui.share">{escape(tx["ui.share"])}</span></button>')


def menus(tx, reviewed):
    """ONE popover behind the Share button: share, embed (four types with Copy), download, suggest."""
    t_ = lambda k: escape(tx[k])
    def pill(attr, key):
        return f'<a class="btn sm" {attr} target="_blank" rel="noopener noreferrer"><span data-t="{key}">{t_(key)}</span></a>'
    def row(kind):
        return (f'<div class="emb-row"><div class="emb-txt"><b data-t="ui.embed.t.{kind}">{t_("ui.embed.t." + kind)}</b>'
                f'<p data-t="ui.embed.d.{kind}">{t_("ui.embed.d." + kind)}</p></div>'
                f'<button type="button" class="btn copy" data-copy-snippet="{kind}"><span data-t="ui.embed.copy">{t_("ui.embed.copy")}</span></button></div>')
    return (f'<div class="pop pop-share" id="pop-share" role="dialog" aria-modal="false" aria-label="{t_("ui.share")}" data-al="ui.share" hidden>'
            f'<div class="sh-top"><button type="button" class="btn sm" data-close-pop aria-label="{t_("ui.embed.close")}" data-al="ui.embed.close"><span data-t="ui.embed.close">{t_("ui.embed.close")}</span></button></div>'
            f'<section class="sh-sec"><h3 data-t="ui.share">{t_("ui.share")}</h3><div class="sh-links">'
            f'<button type="button" class="btn sm" data-act="native" hidden><span data-t="ui.share.native">{t_("ui.share.native")}</span></button>'
            f'<button type="button" class="btn sm" data-act="copy"><span data-t="ui.share.copy">{t_("ui.share.copy")}</span></button>'
            + pill('data-share="linkedin" href="#"', "ui.share.linkedin") + pill('data-share="x" href="#"', "ui.share.x") + pill('data-share="email" href="#"', "ui.share.email") + '</div></section>'
            f'<section class="sh-sec"><h3 data-t="ui.embed">{t_("ui.embed")}</h3>'
            f'<p class="emb-help"><span data-t="ui.embed.help">{t_("ui.embed.help")}</span> <a href="https://github.com/{SITE["repo"]}#the-page" target="_blank" rel="noopener noreferrer" data-how><span data-t="ui.embed.how">{t_("ui.embed.how")}</span></a></p>'
            + row("iframe") + row("component") + row("image") + row("badge") + '</section>'
            f'<section class="sh-sec"><h3 data-t="ui.download">{t_("ui.download")}</h3><div class="sh-links">'
            f'<a class="btn sm" data-dl="png" href="#" download>PNG</a><a class="btn sm" data-dl="svg" href="#" download>SVG</a></div></section>'
            f'<div class="sh-foot"><a data-suggest href="#" target="_blank" rel="noopener noreferrer"><span data-t="ui.suggest">{t_("ui.suggest")}</span></a>'
            f'<span class="reviewed"><span data-t="ui.reviewed.short">{t_("ui.reviewed.short")}</span> <time datetime="{reviewed}">{reviewed}</time></span></div>'
            '<div class="sr" role="status" aria-live="polite" id="emb-live"></div></div>')


FONT_PRELOAD = "atkinson-hyperlegible-next/atkinson-hyperlegible-next-latin-wght-normal.woff2"


def font_css(base):
    """@font-face rules for the self-hosted Atkinson fonts; base is the path from the page to docs/fonts (fonts or ../fonts)."""
    return (ROOT / "assets" / "fonts.css").read_text(encoding="utf-8").replace("__FONTS__", base)


def render(embed=False):
    langs = load_langs()
    tx = langs[DEFAULT]
    layers = miniyaml.load(ROOT / "data" / "layers.yml")["layers"]
    all_groups = [g for L in layers for g in L["groups"] + (L.get("panel") or {}).get("groups", [])]
    reviewed = max(s["accessed"] for g in all_groups for c in g["chips"] for s in c["sources"])
    buttons = "".join(f'<button type="button" data-lang="{k}" aria-pressed="{str(k == DEFAULT).lower()}">{escape(v["lang.name"])}</button>' for k, v in langs.items())
    themes = "".join(f'<button type="button" data-theme-choice="{k}" aria-pressed="{str(k == "auto").lower()}" aria-label="{escape(tx["ui.theme." + k])}" data-al="ui.theme.{k}" '
                     f'title="{escape(tx["ui.theme." + k])}" data-tl="ui.theme.{k}">{THEME_ICONS[k]}</button>' for k in ("auto", "light", "dark"))
    board = (f'<div class="board" role="group" aria-label="{escape(tx["site.title"])}">'
             + lane(layers, "build", tx) + band(layers, "accel", tx) + lane(layers, "use", tx) + band(layers, "bridge", tx) + lane(layers, "agents", tx) + '</div>')
    fonts = "../fonts" if embed else "fonts"
    css = font_css(fonts) + (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
    preload = f'<link rel="preload" href="{fonts}/{FONT_PRELOAD}" as="font" type="font/woff2" crossorigin>'
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
                  f'<div class="bar"><div class="seg langs" role="group" aria-label="{escape(tx["ui.language"])}" data-al="ui.language">{buttons}</div>'
                  f'<div class="seg themes" role="group" aria-label="{escape(tx["ui.theme"])}" data-al="ui.theme">{themes}</div>{share_button(tx)}</div>'
                  f'<span class="small-window" role="status" hidden data-t="ui.small">{escape(tx["ui.small"])}</span>'
                  f'<p class="contrib-note" role="status" hidden data-t="ui.contrib">{escape(tx["ui.contrib"])}</p></header>')
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
{preload}
<script>
(function () {{ try {{ var q = new URLSearchParams(location.search), r = document.documentElement;
  var th = q.get("theme") || localStorage.getItem("webai-theme"); if (th === "light" || th === "dark") r.setAttribute("data-theme", th);
  if (q.get("fit") === "0") r.setAttribute("data-size", "large"); }} catch (e) {{}} }})();
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
{'' if embed else menus(tx, reviewed)}
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
