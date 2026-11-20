# State of the Art of WebAI: specification

**Version 0.4** (draft). The words MUST, SHOULD and MAY are used as in RFC 2119.

This document defines the data a contribution is made of, what makes an entry valid, how texts are translated, how entries are kept fresh, and how the page, the PNG and the awesome list are generated from the same data. `schema/*.json` and `scripts/check.py` implement it; if they disagree with this text, that is a bug in one of them.

## 1. Files

| File | Role |
|---|---|
| `data/layers.yml` | The only place where layers, groups, chips and their sources are written. |
| `i18n/<lang>.yml` | The texts, one file per language. `en` is the reference language. |
| `schema/layers.schema.json`, `schema/i18n.schema.json` | JSON Schemas (draft 2020-12) for the two kinds of file. |
| `assets/icons/*.svg` | Icons referenced by name from the data. |
| `docs/index.html`, `docs/figure-<lang>.png` | Generated. Never edited by hand. |
| `README.md`, `README.pt.md` | Hand-written text plus a generated list (section 9). |

## 2. Data model

```
layer ── group ── chip ── sources (two or more links, optionally grouped by label)
                       └── alert (optional: a dated, evidenced problem)
  ├── where   (only in a layer with layout "rows"; each item has one source)
  └── panel ── group ── chip ...
```

- A **layer** is a stage of the work between a model and a person. Layers are numbered and shown in a column.
- A **group** is a labelled set of chips inside a layer (for example "Format" or "Method").
- A **chip** is one technology, technique, feature, limit or practice. It is the unit of curation: it has a name, a one-line description, an optional status and at least two sources.
- A **source** is a page someone read, with the day they read it and how much it can be trusted.
- A **where item** names a place a model can run (browser, desktop, mobile, edge). A **panel** is a highlighted set of groups, used for the limits.

## 3. Fields

Unknown fields are errors. "R" means required.

### 3.1 Top level (`data/layers.yml`)

| Field | R | Type | Rule |
|---|---|---|---|
| `spec` | yes | string | Exactly `"0.4"` for this version. |
| `layers` | yes | list | At least one layer. |

### 3.2 Layer

| Field | R | Type | Rule |
|---|---|---|---|
| `id` | yes | id | Unique among layers. |
| `n` | yes | integer 1 to 20 | The number shown on the badge. Unique. |
| `icon` | yes | id | A file `assets/icons/<icon>.svg`. |
| `column` | yes | `left`, `center` or `right` | Where the layer is drawn. |
| `layout` | yes | `cols` or `rows` | `cols`: groups carry `col` (0 or 1). `rows`: groups carry `row` (1 to 3); the layer may have `where` and `panel`. |
| `groups` | yes | list | At least one group. |
| `where` | no | list | Only with `rows`. |
| `panel` | no | object | Only with `rows`. |

### 3.3 Group

| Field | R | Type | Rule |
|---|---|---|---|
| `id` | yes | id | Unique among groups, across all layers and panels. |
| `col` | with `cols` and in panels | integer 0 to 2 | The column inside the card or panel. |
| `row` | with `rows` | integer 1 to 3 | The row inside the layer. |
| `chips` | yes | list | 1 to 12 chips. |

### 3.4 Chip

| Field | R | Type | Rule |
|---|---|---|---|
| `id` | yes | id | Unique among chips. Stable: once published it is never renamed (translations and links depend on it). |
| `status` | no | status | The project's life cycle. See 4.4. |
| `alert` | no | alert | A problem someone observed, with date and evidence. See 4.5. Separate from `status`. |
| `featured` | no | boolean | Default `true`. `false`: the chip is not drawn on the figure or the page and appears in the README list under "Also exists". It still needs two sources and its texts. |
| `sources` | yes | list of sources | Two to twelve sources, with distinct urls (section 4). |

There is no `source` key on a chip: a chip with fewer than two sources is invalid.

### 3.5 Where item and panel

A where item is an index entry, not a chip: it has `id`, `icon` and `source` (exactly one link, 4.2), and its name is a plain link on the page. A panel has `id`, `icon` and `groups` (groups with `col` 0 to 2).

### 3.6 Types and limits

