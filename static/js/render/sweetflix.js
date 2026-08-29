/* SWEETFLIX — perpindahan babak, animasi pembuka, pemutar foto, dan pemotong
   teks panjang.

   Kontrak renderer berbabak (lihat static/js/card-frame.js):
   - tiap babak adalah <section class="scene"> ber-id
   - babak yang sedang tampil punya class .active
   - window.show(id) WAJIB ada supaya editor bisa melompat antar babak
*/
(function () {
  "use strict";

  var babak = [].slice.call(document.querySelectorAll(".scene"));
  var menyunting = document.body.classList.contains("is-editing");
  var terakhirHome = "home_a";

  /* Irama kartu. Angkanya sengaja dikumpulkan di satu tempat: pemilik situs
     meminta semuanya lambat dan sinematik, dan menyebar angka ke sepuluh
     tempat membuat satu di antaranya pasti tertinggal. --pudar di CSS harus
     sepadan dengan PUDAR di sini. */
  var FOTO_LAMA = 1700;    // satu foto bertahan di layar saat diputar
  var PUDAR = 900;         // sama dengan --pudar di sweetflix.css

  /* Berapa baris sebelum teks dipotong. Beda karena ruangnya beda: ucapan di
     beranda berbagi tempat dengan judul dan tombol, sedangkan cerita di layar
     detail hampir memiliki seluruh lebar layar. */
  var BARIS = [
    [".hero-desk", 3],
  ];

  function show(id) {
    var ada = false;
    /* Panel detail mengambang DI ATAS berandanya — beranda dibiarkan aktif,
       kalau tidak panelnya cuma melayang di atas hitam dan kehilangan seluruh
       maksudnya sebagai lapisan. */
    var tetap = [id];
    var m = /^detail_([a-z])$/.exec(id);
    if (m) tetap.push("home_" + m[1]);

    babak.forEach(function (s) {
      var aktif = tetap.indexOf(s.id) >= 0;
      s.classList.toggle("active", aktif);
      if (s.id === id) ada = true;
      if (aktif) return;
      // Babak yang ditinggalkan dikembalikan tertutup — kalau tidak, ia masih
      // dalam mode baca (baris poster mundur) waktu penerima kembali ke sana.
      s.classList.remove("baca");
      [].forEach.call(s.querySelectorAll(".hero-desk.terbuka"), function (d) {
        d.classList.remove("terbuka");
      });
      [].forEach.call(s.querySelectorAll(".selengkapnya"), function (t) {
        t.textContent = "selengkapnya";
      });
    });
    if (!ada) return false;
    if (id.indexOf("home_") === 0) terakhirHome = id;
    if (id !== "warp") hentikanPemutar();
    // Teks hanya bisa diukur setelah babaknya terlihat: elemen tersembunyi
    // tingginya nol, jadi memotongnya lebih awal selalu salah.
    perbaruiPotong();
    return true;
  }
  window.show = show;

  /* ── Pemotong teks panjang ─────────────────────────────────────────────── */
  /* data-aksi menunjuk wadah tempat tombol "selengkapnya" duduk — di beranda
     ia sejajar dengan tombol Putar, bukan menempel di bawah kalimatnya. */
  function wadahTombol(el) {
    var sel = el.getAttribute("data-aksi");
    if (!sel) return null;
    var layar = el.closest(".layar");
    return layar ? layar.querySelector(sel) : null;
  }

  function potongSatu(el, baris) {
    var wadah = wadahTombol(el);
    var induk = wadah || el.parentNode;
    var tombol = induk.querySelector(".selengkapnya");
    var terbuka = el.classList.contains("terbuka");
    el.classList.remove("terpotong");
    el.style.setProperty("--baris", baris);
    el.classList.add("terpotong");

    if (el.scrollHeight <= el.clientHeight + 1 && !terbuka) {
      el.classList.remove("terpotong");
      if (tombol) tombol.remove();
      return;
    }
    if (terbuka) el.classList.add("terbuka");
    if (tombol) return;

    tombol = document.createElement("button");
    tombol.type = "button";
    tombol.className = "selengkapnya";
    tombol.textContent = "selengkapnya";
    tombol.addEventListener("click", function (ev) {
      ev.stopPropagation();
      var buka = el.classList.toggle("terbuka");
      tombol.textContent = buka ? "lebih sedikit" : "selengkapnya";
      // Membaca butuh tempat: blok tulisan naik dan baris poster mundur.
      var layar = el.closest(".layar");
      if (layar) layar.classList.toggle("baca", buka && el.classList.contains("hero-desk"));
    });
    if (wadah) wadah.appendChild(tombol);
    else induk.insertBefore(tombol, el.nextSibling);
  }

  function perbaruiPotong() {
    BARIS.forEach(function (pasang) {
      [].forEach.call(document.querySelectorAll(".scene.active " + pasang[0]), function (el) {
        potongSatu(el, pasang[1]);
      });
    });
  }

  /* ── Nama penerima ─────────────────────────────────────────────────────
     Diketik PENERIMA di halaman pertama, lalu dipakai sebagai nama profil dan
     sebagai "Pemeran" di panel cerita. Disimpan per-kartu di localStorage
     supaya ia tidak ditanya lagi besok — pola yang sama dipakai valentine.js
     untuk preferensi suara. */
  var KUNCI_NAMA = "sweetflix-nama:" + location.pathname;

  function pakaiNama(nama) {
    nama = String(nama == null ? "" : nama).trim().slice(0, 24);
    if (!nama || menyunting) return;
    [].forEach.call(document.querySelectorAll("[data-nama-tamu]"), function (el) {
      // textContent, JANGAN innerHTML: yang mengetik ini penerima, dan tanda
      // kurung siku di dalamnya akan merusak tata letak kartunya sendiri.
      el.textContent = nama;
    });
  }

  var kotakNama = document.getElementById("namaTamu");
  var tblLanjut = document.getElementById("tblLanjut");

  if (!menyunting) {
    try {
      var tersimpan = localStorage.getItem(KUNCI_NAMA);
      if (tersimpan) { if (kotakNama) kotakNama.value = tersimpan; pakaiNama(tersimpan); }
    } catch (e) { /* localStorage ditutup peramban — kartunya tetap jalan */ }
  }

  function lanjut() {
    var nama = kotakNama ? kotakNama.value : "";
    if (nama && !menyunting) {
      pakaiNama(nama);
      try { localStorage.setItem(KUNCI_NAMA, nama.trim().slice(0, 24)); } catch (e) {}
    }
    show("profil");
  }

  if (tblLanjut) tblLanjut.addEventListener("click", lanjut);
  // Enter di kotak nama sama dengan menekan Continue.
  if (kotakNama) kotakNama.addEventListener("keydown", function (ev) {
    if (ev.key === "Enter") { ev.preventDefault(); lanjut(); }
  });

  /* ── Pemutar foto: gulungan tegak berlensa tabung ──────────────────────
     Mengikuti rekaman template yang dikirim pemilik situs: foto bertumpuk
     naik terus-menerus dan melengkung seperti permukaan drum, dengan satu
     baris teks yang diam di tengah.

     Kemiringan tiap kartu dihitung ULANG tiap bingkai dari jaraknya ke tengah
     layar. Itu bagian yang tidak bisa dikerjakan CSS sendirian: lengkungannya
     harus mengikuti posisi, bukan waktu. */

  var TINGGI_KARTU = 281;
  var JARAK_KARTU = 24;
  var LANGKAH = TINGGI_KARTU + JARAK_KARTU;
  var TENGAH = 270;                 // separuh tinggi kanvas 540
  var LAMA_FOTO = 1700;             // satu foto melintasi tengah selama ini
  var REM = 900;                    // pengereman di ujung, supaya tidak berhenti mendadak

  var gulung = document.getElementById("warpGulung");
  var kartuWarp = [];
  var jamRaf = null;

  function hentikanPemutar() {
    if (jamRaf) { cancelAnimationFrame(jamRaf); jamRaf = null; }
  }

  function tataKartu(y) {
    var total = kartuWarp.length * LANGKAH;
    kartuWarp.forEach(function (el, i) {
      // Kartu yang sudah lewat di atas dikembalikan ke bawah — gulungan tanpa ujung.
      var pos = i * LANGKAH - y;
      pos = ((pos + LANGKAH) % total + total) % total - LANGKAH;
      var dy = (pos + TINGGI_KARTU / 2 - TENGAH) / TENGAH;
      // Dibatasi SEBELUM dipakai, bukan sesudah. Kartu yang menunggu jauh di
      // bawah layar punya dy sampai 8,6 — tanpa batas ini ia diputar 344
      // derajat, dan kalau kebetulan tepinya masuk layar saat berputar, yang
      // terlihat kartu yang terbalik.
      var batas = Math.max(-1.7, Math.min(1.7, dy));
      var jauh = Math.abs(batas);
      el.style.transform =
        "translate3d(0," + pos.toFixed(1) + "px," + (-jauh * 130).toFixed(1) + "px)" +
        " rotateX(" + (-batas * 40).toFixed(2) + "deg)" +
        " scale(" + (1 - jauh * 0.05).toFixed(3) + ")";
      el.style.opacity = (1 - jauh * 0.42).toFixed(3);
    });
  }

  function mainkanWarp(h) {
    var poster = [].slice.call(document.querySelectorAll("#home_" + h + " .kartu-poster img"));
    // Kartu yang belum diisi foto tidak punya apa-apa untuk diputar.
    if (!gulung || !poster.length) return;

    hentikanPemutar();
    gulung.innerHTML = "";
    kartuWarp = [];

    // Digandakan supaya gulungannya selalu lebih panjang daripada layar —
    // dengan tiga foto saja, tanpa ini akan muncul celah hitam di antaranya.
    var kali = poster.length < 4 ? 3 : 2;
    for (var k = 0; k < kali; k++) {
      poster.forEach(function (img) {
        var d = document.createElement("div");
        d.className = "warp-kartu";
        var g = document.createElement("img");
        g.src = img.src; g.alt = "";
        d.appendChild(g);
        gulung.appendChild(d);
        kartuWarp.push(d);
      });
    }

    show("warp");
    tataKartu(0);
    if (menyunting) return;

    var mulai = null;
    var habis = poster.length * LAMA_FOTO;     // sekali putaran penuh
    var laju = LANGKAH / LAMA_FOTO;            // px per ms

    function langkah(t) {
      if (mulai === null) mulai = t;
      var lewat = t - mulai;
      var y;
      if (lewat <= habis) {
        y = lewat * laju;
        jamRaf = requestAnimationFrame(langkah);
      } else if (lewat <= habis + REM) {
        // Melambat halus, bukan berhenti mendadak.
        var u = (lewat - habis) / REM;
        var pelan = 1 - (1 - u) * (1 - u);      // ease-out kuadrat
        y = habis * laju + laju * REM * 0.5 * (2 * u - pelan * u);
        jamRaf = requestAnimationFrame(langkah);
      } else {
        // Berhenti di sini. Tidak ada tombol lanjut — panah kembali di kiri
        // atas yang jadi jalan keluarnya, sama seperti di panel cerita.
        y = habis * laju + laju * REM * 0.5;
        jamRaf = null;
      }
      tataKartu(y);
    }
    jamRaf = requestAnimationFrame(langkah);
  }

  document.addEventListener("click", function (ev) {
    var el = ev.target.closest("[data-warp]");
    if (!el) return;
    mainkanWarp(el.getAttribute("data-warp"));
  });

  /* ── Tombol yang cuma pindah babak ─────────────────────────────────────── */
  document.addEventListener("click", function (ev) {
    var el = ev.target.closest("[data-ke]");
    if (!el) return;
    show(el.getAttribute("data-ke"));
  });

  document.addEventListener("click", function (ev) {
    if (!ev.target.closest("[data-kembali-dinamis]")) return;
    show(terakhirHome);
  });

  /* ── Poster diklik: buka layar detail profil itu ───────────────────────── */
  function bukaDetail(huruf, nomor) {
    var layar = document.getElementById("detail_" + huruf);
    if (!layar) return;
    [].forEach.call(layar.querySelectorAll(".det"), function (d) {
      d.classList.toggle("tampil", d.getAttribute("data-poster") === String(nomor));
    });
    show("detail_" + huruf);
  }

  document.addEventListener("click", function (ev) {
    var el = ev.target.closest("[data-detail]");
    if (!el) return;
    bukaDetail(el.getAttribute("data-detail"), el.getAttribute("data-poster"));
  });

  /* ── Sambungan editor ──────────────────────────────────────────────────
     Memilih sebuah kolom di daftar editor melompat ke babak tempat kolom itu
     berada. Tanpa ini, memilih "KITA · Cerita 6" tidak memperlihatkan apa-apa. */
  function babakUntukKunci(key) {
    if (key === "f_buka") return "buka";
    if (key === "judul_pilih") return "profil";
    if (key === "merek") return null;   // muncul di beberapa babak sekaligus
    if (/^[a-z]_(avatar|cap)$/.test(key)) return "profil";
    var m = /^([a-z])_/.exec(key);
    if (m) return "home_" + m[1];
    return null;
  }

  window.addEventListener("message", function (ev) {
    var data = ev.data || {};
    if (data.source !== "card-editor") return;
    if (data.type === "select") {
      var tujuan = babakUntukKunci(String(data.key || ""));
      if (tujuan) show(tujuan);
      return;
    }
    // Teks yang baru diketik pembeli bisa jadi lebih panjang dari sebelumnya.
    if (data.type === "text") setTimeout(perbaruiPotong, PUDAR > 0 ? 0 : 0);
  });

  perbaruiPotong();
})();
