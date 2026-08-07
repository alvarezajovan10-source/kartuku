const puppeteer=require('puppeteer-core');
const tidur=(ms)=>new Promise(r=>setTimeout(r,ms));
const CAP='sore itu hujan dan kita cuma duduk di teras sambil ketawa tanpa alasan. aku masih ingat semuanya sampai sekarang, tiap detiknya, sampai bagian kamu tumpahin teh ke sepatuku.';
(async()=>{
const b=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:'new',args:['--no-sandbox']});
const p=await b.newPage();await p.setViewport({width:1440,height:860});
await p.goto('http://localhost:8000/preview/game-8bit/',{waitUntil:'networkidle2'});
await tidur(700);await p.evaluate(()=>window.show('powerups'));await tidur(1000);
await p.evaluate(c=>{document.querySelectorAll('#kisi .cap').forEach(e=>e.textContent=c);},CAP);
await tidur(400);
for(let i=1;i<=4;i++) await p.click(`#kisi .ubin:nth-child(${i})`);
await tidur(900);
console.log(JSON.stringify(await p.evaluate(()=>{
 return [...document.querySelectorAll('#kisi .ubin')].map(u=>{
  const sisi=u.querySelector('.sisi.cerita').getBoundingClientRect();
  const gul=u.querySelector('[data-gulir]').getBoundingClientRect();
  const ub=u.getBoundingClientRect();
  return{
   gulirDiDalamSisi: gul.top>=sisi.top-1 && gul.bottom<=sisi.bottom+1 && gul.left>=sisi.left-1 && gul.right<=sisi.right+1,
   sisiDiDalamUbin: sisi.top>=ub.top-1 && sisi.bottom<=ub.bottom+1,
   potongSisi:getComputedStyle(u.querySelector('.sisi.cerita')).overflow,
   potongGulir:getComputedStyle(u.querySelector('[data-gulir]')).overflowY,
   panah:!!u.querySelector('.panah-gulir.tampak')};
 });
}),null,1));
await p.screenshot({path:'8bit/ubin-panjang.png'});
await b.close();})();
