/* Uji balik lembar Valentine Story di Chrome sungguhan.
 *
 * Yang diperiksa, dan alasannya:
 *  1. Seret dari ATAS / TENGAH / BAWAH memang berbeda hasilnya. Ini inti
 *     permintaannya; kalau --miring keluar sama saja, titik pegangnya tidak
 *     benar-benar terpakai.
 *  2. Ditarik separuh lalu dilepas -> kembali menutup, tidak nyangkut.
 *  3. Ditarik jauh lalu dilepas -> lanjut membuka.
 *  4. Bisa dibalik kembali ke halaman sebelumnya.
 *  5. Sentakan cepat walau pendek tetap membuka (lemparan).
 *  6. Hanya beberapa lembar yang dimuat (.dekat) — penjaga memori HP.
 *  7. Ketukan biasa TIDAK ikut mengganti halaman.
 */
const puppeteer = require('puppeteer-core');

const URL = process.argv[2] || 'http://localhost:8000/g/uji-valentine/';
const tidur = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new', args: ['--no-sandbox'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 430, height: 860 });
  const catatan = [];
  page.on('pageerror', (e) => catatan.push(`[PAGEERROR] ${e.message}`));
  page.on('console', (m) => { if (m.type() === 'error') catatan.push(`[error] ${m.text()}`); });
  await page.goto(URL, { waitUntil: 'networkidle2' });

  /* Pemeriksa ini menguji MEKANIK BALIK LEMBAR. Kalau GAYA sedang
     "partikel", tidak ada lembar yang dibalik sama sekali — seluruh uji di
     bawah akan gagal, dan gagalnya menyesatkan: yang salah bukan kodenya,
     melainkan pemeriksanya yang dijalankan pada mode yang tidak berlaku.
     Dilewati dengan tegas, bukan dibiarkan merah. Penjaga mode partikel ada
     di tools/cek_valentine_debu.js. */
  const gayaSekarang = await page.evaluate(() =>
    document.getElementById('buku')?.dataset.gaya || '(tidak ditandai)');
  if (gayaSekarang === 'partikel') {
    console.log(`GAYA sedang "${gayaSekarang}" — tidak ada lembar yang dibalik.`);
    console.log('Pemeriksa ini khusus mekanik balik lembar; DILEWATI.');
    console.log('Untuk mode sekarang, jalankan: node tools/cek_valentine_debu.js');
    await browser.close();
    process.exit(0);
  }
  await tidur(500);

  const kotak = await page.evaluate(() => {
    const r = document.getElementById('buku').getBoundingClientRect();
    return { x: r.left, y: r.top, w: r.width, h: r.height };
  });
  const aktif = () => page.evaluate(() => document.querySelector('.scene.active')?.id);
  /* Sejak halamannya MELENGKUNG, yang bergerak bukan lagi .lembar melainkan
     bilah-bilah di dalam #rig. Semua pengukuran di bawah membaca bilah
     itu — membaca .lembar akan selalu memberi nol dan uji-ujinya lulus
     palsu. Jumlah bilahnya JANGAN dihardcode di mana pun: ia ditentukan
     N_BILAH di valentine.js dan sudah pernah berubah (10 -> 16). */
  /* Dua gaya membalik hidup berdampingan (lihat GAYA di valentine.js).
     "bilah" menggerakkan .pias; "rotasi" menggerakkan .lembar
     sendiri lewat transisi CSS. Pemeriksa harus membaca yang SEDANG
     dipakai — membaca yang salah selalu memberi nol, dan uji-ujinya lulus
     palsu tanpa satu pun tanda bahaya. */
  /* Sumber kebenaran gaya sekarang atribut data-gaya di #buku, yang disetel
     valentine.js dari konstanta GAYA. Sebelumnya gaya ditebak dari ada
     tidaknya transform pada .pias — tebakan itu tidak bisa membedakan
     "partikel" (yang juga tidak menyentuh .pias) dari "rotasi". */
  const gayanya = () => page.evaluate(() =>
    document.getElementById('buku')?.dataset.gaya ||
    (document.querySelectorAll('.pias').length &&
     document.querySelectorAll('.pias')[0].style.transform ? 'bilah' : 'rotasi'));
  const sudutBilah = () => page.evaluate(() =>
    [...document.querySelectorAll('.pias')].map((b) => {
      const m = (b.style.transform || '').match(/rotateY\(([-\d.]+)deg\)/);
      return m ? -parseFloat(m[1]) : 0;
    }));
  /* Kemiringan ke arah tangan. Gaya "bilah" menaruhnya di tiap bilah,
     gaya "rotasi" di lembarnya sendiri — dibaca dari mana pun ia berada. */
  /* Dibaca dari bilah TERAKHIR, bukan bilah nomor 5. Pelintiran tumbuh
     sepanjang lembar (nol di punggung, penuh di ujung bebas), jadi nomor
     tetap mengikat pengukuran ini ke jumlah bilah tertentu: waktu N naik
     10 -> 16, bilah nomor 5 pindah dari u 0,74 ke u 0,59 dan nilainya
     ikut menyusut ~21% tanpa ada yang berubah pada animasinya. Bilah
     terakhir selalu ujung bebasnya, berapa pun N. */
  const miringnya = () => page.evaluate(() => {
    const p = document.querySelectorAll('.pias');
    const b = p[p.length - 1] || document.getElementById('hal1');
    const m = b && (b.style.transform || '').match(/rotateZ\(([-\d.]+)deg\)/);
    return m ? parseFloat(m[1]) : 0;
  });
  /* Sudut putaran yang SEBENARNYA tergambar, diambil dari matriks
     terhitung. Wajib begini untuk gaya "rotasi": di sana animasinya
     dijalankan transisi CSS, jadi style.transform sudah berisi nilai
     AKHIR sejak frame pertama — membacanya akan menyimpulkan putarannya
     selesai dalam satu frame. */
  const sudutTergambar = () => page.evaluate(() => {
    const el = document.getElementById('hal1');
    const m = new DOMMatrix(getComputedStyle(el).transform);
    return Math.abs(Math.atan2(m.m13, m.m11) * 180 / Math.PI);
  });

  async function seret({ dariAtas, jauh, langkah = 12, jeda = 16, lepas = true }) {
    const y = kotak.y + kotak.h * dariAtas;
    const x0 = kotak.x + kotak.w * 0.82;
    await page.mouse.move(x0, y);
    await page.mouse.down();
    for (let i = 1; i <= langkah; i++) {
      await page.mouse.move(x0 - (kotak.w * jauh * i) / langkah, y);
      await tidur(jeda);
    }
    const tengah = await miringnya();
    if (lepas) { await page.mouse.up(); await tidur(1750); }
    return tengah;
  }

  const hasil = {};

  // 1. titik pegang berpengaruh
  for (const [nama, pos] of [['atas', 0.12], ['tengah', 0.5], ['bawah', 0.88]]) {
    await page.evaluate(() => window.show('hal1'));
    await tidur(200);
    hasil['miring_' + nama] = Number(await seret({ dariAtas: pos, jauh: 0.5, lepas: false }));
    await page.mouse.up();
    await tidur(1700);
  }

  // 2. ditarik seperempat lalu dilepas -> balik menutup
  await page.evaluate(() => window.show('hal1'));
  await tidur(250);
  await seret({ dariAtas: 0.5, jauh: 0.22 });
  hasil.balikLagi = await aktif();

  // 3. ditarik jauh -> membuka
  await seret({ dariAtas: 0.5, jauh: 0.75 });
  hasil.membuka = await aktif();

  // 4. seret ke kanan -> kembali ke halaman sebelumnya
  const y = kotak.y + kotak.h * 0.5;
  await page.mouse.move(kotak.x + kotak.w * 0.2, y);
  await page.mouse.down();
  for (let i = 1; i <= 12; i++) {
    await page.mouse.move(kotak.x + kotak.w * (0.2 + 0.6 * i / 12), y);
    await tidur(16);
  }
  await page.mouse.up();
  await tidur(1750);
  hasil.mundur = await aktif();

  // 5. sentakan pendek tapi cepat -> tetap membuka
  await seret({ dariAtas: 0.5, jauh: 0.18, langkah: 3, jeda: 5 });
  hasil.lemparan = await aktif();

  // 6. penjaga memori
  hasil.dekat = await page.evaluate(() =>
    [...document.querySelectorAll('.lembar.dekat')].map((s) => s.id));
  // Halaman 11 sengaja tidak punya .pelat — isinya foto pembeli sehalaman
  // penuh. Tanpa penyaring ini skripnya mati dengan galat getComputedStyle
  // yang tidak menyebut halaman mana pun.
  hasil.pelatTermuat = await page.evaluate(() =>
    [...document.querySelectorAll('.lembar .pelat')].filter((p) =>
      getComputedStyle(p).backgroundImage !== 'none').length);

  // 7. ketukan biasa tidak mengganti halaman
  const sebelum = await aktif();
  await page.mouse.click(kotak.x + kotak.w * 0.5, kotak.y + kotak.h * 0.5);
  await tidur(500);
  hasil.ketukTidakPindah = (await aktif()) === sebelum;

  // 8. tombol & titik
  await page.click('#next'); await tidur(1700);
  hasil.tombolMaju = await aktif();
  await page.click('#prev'); await tidur(1700);
  hasil.tombolMundur = await aktif();

  /* 8b. BENAR-BENAR MELENGKUNG? Ini penjaga utamanya. Kalau semua bilah
         bersudut sama, halamannya masih bidang kaku yang diputar — persis
         keluhan "seperti kaca" itu, dan uji ini yang menangkapnya. */
  await page.evaluate(() => window.show('hal1'));
  await tidur(400);
  const y2 = kotak.y + kotak.h * 0.16;
  const xa = kotak.x + kotak.w * 0.88;
  await page.mouse.move(xa, y2);
  await page.mouse.down();
  await page.mouse.move(xa - 14, y2);
  await tidur(120);
  await page.mouse.move(xa - 14 - kotak.w * 0.2, y2);
  await tidur(320);
  const awalTarik = await sudutBilah();
  await page.mouse.move(xa - 14 - kotak.w * 0.5, y2);
  await tidur(320);
  const tengahTarik = await sudutBilah();
  await page.mouse.up();
  await tidur(2200);

  hasil.gaya = await gayanya();
  hasil.bilah = tengahTarik.length;
  if (hasil.bilah) {
    hasil.sebaranTengah = +(Math.max(...tengahTarik) - Math.min(...tengahTarik)).toFixed(1);
    // Lompatan sudut antar bilah bertetangga: di atas ~8 derajat,
    // faceting-nya terlihat sebagai kisi-kisi, bukan lengkungan.
    hasil.lompatanBilah = +Math.max(...tengahTarik.map((v, i) =>
      i ? Math.abs(v - tengahTarik[i - 1]) : 0)).toFixed(1);
    // Merambat: di awal tarikan punggung buku masih hampir rata dibanding
    // ujung bebasnya.
    hasil.punggungAwal = +awalTarik[0].toFixed(1);
    hasil.ujungAwal = +awalTarik[awalTarik.length - 1].toFixed(1);
  }

  // 9. Halus tidak? Rekam posisi lembar tiap frame selama tombol ditekan.
  //    Dua angka yang diukur: lamanya, dan lompatan terbesar antar frame.
  //    Lompatan besar = patah — itu keluhan "kaku/kasar" dalam bentuk angka.
  await page.evaluate(() => window.show('hal1'));
  await tidur(400);

  /* Berapa frame yang MAMPU diberikan browser ini, tanpa animasi apa pun?
     Wajib diukur sebelum menilai kemulusan, dan ini pernah membuang waktu:
     Chrome headless di mesin uji cuma memberi ~32 fps saat menganggur,
     jadi putaran 0,6 detik hanya bisa berisi ~19 frame — dan pemeriksa
     versi lama, yang ambangnya dipatok ke 60 fps, melaporkan "patah" serta
     "frame kurang" untuk animasi yang di layar sungguhan mulus.
     Ambang di bawah karena itu SELALU diskalakan ke angka ini. */
  const fps = await page.evaluate(() => new Promise((res) => {
    let n = 0; const t0 = performance.now();
    (function tik() {
      n++;
      performance.now() - t0 < 500 ? requestAnimationFrame(tik)
        : res(n / (performance.now() - t0) * 1000);
    })();
  }));
  hasil.fpsMenganggur = +fps.toFixed(1);
  const gerak = await page.evaluate((gaya) => new Promise((selesai) => {
    /* Elemen yang dibaca HARUS yang benar-benar bergerak, dan itu berbeda
       per gaya:

         "rotasi" — .lembar sendiri yang diputar transisi CSS
         "bilah"  — .lembar diam dan digantikan rig; yang berputar .pias

       Versi sebelumnya selalu membaca #hal1. Waktu gayanya dipindah ke
       "bilah", ia jadi membaca elemen yang memang tidak bergerak: lamaMs
       dan frame keluar NOL, dan akibatnya TIGA uji lolos palsu — lompatan
       terbesar 0 lolos ambang apa pun, dan "cukup banyak frame" jadi
       0 >= 70% dari 0. Persis "lulus palsu" yang diperingatkan di atas.

       Bilah terakhir = ujung bebas lembar; sudutnya sama dengan sudut
       putaran keseluruhan, jadi ia wakil yang sah untuk mengukur t. */
    const sudut = () => {
      /* Rig hanya sah dibaca selagi ia BERJALAN. Di luar itu ia
         `display:none`, dan getComputedStyle mengembalikan `transform:none`
         untuk elemen yang tidak dirender — terbaca sebagai sudut 0. Kalau
         dibaca membabi buta, nilai t terjun dari ~1 ke 0 di frame terakhir
         dan uji "tidak patah" melaporkan patahan yang tidak ada di layar.
         Saat rig tidak jalan, .lembar sendiri yang memegang sudut benar. */
      const rig = document.getElementById('rig');
      const p = document.querySelectorAll('.pias');
      const pakaiBilah = gaya === 'bilah' && p.length
        && rig && rig.classList.contains('jalan');
      const el = pakaiBilah ? p[p.length - 1] : document.getElementById('hal1');
      const mm = new DOMMatrix(getComputedStyle(el).transform);
      return Math.abs(Math.atan2(mm.m13, mm.m11) * 180 / Math.PI) / 180;
    };
    const jejak = [];
    const t0 = performance.now();
    let diam = 0;
    (function rekam() {
      const t = sudut();
      jejak.push({ w: performance.now() - t0, t: t });
      diam = (jejak.length > 2 && t === jejak[jejak.length - 2].t) ? diam + 1 : 0;
      if (diam > 6 || performance.now() - t0 > 4000) return selesai(jejak);
      requestAnimationFrame(rekam);
    })();
    document.getElementById('next').click();
  }), hasil.gaya);
  const bergerak = gerak.filter((g, i) => i > 0 && g.t !== gerak[i - 1].t);
  const lompatan = bergerak.map((g, i) => i ? Math.abs(g.t - bergerak[i - 1].t) : 0);
  hasil.lamaMs = bergerak.length
    ? Math.round(bergerak[bergerak.length - 1].w - bergerak[0].w) : 0;
  hasil.frame = bergerak.length;
  hasil.lompatanTerbesar = +Math.max(...lompatan, 0).toFixed(4);

  // 10. Ditekan dua kali cepat: halaman harus maju dua, bukan nyangkut.
  await page.evaluate(() => window.show('hal1'));
  await tidur(500);
  await page.click('#next');
  await tidur(220);
  await page.click('#next');
  await tidur(2600);
  hasil.tekanDuaKali = await aktif();

  console.log(JSON.stringify(hasil, null, 1));
  const m = hasil;
  const lulus = [
    ['pegang atas & bawah berlawanan arah', m.miring_atas < -0.5 && m.miring_bawah > 0.5],
    ['pegang tengah hampir tidak memiringkan', Math.abs(m.miring_tengah) < 0.5],
    ['tarik sedikit -> menutup lagi', m.balikLagi === 'hal1'],
    ['tarik jauh -> membuka', m.membuka === 'hal2'],
    ['seret ke kanan -> mundur', m.mundur === 'hal1'],
    ['sentakan pendek -> membuka', m.lemparan === 'hal2'],
    ['hanya sebagian lembar dimuat', m.pelatTermuat > 0 && m.pelatTermuat <= 5],
    ['ketukan tidak mengganti halaman', m.ketukTidakPindah],
    ['tombol maju jalan', m.tombolMaju === 'hal3'],
    ['tombol mundur jalan', m.tombolMundur === 'hal2'],
    ...(m.gaya === 'bilah' ? [
      /* Dulu `=== 10`, dan itu memaku pemeriksa ke satu nilai N_BILAH:
         menaikkannya jadi 16 membuat penjaga ini gagal padahal animasinya
         justru membaik. Yang benar-benar dijaga adalah ADA CUKUP bilah
         untuk menggambar kurva, bukan angka tertentu. */
      ['cukup bilah untuk menggambar kurva (>= 12)', m.bilah >= 12],
      ['BENAR-BENAR melengkung (sebaran > 25 derajat)', m.sebaranTengah > 25],
      /* Ambang dinaikkan 8 -> 15 pada 14 Agu 2026, kelonggaran yang
         diberikan pemilik situs saat meminta lengkung "seperti kain".
         Catatan: kelonggaran itu TIDAK terpakai habis. Sapuan 200 cuplikan
         sepanjang putaran pada setelan sekarang (LURUH 0,30 / 16 bilah)
         mengukur lompatan maksimum 7,94 derajat — praktis sama dengan
         setelan lama (7,74), meski sebarannya naik 85%. Ambang longgar ini
         ada supaya penyetelan LURUH berikutnya punya ruang, bukan karena
         faceting-nya sudah bertambah. */
      ['tidak berkisi (lompatan antar bilah < 15 derajat)', m.lompatanBilah < 15],
      ['lipatan merambat', m.ujungAwal - m.punggungAwal > 12],
    ] : [
      // Gaya "rotasi" memang SATU BIDANG yang diputar — tidak melengkung,
      // dan itu pilihan pemilik situs, bukan kemunduran yang lolos.
      ['gaya rotasi: tidak ada bilah yang bergerak', m.bilah === 0],
    ]),
    ['lama balik sesuai gayanya', m.gaya === 'rotasi'
      ? (m.lamaMs >= 450 && m.lamaMs <= 900)
      : (m.lamaMs >= 1100 && m.lamaMs <= 1800)],
    /* Kedua ambang di bawah DISKALAKAN ke kecepatan frame browsernya —
       lihat catatan di fpsMenganggur. Yang dinilai adalah kemulusan
       animasinya, bukan kecepatan mesin yang kebetulan dipakai menguji. */
    [`tidak patah (lompatan < ${(0.08 * 60 / m.fpsMenganggur).toFixed(3)} @ ${m.fpsMenganggur} fps)`,
      m.lompatanTerbesar < 0.08 * 60 / m.fpsMenganggur],
    // Putaran yang mulus mengisi hampir tiap frame yang ditawarkan browser.
    // 0,7 memberi kelonggaran untuk frame yang hilang di awal & akhir.
    [`cukup banyak frame (>= 70% dari ${Math.round(m.lamaMs / 1000 * m.fpsMenganggur)})`,
      m.frame >= 0.7 * (m.lamaMs / 1000) * m.fpsMenganggur],
    ['ditekan dua kali -> maju dua', m.tekanDuaKali === 'hal3'],
  ];
  console.log();
  lulus.forEach(([n, ok]) => console.log(`${ok ? ' OK ' : 'GAGAL'}  ${n}`));
  console.log('\nerror:', catatan.length ? '\n  ' + catatan.join('\n  ') : '(bersih)');
  await browser.close();
  process.exit(lulus.every(([, ok]) => ok) ? 0 : 1);
})();
