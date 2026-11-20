/* Language (?lang=xx), theme (auto/light/dark, ?theme=), export mode (?export=1), fit mode (default; ?fit=0 for full width),
   hover preview and source menus on chips. No dependencies. */
(function () {
  var I18N = window.__I18N__, DEFAULT = "en";
  var q = new URLSearchParams(location.search);
  var root = document.documentElement;
  var lang = DEFAULT;
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
  function popOf(btn) { var m = document.getElementById(btn.getAttribute("aria-controls")); return m && m.closest(".pop"); }
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

  /* ---------- source menus: every chip opens one (touch, click, Enter, Space, ArrowDown) ---------- */
  var openBtn = null;
  function items(pop) { return Array.prototype.slice.call(pop.querySelectorAll('[role="menuitem"]')); }
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
    btn.setAttribute("aria-expanded", "true");
    place(pop, btn);
    openBtn = btn;
    if (focusFirst) { var list = items(pop); if (list[0]) list[0].focus(); }
  }
  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest('button[data-kind="tree"]');
    if (btn) {
      if (openBtn === btn) close(false); else open(btn, e.detail === 0);  // e.detail === 0: opened with the keyboard
      return;
    }
    if (openBtn && !(e.target.closest && e.target.closest(".pop"))) close(false);
  });
  document.addEventListener("keydown", function (e) {
    var btn = e.target.closest && e.target.closest('button[data-kind="tree"]');
    if (btn && (e.key === "ArrowDown" || e.key === "ArrowUp")) { e.preventDefault(); open(btn, true); return; }
    if (e.key === "Escape") { if (openBtn) { e.preventDefault(); close(true); } hideTip(); return; }
    var pop = e.target.closest && e.target.closest(".pop");
    if (!pop) return;
    var list = items(pop), i = list.indexOf(document.activeElement);
    if (e.key === "ArrowDown") { e.preventDefault(); list[(i + 1) % list.length].focus(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); list[(i - 1 + list.length) % list.length].focus(); }
    else if (e.key === "Home") { e.preventDefault(); list[0].focus(); }
    else if (e.key === "End") { e.preventDefault(); list[list.length - 1].focus(); }
    else if (e.key === "Tab") close(false);
  });
  window.addEventListener("scroll", function () { close(false); hideTip(); }, true);
  var lastW = window.innerWidth;
  window.addEventListener("resize", function () { if (window.innerWidth !== lastW) { lastW = window.innerWidth; close(false); hideTip(); } });  // phones resize when the address bar hides

  /* ---------- start ---------- */
  applyLang(pickLang());
  window.addEventListener("load", function () {
    applyLang(lang);
    var want = q.get("open"), tipFor = q.get("tip");  // deep links, handy for screenshots
    if (want) { var b = document.querySelector('[data-id="' + want + '"]'); if (b && b.dataset.kind === "tree") open(b, false); }
    if (tipFor) { var c = document.querySelector('[data-id="' + tipFor + '"]'); if (c) showTip(c); }
  });
})();
