/* Penskala kanvas kartu — pasangan static/css/card-stage.css.
 *
 * Kartu ditata pada lebar tetap 390px, lalu diskalakan agar pas di layar.
 * Skrip ini hanya menghitung faktor skalanya; tata letaknya sendiri tidak
 * pernah berubah, jadi pemenggalan baris sama di perangkat apa pun.
 *
 * Dimuat SINKRON di <head> (tanpa defer) supaya --k sudah benar sebelum
 * halaman digambar pertama kali — kalau tidak, kartu berkedip dari ukuran
 * salah ke ukuran benar.
 */
(function () {
  var W0 = 390;      // lebar kanonis, harus sama dengan --w0 di CSS
  var K_MAX = 1.15;  // batas pembesaran di layar lebar

  var root = document.documentElement;

  function fit() {
    // clientWidth sudah tidak termasuk scrollbar, jadi kartu tidak akan
    // meluber horizontal di desktop yang scrollbar-nya memakan tempat.
    var w = root.clientWidth || window.innerWidth || W0;
    root.style.setProperty("--k", Math.min(w / W0, K_MAX));
  }

  fit();
  window.addEventListener("resize", fit);
  window.addEventListener("orientationchange", fit);

  // Mode flow: tinggi pembungkus harus mengikuti tinggi stage x skala.
  // offsetHeight mengabaikan transform — justru itu yang dibutuhkan.
  document.addEventListener("DOMContentLoaded", function () {
    if (root.dataset.stage !== "flow") return;
    var stage = document.getElementById("card-stage");
    var wrap = document.getElementById("card-viewport");
    if (!stage || !wrap) return;

    function syncHeight() {
      var k = parseFloat(getComputedStyle(root).getPropertyValue("--k")) || 1;
      wrap.style.setProperty("--wrap-h", stage.offsetHeight * k + "px");
    }
    syncHeight();
    window.addEventListener("resize", syncHeight);
    if (window.ResizeObserver) new ResizeObserver(syncHeight).observe(stage);
    // Foto dan font yang selesai dimuat mengubah tinggi setelah DOM siap.
    window.addEventListener("load", syncHeight);
  });
})();
