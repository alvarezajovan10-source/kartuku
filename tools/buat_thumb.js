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
  // Kartunya mendatar 16:9, tapi thumbnailnya tetap 3:4 seperti yang lain —
  // kisi yang seragam lebih penting daripada rasio asli kartunya.
  //
  // WAJIB dipotret di viewport MENDATAR. Kartu ini punya gerbang orientasi:
  // dibuka dalam bentuk tegak, yang tampil cuma layar merah muda bertuliskan
  // "MIRINGKAN HP-MU", bukan kartunya.
  //
  // Jadi potret 16:9-nya disusun ke kanvas 3:4 (lihat `susun`) — kartunya
  // utuh dan dipusatkan, sisanya latar plum bingkai kartunya sendiri.
  // Menyerahkan gambar 16:9 langsung ke slot 3:4 memaksa memilih antara
  // terpotong kiri-kanan (judulnya jadi "PPY BIRTHDA") atau slot dua kolom
  // yang menyisakan bidang kosong besar di bawah tombolnya.
  { slug: 'game-8bit', lebar: 1600, tinggi: 900, cara: 'elemen',
    susun: { lebar: 900, tinggi: 1200, latar: '#3b2233' } },
  // TIDAK dipotret — thumbnailnya buatan tangan, dari tools/buat_thumb_valentine.py.
  //
  // Bukan selera: yang dipotret skrip ini adalah kartu KOSONG, dan sampul
  // Valentine Story hampir seluruhnya lubang foto. Yang tertangkap cuma
  // gradasi pengisi dengan tulisan di atasnya — sebagai gambar etalase itu
  // menjual kartu yang salah. Pemilik situs mengirim sampul yang sama dengan
  // fotonya terisi (LOVESTORY-5.pdf, 21 Agu 2026), dan itu yang dipakai.
  //
  // Dibiarkan di daftar ini, bukan dihapus, supaya yang membaca berikutnya
  // tahu halaman ini SENGAJA dilewati — bukan lupa didaftarkan. Kalau
  // sampulnya suatu hari tidak lagi berlubang foto, cabut `manual` dan
  // angka di bawah langsung berlaku lagi.
  { slug: 'valentine-story',  lebar: 900,  tinggi: 1200, cara: 'elemen',
    manual: 'tools/buat_thumb_valentine.py' },
  // Sweetflix: mendatar 16:9 seperti Game 8-Bit, jadi disusun ke kanvas 3:4
  // yang sama supaya kisi etalase tetap seragam.
  //
  // `babak` menyimpang dari aturan "potret halaman pertama". Halaman pertama
  // Sweetflix layar isian nama: latar gelap dengan satu kotak teks dan tombol.
  // Benar sebagai pembuka kartu, tapi sebagai gambar etalase ia tidak
  // memperlihatkan APA PUN dari isinya. Yang dipotret berandanya, tempat foto
  // dan deretan posternya terlihat.
  { slug: 'sweetflix', lebar: 1600, tinggi: 900, cara: 'elemen', babak: 'home_a',
    susun: { lebar: 900, tinggi: 1200, latar: '#0b0b0f' } },
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

/* Taruh gambar yang sudah jadi di tengah kanvas berukuran lain, lalu tulis
   ulang ke berkas yang sama. Dipakai kartu mendatar supaya thumbnailnya
   berbentuk 3:4 seperti template lain tanpa memotong kartunya.

   Disusun di Chrome yang sudah terbuka, bukan lewat pustaka gambar: skrip
   ini sengaja tidak menambah dependensi di luar puppeteer-core. */
async function susunKeKanvas(browser, berkas, { lebar, tinggi, latar }) {
  const b64 = fs.readFileSync(berkas).toString('base64');
  const page = await browser.newPage();
  await page.setViewport({ width: lebar, height: tinggi, deviceScaleFactor: 3 });
  await page.setContent(
    `<style>
       html,body{margin:0;height:100%}
       body{background:${latar};display:grid;place-items:center;overflow:hidden}
       /* Latar = gambar yang sama, diperbesar dan diburamkan. Pita warna rata
          membuat kartunya terlihat seperti gambar yang kurang tinggi; langit
          kartunya sendiri yang meluber ke tepi membuat bidangnya terbaca
          sebagai satu gambar utuh. */
       .latar{
         position:fixed; inset:-10%;
         background:url(data:image/png;base64,${b64}) center/cover no-repeat;
         filter:blur(28px) saturate(1.1) brightness(.82);
       }
       img{position:relative; width:100%; display:block;
           box-shadow:0 24px 60px rgba(0,0,0,.45)}
     </style>
     <div class="latar"></div>
     <img src="data:image/png;base64,${b64}">`,
    { waitUntil: 'load' },
  );
  await page.screenshot({ path: berkas, type: 'png' });
  await page.close();
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
  });

  for (const t of TEMPLATES) {
    if (t.manual) {
      console.log(`${t.slug}  DILEWATI — thumbnailnya dibuat ${t.manual}`);
      continue;
    }
    const page = await browser.newPage();
    await page.setViewport({ width: t.lebar, height: t.tinggi, deviceScaleFactor: 3 });
    await page.goto(`${BASE}/preview/${t.slug}/`, { waitUntil: 'networkidle0', timeout: 60000 });
    await page.addStyleTag({ content: `${BUANG}{display:none !important}` });
    await page.evaluate(() => document.fonts && document.fonts.ready);
    await tidur(2500);
    if (t.babak) {
      await page.evaluate((b) => { if (typeof window.show === 'function') window.show(b); }, t.babak);
      await tidur(1200);
    }

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
    await page.close();

    if (t.susun) await susunKeKanvas(browser, berkas, t.susun);
    console.log(`${t.slug}  stage=${info}  cara=${t.cara}${t.susun ? '+susun' : ''}  → ${berkas}`);
  }

  await browser.close();
})();
