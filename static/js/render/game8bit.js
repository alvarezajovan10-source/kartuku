/* GAME 8-BIT — perpindahan babak, bar XP, dan ubin power-up yang dibuka.

   Kontrak renderer berbabak (lihat static/js/card-frame.js):
   - tiap babak adalah <section class="scene"> ber-id
   - babak yang sedang tampil punya class .active
   - window.show(id) wajib ada supaya editor bisa melompat antar babak
*/

const babak = [...document.querySelectorAll('.scene')];
const dotsEl = document.getElementById('dots');
const prevBtn = document.getElementById('prev');
const nextBtn = document.getElementById('next');
const navEl = document.querySelector('.nav');
const taman = document.getElementById('taman');
const kurangiGerak = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

let idx = 0;

babak.forEach((_, i) => {
  const d = document.createElement('i');
  d.addEventListener('click', () => ke(i));
  dotsEl.appendChild(d);
});

function ke(n) {
  idx = Math.max(0, Math.min(babak.length - 1, n));
  babak.forEach((s, i) => s.classList.toggle('active', i === idx));
  [...dotsEl.children].forEach((d, i) => d.classList.toggle('on', i === idx));
  prevBtn.disabled = idx === 0;
  nextBtn.disabled = idx === babak.length - 1;
  // Layar judul hanya bisa dilewati lewat PRESS START.
  navEl.classList.toggle('sembunyi', babak[idx].id === 'title');
  if (babak[idx].id === 'levelup') naikLevel();
  temaniBabak(babak[idx].id);
}

/* Dipanggil editor lewat postMessage untuk melompat ke babak tertentu. */
window.show = function (id) {
  const i = babak.findIndex((s) => s.id === id);
  if (i >= 0) ke(i);
};

prevBtn.addEventListener('click', () => ke(idx - 1));
nextBtn.addEventListener('click', () => ke(idx + 1));
document.addEventListener('keydown', (e) => {
  if (babak[idx].id === 'title') return;
  if (e.key === 'ArrowRight') ke(idx + 1);
  if (e.key === 'ArrowLeft') ke(idx - 1);
});

/* Geser jari. Hanya dihitung kalau gerakannya memang mendatar — tanpa syarat
   itu, menggulir isi babak yang panjang ikut terbaca sebagai ganti babak. */
let sx = 0, sy = 0;
document.addEventListener('touchstart', (e) => {
  sx = e.changedTouches[0].clientX; sy = e.changedTouches[0].clientY;
}, { passive: true });
document.addEventListener('touchend', (e) => {
  if (babak[idx].id === 'title') return;
  const dx = e.changedTouches[0].clientX - sx;
  const dy = e.changedTouches[0].clientY - sy;
  if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5) ke(idx + (dx < 0 ? 1 : -1));
}, { passive: true });

/* Seluruh kartu diskalakan transform (lihat card-stage.js), jadi
   getBoundingClientRect memberi ukuran LAYAR sementara left/top yang kita
   tulis dibaca dalam ukuran KARTU. Selisihnya harus dibagi skala.

   Tanpa ini partikel meleset makin jauh makin besar skalanya: di layar lebar
   (skala ~2,8) hati dan kertas pesta terlempar ratusan piksel ke luar kanvas,
   lalu dipotong overflow:hidden — jadi terlihat seperti tidak ada apa-apa
   yang keluar sama sekali. Dulu tidak kentara karena kartu tegak dibatasi
   1,15x; kartu mendatar melepas batas itu, dan bug lamanya baru muncul. */
function skalaKartu() {
  if (!taman || !taman.offsetWidth) return 1;
  return taman.getBoundingClientRect().width / taman.offsetWidth || 1;
}

