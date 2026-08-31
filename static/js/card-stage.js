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

  // Kartu "buku": halaman A4 tegak yang dibalik satu per satu. Sama seperti
  // kartu mendatar, ia harus muat UTUH — halaman majalah yang terpotong
  // bawahnya bukan sekadar kurang enak dilihat, isinya benar-benar hilang.
  // Bedanya, tinggi layar yang dipakai dikurangi dulu sebesar tempat tombol
  // navigasinya, supaya tombol itu tidak duduk di atas halaman.
  var W0_BUKU = 390;
  var H0_BUKU = 551.6;   // 390 x (842,25/595,5) — perbandingan A4
  var K_MAX_BUKU = 1.6;  // di atas ini pelat halamannya mulai terlihat lunak
  var SISA_NAV = 54;

  var root = document.documentElement;

  function fit() {
    // clientWidth sudah tidak termasuk scrollbar, jadi kartu tidak akan
    // meluber horizontal di desktop yang scrollbar-nya memakan tempat.
    var w = root.clientWidth || window.innerWidth || W0;
    // Tinggi yang BENAR-BENAR terlihat. Di Safari iPhone, bilah alamat
    // memakan tinggi tapi tidak mengubah clientHeight, jadi kartu dihitung
    // dari bidang yang lebih besar daripada yang dilihat penerima dan
    // bagian bawahnya bersembunyi di balik bilah.
    var vv = window.visualViewport;
    var hNyata = (vv && vv.height) || root.clientHeight || window.innerHeight;
    if (root.dataset.stage === "lebar") {
      // TANPA K_MAX. Batas 1,15 itu masuk akal untuk kartu tegak — kartu
      // selebar HP tidak perlu dibesarkan sampai memenuhi layar laptop.
      // Untuk kartu mendatar justru kebalikannya: bentuknya sudah sama
      // dengan layar, jadi dibatasi 1,15 ia tampil sebagai kotak kecil di
      // tengah dan penerima harus memperbesar sendiri.
      var h = hNyata || H0_LEBAR;
      root.style.setProperty("--k", Math.min(w / W0_LEBAR, h / H0_LEBAR));
      return;
    }
    if (root.dataset.stage === "buku") {
      var hb = (hNyata || H0_BUKU) - SISA_NAV;
      root.style.setProperty(
        "--k", Math.min(w / W0_BUKU, hb / H0_BUKU, K_MAX_BUKU)
      );
      return;
    }
    root.style.setProperty("--k", Math.min(w / W0, K_MAX));
  }

  fit();
  window.addEventListener("resize", fit);
  window.addEventListener("orientationchange", fit);
  // Bilah alamat Safari yang menyusut TIDAK memicu resize pada window —
  // yang terpicu cuma visualViewport. Tanpa pendengar ini, ruang yang baru
  // dilepas Safari dibiarkan kosong dan kartunya tetap kecil.
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", fit);
    window.visualViewport.addEventListener("scroll", fit);
  }

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
