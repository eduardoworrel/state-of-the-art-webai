"""Renders the awesome-style list from data/layers.yml and writes it between the markers
<!-- awesome:start --> and <!-- awesome:end --> in README.md (en) and README.pt.md (pt).

    python3 scripts/awesome.py          # update both files
    python3 scripts/awesome.py --check  # exit 1 if a file is out of date
"""
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import miniyaml  # noqa: E402

START, END = "<!-- awesome:start -->", "<!-- awesome:end -->"
TARGETS = {"en": "README.md", "pt": "README.pt.md"}
SRC_ORDER = ["docs", "spec", "code", "papers", "blog", "status"]


def sources(chip):
    return chip["sources"]


def link(s, tx):
    title = s.get("title") or urlparse(s["url"]).netloc.removeprefix("www.")
    return f"[{title}]({s['url']})"


def chip_lines(c, tx):
    name = tx[f"chip.{c['id']}"]
    state = f" · *{tx['ui.status.' + c['status']]}*" if c.get("status") else ""
    out = [f"- **{name}**{state} — {tx['desc.' + c['id']]}"]
    if c.get("alert"):
        al = c["alert"]
        icon = {"critical": "🔴", "warning": "🟠", "info": "⚪"}[al["level"]]
        lab = lambda u: (lambda x: x if len(x) <= 46 else x[:24] + "…" + x[-20:])(u.split("://", 1)[1].removeprefix("www."))
        out.append(f"  - {icon} **{tx['ui.alert']} · {tx['ui.alert.level.' + al['level']]} · {tx['ui.alert.kind.' + al['kind']]}** ({tx['ui.alert.observed']} {al['observed']}): {tx['alert.' + c['id']]}")
        out.append(f"  - {tx['ui.alert.evidence']}: " + ", ".join(f"[{lab(u)}]({u})" for u in al["evidence"]))
    ungrouped = [s for s in c["sources"] if not s.get("group")]
    if ungrouped:
        out.append("  - " + ", ".join(link(s, tx) for s in ungrouped))
    for g in SRC_ORDER:
        items = [s for s in c["sources"] if s.get("group") == g]
        if items:
            out.append(f"  - {tx['srcgroup.' + g]}: " + ", ".join(link(s, tx) for s in items))
    return out


ALSO = {"en": "Also exists (not drawn on the figure)", "pt": "Também existe (fora da figura)"}


def group_lines(g, tx, lang="en"):
    main = [c for c in g["chips"] if c.get("featured", True)]
    extra = [c for c in g["chips"] if not c.get("featured", True)]
    out = [f"**{tx['group.' + g['id']]}**", ""]
    for c in main:
        out += chip_lines(c, tx)
    if extra:
        out += ["", f"_{tx['ui.also']}:_", ""]
        for c in extra:
            out += chip_lines(c, tx)
    out.append("")
    return out


def render(lang, layers, tx):
    allsrc = [s for L in layers for g in L["groups"] + (L.get("panel") or {}).get("groups", []) for c in g["chips"] for s in sources(c)]
    reviewed = max(s["accessed"] for s in allsrc)
    nchips = sum(len(g["chips"]) for L in layers for g in L["groups"] + (L.get("panel") or {}).get("groups", []))
    head = {"en": f"_{nchips} chips, {len(allsrc)} source links. Last reviewed: {reviewed}. Generated from `data/layers.yml`: do not edit by hand._",
            "pt": f"_{nchips} chips, {len(allsrc)} links de fonte. Última revisão: {reviewed}. Gerado a partir de `data/layers.yml`: não edite à mão._"}[lang]
    out = [head, ""]
    for L in layers:
        out += [f"### {L['n']}. {tx['layer.' + L['id']]}", f"_{tx['decision.' + L['id']]}_", ""]
        for g in L["groups"]:
            out += group_lines(g, tx)
        if L.get("where"):
            out += [f"**{tx['ui.where']}**", ""]
            for w in L["where"]:
                out.append(f"- [{tx['where.' + w['id'] + '.name']}]({w['source']['url']}) — {tx['where.' + w['id'] + '.desc']}")
            out.append("")
        if L.get("panel"):
            p = L["panel"]
            out += [f"#### {tx['panel.' + p['id']]}", ""]
            for g in p["groups"]:
                out += group_lines(g, tx)
    return "\n".join(out).rstrip() + "\n"


def splice(text, block):
    if START not in text or END not in text:
        raise SystemExit(f"markers {START} / {END} not found")
    pre, rest = text.split(START, 1)
    _, post = rest.split(END, 1)
    return f"{pre}{START}\n{block}{END}{post}"


def update(check=False):
    layers = miniyaml.load(ROOT / "data" / "layers.yml")["layers"]
    stale = []
    for lang, name in TARGETS.items():
        path = ROOT / name
        if not path.exists():
            continue
        tx = miniyaml.load(ROOT / "i18n" / f"{lang}.yml")
        new = splice(path.read_text(encoding="utf-8"), render(lang, layers, tx))
        if new != path.read_text(encoding="utf-8"):
            if check:
                stale.append(name)
            else:
                path.write_text(new, encoding="utf-8")
                print("updated", name)
    return stale


if __name__ == "__main__":
    s = update(check="--check" in sys.argv)
    if s:
        print("out of date:", ", ".join(s), "(run python3 build.py)")
        sys.exit(1)
