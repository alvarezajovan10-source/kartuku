/* Buka kartu di Chrome sungguhan, kumpulkan error, klik tombolnya, foto. */
const puppeteer = require('puppeteer-core');

const URL = process.argv[2] || 'http://localhost:8000/preview/game-8bit/';
const OUT = process.argv[3] || '/private/tmp/claude-501/-Users-jepa-giftcard/5d310635-ee87-43cc-809d-6267459f0afe/scratchpad/8bit';

const tidur = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox', '--window-size=1440,900'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  const catatan = [];
  page.on('console', (m) => catatan.push(`[${m.type()}] ${m.text()}`));
  page.on('pageerror', (e) => catatan.push(`[PAGEERROR] ${e.message}`));
  page.on('requestfailed', (r) => catatan.push(`[GAGAL] ${r.url()} ${r.failure()?.errorText}`));

  await page.goto(URL, { waitUntil: 'networkidle2' });
  await tidur(600);

  const info = await page.evaluate(() => ({
    k: getComputedStyle(document.documentElement).getPropertyValue('--k').trim(),
    babak: [...document.querySelectorAll('.scene')].map((s) => s.id),
    aktif: document.querySelector('.scene.active')?.id,
    teman: document.querySelectorAll('.teman').length,
    pelukAda: !!document.getElementById('pelukBtn'),
    namaSumber: document.getElementById('nama1p')?.textContent,
    namaPapan: document.getElementById('namaCowok')?.textContent,
    fungsi: {
      peluk: typeof peluk, pestaBerdua: typeof pestaBerdua,
      hamburkan: typeof hamburkan, ke: typeof ke,
    },
  }));
  console.log('INFO', JSON.stringify(info, null, 1));

  // ---- uji LEVEL UP ----
  await page.evaluate(() => window.show('levelup'));
  await tidur(1400);
  const pestaKeluar = await page.evaluate(() => document.getElementById('taman').childElementCount);
  await page.screenshot({ path: `${OUT}/uji-levelup.png` });

  // ---- uji HUG ----
  await page.evaluate(() => window.show('wishes'));
  await tidur(700);
  const posAwal = await page.evaluate(() => [...document.querySelectorAll('.teman')].map((t) => t.style.getPropertyValue('--x')));
  await page.click('#pelukBtn').catch((e) => catatan.push('[KLIK GAGAL] ' + e.message));
  await tidur(4200);
  const posAkhir = await page.evaluate(() => [...document.querySelectorAll('.teman')].map((t) => ({
    x: t.style.getPropertyValue('--x'),
    baris: t.querySelector('.sprite').style.backgroundPositionY,
  })));
  await page.screenshot({ path: `${OUT}/uji-hug.png` });

  // Uji penyalin nama: tiru persis yang dilakukan editor pada elemen sumber.
  const namaUji = await page.evaluate(async () => {
    document.getElementById('nama1p').textContent = 'Jepa';
    document.getElementById('nama2p').textContent = 'Valen';
    await new Promise((r) => setTimeout(r, 120));
    return [document.getElementById('namaCowok').textContent,
            document.getElementById('namaCewek').textContent];
  });
  console.log('nama papan setelah diubah:', JSON.stringify(namaUji));
  console.log('taman setelah level up (jumlah partikel):', pestaKeluar);
  console.log('posisi sebelum hug:', JSON.stringify(posAwal));
  console.log('posisi sesudah hug:', JSON.stringify(posAkhir));
  console.log('--- catatan browser ---');
  console.log(catatan.length ? catatan.join('\n') : '(bersih, tidak ada error)');

  await browser.close();
})();
