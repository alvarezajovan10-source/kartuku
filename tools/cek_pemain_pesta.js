/* Uji dua revisi: potret 1P/2P terkunci (bukan slot foto), dan semburan
   pesta di LEVEL UP jauh lebih banyak. */
const puppeteer = require('puppeteer-core');
const OUT = '/private/tmp/claude-501/-Users-jepa-giftcard/5d310635-ee87-43cc-809d-6267459f0afe/scratchpad/8bit';
const tidur = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new', args: ['--no-sandbox'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  const catatan = [];
  page.on('pageerror', (e) => catatan.push('[PAGEERROR] ' + e.message));
  page.on('requestfailed', (r) => catatan.push('[GAGAL] ' + r.url() + ' ' + (r.failure() || {}).errorText));

  const url = process.argv[2] || 'http://localhost:8000/preview/game-8bit/';
  await page.goto(url, { waitUntil: 'networkidle2' });
  await tidur(600);

  // ---- 1. PLAYER SELECT ----
  await page.evaluate(() => window.show('player'));
  await tidur(700);
  const pemain = await page.evaluate(() => {
    const scene = document.getElementById('player');
    const stage = document.getElementById('card-stage').getBoundingClientRect();
    const tokoh = [...scene.querySelectorAll('.tokoh')];
    return {
      slotFotoTersisa: scene.querySelectorAll('[data-frame]').length,
      jumlahPotret: tokoh.length,
      gambar: tokoh.map((t) => {
        const g = getComputedStyle(t);
        return {
          berkas: (g.backgroundImage.match(/8bit-\w+\.png/) || ['TIDAK ADA'])[0],
          piksel: g.imageRendering,
          ukuran: g.width + 'x' + g.height,
        };
      }),
      // Semua isi halaman harus tetap di dalam kartu.
      diDalamKartu: [...scene.querySelectorAll('.slot, .kepala')].every((el) => {
        const r = el.getBoundingClientRect();
        return r.top >= stage.top - 1 && r.bottom <= stage.bottom + 1;
      }),
    };
  });
  await page.screenshot({ path: `${OUT}/uji-player.png` });

  // ---- 2. LEVEL UP ----
  await page.evaluate(() => window.show('title'));
  await tidur(300);
  await page.evaluate(() => window.show('levelup'));
  const puncak = [];
  for (let i = 0; i < 22; i++) {
    puncak.push(await page.evaluate(() => document.getElementById('taman').childElementCount));
    await tidur(180);
  }
  await page.evaluate(() => window.show('levelup'));
  await tidur(1500);
  await page.screenshot({ path: `${OUT}/uji-levelup-baru.png` });
  const jenis = await page.evaluate(() => {
    const anak = [...document.getElementById('taman').children];
    return {
      kertas: anak.filter((e) => e.tagName === 'I').length,
      lambang: anak.filter((e) => e.tagName.toLowerCase() === 'svg')
        .map((e) => (e.innerHTML.match(/#s-\w+/) || [''])[0]),
    };
  });

  console.log('PLAYER SELECT :', JSON.stringify(pemain, null, 1));
  console.log('partikel tiap 180ms:', JSON.stringify(puncak));
  console.log('puncak partikel    :', Math.max(...puncak));
  console.log('jenis butir        :', JSON.stringify(jenis));
  console.log('error browser      :', catatan.length ? catatan.join('\n') : '(bersih)');
  await browser.close();
})();