/* ---------- hati piksel yang berhamburan ---------- */
function hamburkan(x, y, jumlah) {
  if (kurangiGerak || !taman) return;
  const kotak = taman.getBoundingClientRect();
  const k = skalaKartu();
  for (let i = 0; i < jumlah; i++) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    el.setAttribute('viewBox', '0 0 9 8');
    el.innerHTML = '<use href="#s-hati"/>';
    const ukuran = 18 + Math.random() * 22;
    el.style.cssText =
      'position:absolute;width:' + ukuran + 'px;height:' + ukuran + 'px;' +
      'left:' + (x - kotak.left) / k + 'px;top:' + (y - kotak.top) / k + 'px;' +
      'shape-rendering:crispEdges;pointer-events:none';
    taman.appendChild(el);
    const sudut = Math.random() * Math.PI * 2;
    const jauh = 60 + Math.random() * 130;
    el.animate([
      { transform: 'translate(-50%,-50%) scale(.4)', opacity: 1 },
      {
        transform: 'translate(calc(-50% + ' + Math.cos(sudut) * jauh + 'px),' +
          'calc(-50% + ' + (Math.sin(sudut) * jauh + 70) + 'px)) scale(1)',
        opacity: 0,
      },
    ], {
      duration: 850 + Math.random() * 500,
      // steps() menjaga gerakannya tetap patah-patah seperti animasi 8-bit;
      // gerak halus di sini justru merusak gayanya.
      easing: 'steps(9, end)',
    }).onfinish = () => el.remove();
  }
}

/* ---------- semua yang bisa diketuk ----------
   Satu penangan di fase TANGKAP pada document, bukan listener per tombol.
   Alasannya bukan kerapian: di editor, card-frame.js memasang penangan
   tangkap sendiri yang memanggil stopPropagation() pada tiap elemen
   ber-data-edit / data-frame supaya kliknya terbaca sebagai "pilih elemen
   untuk disunting". Tombol HUG, PRESS START, dan ubin power-up semuanya
   ber-data-edit — jadi listener yang menempel di tombolnya sendiri TIDAK
   PERNAH kebagian, dan tombolnya terasa mati waktu dicoba dari editor.

   Berkas ini dimuat sebelum card-frame.js (yang defer), jadi penangan di
   sini mendaftar lebih dulu dan berjalan lebih dulu. Sengaja tidak memanggil
   preventDefault: editor tetap boleh memilih elemennya. */
document.addEventListener('click', (e) => {
  const sasaran = e.target.closest ? e.target : e.target.parentElement;
  if (!sasaran) return;

  const tombol = sasaran.closest('#startBtn, #ulangBtn, #pelukBtn');
  if (tombol) {
    const r = tombol.getBoundingClientRect();
    if (tombol.id === 'startBtn') {
      hamburkan(r.left + r.width / 2, r.top + r.height / 2, 10);
      ke(1);
    } else if (tombol.id === 'ulangBtn') {
      document.querySelectorAll('#kisi .ubin').forEach((u) => {
        u.classList.remove('terbuka', 'terbalik');
      });
      ke(0);
    } else {
      peluk();
    }
    return;
  }

  const ubin = sasaran.closest('#kisi .ubin');
  if (ubin) {
    if (!ubin.classList.contains('terbuka')) {
      // Ketukan pertama: tutup "?" pecah, ceritanya yang terbaca duluan.
      ubin.classList.add('terbuka');
      const r = ubin.getBoundingClientRect();
      hamburkan(r.left + r.width / 2, r.top + r.height / 2, 4);
    } else {
      // Sesudah terbuka, tiap ketukan membaliknya bolak-balik.
      ubin.classList.toggle('terbalik');
    }
    return;
  }

  const lilin = sasaran.closest('.lilin');
  if (lilin) ketukLilin(lilin);
}, true);

/* ---------- bar XP & LEVEL UP ----------
   Bar diisi dulu, baru tulisannya meletup. Dijalankan ulang tiap kali babak
   ini dibuka, jadi penerima yang mundur lalu maju lagi tetap melihatnya. */
const xpIsi = document.getElementById('xpIsi');
const popLevel = document.getElementById('popLevel');
let timerLevel = null;

function naikLevel() {
  if (!xpIsi || !popLevel) return;
  clearTimeout(timerLevel);
  popLevel.classList.remove('meletup');
  xpIsi.style.width = '0';

  if (kurangiGerak) {
    xpIsi.style.width = '100%';
    return;
  }
  // Dipaksa menggambar sekali supaya transisi lebarnya benar-benar mulai
  // dari nol — tanpa ini browser menggabung dua penulisan jadi satu.
  void xpIsi.offsetWidth;
  requestAnimationFrame(() => { xpIsi.style.width = '100%'; });
  // Semburan pembuka begitu babaknya dibuka: karakternya yang memulai
  // pesta, bar XP-nya menyusul. Sengaja SATU letupan saja — puncaknya
  // bukan di sini, dan menumpahkan semuanya di depan membuat "LEVEL UP!"
  // yang menyusul terasa datar.
  pestaBerdua(1);
  timerLevel = setTimeout(() => {
    popLevel.classList.add('meletup');
    const r = popLevel.getBoundingClientRect();
    hamburkan(r.left + r.width / 2, r.top + r.height / 2, 16);
    // Puncaknya: tepat waktu tulisannya meletup, semburan penuh.
    pestaBerdua(LETUPAN);
  }, 1150);
}

