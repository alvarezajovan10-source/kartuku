/* BIRTHDAY MAGAZINE — membalik HAMPARAN majalah terbuka.
 * ───────────────────────────────────────────────────────────────────────────
 * Pasangan: cards/templates/cards/render/bdaymag.html, static/css/render/bdaymag.css
 *
 * Mesin baliknya SALINAN majalah.js (Majalah Cinta), bukan dipakai bersama:
 * Majalah Cinta masih dikerjakan terpisah, dan dua template yang saling
 * bergantung pada satu berkas JS akan saling merusak tiap kali salah satunya
 * diubah. Dua tambahan di sini — lihat "Pelat dekat" dan "Teks muat" di
 * bawah. Penjelasan aslinya tetap dibiarkan apa adanya:
 *
 * Modelnya buku sungguhan, dan itu yang membedakannya dari renderer
 * "valentine" (satu halaman memudar di tempat). Yang berputar bukan seluruh
 * hamparan, melainkan SATU LEMBAR: sisi mukanya halaman kanan hamparan
 * sekarang, sisi baliknya halaman kiri hamparan berikutnya. Selama lembar itu
 * berputar, yang terlihat di bawahnya adalah halaman kiri lama (tetap di
 * tempat) dan halaman kanan baru (baru terbuka) — persis seperti membalik
 * lembaran majalah dengan jari.
 *
 * Kenapa memakai KLON, bukan memutar elemen .scene aslinya:
 * satu hamparan adalah dua elemen bersaudara, sedangkan lembar yang berputar
 * membutuhkan satu elemen yang punya dua sisi. Memaksa DOM asli masuk ke
 * bentuk itu berarti memindah-mindahkan halaman antar induk di tengah animasi,
 * dan setiap pemindahan menghapus keadaan yang dipegang editor (elemen terpilih,
 * kotak sorot, posisi crop foto). Klon dibuang setelah putaran selesai, jadi
 * DOM asli tidak pernah tersentuh.
 *
 * KONTRAK dengan editor (jangan diubah tanpa mengubah card-frame.js juga):
 *   - tiap hamparan <section class="scene"> punya id;
 *   - hamparan yang sedang dibaca punya class .active;
 *   - window.show(id) wajib ada supaya editor bisa melompat ke hamparan itu.
 */
