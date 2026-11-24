# Feedback from ErikH2000: what changed (branch `feedback-erik`, local only)

1. **First sentence.** `site.tagline` (also `<title>` meta description, og:description, share text) now says what the page is and is not: "An infographic of the layers between a model and a person when it runs on the device, with each layer's options. Not a step-by-step wizard, no model picker, no advice for your case. Each info icon opens its sources." PT equivalent. `ui.legend` now says "Each info icon opens...". The header paragraph wraps (it used to be cut with an ellipsis). Texts are drafts for Eduardo to adjust (max 220 chars, enforced by check.py).
2. **Dropdowns.** Already replaced by the info icon; nothing to do.
3. **Icons that animate on hover and do nothing on click.** They were the "Where it runs" pictograms (browser, desktop, mobile, edge): they jumped and grew on hover/focus but only the name is a link. Chose to **remove the hover/focus animation**. The idle decorative loops inside them (cursor blink, glow, LEDs) stay and are already off with reduced motion or `?motion=0`. Nothing was invented to make them clickable. If Erik meant another icon, the screenshot is missing: please confirm.
4. **Broken-link alerts.** For readers the page no longer shows alerts of kind `broken-link` (marker, alert box, broken evidence links; the 10 alert chips become 5). Contributor mode: `?contribuir=1` or `?contribute=1` shows everything as before, plus a header note (PT/EN). Alerts stay in `data/layers.yml`, README lists, `linkcheck.py`. Documented in CONTRIBUTING.md, SPEC.md (4.5) and README. Set of hidden kinds: `READER_HIDDEN` in `build.py`.
5. **Hover vs click.** Chose to **remove hover handling** (simpler, no hover on phones). The chip panel (click, tap, Enter/Space) shows the full information; keyboard focus still shows the focus ring and no longer pops a short preview. Removed the tooltip code, markup and CSS and the `?tip=` parameter.

Also regenerated: docs/index.html, docs/embed, figures (PNG/SVG; the broken-link markers are gone from them), READMEs.

## For Eduardo to decide (nothing deleted)

Alert types today (10 alerts): broken-link 5 (olive, onnxruntime, ort-web, ort-genai, ort-genai-builder: hidden from readers); deprecated 2 (AutoAWQ, MediaPipe LLM Inference mobile), superseded 1 (AutoGPTQ), moved 2 (Optimum, litert-torch): shown to everyone.
- broken-link: keep hidden from readers; they are maintenance work. The 5 point to the same Microsoft repos that answered 404 on 2026-11-20: recheck, and if the URLs are back, remove the alerts.
- removed (none now): same family as broken-link (source gone). Conservative default shows it; consider hiding it from readers too.
- deprecated / superseded: real information for a reader choosing a tool; keep visible.
- moved: low value for a reader (redirect only); could be contributor-only or become a plain note in the description.
- Still open: whether the contributor URL should be linked from the footer, and the final wording of the tagline.

## Verification

- `python3 scripts/check.py` ok; `python3 build.py` run, outputs committed; `python3 scripts/test_resize.py --quick` PASS; `python3 export.py` run.
- Chrome (playwright, file://), docs/index.html and docs/embed, PT/EN, light/dark, 1280 and 390: no horizontal scroll, no clipped text (before/after in `.capturas/`, outside git; `test_feedback.js` and `shots.js` there). Automated check: reader mode shows no "link broken" text, the Olive panel has only its 3 sources; contributor mode shows alert and evidence on all 10 alert chips; no tooltip element on hover. Not run: full `test_resize.py` matrix (only `--quick`).
- Note: in headless Playwright at 1280x800 the board overflows the viewport in the screenshots, before and after my change alike; test_resize (real Chrome via CDP) confirms exact fit.
