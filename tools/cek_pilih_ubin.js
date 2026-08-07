const puppeteer=require('puppeteer-core');
const tidur=(ms)=>new Promise(r=>setTimeout(r,ms));
(async()=>{
const b=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:'new',args:['--no-sandbox']});
const p=await b.newPage();await p.setViewport({width:1600,height:1000});
await p.goto('http://localhost:8000/create/game-8bit/',{waitUntil:'networkidle2'});
await tidur(1900);
const f=p.frames().find(x=>x!==p.mainFrame());
await f.evaluate(()=>window.show('powerups'));await tidur(1200);

// Siapa yang sebenarnya tertimpa di titik tengah ubin, sebelum & sesudah dibuka?
const siapa=()=>f.evaluate(()=>{
 const u=document.querySelector('#kisi .ubin');
 const r=u.getBoundingClientRect();
 const el=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2);
 const t=document.querySelector('#kisi .tanya');
 return{kena:el.className||el.tagName, pilih:el.closest('[data-edit],[data-frame]')?.getAttribute('data-edit')||el.closest('[data-edit],[data-frame]')?.getAttribute('data-frame'),
  tanyaOpacity:getComputedStyle(t).opacity, tanyaPointer:getComputedStyle(t).pointerEvents,
  terbuka:u.classList.contains('terbuka')};
});
console.log('SEBELUM dibuka:',JSON.stringify(await siapa()));
await f.click('#kisi .ubin:nth-child(1)');await tidur(900);
console.log('SESUDAH dibuka:',JSON.stringify(await siapa()));
await b.close();})();
