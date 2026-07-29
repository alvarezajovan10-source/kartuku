const scenes = document.querySelectorAll('.scene');
function show(id){
  const el = document.getElementById(id);
  if(!el) return;                       // bagian bisa absen kalau datanya kosong
  scenes.forEach(s => s.classList.toggle('active', s.id === id));
  el.scrollTop = 0;
}
// ── Musik latar (komponen bersama cards/_bgm.html) ─────────────────
// Piringan hitam ikut status musik: berhenti berputar saat dijeda,
// dan bisa diklik sebagai tombol putar/jeda kedua.
document.addEventListener('bgmstate', (e) => {
  document.querySelectorAll('.vinyl').forEach(
    v => v.classList.toggle('paused', !e.detail.playing)
  );
});
if(window.bgmToggle){
  document.querySelectorAll('.vinyl').forEach(v => {
    v.style.cursor = 'pointer';
    v.addEventListener('click', () => window.bgmToggle());
  });
}

// cover seal + hero flow
const envelope = document.getElementById('envelope');
document.getElementById('sealBtn').addEventListener('click', () => show('hero'));
envelope.addEventListener('click', (e) => {
  if(e.target.closest('#sealBtn')) return; show('hero');
});
// all data-go buttons
document.querySelectorAll('[data-go]').forEach(b =>
  b.addEventListener('click', () => show(b.dataset.go))
);
// cake: blow out candles + reveal wish + tiny confetti
const cakeWrap = document.getElementById('cakeWrap');
cakeWrap.addEventListener('click', () => {
  if(cakeWrap.classList.contains('blown')) return;   // sekali tiup saja
  cakeWrap.classList.add('blown');
  document.getElementById('wish').classList.add('show');
  if(window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  for(let i=0;i<24;i++){
    const c=document.createElement('div');
    c.style.cssText=`position:fixed;top:40%;left:50%;width:8px;height:8px;border-radius:2px;pointer-events:none;z-index:99;background:${['#f7d774','#e78ea0','#7fb0d6','#faf2e4'][i%4]}`;
    document.body.appendChild(c);
    const ang=Math.random()*Math.PI*2, dist=120+Math.random()*160;
    c.animate([
      {transform:'translate(-50%,-50%) rotate(0)',opacity:1},
      {transform:`translate(${Math.cos(ang)*dist}px,${Math.sin(ang)*dist+120}px) rotate(${Math.random()*720}deg)`,opacity:0}
    ],{duration:1200+Math.random()*600,easing:'cubic-bezier(.2,.6,.3,1)'}).onfinish=()=>c.remove();
  }
});
