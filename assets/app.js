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
  function name(el) { var n = el.querySelector(".n"); return n ? n.textContent : el.textContent; }

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
    document.querySelectorAll(".pop[data-menu]").forEach(function (p) {
      p.setAttribute("aria-label", t("ui.menu").replace("{name}", t("chip." + p.getAttribute("data-menu"))));
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
  var themeNow = q.get("theme") || store(true, "webai-theme") || "auto";
  applyTheme(themeNow);
  document.querySelectorAll("[data-theme-choice]").forEach(function (b) {
    b.addEventListener("click", function () { store(false, "webai-theme", b.dataset.themeChoice); applyTheme(b.dataset.themeChoice); });
  });

  /* ---------- hover preview ---------- */
  var tip = document.getElementById("tip"), tipTimer = null;
  var canHover = window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  function place(el, anchor) {
    el.style.visibility = "hidden"; el.hidden = false;
    var r = anchor.getBoundingClientRect(), w = el.offsetWidth, h = el.offsetHeight;
    var x = Math.min(Math.max(8, r.left), window.innerWidth - w - 8), y = r.bottom + 6;
    if (y + h > window.innerHeight - 8 && r.top - 6 - h > 8) y = r.top - 6 - h;
    el.style.left = x + "px"; el.style.top = y + "px"; el.style.visibility = "";
  }
  function showTip(chip) {
    var d = chip.dataset, n = +d.n, lines = [];
    var head = document.createElement("strong"); head.textContent = name(chip);
    var line1 = document.createElement("div"); line1.appendChild(head);
    if (d.status) { var s = document.createElement("em"); s.textContent = t("ui.status." + d.status); line1.appendChild(s); }
    var line2 = document.createElement("div"); line2.className = "sub";
    line2.textContent = [t("ui.reviewed.short") + " " + d.date, n > 1 ? plural(n) : d.host + " · " + t("ui.level." + d.level)].join(" · ");
    tip.replaceChildren(line1, line2);
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

  /* ---------- source menus (tree chips) ---------- */
  var openBtn = null;
  function items(pop) { return Array.prototype.slice.call(pop.querySelectorAll('[role="menuitem"]')); }
  function popOf(btn) { return document.getElementById(btn.getAttribute("aria-controls")); }
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
