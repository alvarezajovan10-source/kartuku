/* Tutorial berlangkah di layar editor kartu.
 *
 * Alasannya nyata: orang mengerti editor ini di laptop tapi tersesat di HP.
 * Di HP panel kontrol berada DI BAWAH pratinjau, jadi saat kartu pertama
 * terbuka yang terlihat hanya kartunya — kolom ganti teks, tombol pilih foto,
 * dan kolom lagu semuanya di luar layar. Yang paling sering tidak ditemukan
 * adalah pengganti halaman.
 *
 * Dua aturan yang membentuk berkas ini:
 *
 *   1. Sorotnya menunjuk KOTAK yang sebenarnya dipakai — kolom teksnya sendiri,
 *      tombol pilih fotonya sendiri — bukan sekadar panel besar tempat semua
 *      itu berada. Menunjuk seluruh panel sama saja dengan tidak menunjuk.
 *
 *   2. Kotak teks dan tombol foto baru ADA setelah pengguna mengetuk sesuatu di
 *      kartu. Jadi langkahnya menunggu: "ketuk tulisan di kartu" bertahan
 *      sampai kolomnya benar-benar muncul, baru maju sendiri dan menyorotnya.
 *      Ini yang membuatnya terasa seperti tutorial permainan, bukan daftar
 *      instruksi yang dibaca lalu dilupakan.
 *
 * Tidak memakai pustaka apa pun dan tidak menyentuh Alpine — kalau berkas ini
 * gagal dimuat, editornya tetap berjalan seperti biasa.
 */
