/* ---------- build ransom letters ---------- */
const variants = ['v1','v2','v3','v4','v5','v6'];
// Diekspos supaya editor bisa membangun ulang saat teksnya diubah.
window.buildRansom = function (el) {
  el.textContent = '';
  let i = 0;

  // Tiap KATA dibungkus .rw sendiri. Dulu semua huruf jadi item flex langsung,
  // sehingga flex-wrap boleh memutus di tengah kata — "SELAMAT" bisa pecah
  // jadi "SELA" dan "MAT" di baris berbeda. Membungkus per kata membuat
  // pemutusan hanya terjadi di spasi, seperti teks biasa.
  const huruf = (ch) => {
    const s = document.createElement('span');
    s.className = 'rl ' + variants[Math.floor(Math.random() * variants.length)];
    s.textContent = ch;
    s.style.setProperty('--r', (Math.random() * 16 - 8).toFixed(1) + 'deg');
    s.style.setProperty('--d', (i++ * 0.06).toFixed(2) + 's');
    return s;
  };

  // Enter dari user = pindah baris.
  (el.dataset.text || '').split('\n').forEach((baris, bi) => {
    if (bi) {
      const br = document.createElement('span');
      br.style.flexBasis = '100%';
      el.appendChild(br);
    }
    baris.split(' ').forEach((kata, ki) => {
      // Flexbox membuang spasi teks; nbsp pun tak memberi jarak antar item flex.
      if (ki) {
        const sp = document.createElement('span');
        sp.style.width = '.55em';
        el.appendChild(sp);
      }
      if (!kata) return;
      const grup = document.createElement('span');
      grup.className = 'rw';
      [...kata].forEach((ch) => grup.appendChild(huruf(ch)));
      el.appendChild(grup);
    });
  });
  el.classList.add('in');
};
document.querySelectorAll('.ransom').forEach(el => window.buildRansom(el));

/* ---------- scroll reveal ---------- */
const io = new IntersectionObserver((entries) => {
  entries.forEach(e => { if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } });
}, { threshold: 0.25 });
document.querySelectorAll('.reveal, .ransom').forEach(el => io.observe(el));

/* ---------- falling dried leaves + petals + hearts ---------- */
const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const layer = document.getElementById('leaves');
const leafColors = ['#b5722e','#c98a3a','#9c5a2a','#8a6d2f','#c46a4e'];
const petalColors = ['#e8a9b4','#e6c0a0'];

function makeSVG(kind){
  const ns='http://www.w3.org/2000/svg';
  const svg=document.createElementNS(ns,'svg');
  svg.setAttribute('viewBox','0 0 24 24');
  if(kind==='leaf'){
    const p=document.createElementNS(ns,'path');
    p.setAttribute('d','M12 2C6 6 4 14 12 22 20 14 18 6 12 2z');
    p.setAttribute('fill', leafColors[Math.floor(Math.random()*leafColors.length)]);
    const v=document.createElementNS(ns,'path');
    v.setAttribute('d','M12 4v16'); v.setAttribute('stroke','rgba(60,30,10,.35)'); v.setAttribute('stroke-width','1'); v.setAttribute('fill','none');
    svg.append(p,v);
  } else if(kind==='petal'){
    const p=document.createElementNS(ns,'path');
    p.setAttribute('d','M12 3C7 7 7 17 12 21 17 17 17 7 12 3z');
    p.setAttribute('fill', petalColors[Math.floor(Math.random()*petalColors.length)]);
    svg.append(p);
  } else {
    const p=document.createElementNS(ns,'path');
    p.setAttribute('d','M12 21s-7.5-4.9-10-9.2C.3 8.6 1.7 5 5 5c2 0 3.2 1.2 4 2.3C9.8 6.2 11 5 13 5c3.3 0 4.7 3.6 3 6.8C19.5 16.1 12 21 12 21z');
    p.setAttribute('fill','rgba(232,143,160,.9)');
    svg.append(p);
  }
  return svg;
}

function spawn(){
  const roll=Math.random();
  const kind = roll<0.72 ? 'leaf' : roll<0.9 ? 'petal' : 'heart';
  const size = kind==='leaf' ? 16+Math.random()*16 : 12+Math.random()*8;
  const el=makeSVG(kind);
  const startX=Math.random()*100;
  const drift=(Math.random()*24-12);
  el.style.cssText=`position:absolute;top:-6%;left:${startX}vw;width:${size}px;height:${size}px;opacity:${0.5+Math.random()*0.4}`;
  layer.appendChild(el);
  const dur=9000+Math.random()*7000;
  el.animate([
    {transform:`translate(0,0) rotate(0deg)`},
    {transform:`translate(${drift*0.5}vw,55vh) rotate(${180*(Math.random()<.5?1:-1)}deg)`,offset:.5},
    {transform:`translate(${drift}vw,110vh) rotate(${360*(Math.random()<.5?1:-1)}deg)`}
  ],{duration:dur,easing:'cubic-bezier(.45,.05,.55,.95)'}).onfinish=()=>el.remove();
}

if(!reduce){
  for(let i=0;i<10;i++) setTimeout(spawn, Math.random()*4000);
  setInterval(spawn, 900);
} else {
  for(let i=0;i<5;i++) spawn();
}
