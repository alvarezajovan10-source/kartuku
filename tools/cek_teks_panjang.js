/* Uji khusus: teks panjang tidak boleh meluber keluar kartu, dan tombol HUG
   tidak boleh dilintasi garis pita lantai. */
const puppeteer = require('puppeteer-core');
const OUT = '/private/tmp/claude-501/-Users-jepa-giftcard/5d310635-ee87-43cc-809d-6267459f0afe/scratchpad/8bit';
const tidur = (ms) => new Promise((r) => setTimeout(r, ms));

const PANJANG =
  'happy birthday to my favorite person in the world. you\'re the best person i could ' +
  'ever ask for, and i don\'t know where i\'d be without you. you\'re the funniest, ' +
  'sweetest, and most loving person ever. you always make me smile whenever i\'m upset, ' +
  'and i\'m so lucky that i met you. i want you to know how loved you are, not just ' +
  'because it\'s your birthday but because every single day you deserve the world, and ' +
  'i never want to lose you. i hope you have an amazing birthday. i love you more than ' +
  'anything, and you will always be my person in every universe. ilove you so much baby.';

(async () => {
  const browser = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new', args: ['--no-sandbox'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  const catatan = [];
  page.on('pageerror', (e) => catatan.push('[PAGEERROR] ' + e.message));
  await page.goto('http://localhost:8000/preview/game-8bit/', { waitUntil: 'networkidle2' });
  await tidur(500);

  // Isi teks sepanjang yang ditulis pembeli sungguhan.
  await page.evaluate((t) => {
    document.querySelector('#dialog .surat').textContent = t;
    document.querySelector('#wishes .kecil').textContent = t;
    document.querySelector('#wishes .panel-teks').textContent = 'MAKE A WISH';
  }, PANJANG);

  const hasil = {};
  for (const babak of ['dialog', 'wishes']) {
    await page.evaluate((b) => window.show(b), babak);
    await tidur(500);
    hasil[babak] = await page.evaluate((b) => {
      const scene = document.getElementById(b);
      const isi = scene.querySelector('.isi');
      const stage = document.getElementById('card-stage').getBoundingClientRect();
      const kotak = isi.getBoundingClientRect();
      return {
        meluberAtas: +(stage.top - kotak.top).toFixed(1),
        meluberBawah: +(kotak.bottom - stage.bottom).toFixed(1),
        bisaDigulir: [...scene.querySelectorAll('.gulung, .ucap, .isi')]
          .some((el) => el.scrollHeight > el.clientHeight + 1),
        semuaTerlihat: [...scene.querySelectorAll('.kepala, .mulai')].every((el) => {
          const r = el.getBoundingClientRect();
          return r.top >= stage.top - 1 && r.bottom <= stage.bottom + 1;
        }),
      };
    }, babak);
    await page.screenshot({ path: `${OUT}/uji-${babak}-panjang.png` });
  }

  // Tombol HUG vs garis pita lantai.
  const tombol = await page.evaluate(() => {
    const b = document.getElementById('pelukBtn').getBoundingClientRect();
    const l = document.querySelector('.lantai').getBoundingClientRect();
    const zT = getComputedStyle(document.getElementById('pelukBtn').closest('.scene')).zIndex;
    const zL = getComputedStyle(document.querySelector('.lantai')).zIndex;
    return {
      tombolBawah: +b.bottom.toFixed(1), garisLantai: +l.top.toFixed(1),
      zBabak: zT, zLantai: zL,
      garisMenimpaTombol: zL > zT && l.top < b.bottom && l.top > b.top,
    };
  });

  console.log('teks panjang :', JSON.stringify(hasil, null, 1));
  console.log('tombol HUG   :', JSON.stringify(tombol));
  console.log('error browser:', catatan.length ? catatan.join('\n') : '(bersih)');
  await browser.close();
})();
