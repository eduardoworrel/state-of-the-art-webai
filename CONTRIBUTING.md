# Contributing

Two kinds of contribution: **content** (chips, sources) and **translation**. Both are text files; you do not need to touch the layout. The rules are in [SPEC.md](SPEC.md); this page is the short version.

## Before you open a pull request

```sh
python3 scripts/check.py     # data and translations against the spec
python3 build.py             # refreshes docs/index.html, README.md and README.pt.md
```

`check.py` names the file, the layer, the group and the chip of every problem. CI runs the same check, rebuilds, and fails if `docs/index.html`, `README.md` or `README.pt.md` change, so commit the rebuilt files.

## Add or change a chip

1. Find the group in `data/layers.yml` and add the chip with **at least two sources**, with distinct urls and, preferably, of different kinds:

   ```yaml
   - id: webgpu                  # lowercase, digits and dashes; unique; never renamed
     sources:
       - url: https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API
         accessed: "2026-11-20"  # the day you read the page, quoted
         level: primary          # primary | trusted | calculation
         title: "MDN: WebGPU API"
         group: docs             # docs | spec | code | papers | blog | status
       - url: https://www.w3.org/TR/webgpu/
         accessed: "2026-11-20"
         level: primary
         title: "W3C: WebGPU"
         group: spec
   ```

   A chip with fewer than two sources is not accepted. If you can only find one trustworthy source, open a pull request that adds the chip to the "Open items" list in `README.md` instead, and say what you found.

2. Add its texts to **every** file in `i18n/`: `chip.<id>` (the name, up to 28 characters) and `desc.<id>` (one line saying what it is, 10 to 140 characters). If you only speak one language, write the English and open the pull request: the check lists what the other languages still need.
3. Run the check and the build. `python3 scripts/linkcheck.py` opens every link and every alert evidence url (it needs network and is not run in CI).

### What counts as a chip

A short noun phrase: a runtime, a library, a format, a technique, a browser feature, a limit or a practice. Not a product pitch, a benchmark number or an opinion.

### What counts as a source

| Level | Use it for |
|---|---|
| `primary` | The specification, the official documentation, the project README, a paper. |
| `trusted` | An engineering post or an issue from the people who maintain the project or the browser. |
| `calculation` | A figure that is derived (for example, parameters times bytes per parameter). Explain the arithmetic in the pull request. |

The source must say what the chip and its description say. Open the page and read it; do not cite a search result or a url you guessed. Every url must answer 200: if it redirects, use the final one. Put the day you read it in `accessed`. A source older than 180 days earns a warning and older than 365 days fails the check: re-read it and update the date, or remove the chip.

### Status

If a chip is not plainly available, say so with `status`, using only what the source says that day:

- `proposal`: written down, no browser or platform ships it.
- `experimental`: behind a flag, an origin trial or a draft that vendors are testing.
- `origin-trial`, `preview`, `stable`: only when the official page uses those words for it.
- `open-question`: the topic matters, but there is no comparable, agreed measurement yet.

Do not write "deprecated", "stable" or "supported by browser X", and do not give a version number, unless the source says it in those words. When a page gives different states for different contexts, leave `status` out and say so in the description.

### Too many chips in a group

The figure is a cut. If a group would crowd its card, keep the most relevant chips drawn and add `featured: false` to the rest: they still need two sources and their texts, and they show up in the README under "Also exists".

### Alerts

A chip can carry an `alert`: a problem **you observed**, on a day, with evidence anyone can open. It is not the same as `status` (the project's life cycle).

```yaml
- id: onnxruntime
  alert:
    level: critical          # critical | warning | info (it follows from kind)
    kind: broken-link        # broken-link, removed -> critical; deprecated, superseded -> warning; moved -> info
    observed: "2026-11-20"
    evidence:                # 1 to 8 urls
      - https://github.com/microsoft/onnxruntime
      - https://www.npmjs.com/package/onnxruntime-web
  sources: [...]             # still two sources that work
```

Then write `alert.<chip id>` in every language, saying **only what you saw, with the date**: "the repository answers 404 on 2026-11-20". Do not write that a project is abandoned, dead or unmaintained, and do not guess a cause, unless a source says it (then quote and link it). A broken link does not count as one of the two sources: add a working one and keep the broken one as evidence. After 30 days the check warns: look again, then update `observed` and the text, or remove the alert. `python3 scripts/linkcheck.py` opens the evidence for you.

### Models managed by the platform

Some entries are not about running a model you ship: you call an API, and the browser or the system downloads, updates and removes the model (the built-in browser APIs such as the Prompt API, AICore on Android, Foundation Models on Apple platforms). These live in **Integrate in the app** (groups *Browser API* and *Native SDK*), not in **Run**, where you bring the model. Write "the browser (or the system) manages the model". Do not write "shared between sites" unless an official page says so.

### Groups, layers and icons

Groups use `col` (0 or 1 in a card, 0 to 2 in the limits panel) or `row` (in the Run layer). Their text keys are `group.<id>`. A new icon is an SVG in `assets/icons/`; use `data-f` and `data-s` attributes (`ink`, `acc`, `bg`, `paper`, `edge`, `track`, `muted`) instead of colors so it follows the light and dark themes. Changes to the data model itself (new fields, new enumerations) are spec changes: see SPEC.md section 8.

## Translate

1. Copy `i18n/en.yml` to `i18n/<code>.yml` (for example `es.yml`).
2. Translate the values, not the keys. Keep technology names (ONNX, WebGPU, LoRA, ...) and the `{n}` and `{name}` placeholders.
3. Set `lang.name` to the name of the language in that language (it labels the button).
4. For plurals, add the categories your language needs (`ui.sources.few`, `ui.sources.many`, ...); `other` is required.
5. Run `python3 scripts/check.py`. It lists every key still missing and every text that is too long.

Keep texts short: chips and group labels have little room. Test with `?lang=<code>` and look for chips that wrap.

## Where the site lives

The public address is the one constant `base_url` in `site.toml` (keep the trailing slash). Change it there and run `python3 build.py`: the share links, the embed snippets, the canonical link and `docs/sitemap.xml` follow. `repo` is the GitHub repository that the "Suggest or correct" links open. Run `python3 export.py` too when the data changes, so the PNG and SVG figures match. The embed web component takes its address from its own script URL, so it needs no setting.

## Layout

The map follows the window continuously (`assets/app.js`, function `arrange()`): on every resize it measures the arrangements of the five cards and picks the largest scale that fits the free rectangle (a quick re-fit of the current arrangement on each frame while dragging, a full search when the window stops). Change the layout rules there, and the spacing in `assets/style.css`; text uses `--u` and everything that is not text (padding, gaps, icons, margins) uses `--s`, which grows more slowly than `--u` (`setUnit()` in `assets/app.js`), so the room goes to the text. After a layout change run `python3 scripts/test_resize.py` (needs Chrome).

## Motion

The page has small motions (the model line, the dot on it, the "Where it runs" items and their icons). They are decoration only: never put information in a motion, and a new icon must look right and say the same when still. Motion is driven by the `motion` class that `assets/app.js` sets on `<html>`, only when the system does not ask for reduced motion, `?motion=0` is absent and the page is not exported. To add a motion to an icon, tag the part with a class (for example `m-led1`) and write the keyframes under `html.motion` in `assets/style.css`; nothing else.

## Style

- Plain words. No marketing, no superlatives.
- One idea per chip.
- English is the reference language: write new text there first.
