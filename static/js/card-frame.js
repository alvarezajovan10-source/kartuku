/* Dijalankan DI DALAM iframe preview editor.

   Tiga tugas:
   1. membuat elemen ber-data-edit / data-surface / data-frame bisa diklik,
   2. memberi tahu editor elemen mana yang dipilih,
   3. menerapkan perubahan teks, gaya, dan warna tanpa memuat ulang.

   Tidak pernah ikut ke kartu asli — hanya dimuat saat `editing`. */

(function () {
  "use strict";

  var SELECTORS = "[data-edit], [data-frame]";

  var styleRules = {};
  function renderStyleRules() {
    var el = document.getElementById("user-style");
    if (!el) {
      el = document.createElement("style");
      el.id = "user-style";
      document.head.appendChild(el);
    }
    el.textContent = Object.keys(styleRules)
      .filter(function (key) { return styleRules[key]; })
      .map(function (key) {
        var esc = cssEscape(key);
        return '[data-edit="' + esc + '"], [data-frame="' + esc + '"] { ' + styleRules[key] + ' }';
      })
      .join("\n");
  }

  function all(selector) {
    return Array.prototype.slice.call(document.querySelectorAll(selector));
  }

  function keyOf(el) {
    return el.dataset.edit || el.dataset.frame || el.dataset.surface || "";
  }

  function highlight(key) {
    all(SELECTORS).forEach(function (el) {
      el.classList.toggle("is-selected", keyOf(el) === key);
    });
  }

  function send(message) {
    parent.postMessage(Object.assign({ source: "card-frame" }, message), "*");
  }

  function activeScene() {
    var scene = document.querySelector(".scene.active");
    return scene ? scene.id : "";
  }

  /* Dipakai kontrol di dalam kartu yang MENGATUR teks lewat klik, bukan
     lewat mengetik — sejauh ini: memilih tanggal yang dilingkari di kalender
     Valentine Story. Renderer memperbarui tampilannya sendiri supaya klik
     terasa langsung; ini yang membuat pilihannya ikut tersimpan. */
  window.simpanTeks = function (key, value) {
    send({ type: "settext", key: String(key), value: String(value) });
  };

  document.addEventListener("click", function (event) {
    // Elemen terdalam menang: klik nama penerima memilih namanya, bukan
    // seluruh baris ucapan yang membungkusnya.
    var el = event.target.closest(SELECTORS);
    if (!el) return;
    event.preventDefault();
    event.stopPropagation();
    var key = keyOf(el);
    highlight(key);
    send({ type: "select", key: key, scene: activeScene() });
  }, true);

  // Tautan tidak boleh membawa iframe berpindah halaman.
  document.addEventListener("click", function (event) {
    var link = event.target.closest("a[href]");
    if (link) event.preventDefault();
  });

  window.addEventListener("message", function (event) {
    var data = event.data || {};
    if (data.source !== "card-editor") return;

    if (data.type === "style") {
      // Semua gaya user dikumpulkan di SATU stylesheet suntikan. Ini satu
      // jalur, idempoten, dan tidak bisa kalah dari gaya inline mana pun
      // (server tidak memancarkan gaya inline saat mode edit).
      styleRules[data.key] = data.css || "";
      renderStyleRules();
    }

    if (data.type === "colors") {
      var root = document.documentElement;
      Object.keys(data.colors).forEach(function (key) {
        root.style.setProperty("--c-" + key, data.colors[key]);
      });
    }

    if (data.type === "text") {
      all('[data-edit="' + cssEscape(data.key) + '"]').forEach(function (el) {
        // data-no-text: isi elemen bukan teks polos (player lagu, dsb.)
        if (el.hasAttribute("data-no-text")) return;
        // Judul "ransom" dibangun per huruf oleh template — bangun ulang.
        if (el.dataset.text !== undefined && typeof window.buildRansom === "function") {
          el.dataset.text = data.value || el.dataset.placeholder || "";
          window.buildRansom(el);
          return;
        }
        el.textContent = data.value || el.dataset.placeholder || "";
        el.classList.toggle("is-blank", !data.value);
      });
    }

    if (data.type === "scene" && typeof window.show === "function") {
      window.show(data.value);
    }

    // Editor memasang ulang sorotan setelah preview dimuat ulang.
    if (data.type === "select") highlight(data.key);

    if (data.type === "reload") window.location.reload();
  });

  function cssEscape(value) {
    return String(value).replace(/["\\]/g, "\\$&");
  }

  // Kalau URL membawa ?scene=, langsung buka babak itu — inilah yang
  // membuat preview TIDAK balik ke sampul setiap kali dimuat ulang.
  (function () {
    var scene = new URLSearchParams(location.search).get("scene");
    if (!scene) return;
    var target = document.getElementById(scene);
    if (!target || !target.classList.contains("scene")) return;
    document.querySelectorAll(".scene").forEach(function (el) {
      el.classList.toggle("active", el === target);
    });
  })();

  window.addEventListener("load", function () {
    send({
      type: "ready",
      // data-tanpa-tab: babak yang ADA dan bisa dituju window.show(), tapi
      // tidak pantas muncul sebagai tab di editor — mis. layar pemutar foto
      // Sweetflix, yang isinya dibangun JS dan tidak punya satu pun kolom
      // untuk disunting. Tab yang tidak bisa diapa-apakan cuma membingungkan.
      scenes: all(".scene[id]:not([data-tanpa-tab])").map(function (el) { return el.id; }),
    });
  });
})();
