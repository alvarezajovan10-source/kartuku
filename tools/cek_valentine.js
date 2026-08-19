/* Kalibrasi & pemeriksa template Valentine Story.
 *
 * Teks HTML di template ini duduk di atas pelat gambar yang posisinya mati.
 * Meleset dua-tiga piksel saja sudah terlihat sebagai teks yang "tidak
 * menempel". Skrip ini mengukur di Chrome SUNGGUHAN di mana garis alas huruf
 * benar-benar jatuh, lalu menghitung berapa --asc yang seharusnya dipakai —
 * jadi angkanya diukur, bukan ditebak.
 *
 * Jalankan:
 *   NODE_PATH=<node_modules> node tools/cek_valentine.js <url> <folder-keluaran>
 */
const fs = require('fs');
const puppeteer = require('puppeteer-core');

const URL = process.argv[2] || 'http://localhost:8000/g/uji-valentine/';
const OUT = process.argv[3] || '/tmp/valentine';
const LEBAR = Number(process.argv[4] || 430);
const TINGGI = Number(process.argv[5] || 860);

const tidur = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox', `--window-size=${LEBAR},${TINGGI}`],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: LEBAR, height: TINGGI, deviceScaleFactor: 2 });

  const catatan = [];
  page.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') catatan.push(`[${m.type()}] ${m.text()}`); });
  page.on('pageerror', (e) => catatan.push(`[PAGEERROR] ${e.message}`));
  page.on('requestfailed', (r) => catatan.push(`[GAGAL] ${r.url()} ${r.failure()?.errorText}`));

  await page.goto(URL, { waitUntil: 'networkidle2' });
  await page.evaluate(() => document.fonts.ready);
  await tidur(500);

  const ukur = await page.evaluate(() => {
    const H0 = 551.6;
    const hasil = [];
    document.querySelectorAll('.tx').forEach((el) => {
      const kertas = el.closest('.kertas').getBoundingClientRect();

      // Teks bertanda data-tengah TIDAK digantung pada garis alas: ia
      // dipusatkan di dalam bentuk (elips halaman 10). Mengukur garis
      // alasnya di sini akan selalu melaporkan "meleset" padahal justru
      // itu yang benar — jadi yang diukur titik tengah tegaknya, terhadap
      // titik tengah elips yang ditulis di CSS `top`. Ukuran yang berbeda,
      // ketelitian yang sama.
      if (el.hasAttribute('data-tengah')) {
        const kotak = el.getBoundingClientRect();
        const skala0 = kertas.height / H0;
        const tengah = (kotak.top + kotak.height / 2 - kertas.top) / skala0;
        const sasaran = parseFloat(getComputedStyle(el).top);
        hasil.push({
          kelas: [...el.classList].filter((c) => /^t-\w+\d$/.test(c))[0] || el.className,
          font: getComputedStyle(el).fontFamily.split(',')[0].replace(/["']/g, ''),
          halaman: el.closest('.lembar').id,
          ukuran: 'tengah',
          target: +sasaran.toFixed(2),
          nyata: +tengah.toFixed(2),
          selisih: +(tengah - sasaran).toFixed(2),
          fontPx: +parseFloat(getComputedStyle(el).fontSize).toFixed(2),
          jb: +(parseFloat(getComputedStyle(el).lineHeight) / parseFloat(getComputedStyle(el).fontSize)).toFixed(3),
          cfSeharusnya: null,
        });
        return;
      }

      // Elemen sebaris setinggi nol dengan vertical-align:baseline: tepi
      // bawahnya PERSIS di garis alas huruf baris pertama. Ini satu-satunya
      // cara mengukur garis alas dari DOM tanpa menebak metrik font.
      const sasaranEl = el.matches('.t-body4') ? el.querySelector('p') : el;
      const probe = document.createElement('span');
      probe.style.cssText = 'display:inline-block;width:0;height:0;vertical-align:baseline';
      sasaranEl.insertBefore(probe, sasaranEl.firstChild);
      const alas = probe.getBoundingClientRect().bottom;
      probe.remove();

      const skala = kertas.height / H0;
      const g = getComputedStyle(el);
      const fs = parseFloat(g.fontSize);
      const jb = parseFloat(g.lineHeight) / parseFloat(g.fontSize);
      const asc = jb / 2 + (parseFloat(g.getPropertyValue('--cf')) || 0);
      const target = parseFloat(g.top);              // px lokal, dari CSS
      const nyata = (alas - kertas.top) / skala;     // px lokal, terukur

      hasil.push({
        kelas: [...el.classList].filter((c) => c.startsWith('t-'))[0] || el.className,
        font: g.fontFamily.split(',')[0].replace(/["']/g, ''),
        halaman: el.closest('.lembar').id,
        target: +target.toFixed(2),
        nyata: +nyata.toFixed(2),
        selisih: +(nyata - target).toFixed(2),
        fontPx: +fs.toFixed(2),
        jb: +jb.toFixed(3),
        // --cf yang seharusnya: buang lagi suku half-leading, sisanya
        // murni sifat font dan harus sama untuk semua teks berfont sama.
        cfSeharusnya: +(asc + (nyata - target) / fs - jb / 2).toFixed(4),
      });
    });
    return hasil;
  });

  const perFont = {};
  ukur.forEach((u) => {
    // Teks yang dipusatkan tidak punya --cf untuk dirata-ratakan.
    if (u.cfSeharusnya === null) return;
    (perFont[u.font] = perFont[u.font] || []).push(u.cfSeharusnya);
  });

  const rangkum = await page.evaluate(() => ({
    k: getComputedStyle(document.documentElement).getPropertyValue('--k').trim(),
    babak: [...document.querySelectorAll('.scene')].map((s) => s.id),
    aktif: document.querySelector('.scene.active')?.id,
    dekat: [...document.querySelectorAll('.lembar.dekat')].map((s) => s.id),
    bingkai: document.querySelectorAll('.bingkai').length,
    teks: document.querySelectorAll('.tx').length,
  }));

  console.log('RINGKAS', JSON.stringify(rangkum));
  console.log('\nGARIS ALAS (px lokal; selisih 0 = tepat di atas pelatnya)');
  console.log('  baris bertanda [tengah] diukur dari titik tengah, bukan garis alas');
  ukur.forEach((u) => {
    const tanda = Math.abs(u.selisih) < 0.6 ? '  ' : '!!';
    const cf = u.cfSeharusnya === null ? '[tengah]' : `cf→${u.cfSeharusnya}`;
    console.log(`${tanda} ${u.halaman.padEnd(6)} ${u.kelas.padEnd(12)} ${u.font.padEnd(14)} target=${String(u.target).padStart(7)} nyata=${String(u.nyata).padStart(7)} selisih=${String(u.selisih).padStart(6)}  ${cf}`);
  });
  console.log('\n--c-<font> YANG SEHARUSNYA (rata-rata per font)');
  Object.keys(perFont).forEach((f) => {
    const a = perFont[f];
    const rata = a.reduce((s, v) => s + v, 0) / a.length;
    const sebar = Math.max(...a) - Math.min(...a);
    console.log(`  ${f.padEnd(16)} ${rata.toFixed(4)}   (sebaran ${sebar.toFixed(4)}, ${a.length} teks)`);
  });

  // Potret tiap halaman untuk dibandingkan dengan PDF aslinya.
  const halaman = rangkum.babak;
  for (const id of halaman) {
    await page.evaluate((x) => window.show(x), id);
    await tidur(320);
    const el = await page.$('#card-stage');
    await el.screenshot({ path: `${OUT}/${id}.png` });
  }

  console.log(`\npotret: ${OUT}/hal1.png .. ${halaman.length} halaman`);
  console.log('error:', catatan.length ? '\n  ' + catatan.join('\n  ') : '(bersih)');
  await browser.close();
})();
