/* Language (?lang=xx), theme (auto/light/dark, ?theme=), export mode (?export=1), fit mode (default; ?fit=0 for full width),
   hover preview and source menus on chips, size control, share / embed / download / suggest actions, #chip-id deep links.
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
    hideTip();
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

  /* ---------- hover preview: the head of the chip's menu (name, state, description, review, sources) and its alert ---------- */
  var tip = document.getElementById("tip"), tipTimer = null;
  var canHover = window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  function popOf(btn) { var m = document.getElementById(btn.getAttribute("aria-controls")); return m && (m.closest(".pop") || m); }
  function clean(node) {
    var c = node.cloneNode(true);
    c.querySelectorAll("[id]").forEach(function (e) { e.removeAttribute("id"); });
    c.removeAttribute("aria-labelledby");
    return c;
  }
  function showTip(chip) {
    var pop = chip.dataset.kind === "tree" ? popOf(chip) : null, parts = [];
    if (pop) {
      parts.push(clean(pop.querySelector(".pop-head")));
      var al = pop.querySelector(".pop-alert");
      if (al) parts.push(clean(al));
      if (pop.dataset.alert) tip.setAttribute("data-alert", pop.dataset.alert); else tip.removeAttribute("data-alert");
    } else {                                  // where-it-runs items: one link, no menu
      var d = chip.dataset, line = document.createElement("div");
      line.className = "pop-head";
      line.innerHTML = "<div class='ph-top'><strong></strong></div><p class='ph-meta'></p>";
      line.querySelector("strong").textContent = chip.textContent;
      line.querySelector(".ph-meta").textContent = t("ui.reviewed.short") + " " + d.date + " · " + d.host + " · " + t("ui.level." + d.level);
      parts.push(line); tip.removeAttribute("data-alert");
    }
    tip.replaceChildren.apply(tip, parts);
    place(tip, chip);
  }
  function hideTip() { clearTimeout(tipTimer); if (tip) tip.hidden = true; }
  if (canHover) {
    document.addEventListener("mouseover", function (e) {
      var c = e.target.closest && e.target.closest("[data-kind]");
      if (!c || c.getAttribute("aria-expanded") === "true") return;
      clearTimeout(tipTimer); tipTimer = setTimeout(function () { showTip(c); }, 150);
    });
    document.addEventListener("mouseout", function (e) {
      var c = e.target.closest && e.target.closest("[data-kind]");
      if (c && !c.contains(e.relatedTarget)) hideTip();
    });
  }
  document.addEventListener("focusin", function (e) {
    var c = e.target.closest && e.target.closest("[data-kind]");
    if (c && c.matches(":focus-visible") && c.getAttribute("aria-expanded") !== "true") showTip(c); else if (!c) hideTip();
  });
  document.addEventListener("focusout", hideTip);

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
    close(false); hideTip();
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
    set("[data-dl]", function (a) { var p = a.getAttribute("data-dl").split("-"); a.href = SITE.base + "figure-" + lang + (p[1] === "dark" ? "-dark" : "") + "." + p[0]; a.setAttribute("download", "state-of-the-art-webai-" + lang + "-" + p[1] + "." + p[0]); });
    set("[data-suggest]", function (a) { a.href = issueUrl(); });
    set("[data-edit]", function (a) { a.href = "https://github.com/" + SITE.repo + "/edit/" + SITE.branch + "/data/layers.yml"; });
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
    if (e.key === "Escape") { if (openBtn) { e.preventDefault(); close(true); } hideTip(); return; }
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
  window.addEventListener("scroll", function (e) { if (e.target.closest && e.target.closest(".pop")) return; close(false); hideTip(); }, true);   // scrolling inside a menu keeps it open
  var lastW = window.innerWidth;
  window.addEventListener("resize", function () { if (window.innerWidth !== lastW) { lastW = window.innerWidth; close(false); hideTip(); } });  // phones resize when the address bar hides
  window.addEventListener("hashchange", openChipFromHash);

  /* ---------- size: Fit to screen / Normal / Large (what each means is in arrange() below) ---------- */
  function applySize(s) {
    root.classList.add("sized"); root.setAttribute("data-size", s);
    document.querySelectorAll("[data-size-choice]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.sizeChoice === s)); });
    arrange();
  }
  document.querySelectorAll("[data-size-choice]").forEach(function (b) {
    b.addEventListener("click", function () {
      store(false, "webai-size", b.dataset.sizeChoice);
      var u = new URL(location.href); u.searchParams.set("size", b.dataset.sizeChoice); u.searchParams.delete("fit"); history.replaceState(null, "", u);
      applySize(b.dataset.sizeChoice);
    });
  });
  var resizeTimer = null;
  window.addEventListener("resize", function () { clearTimeout(resizeTimer); resizeTimer = setTimeout(arrange, 120); });

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
  function drawFlow() {
    var board = document.querySelector(".board");
    if (!board) return;
    var b = board.getBoundingClientRect(), W = Math.round(b.width), H = Math.round(b.height);
    var svg = board.querySelector("svg.flow");
    if (!svg) {
      svg = document.createElementNS(NS, "svg"); svg.setAttribute("class", "flow"); svg.setAttribute("aria-hidden", "true");
      svg.appendChild(document.createElementNS(NS, "path")).setAttribute("class", "fl-path");
      board.appendChild(svg);
    }
    svg.setAttribute("width", W); svg.setAttribute("height", H); svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    var cols = Array.prototype.slice.call(board.querySelectorAll(".cols > .col")).filter(function (c) { return c.firstElementChild; });
    if (!cols.length) return;
    var xs = cols.map(function (c) { var r = c.querySelector(".badge").getBoundingClientRect(); return r.left + r.width / 2 - b.left; });
    var cr = board.querySelector(".cols").getBoundingClientRect(), u = parseFloat(getComputedStyle(board).fontSize) || 13, r = 1.5 * u;
    var yTop = (cr.top - b.top) / 2, yBot = (cr.bottom - b.top) + (b.bottom - cr.bottom) / 2, k = xs.length;
    // the model goes down the first column's gutter, turns along the bottom, goes up the next, turns along the top, and so on
    var d = "M" + xs[0] + ",0";
    for (var i = 0; i < k; i++) {
      var down = i % 2 === 0, x = xs[i];
      if (i === k - 1) { d += " L" + x + "," + (down ? H : 0); break; }
      var nx = xs[i + 1], yt = down ? yBot : yTop, dy = down ? -r : r;
      d += " L" + x + "," + (yt + dy) + " Q" + x + "," + yt + " " + (x + r) + "," + yt + " L" + (nx - r) + "," + yt + " Q" + nx + "," + yt + " " + nx + "," + (yt + dy);
    }
    var tm = document.getElementById("tag-model"), tp = document.getElementById("tag-person"), endsDown = (k - 1) % 2 === 0;
    if (tm) { tm.style.left = (xs[0] + 0.7 * u) + "px"; tm.style.top = "2px"; }
    if (tp) { tp.style.left = (xs[k - 1] + 0.7 * u) + "px"; tp.style.top = endsDown ? (H - 1.5 * u - 2) + "px" : "2px"; }
    svg.querySelector(".fl-path").setAttribute("d", d);
    root.classList.add("flow");
    var dot = svg.querySelector(".fl-dot");
    if (motionOn()) {
      if (!dot) {
        dot = document.createElementNS(NS, "g"); dot.setAttribute("class", "fl-dot");
        var h = dot.appendChild(document.createElementNS(NS, "circle")); h.setAttribute("class", "halo"); h.setAttribute("r", 9);
        dot.appendChild(document.createElementNS(NS, "circle")).setAttribute("r", 4.5);
        var m = dot.appendChild(document.createElementNS(NS, "animateMotion")); m.setAttribute("dur", "18s"); m.setAttribute("repeatCount", "indefinite");
        svg.appendChild(dot);
      }
      dot.querySelector("animateMotion").setAttribute("path", d);
    } else if (dot) { dot.remove(); }
  }

  /* ---------- layout: the board uses the window. It picks the chip font and how the five cards are arranged in columns.
     Normal: the target font (about 13px at 1440 wide, 14px at 1920), Large: a bigger font, Fit to screen: the biggest font, never below 12px,
     with which the whole map fits without scrolling. The cards are re-arranged (1 to 5 columns, stacked or side by side) and stretch to fill
     the width and the height; if nothing fits at the smallest font the page scrolls instead of shrinking the text. ---------- */
  var cards = null, CARD_W = [1.0, 1.25, 1.9, 1.15, 0.95];   // how wide each card likes to be, relative to the others
  function compositions(n, k) {                                // every way to cut n consecutive cards into k columns
    var out = [];
    (function rec(left, parts, cur) {
      if (parts === 1) { out.push(cur.concat(left)); return; }
      for (var i = 1; i <= left - parts + 1; i++) rec(left - i, parts - 1, cur.concat(i));
    })(n, k, []);
    return out;
  }
  var PRESETS = [[1, 1, 1, 1, 1], [1, 1.45, 1, 1, 1], [1, 1, 1.35, 1, 1], [1, 1.3, 1.2, 1, 1], [1.2, 1.3, 1, 1, 1]];   // widths to try for the cards
  function setColumns(sizes, weights, preset) {
    var el = document.querySelector(".board .cols"), at = 0;
    while (el.children.length < sizes.length) { var c = document.createElement("div"); c.className = "col"; el.appendChild(c); }
    var w = [];
    sizes.forEach(function (n, ci) {
      var m = 0;
      for (var j = 0; j < n; j++) { el.children[ci].appendChild(cards[at]); m = Math.max(m, CARD_W[at] * (preset ? preset[at] : 1)); at++; }
      w.push(m);
    });
    while (el.children.length > sizes.length) el.removeChild(el.lastChild);
    el.classList.add("js");
    el.style.gridTemplateColumns = (weights || w).map(function (x) { return "minmax(0," + x + "fr)"; }).join(" ");
  }
  function arrange() {
    var board = document.querySelector(".board");
    if (!board) return;
    var el = board.querySelector(".cols");
    cards = cards || Array.prototype.slice.call(el.querySelectorAll(".card")).sort(function (a, b) { return a.dataset.n - b.dataset.n; });
    if (root.classList.contains("export")) { setColumns([2, 1, 2], [1, 1.43, 1]); drawFlow(); return; }   // the static figure keeps the classic layout
    var vw = window.innerWidth, mode = root.getAttribute("data-size") || "normal", embed = root.classList.contains("embed");
    var base = Math.min(18, Math.max(12, 13 + Math.min(vw - 1440, 480) * 0.00104 + Math.max(vw - 1920, 0) * 0.0035)), phone = vw <= 700, uMax, uMin;   // 13px at 1440, 13.5 at 1920, growing after
    
    if (phone) uMax = uMin = 14;
    else if (mode === "large") uMax = uMin = Math.min(22, base * 1.18);
    else if (mode === "fit") { uMax = base; uMin = 12; }
    else uMax = uMin = base;
    board.style.minHeight = "";
    var top = board.getBoundingClientRect().top + window.pageYOffset, avail = embed ? Infinity : window.innerHeight - top - 20, u = uMax, pick = null, fits = false;
    for (;;) {
      board.style.setProperty("--u", u + "px");
      var W = board.clientWidth, gc = u * 1.9, kmax = phone ? 1 : Math.max(1, Math.min(5, Math.floor((W + gc) / (u * 24 + gc)))), fit = null, small = null;
      for (var k = 1; k <= kmax; k++) {
        compositions(5, k).forEach(function (sz) {
          setColumns(sz);
          var h = board.offsetHeight, cand = { sz: sz, h: h };
          if (h <= avail && (!fit || h > fit.h)) fit = cand;            // of those that fit, the one that needs the least stretching
          if (!small || h < small.h) small = cand;                      // otherwise the shortest
        });
      }
      if (embed) { pick = small; break; }
      if (fit) { pick = fit; fits = true; break; }
      if (u - 0.5 >= uMin) { u -= 0.5; continue; }
      pick = small; break;
    }
    setColumns(pick.sz, null, pick.pre);
    if (fits) board.style.minHeight = avail + "px";                    // fill the room: the cards stretch evenly
    drawFlow(); postHeight();
    var chip = board.querySelector(".chip"), se = document.scrollingElement;
    document.body.setAttribute("data-fit", "unit " + u + "px; chip " + (chip ? getComputedStyle(chip).fontSize : "?") + "; columns " + pick.sz.join("+") + "; board " + board.offsetWidth + "x" + board.offsetHeight +
      "; window " + vw + "x" + window.innerHeight + "; board bottom at " + Math.round(board.getBoundingClientRect().bottom + window.pageYOffset) + " of " + window.innerHeight + "; fits " + fits + "; page scrolls vertically " + (se.scrollHeight > se.clientHeight) + ", horizontally " + (se.scrollWidth > se.clientWidth));
  }
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

  /* ---------- start ---------- */
  applyLang(pickLang());
  applyMotion();
  document.querySelectorAll("[data-size-choice]").forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.sizeChoice === root.getAttribute("data-size"))); });
  window.addEventListener("load", function () {
    arrange();
    applyMotion();
    postHeight(); openChipFromHash();
    if (q.get("xhtml")) exportXhtml();
    var want = q.get("open"), tipFor = q.get("tip");  // deep links, handy for screenshots
    if (want) { var b = document.querySelector('[data-id="' + want + '"]'); if (b && b.dataset.kind === "tree") open(b, false); }
    if (tipFor) { var c = document.querySelector('[data-id="' + tipFor + '"]'); if (c) showTip(c); }
    var mn = q.get("menu"); if (mn) { var mb = document.querySelector('[data-menu-btn="' + mn + '"]'); if (mb) open(mb, false); }
  });
})();