/* ---------- penanda "masih ada lanjutannya" ----------
   Panah di dasar bagan hanya menyala selama masih ada teks di bawah yang
   belum terlihat, dan padam begitu penerima sampai ke bawah. Tanpa penanda,
   tidak ada alasan bagi penerima menduga suratnya masih berlanjut — dan
   bagian yang tidak terbaca sama saja dengan tidak ditulis. */
function tandaGulir(kotak) {
  const panah = kotak.parentElement.querySelector('.panah-gulir')
    || kotak.closest('.panel, .kotak-dialog')?.querySelector('.panah-gulir');
  if (!panah) return;
  const segarkan = () => {
    const sisa = kotak.scrollHeight - kotak.clientHeight - kotak.scrollTop;
    panah.classList.toggle('tampak', sisa > 4);
  };
  kotak.addEventListener('scroll', segarkan, { passive: true });
  window.addEventListener('resize', segarkan);
  // Teks yang diubah pembeli di editor mengubah tingginya juga.
  if (window.MutationObserver) {
    new MutationObserver(segarkan).observe(kotak, {
      subtree: true, childList: true, characterData: true,
    });
  }
  segarkan();
}
document.querySelectorAll('[data-gulir]').forEach(tandaGulir);
// Font permainan dimuat belakangan dan mengubah tinggi teks; hitung ulang.
window.addEventListener('load', () => {
  document.querySelectorAll('[data-gulir]').forEach((k) => k.dispatchEvent(new Event('scroll')));
});

/* ---------- ajakan memiringkan HP ----------
   Lapisannya hanya tampil di layar tegak (diatur CSS). Tombolnya menutup
   pilihan itu untuk seterusnya — penerima yang memang ingin membaca sambil
   tegak tidak boleh dipaksa. */
const putarEl = document.getElementById('putarHp');
const putarBtn = document.getElementById('putarLanjut');
if (putarBtn && putarEl) {
  putarBtn.addEventListener('click', () => putarEl.classList.add('pergi'));
}

/* ================= TEMAN ==================================================
   Dua karakter yang menemani penerima sepanjang kartu.

   Aturannya: selalu terlihat, tidak pernah teleport, geraknya wajar. Karena
   babak berganti dengan potongan tegas, mereka TIDAK boleh tinggal di dalam
   babak — mereka hidup di lapisan sendiri, dan tiap babak berganti mereka
   BERJALAN ke posisi barunya. Jarak jauh ditempuh sambil berlari, jarak
   dekat sambil berjalan; itu yang membuat perpindahannya terbaca wajar
   alih-alih seperti benda yang digeser.

   Barisnya harus sama persis dengan URUTAN di pembuat sheet-nya. Kalau
   urutan di sana diubah, ubah juga di sini. */
const ANIM = {
  idle: { baris: 0, frames: 2, dur: 1.1 },
  walk: { baris: 1, frames: 4, dur: .62 },
  run: { baris: 2, frames: 4, dur: .42 },
  wave: { baris: 3, frames: 3, dur: .66 },
  happy: { baris: 4, frames: 2, dur: .5 },
  surprised: { baris: 5, frames: 2, dur: .7 },
  sit: { baris: 6, frames: 2, dur: 1.5 },
  sleep: { baris: 7, frames: 2, dur: 2.2 },
  jump: { baris: 8, frames: 3, dur: .5 },
  celebrate: { baris: 9, frames: 4, dur: .48 },
  hug: { baris: 10, frames: 2, dur: 1.4 },
  blow: { baris: 11, frames: 3, dur: .42 },
};

const TINGGI_FRAME = 138;
const LEBAR_TEMAN = 102;
const W_KANVAS = 960;          // lebar kanonis; sama dengan --w0 di CSS

