const puppeteer=require('puppeteer-core');
const tidur=(ms)=>new Promise(r=>setTimeout(r,ms));
(async()=>{
const b=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:'new',args:['--no-sandbox']});
const p=await b.newPage();await p.setViewport({width:1440,height:900});
const err=[];p.on('pageerror',e=>err.push('[PAGEERROR] '+e.message));
p.on('requestfailed',r=>err.push('[GAGAL] '+r.url()));
await p.goto('http://localhost:8000/preview/game-8bit/',{waitUntil:'networkidle2'});
await tidur(700);
await p.evaluate(()=>window.show('kue'));await tidur(1400);
const K=async()=>p.evaluate(()=>{
 const st=document.getElementById('card-stage').getBoundingClientRect();
 const k=st.width/960;
 const R=(el)=>{const r=el.getBoundingClientRect();return{x:+((r.left-st.left)/k).toFixed(0),x2:+((r.right-st.left)/k).toFixed(0),y:+((r.top-st.top)/k).toFixed(0),y2:+((r.bottom-st.top)/k).toFixed(0)};};
 return{kue:R(document.querySelector('.kue-panggung')),
  lilin:[...document.querySelectorAll('.lilin')].map(e=>({...R(e),padam:e.classList.contains('padam')})),
  teman:[...document.querySelectorAll('.teman')].map(e=>({...R(e),hadap:e.querySelector('.sprite').style.getPropertyValue('--hadap'),baris:e.querySelector('.sprite').style.backgroundPositionY})),
  judul:R(document.querySelector('#kue .kepala'))};
});
console.log('AWAL', JSON.stringify(await K(),null,1));
await p.screenshot({path:'8bit/kue-awal.png'});
// Ketuk lilin 1 dan 2 beruntun.
await p.click('.lilin.l1');await tidur(120);await p.click('.lilin.l3');
await tidur(900);await p.screenshot({path:'8bit/kue-tiup.png'});
await tidur(2600);
console.log('SETELAH 2 KETUKAN', JSON.stringify((await K()).lilin.map(l=>l.padam)));
// Sisanya.
for(const s of ['.lilin.l2','.lilin.l4','.lilin.l5']){await p.click(s);await tidur(2400);}
await tidur(1200);
const akhir=await K();
console.log('SEMUA:', JSON.stringify(akhir.lilin.map(l=>l.padam)));
console.log('anim teman:', JSON.stringify(akhir.teman.map(t=>t.baris)));
console.log('partikel :', await p.evaluate(()=>document.getElementById('taman').childElementCount));
await p.screenshot({path:'8bit/kue-selesai.png'});
console.log('error:',err.length?err.join('\n'):'(bersih)');
await b.close();})();
