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

/* ---------- hati piksel yang berhamburan ---------- */
function hamburkan(x, y, jumlah) {
  if (kurangiGerak || !taman) return;
  const kotak = taman.getBoundingClientRect();
  for (let i = 0; i < jumlah; i++) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    el.setAttribute('viewBox', '0 0 9 8');
    el.innerHTML = '<use href="#s-hati"/>';
    const ukuran = 18 + Math.random() * 22;
    el.style.cssText =
      'position:absolute;width:' + ukuran + 'px;height:' + ukuran + 'px;' +
      'left:' + (x - kotak.left) + 'px;top:' + (y - kotak.top) + 'px;' +
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

/* ---------- layar judul ---------- */
const startBtn = document.getElementById('startBtn');
if (startBtn) {
  startBtn.addEventListener('click', (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    hamburkan(r.left + r.width / 2, r.top + r.height / 2, 10);
    ke(1);
  });
}

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
  // Semburan pertama begitu babaknya dibuka: karakternya yang memulai
  // pesta, bar XP-nya menyusul.
  pestaBerdua();
  timerLevel = setTimeout(() => {
    popLevel.classList.add('meletup');
    const r = popLevel.getBoundingClientRect();
    hamburkan(r.left + r.width / 2, r.top + r.height / 2, 12);
    pestaBerdua();
  }, 1150);
}

/* ---------- ubin power-up ---------- */
document.querySelectorAll('#kisi .ubin').forEach((ubin) => {
  ubin.addEventListener('click', (e) => {
    if (ubin.classList.contains('terbuka')) return;
    ubin.classList.add('terbuka');
    const r = ubin.getBoundingClientRect();
    hamburkan(r.left + r.width / 2, r.top + r.height / 2, 4);
  });
});

/* ---------- main lagi ---------- */
const ulangBtn = document.getElementById('ulangBtn');
if (ulangBtn) {
  ulangBtn.addEventListener('click', () => {
    document.querySelectorAll('#kisi .ubin').forEach((u) => u.classList.remove('terbuka'));
    ke(0);
  });
}

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
  scores:      { x: [.10, .88], laku: 'happy' },
  gameover:    { x: [.25, .71], laku: 'celebrate' },
};

const JEDA_TIDUR = 20000;      // diam selama ini -> mereka ketiduran

function Teman(el, mula) {
  this.el = el;
  this.sprite = el.querySelector('.sprite');
  this.x = mula;
  this.tujuan = mula;
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
    const lari = jarak > 300;
    const laju = (lari ? 210 : 96) * dt;
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
})();

/* ---------- pesta meriah ----------
   Kertas warna yang disemburkan kedua karakter LURUS KE ATAS, lalu jatuh
   melebar. Bukan meletup ke segala arah: yang menyemburkan adalah karakter
   di lantai, jadi arah naik itulah yang membuatnya terbaca datang dari
   mereka, bukan muncul begitu saja di udara. */
const WARNA_PESTA = ['#ffd23f', '#ff6bb5', '#a8e6cf', '#b9a5e3', '#ffffff', '#ff2d8a'];

function pesta(x, y, jumlah) {
  if (kurangiGerak || !taman) return;
  const kotak = taman.getBoundingClientRect();
  for (let i = 0; i < jumlah; i++) {
    const el = document.createElement('i');
    const sisi = 5 + Math.floor(Math.random() * 6);
    el.style.cssText =
      'position:absolute;width:' + sisi + 'px;height:' + (sisi + Math.round(Math.random() * 4)) + 'px;' +
      'background:' + WARNA_PESTA[i % WARNA_PESTA.length] + ';' +
      'left:' + (x - kotak.left) + 'px;top:' + (y - kotak.top) + 'px;pointer-events:none';
    taman.appendChild(el);

    const miring = (Math.random() - .5) * 150;   // sebaran mendatar saat naik
    const tinggi = 190 + Math.random() * 200;
    el.animate([
      { transform: 'translate(-50%,-50%) scale(.4) rotate(0deg)', opacity: 1 },
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
      easing: 'cubic-bezier(.16,.72,.4,1)',
    }).onfinish = () => el.remove();
  }
}

/* Kedua karakter menyemburkan pestanya sekaligus. Dipanggil tiap babak
   LEVEL UP dibuka, jadi penerima yang mundur lalu maju lagi tetap
   kebagian. */
function pestaBerdua() {
  if (!regu.length) return;
  regu.forEach((t) => {
    const r = t.el.getBoundingClientRect();
    pesta(r.left + r.width / 2, r.top + r.height * .3, 16);
  });
}

/* ---------- berpelukan ----------
   Dipanggil tombol di babak WISHES. Mereka tidak langsung berpelukan di
   tempat — masing-masing BERJALAN saling mendekat dulu, lalu berhadapan.
   Itu syarat yang sama dengan aturan tidak boleh teleport: gerak yang tidak
   ditempuh tidak pernah terbaca sebagai gerak sungguhan.

   Titik temunya digeser ke kiri dari tengah karena tombol navigasi duduk di
   tengah bawah; berpelukan tepat di sana membuat mereka tertutup tombol. */
let memeluk = false;
let hatiPeluk = false;

function peluk() {
  if (!regu.length) return;
  sentuhTerakhir = performance.now();
  memeluk = true;
  hatiPeluk = false;
  regu[0].tujuan = W_KANVAS * .22 - LEBAR_TEMAN / 2;
  regu[1].tujuan = W_KANVAS * .31 - LEBAR_TEMAN / 2;
  regu[0].kunci = 1;    // yang kiri menghadap kanan
  regu[1].kunci = -1;   // yang kanan menghadap kiri
  regu.forEach((t) => { t.laku = 'hug'; t.sekali = null; });
}

const pelukBtn = document.getElementById('pelukBtn');
if (pelukBtn) pelukBtn.addEventListener('click', peluk);

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
    t.tujuan = W_KANVAS * p.x[i] - LEBAR_TEMAN / 2;
    t.laku = p.laku;
    t.sekali = null;
    t.kunci = null;
  });
  // Pindah babak membatalkan pelukan: mereka punya urusan lain di sana.
  memeluk = false;
}

/* Babak awal. Saat MENGEDIT, layar judul dilewati supaya pembeli tidak harus
   menekan START tiap kali pratinjau dimuat ulang. */
ke(document.body.classList.contains('is-editing') ? 1 : 0);
