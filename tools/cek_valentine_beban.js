/* Seberapa berat satu putaran, termasuk di perangkat lemah.
 *
 * CPU dicekik lewat CDP untuk menirukan HP kelas menengah-bawah — di situlah
 * kebanyakan pembeli membuka kartunya. Yang diukur bukan "terasa mulus"
 * melainkan angka: berapa frame yang tergambar dan berapa lama jeda
 * terpanjang antar frame.
 */
const puppeteer = require('puppeteer-core');
const tidur = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const b = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new', args: ['--no-sandbox'],
  });
  /* Berapa frame yang MAMPU diberikan mesin ini, tanpa animasi apa pun?
     Diukur di halaman kosong, sebelum apa-apa. Wajib: Chrome headless di
     mesin uji ini kadang cuma memberi ~31 fps saat menganggur (tergantung
     beban & suhu), dan ambang tetap 45/28 fps kemudian melaporkan
     "TERSENDAT" untuk animasi yang sebenarnya mengisi 97% frame yang
     tersedia. Verdict di bawah karena itu diukur sebagai PERSENTASE dari
     angka ini, bukan terhadap 60 fps yang diandaikan.

     Ini pelajaran yang sama dengan yang sudah dicatat di cek_valentine_balik.js
     — di sana ambangnya sudah diskalakan, di sini dulu belum. */
  const pIdle = await b.newPage();
  await pIdle.goto('about:blank');
  const fpsMenganggur = await pIdle.evaluate(() => new Promise((res) => {
    let n = 0; const t0 = performance.now();
    (function tik() {
      n++;
      performance.now() - t0 < 1000 ? requestAnimationFrame(tik)
        : res(n / (performance.now() - t0) * 1000);
    })();
  }));
  await pIdle.close();
  console.log(`fps menganggur mesin ini: ${fpsMenganggur.toFixed(1)}` +
    ` (ambang diskalakan ke angka ini, bukan ke 60)`);

  for (const cekik of [1, 4, 6]) {
    const p = await b.newPage();
    await p.setViewport({ width: 430, height: 860 });
    const cdp = await p.target().createCDPSession();
    await p.goto('http://localhost:8000/g/uji-valentine/', { waitUntil: 'networkidle2' });
    await tidur(900);
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: cekik });
    await tidur(300);

    const r = await p.evaluate(() => new Promise((selesai) => {
      const jeda = [];
      let lalu = performance.now();
      let diam = 0;
      /* Sudut yang SEBENARNYA tergambar, dari matriks terhitung. Membaca
         style.transform tidak sah untuk gaya "rotasi" — di sana nilainya
         sudah berisi sudut AKHIR sejak frame pertama, jadi terbaca
         "selesai" seketika dan hasilnya nol frame.

         Elemennya juga harus yang benar-benar bergerak. Di gaya "bilah",
         .lembar DIAM dan digantikan rig; yang berputar adalah .pias.
         Membaca #hal1 di sana memberi 2 frame dan "fps 96 saat CPU
         dicekik 6x" — angka mustahil yang terbaca sebagai lulus. */
      const sudut = () => {
        /* Rig hanya sah dibaca selagi BERJALAN — di luar itu ia
           `display:none` dan computed transform-nya `none` (terbaca 0). */
        const rig = document.getElementById('rig');
        const p = document.querySelectorAll('.pias');
        const pakaiBilah = p.length && rig && rig.classList.contains('jalan');
        const el = pakaiBilah ? p[p.length - 1] : document.getElementById('hal1');
        const m = new DOMMatrix(getComputedStyle(el).transform);
        return Math.abs(Math.atan2(m.m13, m.m11) * 180 / Math.PI);
      };
      let akhir = sudut();
      (function ukur() {
        const kini = performance.now();
        jeda.push(kini - lalu);
        lalu = kini;
        const a = sudut();
        diam = a === akhir ? diam + 1 : 0;
        akhir = a;
        if ((diam > 8 && jeda.length > 12) || jeda.length > 400) {
          jeda.shift();
          const bergerak = jeda.slice(2, -8);
          return selesai({
            frame: bergerak.length,
            fpsRata: +(1000 / (bergerak.reduce((s, v) => s + v, 0) / bergerak.length)).toFixed(1),
            jedaTerlama: +Math.max(...bergerak).toFixed(1),
          });
        }
        requestAnimationFrame(ukur);
      })();
      document.getElementById('next').click();
    }));
    /* Yang dinilai: seberapa besar bagian frame yang TERSEDIA berhasil
       diisi animasinya — bukan angka fps mutlak, yang cuma memberi tahu
       seberapa sibuk mesin penguji saat itu. */
    const isi = r.fpsRata / fpsMenganggur;
    console.log(`cekik ${cekik}x  frame ${String(r.frame).padStart(3)}  ` +
      `fps rata ${String(r.fpsRata).padStart(5)}  jeda terlama ${String(r.jedaTerlama).padStart(6)} ms` +
      `  mengisi ${(isi * 100).toFixed(0).padStart(3)}%` +
      `   ${isi >= 0.85 ? 'mulus' : isi >= 0.6 ? 'cukup' : 'TERSENDAT'}`);
    await p.close();
  }
  await b.close();
})();
