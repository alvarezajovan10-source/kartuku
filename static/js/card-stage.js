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
  var W0 = 390;      // lebar kanonis kartu tegak, harus sama dengan --w0 di CSS
  var K_MAX = 1.15;  // batas pembesaran di layar lebar

  // Kartu mendatar 16:9 punya kanvas kanonisnya sendiri. Bedanya bukan cuma
  // angka: kartu tegak hanya dibatasi lebar layar (tingginya boleh lebih
  // panjang, isinya digulir), sedangkan kartu mendatar harus muat UTUH —
  // memotong tingginya berarti memotong isi babak. Jadi skalanya dibatasi
  // dari dua sisi sekaligus.
  var W0_LEBAR = 960;
  var H0_LEBAR = 540;

  var root = document.documentElement;

  function fit() {
    // clientWidth sudah tidak termasuk scrollbar, jadi kartu tidak akan
    // meluber horizontal di desktop yang scrollbar-nya memakan tempat.
    var w = root.clientWidth || window.innerWidth || W0;
    if (root.dataset.stage === "lebar") {
      // TANPA K_MAX. Batas 1,15 itu masuk akal untuk kartu tegak — kartu
      // selebar HP tidak perlu dibesarkan sampai memenuhi layar laptop.
      // Untuk kartu mendatar justru kebalikannya: bentuknya sudah sama
      // dengan layar, jadi dibatasi 1,15 ia tampil sebagai kotak kecil di
      // tengah dan penerima harus memperbesar sendiri.
      var h = root.clientHeight || window.innerHeight || H0_LEBAR;
      root.style.setProperty("--k", Math.min(w / W0_LEBAR, h / H0_LEBAR));
      return;
    }
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

    var terakhir = -1;
    function syncHeight() {
      var k = parseFloat(getComputedStyle(root).getPropertyValue("--k")) || 1;
      var tinggi = Math.round(stage.offsetHeight * k);
      // Berhenti kalau tidak berubah berarti. Tanpa penjaga ini, satu
      // kesalahan tata letak saja bisa membuat ukur → ubah → ukur berputar
      // tanpa henti dan kartunya menyusut habis (lihat catatan align-items
      // di card-stage.css).
      if (Math.abs(tinggi - terakhir) < 2) return;
      terakhir = tinggi;
      wrap.style.setProperty("--wrap-h", tinggi + "px");
    }
    syncHeight();
    window.addEventListener("resize", syncHeight);
    if (window.ResizeObserver) new ResizeObserver(syncHeight).observe(stage);
    // Foto dan font yang selesai dimuat mengubah tinggi setelah DOM siap.
    window.addEventListener("load", syncHeight);
  });
})();
