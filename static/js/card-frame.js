/* Dijalankan DI DALAM iframe preview editor.

   Tugasnya tiga:
   1. menandai elemen ber-atribut data-edit sebagai bisa diklik,
   2. memberitahu halaman editor elemen mana yang dipilih,
   3. menerapkan perubahan teks & gaya dari editor tanpa memuat ulang.

   Tidak pernah ikut terkirim ke kartu asli — hanya dimuat saat `editing`. */

(function () {
  "use strict";

  var selected = null;

  function targets() {
    return Array.prototype.slice.call(document.querySelectorAll("[data-edit]"));
  }

  function highlight(key) {
    targets().forEach(function (el) {
      el.classList.toggle("is-selected", el.dataset.edit === key);
    });
  }

  function send(message) {
    parent.postMessage(Object.assign({ source: "card-frame" }, message), "*");
  }

  function select(key, el) {
    selected = key;
    highlight(key);
    var rect = el.getBoundingClientRect();
    send({ type: "select", key: key, top: rect.top, height: rect.height });
  }

  document.addEventListener("click", function (event) {
    var el = event.target.closest("[data-edit]");
    if (!el) return;
    // Di dalam editor, klik dipakai untuk memilih — bukan menjalankan kartu.
    event.preventDefault();
    event.stopPropagation();
    select(el.dataset.edit, el);
  }, true);

  // Tombol/animasi kartu tetap boleh jalan, tapi tautan tidak boleh membawa
  // iframe berpindah halaman.
  document.addEventListener("click", function (event) {
    var link = event.target.closest("a[href]");
    if (link) event.preventDefault();
  });

  window.addEventListener("message", function (event) {
    var data = event.data || {};
    if (data.source !== "card-editor") return;

    if (data.type === "style") {
      var root = document.getElementById("kv-root") || document.documentElement;
      Object.keys(data.vars).forEach(function (name) {
        root.style.setProperty(name, data.vars[name]);
      });
      if (data.vars["--bg"]) document.body.style.background = data.vars["--bg"];
    }

    if (data.type === "colors") {
      var el = document.documentElement;
      Object.keys(data.colors).forEach(function (key) {
        el.style.setProperty("--c-" + key, data.colors[key]);
      });
    }

    if (data.type === "text") {
      document.querySelectorAll('[data-edit="' + data.key + '"]').forEach(function (el) {
        var prefix = el.dataset.prefix || "";
        el.textContent = data.value ? prefix + data.value : el.dataset.placeholder || "";
        el.classList.toggle("is-blank", !data.value);
      });
    }

    if (data.type === "shape") {
      document.querySelectorAll("[data-photos]").forEach(function (el) {
        el.className = el.className.replace(/\bshape-\S+/g, "").trim();
        el.classList.add("shape-" + data.value);
      });
    }

    if (data.type === "scene") {
      // Template berbabak (mis. Amplop Merah) — pindah ke babak tertentu.
      if (typeof window.show === "function") window.show(data.value);
    }

    if (data.type === "reload") {
      window.location.reload();
    }
  });

  // Beri tahu editor daftar elemen & babak yang tersedia begitu siap.
  window.addEventListener("load", function () {
    send({
      type: "ready",
      keys: targets().map(function (el) { return el.dataset.edit; }),
      scenes: Array.prototype.map.call(
        document.querySelectorAll(".scene[id]"),
        function (el) { return el.id; }
      ),
    });
  });
})();
