/* Galeri halaman produk: strip thumbnail + panah, seperti listing rujukan.
 *
 * Slide nomor 0 BUKAN gambar melainkan iframe kartu yang hidup. Karena itu
 * catatan "sapu untuk membalik halaman" di bawahnya cuma boleh tampil saat
 * slide itu yang terbuka — di atas potret diam, kalimat itu berbohong.
 */
(function () {
  var galeri = document.querySelector(".lst-galeri");
  if (!galeri) return;

  var thumb = [].slice.call(galeri.querySelectorAll(".lst-thumb"));
  var slide = [].slice.call(galeri.querySelectorAll(".lst-slide"));
  var kini = galeri.querySelector(".lst-kini");
  var catatan = document.querySelector("[data-catatan-hidup]");
  var i = 0;

  function tampil(n) {
    i = (n + slide.length) % slide.length;
    slide.forEach(function (el, k) { el.classList.toggle("is-on", k === i); });
    thumb.forEach(function (el, k) {
      el.classList.toggle("is-on", k === i);
      el.setAttribute("aria-selected", k === i ? "true" : "false");
    });
    if (kini) kini.textContent = String(i + 1);
    if (catatan) catatan.style.visibility = i === 0 ? "visible" : "hidden";
    // Thumbnail yang dipilih lewat panah bisa berada di luar strip yang
    // tergulir — tanpa ini penanda aktifnya tidak pernah terlihat.
    if (thumb[i]) thumb[i].scrollIntoView({ block: "nearest", inline: "nearest" });
  }

  thumb.forEach(function (el) {
    el.addEventListener("click", function () { tampil(parseInt(el.dataset.i, 10)); });
  });
  var prev = galeri.querySelector(".lst-prev");
  var next = galeri.querySelector(".lst-next");
  if (prev) prev.addEventListener("click", function () { tampil(i - 1); });
  if (next) next.addEventListener("click", function () { tampil(i + 1); });

  /* Panah kiri/kanan keyboard hanya saat fokus ada DI DALAM galeri. Kalau
     dipasang ke seluruh dokumen, pembeli yang sedang mengetik di kolom cari
     akan ikut menggeser galerinya. */
  galeri.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") { tampil(i - 1); e.preventDefault(); }
    if (e.key === "ArrowRight") { tampil(i + 1); e.preventDefault(); }
  });

  tampil(0);
})();
