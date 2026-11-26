/* Language (?lang=xx), theme (auto/light/dark, ?theme=), export mode (?export=1), fit mode (default; ?fit=0 for full width),
   source menus on chips (click or keyboard; no hover preview), contributor mode (?contribuir=1), size control, share / embed / download / suggest actions, #chip-id deep links.
   Static, no tracking, no dependencies. */
(function () {
  var I18N = window.__I18N__, DEFAULT = "en";
  var q = new URLSearchParams(location.search);
  var root = document.documentElement;
  var lang = DEFAULT, SITE = window.__SITE__ || { base: location.href.split("?")[0], repo: "", branch: "main" };
  if (q.get("export")) root.classList.add("export");

  function store(get, key, value) {
    try { return get ? localStorage.getItem(key) : localStorage.setItem(key, value); } catch (e) { return null; }
  }
  function t(key) { return (I18N[lang] && I18N[lang][key]) || I18N[DEFAULT][key] || key; }

  /* ---------- language ---------- */
  function pickLang() {
    var want = q.get("lang") || store(true, "webai-lang") || (navigator.language || DEFAULT).slice(0, 2);
    return I18N[want] ? want : DEFAULT;
  }
  function plural(n) {
    var cat = "other";
    try { cat = new Intl.PluralRules(lang).select(n); } catch (e) {}
    return t("ui.sources." + (I18N[lang]["ui.sources." + cat] ? cat : "other")).replace("{n}", n);
  }
  function applyLang(l) {
    lang = l;
    root.lang = l;
    document.querySelectorAll("[data-t]").forEach(function (el) { el.textContent = t(el.getAttribute("data-t")); });
    document.querySelectorAll("[data-al]").forEach(function (el) { el.setAttribute("aria-label", t(el.getAttribute("data-al"))); });
    document.querySelectorAll("[data-tl]").forEach(function (el) { el.setAttribute("title", t(el.getAttribute("data-tl"))); });
    document.querySelectorAll("[data-menu-label]").forEach(function (m) {
      m.setAttribute("aria-label", t("ui.menu").replace("{name}", t("chip." + m.getAttribute("data-menu-label"))));
    });
    document.querySelectorAll(".ph-meta").forEach(function (m) {
      m.textContent = t("ui.reviewed.short") + " " + m.dataset.date + " · " + plural(+m.dataset.n);
    });
    document.querySelectorAll("[data-lang]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.lang === l)); });
    document.title = t("site.title");
    refreshLinks(); fillSnippets(); arrange();
    var page = document.querySelector(".page");
    if (page) document.body.setAttribute("data-board-h", Math.ceil(page.getBoundingClientRect().height));
  }
  document.querySelectorAll("[data-lang]").forEach(function (b) {
    b.addEventListener("click", function () {
      store(false, "webai-lang", b.dataset.lang);
      var u = new URL(location.href); u.searchParams.set("lang", b.dataset.lang); history.replaceState(null, "", u);
      applyLang(b.dataset.lang);
    });
  });

  /* ---------- theme: auto (follows the system), light, dark ---------- */
  function applyTheme(choice) {
    if (choice === "light" || choice === "dark") root.setAttribute("data-theme", choice); else root.removeAttribute("data-theme");
    document.querySelectorAll("[data-theme-choice]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.themeChoice === (choice || "auto"))); });
  }
  applyTheme(q.get("theme") || store(true, "webai-theme") || "auto");
  document.querySelectorAll("[data-theme-choice]").forEach(function (b) {
    b.addEventListener("click", function () { store(false, "webai-theme", b.dataset.themeChoice); applyTheme(b.dataset.themeChoice); });
  });

  /* ---------- placing floating boxes ---------- */
  function place(el, anchor) {
    el.style.visibility = "hidden"; el.hidden = false; el.style.maxHeight = "";
    var r = anchor.getBoundingClientRect(), w = el.offsetWidth, h = el.offsetHeight, gap = 8, m = 8;
    var x = Math.min(Math.max(m, r.left), window.innerWidth - w - m);
    var below = window.innerHeight - r.bottom - gap - m, above = r.top - gap - m, y;
    if (h <= below) y = r.bottom + gap;                         // fits under the chip
    else if (h <= above) y = r.top - gap - h;                   // fits over the chip
    else {                                                      // fits on neither side: take the bigger side and scroll inside, never cover the chip
      var room = Math.max(below, above);
      el.style.maxHeight = Math.max(160, room) + "px";
      y = below >= above ? r.bottom + gap : r.top - gap - Math.min(h, Math.max(160, room));
    }
    el.style.left = x + "px"; el.style.top = y + "px"; el.style.visibility = "";
  }

  /* ---------- contributor mode (?contribuir=1 or ?contribute=1): shows what the reader does not see, the broken-link alerts and their evidence ---------- */
  var contrib = q.get("contribuir") === "1" || q.get("contribute") === "1";
  function popOf(btn) { var m = document.getElementById(btn.getAttribute("aria-controls")); return m && (m.closest(".pop") || m); }
  if (contrib && !root.classList.contains("export")) {
    root.classList.add("contrib");
    document.querySelectorAll("[data-contrib-only]").forEach(function (e) { e.hidden = false; });
    document.querySelectorAll("[data-alert-c]").forEach(function (e) { e.setAttribute("data-alert", e.getAttribute("data-alert-c")); });
    var cn = document.querySelector(".contrib-note"); if (cn) cn.hidden = false;
  }

  /* ---------- menus and panels: chips (sources), Share, Download, Suggest, and the Embed panel ---------- */
  var openBtn = null;
  function items(pop) { return Array.prototype.slice.call(pop.querySelectorAll('[role="menuitem"]:not([hidden])')); }
  function close(returnFocus) {
    if (!openBtn) return;
    var btn = openBtn; openBtn = null;
    popOf(btn).hidden = true;
    btn.setAttribute("aria-expanded", "false");
    if (returnFocus) btn.focus();
  }
  function open(btn, focusFirst) {
    close(false);
    var pop = popOf(btn);
    refreshLinks(); fillSnippets();
    btn.setAttribute("aria-expanded", "true");
    place(pop, btn);
    openBtn = btn;
    var isDialog = pop.getAttribute("role") === "dialog";
    if (focusFirst || isDialog) { var list = isDialog ? Array.prototype.slice.call(pop.querySelectorAll("button, a[href]")) : items(pop); if (list[0]) list[0].focus(); }
  }
  function toast(msg) {
    var el = document.createElement("div"); el.className = "toast"; el.setAttribute("role", "status"); el.textContent = msg; document.body.appendChild(el);
    setTimeout(function () { el.remove(); }, 1800);
  }
  function copyText(text, msg, then) {
    function done() { if (msg) toast(msg); if (then) then(); }
    if (navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(text).then(done, fallback); } else { fallback(); }
    function fallback() {
      var ta = document.createElement("textarea"); ta.value = text; ta.style.cssText = "position:fixed;opacity:0"; document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); done(); } catch (e) {} ta.remove();
    }
  }
  function pageUrl() { return SITE.base + "?lang=" + lang; }
  function enc(s) { return encodeURIComponent(s); }
  function issueUrl() { return "https://github.com/" + SITE.repo + "/issues/new?body=" + enc("Page: " + pageUrl() + "\n\n"); }
  function refreshLinks() {
    var url = pageUrl(), title = t("site.title"), set = function (sel, fn) { document.querySelectorAll(sel).forEach(fn); };
    set("[data-share]", function (a) {
      var k = a.getAttribute("data-share");
      a.href = k === "linkedin" ? "https://www.linkedin.com/sharing/share-offsite/?url=" + enc(url)
        : k === "x" ? "https://x.com/intent/post?text=" + enc(title) + "&url=" + enc(url)
        : "mailto:?subject=" + enc(title) + "&body=" + enc(t("site.tagline") + "\n\n" + url);
    });
    set("[data-dl]", function (a) { var ext = a.getAttribute("data-dl"), th = curTheme(); a.href = SITE.base + "figure-" + lang + (th === "dark" ? "-dark" : "") + "." + ext; a.setAttribute("download", "state-of-the-art-webai-" + lang + "-" + th + "." + ext); });
    set("[data-suggest]", function (a) { a.href = issueUrl(); });
    var nat = document.querySelector('[data-act="native"]'); if (nat) nat.hidden = !navigator.share;
  }
  function curTheme() { var th = root.getAttribute("data-theme"); return th || (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"); }
  function snippets() {
    var origin = new URL(SITE.base).origin, theme = "auto", fig = SITE.base + "figure-" + lang + (curTheme() === "dark" ? "-dark" : "");   // language and theme follow the page
    return {
      iframe: '<iframe id="soa-map" src="' + SITE.base + "embed/?lang=" + lang + "&theme=" + theme + '" title="' + t("site.title") + '" style="width:100%;border:0;min-height:320px" loading="lazy"></iframe>\n' +
        '<script>\naddEventListener("message", function (e) {\n  var f = document.getElementById("soa-map");\n  if (e.origin !== "' + origin + '" || e.source !== f.contentWindow) return;\n' +
        '  if (e.data && e.data.type === "soa-height") f.style.height = Math.ceil(e.data.height) + "px";\n});\n<\/script>',
      component: '<script src="' + SITE.base + 'embed.js" async><\/script>\n<state-of-the-art-webai lang="' + lang + '" theme="' + theme + '"></state-of-the-art-webai>',
      image: '<a href="' + pageUrl() + '"><img src="' + fig + '.png" alt="' + t("site.title") + '" style="max-width:100%"></a>\n<!-- ' + t("ui.embed.credit") + " SVG: " + fig + ".svg -->",
      badge: "[![" + t("site.title") + "](" + SITE.base + "badge.svg)](" + SITE.base + ")"
    };
  }
  function fillSnippets() {
    var s = snippets();
    document.querySelectorAll("code[data-preview]").forEach(function (c) { c.textContent = s[c.getAttribute("data-preview")].split("\n")[0]; });   // one truncated line; the full code goes to the clipboard
    var how = document.querySelector("a[data-how]"); if (how) how.href = "https://github.com/" + SITE.repo + (lang === "pt" ? "/blob/" + SITE.branch + "/README.pt.md#a-página" : "#the-page");
  }
  function openChipFromHash() {
    var id = decodeURIComponent(location.hash.slice(1)), b = id && document.querySelector('button.chip[data-id="' + id.replace(/"/g, "") + '"]');
    if (!b) return;
    b.scrollIntoView({ block: "center" });
    setTimeout(function () { open(b, false); }, 300);   // after the scroll settles (scrolling closes menus)
  }
  document.addEventListener("click", function (e) {
    var act = e.target.closest && e.target.closest("[data-act]");
    if (act) {
      var kind = act.getAttribute("data-act");
      if (kind === "native") navigator.share({ title: t("site.title"), text: t("site.tagline"), url: pageUrl() }).catch(function () {});
      else copyText(pageUrl(), t("ui.share.copied"));
      close(false); return;
    }
    var cs = e.target.closest && e.target.closest("[data-copy-snippet]");
    if (cs) {
      var label = cs.querySelector("span"), live = document.getElementById("emb-live");
      copyText(snippets()[cs.getAttribute("data-copy-snippet")], null, function () {
        label.textContent = t("ui.embed.copied"); cs.classList.add("done"); if (live) live.textContent = t("ui.embed.copied") + ": " + t("ui.embed.t." + cs.getAttribute("data-copy-snippet"));
        setTimeout(function () { label.textContent = t("ui.embed.copy"); cs.classList.remove("done"); if (live) live.textContent = ""; }, 1500);
      });
      return;
    }
    if (e.target.closest && e.target.closest("[data-close-pop]")) { close(true); return; }
    var btn = e.target.closest && e.target.closest("button[aria-haspopup][aria-controls]");
    if (btn) {
      if (openBtn === btn) close(false); else open(btn, e.detail === 0);  // e.detail === 0: opened with the keyboard
      return;
    }
    if (openBtn && !(e.target.closest && e.target.closest(".pop"))) close(false);
  });
  document.addEventListener("keydown", function (e) {
    var btn = e.target.closest && e.target.closest("button[aria-haspopup][aria-controls]");
    if (btn && btn.getAttribute("aria-haspopup") === "menu" && (e.key === "ArrowDown" || e.key === "ArrowUp")) { e.preventDefault(); open(btn, true); return; }
    if (e.key === "Escape") { if (openBtn) { e.preventDefault(); close(true); } return; }
    var pop = e.target.closest && e.target.closest(".pop");
    if (!pop) return;
    if (pop.getAttribute("role") === "dialog") {          // the embed panel: Tab stays inside it
      if (e.key === "Tab") {
        var f = Array.prototype.slice.call(pop.querySelectorAll("button, a[href]")), first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); } else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
      return;
    }
    var list = items(pop), i = list.indexOf(document.activeElement);
    if (e.key === "ArrowDown") { e.preventDefault(); list[(i + 1) % list.length].focus(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); list[(i - 1 + list.length) % list.length].focus(); }
    else if (e.key === "Home") { e.preventDefault(); list[0].focus(); }
    else if (e.key === "End") { e.preventDefault(); list[list.length - 1].focus(); }
    else if (e.key === "Tab") close(false);
  });
  window.addEventListener("scroll", function (e) { if (e.target.closest && e.target.closest(".pop")) return; close(false); }, true);   // scrolling inside a menu keeps it open
  var lastW = window.innerWidth;
  window.addEventListener("resize", function () { if (window.innerWidth !== lastW) { lastW = window.innerWidth; close(false); } });  // phones resize when the address bar hides
  window.addEventListener("hashchange", openChipFromHash);

  /* ---------- embed: tell the parent page how tall we are (the parent validates the origin; so do we) ---------- */
  var embedded = root.classList.contains("embed") && window.parent !== window;
  var parentOrigin = (location.ancestorOrigins && location.ancestorOrigins[0]) || (document.referrer ? new URL(document.referrer).origin : "*");
  function postHeight() {
    if (!embedded) return;
    var page = document.querySelector(".page"); if (!page) return;
    window.parent.postMessage({ type: "soa-height", height: Math.ceil(page.getBoundingClientRect().height + 8) }, parentOrigin);
  }
  window.addEventListener("message", function (e) {       // optional: the parent can change language or theme
    if (!embedded || e.source !== window.parent || (parentOrigin !== "*" && e.origin !== parentOrigin)) return;
    var d = e.data; if (!d || d.type !== "soa-set") return;
    if (I18N[d.lang]) applyLang(d.lang);
    if (d.theme === "light" || d.theme === "dark" || d.theme === "auto") applyTheme(d.theme);
  });

  /* ---------- the model line: one SVG path over the board; it marches (dash offset) and carries a small dot when motion is on.
     Motion is decoration only: off with prefers-reduced-motion, with ?motion=0, and in the PNG export. ---------- */
  var NS = "http://www.w3.org/2000/svg", reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
  function motionOn() { return !root.classList.contains("export") && q.get("motion") !== "0" && !(reduce && reduce.matches); }
  function drawFlow() {}   // the model line of the single-path map is gone: lanes carry their own arrows (CSS)

  /* ---------- layout: the board uses the window. It has three lanes (rows) with a fixed arrangement, so only the chip font is searched:
     Normal: the target font (about 13px at 1440 wide, 14px at 1920), Large: a bigger font, Fit to screen: the biggest font, never below 12px if it can,
     with which the whole map fits without scrolling; the lanes stretch to fill the height. If nothing fits at the smallest font the page scrolls. ---------- */
  var U_MIN = 5, U_NOTICE = 9, U_MAX = 20, state = { sz: [1], u: 13 };      // chip font limits (px) and the last choice. The arrangement is fixed (three lanes): only the font is searched.
  function setColumns() {}
  var S_BASE = 2.2, S_RATE = 0.45;   // non-text sizes (padding, gaps, icons) scale slower than the text: s = 2.2px + 0.45 u
  function setUnit(board, u) { board.style.setProperty("--u", u + "px"); board.style.setProperty("--s", (S_BASE + S_RATE * u).toFixed(2) + "px"); }
  function heightOf(board, sz, u) { setUnit(board, u); setColumns(sz); return board.offsetHeight; }
  function maxU(board, k) { return U_MAX; }          // the narrowest a column may get is 24 units
  function candidates() { return [[1]]; }
  function sameSz(a, b) { return a && b && a.join("+") === b.join("+"); }
  var STEP = 0.975, STEP_ALL = 0.94;   // font steps of 2.5% between tries: continuous enough, and a layout measure is cheap
  // quick: this arrangement only. Walk the font up from where it was while it fits, or down until it does.
  function fitOne(board, sz, avail, u) {
    var cap = Math.min(U_MAX, maxU(board, sz.length)); u = Math.min(cap, Math.max(U_MIN, u));
    if (heightOf(board, sz, u) <= avail) { for (var i = 0; i < 12 && u / STEP <= cap; i++) { var up = u / STEP; if (heightOf(board, sz, up) > avail) break; u = up; } return u; }
    while (u > U_MIN) { u = Math.max(U_MIN, u * STEP); if (heightOf(board, sz, u) <= avail) return u; }
    return 0;
  }
  // full: every arrangement. From the largest font that could possibly fit, step down until some arrangement fits; that is the largest scale.
  function fitAll(board, avail) {
    var u0 = state.u, hmin = Infinity;
    candidates(board, u0, false).forEach(function (sz) { hmin = Math.min(hmin, heightOf(board, sz, u0)); });
    var u = Math.min(U_MAX, u0 * Math.sqrt(avail / hmin) * 1.25);
    for (; u >= U_MIN; u *= STEP_ALL) {
      var fit = null;
      candidates(board, u, false).forEach(function (sz) {
        if (u > maxU(board, sz.length)) return;
        var h = heightOf(board, sz, u);
        if (h <= avail && (!fit || h > fit.h)) fit = { sz: sz, h: h };          // of those that fit, the one that needs the least stretching
      });
      if (fit) {                                                                     // the coarse step found the neighbourhood: now every arrangement, in small steps
        var fine = candidates(board, u, false).map(function (sz) { return { sz: sz, u: fitOne(board, sz, avail, u) }; }).filter(function (r) { return r.u > 0; }).sort(function (x, y) { return y.u - x.u; });
        var best = fine[0], keep = state.sz && fine.filter(function (r) { return sameSz(r.sz, state.sz); })[0];
        return keep && keep.u >= best.u * 0.96 ? keep : best;                        // hysteresis: keep the current arrangement unless another is clearly bigger
      }
    }
    return null;
  }
  function geometry(board, embed) {
    var foot = document.querySelector(".foot"), page = document.querySelector(".page"), top = board.getBoundingClientRect().top + window.pageYOffset;
    var below = embed ? 0 : (foot ? foot.getBoundingClientRect().height + parseFloat(getComputedStyle(foot).marginTop) : 0) + parseFloat(getComputedStyle(page).paddingBottom);
    return { avail: embed ? Infinity : Math.floor(document.documentElement.clientHeight - top - below) };   // exact: the layout viewport, nothing rounded up
  }
  /* Fit to screen (the default): the largest scale at which some arrangement fits the available rectangle without scrolling. Every arrangement is
     measured, the best few are solved for their largest font, the biggest wins (the previous one is kept unless the new one is clearly better:
     hysteresis). `quick` re-solves only the current arrangement (cheap, run on every frame while the window is dragged); the full search runs
     when the window stops. Normal: a fixed 13px font. Large: a bigger font. Both reflow and may scroll. */
  // marks the group that starts each column of a card or panel, so the dotted separator above a group is not drawn at the top of a column
  function markFirst() {
    document.querySelectorAll(".card .groups, .panel .groups").forEach(function (g) {
      var gs = Array.prototype.slice.call(g.children), top = gs.length ? gs[0].getBoundingClientRect().top : 0;
      gs.forEach(function (x) { x.classList.toggle("first", x.getBoundingClientRect().top - top < 3); });
    });
  }
  function arrange(quick) {
    arrange2(quick); markFirst();
  }
  function arrange2(quick) {
    var board = document.querySelector(".board");
    if (!board) return;
    if (root.classList.contains("export")) return;   // the static figure keeps the classic layout (--u set in CSS)
    var vw = window.innerWidth, mode = root.getAttribute("data-size") === "large" ? "large" : "fit", embed = root.classList.contains("embed"), phone = vw <= 700;
    var fitMode = !phone && !embed && mode === "fit";
    root.classList.remove("fitted");
    if (fitMode) root.classList.add("fitting");                         // no scrollbars while measuring: the width is the final one
    board.style.minHeight = "";
    var t0 = performance.now(), notice = false, pick, u, fits = false, g = geometry(board, embed);
    if (phone || embed || mode !== "fit") {
      u = phone ? 14 : embed ? Math.min(18, Math.max(12, 13 + Math.min(vw - 1440, 480) * 0.00104)) : Math.min(U_MAX, Math.max(15, 15 + (vw - 1440) * 0.004));
      var small = null;
      candidates(board, u, phone).forEach(function (sz) { var h = heightOf(board, sz, u); if (!small || h < small.h) small = { sz: sz, h: h }; });
      pick = small.sz;
    } else {
      var best = null;
      if (quick && state.sz) { var s = fitOne(board, state.sz, g.avail, state.u); if (s > 0) best = { sz: state.sz, u: s }; }
      if (!best) best = fitAll(board, g.avail);
      if (!best) {                                                      // nothing fits even at the smallest font: the shortest, and scroll
        u = U_MIN; var sm = null;
        candidates(board, u, false).forEach(function (sz) { var h = heightOf(board, sz, u); if (!sm || h < sm.h) sm = { sz: sz, h: h }; });
        best = { sz: sm.sz, u: U_MIN }; notice = true;
      }
      pick = best.sz; u = Math.max(U_MIN, best.u); fits = !notice;
    }
    state.sz = pick; state.u = u;
    heightOf(board, pick, u);
    root.classList.remove("fitting");
    if (fits && fitMode) root.classList.add("fitted");               // the page is exactly one viewport tall: the board fills what is left and nothing scrolls
    var sw = document.querySelector(".small-window"); if (sw) sw.hidden = !(notice || (!phone && !embed && mode === "fit" && u < U_NOTICE));
    drawFlow(); postHeight();
    var chip = board.querySelector(".chip"), se = document.scrollingElement;
    document.body.setAttribute("data-fit", "unit " + (Math.round(u * 100) / 100) + "px; chip " + (chip ? getComputedStyle(chip).fontSize : "?") + "; lanes 3" + "; board " + board.offsetWidth + "x" + board.offsetHeight +
      "; window " + vw + "x" + window.innerHeight + "; board bottom at " + Math.round(board.getBoundingClientRect().bottom + window.pageYOffset) + " of " + window.innerHeight + "; fits " + fits + "; " + (quick ? "quick" : "full") + " fit took " + Math.round(performance.now() - t0) + " ms; page scrolls vertically " + (se.scrollHeight > se.clientHeight) + ", horizontally " + (se.scrollWidth > se.clientWidth));
  }
  // follow the window continuously: resize, the visual viewport (zoom), and a fixed sentinel that is as big as the viewport
  var frame = 0, idle = null;
  function schedule() {
    if (!frame) frame = requestAnimationFrame(function () { frame = 0; arrange(true); });
    clearTimeout(idle); idle = setTimeout(function () { arrange(false); }, 140);
  }

  window.addEventListener("resize", schedule);
  if (window.visualViewport) window.visualViewport.addEventListener("resize", schedule);
  window.addEventListener("orientationchange", schedule);
  (function () {
    var s = document.createElement("div"); s.setAttribute("aria-hidden", "true"); s.style.cssText = "position:fixed;inset:0;visibility:hidden;pointer-events:none;z-index:-1";
    document.body.appendChild(s);
    if (window.ResizeObserver) new ResizeObserver(schedule).observe(s);
  })();
  function applyMotion() { root.classList.toggle("motion", motionOn()); drawFlow(); }
  if (reduce && reduce.addEventListener) reduce.addEventListener("change", applyMotion);
  if (window.ResizeObserver) { var ro = new ResizeObserver(function () { requestAnimationFrame(function () { drawFlow(); postHeight(); }); }); ro.observe(document.querySelector(".board")); }

  /* ---------- export helper (used by export.py): the static board as XHTML, for the SVG figure ---------- */
  function exportXhtml() {
    var board = document.querySelector(".board").cloneNode(true);
    board.querySelectorAll(".pop, .fl-dot").forEach(function (e) { e.remove(); });
    board.querySelectorAll("[id]").forEach(function (e) { e.removeAttribute("id"); });
    var r = document.querySelector(".board").getBoundingClientRect(), x = new XMLSerializer().serializeToString(board);
    document.body.innerHTML = "<textarea id='xhtml' data-w='" + Math.round(r.width) + "' data-h='" + Math.round(r.height) + "'></textarea>";
    document.getElementById("xhtml").textContent = x;
  }

  setTimeout(function () { root.classList.add("settled"); }, 2200);   // the entrance animation runs once; a re-fit must not replay it

  /* ---------- start ---------- */
  applyLang(pickLang());
  applyMotion();
  // The layout measures text, and the text width depends on the font: wait for the web font before the final arrangement (and redo it if a font
  // arrives later, for example the latin-ext part when a language needs it).
  function fontsReady() { return document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve(); }
  if (document.fonts && document.fonts.addEventListener) document.fonts.addEventListener("loadingdone", function () { arrange(); postHeight(); });
  window.addEventListener("load", function () { fontsReady().then(start, start); });
  function start() {
    arrange();
    applyMotion();
    postHeight(); openChipFromHash();
    if (q.get("xhtml")) exportXhtml();
    var want = q.get("open");  // deep links, handy for screenshots
    if (want) { var b = document.querySelector('[data-id="' + want + '"]'); if (b && b.dataset.kind === "tree") open(b, false); }
    var mn = q.get("menu"); if (mn) { var mb = document.querySelector('[data-menu-btn="' + mn + '"]'); if (mb) open(mb, false); }
  }
})();
