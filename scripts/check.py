#!/usr/bin/env python3
"""Validates data/layers.yml and i18n/*.yml against SPEC.md (schema/*.json plus the rules a schema cannot express).

    python3 scripts/check.py [--verbose]

Exit code 1 if anything is wrong. Every message starts with the file and says which layer, group and chip it is about.
Source freshness: a source read more than 180 days ago is a warning, more than 365 days ago is an error
(set CHECK_TODAY=YYYY-MM-DD to test).
"""
import datetime
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import miniyaml  # noqa: E402
import minischema  # noqa: E402

LAYERS_FILE = "data/layers.yml"
STATIC_KEYS = (["lang.name", "site.title", "site.tagline", "label.model", "label.person", "ui.source", "ui.accessed", "ui.language", "ui.where", "ui.legend",
                "ui.contribute", "ui.reviewed", "ui.reviewed.short", "ui.license", "ui.theme", "ui.theme.auto", "ui.theme.light", "ui.theme.dark",
                "ui.sources.one", "ui.sources.other", "ui.menu", "ui.opens", "ui.alert", "ui.alert.observed", "ui.alert.evidence", "ui.also"]
               + [f"ui.alert.level.{x}" for x in ("critical", "warning", "info")]
               + [f"ui.alert.kind.{x}" for x in ("broken-link", "removed", "deprecated", "superseded", "moved")]
               + [f"ui.level.{x}" for x in ("primary", "trusted", "calculation")]
               + [f"ui.status.{x}" for x in ("proposal", "experimental", "open-question", "stable", "origin-trial", "preview")]
               + [f"srcgroup.{x}" for x in ("docs", "spec", "code", "papers", "blog", "status")])
PLURALS = {"zero", "one", "two", "few", "many", "other"}
WARN_DAYS, ERROR_DAYS = 180, 365
ALERT_WARN_DAYS = 30
ALERT_LEVEL = {"broken-link": "critical", "removed": "critical", "deprecated": "warning", "superseded": "warning", "moved": "info"}
CONCLUSIONS = re.compile(r"abandon|unmaintained|\bdead\b|\bmorto\b|sem manuten", re.I)  # alerts describe what was seen, they do not conclude

errors, warnings = [], []


def err(file, where, msg):
    errors.append(f"{file}: {where}: {msg}")


def warn(file, where, msg):
    warnings.append(f"{file}: {where}: {msg}")


def describe(data, path):
    """Turns $.layers[2].groups[0].chips[3].source.url into: layer 'run' > group 'cache' > chip 'opfs' > source.url"""
    kinds = {"layers": "layer", "groups": "group", "chips": "chip", "where": "where", "sources": "source"}
    node, label, field, last = data, [], [], ""
    for key, idx in re.findall(r"\.([A-Za-z_]+)|\[(\d+)\]", path):
        try:
            node = node[key] if key else node[int(idx)]
        except (KeyError, IndexError, TypeError):
            field.append(key or f"[{idx}]")
            continue
        if key:
            last = key
            field.append(key)
        else:
            field.append(f"[{idx}]")
        if isinstance(node, dict) and "id" in node and not key:
            label.append(f"{kinds.get(last, 'item')} '{node['id']}'")
            field = []
    tail = "".join(f".{f}" if not f.startswith("[") else f for f in field).lstrip(".")
    return " > ".join(label + ([tail] if tail else [])) or "(top level)"


def pre_checks(data):
    """Friendly messages for the most common mistakes, before the schema speaks."""
    if isinstance(data, dict) and data.get("spec") not in (None, "0.4"):
        err(LAYERS_FILE, "spec", f"declares spec {data.get('spec')!r}; this checker implements 0.4 (see SPEC.md, section 8)")
    for L in data.get("layers") or []:
        for g in (L.get("groups") or []) + ((L.get("panel") or {}).get("groups") or []):
            for c in g.get("chips") or []:
                where = f"layer '{L.get('id')}' > group '{g.get('id')}' > chip '{c.get('id')}'"
                srcs = c.get("sources")
                if "source" in c:
                    err(LAYERS_FILE, where, "uses `source`, which chips no longer have in spec 0.4: list the links under `sources` (at least two)")
                if srcs is None and "source" not in c:
                    err(LAYERS_FILE, where, "has no sources: every chip needs `sources` with at least two links (SPEC.md section 4)")
                if isinstance(srcs, list):
                    n = len(srcs)
                    if n < 2:
                        err(LAYERS_FILE, where, f"has {n} link(s); every chip needs at least 2 sources with distinct urls (SPEC.md section 4). Add a second source or move the chip to the waiting list in README.md")
                    urls = [s.get("url") for s in srcs if isinstance(s, dict)]
                    dups = sorted({u for u in urls if urls.count(u) > 1})
                    if dups:
                        err(LAYERS_FILE, where, f"lists the same url more than once ({n} links, {len(set(urls))} distinct): {', '.join(dups)}")
                    groups = {s.get("group") for s in srcs if isinstance(s, dict)}
                    if n >= 2 and len(groups) < 2:
                        warn(LAYERS_FILE, where, f"all {n} sources are in the same group ({next(iter(groups)) or 'no group'}); prefer sources of different kinds (docs + code, docs + spec, ...)")


