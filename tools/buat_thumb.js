/* Pemotret sampul template untuk thumbnail beranda.
 *
 * Memotret HALAMAN PERTAMA tiap template — sampul yang dilihat penerima saat
 * kartu baru dibuka, bukan potongan tengah.
 *
 * Yang dibuang sebelum memotret: bilah pratinjau, tombol lagu + catatannya,
 * tombol layar penuh, pager halaman, dan petunjuk "geser". Semuanya perkakas
 * pembaca, bukan bagian kartu — kalau ikut terpotret, thumbnailnya terlihat
 * seperti tangkapan layar aplikasi, bukan seperti kartunya sendiri.
 *
 * Dua cara memotret, dipilih dari bentuk kartunya:
 *   "elemen"   — potret #card-stage persis di batasnya. Untuk kartu yang muat
 *                utuh di layar (stage "lebar" dan "buku"); tanpa ini tepinya
 *                kebagian latar gelap kosong yang lebar.
 *   "viewport" — potret layar apa adanya. Untuk stage "flow" yang halamannya
 *                bergulir: batas elemennya setinggi SELURUH gulungan, jadi
 *                memotret elemen justru menghasilkan pita panjang.
 *
 * Lily sengaja tidak ada di daftar — masih tahap pengembangan, belum deploy.
 *
 * Jalankan:
 *   NODE_PATH=<node_modules> node tools/buat_thumb.js <base-url> <folder-keluaran>
 */
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

const BASE = process.argv[2] || 'http://127.0.0.1:8009';
const OUT = process.argv[3] || '/tmp/thumb';

const TEMPLATES = [
  { slug: 'game-8bit',        lebar: 1600, tinggi: 900,  cara: 'elemen'   },
  { slug: 'valentine-story',  lebar: 900,  tinggi: 1200, cara: 'elemen'   },
  // Stage "flow": lebar kanonis kartu 390px. Viewport dibuat sedikit lebih
  // lebar saja — dilebarkan sampai 900px, kartunya tetap 390px dan sisanya
  // jadi latar kosong.
  { slug: 'scrapbook-cerita', lebar: 480,  tinggi: 900,  cara: 'viewport',
    fokus: '.cover-card', rasio: 3 / 4 },
];

const BUANG = [
  '.preview-bar', '#bgm', '.bgm-fab', '.bgm-note', '.fs-fab',
  'nav.nav', '#petunjuk', '.scroll-hint',
].join(',');

const tidur = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
  });

  for (const t of TEMPLATES) {
    const page = await browser.newPage();
    await page.setViewport({ width: t.lebar, height: t.tinggi, deviceScaleFactor: 3 });
    await page.goto(`${BASE}/preview/${t.slug}/`, { waitUntil: 'networkidle0', timeout: 60000 });
    await page.addStyleTag({ content: `${BUANG}{display:none !important}` });
    await page.evaluate(() => document.fonts && document.fonts.ready);
    await tidur(2500);

    const berkas = path.join(OUT, `${t.slug}.png`);
    if (t.cara === 'elemen') {
      const stage = await page.$('#card-stage');
      if (!stage) throw new Error(`${t.slug}: #card-stage tidak ditemukan`);
      await stage.screenshot({ path: berkas, type: 'png' });
    } else {
      // Sampul stage "flow" duduk di bawah layar dengan ruang kosong lebar di
      // atasnya — benar di HP, timpang sebagai thumbnail. Kalau `fokus` diisi,
      // bidik kotak `rasio` yang berpusat di elemen itu.
      const clip = t.fokus
        ? await page.evaluate((sel, rasio) => {
            const el = document.querySelector(sel);
            if (!el) return null;
            const r = el.getBoundingClientRect();
            const tengahY = r.top + r.height / 2;
            const w = window.innerWidth;
            const h = Math.round(w / rasio);
            // Jepit ke dalam viewport: kotak yang menggantung di luar layar
            // membuat Chrome memotret pita hitam.
            const y = Math.max(0, Math.min(window.innerHeight - h, Math.round(tengahY - h / 2)));
            return { x: 0, y, width: w, height: h };
          }, t.fokus, t.rasio)
        : null;
      if (t.fokus && !clip) throw new Error(`${t.slug}: fokus ${t.fokus} tidak ditemukan`);
      await page.screenshot({ path: berkas, type: 'png', ...(clip ? { clip } : {}) });
    }

    const info = await page.evaluate(() => document.documentElement.dataset.stage || '?');
    console.log(`${t.slug}  stage=${info}  cara=${t.cara}  → ${berkas}`);
    await page.close();
  }

  await browser.close();
})();
