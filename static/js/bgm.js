/* Musik latar kartu — pasangan dari cards/_bgm.html.
 *
 * Memakai IFrame Player API resmi YouTube, bukan postMessage manual. API resmi
 * menangani `origin` sendiri (sumber "Error 153"), dan yang terpenting mengirim
 * kode error lewat onError sehingga kegagalan bisa dijelaskan ke penerima
 * alih-alih gagal senyap.
 *
 * Id video dan mode debug dibaca dari data-attribute #bgm — dulu keduanya
 * dicetak langsung oleh Django ke dalam skrip ini.
 */
(function(){
  var holder = document.getElementById('bgm');
  var fab = document.getElementById('bgmFab');
  var note = document.getElementById('bgmNote');
  var label = fab.querySelector('.bgm-label');
  var vid = holder.dataset.vid;
  var debug = holder.dataset.debug === '1';
  var player = null, ready = false, playing = false, wantPlay = false;

  function say(html, dead){
    note.innerHTML = html;
    note.classList.add('on');
    if(dead){ fab.disabled = true; fab.classList.remove('fresh','playing'); }
  }
  function emit(){
    document.dispatchEvent(new CustomEvent('bgmstate', {detail:{playing:playing}}));
  }
  function apply(){
    fab.classList.toggle('playing', playing);
    label.textContent = playing ? 'jeda' : 'putar lagu';
    fab.setAttribute('aria-label', playing ? 'Jeda lagu' : 'Putar lagu di kartu ini');
    emit();
  }

  window.onYouTubeIframeAPIReady = function(){
    player = new YT.Player('bgm', {
      videoId: vid,
      playerVars: {controls: debug ? 1 : 0,
                   playsinline: 1, rel: 0, loop: 1, playlist: vid},
      events: {
        onReady: function(){
          ready = true;
          if(wantPlay){ player.playVideo(); }
          if(debug){ say('Pemutar siap. Klik "putar lagu".'); }
        },
        onStateChange: function(e){
          if(e.data === YT.PlayerState.PLAYING){ playing = true; apply(); }
          else if(e.data === YT.PlayerState.PAUSED || e.data === YT.PlayerState.ENDED){
            playing = false; apply();
          }
        },
        onError: function(e){
          // 101 & 150 = pemutaran ditolak. Hati-hati menafsirkannya: YouTube
          // juga membalas 150 kalau halaman diakses lewat ALAMAT IP mentah
          // (127.0.0.1 / 192.168.x). Nama host "localhost" dan domain publik
          // diterima. Jadi di alamat IP, error ini belum tentu soal videonya.
          if(e.data === 101 || e.data === 150){
            if(/^\d+\.\d+\.\d+\.\d+$/.test(window.location.hostname)){
              say('Lagu tidak bisa diputar lewat alamat IP — ini batasan '
                + 'YouTube, bukan masalah lagunya. Buka halaman ini lewat '
                + '<b>localhost</b> atau domain aslinya.', true);
              return;
            }
            say('Lagu ini tidak boleh diputar di luar YouTube. '
              + '<a href="https://www.youtube.com/watch?v=' + vid
              + '" target="_blank" rel="noopener">Dengar di YouTube</a>', true);
          } else if(e.data === 100){
            say('Lagu tidak ditemukan — mungkin sudah dihapus.', true);
          } else {
            say('Lagu gagal dimuat (kode ' + e.data + ').', true);
          }
        }
      }
    });
  };

  fab.addEventListener('click', function(){
    if(!ready){ wantPlay = true; say('Menyiapkan lagu…'); return; }
    if(playing){ player.pauseVideo(); } else { player.playVideo(); }
  });
  window.bgmToggle = function(){ fab.click(); };

  // Muat API resmi.
  var tag = document.createElement('script');
  tag.src = 'https://www.youtube.com/iframe_api';
  tag.onerror = function(){ say('Gagal memuat pemutar — periksa koneksi.', true); };
  document.head.appendChild(tag);
})();
