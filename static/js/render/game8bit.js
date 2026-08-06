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
  timerLevel = setTimeout(() => {
    popLevel.classList.add('meletup');
    const r = popLevel.getBoundingClientRect();
    hamburkan(r.left + r.width / 2, r.top + r.height / 2, 12);
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

/* Babak awal. Saat MENGEDIT, layar judul dilewati supaya pembeli tidak harus
   menekan START tiap kali pratinjau dimuat ulang. */
ke(document.body.classList.contains('is-editing') ? 1 : 0);
