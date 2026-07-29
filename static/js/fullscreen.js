(function(){
  var fab = document.getElementById('fsFab');
  var root = document.documentElement;
  var request = root.requestFullscreen || root.webkitRequestFullscreen;
  if(!request) return;                       // iPhone Safari: tanpa tombol
  fab.classList.add('supported');

  function active(){
    return !!(document.fullscreenElement || document.webkitFullscreenElement);
  }
  function sync(){
    fab.classList.toggle('active', active());
    fab.setAttribute('aria-label',
      active() ? 'Keluar dari layar penuh' : 'Tampilkan layar penuh');
  }
  fab.addEventListener('click', function(){
    if(active()){
      (document.exitFullscreen || document.webkitExitFullscreen).call(document);
    } else {
      request.call(root);
    }
  });
  // Sinkron juga saat user keluar lewat tombol Esc / gestur sistem.
  document.addEventListener('fullscreenchange', sync);
  document.addEventListener('webkitfullscreenchange', sync);
})();