| Type | Rule |
|---|---|
| `id` | Lowercase letters, digits and single dashes (kebab-case), 2 to 40 characters, starting with a letter or digit: `^[a-z0-9]+(-[a-z0-9]+)*$`. Ids are never reused for another meaning. |
| date | ISO 8601 calendar date `YYYY-MM-DD`, quoted in YAML. |
| url | `https://`, no spaces, at most 300 characters. A link to a page, not to a search result. |
| text limits | See section 6.5. |

## 4. Sources

### 4.1 The rule: at least two, distinct

Every chip MUST have at least two sources, with **distinct urls**. Sources SHOULD be of different kinds (the `group` of 4.3): documentation and code, documentation and specification, documentation and status page, a paper and its code. A chip that cannot get a second trustworthy source does not enter the map: it waits in the "Open items" list of `README.md` until one exists. Do not pad a chip with a weak link to reach two.

| Sources | Result |
|---|---|
| none, one, or the same url twice | invalid: the check fails and says how many links the chip has |
| two or more distinct urls | valid; the chip opens a menu with the links on the page |

A source tree can carry labels (`group`) or not. Labels are an optional capability of the list, not a different form.

### 4.2 A source

```yaml
- id: webgpu
  sources:
    - url: https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API
      accessed: "2026-11-20"
      level: primary
      title: "MDN: WebGPU API"
      group: docs
    - url: https://www.w3.org/TR/webgpu/
      accessed: "2026-11-20"
      level: primary
      title: "W3C: WebGPU"
      group: spec
    - url: https://web.dev/blog/webgpu-supported-major-browsers
      accessed: "2026-11-20"
      level: primary
      title: "web.dev: browser support"
      group: status
```

| Field | R | Rule |
|---|---|---|
| `url` | yes | See 3.6. It MUST answer HTTP 200 when you open it (after redirects). If the page moved, use the final url. |
| `accessed` | yes | The day the page was read, not the day it was published. |
| `level` | yes | `primary`, `trusted` or `calculation` (4.4). |
| `title` | yes | A short label, 2 to 60 characters, written in English. It names the page; it is not translated. |
| `group` | no, recommended | One of the source groups (4.3). Links without `group` are listed first. |

A where item's `source` has the same fields, except that `title` is optional and `group` is not allowed.

You MUST have opened and read the page. The page must say what the chip and its description say; a search result, a URL guessed from a pattern, or memory is not a source. `scripts/linkcheck.py` (network, not run in CI) opens every url and reports what does not answer 200 or that redirects.

### 4.3 Source groups

`docs` (official documentation), `spec` (specification, explainer or standard), `code` (repository, README, issue or package page), `papers` (papers), `blog` (engineering or announcement post), `status` (where a thing stands: standards positions, support tables, trials). The label shown is the translation of `srcgroup.<group>`.

### 4.4 Level and status

#### Status

An optional `status` tells the reader that a chip is not plainly "available". Use it only for what the source says.

| Value | Meaning |
|---|---|
| `proposal` | Written down as a proposal; no browser or platform ships it. |
| `experimental` | Behind a flag, an origin trial or a draft that vendors are testing. |
| `origin-trial` | Available to sites through an origin trial. |
| `preview` | In an early or developer preview. |
| `stable` | The official page calls it stable or generally available. |
| `open-question` | The topic matters, but no comparable, agreed measurement or answer exists yet. |

Rules: the value MUST be what the source says on `accessed`. Never infer a version number, a platform list or "stable"/"deprecated" from other pages. When the official page gives different states for different contexts, leave `status` out and say so in the chip's description.

#### Level

| Value | Use it for |
|---|---|
| `primary` | Specification, official documentation, the project's README, a paper. |
| `trusted` | An engineering post or issue from the people who maintain the project or the browser. |
| `calculation` | A figure derived from sources (for example, parameters times bytes per parameter). The pull request explains the arithmetic. |

### 4.5 Alerts

`status` (4.4) says where a project stands in its life. An **alert** says that someone **observed a problem** on a day: a link that answers 404, a page that says a thing is deprecated, an address that moved. The two are independent: a chip can have a status, an alert, both or neither.

```yaml
- id: mediapipe
  alert:
    level: warning            # critical | warning | info
    kind: deprecated          # broken-link | removed | deprecated | superseded | moved
    observed: "2026-11-20"    # the day you saw it
    evidence:                 # pages anyone can open to see it again (1 to 8)
      - https://web.archive.org/web/20260517083853/https://ai.google.dev/edge/mediapipe/solutions/genai/llm_inference
      - https://developers.google.com/edge/litert-lm
  sources: [...]
```