/* Ke mana mereka berdiri di tiap babak, dan sedang apa. Posisi dalam pecahan
   lebar kanvas supaya gampang dibaca. */
const PANGGUNG = {
  title:       { x: [.24, .72], laku: 'wave' },
  player:      { x: [.19, .78], laku: 'happy' },
  levelup:     { x: [.22, .75], laku: 'celebrate' },
  dialog:      { x: [.06, .91], laku: 'sit' },
  wishes:      { x: [.13, .85], laku: 'surprised' },
  powerups:    { x: [.05, .92], laku: 'idle' },
  // Mengapit kue di paruh kiri, saling berhadapan. Angkanya bukan selera:
  // kue berdiri di x 85-285, dan tombol navigasi menguasai x 360-600 di
  // dasar kartu — keduanya harus dihindari badan mereka.
  kue:         { x: [.07, .335], laku: 'idle', hadap: [1, -1] },
  gameover:    { x: [.25, .71], laku: 'celebrate' },
};

const JEDA_TIDUR = 20000;      // diam selama ini -> mereka ketiduran

function Teman(el, mula) {
  this.el = el;
  this.sprite = el.querySelector('.sprite');
  this.x = mula;
  this.tujuan = mula;
  this.pangkal = mula;         // tempat berdiri di babak ini; lihat temaniBabak
  this.lari = false;
  this.hadap = 1;
  this.anim = '';
  this.laku = 'idle';          // yang dimainkan setelah sampai
  this.kunci = null;           // arah hadap yang dipaksa, kalau ada
  this.sekali = null;          // animasi sekali jalan (mis. dari klik)
  this.sampai = 0;
  this.pasang('idle');
  this.gambar();
}

Teman.prototype.pasang = function (nama) {
  if (this.anim === nama) return;
  const a = ANIM[nama] || ANIM.idle;
  this.anim = nama;
  this.sprite.style.setProperty('--frames', a.frames);
  this.sprite.style.setProperty('--dur', a.dur + 's');
  this.sprite.style.backgroundPositionY = -(a.baris * TINGGI_FRAME) + 'px';
};

/* Sekali berangkat, sekali diputuskan: berjalan atau berlari. Sempat
   diputuskan ulang tiap frame dari sisa jarak, dan hasilnya pejalan yang
   melambat sendiri di tengah jalan — perjalanan panjang jadi memakan lima
   detik dan terbaca seperti macet. */
Teman.prototype.pergiKe = function (x) {
  this.lari = Math.abs(x - this.x) > 200;
  this.tujuan = x;
};

Teman.prototype.gambar = function () {
  this.el.style.setProperty('--x', this.x.toFixed(1) + 'px');
  this.sprite.style.setProperty('--hadap', this.hadap);
};

/* Animasi sekali jalan, lalu kembali ke perilaku babak. */
Teman.prototype.mainkan = function (nama, lama) {
  this.sekali = nama;
  this.sampai = performance.now() + lama;
  this.pasang(nama);
};

Teman.prototype.langkah = function (dt, now) {
  const beda = this.tujuan - this.x;
  const jarak = Math.abs(beda);

  if (jarak > 2) {
    // Jarak jauh ditempuh berlari — orang tidak berjalan santai menyeberangi
    // layar, dan langkah pelan sejauh itu terlihat seperti benda digeser.
    const lari = this.lari;
    const laju = (lari ? 260 : 104) * dt;
    this.x += Math.sign(beda) * Math.min(laju, jarak);
    this.hadap = beda < 0 ? -1 : 1;
    this.pasang(lari ? 'run' : 'walk');
    this.sekali = null;
    this.gambar();
    return;
  }

  this.x = this.tujuan;
  if (this.kunci !== null) this.hadap = this.kunci;
  if (this.sekali) {
    if (now < this.sampai) return;
    this.sekali = null;
  }
  this.pasang(this.laku);
  this.gambar();
};

const temanCowok = document.getElementById('temanCowok');
const temanCewek = document.getElementById('temanCewek');
let regu = [];
let sentuhTerakhir = performance.now();

