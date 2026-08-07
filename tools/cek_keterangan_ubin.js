const puppeteer=require('puppeteer-core');
const tidur=(ms)=>new Promise(r=>setTimeout(r,ms));
const KET='hari pertama kita ketemu';
(async()=>{
const b=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:'new',args:['--no-sandbox']});
const p=await b.newPage();await p.setViewport({width:1600,height:1050});
const err=[];p.on('pageerror',e=>err.push('[PAGEERROR] '+e.message));
await p.goto('http://localhost:8000/create/game-8bit/',{waitUntil:'networkidle2'});
await tidur(2000);
let f=p.frames().find(x=>x!==p.mainFrame());
await f.evaluate(()=>window.show('powerups'));await tidur(1200);
await f.click('#kisi .ubin:nth-child(1)');await tidur(900);
const inp=await p.$('#pick-photo');
await inp.uploadFile('/Users/jepa/giftcard/static/img/sample/1.jpg');
await tidur(1500);
// Dialog potong: pakai fotonya.
await p.evaluate(()=>[...document.querySelectorAll('.crop-actions button')].find(b=>/Pakai foto/.test(b.textContent)).click());
await tidur(5000);
const st=await p.evaluate(()=>{const c=document.querySelector('#cap-bingkai');
 return{kotakKeterangan:!!c&&c.offsetParent!==null,batas:c&&c.maxLength,
  petunjuk:(document.querySelector('.ed-note')||{}).textContent?.trim()};});
console.log('panel foto:',JSON.stringify(st));
if(!st.kotakKeterangan){console.log('gagal unggah');console.log(err.join('\n'));await b.close();return;}
await p.click('#cap-bingkai');
await p.type('#cap-bingkai',KET,{delay:2});
await p.evaluate(()=>{const c=document.querySelector('#cap-bingkai');c.dispatchEvent(new Event('change',{bubbles:true}));c.blur();});
await tidur(3000);
f=p.frames().find(x=>x!==p.mainFrame());
const url=await f.url();
const p2=await b.newPage();await p2.setViewport({width:1600,height:1000});
await p2.goto(url,{waitUntil:'networkidle2'});await tidur(1600);
await p2.evaluate(()=>window.show('powerups'));await tidur(800);
console.log('keterangan dari server:',JSON.stringify(await p2.evaluate(()=>document.querySelector('#kisi .ubin .cap').textContent.trim())));
await p2.click('#kisi .ubin:nth-child(1)');await tidur(1000);
await p2.screenshot({path:'8bit/ket-cerita.png'});
await p2.click('#kisi .ubin:nth-child(1)');await tidur(1200);
await p2.screenshot({path:'8bit/ket-foto.png'});
console.log('error:',err.join('\n')||'(bersih)');
await b.close();})();