| Field | R | Rule |
|---|---|---|
| `level` | yes | `critical`, `warning` or `info`. It follows from `kind` (below); `check.py` rejects a mismatch. |
| `kind` | yes | `broken-link` (a link a chip relies on answers an error), `removed` (the project or page is gone, said by the source), `deprecated` (a source says so), `superseded` (a source names its replacement), `moved` (the address changed, content found elsewhere). |
| `observed` | yes | ISO date of the observation. |
| `evidence` | yes | 1 to 8 https urls. A broken link is itself the evidence and may be listed even though it does not answer. |
| text | yes | The i18n key `alert.<chip id>` (20 to 600 characters) says what was observed. |

| kind | level | colour |
|---|---|---|
| `broken-link`, `removed` | `critical` | red |
| `deprecated`, `superseded` | `warning` | amber |
| `moved` | `info` | grey |

Rules:

1. **Evidence or nothing.** An alert without verifiable evidence (a url and the observation date) is invalid.
2. **Describe, do not conclude.** The text says what was seen, with the date ("the repository answers 404 on 2026-11-20"). It never says a project is abandoned, dead or unmaintained, and never names a cause, unless a source says so, in which case it quotes that source and links it. `check.py` rejects the words *abandon*, *dead*, *unmaintained* (and the Portuguese equivalents) and requires a date in the text.
3. **Alerts expire for review.** After 30 days `check.py` warns: look again, then update `observed` and the text, or remove the alert. `scripts/linkcheck.py` also opens the evidence and flags a `broken-link` or `removed` alert whose repository evidence answers 200 again.
4. **Keep the two-sources rule.** A broken link does not count as one of the two sources; the chip needs two sources that work, and the broken link goes in `evidence`.
5. **Texts in every language.** `alert.<chip id>` exists in each `i18n/<lang>.yml`; the labels come from `ui.alert.level.*` and `ui.alert.kind.*`.

On the page an alert shows as a marker in the level's colour inside the chip (a different shape per level, so colour is not the only signal: octagon for critical, triangle for warning, circle for info) with text for screen readers ("Alert: Critical, Link broken"). The preview and the menu take the level's background and border and show, on top, the alert title, the detail, the day it was observed and (in the menu) the evidence links. In the awesome list the alert is a line under the chip.

### 4.6 Figure and list

The figure is a cut, the README list is the full set. When a group would crowd its card, keep the most relevant chips drawn and mark the rest `featured: false`: they stay in `data/layers.yml`, in `i18n/` and in the awesome list (under "Also exists"), with the same rules (two sources, texts, alerts). Choose by relevance to running models in a browser, on a phone or on an edge board.

## 5. Entry types and where they live

Every chip is a thing a person who ships a model has to choose, know or watch. Two kinds of entry need care.

- **You bring the model.** A runtime, a format, a quantization method, a limit. These live in **Choose and adapt**, **Convert and quantize** and **Run**.
- **The platform brings the model.** A *platform-managed model* is a model you do not ship: you call an API and the platform downloads, updates and removes the model. Examples: the Prompt API and the other built-in browser APIs (the browser manages a Gemini Nano model), AICore on Android, Apple's Foundation Models. These entries live in **Integrate in the app**, in the groups *Browser API* and *Native SDK*, never in **Run**.

Wording for platform-managed entries: write "the browser (or the system) manages the model". Do not write that a model is "shared between sites", and do not give a browser version or a stability label unless the official page says it on the day you read it.

## 6. Internationalization

### 6.1 Reference language and files

`i18n/en.yml` is the reference language: new text is written there first. Each other language is `i18n/<code>.yml`, where `<code>` is a lowercase language code (`pt`, `es`, `zh`). One file is a flat map from key to text.

### 6.2 Keys

One key per id, derived from the data; there are no free-form keys besides the fixed UI ones.