/* Keadaan pelukan sengaja dideklarasikan DI SINI, jauh sebelum peluk()
   dipakai di bawah. Sempat ditaruh dekat fungsinya, dan akibatnya fatal:
   loop animasi di bawah mulai berjalan seketika dan langsung memanggil
   cekPeluk(), yang membaca `memeluk` sebelum baris `let`-nya sempat jalan.
   JavaScript melempar ReferenceError di situ, dan SELURUH sisa berkas ini
   berhenti dieksekusi — pesta, penyalin nama, dan perintah pelukan ikut
   mati, walau tidak ada yang salah dengan kodenya sendiri. */
let memeluk = false;
let hatiPeluk = false;

/* Keadaan babak TIUP LILIN — sengaja ikut dideklarasikan di sini, dengan
   alasan yang persis sama seperti dua baris di atas: ke() dipanggil di baris
   terakhir berkas ini dan memanggil temaniBabak(), yang membaca semuaPadam.
   Kalau deklarasinya menunggu sampai dekat fungsi-fungsi lilin di bawah,
   pembacaan itu jatuh sebelum `let`-nya jalan dan seluruh berkas mati. */
let antreLilin = [];
let sedangTiup = false;
let giliranTiup = 0;
let timerTiup = [];
let semuaPadam = false;

if (temanCowok && temanCewek) {
  regu = [
    new Teman(temanCowok, W_KANVAS * PANGGUNG.title.x[0] - LEBAR_TEMAN / 2),
    new Teman(temanCewek, W_KANVAS * PANGGUNG.title.x[1] - LEBAR_TEMAN / 2),
  ];

  regu.forEach((t, i) => {
    t.el.addEventListener('click', () => {
      sentuhTerakhir = performance.now();
      // Yang diketuk melompat, pasangannya ikut melambai — mereka sepasang,
      // jadi menanggapi berdua terasa lebih hidup daripada sendiri-sendiri.
      t.mainkan('jump', 700);
      regu[1 - i].mainkan('wave', 900);
    });
  });

  let lalu = performance.now();
  (function putar(now) {
    const dt = Math.min((now - lalu) / 1000, .05);   // lompatan waktu saat
    lalu = now;                                       // tab ditinggal dibuang
    if (now - sentuhTerakhir > JEDA_TIDUR) {
      regu.forEach((t) => { t.laku = 'sleep'; });
    }
    regu.forEach((t) => t.langkah(dt, now));
    cekPeluk();
    requestAnimationFrame(putar);
  })(lalu);
}

/* Nama di papan atas kepala mengambil dari isian 1P dan 2P: 1P milik cowok,
   2P milik cewek. Disalin, bukan diedit langsung di sini — kalau papan ini
   ikut jadi sasaran klik editor, pembeli punya dua tempat berbeda untuk
   mengubah satu nama yang sama.

   MutationObserver dipakai supaya papannya ikut berubah SAAT pembeli
   mengetik di editor; tanpa itu namanya baru muncul setelah pratinjau
   dimuat ulang. */
(function cerminNama() {
  const pasangan = [
    [document.getElementById('nama1p'), document.getElementById('namaCowok')],
    [document.getElementById('nama2p'), document.getElementById('namaCewek')],
  ].filter(([a, b]) => a && b);
  if (!pasangan.length) return;

  const salin = () => pasangan.forEach(([sumber, papan]) => {
    papan.textContent = (sumber.textContent || '').trim();
  });
  salin();

  const babakPlayer = document.getElementById('player');
  if (babakPlayer && window.MutationObserver) {
    new MutationObserver(salin).observe(babakPlayer, {
      subtree: true, childList: true, characterData: true,
    });
  }

  // Jalur kedua: dengarkan langsung pesan editor. MutationObserver saja
  // ternyata tidak cukup diandalkan di sini, dan nama yang tidak ikut
  // berubah membuat pembeli mengira fiturnya rusak. setTimeout dipakai
  // karena berkas ini mendaftar sebelum card-frame.js — tanpa jeda, kita
  // membaca teks LAMA yang belum sempat ditimpa.
  window.addEventListener('message', (event) => {
    const d = event.data || {};
    if (d.source === 'card-editor' && (d.type === 'text' || d.type === 'reload')) {
      setTimeout(salin, 0);
    }
  });
})();

