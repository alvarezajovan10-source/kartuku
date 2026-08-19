/* Muat di beberapa ukuran layar: halaman A4 harus MUAT UTUH di semuanya. */
const puppeteer = require('puppeteer-core');
const UKURAN=[['HP tegak',390,844],['HP kecil',360,640],['HP mendatar',844,390],
              ['tablet',820,1180],['laptop',1440,900],['layar besar',1920,1200]];
(async()=>{
  const b=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:'new',args:['--no-sandbox']});
  for(const [nama,w,h] of UKURAN){
    const p=await b.newPage(); await p.setViewport({width:w,height:h});
    await p.goto('http://localhost:8000/g/uji-valentine/',{waitUntil:'networkidle2'});
    await new Promise(r=>setTimeout(r,500));
    const o=await p.evaluate(()=>{
      const k=parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--k'));
      const r=document.querySelector('#hal1 .muka.depan').getBoundingClientRect();
      const nav=document.querySelector('.nav').getBoundingClientRect();
      return {k:+k.toFixed(3),x:+r.x.toFixed(0),y:+r.y.toFixed(0),w:+r.width.toFixed(0),h:+r.height.toFixed(0),
              navAtas:+nav.top.toFixed(0)};
    });
    const muat = o.x>=-1 && o.y>=-1 && o.x+o.w<=w+1 && o.y+o.h<=h+1;
    const bentrok = o.y+o.h > o.navAtas;
    console.log(`${nama.padEnd(12)} ${String(w).padStart(4)}x${String(h).padStart(4)}  k=${String(o.k).padEnd(5)} halaman ${o.w}x${o.h} @ ${o.x},${o.y}  ${muat?'MUAT':'TERPOTONG'}${bentrok?'  nav menimpa halaman':''}`);
    await p.close();
  }
  await b.close();
})();