| Key | Text | Max chars |
|---|---|---|
| `layer.<id>` | Layer title | 30 |
| `decision.<layer id>` | The question at the bottom of the layer | 40 |
| `group.<id>` | Group label (shown in capitals) | 24 |
| `panel.<id>` | Panel title | 24 |
| `chip.<id>` | Chip name | 28 |
| `desc.<chip id>` | One line saying what the chip is (used by the awesome list), 10 to 140 | 140 |
| `where.<id>.name`, `where.<id>.desc` | Place and what runs there | 20, 60 |
| `srcgroup.<group>` | Label of a source group | 20 |
| `alert.<chip id>` | What was observed, with the date (4.5) | 600 |
| `ui.*`, `label.*`, `site.*`, `lang.name` | Interface texts, listed in `scripts/check.py` | 220 |

Every key that the data needs MUST exist in every language; a key nothing refers to MUST be removed.

### 6.3 Fallback

The page uses the language in `?lang=`, then the stored choice, then the browser's language, then `en`. A missing key falls back to the English text, then to the key itself. `scripts/check.py` fails on a missing key, so a fallback is only seen by someone running an old build.

### 6.4 Adding a language

1. Copy `i18n/en.yml` to `i18n/<code>.yml`.
2. Translate the values. Keep the keys, the `{n}` and `{name}` placeholders, and technology names (ONNX, WebGPU, LoRA, ...).
3. Set `lang.name` to the language's own name (it is the button label).
4. Run `python3 scripts/check.py`, `python3 build.py`, and look for chips that wrap in `?lang=<code>`.

### 6.5 Plurals and lengths

- Counts use `ui.sources.<category>` with the CLDR categories `zero`, `one`, `two`, `few`, `many`, `other` and the placeholder `{n}`. `other` is required in every language and `one` in `en`; the page picks the category with `Intl.PluralRules(<lang>)` and falls back to `other`.
- Limits count characters in the language written. Chips and group labels have little room: when a translation does not fit, shorten the text (a shorter synonym or an abbreviation), do not change the limit.
- Right-to-left languages are not supported in 0.4.
- Source `title` values and technology names are not translated.

## 7. Curation

### 7.1 Entry criteria

A chip enters when all of these hold:

1. **Two sources say it.** At least two distinct pages, opened and read by the contributor, state what the chip and its description state (section 4). A search result, a social post, a guessed url or memory is not a source.
2. **It belongs on the map.** It is a technology, technique, feature, limit or practice that a person shipping a model to a browser, phone or edge device meets. Not a product pitch, a benchmark number or an opinion.
3. **Its state is told.** If it is a proposal, experimental, in trial, in preview or an open question, `status` says so (4.4).
4. **It fits.** The name is at most 28 characters in every language and the description is one line.

Prefer primary sources. A `trusted` source is fine for what the project's own maintainers say. A claim that only a secondary source supports is `trusted` and the pull request says why.

### 7.2 Project state and wording

Say what the source says and no more. Do not call a project "dead", "deprecated", "stable", "production-ready" or "supported" unless the source uses those words for that thing. Prefer what the page shows ("the documentation points to X") to a conclusion drawn from it.

### 7.3 Review date and ageing

`accessed` is the day the page was read. A source ages:

| Age of `accessed` | Check result |
|---|---|
| up to 180 days | ok |
| 181 to 365 days | warning: due for a re-read |
| more than 365 days | error: re-read and update `accessed`, or remove the chip |
| in the future | error |

Re-reading means opening the page again, confirming that the chip and its description still hold (or fixing them), and updating `accessed`. The date shown at the foot of the page is the most recent `accessed`.

### 7.4 Removal

A chip leaves when its source is gone and no other source says it, when it is replaced (the replacement links to the old one in the pull request), or when it expires (7.3). Its id is not reused.

## 8. Versioning and change policy

- The spec has a version `MAJOR.MINOR`. `data/layers.yml` declares it in `spec:`; `scripts/check.py` refuses a file that declares another version.
- While MAJOR is 0, a MINOR bump may change fields or rules. Each bump is listed in the changelog below with a migration note, and `scripts/check.py` ships with the same change.
- From 1.0: a MINOR bump only adds optional things; a MAJOR bump may break, and the old MAJOR is supported by the check for one more MINOR cycle.
- A change to the spec is a pull request that edits `SPEC.md`, both schemas, `scripts/check.py`, the data (migration) and the changelog together. A change to an enumeration (status, level, source groups) counts as a spec change.
- Ids are stable: renaming one is a breaking change for every translation, so it is done by adding the new id and removing the old one in the same pull request.

