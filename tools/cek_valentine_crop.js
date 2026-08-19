/* Kotak crop harus berbentuk sama dengan bingkai tujuannya, dan cukup besar.
 *
 * Dulu kanvasnya selalu 640x640. Dua akibatnya tidak pernah memunculkan
 * error: pembeli memilih bagian foto di bentuk yang bukan bentuk
 * tampilannya, dan hasil potongannya tidak pernah lebih dari 640 px —
 * itulah kenapa foto sampul yang memenuhi satu halaman terlihat pecah.
 */
const puppeteer = require('puppeteer-core');
const tidur = (ms) => new Promise((r) => setTimeout(r, ms));

// slot -> [rasio bingkai, sisi panjang minimum yang diharapkan]
const HARAP = { f_sampul: [0.707, 2000], f_pita1: [1.4726, 1000], f_klip1: [0.847, 1000] };

(async () => {
  const b = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new', args: ['--no-sandbox'],
  });
  const p = await b.newPage();
  await p.setViewport({ width: 1440, height: 940 });
  const err = [];
  p.on('pageerror', (e) => err.push(e.message));
  await p.goto('http://localhost:8000/create/valentine-story/', { waitUntil: 'networkidle2' });
  await tidur(3000);

  // Foto uji besar dibuat di browser, jadi tidak perlu berkas di disk.
  const hasil = {};
  for (const slot of Object.keys(HARAP)) {
    const ukuran = await p.evaluate(async (s) => {
      const d = Alpine.$data(document.querySelector('[x-data]'));
      const c = document.createElement('canvas');
      c.width = 3000; c.height = 2000;
      const x = c.getContext('2d');
      x.fillStyle = '#c33'; x.fillRect(0, 0, 3000, 2000);
      const blob = await new Promise((r) => c.toBlob(r, 'image/jpeg', .9));
      d.cropQueue.push({ file: new File([blob], 'uji.jpg', { type: 'image/jpeg' }), slot: s });
      d.nextCrop();
      await new Promise((r) => setTimeout(r, 900));
      const k = document.querySelector('[x-ref=cropCanvas]');
      const out = { w: k.width, h: k.height, terbuka: d.cropOpen };
      d.cancelCrop();
      return out;
    }, slot);
    await tidur(400);
    hasil[slot] = ukuran;
  }

  console.log(JSON.stringify(hasil, null, 1));
  const lulus = [];
  for (const [slot, [rasio, minSisi]] of Object.entries(HARAP)) {
    const u = hasil[slot];
    const r = u.w / u.h;
    lulus.push([`${slot}: bentuk kotak = bentuk bingkai`, Math.abs(r - rasio) < 0.02]);
    lulus.push([`${slot}: sisi panjang >= ${minSisi}px`, Math.max(u.w, u.h) >= minSisi]);
  }
  console.log();
  lulus.forEach(([n, ok]) => console.log(`${ok ? ' OK ' : 'GAGAL'}  ${n}`));
  console.log('\nerror:', err.length ? err.join('; ') : '(bersih)');
  await b.close();
  process.exit(lulus.every(([, ok]) => ok) ? 0 : 1);
})();
