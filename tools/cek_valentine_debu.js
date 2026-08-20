/* Uji peralihan halaman mode "partikel" (debu berpendar) di Chrome sungguhan.
 *
 * Pasangan cek_valentine_balik.js: yang itu menguji mekanik balik lembar,
 * yang ini menguji mekanik memudar + debu. Keduanya memeriksa GAYA lebih
 * dulu dan melewati diri sendiri kalau mode yang aktif bukan miliknya —
 * jadi keduanya bisa dijalankan berurutan tanpa satu pun jadi merah palsu.
 *
 * Yang diperiksa, dan alasannya:
 *  1. Halaman benar-benar berganti lewat tombol, titik, sapuan, dan keyboard.
 *  2. Debu SUNGGUH tergambar di tengah peralihan. Ini penjaga utamanya:
 *     seluruh sisanya tetap lulus walau kanvasnya kosong melompong, dan
 *     "peralihan tanpa debu" persis kemunduran yang paling mudah lolos.
 *  3. Debu BERPENDAR — lebih terang daripada halaman asalnya. Pernah salah:
 *     warna dipakai mentah, dan halaman gelap melepas bintik kelabu yang
 *     terbaca sebagai kotoran di atas halaman terang berikutnya.
 *  4. Kanvas bersih lagi sesudahnya, dan tidak ada opacity sisa yang
 *     tertinggal di elemen lembar.
 *  5. Tidak ada dua peralihan yang berjalan bersamaan (tekan cepat dua kali).
 *
 * Jalankan:
 *   NODE_PATH=<node_modules berisi puppeteer-core> node tools/cek_valentine_debu.js
 */
const puppeteer = require('puppeteer-core');

const URL = process.argv[2] || 'http://localhost:8000/uji-valentine/';
const tidur = (ms) => new Promise((r) => setTimeout(r, ms));

/* Lama satu peralihan, HARUS sama dengan LAMA_LARUT di valentine.js.
 *
 * Ditulis sebagai satu nama, dan jeda di bawah dihitung DARI nama ini, karena
 * angka mentah di sini sudah pernah basi diam-diam: peralihannya dinaikkan
 * 1100 -> 2500 ms (19 Agu 2026) tanpa berkas ini ikut disetel, dan sesudah itu
 * pemeriksanya mengambil cuplikan "sesudah peralihan selesai" pada 1480 ms —
 * yaitu di TENGAH peralihan. Hasilnya dua kegagalan palsu yang menetap
 * ("kanvas bersih lagi", "tidak ada opacity sisa"), plus satu yang berkedip
 * (jumlah debu di 280 ms, karena sepertiga butirnya belum berangkat). */