## 9. Generated outputs

| Output | Command | Rule |
|---|---|---|
| `docs/index.html` | `python3 build.py` | One static page with all languages inside. Every chip opens a menu with its sources. `?lang=`, `?theme=light|dark`, `?fit=0` (full width) and `?export=1` (board only) are supported. |
| `docs/figure-<lang>.png` | `python3 export.py` | Full-width board, headless Chrome. |
| awesome list | `python3 build.py` (or `python3 scripts/awesome.py`) | Written between `<!-- awesome:start -->` and `<!-- awesome:end -->` in `README.md` (en) and `README.pt.md` (pt). Never edit between the markers. |

The awesome list has one section per layer and, inside it, one block per group (and per panel). A chip is one line, `- **name** · *state* — description`, followed by its links: ungrouped links first and then one line per source group, `  - Docs: [title](url), [title](url)`. The where items follow the groups of their layer, one link each. The header line carries the counts and the most recent review date.

CI runs `python3 scripts/check.py`, then `python3 build.py`, and fails if `docs/index.html`, `README.md` or `README.pt.md` change, so the committed outputs are always current.

## 10. Page behaviour (informative)

- **Chips.** A chip is a `<button aria-haspopup="menu" aria-expanded>` that opens a `role="menu"` list of `role="menuitem"` links, with `role="group"` for the labelled groups. There is no direct-link chip. The where items (browser, desktop, mobile, edge) are plain links. Enter, Space or a tap opens it; Arrow keys, Home and End move; Escape closes and returns focus to the chip; Tab or a click outside closes it.
- **Preview.** With a mouse (or keyboard focus) a chip shows a short preview: name, status, the one-line description, review date, number of sources and, if there is one, the alert (title, detail, day observed). It never takes the pointer (it does not hide the neighbouring chip from the mouse), opens under the chip or above it when there is no room, and stays inside the screen. The menu opened by click or tap has the same head and alert, then the evidence and the sources; when it does not fit it scrolls inside and never covers its own chip.
- **Themes.** Automatic (follows the system), light or dark. The choice is remembered in `localStorage` (the page works without it).
- **Motion.** Decoration only. The model line and the "Where it runs" icons may move; no information depends on it. Off with `prefers-reduced-motion`, `?motion=0` and in the PNG export (`?export=1`).
- **Demo width.** `docs/index.html` limits the board to fit a laptop screen. `?fit=0` and the PNG export keep the full layout.

## Decisions waiting for approval (0.4)

1. **`featured: false`** (new, optional) keeps a chip off the figure and the page but in the README "Also exists" list. The alternative is a separate list file.
2. Tool groups: "Export with" and "Quantize with" (layer 2). Libraries that wrap a generation loop sit in Run > Runtime.
3. An alert needs one of five kinds; a README notice such as "new feature development is minimized" (torchao) fits none, so it is written in the description, not as an alert. Add a kind (for example `reduced`) if you want those flagged.
4. Earlier decisions (0.3 and 0.2) still stand: alert as its own field with `level` following `kind`, 30-day expiry warning, a broken link does not count as a source, two or more sources per chip, six source groups, status values, ageing 180/365 days, one-line `desc`.

## Changelog

- **0.1** (2026-11-19): first draft.
- **0.2** (2026-11-20): every chip needs at least two sources with distinct urls (`source` is removed from chips; `sources` has a minimum of two); every source carries `title` and, preferably, `group`; the page has no direct-link chip. Migration: `source:` blocks become the first entry of `sources:`, plus a second source. `scripts/linkcheck.py` added.
- **0.3** (2026-11-20): optional `alert` on a chip (`level`, `kind`, `observed`, `evidence`; text `alert.<chip id>`), separate from `status`; alert colours, marker and preview; hover preview now carries the description and the alert; `linkcheck.py` reports alert evidence. Migration: none for existing data besides `spec: "0.3"`.
- **0.4** (2026-11-20): optional `featured` on a chip (off the figure, in the README "Also exists" list); `quant-tools` and `export-tools` groups; quoted words inside an alert text are not treated as our conclusion. Migration: `spec: "0.4"`.
- **0.4** (2026-11-20, addendum): decorative motion (SVG model line, `?motion=0`, reduced motion respected); no data change.
