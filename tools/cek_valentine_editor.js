/* Uji editor untuk Valentine Story.
 *
 * Yang paling mudah rusak di template ini: fotonya ada DI BELAKANG pelat
 * gambar. Kalau lapisan ketuknya salah taruh, klik bingkai foto ditelan
 * pelat dan pembeli tidak pernah bisa mengganti fotonya — tanpa pesan
 * error apa pun. Jadi yang diuji bukan "halaman terbuka", melainkan
 * klik demi klik.
 */
const puppeteer = require('puppeteer-core');

const SLUG = process.argv[2] || 'valentine-story';
const ASAL = process.argv[3] || 'http://localhost:8000';
const tidur = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new', args: ['--no-sandbox', '--window-size=1440,940'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 940 });
  const catatan = [];
  page.on('pageerror', (e) => catatan.push(`[PAGEERROR] ${e.message}`));
  page.on('console', (m) => { if (m.type() === 'error') catatan.push(`[error] ${m.text()}`); });

  await page.goto(`${ASAL}/create/${SLUG}/`, { waitUntil: 'networkidle2' });
  await tidur(2500);

  const bingkai = await page.frames().find((f) => f.url().includes('/frame/'));
  if (!bingkai) { console.log('GAGAL: iframe preview tidak ketemu'); process.exit(1); }
  await tidur(1200);

  const hasil = {};
  hasil.babakTerbaca = await page.evaluate(() =>
    [...document.querySelectorAll('[x-model="currentScene"] option, .ed-scene option')]
      .map((o) => o.textContent.trim()).slice(0, 12));

  // 1. klik teks -> panel teks terbuka
  await bingkai.click('.t-mast');
  await tidur(600);
  hasil.pilihTeks = await page.evaluate(() => {
    const el = document.querySelector('.ed-input');
    return { terlihat: !!el && el.offsetParent !== null, isi: el ? el.value : null };
  });

  // 2. klik bingkai foto -> panel foto terbuka (BUKAN tertelan pelat)
  await bingkai.evaluate(() => window.show('hal7'));
  await tidur(400);
  await bingkai.click('[data-frame="f_liontin_a"] .ketuk');
  await tidur(600);
  hasil.pilihFoto = await bingkai.evaluate(() => {
    const el = document.querySelector('.is-selected');
    return el ? (el.dataset.frame || el.dataset.edit || '') : null;
  });

  // 3. tiap bingkai bisa diklik, satu per satu
  const kunci = await bingkai.evaluate(() =>
    [...document.querySelectorAll('[data-frame]')].map((e) => e.dataset.frame));
  const gagalKlik = [];
  for (const k of kunci) {
    // Halaman yang memuatnya harus dibuka dulu. Bingkai di halaman lain
    // memang tertutup halaman yang sedang dibaca — itu benar, bukan bug.
    await bingkai.evaluate((x) => {
      const el = document.querySelector(`[data-frame="${x}"]`);
      window.show(el.closest('.lembar').id);
    }, k);
    await tidur(160);
    await bingkai.click(`[data-frame="${k}"] .ketuk`);
    await tidur(160);
    const terpilih = await bingkai.evaluate((x) =>
      document.querySelector(`[data-frame="${x}"]`).classList.contains('is-selected'), k);
    if (!terpilih) gagalKlik.push(k);
  }
  hasil.bingkaiTotal = kunci.length;
  hasil.bingkaiGagalDiklik = gagalKlik;

  // 4. tiap teks bisa diklik
  const kunciTeks = await bingkai.evaluate(() =>
    [...document.querySelectorAll('[data-edit]')].map((e) => e.dataset.edit));
  const gagalTeks = [];
  for (const k of kunciTeks) {
    await bingkai.evaluate((x) => {
      const el = document.querySelector(`[data-edit="${x}"]`);
      el.closest('.lembar') && window.show(el.closest('.lembar').id);
    }, k);
    await tidur(120);
    await bingkai.click(`[data-edit="${k}"]`);
    await tidur(140);
    const ok = await bingkai.evaluate((x) =>
      document.querySelector(`[data-edit="${x}"]`).classList.contains('is-selected'), k);
    if (!ok) gagalTeks.push(k);
  }
  hasil.teksTotal = kunciTeks.length;
  hasil.teksGagalDiklik = gagalTeks;

  // 5. mengetik teks langsung terlihat di preview
  await bingkai.evaluate(() => window.show('hal1'));
  await bingkai.click('[data-edit="mast"]');
  await tidur(400);
  await page.evaluate(() => {
    const el = document.querySelector('.ed-input');
    el.value = 'CERITA KITA';
    el.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await tidur(700);
  hasil.teksIkutBerubah = await bingkai.evaluate(() =>
    document.querySelector('[data-edit="mast"]').textContent.trim());

  // 6. lompat halaman dari panel
  await bingkai.evaluate(() => window.show('hal7'));
  await tidur(500);
  hasil.lompatHalaman = await bingkai.evaluate(() =>
    document.querySelector('.scene.active')?.id);

  await page.screenshot({ path: '/tmp/valentine-editor.png' });
  console.log(JSON.stringify(hasil, null, 1));
  const lulus = [
    ['klik teks membuka panel', hasil.pilihTeks.terlihat],
    ['klik bingkai foto terbaca', hasil.pilihFoto === 'f_liontin_a'],
    ['semua bingkai foto bisa diklik', hasil.bingkaiGagalDiklik.length === 0],
    ['semua teks bisa diklik', hasil.teksGagalDiklik.length === 0],
    ['ketikan langsung tampil', hasil.teksIkutBerubah === 'CERITA KITA'],
    ['lompat halaman jalan', hasil.lompatHalaman === 'hal7'],
  ];
  console.log();
  lulus.forEach(([n, ok]) => console.log(`${ok ? ' OK ' : 'GAGAL'}  ${n}`));
  console.log('\nerror:', catatan.length ? '\n  ' + catatan.join('\n  ') : '(bersih)');
  await browser.close();
  process.exit(lulus.every(([, ok]) => ok) ? 0 : 1);
})();