const LARUT = 2500;

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new', args: ['--no-sandbox'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 430, height: 860 });
  const catatan = [];
  page.on('pageerror', (e) => catatan.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error') catatan.push(m.text()); });

  await page.goto(URL, { waitUntil: 'networkidle2' });
  await tidur(1400);

  const gaya = await page.evaluate(() =>
    document.getElementById('buku')?.dataset.gaya || '(tidak ditandai)');
  if (gaya !== 'partikel') {
    console.log(`GAYA sedang "${gaya}" — bukan mode partikel. DILEWATI.`);
    console.log('Untuk mode itu, jalankan: node tools/cek_valentine_balik.js');
    await browser.close();
    process.exit(0);
  }

  const aktif = () => page.evaluate(() => document.querySelector('.scene.active')?.id);
  const hasil = { gaya };

  /* Berapa piksel kanvas yang tergambar, dan seberapa terang.
     Diambil dari kanvas LANGSUNG, bukan dari tangkapan layar: tangkapan
     layar mencampur debu dengan isi halaman di belakangnya, dan dari situ
     "debu tidak digambar" tidak bisa dibedakan dari "debu digambar tapi
     tertutup". */
  const bacaKanvas = () => page.evaluate(() => {
    const c = document.getElementById('debu');
    if (!c || !c.width) return { ada: 0, terang: 0 };
    const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
    let n = 0, jml = 0;
    for (let i = 0; i < d.length; i += 4) {
      if (d[i + 3] < 8) continue;
      n++;
      jml += Math.max(d[i], d[i + 1], d[i + 2]);
    }
    return { ada: n, terang: n ? jml / n : 0 };
  });

  // 1. Tombol maju
  await page.click('#next');
  // Seperempat perjalanan: cukup jauh supaya sebagian besar butir sudah
  // berangkat (tunda diundi sampai 0,45), cukup awal supaya belum ada yang
  // habis. Pecahannya yang ditetapkan, bukan miliseknya.
  await tidur(LARUT * 0.26);
  const tengah = await bacaKanvas();
  hasil.piksekDebu = tengah.ada;
  hasil.terangDebu = +tengah.terang.toFixed(1);
  // Lewat garis akhir, plus kelonggaran satu-dua frame untuk bersih-bersih.
  await tidur(LARUT * 0.74 + 350);
  hasil.setelahMaju = await aktif();
  hasil.kanvasBersih = (await bacaKanvas()).ada;

  // Tidak ada opacity sisa yang tertinggal menempel di elemen.
  hasil.opasitasSisa = await page.evaluate(() =>
    [...document.querySelectorAll('.lembar')].filter((e) => e.style.opacity !== '').length);

  // 2. Tombol mundur
  await page.click('#prev');
  await tidur(1500);
  hasil.setelahMundur = await aktif();

  // 3. Sapuan mendatar (pengganti seret di mode balik lembar)
  const kotak = await page.evaluate(() => {
    const r = document.getElementById('buku').getBoundingClientRect();
    return { x: r.x, y: r.y, w: r.width, h: r.height };
  });
  const y = kotak.y + kotak.h * 0.5;
  await page.mouse.move(kotak.x + kotak.w * 0.8, y);
  await page.mouse.down();
  await page.mouse.move(kotak.x + kotak.w * 0.2, y, { steps: 8 });
  await page.mouse.up();
  await tidur(1500);
  hasil.setelahSapu = await aktif();

  // Sapuan TEGAK tidak boleh mengganti halaman — itu gerakan menggulir.
  const sebelumTegak = await aktif();
  await page.mouse.move(kotak.x + kotak.w * 0.5, kotak.y + kotak.h * 0.25);
  await page.mouse.down();
  await page.mouse.move(kotak.x + kotak.w * 0.5, kotak.y + kotak.h * 0.75, { steps: 8 });
  await page.mouse.up();
  await tidur(900);
  hasil.sapuTegakDiam = (await aktif()) === sebelumTegak;

  // 4. Ditekan dua kali beruntun harus maju dua, bukan tertelan.
  const sebelumDua = await aktif();
  await page.click('#next');
  await tidur(120);
  await page.click('#next');
  await tidur(2400);
  hasil.tekanDuaKali = await aktif();
  hasil.majuDua =
    Number((hasil.tekanDuaKali || '').replace('hal', '')) -
    Number((sebelumDua || '').replace('hal', ''));

  /* 5. SKIP CEPAT — penjaga kemunduran yang paling penting di berkas ini.
        Menekan lanjut jauh lebih cepat daripada lama peralihan pernah
        meninggalkan `opacity` inline menempel di halaman yang peralihannya
        disusul. Gaya inline tidak bisa ditimpa aturan CSS, jadi tiap
        tekanan menambah satu halaman setengah transparan, dan layarnya
        jadi bubur berlapis-lapis.

        Bug kedua di sebelahnya: halaman tujuan dipaksa mulai dari nol tiap
        peralihan, jadi pada tekanan beruntun ia tidak pernah sempat muncul
        dan layar justru KOSONG. Dua-duanya diukur di sini. */
  await page.evaluate(() => new Promise((res) => {
    let n = 0;
    const tik = setInterval(() => {
      document.getElementById('next').click();
      if (++n >= 6) { clearInterval(tik); res(); }
    }, 110);
  }));
  const cepat = await page.evaluate(() => new Promise((res) => {
    const rekam = []; const t0 = performance.now();
    (function f() {
      let jml = 0, n = 0;
      document.querySelectorAll('.lembar').forEach((e) => {
        const s = getComputedStyle(e);
        if (s.visibility === 'hidden') return;
        const o = parseFloat(s.opacity) || 0;
        jml += o; if (o > 0.02) n++;
      });
      rekam.push([jml, n]);
      if (performance.now() - t0 < 900) return requestAnimationFrame(f);
      res({ minTotal: Math.min(...rekam.map((r) => r[0])),
            maksHalaman: Math.max(...rekam.map((r) => r[1])) });
    })();
  }));
  hasil.skipMinTotal = +cepat.minTotal.toFixed(2);
  hasil.skipMaksHalaman = cepat.maksHalaman;
  await tidur(2200);
  hasil.skipSisa = await page.evaluate(() =>
    [...document.querySelectorAll('.lembar')].filter((e) =>
      e.style.opacity !== '' || e.classList.contains('keluar') ||
      e.classList.contains('masuk')).length);
  hasil.skipTampak = await page.evaluate(() =>
    [...document.querySelectorAll('.lembar')].filter((e) => {
      const s = getComputedStyle(e);
      return s.visibility !== 'hidden' && parseFloat(s.opacity) > 0.02;
    }).length);

  // 6. Keyboard
  const sebelumKey = await aktif();
  await page.keyboard.press('ArrowRight');
  await tidur(1500);
  hasil.setelahKeyboard = await aktif();
  hasil.keyboardJalan = hasil.setelahKeyboard !== sebelumKey;

  console.log(JSON.stringify(hasil, null, 1));

  const lulus = [
    ['tombol maju mengganti halaman', hasil.setelahMaju === 'hal2'],
    ['tombol mundur mengganti halaman', hasil.setelahMundur === 'hal1'],
    ['sapuan mendatar mengganti halaman', hasil.setelahSapu === 'hal2'],
    ['sapuan tegak TIDAK mengganti halaman', hasil.sapuTegakDiam],
    ['keyboard mengganti halaman', hasil.keyboardJalan],
    ['ditekan dua kali -> maju dua', hasil.majuDua === 2],
    // Penjaga utama: tanpa ini semua uji di atas tetap lulus walau
    // kanvasnya kosong dan peralihannya cuma memudar tanpa debu.
    ['debu BENAR-BENAR tergambar (> 2000 piksel)', hasil.piksekDebu > 2000],
    // Debu berpendar: lebih terang daripada kertas mana pun di template ini.
    ['debu berpendar (kecerahan puncak > 190)', hasil.terangDebu > 190],
    ['kanvas bersih lagi sesudahnya', hasil.kanvasBersih === 0],
    ['tidak ada opacity sisa di elemen', hasil.opasitasSisa === 0],
    // Skip cepat: tidak menumpuk, tidak berkedip gelap, tidak menyisakan apa pun.
    ['skip cepat: halaman TIDAK menumpuk (maks 2)', hasil.skipMaksHalaman <= 2],
    ['skip cepat: layar tidak pernah kosong (total >= 0,9)', hasil.skipMinTotal >= 0.9],
    ['skip cepat: mengendap ke satu halaman', hasil.skipTampak === 1],
    ['skip cepat: tidak ada sisa kelas/opacity', hasil.skipSisa === 0],
  ];
  console.log();
  lulus.forEach(([n, ok]) => console.log(`${ok ? ' OK ' : 'GAGAL'}  ${n}`));
  console.log('\nerror:', catatan.length ? '\n  ' + catatan.join('\n  ') : '(bersih)');
  await browser.close();
  process.exit(lulus.every(([, ok]) => ok) ? 0 : 1);
})();