/* ---------- pesta meriah ----------
   Kertas warna yang disemburkan kedua karakter LURUS KE ATAS, lalu jatuh
   melebar. Bukan meletup ke segala arah: yang menyemburkan adalah karakter
   di lantai, jadi arah naik itulah yang membuatnya terbaca datang dari
   mereka, bukan muncul begitu saja di udara. */
const WARNA_PESTA = ['#ffd23f', '#ff6bb5', '#a8e6cf', '#b9a5e3', '#ffffff', '#ff2d8a'];

/* Isi semburannya tidak seragam. Kertas polos saja terbaca rata dan murah;
   beberapa hati dan bintang kerlip di antaranya yang membuatnya terbaca
   sebagai perayaan. Porsinya sengaja timpang — hati dan bintang hanya
   selingan, kalau sama banyak dengan kertas hasilnya jadi ramai tanpa
   bentuk. Keduanya SVG, yang lebih mahal digambar daripada kotak polos,
   jadi jumlahnya juga ditahan demi HP lama. */
function butirPesta(i) {
  const undi = i % 8;
  if (undi === 3 || undi === 6) return { lambang: '#s-hati', vb: '0 0 9 8', sisi: 15 + Math.random() * 12 };
  if (undi === 5) return { lambang: '#s-kilau', vb: '0 0 7 7', sisi: 13 + Math.random() * 10 };
  return null;
}

function pesta(x, y, jumlah, tunda) {
  if (kurangiGerak || !taman) return;
  const kotak = taman.getBoundingClientRect();
  const k = skalaKartu();
  for (let i = 0; i < jumlah; i++) {
    const bentuk = butirPesta(i);
    let el;
    if (bentuk) {
      el = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      el.setAttribute('viewBox', bentuk.vb);
      el.innerHTML = '<use href="' + bentuk.lambang + '"/>';
      el.style.cssText =
        'position:absolute;width:' + bentuk.sisi + 'px;height:' + bentuk.sisi + 'px;' +
        'shape-rendering:crispEdges;' +
        'left:' + (x - kotak.left) / k + 'px;top:' + (y - kotak.top) / k + 'px;pointer-events:none';
    } else {
      el = document.createElement('i');
      const sisi = 5 + Math.floor(Math.random() * 6);
      el.style.cssText =
        'position:absolute;width:' + sisi + 'px;height:' + (sisi + Math.round(Math.random() * 4)) + 'px;' +
        'background:' + WARNA_PESTA[i % WARNA_PESTA.length] + ';' +
        'left:' + (x - kotak.left) / k + 'px;top:' + (y - kotak.top) / k + 'px;pointer-events:none';
    }
    taman.appendChild(el);

    const miring = (Math.random() - .5) * 210;  // sebaran mendatar saat naik
    const tinggi = 190 + Math.random() * 260;
    el.animate([
      { transform: 'translate(-50%,-50%) scale(.4) rotate(0deg)', opacity: 0 },
      { transform: 'translate(-50%,-50%) scale(.4) rotate(0deg)', opacity: 1, offset: .001 },
      {
        transform: 'translate(calc(-50% + ' + miring * .5 + 'px), calc(-50% - ' + tinggi + 'px))' +
          ' scale(1) rotate(' + (Math.random() * 260 - 130) + 'deg)',
        opacity: 1, offset: .42,
      },
      {
        transform: 'translate(calc(-50% + ' + miring * 1.8 + 'px), calc(-50% + ' + (170 + Math.random() * 120) + 'px))' +
          ' scale(.9) rotate(' + (Math.random() * 500 - 250) + 'deg)',
        opacity: 0,
      },
    ], {
      duration: 1500 + Math.random() * 900,
      // Butir yang belum berangkat harus TIDAK TERLIHAT, bukan menumpuk
      // sebagai gumpalan diam di mulut semburan — itu sebabnya bingkai
      // pertama memakai opacity 0 dan isian mundurnya dikunci.
      delay: (tunda || 0) + Math.random() * 190,
      fill: 'backwards',
      easing: 'cubic-bezier(.16,.72,.4,1)',
    }).onfinish = () => el.remove();
  }
}

/* Kedua karakter menyemburkan pestanya sekaligus. Dipanggil tiap babak
   LEVEL UP dibuka, jadi penerima yang mundur lalu maju lagi tetap
   kebagian.

   Tiga letupan beruntun, bukan satu tumpahan besar: sekali semprot habis
   dalam sekejap dan yang tertinggal cuma kertas jatuh. Jeda 380 ms membuat
   semburan berikutnya berangkat waktu gelombang sebelumnya masih di puncak,
   jadi udaranya penuh terus selama babaknya dibaca. */