def semantic(data, today):
    expected = set(STATIC_KEYS)
    seen = {"layer": set(), "group": set(), "chip": set(), "where": set()}
    alerts = []
    numbers = set()
    icons = {p.stem for p in (ROOT / "assets" / "icons").glob("*.svg")}

    def dup(kind, i, where):
        if i in seen[kind]:
            err(LAYERS_FILE, where, f"duplicate {kind} id '{i}' (ids are unique across the whole file)")
        seen[kind].add(i)

    def fresh(src, where):
        d = src.get("accessed")
        try:
            age = (today - datetime.date.fromisoformat(d)).days
        except (TypeError, ValueError):
            return  # the schema reports the format
        if age < 0:
            err(LAYERS_FILE, where, f"accessed {d} is in the future")
        elif age > ERROR_DAYS:
            err(LAYERS_FILE, where, f"source read {age} days ago ({d}): read it again and update `accessed`, or remove the chip")
        elif age > WARN_DAYS:
            warn(LAYERS_FILE, where, f"source read {age} days ago ({d}): due for a re-read")

    def groups(gs, where, mode):
        for g in gs:
            gw = f"{where} > group '{g.get('id')}'"
            dup("group", g.get("id"), gw)
            expected.add(f"group.{g.get('id')}")
            if mode == "rows" and "row" not in g:
                err(LAYERS_FILE, gw, "layout 'rows' needs `row` (1 to 3)")
            if mode == "cols" and "col" not in g:
                err(LAYERS_FILE, gw, "needs `col` (0 to 2)")
            for c in g.get("chips") or []:
                cw = f"{gw} > chip '{c.get('id')}'"
                dup("chip", c.get("id"), cw)
                expected.update({f"chip.{c.get('id')}", f"desc.{c.get('id')}"})
                if isinstance(c.get("alert"), dict):
                    expected.add(f"alert.{c.get('id')}")
                    alerts.append((cw, c))
                for s in (c.get("sources") or []):
                    if isinstance(s, dict):
                        fresh(s, cw)

    for L in data.get("layers") or []:
        w = f"layer '{L.get('id')}'"
        dup("layer", L.get("id"), w)
        expected.update({f"layer.{L.get('id')}", f"decision.{L.get('id')}"})
        if L.get("n") in numbers:
            err(LAYERS_FILE, w, f"layer number n={L.get('n')} is used twice")
        numbers.add(L.get("n"))
        if L.get("icon") not in icons:
            err(LAYERS_FILE, w, f"icon '{L.get('icon')}' not found in assets/icons/")
        groups(L.get("groups") or [], w, L.get("layout"))
        for it in L.get("where") or []:
            ww = f"{w} > where '{it.get('id')}'"
            dup("where", it.get("id"), ww)
            expected.update({f"where.{it.get('id')}.name", f"where.{it.get('id')}.desc"})
            if it.get("icon") not in icons:
                err(LAYERS_FILE, ww, f"icon '{it.get('icon')}' not found in assets/icons/")
            if isinstance(it.get("source"), dict):
                fresh(it["source"], ww)
        if L.get("panel"):
            p = L["panel"]
            expected.add(f"panel.{p.get('id')}")
            if p.get("icon") not in icons:
                err(LAYERS_FILE, f"{w} > panel", f"icon '{p.get('icon')}' not found in assets/icons/")
            groups(p.get("groups") or [], f"{w} > panel", "cols")
    for cw, c in alerts:
        a = c["alert"]
        want = ALERT_LEVEL.get(a.get("kind"))
        if want and a.get("level") != want:
            err(LAYERS_FILE, f"{cw} > alert", f"kind '{a.get('kind')}' is level '{want}', not '{a.get('level')}' (SPEC.md section 4.5)")
        try:
            age = (today - datetime.date.fromisoformat(a.get("observed"))).days
            if age < 0:
                err(LAYERS_FILE, f"{cw} > alert", f"observed {a['observed']} is in the future")
            elif age > ALERT_WARN_DAYS:
                warn(LAYERS_FILE, f"{cw} > alert", f"observed {age} days ago ({a['observed']}): check again and update `observed`, or remove the alert")
        except (TypeError, ValueError):
            pass
        ev = a.get("evidence") or []
        if len(ev) != len(set(ev)):
            err(LAYERS_FILE, f"{cw} > alert", "lists the same evidence url twice")
    return expected, seen, alerts


