/* Seberapa lebar teks font pengganti dibanding font Canva aslinya.
 *
 * Font asli desain ini berbayar dan tidak boleh dipasang di situs, jadi
 * dipakai padanan bebas. Padanan yang bagus bentuknya belum tentu sama
 * lebarnya — dan di template ini lebar itu penting, karena satu baris yang
 * 8% lebih lebar akan melipat di tempat yang salah atau keluar halaman.
 *
 * Skrip ini mengukur lebar NYATA baris pertama tiap teks di Chrome, lalu
 * membandingkannya dengan lebar baris yang sama di PDF aslinya.
 */
const puppeteer = require('puppeteer-core');

const URL = process.argv[2] || 'http://localhost:8000/g/uji-valentine/';

// kelas -> lebar baris pertama di PDF, dalam pt (595,5 pt = lebar halaman)
const SASARAN = {
  't-mast': 463.3,      // LOVESTORY
  't-script': 282.7,    // Magazine
  't-edisi': 258.6,     // ANNIVERSARY (baris terpanjang)
  't-tanggal': 134.6,   // JULY 2026
  't-nama': 180.6,      // ROCKY &
  't-tagline': 227.4,   // THE PERFECT
  't-kata': 141.6,      // i love you endlessly.
  't-judul4': 274.3,    // T H E DAY
  't-body4': 545.9,     // satu baris penuh (rata kanan-kiri)
  't-bulan': 297.9,     // J u l y
  't-judul6': 456.0,    // Our Love
  't-h6a': 249.9,       // Physical Touch
  't-t6a': 309.9,       // My favorite place has always
  't-h6b': 345.9,       // Words Of Affirmation
  't-t6b': 473.8,       // The right words from the right person can heal
  't-eternal': 195.1,   // eternal love.
  't-pasang': 261.2,    // rocky & riana
  't-tutup': 423.9,     // From strangers to memories, from memories to
};

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 430, height: 860, deviceScaleFactor: 1 });
  await page.goto(URL, { waitUntil: 'networkidle2' });
  await page.evaluate(() => document.fonts.ready);
  await new Promise((r) => setTimeout(r, 400));

  const hasil = await page.evaluate(() => {
    const H0 = 551.6, W0 = 390, PT = 595.5;
    const out = [];
    document.querySelectorAll('.tx').forEach((el) => {
      const isi = el.matches('.t-body4') ? el.querySelector('p') : el;
      // Lebar baris PERTAMA saja: kotak pertama dari Range yang menyelimuti
      // seluruh teks. Kalau diambil lebar elemennya, yang terukur lebar
      // kotaknya, bukan lebar hurufnya.
      const r = document.createRange();
      r.selectNodeContents(isi);
      // Kotak TERLEBAR, bukan kotak pertama: Range memecah rect di tiap
      // baris DAN di tiap pergantian baris baru, jadi rect pertama sering
      // cuma potongan pendek ("4ND"), bukan baris terpanjangnya.
      const kotak = [...r.getClientRects()].filter((k) => k.width > 0.5);
      if (!kotak.length) return;
      const lebarMaks = Math.max(...kotak.map((k) => k.width));
      // Jumlah baris NYATA = banyaknya posisi atas yang berbeda. Wajib
      // diperiksa: kalau teks melipat di luar rencana, kotak terlebar cuma
      // potongan baris, dan "lebarnya sudah pas" jadi kesimpulan palsu.
      const baris = new Set(kotak.map((k) => Math.round(k.top))).size;
      const diminta = (isi.textContent.match(/\n/g) || []).length + 1;
      const kertas = el.closest('.kertas').getBoundingClientRect();
      const skala = kertas.width / W0;
      const g = getComputedStyle(el);
      out.push({
        kelas: [...el.classList].find((c) => c.startsWith('t-')),
        font: g.fontFamily.split(',')[0].replace(/["']/g, ''),
        baris: baris,
        diminta: diminta,
        // px lokal -> pt halaman
        lebarPt: +((lebarMaks / skala) * (PT / W0)).toFixed(1),
        fontPx: +parseFloat(g.fontSize).toFixed(2),
      });
    });
    return out;
  }, );

  console.log('kelas         font            baris  lebar-nyata  sasaran   rasio   font-size usul');
  hasil.forEach((h) => {
    const s = SASARAN[h.kelas];
    if (!s) return;
    const rasio = h.lebarPt / s;
    const usul = (h.fontPx / rasio).toFixed(2);
    const tanda = Math.abs(rasio - 1) < 0.03 ? '  ' : '!!';
    console.log(
      `${tanda} ${h.kelas.padEnd(11)} ${h.font.padEnd(15)} ${(h.baris === h.diminta ? ' ' : '*') + h.baris}/${h.diminta}   ` +
      `${String(h.lebarPt).padStart(7)}pt  ${String(s).padStart(6)}pt  ` +
      `${rasio.toFixed(3).padStart(6)}   ${String(h.fontPx).padStart(6)} → ${usul}`
    );
  });
  await browser.close();
})();
