/* Galeri foto produk: satu potret per halaman kartu, untuk halaman /template/<slug>/.
 *
 * Halaman produk rujukan (listing Etsy) memajang sekitar sepuluh foto di strip
 * kiri. Kartuku cuma punya SATU thumbnail per template, dan sisi kiri halaman
 * jadi kosong justru di bagian yang paling menjual.
 *
 * Foto-fotonya tidak perlu dibuat tangan: kartunya sendiri sudah punya
 * belasan halaman. Skrip ini membuka kartu contoh tiap template, memotret
 * SETIAP halamannya, lalu menyimpannya berurutan. Karena sumbernya kartu
 * sungguhan, galerinya tidak mungkin berbeda dari yang dibeli orang — dan
 * ikut berubah sendiri begitu desainnya disunting.
 *
 * Perkakas pembaca (bilah pratinjau, tombol lagu, tombol layar penuh, pager,
 * petunjuk geser) disembunyikan dulu, sama seperti tools/buat_thumb.js.
 *
 * Jalankan:
 *   NODE_PATH=<node_modules> node tools/buat_galeri_template.js <base-url> <folder-keluaran>
 */
const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer-core');

const BASE = process.argv[2] || 'http://127.0.0.1:8000';
const OUT = process.argv[3] || 'static/img/galeri';

/* Kartu "flow" (Scrapbook) tidak punya halaman terpisah — ia satu gulungan
   panjang. Yang dipotret di sana BAB-nya, lewat .chapter, bukan .scene. */
const TEMPLATES = [
  { slug: 'valentine-story',  lebar: 900,  tinggi: 1200, pilih: '.lembar' },
  { slug: 'game-8bit',        lebar: 1600, tinggi: 900,  pilih: '.scene'  },
  /* Sweetflix: babaknya ditulis TEGAS, tidak diambil dari .scene.
     Dua alasan. Babak pemutar foto kosong sampai tombol Putar ditekan — kalau
     ikut dipotret otomatis, yang masuk galeri layar hitam. Dan layar cerita
     memuat delapan panel yang cuma satu tampil, jadi memotretnya sekali
     membuang tujuh yang lain; di sini ia dipotret tiga kali dengan poster
     berbeda. Tanda "#n" berarti: buka babak itu lalu tampilkan poster ke-n. */
  { slug: 'sweetflix', lebar: 1600, tinggi: 900, pilih: '.scene',
    halaman: ['buka', 'profil', 'home_a', 'detail_a#1', 'detail_a#4', 'detail_a#7'] },
  /* Kartu BERGULIR (Scrapbook) sengaja TIDAK ada di sini.

     Sempat dipotret jadi satu gambar panjang yang digulir di kotak galeri,
     dan hasilnya persis mengulang isi nomor satu: kartu hidupnya sendiri
     sudah bisa digulir di dalam iframe-nya. Dua isi yang sama di satu strip
     bukan galeri, cuma pengulangan — dan pengulangan di halaman jualan
     membuat barangnya terlihat lebih sedikit daripada yang sebenarnya.

     Aturannya umum, bukan khusus Scrapbook: kartu ber-stage "flow" tidak
     butuh potret diam sama sekali. Yang berhalaman tetap butuh, karena
     kartu hidupnya cuma menampilkan satu halaman pada satu waktu. */
];

const BUANG = [
  '.preview-bar', '#bgm', '.bgm-fab', '.bgm-note', '.fs-fab',
  'nav.nav', '#petunjuk', '.scroll-hint',
].join(',');

const tidur = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new', args: ['--no-sandbox'],
  });

  /* Argumen ketiga (opsional) = slug yang mau dibuat saja. Tanpa itu semua
     template ditulis ulang, dan menulis ulang yang sudah benar cuma menambah
     peluang berubah tanpa disadari. */
  const saring = process.argv[4];
  for (const t of TEMPLATES) {
    if (saring && t.slug !== saring) continue;
    const dir = path.join(OUT, t.slug);
    fs.rmSync(dir, { recursive: true, force: true });
    fs.mkdirSync(dir, { recursive: true });

    const page = await browser.newPage();
    /* 1,5x, bukan 2x, dan JPEG bukan PNG. Diukur: 2x/PNG menghasilkan 34 MB
       untuk 26 gambar — di disk 512 MB itu sepertiga jatah, habis untuk foto
       etalase yang tidak pernah dilihat lebih besar dari 900 px. */
    await page.setViewport({ width: t.lebar, height: t.tinggi, deviceScaleFactor: 1.5 });
    await page.goto(`${BASE}/preview/${t.slug}/?sematan=1`, { waitUntil: 'networkidle0', timeout: 60000 });
    await page.addStyleTag({ content: `${BUANG}{display:none !important}` });
    await page.evaluate(() => document.fonts && document.fonts.ready);
    await tidur(2500);

    const id = t.halaman || await page.evaluate((sel) =>
      [...document.querySelectorAll(sel)].map((el, i) => el.id || `n${i}`), t.pilih);

    let n = 0;
    for (const halaman of id) {
      /* window.show() ada di kartu berbabak; kartu bergulir tidak punya, jadi
         di sana elemennya digulirkan ke tengah layar. */
      await page.evaluate((h, sel) => {
        /* "babak#n": buka babaknya lalu tampilkan panel ke-n di dalamnya. */
        const [nama, poster] = h.split('#');
        if (typeof window.show === 'function' && !nama.startsWith('n')) {
          window.show(nama);
          if (poster) {
            const kotak = document.querySelectorAll('#' + nama + ' [data-poster]');
            kotak.forEach(function (d) {
              d.classList.toggle('tampil', d.getAttribute('data-poster') === poster);
            });
          }
          return;
        }
        const el = [...document.querySelectorAll(sel)][parseInt(nama.slice(1), 10)];
        if (el) el.scrollIntoView({ block: 'center' });
      }, halaman, t.pilih);
      await tidur(900);

      const target = await page.$('#card-stage') || await page.$('body');
      n += 1;
      const berkas = path.join(dir, String(n).padStart(2, '0') + '.jpg');
      await target.screenshot({ path: berkas, type: 'jpeg', quality: 82 });
    }
    console.log(`${t.slug.padEnd(18)} ${n} halaman -> ${dir}`);
    await page.close();
  }
  await browser.close();
})();