def main():
    today = datetime.date.fromisoformat(os.environ["CHECK_TODAY"]) if os.environ.get("CHECK_TODAY") else datetime.date.today()
    layers_schema = json.loads((ROOT / "schema" / "layers.schema.json").read_text())
    i18n_schema = json.loads((ROOT / "schema" / "i18n.schema.json").read_text())
    data = miniyaml.load(ROOT / LAYERS_FILE)

    pre_checks(data)
    for path, msg in minischema.validate(data, layers_schema, layers_schema):
        err(LAYERS_FILE, describe(data, path), msg)
    expected, seen, alerts = semantic(data, today)

    files = sorted((ROOT / "i18n").glob("*.yml"))
    if not any(f.stem == "en" for f in files):
        err("i18n", "(folder)", "en.yml (the reference language) is missing")
    names = {}
    for f in files:
        rel, tx = f"i18n/{f.name}", miniyaml.load(f)
        for path, msg in minischema.validate(tx, i18n_schema, i18n_schema):
            err(rel, path.removeprefix("$."), msg)
        for k in sorted(expected - set(tx)):
            err(rel, k, "missing text (copy the English line from i18n/en.yml and translate it)")
        extra = {k for k in tx if re.match(r"^ui\.sources\.(\w+)$", k) and k.rsplit(".", 1)[1] in PLURALS}
        for k in sorted(set(tx) - expected - extra):
            err(rel, k, "unused key (nothing in data/layers.yml refers to it; remove it)")
        for _, c in alerts:
            text = tx.get(f"alert.{c['id']}", "")
            if CONCLUSIONS.search(re.sub(r'“[^”]*”|"[^"]*"', "", text)):  # words inside quotation marks are the source's, not ours
                err(rel, f"alert.{c['id']}", "concludes instead of describing what was observed (words like abandoned/dead): say what you saw, with the date, or quote the source between quotation marks")
            if c["alert"].get("observed") and "alert." + c["id"] in tx and not re.search(r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}", text):
                err(rel, f"alert.{c['id']}", "must state the date of the observation (for example 2026-11-20)")
        if f.stem == "en" and "ui.sources.one" not in tx:
            err(rel, "ui.sources.one", "the reference language needs both ui.sources.one and ui.sources.other")
        for k in ("ui.sources.one", "ui.sources.other"):
            if k in tx and "{n}" not in tx[k]:
                err(rel, k, "must contain the {n} placeholder")
        if "ui.menu" in tx and "{name}" not in tx["ui.menu"]:
            err(rel, "ui.menu", "must contain the {name} placeholder")
        if tx.get("lang.name") in names:
            err(rel, "lang.name", f"same as {names[tx['lang.name']]}")
        names[tx.get("lang.name")] = rel

    n_chips = len(seen["chip"])
    same = [w for w in warnings if "same group" in w]
    other = [w for w in warnings if "same group" not in w]
    for w in other + (same if "--verbose" in sys.argv else []):
        print("warning:", w)
    if same and "--verbose" not in sys.argv:
        print(f"note: {len(same)} chips have all their sources in one group (docs + code, docs + spec, ... is better); --verbose lists them")
    if errors:
        print(f"{len(errors)} problem(s):")
        print("\n".join(" - " + e for e in errors))
        sys.exit(1)
    print(f"ok: {len(seen['layer'])} layers, {len(seen['group'])} groups, {n_chips} chips, {len(files)} languages, spec 0.4")


if __name__ == "__main__":
    main()
