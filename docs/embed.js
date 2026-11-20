/* <state-of-the-art-webai lang="pt" theme="auto"></state-of-the-art-webai>
   Add <script src=".../embed.js" async></script> once. The element shows the live map in an iframe inside a shadow root and
   follows its height. Nothing is stored and nothing is tracked. The address comes from the script's own URL, so the map is always
   the one the site serves today. */
(function () {
  var script = document.currentScript, base = new URL(".", script ? script.src : location.href).href, origin = new URL(base).origin;
  class SOA extends HTMLElement {
    static get observedAttributes() { return ["lang", "theme"]; }
    connectedCallback() {
      if (this.frame) return;
      var root = this.attachShadow({ mode: "open" });
      root.innerHTML = '<style>:host{display:block}iframe{width:100%;border:0;display:block;min-height:320px}</style>';
      this.frame = document.createElement("iframe");
      this.frame.title = "State of the Art of WebAI";
      this.frame.loading = "lazy";
      root.appendChild(this.frame);
      var me = this;
      this.onMsg = function (e) {   // only the iframe we created, only from the site's origin, only our message type
        if (e.source !== me.frame.contentWindow || (e.origin !== origin && origin !== "null")) return;
        var d = e.data;
        if (d && d.type === "soa-height" && typeof d.height === "number") me.frame.style.height = Math.ceil(d.height) + "px";
      };
      window.addEventListener("message", this.onMsg);
      this.load();
    }
    disconnectedCallback() { window.removeEventListener("message", this.onMsg); }
    attributeChangedCallback() { if (this.frame) this.load(); }
    load() {
      var q = new URLSearchParams();
      q.set("lang", this.getAttribute("lang") || document.documentElement.lang || "en");
      q.set("theme", this.getAttribute("theme") || "auto");
      this.frame.src = base + "embed/?" + q;
    }
  }
  if (!customElements.get("state-of-the-art-webai")) customElements.define("state-of-the-art-webai", SOA);
})();
