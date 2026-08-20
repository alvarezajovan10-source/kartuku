/* Halaman 11 (surat "Letter For You"): teksnya tidak boleh keluar dari kotak
 * merah POLOS di dalam catatannya.
 *
 * Kenapa ini perlu pemeriksa sendiri, padahal cek_valentine.js sudah memotret
 * tiap halaman: yang gampang rusak di sini bukan posisi awalnya, melainkan
 * apa yang terjadi saat pembeli menulis panjang. Catatan merahnya digambar
 * sedikit miring, sudut kanan atas dan kiri bawahnya ditimpa selotip, dan dua
 * sudut sisanya punya goresan hias — jadi surat yang meluber tidak jatuh ke
 * kertas kosong, melainkan ke atas selotip, dan di potret sekilas itu terbaca
 * seperti "cuma agak turun".
 *
 * Angka POLOS di bawah bukan tebakan: itu keluaran tools/buat_pelat_hal11.py,
 * yang mencari persegi panjang terbesar yang seluruhnya merah catatan. Kalau
 * PDF-nya berganti, jalankan skrip itu lagi dan salin angkanya ke SINI juga.
 *
 * Jalankan:
 *   NODE_PATH=<node_modules berisi puppeteer-core>  *     node tools/cek_valentine_hal11.js <url-kartu> [folder-potret]
 */
const puppeteer = require('puppeteer-core');
const tidur = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = process.argv[3];

// Kotak merah POLOS, hasil ukur tools/buat_pelat_hal11.py (persen halaman).
const POLOS = { kiri: 12.732, atas: 28.775, lebar: 66.479, tinggi: 59.886 };

const PANJANG =
  'sayang, aku nggak pernah pandai merangkai kata, tapi malam ini aku mau coba. ' +
  'terima kasih sudah bertahan waktu aku lagi susah-susahnya, sudah mendengarkan ' +
  'cerita yang itu-itu saja tanpa pernah kelihatan bosan, dan sudah membuat hari ' +
  'yang biasa jadi terasa istimewa. aku ingin kamu tahu betapa dicintainya kamu, ' +
  'bukan cuma hari ini tapi setiap hari. kamu pantas mendapat dunia, dan aku tidak ' +
  'pernah mau kehilangan kamu. selamat hari jadi kita yang keempat, cintaku.';

(async () => {
  const b = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new', args: ['--no-sandbox'] });
  const p = await b.newPage();
  await p.setViewport({ width: 430, height: 860, deviceScaleFactor: 2 });
  const galat = [];
  p.on('pageerror', (e) => galat.push('[PAGEERROR] ' + e.message));
  await p.goto(process.argv[2], { waitUntil: 'networkidle2' });
  await p.evaluate(() => document.fonts.ready);
  await p.evaluate(() => window.show('hal11'));
  await tidur(400);

  const ukur = (label) => p.evaluate((POLOS) => {
    const H0 = 551.6, W0 = 390;
    const kertas = document.querySelector('#hal11 .kertas').getBoundingClientRect();
    const sk = kertas.height / H0;
    const kotak = {
      kiri: POLOS.kiri / 100 * W0, atas: POLOS.atas / 100 * H0,
      kanan: (POLOS.kiri + POLOS.lebar) / 100 * W0,
      bawah: (POLOS.atas + POLOS.tinggi) / 100 * H0,
    };
    const out = { kotakPolos: kotak, teks: {} };
    ['t-wish', 't-pesan'].forEach((k) => {
      const el = document.querySelector('#hal11 .' + k);
      const r = el.getBoundingClientRect();
      const lokal = {
        kiri: +((r.left - kertas.left) / sk).toFixed(1),
        atas: +((r.top - kertas.top) / sk).toFixed(1),
        kanan: +((r.right - kertas.left) / sk).toFixed(1),
        bawah: +((r.bottom - kertas.top) / sk).toFixed(1),
      };
      out.teks[k] = { ...lokal,
        muat: +(parseFloat(getComputedStyle(el).getPropertyValue('--muat')) || 1).toFixed(3),
        baris: Math.round(r.height / (parseFloat(getComputedStyle(el).lineHeight) )),
      };
    });
    return out;
  }, POLOS);

  const lapor = async (label) => {
    const u = await ukur();
    const k = u.kotakPolos;
    const t = u.teks['t-pesan'];
    const di = t.kiri >= k.kiri - 0.5 && t.kanan <= k.kanan + 0.5 &&
               t.atas >= k.atas - 0.5 && t.bawah <= k.bawah + 0.5;
    console.log(`${label}`);
    console.log(`  kotak merah polos : kiri ${k.kiri.toFixed(1)} atas ${k.atas.toFixed(1)} kanan ${k.kanan.toFixed(1)} bawah ${k.bawah.toFixed(1)}`);
    console.log(`  .t-pesan          : kiri ${t.kiri} atas ${t.atas} kanan ${t.kanan} bawah ${t.bawah}  (${t.baris} baris, --muat ${t.muat})`);
    console.log(`  di dalam kotak    : ${di ? 'YA' : 'TIDAK — MELUBER'}`);
    const w = u.teks['t-wish'];
    console.log(`  .t-wish           : kiri ${w.kiri} atas ${w.atas} kanan ${w.kanan} bawah ${w.bawah} (${w.baris} baris, --muat ${w.muat})`);
    return di;
  };

  const ok1 = await lapor('BAWAAN');
  if (OUT) { const el = await p.$('#card-stage'); await el.screenshot({ path: `${OUT}/hal11-bawaan.png` }); }

  await p.evaluate((t) => { document.querySelector('#hal11 .t-pesan').textContent = t; }, PANJANG);
  await tidur(400);
  const ok2 = await lapor('\nSURAT PANJANG (' + PANJANG.length + ' huruf)');
  if (OUT) { const el = await p.$('#card-stage'); await el.screenshot({ path: `${OUT}/hal11-panjang.png` }); }

  await p.evaluate(() => { document.querySelector('#hal11 .t-wish').textContent = 'Surat Untuk Kamu, Sayangku'; });
  await tidur(400);
  const ok3 = await lapor('\nJUDUL PANJANG');
  if (OUT) { const el = await p.$('#card-stage'); await el.screenshot({ path: `${OUT}/hal11-judul.png` }); }

  console.log('\nerror:', galat.length ? galat.join('\n  ') : '(bersih)');
  console.log('HASIL:', ok1 && ok2 && ok3 ? 'LULUS' : 'GAGAL');
  await b.close();
})();
