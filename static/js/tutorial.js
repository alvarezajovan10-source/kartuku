/* Tutorial berlangkah di layar editor kartu.
 *
 * Alasannya nyata, bukan hiasan: orang mengerti editor ini di laptop tapi
 * tersesat di HP. Di HP panel kontrol berada DI BAWAH pratinjau, jadi saat
 * kartu pertama terbuka yang terlihat hanya kartunya — tombol ganti teks,
 * pilih foto, dan tempel lagu semuanya di luar layar. Yang paling sering
 * tidak ditemukan adalah pengganti halaman.
 *
 * Cara kerjanya: satu lubang sorot di atas layar gelap, plus kotak penjelasan
 * yang menempel di dekatnya. Tidak memakai pustaka apa pun, dan tidak
 * menyentuh Alpine — kalau berkas ini gagal dimuat, editornya tetap berjalan
 * seperti biasa.
 */
(function () {
  "use strict";

  var KUNCI = "kartuku-tutorial-v1";
  var LANGKAH = [
    {
      pilih: ".ed-scenes",
      judul: "Kartu ini punya beberapa halaman",
      teks: "Ketuk nomor halaman untuk berpindah. Tiap halaman diisi " +
            "sendiri-sendiri, jadi jangan lupa memeriksa semuanya sebelum " +
            "membuat link.",
    },
    {
      pilih: ".ed-stage",
      judul: "Ketuk apa pun di kartu untuk mengubahnya",
      teks: "Tulisan, foto, semuanya bisa diketuk langsung di sini. Yang " +
            "kamu ketuk itulah yang akan diubah.",
    },
    {
      pilih: ".ed-panel",
      judul: "Kotak pengaturannya muncul di sini",
      teks: "Di HP, bagian ini ada DI BAWAH kartu — geser layar ke bawah " +
            "kalau tidak terlihat. Setelah mengetuk tulisan, kolom untuk " +
            "mengganti katanya muncul di sini. Kalau yang diketuk foto, " +
            "tombol pilih foto yang muncul.",
    },
    {
      pilih: ".ed-song",
      judul: "Tambahkan lagu (boleh dilewati)",
      teks: "Tempel link YouTube di kolom ini. Lagunya akan berbunyi saat " +
            "penerima membuka kartumu.",
    },
    {
      pilih: ".ed-submit",
      judul: "Terakhir: buat link kartunya",
      teks: "Kalau semua halaman sudah beres, tekan tombol ini. Kamu akan " +
            "dapat link dan QR yang bisa dibagikan ke orang yang dituju.",
    },
  ];

  var tirai, sorot, kotak, langkahAktif = 0, jalan = [];

  function terlihat(el) {
    if (!el) return false;
    var r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    var g = window.getComputedStyle(el);
    return g.display !== "none" && g.visibility !== "hidden";
  }

  function sudahPernah() {
    try { return window.localStorage.getItem(KUNCI) === "1"; } catch (e) { return false; }
  }

  function tandaiSelesai() {
    try { window.localStorage.setItem(KUNCI, "1"); } catch (e) { /* mode privat */ }
  }

  function bikinTombolUlang() {
    if (document.querySelector(".tut-ulang")) return;
    var b = document.createElement("button");
    b.type = "button";
    b.className = "tut-ulang";
    b.textContent = "?";
    b.title = "Lihat tutorial lagi";
    b.setAttribute("aria-label", "Lihat tutorial lagi");
    b.addEventListener("click", function () { mulai(true); });
    document.body.appendChild(b);
  }

  function tutup(selesai) {
    if (tirai) tirai.remove();
    if (sorot) sorot.remove();
    if (kotak) kotak.remove();
    tirai = sorot = kotak = null;
    document.removeEventListener("keydown", padaTombol);
    window.removeEventListener("resize", gambarUlang);
    window.removeEventListener("scroll", gambarUlang, true);
    if (selesai) tandaiSelesai();
    bikinTombolUlang();
  }

  function padaTombol(e) {
    if (e.key === "Escape") tutup(true);
    else if (e.key === "ArrowRight" || e.key === "Enter") maju();
    else if (e.key === "ArrowLeft") mundur();
  }

  function maju() {
    if (langkahAktif >= jalan.length - 1) tutup(true);
    else { langkahAktif++; gambarUlang(); }
  }

  function mundur() {
    if (langkahAktif > 0) { langkahAktif--; gambarUlang(); }
  }

  function gambarUlang() {
    var l = jalan[langkahAktif];
    if (!l) return tutup(true);
    var el = document.querySelector(l.pilih);

    // Sasaran bisa hilang di tengah jalan — panel berubah mengikuti apa yang
    // sedang dipilih pengguna. Kalau hilang, langkahnya tetap ditampilkan
    // tanpa sorotan, bukan dibiarkan menunjuk tempat kosong.
    if (terlihat(el)) {
      var r = el.getBoundingClientRect();
      var pad = 6;
      sorot.classList.remove("is-kosong");
      sorot.style.top = (r.top - pad) + "px";
      sorot.style.left = (r.left - pad) + "px";
      sorot.style.width = (r.width + pad * 2) + "px";
      sorot.style.height = (r.height + pad * 2) + "px";
      taruhKotak(r);
    } else {
      sorot.classList.add("is-kosong");
      sorot.style.top = "50%";
      sorot.style.left = "50%";
      taruhKotak(null);
    }

    kotak.querySelector(".tut-nomor").textContent =
      "Langkah " + (langkahAktif + 1) + " dari " + jalan.length;
    kotak.querySelector(".tut-judul").textContent = l.judul;
    kotak.querySelector(".tut-teks").textContent = l.teks;
    kotak.querySelector(".tut-mundur").style.display = langkahAktif === 0 ? "none" : "";
    kotak.querySelector(".tut-lanjut").textContent =
      langkahAktif === jalan.length - 1 ? "Selesai" : "Lanjut";
  }

  function taruhKotak(r) {
    var lebar = kotak.offsetWidth || 320;
    var tinggi = kotak.offsetHeight || 190;
    var jarak = 14;
    var atas, kiri;

    if (!r) {
      atas = (window.innerHeight - tinggi) / 2;
      kiri = (window.innerWidth - lebar) / 2;
    } else {
      // Ditaruh di bawah sasaran kalau muat; kalau tidak, di atasnya. Ini yang
      // membuatnya tetap terbaca di layar HP yang pendek.
      var bawah = r.bottom + jarak;
      atas = (bawah + tinggi <= window.innerHeight - 8) ? bawah : r.top - tinggi - jarak;
      kiri = r.left + (r.width - lebar) / 2;
    }

    // Dijaga tetap di dalam layar — kotak yang setengah terpotong lebih buruk
    // daripada kotak yang tidak persis menempel sasaran.
    atas = Math.max(8, Math.min(atas, window.innerHeight - tinggi - 8));
    kiri = Math.max(8, Math.min(kiri, window.innerWidth - lebar - 8));
    kotak.style.top = atas + "px";
    kotak.style.left = kiri + "px";
  }

  function bangunKotak() {
    kotak = document.createElement("div");
    kotak.className = "tut-kotak";
    kotak.setAttribute("role", "dialog");
    kotak.setAttribute("aria-modal", "true");
    kotak.setAttribute("aria-label", "Tutorial editor kartu");
    kotak.innerHTML =
      '<p class="tut-nomor"></p>' +
      '<h2 class="tut-judul"></h2>' +
      '<p class="tut-teks"></p>' +
      '<div class="tut-aksi">' +
      '<button type="button" class="tut-lewati">Lewati</button>' +
      '<button type="button" class="tut-mundur">Kembali</button>' +
      '<button type="button" class="tut-lanjut">Lanjut</button>' +
      "</div>";
    kotak.querySelector(".tut-lewati").addEventListener("click", function () { tutup(true); });
    kotak.querySelector(".tut-mundur").addEventListener("click", mundur);
    kotak.querySelector(".tut-lanjut").addEventListener("click", maju);
    document.body.appendChild(kotak);
  }

  function mulai(paksa) {
    if (!paksa && sudahPernah()) { bikinTombolUlang(); return; }
    if (kotak) return;

    // Langkah yang sasarannya tidak ada dibuang — kartu satu halaman tidak
    // perlu diajari cara berpindah halaman.
    jalan = LANGKAH.filter(function (l) {
      return terlihat(document.querySelector(l.pilih));
    });
    if (!jalan.length) return;

    langkahAktif = 0;
    tirai = document.createElement("div");
    tirai.className = "tut-tirai";
    tirai.addEventListener("click", function () { tutup(true); });
    document.body.appendChild(tirai);

    sorot = document.createElement("div");
    sorot.className = "tut-sorot";
    document.body.appendChild(sorot);

    bangunKotak();
    gambarUlang();
    kotak.querySelector(".tut-lanjut").focus();
    document.addEventListener("keydown", padaTombol);
    window.addEventListener("resize", gambarUlang);
    window.addEventListener("scroll", gambarUlang, true);
  }

  /* Editor digambar Alpine, jadi elemennya belum ada saat skrip ini jalan.
     Ditunggu sampai pratinjaunya benar-benar terlihat, dengan batas waktu
     supaya tidak menunggu selamanya kalau editornya gagal dimuat. */
  function tunggu() {
    var mulaiTunggu = Date.now();
    var jeda = setInterval(function () {
      if (terlihat(document.querySelector(".ed-stage"))) {
        clearInterval(jeda);
        setTimeout(function () { mulai(false); }, 350);
      } else if (Date.now() - mulaiTunggu > 12000) {
        clearInterval(jeda);
      }
    }, 200);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", tunggu);
  } else {
    tunggu();
  }
})();