const LETUPAN = 3;
const ISI_LETUPAN = 16;
const JEDA_LETUPAN = 380;

function pestaBerdua(letupan) {
  if (!regu.length) return;
  const kali = letupan || LETUPAN;
  regu.forEach((t) => {
    const r = t.el.getBoundingClientRect();
    for (let n = 0; n < kali; n++) {
      pesta(r.left + r.width / 2, r.top + r.height * .3, ISI_LETUPAN, n * JEDA_LETUPAN);
    }
  });
}

/* ---------- berpelukan ----------
   Dipanggil tombol di babak WISHES. Mereka tidak langsung berpelukan di
   tempat — masing-masing BERJALAN saling mendekat dulu, lalu berhadapan.
   Itu syarat yang sama dengan aturan tidak boleh teleport: gerak yang tidak
   ditempuh tidak pernah terbaca sebagai gerak sungguhan.

   Titik temunya digeser ke kiri dari tengah karena tombol navigasi duduk di
   tengah bawah; berpelukan tepat di sana membuat mereka tertutup tombol. */
function peluk() {
  if (!regu.length) return;
  sentuhTerakhir = performance.now();
  memeluk = true;
  hatiPeluk = false;
  regu[0].pergiKe(W_KANVAS * .22 - LEBAR_TEMAN / 2);
  regu[1].pergiKe(W_KANVAS * .31 - LEBAR_TEMAN / 2);
  regu[0].kunci = 1;    // yang kiri menghadap kanan
  regu[1].kunci = -1;   // yang kanan menghadap kiri
  regu.forEach((t) => { t.laku = 'hug'; t.sekali = null; t.el.classList.add('merapat'); });
}

/* Hati baru muncul setelah keduanya benar-benar sampai dan berpelukan —
   kalau dipicu bersamaan dengan tombol, hatinya meletup di tempat kosong
   sementara mereka masih dalam perjalanan. */
function cekPeluk() {
  if (!memeluk || hatiPeluk) return;
  if (!regu.every((t) => Math.abs(t.x - t.tujuan) < 2)) return;
  hatiPeluk = true;
  const a = regu[0].el.getBoundingClientRect();
  const b = regu[1].el.getBoundingClientRect();
  hamburkan((a.right + b.left) / 2, a.top + a.height * .45, 10);
}

/* Dipanggil dari ke() tiap babak berganti. */
function temaniBabak(id) {
  if (!regu.length) return;
  const p = PANGGUNG[id] || PANGGUNG.powerups;
  sentuhTerakhir = performance.now();
  regu.forEach((t, i) => {
    t.pergiKe(W_KANVAS * p.x[i] - LEBAR_TEMAN / 2);
    // Titik pangkalnya diingat: di babak kue mereka maju-mundur dari sini,
    // dan tanpa catatan ini tidak ada tempat untuk kembali.
    t.pangkal = t.tujuan;
    t.laku = id === 'kue' && semuaPadam ? 'celebrate' : p.laku;
    t.sekali = null;
    t.kunci = p.hadap ? p.hadap[i] : null;
    t.el.classList.remove('merapat');
  });
  // Pindah babak membatalkan pelukan: mereka punya urusan lain di sana.
  memeluk = false;
  if (id !== 'kue') batalkanTiup();
}

/* ---------- TIUP LILIN ----------
   Ketuk api sebuah lilin, dan salah satu karakter MENGHAMPIRI lalu meniupnya.
   Bukan padam di tempat begitu diketuk: aturan yang dipegang sejak awal
   adalah mereka tidak boleh berpindah atau bertindak dari jarak jauh, dan
   nyala yang mati sendiri tanpa ada yang datang meniup membuat kedua
   karakter itu jadi hiasan, bukan pelaku.

   Antrean dipakai karena penerima pasti mengetuk beruntun. Tanpa antrean,
   ketukan kedua menyuruh karakter yang sama berbalik di tengah jalan dan
   dua tiupan saling memotong. */
const lilinSemua = [...document.querySelectorAll('.lilin')];
const panggungKue = document.querySelector('.kue-panggung');

