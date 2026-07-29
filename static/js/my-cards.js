// Link yang disalin memakai host halaman ini, jadi kalau kamu membuka
// dashboard lewat tunnel, link yang tersalin ikut versi tunnel-nya.
document.querySelectorAll('.mc-copy').forEach(function (btn) {
  btn.addEventListener('click', function () {
    navigator.clipboard.writeText(btn.dataset.url).then(function () {
      var old = btn.textContent;
      btn.textContent = 'Tersalin ✓';
      setTimeout(function () { btn.textContent = old; }, 1400);
    });
  });
});