(function () {
  "use strict";

  var majalah = document.getElementById("majalah");
  if (!majalah) return;

  var scenes = [].slice.call(majalah.querySelectorAll(".scene"));
  if (!scenes.length) return;

  var nav = document.getElementById("nav");
  var hitung = document.getElementById("nav-hitung");
  var tblMundur = nav && nav.querySelector('[data-arah="mundur"]');
  var tblMaju = nav && nav.querySelector('[data-arah="maju"]');

  var mengedit = document.body.classList.contains("is-editing");
  var KUNCI = "bdaymag:" + location.pathname;

  var indeks = 0;
  var sibuk = false;

  var hemat = window.matchMedia
    && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ── Bantuan ──────────────────────────────────────────────────────────── */

  /* Klon satu halaman, dibersihkan dari segala yang membuatnya "hidup".
   *
   * Membuang id & penanda editor itu WAJIB, bukan kerapian: klon berumur
   * sekejap, tapi selama ia ada, document.getElementById dan
   * querySelector("[data-edit=...]") bisa menemukan KLON lebih dulu daripada
   * elemen aslinya — dan editor lalu menyorot atau menulis ke elemen yang
   * sebentar lagi dibuang. Gejalanya: suntingan yang "hilang" kalau pembeli
   * mengetik tepat saat halaman sedang dibalik.
   *
   * Tiap klon diberi lapisan .bayang sendiri (lihat bdaymag.css).
   */
  function klonHalaman(hal) {
    var k = hal.cloneNode(true);
    k.removeAttribute("id");
    [].forEach.call(k.querySelectorAll("[id],[data-edit],[data-frame]"), function (el) {
      el.removeAttribute("id");
      el.removeAttribute("data-edit");
      el.removeAttribute("data-frame");
    });
    var b = document.createElement("div");
    b.className = "bayang";
    k.appendChild(b);
    return k;
  }

  function halKiri(scene) { return scene.querySelector(".hal.kiri"); }
  function halKanan(scene) { return scene.querySelector(".hal.kanan"); }

  function segarkanNav() {
    if (hitung) hitung.textContent = (indeks + 1) + " / " + scenes.length;
    if (tblMundur) tblMundur.disabled = indeks === 0;
    if (tblMaju) tblMaju.disabled = indeks === scenes.length - 1;
  }

  /* Pelat dekat: hanya hamparan aktif dan kedua tetangganya yang pelatnya
   * di-decode (aturan .scene:not(.dekat) di bdaymag.css). Tetangga ikut
   * karena lembar yang berputar memperlihatkan halaman hamparan berikutnya
   * SEBELUM hamparan itu jadi aktif. */
  function pasangDekat(i) {
    scenes.forEach(function (s, n) { s.classList.toggle("dekat", Math.abs(n - i) <= 1); });
  }

  function pasangAktif(i) {
    scenes.forEach(function (s, n) { s.classList.toggle("active", n === i); });
    indeks = i;
    pasangDekat(i);
    segarkanNav();
    var id = scenes[i].id;
    /* Hamparan yang sedang dibaca diingat, supaya kartu yang dimuat ulang
     * (Safari membuang tab yang lama didiamkan, atau editor memuat ulang
     * pratinjau sesudah foto/teks disimpan) kembali ke halaman yang sama,
     * bukan ke sampul. */
    try { sessionStorage.setItem(KUNCI, id); } catch (e) {}
    // Editor perlu tahu halaman mana yang terbuka: ia memuat ulang
    // pratinjau dengan ?scene= miliknya sendiri setelah tiap simpanan.
    if (mengedit && window.parent !== window) {
      window.parent.postMessage({ source: "card-frame", type: "halaman", scene: id }, "*");
    }
  }

  /* Hamparan awal. DIBACA SENDIRI dari ?scene=, bukan menunggu card-frame.js:
   * card-frame.js dimuat `defer`, jadi ia baru memasang .active SESUDAH skrip
   * ini jalan — dulu mesin ini mengira sampul yang terbuka, pelat hamparan
   * yang tampil tidak di-decode (gambar jalan & bingkai polaroid hilang), dan
   * panah berikutnya melompat ke halaman 2. */
  function hamparanAwal() {
    var cari = function (id) {
      var el = id && document.getElementById(id);
      return el ? scenes.indexOf(el) : -1;
    };
    var i = cari(new URLSearchParams(location.search).get("scene"));
    if (i < 0 && !mengedit) {
      try { i = cari(sessionStorage.getItem(KUNCI)); } catch (e) { i = -1; }
    }
    if (i < 0) i = Math.max(0, scenes.indexOf(majalah.querySelector(".scene.active")));
    return i;
  }

  /* ── Lembar yang berputar ────────────────────────────────────────────── */

  /* Satu putaran disiapkan (klon dipasang) lalu digerakkan lewat SUDUT.
   * Semua yang berubah per bingkai hanya transform & opacity — keduanya
   * dikerjakan compositor, jadi putaran tetap mulus walau halamannya berat.
   *
   * Sudut: 0 = lembar rebah di kanan, -180 = rebah di kiri. Maju berangkat
   * dari 0 ke -180, mundur sebaliknya. */
  function siapkan(tujuan) {
    var maju = tujuan > indeks;
    var kini = scenes[indeks];
    var lain = scenes[tujuan];
    var muka = maju ? halKanan(kini) : halKanan(lain);
    var balikan = maju ? halKiri(lain) : halKiri(kini);
    var dasarKiri = maju ? halKiri(kini) : halKiri(lain);
    var dasarKanan = maju ? halKanan(lain) : halKanan(kini);
    if (!muka || !balikan || !dasarKiri || !dasarKanan) return null;

    pasangDekat(tujuan);
    var dasar = document.createElement("div");
    dasar.id = "dasar";
    var kiri = klonHalaman(dasarKiri);
    var kanan = klonHalaman(dasarKanan);
    dasar.appendChild(kiri);
    dasar.appendChild(kanan);

    var lembar = document.createElement("div");
    lembar.id = "lembar";
    var sMuka = klonHalaman(muka);
    sMuka.classList.add("sisi", "muka");
    var sBalik = klonHalaman(balikan);
    sBalik.classList.add("sisi", "balik");
    lembar.appendChild(sMuka);
    lembar.appendChild(sBalik);

    majalah.appendChild(dasar);
    majalah.appendChild(lembar);

    return {
      tujuan: tujuan,
      maju: maju,
      dasar: dasar,
      lembar: lembar,
      bayang: [sMuka.lastChild, sBalik.lastChild, kiri.lastChild, kanan.lastChild],
      sisi: [sMuka, sBalik],
      sudut: maju ? 0 : -180,
      anim: null,
    };
  }

  /* Gaya pada satu sudut. Lembar paling gelap saat tegak lurus pandangan;
   * halaman di bawahnya teduh di sisi yang sedang dinaungi lembar. */
  function gayaSudut(a) {
    var s = Math.sin(-a * Math.PI / 180);
    var p = -a / 180;
    return {
      lembar: "rotateY(" + a.toFixed(2) + "deg)",
      sisi: (s * .38).toFixed(3),
      kiri: (p * p * .22).toFixed(3),
      kanan: ((1 - p) * (1 - p) * .3).toFixed(3),
      // Sisi mana yang tampak diurus SENDIRI, bukan oleh backface-visibility:
      // WebKit (Safari) tidak mematuhinya di sini dan memperlihatkan muka
      // lembar TERCERMIN dari belakang. Pertukarannya tepat di 90 derajat,
      // saat lembar tegak lurus layar, jadi tak kasatmata.
      muka: a > -90 ? 1 : 0,
      balik: a > -90 ? 0 : 1,
    };
  }

  function pasangSudut(ctx, a) {
    ctx.sudut = a;
    var g = gayaSudut(a);
    ctx.lembar.style.transform = g.lembar;
    ctx.bayang[0].style.opacity = g.sisi;
    ctx.bayang[1].style.opacity = g.sisi;
    ctx.bayang[2].style.opacity = g.kiri;
    ctx.bayang[3].style.opacity = g.kanan;
    ctx.sisi[0].style.opacity = g.muka;
    ctx.sisi[1].style.opacity = g.balik;
  }

  /* Gerak dari sudut sekarang ke `ke` dengan Web Animations. Keyframe
   * dicuplik per ~15 derajat supaya bayangan ikut lengkung sinusnya, plus
   * dua cuplikan mengapit 90 derajat untuk pertukaran sisi lembar. Sudut
   * linear terhadap kemajuan, jadi offset keyframe = jarak sudutnya. */
  function gerakkan(ctx, ke, durasi, lengkung) {
    var dari = ctx.sudut;
    var jarak = ke - dari;
    if (!jarak) return Promise.resolve();
    var titik = [];
    var n = Math.max(2, Math.ceil(Math.abs(jarak) / 15));
    for (var i = 0; i <= n; i++) titik.push(i / n);
    [-90.05, -89.95].forEach(function (a) {
      var o = (a - dari) / jarak;
      if (o > 0 && o < 1) titik.push(o);
    });
    titik.sort(function (x, y) { return x - y; });
    var jalur = [[], [], [], [], [], [], []];
    titik.forEach(function (o) {
      var g = gayaSudut(dari + jarak * o);
      jalur[0].push({ offset: o, transform: g.lembar });
      jalur[1].push({ offset: o, opacity: g.sisi });
      jalur[2].push({ offset: o, opacity: g.sisi });
      jalur[3].push({ offset: o, opacity: g.kiri });
      jalur[4].push({ offset: o, opacity: g.kanan });
      jalur[5].push({ offset: o, opacity: g.muka });
      jalur[6].push({ offset: o, opacity: g.balik });
    });
    var opsi = { duration: durasi, easing: lengkung, fill: "forwards" };
    var semua = [ctx.lembar].concat(ctx.bayang, ctx.sisi).map(function (el, j) {
      return el.animate(jalur[j], opsi);
    });
    return semua[0].finished.then(function () { pasangSudut(ctx, ke); });
  }

  function buang(ctx) {
    // Dua bingkai: hamparan baru sudah aktif & tergambar sebelum klon pergi.
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        if (ctx.lembar.parentNode) ctx.lembar.parentNode.removeChild(ctx.lembar);
        if (ctx.dasar.parentNode) ctx.dasar.parentNode.removeChild(ctx.dasar);
        sibuk = false;
      });
    });
  }

  /* Selesaikan putaran: jadi = sampai tujuan, tidak = kembali ke semula. */
  function tuntaskan(ctx, jadi, durasi, lengkung) {
    var ke = jadi === ctx.maju ? -180 : 0;
    return gerakkan(ctx, ke, durasi, lengkung).then(function () {
      if (jadi) pasangAktif(ctx.tujuan);
      else pasangDekat(indeks);
      buang(ctx);
    });
  }

  var DURASI_PENUH = 880;
  var LENGKUNG = "cubic-bezier(.32, .06, .22, 1)";   // terangkat pelan, jatuh lembut

  function balik(tujuan) {
    var aktifDom = scenes.indexOf(majalah.querySelector(".scene.active"));
    if (aktifDom >= 0 && aktifDom !== indeks) pasangAktif(aktifDom);
    if (sibuk || tujuan < 0 || tujuan >= scenes.length || tujuan === indeks) return;

    // Lompatan lebih dari satu hamparan (editor melompat ke halaman jauh)
    // tidak dianimasikan: yang benar secara harfiah adalah membalik lima
    // lembar berturut-turut, dan itu memakan empat detik untuk sesuatu yang
    // diminta pembeli supaya CEPAT sampai.
    if (hemat || Math.abs(tujuan - indeks) > 1 || !Element.prototype.animate) {
      pasangAktif(tujuan);
      return;
    }
    var ctx = siapkan(tujuan);
    if (!ctx) { pasangAktif(tujuan); return; }
    sibuk = true;
    pasangSudut(ctx, ctx.sudut);
    // Dua bingkai jeda: klon digambar dulu di posisi diam (tampilannya sama
    // persis dengan hamparan sekarang), baru bergerak. Menggambar klon pertama
    // kali makan 40-110 ms di WebKit; kalau itu jatuh di tengah gerakan,
    // lembarnya tersentak. Di sini ia jatuh saat semuanya masih diam.
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        tuntaskan(ctx, true, DURASI_PENUH, LENGKUNG);
      });
    });
  }

  function maju() { balik(indeks + 1); }
  function mundur() { balik(indeks - 1); }

  /* ── Kendali ─────────────────────────────────────────────────────────── */

  if (tblMaju) tblMaju.addEventListener("click", maju);
  if (tblMundur) tblMundur.addEventListener("click", mundur);

  document.addEventListener("keydown", function (e) {
    if (e.key === "ArrowRight" || e.key === "PageDown") { maju(); }
    else if (e.key === "ArrowLeft" || e.key === "PageUp") { mundur(); }
  });

  /* Tarik halaman dengan jari/mouse: lembar mengikuti jari seperti kertas
   * sungguhan, lalu dilepas — diteruskan kalau sudah lewat sepertiga atau
   * dilempar cepat, dikembalikan kalau tidak. Syarat mendatar (|dx| > |dy|)
   * dan ambang 10px supaya menggulir halaman di HP tidak ikut membalik. */
  var habisTarik = false;
  (function () {
    var t = null;
    majalah.addEventListener("pointerdown", function (e) {
      if (sibuk || (e.pointerType === "mouse" && e.button !== 0)) return;
      if (e.target.closest && e.target.closest(".gulir")) return;   // menggulir surat
      t = { id: e.pointerId, x0: e.clientX, y0: e.clientY, ctx: null, jalan: [] };
    });
    majalah.addEventListener("pointermove", function (e) {
      if (!t || e.pointerId !== t.id) return;
      var dx = e.clientX - t.x0, dy = e.clientY - t.y0;
      if (!t.ctx) {
        if (Math.abs(dx) < 10 || Math.abs(dx) <= Math.abs(dy)) {
          if (Math.abs(dy) > 14) t = null;   // gulir tegak: lepaskan
          return;
        }
        var tujuan = dx < 0 ? indeks + 1 : indeks - 1;
        if (hemat || tujuan < 0 || tujuan >= scenes.length || !Element.prototype.animate) { t = null; return; }
        t.ctx = siapkan(tujuan);
        if (!t.ctx) { t = null; return; }
        sibuk = true;
        try { majalah.setPointerCapture(e.pointerId); } catch (err) {}
      }
      var lebar = majalah.getBoundingClientRect().width * .8;
      var p = Math.max(0, Math.min(1, (t.ctx.maju ? -dx : dx) / lebar));
      pasangSudut(t.ctx, t.ctx.maju ? -180 * p : -180 * (1 - p));
      t.jalan.push([e.timeStamp, dx]);
      if (t.jalan.length > 6) t.jalan.shift();
    });
    function lepas(e) {
      if (!t || e.pointerId !== t.id) return;
      var ctx = t.ctx, jalan = t.jalan;
      t = null;
      if (!ctx) return;
      habisTarik = true;
      setTimeout(function () { habisTarik = false; }, 60);
      var p = ctx.maju ? -ctx.sudut / 180 : 1 + ctx.sudut / 180;
      var v = 0;
      if (jalan.length > 1) {
        var a = jalan[0], b = jalan[jalan.length - 1];
        v = (b[1] - a[1]) / Math.max(1, b[0] - a[0]);   // px per ms
        if (ctx.maju) v = -v;
      }
      var jadi = e.type !== "pointercancel" && (p > .33 || v > .45);
      var sisa = jadi ? 1 - p : p;
      tuntaskan(ctx, jadi, Math.max(200, DURASI_PENUH * .75 * sisa), "cubic-bezier(.2, .7, .3, 1)");
    }
    majalah.addEventListener("pointerup", lepas);
    majalah.addEventListener("pointercancel", lepas);
  })();

  // Klik yang menyusul sebuah tarikan bukan klik: jangan sampai ia memilih
  // elemen di editor atau membalik halaman sekali lagi.
  document.addEventListener("click", function (e) {
    if (habisTarik) { e.stopPropagation(); e.preventDefault(); }
  }, true);

  /* Klik separuh kanan/kiri halaman. TIDAK dipasang saat mengedit: di editor,
   * klik pada halaman berarti "pilih elemen ini", dan membalik halaman di
   * bawah jari pembeli yang sedang memilih teks membuat editor terasa rusak. */
  if (!mengedit) {
    majalah.addEventListener("click", function (e) {
      if (e.target.closest && e.target.closest(".gulir")) return;   // sedang membaca surat
      var kotak = majalah.getBoundingClientRect();
      if (e.clientX > kotak.left + kotak.width / 2) maju(); else mundur();
    });
  }

  /* ── Kontrak editor ──────────────────────────────────────────────────── */

  window.show = function (id) {
    var i = scenes.indexOf(document.getElementById(id));
    if (i >= 0) balik(i);
  };

  /* ── Ajakan memutar HP ───────────────────────────────────────────────── */

  (function () {
    var hint = document.getElementById("putar-hp");
    if (!hint) return;
    // Cuma untuk layar yang benar-benar sempit DAN tegak. Laptop dengan
    // jendela kecil tidak perlu disuruh memutar apa pun.
    if (window.innerWidth > 560 || window.innerHeight < window.innerWidth) return;
    // Dan TIDAK PERNAH di editor. Di sana kartunya duduk dalam iframe sempit
    // di samping panel — sempit karena bingkainya, bukan karena HP-nya — jadi
    // ajakan memutar HP muncul di layar laptop dan menutupi kartu yang sedang
    // disunting.
    if (mengedit) return;
    hint.hidden = false;
    var buang = function () { hint.hidden = true; };
    setTimeout(buang, 6000);
    hint.addEventListener("click", buang);
    window.addEventListener("orientationchange", buang);
  })();

  /* ── Teks muat ───────────────────────────────────────────────────────── */

  /* Teks pembeli yang lebih panjang dari bawaannya dikecilkan sampai muat di
   * kotak teks desainnya (pola --muat dari Valentine Story). Selama teksnya
   * muat, --muat tetap 1 dan desainnya tidak berubah sepiksel pun. Tanpa ini,
   * nama panjang di sampul atau surat yang ditulis panjang menabrak foto dan
   * tulisan lain — halaman majalah tidak bisa memanjang.
   *
   * Tinggi yang dibandingkan adalah tinggi blok teks SETELAH margin negatif
   * .tx (baris pertama setinggi ukuran Canva, lihat bdaymag.css) — itulah
   * yang setara dengan tinggi kotak teks Canva. Kelonggaran 4% menyerap beda
   * metrik font pengganti (Bellefair untuk The Seasons). */
  var LONGGAR = 1.04;
  var MUAT_MIN = 0.4;

  // Kotak "boleh-gulir" (isi surat): huruf berhenti mengecil di sini, sisanya
  // digulir. Di bawah ~80% huruf surat tidak terbaca lagi di HP.
  var MUAT_MIN_GULIR = 0.8;

  function terlalu(tx, kotak) {
    var tepi = parseFloat(getComputedStyle(tx).marginTop) || 0;
    // Kotak "ketat" tidak diberi kelonggaran: tepat di bawahnya ada teks lain
    // (isi surat -> salam penutup), dan 4% lebih sudah menabraknya.
    var longgar = kotak.classList.contains("ketat") ? 1 : LONGGAR;
    var tinggi = kotak.clientHeight
      - (parseFloat(getComputedStyle(kotak).paddingBottom) || 0);
    return tx.offsetHeight + 2 * tepi > tinggi * longgar + 1
      || tx.scrollWidth > kotak.clientWidth + 2;
  }

  function muatkan(tx) {
    var kotak = tx.parentNode;
    var bolehGulir = kotak.classList.contains("boleh-gulir");
    var min = bolehGulir ? MUAT_MIN_GULIR : MUAT_MIN;
    kotak.classList.remove("gulir", "di-ujung");
    tx.style.setProperty("--muat", "1");
    if (!terlalu(tx, kotak)) return;
    tx.style.setProperty("--muat", min.toFixed(3));
    if (terlalu(tx, kotak)) {
      // Tidak muat bahkan di ukuran terkecil: digulir, tidak dipotong.
      if (bolehGulir) kotak.classList.add("gulir");
      return;
    }
    var bawah = min, atas = 1;
    for (var i = 0; i < 7; i++) {
      var tengah = (bawah + atas) / 2;
      tx.style.setProperty("--muat", tengah.toFixed(3));
      if (terlalu(tx, kotak)) atas = tengah; else bawah = tengah;
    }
    tx.style.setProperty("--muat", bawah.toFixed(3));
  }

  // Pudar bawah hilang begitu surat digulir sampai habis.
  majalah.addEventListener("scroll", function (e) {
    var k = e.target;
    if (!k.classList || !k.classList.contains("gulir")) return;
    k.classList.toggle("di-ujung", k.scrollTop + k.clientHeight >= k.scrollHeight - 2);
  }, true);

  function muatkanSemua() {
    [].forEach.call(majalah.querySelectorAll(".kotak-tx > .tx"), muatkan);
  }

  muatkanSemua();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(muatkanSemua);
  window.addEventListener("load", muatkanSemua);

  // Di editor teks berubah lewat card-frame.js (textContent) dan gaya lewat
  // stylesheet suntikan — dua-duanya tanpa memuat ulang halaman.
  if (document.body.classList.contains("is-editing") && window.MutationObserver) {
    var antre = 0;
    var jadwalkan = function () {
      cancelAnimationFrame(antre);
      antre = requestAnimationFrame(muatkanSemua);
    };
    // Klon lembar yang dipasang/dibuang saat membalik bukan perubahan teks;
    // mengukur ulang 50 teks di awal putaran membuatnya tersendat.
    new MutationObserver(function (daftar) {
      var klon = function (n) { return n.id === "lembar" || n.id === "dasar"; };
      var nyata = daftar.some(function (m) {
        return m.type !== "childList" || m.target !== majalah
          || ![].every.call(m.addedNodes, klon) || ![].every.call(m.removedNodes, klon);
      });
      if (nyata) jadwalkan();
    }).observe(majalah, { childList: true, characterData: true, subtree: true });
    new MutationObserver(jadwalkan).observe(document.head, { childList: true, characterData: true, subtree: true });
  }

  pasangAktif(hamparanAwal());
})();
