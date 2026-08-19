/* Kalender Valentine Story: klik tanggal memindahkan hatinya.
 *
 * Yang diuji bukan cuma "hatinya pindah di layar" — itu bagian yang mudah.
 * Yang gampang diam-diam rusak adalah rantainya: klik di DALAM iframe harus
 * sampai ke editor lewat pesan settext, tersimpan ke server, dan masih ada
 * di sana waktu kartunya dimuat ulang. Kalau satu mata rantai putus,
 * pembeli melihat hatinya pindah lalu kembali sendiri ke tanggal 13.
 */
const puppeteer = require('puppeteer-core');
const tidur=(ms)=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const b=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:'new',args:['--no-sandbox']});
  const p=await b.newPage(); await p.setViewport({width:1440,height:940});
  const err=[]; p.on('pageerror',e=>err.push(e.message));
  p.on('console',m=>{if(m.type()==='error')err.push(m.text());});
  await p.goto('http://localhost:8000/create/valentine-story/',{waitUntil:'networkidle2'});
  await tidur(3000);
  const f=p.frames().find(x=>x.url().includes('/frame/'));
  await f.evaluate(()=>window.show('hal5')); await tidur(600);

  const awal = await f.evaluate(()=>document.querySelector('.lingkaran').getAttribute('class'));
  const tombol = await f.evaluate(()=>document.querySelectorAll('.hari').length);
  await f.click('.hari[data-hari="20"]'); await tidur(400);
  const sesudah = await f.evaluate(()=>document.querySelector('.lingkaran').getAttribute('class'));
  const posisi = await f.evaluate(()=>{
    const l=document.querySelector('.lingkaran'); const g=getComputedStyle(l);
    return {x:g.getPropertyValue('--x').trim(), y:g.getPropertyValue('--y').trim()};
  });
  const diEditor = await p.evaluate(()=>{
    const el=document.querySelector('[x-data]'); return Alpine.$data(el).texts.hari;
  }).catch(()=>null);
  await tidur(1500);                     // tunggu autosave
  const kartu = await p.evaluate(()=>document.querySelector('[x-data]') && Alpine.$data(document.querySelector('[x-data]')).cardId).catch(()=>null);

  // muat ulang halaman frame dari server: pilihannya harus bertahan
  const p2=await b.newPage(); await p2.setViewport({width:430,height:860});
  await p2.goto(`http://localhost:8000/create/valentine-story/frame/?card=${kartu}`,{waitUntil:'networkidle2'});
  await tidur(700);
  const tersimpan = await p2.evaluate(()=>document.querySelector('.lingkaran').getAttribute('class'));

  console.log(JSON.stringify({tombol,awal,sesudah,posisi,diEditor,tersimpan},null,1));
  const ok=[['31 tanggal bisa diklik',tombol===31],
            ['bawaan tanggal 13',awal==='lingkaran hh13'],
            ['klik 20 -> hati pindah',sesudah==='lingkaran hh20'],
            ['koordinat ikut berubah',posisi.x==='76.744%'],
            ['tersimpan di editor',diEditor==='20'],
            ['bertahan setelah dimuat ulang',tersimpan==='lingkaran hh20']];
  console.log(); ok.forEach(([n,v])=>console.log(`${v?' OK ':'GAGAL'}  ${n}`));
  console.log('\nerror:',err.length?err.join('; '):'(bersih)');
  await b.close(); process.exit(ok.every(([,v])=>v)?0:1);
})();