(function () {
  "use strict";

  var FOTO = 'label[for="pick-photo"], label[for="pick-gallery"]';

  var LANGKAH = [
    {
      pilih: ".ed-scenes",
      opsional: true,
      judul: "Kartu ini punya beberapa halaman",
      teks: "Ketuk nomor halaman untuk berpindah. Tiap halaman diisi " +
            "sendiri-sendiri — periksa semuanya sebelum membuat link.",
    },
    {
      pilih: ".ed-stage",
      tunggu: ".ed-head .ed-input",
      judul: "Ketuk tulisan di kartu",
      teks: "Coba ketuk salah satu tulisan di kartu sekarang. Tutorial ini " +
            "menunggu sampai kamu mengetuknya.",
    },
    {
      pilih: ".ed-head .ed-input",
      opsional: true,
      judul: "Ini kotak untuk mengganti tulisannya",
      teks: "Hapus isinya, lalu ketik kalimatmu sendiri. Perubahannya langsung " +
            "terlihat di kartu, dan tersimpan otomatis.",
    },
    {
      pilih: ".ed-stage",
      tunggu: FOTO,
      lewatiBoleh: true,
      judul: "Sekarang ketuk kotak foto di kartu",
      teks: "Kalau kartu ini punya tempat foto, ketuk kotaknya. Kalau tidak " +
            "ada, tekan Lanjut saja.",
    },
    {
      pilih: FOTO,
      opsional: true,
      judul: "Tombol ini untuk memilih foto",
      teks: "Ketuk, lalu pilih foto dari galeri HP-mu. Setelah terpilih kamu " +
            "bisa menggeser dan memotongnya.",
    },
    {
      pilih: ".ed-song .ed-input",
      opsional: true,
      judul: "Kotak ini untuk lagu",
      teks: "Tempel link YouTube di sini. Lagunya berbunyi saat penerima " +
            "membuka kartumu. Boleh dikosongkan.",
    },
    {
      pilih: ".ed-submit",
      judul: "Terakhir: buat link kartunya",
      teks: "Kalau semua halaman sudah beres, tekan tombol ini. Kamu akan " +
            "dapat link dan QR untuk dibagikan.",
    },
  ];

  var tirai, sorot, kotak, ke = 0, pengintai = null;

  function terlihat(el) {
    if (!el) return false;
    var r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) return false;
    var g = window.getComputedStyle(el);
    return g.display !== "none" && g.visibility !== "hidden";
  }

  /* Satu pemilih bisa cocok ke beberapa elemen yang saling bergantian — kolom
     teks punya versi <textarea> dan <input>, dan hanya salah satunya tampil.
     Yang dipakai selalu yang benar-benar terlihat. */
  function cari(pemilih) {
    var daftar = document.querySelectorAll(pemilih);
    for (var i = 0; i < daftar.length; i++) {
      if (terlihat(daftar[i])) return daftar[i];
    }
    return null;
  }

  function hentikanIntai() {
    if (pengintai) { clearInterval(pengintai); pengintai = null; }
  }

  function bikinTombolUlang() {
    if (document.querySelector(".tut-ulang")) return;
    var b = document.createElement("button");
    b.type = "button";
    b.className = "tut-ulang";
    b.textContent = "?";
    b.title = "Lihat tutorial lagi";
    b.setAttribute("aria-label", "Lihat tutorial lagi");
    b.addEventListener("click", mulai);
    document.body.appendChild(b);
  }

  function tutup() {
    hentikanIntai();
    if (tirai) tirai.remove();
    if (sorot) sorot.remove();
    if (kotak) kotak.remove();
    tirai = sorot = kotak = null;
    document.removeEventListener("keydown", padaTombol);
    window.removeEventListener("resize", posisikan);
    window.removeEventListener("scroll", posisikan, true);
    bikinTombolUlang();
  }

  function padaTombol(e) {
    if (e.key === "Escape") tutup();
    else if (e.key === "ArrowRight") maju();
    else if (e.key === "ArrowLeft") mundur();
  }

  function maju() {
    if (ke >= LANGKAH.length - 1) return tutup();
    ke++;
    tampilkan();
  }

  function mundur() {
    if (ke <= 0) return;
    ke--;
    tampilkan();
  }

  /* Berapa langkah yang benar-benar akan dilalui, untuk penomoran "x dari y".
     Dihitung ulang tiap kali karena langkah opsional muncul dan hilang
     mengikuti apa yang sedang dipilih pengguna. */
  function totalLangkah() {
    var n = 0;
    for (var i = 0; i < LANGKAH.length; i++) {
      if (!LANGKAH[i].opsional || cari(LANGKAH[i].pilih)) n++;
    }
    return n;
  }

  function nomorSekarang() {
    var n = 0;
    for (var i = 0; i <= ke; i++) {
      if (!LANGKAH[i].opsional || cari(LANGKAH[i].pilih)) n++;
    }
    return n;
  }

  function tampilkan() {
    hentikanIntai();

    // Langkah opsional yang sasarannya belum ada dilewati — belum tentu
    // selamanya tidak ada, tapi saat ini tidak ada yang bisa ditunjuk.
    var batas = 0;
    while (ke < LANGKAH.length && LANGKAH[ke].opsional && !cari(LANGKAH[ke].pilih)) {
      ke++;
      if (++batas > LANGKAH.length) break;
    }
    if (ke >= LANGKAH.length) return tutup();

    var l = LANGKAH[ke];
    kotak.querySelector(".tut-nomor").textContent =
      "Langkah " + nomorSekarang() + " dari " + totalLangkah();
    kotak.querySelector(".tut-judul").textContent = l.judul;
    kotak.querySelector(".tut-teks").textContent = l.teks;
    kotak.querySelector(".tut-mundur").style.display = ke === 0 ? "none" : "";
    kotak.querySelector(".tut-lanjut").textContent =
      ke === LANGKAH.length - 1 ? "Selesai" : "Lanjut";

    posisikan();

    // Langkah yang menunggu perbuatan: begitu kotak yang dijanjikan muncul,
    // tutorial maju sendiri dan langsung menyorotnya.
    if (l.tunggu) {
      pengintai = setInterval(function () {
        if (cari(l.tunggu)) { hentikanIntai(); maju(); }
      }, 300);
    }
  }

  function posisikan() {
    if (!kotak) return;
    var l = LANGKAH[ke];
    var el = l && cari(l.pilih);

    if (el) {
      // Sasaran digulir ke tengah layar dulu — di HP panelnya ada di bawah
      // pratinjau, dan menyorot sesuatu di luar layar tidak menolong siapa pun.
      var r0 = el.getBoundingClientRect();
      if (r0.top < 60 || r0.bottom > window.innerHeight - 60) {
        el.scrollIntoView({ block: "center", behavior: "smooth" });
      }
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
      var bawah = r.bottom + jarak;
      atas = (bawah + tinggi <= window.innerHeight - 8) ? bawah : r.top - tinggi - jarak;
      kiri = r.left + (r.width - lebar) / 2;
    }

    // Dijaga tetap utuh di layar: kotak yang terpotong lebih buruk daripada
    // kotak yang tidak persis menempel sasarannya.
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
    kotak.querySelector(".tut-lewati").addEventListener("click", tutup);
    kotak.querySelector(".tut-mundur").addEventListener("click", mundur);
    kotak.querySelector(".tut-lanjut").addEventListener("click", maju);
    document.body.appendChild(kotak);
  }

  function mulai() {
    if (kotak) return;
    ke = 0;

    tirai = document.createElement("div");
    tirai.className = "tut-tirai";
    // Tirai TIDAK menutup tutorial saat diketuk: langkah yang menunggu
    // perbuatan mengharuskan pengguna mengetuk kartu di belakangnya, dan
    // ketukan yang meleset sedikit dulu membuat tutorialnya hilang begitu saja.
    document.body.appendChild(tirai);

    sorot = document.createElement("div");
    sorot.className = "tut-sorot";
    document.body.appendChild(sorot);

    bangunKotak();
    tampilkan();
    kotak.querySelector(".tut-lanjut").focus();
    document.addEventListener("keydown", padaTombol);
    window.addEventListener("resize", posisikan);
    window.addEventListener("scroll", posisikan, true);
  }

  /* Editor digambar Alpine, jadi elemennya belum ada saat skrip ini jalan.
     Ditunggu sampai pratinjaunya terlihat, dengan batas waktu supaya tidak
     menunggu selamanya kalau editornya gagal dimuat. */
  function tunggu() {
    var mulaiTunggu = Date.now();
    var jeda = setInterval(function () {
      if (terlihat(document.querySelector(".ed-stage"))) {
        clearInterval(jeda);
        setTimeout(mulai, 400);
      } else if (Date.now() - mulaiTunggu > 12000) {
        clearInterval(jeda);
        bikinTombolUlang();
      }
    }, 200);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", tunggu);
  } else {
    tunggu();
  }
})();