function tundaTiup(fn, ms) {
  timerTiup.push(setTimeout(fn, ms));
}

function batalkanTiup() {
  timerTiup.forEach(clearTimeout);
  timerTiup = [];
  antreLilin = [];
  sedangTiup = false;
}

function ketukLilin(el) {
  if (el.classList.contains('padam') || antreLilin.includes(el)) return;
  sentuhTerakhir = performance.now();
  antreLilin.push(el);
  jalankanAntreLilin();
}

function jalankanAntreLilin() {
  if (sedangTiup) return;
  const el = antreLilin.shift();
  if (!el) return;
  if (el.classList.contains('padam')) return jalankanAntreLilin();

  // Tanpa karakter (mis. sprite gagal dimuat) lilinnya tetap harus bisa
  // padam — kalau tidak, babak ini jadi buntu total.
  if (!regu.length) {
    padamkanLilin(el);
    return jalankanAntreLilin();
  }

  sedangTiup = true;
  const t = regu[giliranTiup % regu.length];
  giliranTiup += 1;

  // Selangkah ke arah kue, bukan menyeberang: jaraknya pendek supaya lima
  // kali bolak-balik tidak terasa seperti menunggu. Sengaja cuma 18 piksel —
  // langkah yang lebih panjang membuat badan mereka menutupi kue, dan yang
  // sedang ditiup jadi tidak kelihatan.
  const maju = t === regu[0] ? 14 : -14;
  t.pergiKe(t.pangkal + maju);
  const tempuh = Math.abs(maju) / 104 * 1000 + 140;

  tundaTiup(() => {
    t.mainkan('blow', 780);
    // Apinya padam SESUDAH embusannya mulai, bukan bersamaan dengan langkah.
    tundaTiup(() => padamkanLilin(el), 280);
    tundaTiup(() => {
      t.pergiKe(t.pangkal);
      sedangTiup = false;
      tundaTiup(jalankanAntreLilin, 240);
    }, 800);
  }, tempuh);
}

function padamkanLilin(el) {
  if (el.classList.contains('padam')) return;
  el.classList.add('padam');
  asapLilin(el);
  if (lilinSemua.every((l) => l.classList.contains('padam'))) selesaiTiup();
}

/* Kepulan asap dari sumbu. Koordinatnya dibagi skala kartu dengan alasan yang
   sama seperti partikel lain — lihat catatan di skalaKartu(). */
function asapLilin(el) {
  if (kurangiGerak || !taman) return;
  const kotak = taman.getBoundingClientRect();
  const k = skalaKartu();
  const r = el.getBoundingClientRect();
  const x = (r.left + r.width / 2 - kotak.left) / k;
  const y = (r.top + r.height * .28 - kotak.top) / k;
  for (let i = 0; i < 5; i++) {
    const p = document.createElement('i');
    const sisi = 5 + Math.random() * 5;
    p.className = 'asap';
    p.style.cssText = 'position:absolute;width:' + sisi + 'px;height:' + sisi + 'px;' +
      'background:#cbb9c6;left:' + x + 'px;top:' + y + 'px;pointer-events:none';
    taman.appendChild(p);
    p.animate([
      { transform: 'translate(-50%,-50%) scale(.6)', opacity: .85 },
      {
        transform: 'translate(calc(-50% + ' + (Math.random() * 26 - 13) + 'px),' +
          'calc(-50% - ' + (34 + Math.random() * 30) + 'px)) scale(1.5)',
        opacity: 0,
      },
    ], { duration: 700 + Math.random() * 500, delay: i * 70, easing: 'steps(7, end)' })
      .onfinish = () => p.remove();
  }
}

function selesaiTiup() {
  semuaPadam = true;
  regu.forEach((t) => { t.laku = 'celebrate'; t.sekali = null; });
  pestaBerdua(LETUPAN);
  if (panggungKue) {
    const r = panggungKue.getBoundingClientRect();
    hamburkan(r.left + r.width / 2, r.top + r.height * .2, 12);
  }
}

/* Babak awal. Saat MENGEDIT, layar judul dilewati supaya pembeli tidak harus
   menekan START tiap kali pratinjau dimuat ulang. */
ke(document.body.classList.contains('is-editing') ? 1 : 0);
