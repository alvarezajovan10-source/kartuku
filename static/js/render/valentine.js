/* VALENTINE STORY — berpindah halaman majalah.

   TIGA MEKANIK hidup berdampingan di berkas ini, dipilih lewat satu kata
   `GAYA` (cari di bawah). Yang dipakai sejak 16 Agustus 2026:

     "partikel" — halaman MEMUDAR di tempat sambil melepas debu berpendar
                  yang naik, berwarna mengikuti halamannya. Tidak ada yang
                  diputar sama sekali; seluruh mesin balik lembar di bawah
                  tidak berjalan. Permintaan pemilik situs.

   Dua sisanya — "bilah" dan "rotasi" — membalik lembar sungguhan dan
   dijelaskan panjang lebar di bawah. Keduanya SENGAJA dipertahankan utuh
   atas permintaan pemilik situs: keputusan animasi template ini sudah
   berbalik tiga kali, dan membangun ulang jalur bilah memakan berjam-jam
   pengukuran. Yang tidak dipakai tidak berjalan sama sekali.

   ── Sisanya di bawah ini berlaku untuk gaya "bilah"/"rotasi" ──────────

   HALAMANNYA MELENGKUNG, TIDAK DIPUTAR. Ini pembeda utamanya, dan sekali
   dilanggar seluruh rasanya hilang.

   Versi sebelumnya memakai satu transform 3D pada satu bidang datar
   (`rotateY` pada .lembar). Bidang datar yang diputar tetap bidang datar:
   siluetnya selalu segi empat bertepi lurus, dan mata membacanya sebagai
   kaca atau keramik, bukan kertas. Memperlambatnya, memberi bayangan, dan
   memberi sedikit skew tidak menolong — semuanya hiasan di atas geometri
   yang salah.

   Sekarang halaman dipecah jadi SEPULUH BILAH tegak, dan posisi tiap bilah
   DIAKUMULASI dari bilah sebelumnya (lihat taruh()). Karena disambung ujung
   ke ujung, siluetnya jadi kurva sungguhan, bukan sepuluh kotak yang
   kebetulan miring. Ketajaman lipatannya mengendur seiring putaran, jadi
   lipatan itu MERAMBAT dari tepi kanan ke punggung buku — seperti kertas
   yang ditarik jari.

   Kenapa bilah CSS, bukan WebGL atau Canvas: isi halaman ini DOM hidup —
   teks yang bisa disunting dan bingkai foto yang bisa diklik. Dua-duanya
   butuh halaman jadi tekstur lebih dulu, dan tidak ada cara memotret DOM
   secara setia tanpa dependensi berat. Dengan bilah, hurufnya tetap huruf
   sungguhan.

   SATU PEGAS untuk seret DAN lepas. Selama diseret, sasaran pegas adalah
   posisi jari — lembarnya MENGEJAR jari, tidak menempel mati padanya, dan
   dari situlah datang hambatan serta kelambanan. Saat dilepas, sasarannya
   jadi 0 atau 1 dan kecepatan jari jadi kecepatan awal pegas. Satu rumus
   untuk dua keadaan berarti tidak ada patahan di detik jari diangkat —
   patahan itu yang membuat gerakan terbaca sebagai animasi, bukan kertas.

   Kontrak renderer berbabak (lihat static/js/card-frame.js):
   - tiap halaman <section class="scene"> ber-id
   - halaman yang sedang dibaca punya class .active
   - window.show(id) wajib ada supaya editor bisa melompat antar halaman
*/
(function () {
  "use strict";

  var lembar = [].slice.call(document.querySelectorAll(".lembar"));
  var buku = document.getElementById("buku");
  var dotsEl = document.getElementById("dots");
  var prevBtn = document.getElementById("prev");
  var nextBtn = document.getElementById("next");
  var petunjuk = document.getElementById("petunjuk");
  var hemat = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* GAYA membalik halaman. Dua-duanya lengkap dan bisa dipakai; ganti
     satu kata ini saja untuk berpindah.

       "rotasi" — satu bidang diputar rotateY dengan transisi CSS 0,6 detik.
                  Inilah yang diminta pemilik situs (mengikuti spek gaya
                  heyzine). Sederhana, ringan, dan gerakannya rapi.
       "bilah"  — halaman dipecah sepuluh bilah tegak yang melengkung
                  (lihat taruh()). Lebih menyerupai kertas sungguhan, tapi
                  jauh lebih banyak kodenya.

     Catatan jujur: "bilah" dibangun justru karena "rotasi" pernah dinilai
     "seperti keramik kaca" — bidang datar yang diputar siluetnya selalu
     segi empat bertepi lurus. Pemilik situs sudah menimbang itu dan tetap
     memilih "rotasi". Kodenya tidak dihapus supaya keputusan ini bisa
     dibalik tanpa membangun ulang.

     14 Agu 2026 — DIBALIK, dan inilah pembalikan yang KEDUA. Keluhannya
     kembali persis sama, cuma metaforanya berganti: "seperti menarik kayu".
     Itu memang sifat bidang datar yang diputar, bukan cacat penyetelan, dan
     tidak ada nilai transisi yang bisa memperbaikinya — karena itu jalurnya
     yang diganti, bukan angkanya. Kelengkungannya sekaligus diperdalam
     (lihat LURUH) atas permintaan pemilik situs: "seperti membuka kain".

     Jalur "rotasi" TETAP tidak dihapus. Sudah berbalik dua kali; anggap
     saja akan berbalik lagi.

     16 Agu 2026 — DIGANTI LAGI, kali ini bukan menyetel melainkan mengganti
     mekaniknya: pemilik situs meminta halaman TIDAK dibalik sama sekali,
     melainkan MEMUDAR di tempat sambil melepas debu berpendar yang naik ke
     atas, berwarna mengikuti halamannya. Nilai barunya "partikel".

     Kedua jalur balik lembar di atas TETAP UTUH dan bisa dihidupkan dengan
     mengganti satu kata ini. Itu permintaan eksplisit pemilik situs, dan
     alasannya kuat: keputusan animasi di template ini sudah berbalik tiga
     kali, sedangkan membangun ulang jalur bilah memakan berjam-jam
     pengukuran. Yang tidak dipakai tidak berjalan sama sekali — cek GAYA
     di taruh(), ke(), dan penangan pointer. */
  var GAYA = "partikel";

  /* ── mode "partikel" ─────────────────────────────────────────────────
     Lama satu peralihan. "Perlahan" yang diminta: cukup lambat untuk
     terbaca sebagai memudar, cukup cepat untuk tidak menghalangi orang
     yang ingin membaca cepat. */
  var LAMA_LARUT = 2500;

  /* 2500 ms, naik dari 1100 (19 Agu 2026, permintaan pemilik situs: "lebih
     santai"). Kecepatan naik debunya WAJIB ikut turun, dan itu bukan selera
     melainkan aritmetika: pada 0,10-0,34 px/ms yang lama, butir tercepat
     menempuh 850 px dalam 2,5 detik — sedangkan halamannya cuma setinggi
     552 px. Seluruh debu akan sudah keluar layar jauh sebelum peralihannya
     selesai, dan yang tersisa di paruh kedua cuma halaman memudar tanpa
     debu sama sekali. Angka di bawah menjaga jarak tempuhnya kira-kira
     sama seperti dulu (110-375 px), cuma ditempuh lebih lama. */
  var JUMLAH_DEBU = 260;      // "ramai", tapi masih 60 fps di HP kelas bawah
  var DEBU_NAIK = [0.044, 0.150];  // px per ms, ke atas
  var DEBU_SAMPING = 0.020;        // amplitudo goyang mendatar
  var DEBU_UKURAN = [0.9, 4.2];    // jari-jari px, sebaran dilebarkan
  var PETAK_WARNA = 12;       // sisi kisi cuplikan warna halaman (12x17)

  /* Sebagian kecil butir berbentuk HATI, sisanya tetap debu bulat.
     Sepersepuluh, dan porsi itu sengaja kecil: hati adalah AKSEN. Waktu
     dicoba pada porsi besar, efeknya berhenti terbaca sebagai "halaman
     larut jadi debu" dan berubah jadi hujan hiasan yang menempel di depan
     kartu. */
  var PORSI_HATI = 0.10;

  /* Ruang di LUAR kertas tempat debu boleh melayang sebelum habis, dalam px
     desain. Kertas dan bingkai kartu itu kotak yang sama persis (390x552),
     jadi ruang ini tidak ada dengan sendirinya — kanvasnya yang dilebarkan
     ke luar sebanyak ini di keempat sisi.

     Dibatasi #card-viewport yang overflow:hidden, jadi debu tidak pernah
     bisa lolos ke luar bingkai kartu betapa pun lebar layarnya. */
  var TEPI_DEBU = 44;

  /* Pudar di perbatasan: mulai meredup PUDAR_TEPI[0] px sebelum tepi kertas,
     habis PUDAR_TEPI[1] px sesudahnya. Menstraddle tepinya, bukan berhenti
     di situ — itu yang membuat debunya terbaca melayang keluar, bukan
     terpotong penggaris.

     Perlu karena di layar lebar tepi ATAS kertas berimpit dengan tepi
     #card-viewport (terukur: pada 1440x900 halaman menempati y 0..846 dari
     900), jadi tanpa peredupan ini debu yang naik akan tergunting rata di
     garis yang persis lurus. */
  var PUDAR_TEPI = [20, 30];

  // Kurva & lama transisi persis seperti spek yang diminta.
  var LAMA_ROTASI = 600;
  var KURVA_ROTASI = "cubic-bezier(.645,.045,.355,1)";

  /* Jumlah bilah. Tetap sama di semua perangkat — itu yang dipilih pemilik
     situs, dan sifat itu dipertahankan; yang berubah cuma angkanya.

     Naik 10 -> 12 (14 Agu 2026), hasil tawar-menawar DUA artefak yang
     tarik-menarik. Diukur, bukan dikira:

         bilah   seam Safari/baris   faceting
            10          5,45          12,32 deg
            12          6,05          10,12 deg   <- dipakai
            14          7,97           9,14 deg
            16          8,99           7,94 deg

     Menambah bilah menghaluskan lengkungnya (faceting turun) tapi MENAMBAH
     garis gelap tegak antar bilah di Safari — satu garis per batas bilah.
     Kontrol halaman diam mengukur 0,00 garis, jadi garis-garis itu memang
     artefak, bukan tekstur foto. Kelengkungan (LURUH) tidak berpengaruh
     sama sekali pada seam: 16 bilah pada LURUH 1,0 dan 0,30 sama-sama 8,96.

     Dua belas dipilih pemilik situs: seam turun sepertiga dari 16, dan
     faceting 10,1 derajat masih di dalam jatah 15 derajat yang diberikan.

     Harganya DOM: tiap bilah memuat klon utuh .kertas. Kalau
     tools/cek_valentine_beban.js jatuh di bawah 60 fps, turunkan ke 14 atau
     12 dan kompensasi dengan LURUH yang lebih besar — jangan didiamkan. */
  var N_BILAH = 12;
  var W0 = 390;           // lebar kanvas kanonis (lihat card-stage.css)
  var H0 = 551.6;
  var TINDIH = 1.5;       // px bilah saling menimpa, menutup celah rambut

  var MIRING_MAKS = 16;   // derajat pelintiran lipatan saat dipegang di ujung
  var GELOMBANG = 7;      // derajat gelombang kedua — busur C tidak sendirian
  var CAHAYA = 32 * Math.PI / 180;   // arah sumber cahaya terhadap halaman
  var AMBANG = 0.5;       // lewat separuh = lepas, kurang = balik lagi
  var LAJU_LEMPAR = 0.55; // px/ms; secepat ini dianggap sengaja dilempar
  var KUNCI = 8;          // px sebelum arah seretan diputuskan
  var DEKAT = 1;          // lembar yang tetap dimuat sebelum halaman ini
  var DEPAN = 2;          // ... dan sesudahnya

  /* Pegas. k menentukan cepatnya, redaman menentukan lembutnya mendarat.
     Disetel supaya perjalanan penuh lewat tombol mendarat di sekitar 1,4
     detik — angka yang dipilih pemilik situs. Karena ini benda fisik,
     lamanya TIDAK persis sama tiap kali: jarak dan kecepatan lemparan ikut
     menentukan, seperti kertas sungguhan. */
  var PEGAS_K = 25;
  var PEGAS_REDAM = 2 * Math.sqrt(25) * 0.92;
  var DIAM_POSISI = 0.0015;   // sedekat ini ke sasaran, dianggap sampai
  var DIAM_LAJU = 0.02;

  /* Simpangan tetap per bilah, bukan acak tiap frame. Tepi kertas sungguhan
     tidak pernah sempurna; tanpa ini lipatannya terlihat seperti rumus.

     Dulu ini array sepuluh angka yang diketik tangan — dan itu mengunci
     N_BILAH di sepuluh secara diam-diam. Menaikkan N_BILAH membuat
     SIMPANG[10..] jadi undefined, `d` jadi NaN, seluruh string transform
     tidak sah, dan LEMBARNYA HILANG dari layar tanpa satu pun error di
     console. Sekarang dibangkitkan sepanjang N_BILAH.

     Tetap DETERMINISTIK (bukan Math.random) dengan alasan yang sama seperti
     dulu: simpangan yang diundi ulang tiap frame membuat tepi lembarnya
     bergetar. Deret sin-fract di bawah memberi angka yang tampak acak tapi
     selalu sama tiap kali halaman dimuat. */
  var SIMPANG = [];
  for (var s = 0; s < N_BILAH; s++) {
    var acak = Math.sin((s + 1) * 12.9898) * 43758.5453;
    SIMPANG.push(((acak - Math.floor(acak)) * 2 - 1) * 0.38);
  }

  var idx = 0;
  var seret = null;       // { i, y0, x0, mundur, t, waktu, laju }
  var animasi = null;
  var abaikanKlik = false;

  var jatuhnya = lembar.map(function (el) {
    return el.querySelector(".depan > .jatuh");
  });
  var redupPolos = lembar.map(function (el) {
    return el.querySelector(".depan > .redup");
  });

  function jepit(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
  function halus(v) { return v * v * (3 - 2 * v); }   // smoothstep

  /* ── rig bilah ────────────────────────────────────────────────────────
     Satu rig dipakai bergantian: hanya satu lembar yang pernah berputar
     pada satu waktu. Tiap bilah adalah JENDELA ke satu potongan tegak
     halaman — di dalamnya ada klon utuh .kertas yang digeser ke kiri,
     lalu dipotong oleh overflow bilahnya.

     overflow:hidden dipasang di MUKA, bukan di bilahnya. Elemen ber-overflow
     memaksa isinya jadi datar, dan bilah harus tetap preserve-3d supaya
     sisi depan dan belakangnya bisa saling membelakangi. */
  var rig = document.getElementById("rig");
  var bilah = [];
  var rigUntuk = -1;
  var rigAktif = false;

  /* Bilah TIDAK selebar sama. Lengkungan selalu paling tajam di tepi bebas
     (turunan sudutnya maksimal di situ, berapa pun tahap putarannya), jadi
     di sanalah resolusinya dibutuhkan. Dengan lebar sama rata, sudut antar
     bilah di dekat lipatan melompat belasan derajat sekaligus dan hurufnya
     terlihat patah di batas bilah.

     Batas bilah: u = (k/N)^0.5. Bukan angka karangan — kelengkungan di
     sini sebanding u kuadrat, jadi pangkat itu yang membuat SUDUT tiap
     bilah kira-kira sama besar, bukan lebarnya. Pada 16 bilah hasilnya
     bilah kiri 25% lebar halaman (di sana hampir tidak melengkung, satu
     bidang datar sudah cukup) dan bilah kanan 3,2% (di sana lengkungnya
     tajam). Lompatan sudut antar bilah tetap di bawah 8 derajat di seluruh
     lembar — di atas itu faceting-nya terlihat sebagai kisi-kisi jendela.

     Dihitung sekali; mengubah lebar tiap frame akan memicu layout ulang. */
  var BATAS = [];
  for (var q = 0; q <= N_BILAH; q++) {
    BATAS.push(Math.pow(q / N_BILAH, 0.5));
  }
  function kiriBilah(k) { return BATAS[k] * W0; }
  function lebarBilah(k) { return (BATAS[k + 1] - BATAS[k]) * W0; }

  function bangunRig() {
    if (!rig || bilah.length) return;
    for (var k = 0; k < N_BILAH; k++) {
      var b = document.createElement("div");
      b.className = "pias";
      b.style.left = kiriBilah(k).toFixed(2) + "px";
      b.style.width = (lebarBilah(k) + TINDIH).toFixed(2) + "px";
      var sisi = {};
      ["depan", "belakang"].forEach(function (nama) {
        var muka = document.createElement("div");
        muka.className = "pias-muka " + nama;
        var jendela = document.createElement("div");
        jendela.className = "pias-jendela";
        jendela.style.left = (-kiriBilah(k)).toFixed(2) + "px";
        jendela.style.width = W0 + "px";
        jendela.style.height = H0 + "px";
        muka.appendChild(jendela);
        var redup = document.createElement("span");
        redup.className = "pias-redup";
        muka.appendChild(redup);
        b.appendChild(muka);
        sisi[nama] = { jendela: jendela, redup: redup };
      });
      rig.appendChild(b);
      bilah.push({ el: b, depan: sisi.depan, belakang: sisi.belakang });
    }
  }

  /* Isi rig dengan salinan halaman ke-i. Dipanggil saat putaran DIMULAI —
     bukan tiap frame, dan bukan saat jari sudah bergerak: sepuluh klon
     sekaligus memakan beberapa milidetik, dan milidetik itu paling
     kentara tepat di awal gerakan. */
  function isiRig(i) {
    // Gaya "rotasi" tidak memakai bilah sama sekali. Tanpa penjaga ini,
    // sepuluh klon halaman tetap dibuat tiap balikan — kerja penuh yang
    // hasilnya tidak pernah terlihat.
    if (GAYA !== "bilah") return;
    bangunRig();
    if (!rig || rigUntuk === i) return;
    var sumber = lembar[i] && lembar[i].querySelector(".depan > .kertas");
    if (!sumber) return;
    // Warna kertas halaman ini disetel lewat #halN di CSS. Klon kehilangan
    // id-nya, jadi nilainya dibawa ke rig sebagai gaya sebaris.
    rig.style.setProperty(
      "--kertas-bg",
      getComputedStyle(lembar[i]).getPropertyValue("--kertas-bg")
    );
    for (var k = 0; k < N_BILAH; k++) {
      var klon = sumber.cloneNode(true);
      // Atribut editor dibuang: kalau tidak, card-frame.js melihat elemen
      // kembar dan sorotan pilihannya bisa mendarat di klon, bukan di
      // halaman aslinya.
      klon.removeAttribute("id");
      [].forEach.call(klon.querySelectorAll("[id],[data-edit],[data-frame]"),
        function (el) {
          el.removeAttribute("id");
          el.removeAttribute("data-edit");
          el.removeAttribute("data-frame");
        });
      var j = bilah[k].depan.jendela;
      j.innerHTML = "";
      j.appendChild(klon);
    }
    rigUntuk = i;
  }

  function pakaiRig(i) {
    if (rigAktif) return;
    isiRig(i);
    if (!rig || !bilah.length) return;
    rig.style.zIndex = String(20 - i);
    rig.classList.add("jalan");
    lembar[i].classList.add("diganti-rig");
    rigAktif = true;
  }

  function lepasRig() {
    if (!rigAktif) return;
    rig.classList.remove("jalan");
    if (lembar[rigUntuk]) lembar[rigUntuk].classList.remove("diganti-rig");
    rigAktif = false;
  }

  var LENTUR = 3;   // makin besar, lipatan makin mengumpul di tepi bebas

  /* Pangkat peluruhan kelengkungan — SATU angka yang mengatur seberapa
     "kain" rasanya. Makin kecil, makin dalam lengkungnya. Tabelnya ada di
     taruh(); 1 mengembalikan perilaku lama yang terasa seperti papan. */
  var LURUH = 0.30;

  function sudutDi(u, A, tinggal, busur) {
    /* Gelombang kedua diredam di kedua ujungnya (dikali sin(pi*u)). Tanpa
       redaman itu, kemiringannya justru paling curam TEPAT di tepi bebas —
       tempat bilahnya paling rapat — dan lompatan sudut antar bilah di situ
       kembali terlihat sebagai kisi-kisi. */
    return A * (1 - tinggal * (1 - Math.pow(u, LENTUR)))
         + GELOMBANG * Math.sin(2 * Math.PI * u) * Math.sin(Math.PI * u) * busur;
  }

  /* Gelap digradasi MELINTASI bilah, dari sudut batas kirinya ke
     batas kanannya. Satu nilai rata per bilah membuat halaman terlihat
     berpita sepuluh kolom, dan pita itu merusak ilusi kertas lebih parah
     daripada sudut-sudut geometrinya sendiri. */
  function kelam(r, kuat) {
    return jepit((1 - Math.cos(r - CAHAYA)) / 2) * kuat;
  }
  function gelap(rKi, rKa, kuat) {
    return pita("24,12,9", rKi, rKa, function (r) { return +kelam(r, kuat); });
  }

  /* Gradien dengan LIMA titik per bilah, bukan dua.

     Dengan dua titik, tiap bilah menggambar tali busur lurus di antara dua
     cuplikan. Nilainya memang bersambung di batas bilah, tapi KEMIRINGANNYA
     patah — dan patahan kemiringan pada permukaan terang justru yang paling
     mudah dilihat mata (efek pita Mach). Itulah "retakan kaca" yang
     terlihat: bukan celah, bukan bayangan dobel, melainkan patahan
     kemiringan cahaya di sepuluh tempat sekaligus.

     Lima titik per bilah = lima puluh cuplikan sepanjang halaman; sisa
     patahannya turun di bawah ambang yang bisa dilihat. Ini tetap murah:
     yang berubah cuma string, dan lebar elemennya tidak ikut berubah jadi
     tidak memicu layout. */
  function pita(warna, r0, r1, hitung) {
    var stop = [];
    for (var n = 0; n <= 4; n++) {
      var r = r0 + (r1 - r0) * (n / 4);
      stop.push("rgba(" + warna + "," + hitung(r).toFixed(3) + ") " + (n * 25) + "%");
    }
    return "linear-gradient(90deg," + stop.join(",") + ")";
  }

  /* ── menggambar satu lembar pada posisi t ──────────────────────────────
     t = 0 lembar masih rata di kanan, t = 1 sudah berpindah ke kiri.
     pegang = 0 di tepi atas, 1 di tepi bawah, 0,5 di tengah. */
  /* ── debu berpendar ───────────────────────────────────────────────────
     Satu kanvas dipakai ulang untuk seluruh peralihan. Partikel digambar
     ke kanvas, BUKAN sebagai elemen DOM: 190 elemen yang digeser tiap frame
     memaksa browser menghitung ulang tata letak enam puluh kali sedetik,
     dan itu persis yang dihindari di seluruh template ini. */
  var kanvas = document.getElementById("debu");
  var ktx = kanvas ? kanvas.getContext("2d") : null;
  var debuJalan = 0;

  /* CSS ikut bercabang lewat atribut ini, jadi mengganti GAYA cukup satu
     kata di atas — tidak ada aturan CSS yang perlu dicabut manual. */
  if (buku) buku.setAttribute("data-gaya", GAYA);

  /* Kanvas mengikuti ukuran halaman, dan halaman diskalakan ulang tiap kali
     jendelanya berubah (lihat card-stage.js). Diukur ulang saat peralihan
     dimulai juga, tapi ini menangkap perubahan yang terjadi di antaranya. */
  window.addEventListener("resize", ukurKanvas);
  window.addEventListener("orientationchange", ukurKanvas);

  function ukurKanvas() {
    if (!kanvas || !buku) return;

    /* offsetWidth/Height, BUKAN getBoundingClientRect().

       Ini pernah salah dan cacatnya cuma muncul di layar lebar.
       getBoundingClientRect() mengembalikan piksel SESUDAH panggungnya
       diskalakan (#card-stage memakai transform: matrix(...)), sedangkan
       style.width berlaku SEBELUM penskalaan — jadi angkanya kena skala dua
       kali. Terukur:

           layar         skala panggung   kanvas debu jadi
           390x844            1,000          1,00x halaman   <- kebetulan pas
           1440x900           1,534          1,53x halaman   <- meluber 53%

       Di HP skalanya kebetulan tepat 1,0, jadi salahnya tidak bergejala sama
       sekali; di desktop debunya berhamburan sampai ke luar kartu. Dilaporkan
       pemilik situs 19 Agu 2026. offsetWidth mengembalikan px LOKAL, satuan
       yang sama dengan style.width, jadi berapa pun skalanya tidak lagi
       berpengaruh. Dijaga test_kanvas_debu_diukur_dalam_piksel_lokal. */
    var w = buku.offsetWidth + TEPI_DEBU * 2;
    var h = buku.offsetHeight + TEPI_DEBU * 2;

    /* DPR dibatasi 2: di layar 3x, kanvas seluas halaman berarti tiga kali
       lipat piksel yang harus digambar tiap frame tanpa ada yang bisa
       melihat bedanya pada titik debu selebar 2 px. */
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    kanvas.width = Math.round(w * dpr);
    kanvas.height = Math.round(h * dpr);
    kanvas.style.width = w + "px";
    kanvas.style.height = h + "px";
    // Digeser keluar supaya kertas duduk di tengah kanvas. Ditaruh di sini,
    // bukan di CSS, supaya TEPI_DEBU cuma tertulis di SATU tempat.
    kanvas.style.left = -TEPI_DEBU + "px";
    kanvas.style.top = -TEPI_DEBU + "px";
    halamanW = buku.offsetWidth;
    halamanH = buku.offsetHeight;
    if (ktx) ktx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  /* ── Rupa butir ───────────────────────────────────────────────────────
     Tiap butir digambar dari SPRITE yang sudah jadi, bukan dengan menyusun
     path tiap frame. Alasannya ongkos: nyala bergradasi butuh
     createRadialGradient, dan membuatnya 260 kali per frame pada 60 fps
     berarti 15.600 gradien per detik. Sprite-nya dibuat sekali per warna
     lalu dipakai ulang lewat drawImage, yang murah.

     Warnanya dibulatkan ke 16 tingkat per kanal sebelum jadi kunci cache.
     Satu halaman biasanya cuma menghasilkan belasan warna berbeda sesudah
     pembulatan, jadi cache-nya kecil dan nyaris selalu kena. */
  var SISI_SPRITE = 64;
  var spriteCache = {};

  function jalurHati(c, s) {
    c.beginPath();
    c.moveTo(0, s * 0.33);
    c.bezierCurveTo(0, s * 0.10, -s * 0.50, -s * 0.10, -s * 0.50, -s * 0.33);
    c.bezierCurveTo(-s * 0.50, -s * 0.60, -s * 0.15, -s * 0.62, 0, -s * 0.33);
    c.bezierCurveTo(s * 0.15, -s * 0.62, s * 0.50, -s * 0.60, s * 0.50, -s * 0.33);
    c.bezierCurveTo(s * 0.50, -s * 0.10, 0, s * 0.10, 0, s * 0.33);
    c.closePath();
  }

  function sprite(bentuk, r, g, b) {
    var kunci = bentuk + ((r >> 4) << 8 | (g >> 4) << 4 | (b >> 4));
    if (spriteCache[kunci]) return spriteCache[kunci];

    var c = document.createElement("canvas");
    c.width = c.height = SISI_SPRITE;
    var cc = c.getContext("2d");
    var t = SISI_SPRITE / 2;
    var warna = (r | 0) + "," + (g | 0) + "," + (b | 0);

    if (bentuk === "h") {
      /* Hati: nyala lembut di belakangnya, bentuknya di depan. Tanpa nyala
         itu hatinya terbaca sebagai stiker yang ditempel, bukan sesuatu yang
         berpendar seperti debunya. */
      var n = cc.createRadialGradient(t, t, 0, t, t, t);
      n.addColorStop(0, "rgba(" + warna + ",0.5)");
      n.addColorStop(0.5, "rgba(" + warna + ",0.16)");
      n.addColorStop(1, "rgba(" + warna + ",0)");
      cc.fillStyle = n;
      cc.fillRect(0, 0, SISI_SPRITE, SISI_SPRITE);
      cc.translate(t, t);
      jalurHati(cc, SISI_SPRITE * 0.62);
      cc.fillStyle = "rgba(" + warna + ",1)";
      cc.fill();
    } else {
      /* Debu: gradien radial dengan inti hampir pekat lalu turun cepat.
         Perhentian di 0,25 itu yang membedakannya dari bulatan rata — tanpa
         itu hasilnya piringan bertepi tegas, dan justru tepi tegas itu yang
         membuat versi lama terlihat seperti titik cat. */
      var gr = cc.createRadialGradient(t, t, 0, t, t, t);
      gr.addColorStop(0, "rgba(" + warna + ",1)");
      gr.addColorStop(0.25, "rgba(" + warna + ",0.72)");
      gr.addColorStop(0.6, "rgba(" + warna + ",0.20)");
      gr.addColorStop(1, "rgba(" + warna + ",0)");
      cc.fillStyle = gr;
      cc.fillRect(0, 0, SISI_SPRITE, SISI_SPRITE);
    }
    spriteCache[kunci] = c;
    return c;
  }

  /* Warna debu diambil dari PELAT halamannya sendiri, jadi tiap halaman
     melepas debu berwarna dirinya: halaman kalender merah tua melepas
     merah, halaman rajut krem melepas krem.

     Dicuplik ke kisi 12x17 sekali per halaman lalu disimpan. Pelatnya
     berkas static satu asal, jadi kanvasnya tidak tercemar dan getImageData
     boleh dipakai. Foto pembeli TIDAK ikut dicuplik — bisa dari R2 yang
     beda asal, dan itu akan mencemari kanvas. */
  var warnaCache = {};

  function warnaHalaman(i, siap) {
    if (warnaCache[i]) { siap(warnaCache[i]); return; }
    var el = lembar[i];
    var pelat = el && el.querySelector(".pelat");
    var url = pelat && (getComputedStyle(pelat).backgroundImage || "").match(/url\(["']?([^"')]+)/);
    if (!url) { siap(warnaCache[i] = cadanganWarna(el)); return; }

    var img = new Image();
    img.onload = function () {
      try {
        var c = document.createElement("canvas");
        var lebar = PETAK_WARNA, tinggi = Math.round(PETAK_WARNA * 1.414);
        c.width = lebar; c.height = tinggi;
        var cc = c.getContext("2d", { willReadFrequently: true });
        cc.drawImage(img, 0, 0, lebar, tinggi);
        var d = cc.getImageData(0, 0, lebar, tinggi).data;
        var daftar = [];
        for (var y = 0; y < tinggi; y++) {
          for (var x = 0; x < lebar; x++) {
            var o = (y * lebar + x) * 4;
            // Piksel tembus pandang = lubang foto; lewati, itu bukan warna halaman.
            if (d[o + 3] < 120) continue;
            var c3 = pendar(d[o], d[o + 1], d[o + 2]);
            c3.u = (x + 0.5) / lebar;
            c3.v = (y + 0.5) / tinggi;
            daftar.push(c3);
          }
        }
        /* Pelat yang cuma menyisakan segelintir piksel opak (halaman yang
           hampir seluruhnya lubang foto) tetap dipakai, tapi DILENGKAPI warna
           kertasnya — kalau tidak, seluruh debu halaman itu mengambil warna
           dari bingkai tepinya saja. */
        warnaCache[i] = daftar.length >= 8 ? daftar
                      : daftar.concat(cadanganWarna(el));
      } catch (e) {
        warnaCache[i] = cadanganWarna(el);
      }
      siap(warnaCache[i]);
    };
    img.onerror = function () { siap(warnaCache[i] = cadanganWarna(el)); };
    img.src = url[1];
  }

  /* Mengubah warna permukaan jadi warna DEBU BERPENDAR.

     Dua langkah, dan keduanya perlu:

     1. Diangkat ke arah putih. Debu yang berpendar adalah butiran tertimpa
        cahaya, jadi selalu lebih terang daripada permukaan asalnya.
     2. Lantai kecerahan. Halaman yang sangat gelap — sampul, kalender merah
        tua — kalau cuma diangkat 55% masih menghasilkan debu kelabu yang di
        tangkapan layar terbaca sebagai BINTIK KOTOR di atas halaman
        berikutnya yang terang. Lantai ini menjamin butirnya selalu lebih
        terang daripada latar mana pun, sambil menjaga RONA-nya: merah tua
        jadi merah muda pucat, bukan putih rata. */
  function pendar(r, g, b) {
    r += (255 - r) * 0.55; g += (255 - g) * 0.55; b += (255 - b) * 0.55;
    var puncak = Math.max(r, g, b);
    if (puncak < 205) {
      var naik = 205 / Math.max(puncak, 1);
      r = Math.min(255, r * naik); g = Math.min(255, g * naik); b = Math.min(255, b * naik);
    }
    return { r: r, g: g, b: b };
  }

  /* Dipakai kalau pelatnya tidak menyisakan satu pun piksel opak untuk
     dicuplik. Itu BUKAN kasus langka: sampul dan halaman penutup seluruhnya
     lubang foto (terukur: 0 opak dari 204 cuplikan), dan halaman 11 memang
     tidak punya pelat sama sekali. Warna diambil dari kertas halamannya,
     lalu disebar jadi beberapa nuansa supaya debunya tidak tampak seragam
     seperti satu warna cat. */
  function cadanganWarna(el) {
    var bg = el ? getComputedStyle(el).getPropertyValue("--kertas-bg").trim() : "";
    var m = bg.match(/^#([0-9a-f]{6})$/i);
    var n = m ? parseInt(m[1], 16) : 0xfff7ea;
    var dasar = [(n >> 16) & 255, (n >> 8) & 255, n & 255];
    var daftar = [];
    for (var k = 0; k < 12; k++) {
      var goyang = 1 + (Math.random() - 0.5) * 0.35;
      var c = pendar(Math.min(255, dasar[0] * goyang),
                     Math.min(255, dasar[1] * goyang),
                     Math.min(255, dasar[2] * goyang));
      c.u = Math.random(); c.v = Math.random();
      daftar.push(c);
    }
    return daftar;
  }

  /* Seberapa terang butir di titik (x,y) boleh menyala, mengingat jaraknya
     dari tepi kertas. 1 di dalam kertas, meluruh jadi 0 di dalam pita
     TEPI_DEBU di luarnya.

     Dihitung per SISI lalu diambil yang terkecil, jadi butir yang keluar
     lewat sudut memudar seperti yang lewat sisi lurus. */
  function pudarTepi(x, y) {
    var kiri = x - TEPI_DEBU;
    var atas = y - TEPI_DEBU;
    var kanan = TEPI_DEBU + halamanW - x;
    var bawah = TEPI_DEBU + halamanH - y;
    var d = Math.min(kiri, atas, kanan, bawah);
    if (d >= -PUDAR_TEPI[0]) return 1;              // masih jauh di dalam
    var lewat = -d - PUDAR_TEPI[0];                 // seberapa jauh melewati
    return jepit(1 - lewat / (PUDAR_TEPI[0] + PUDAR_TEPI[1]));
  }

  // Diisi ukurKanvas(); dipakai pudarTepi().
  var halamanW = 0, halamanH = 0;

  /* Membersihkan SELURUH sisa peralihan, siapa pun yang meninggalkannya.

     Ini yang dulu hilang, dan akibatnya parah: peralihan yang disusul
     sebelum selesai memang menghentikan loop-nya, tapi `opacity` inline yang
     sudah terlanjur dipasang dibiarkan menempel. Gaya inline TIDAK bisa
     ditimpa aturan CSS `.lembar { opacity: 0 }`, jadi tiap kali penerima
     menekan lanjut dengan cepat, satu halaman lagi tertinggal setengah
     transparan — dan halaman-halaman itu menumpuk jadi bubur.

     Menyapu semua lembar, bukan cuma dua yang terlibat: kalau ada tiga
     peralihan tertumpuk, yang tertinggal juga lebih dari dua. */
  function bersihkanSisa() {
    lembar.forEach(function (el) {
      el.style.opacity = "";
      el.classList.remove("masuk");
      el.classList.remove("keluar");
    });
    if (ktx) ktx.clearRect(0, 0, kanvas.width, kanvas.height);
  }

  function larutkan(dari, tuju, selesai) {
    /* Nomor peralihan dinaikkan SINKRON di sini, bukan nanti setelah warna
       selesai diambil. Pengambilan warna bisa menunggu gambar ter-decode,
       dan dua peralihan beruntun bisa menyelesaikan pengambilannya dengan
       urutan terbalik — nomor yang dinaikkan belakangan membuat peralihan
       LAMA mengira dirinya yang terbaru. */
    var akuId = ++debuJalan;
    bersihkanSisa();

    var elDari = lembar[dari], elTuju = lembar[tuju];
    if (!elTuju) { if (selesai) selesai(); return; }

    // Tujuan sudah boleh memuat gambarnya SEKARANG, bukan setelah peralihan
    // selesai — kalau menunggu, halaman baru muncul dalam keadaan kosong.
    lembar.forEach(function (el, j) {
      if (j >= tuju - DEKAT && j <= tuju + DEPAN) el.classList.add("dekat");
    });
    elTuju.classList.add("masuk");
    /* Halaman yang DITINGGALKAN wajib ditandai juga.

       Tanpa ini ia bukan .active dan bukan .masuk, jadi aturan mode
       partikel menyembunyikannya (`visibility: hidden`) — dan `opacity`
       inline yang dipasang tiap frame di bawah tidak berpengaruh apa pun
       pada elemen yang tersembunyi. Akibatnya halaman lama LENYAP SEKETIKA
       alih-alih memudar, dan yang tersisa cuma halaman baru yang muncul.
       Persis kebalikan dari "menghilang perlahan" yang diminta. */
    if (elDari && elDari !== elTuju) elDari.classList.add("keluar");

    if (hemat || !ktx || !elDari) {
      // Hormati prefers-reduced-motion: tukar saja, tanpa debu.
      bersihkanSisa();
      if (selesai) selesai();
      return;
    }

    ukurKanvas();
    /* Koordinat butir dihitung dalam px LOKAL, sama seperti kanvasnya —
       lihat catatan panjang di ukurKanvas(). Kertas dan #buku itu kotak yang
       sama persis (terukur 390x552 lokal di kedua konteks: pratinjau
       berdiri sendiri MAUPUN iframe editor), jadi tidak perlu diukur
       terpisah. Titik (0,0) kanvas ada di TEPI_DEBU px di luar sudut kertas. */
    var halW = buku.offsetWidth, halH = buku.offsetHeight;

    warnaHalaman(dari, function (warna) {
      var butir = [];
      for (var n = 0; n < JUMLAH_DEBU; n++) {
        /* Posisi diundi RATA di seluruh halaman, lalu warnanya diambil dari
           cuplikan TERDEKAT ke titik itu.

           Versi pertama menaruh tiap butir persis di titik cuplikannya, dan
           itu salah untuk halaman yang didominasi lubang foto — sampul
           misalnya hampir seluruhnya lubang, jadi cuplikan yang tersisa cuma
           di bingkai tepinya dan SELURUH debu menggerombol di situ.
           Memisahkan posisi dari sumber warna membuat sebarannya rata tanpa
           kehilangan sifat "warnanya mengikuti bagian halaman itu".

           Cuma pelatnya yang dicuplik, tidak pernah foto pembeli: foto bisa
           datang dari R2 yang beda asal, dan itu mencemari kanvas sehingga
           getImageData dilarang. */
        var pu = Math.random(), pv = Math.random();
        var w = warna[0], jarak = Infinity;
        for (var q = 0; q < warna.length; q++) {
          var d2 = (warna[q].u - pu) * (warna[q].u - pu) +
                   (warna[q].v - pv) * (warna[q].v - pv);
          if (d2 < jarak) { jarak = d2; w = warna[q]; }
        }
        /* Ukuran diundi dengan pangkat 2, bukan rata. Undian rata memberi
           terlalu banyak butir berukuran menengah dan hasilnya terbaca
           seragam; dipangkatkan, mayoritasnya jadi halus dan hanya
           segelintir yang besar — dan justru segelintir itu yang memberi
           kesan ada kedalaman. */
        var kasar = Math.pow(Math.random(), 2);
        var hati = Math.random() < PORSI_HATI;
        butir.push({
          x: TEPI_DEBU + pu * halW,
          y: TEPI_DEBU + pv * halH,
          naik: DEBU_NAIK[0] + Math.random() * (DEBU_NAIK[1] - DEBU_NAIK[0]),
          fase: Math.random() * Math.PI * 2,
          ayun: 0.4 + Math.random() * 0.8,
          // Hati dibuat lebih besar daripada debu: pada ukuran debu, bentuk
          // hatinya tidak terbaca sama sekali dan cuma jadi bintik gemuk.
          jari: (DEBU_UKURAN[0] + kasar * (DEBU_UKURAN[1] - DEBU_UKURAN[0])) * (hati ? 2.1 : 1),
          hati: hati,
          // Hati berputar pelan; arah dan lajunya diundi supaya tidak ada
          // dua yang bergerak serempak.
          putar: (Math.random() - 0.5) * 0.0016,
          sudut: (Math.random() - 0.5) * 0.9,
          // Kedip halus. Butir debu sungguhan menangkap cahaya sesekali;
          // tanpa ini semuanya meredup dengan kurva yang sama persis dan
          // terbaca sebagai satu lapisan yang di-fade, bukan banyak butir.
          kedip: 0.75 + Math.random() * 0.25,
          lajuKedip: 0.002 + Math.random() * 0.004,
          // Ditunda acak supaya debunya tidak berangkat serempak seperti
          // satu barisan — yang membuatnya terbaca sebagai efek, bukan debu.
          tunda: Math.random() * 0.45,
          r: w.r, g: w.g, b: w.b,
        });
      }

      // Sudah disusul peralihan lain selagi warnanya diambil.
      if (akuId !== debuJalan) return;

      /* Titik AWAL diambil dari keadaan yang terlihat SEKARANG, bukan
         diandaikan 0 dan 1.

         Versi pertama memakai rumus mutlak: tujuan tetap 0 sampai p > 0,25
         baru mulai naik. Itu benar untuk satu peralihan yang dibiarkan
         selesai, tapi salah besar saat penerima menekan lanjut beruntun —
         tiap peralihan baru MENGEMBALIKAN tujuan ke nol, dan dengan jeda
         110 ms ia tidak pernah lolos dari zona mati itu. Terukur: 66% frame
         di bawah 0,35 opasitas, layar praktis kosong selama 800 ms.

         Dengan titik awal dibaca dari keadaan nyata, halaman yang sudah
         terlihat TETAP terlihat: skip cepat jadi berpindah tegas sambil
         tetap melepas debu, bukan berkedip gelap. */
      var awalDari = parseFloat(getComputedStyle(elDari).opacity) || 0;

      var t0 = performance.now();

      (function bingkai(kini) {
        if (akuId !== debuJalan) return;              // peralihan disusul yang baru
        var p = jepit((kini - t0) / LAMA_LARUT);

        // Halaman lama memudar; yang baru menyusul sedikit terlambat supaya
        // keduanya tidak pernah sama-sama pekat dan saling menumpuk.
        /* HANYA halaman lama yang dianimasikan. Halaman tujuan diam di
           bawahnya pada opasitas penuh, dan tersingkap seiring yang di atas
           larut — itu yang membuatnya terbaca sebagai halaman menghilang,
           bukan dua gambar saling silang. Sebagai bonus, skip beruntun jadi
           tegas: halaman tujuan tidak pernah setengah pudar menunggu
           gilirannya. */
        /* Halamannya habis pada 72% peralihan, bukan 100%.

           Dengan 2,5 detik, membiarkannya memudar sampai detik terakhir
           berarti seperempat waktu terakhir dihabiskan menonton halaman yang
           tinggal beberapa persen opasitasnya — tidak terlihat berubah, cuma
           terasa lambat. Diselesaikan lebih awal, sisa waktunya jadi milik
           debu yang masih melayang di atas halaman baru, dan ITU yang
           terbaca sebagai "santai". */
        elDari.style.opacity = String(awalDari * Math.pow(1 - jepit(p / 0.72), 1.5));

        ktx.clearRect(0, 0, kanvas.width, kanvas.height);
        ktx.globalCompositeOperation = "lighter";
        for (var k = 0; k < butir.length; k++) {
          var b = butir[k];
          var q = (p - b.tunda) / (1 - b.tunda);
          if (q <= 0) continue;
          q = jepit(q);
          var umur = kini - t0 - b.tunda * LAMA_LARUT;
          var x = b.x + Math.sin(b.fase + umur * 0.004) * b.ayun * DEBU_SAMPING * umur;
          var y = b.y - b.naik * umur;

          // Menyala di awal lalu pudar — itu "berpendar", bukan sekadar hilang.
          var a = Math.sin(Math.PI * q) * 0.95;
          // Kedip halus di atas kurva itu, beda fase tiap butir.
          a *= b.kedip + (1 - b.kedip) * (0.5 + 0.5 * Math.sin(b.fase + umur * b.lajuKedip));
          a *= pudarTepi(x, y);
          if (a <= 0.012) continue;

          var jari = b.jari * (1 - q * 0.45);
          var img = sprite(b.hati ? "h" : "d", b.r, b.g, b.b);
          ktx.globalAlpha = a;
          if (b.hati) {
            ktx.save();
            ktx.translate(x, y);
            ktx.rotate(b.sudut + umur * b.putar);
            ktx.drawImage(img, -jari * 2, -jari * 2, jari * 4, jari * 4);
            ktx.restore();
          } else {
            // Sprite-nya bernyala sampai ke tepi kotaknya, jadi digambar
            // selebar 4x jari-jari: intinya sebesar jari-jari yang diminta,
            // sisanya pendar yang meluruh.
            ktx.drawImage(img, x - jari * 2, y - jari * 2, jari * 4, jari * 4);
          }
        }
        ktx.globalAlpha = 1;
        ktx.globalCompositeOperation = "source-over";

        if (p < 1) return requestAnimationFrame(bingkai);

        bersihkanSisa();
        if (selesai) selesai();
      })(t0);
    });
  }

  function taruh(i, t, pegang) {
    var tc = jepit(t);

    /* Mode "partikel" tidak memutar apa pun: halaman diam di tempatnya, dan
       yang berubah cuma mana yang terlihat. Transform dibersihkan supaya
       sisa putaran dari gaya lain tidak tertinggal kalau GAYA diganti saat
       halaman sudah termuat. */
    if (GAYA === "partikel") {
      lepasRig();
      lembar[i].style.transform = "";
      lembar[i].classList.remove("terbalik");
      if (redupPolos[i]) redupPolos[i].style.opacity = "0";
      if (jatuhnya[i + 1]) jatuhnya[i + 1].style.opacity = "0";
      return;
    }

    /* Muka mana yang menghadap pembaca — ditentukan di sini, bukan
       diserahkan ke `backface-visibility`.

       Safari/WebKit tidak mematuhi backface-visibility untuk .muka: lembar
       yang sudah dibalik ke kiri menampilkan isi halaman depannya TERCERMIN
       ("Contents" terbaca terbalik) alih-alih punggung kertas polos. Chrome
       mematuhinya, jadi cacat ini tidak muncul di pemeriksa mana pun.

       Memberi .muka.depan transform 3D sendiri memang membuat WebKit
       mematuhinya — tapi sekaligus MENGOSONGKAN halamannya (terukur: isi
       halaman tinggal 17 warna, dari 8.819). Jadi jalur itu dibuang.

       Ditukar di tc = 0,5, yaitu tepat saat lembarnya tegak lurus layar dan
       tidak ada yang terlihat — pertukarannya karena itu tak kasatmata. */
    lembar[i].classList.toggle("terbalik", tc > 0.5);
    var g = (pegang === undefined ? 0.5 : pegang) - 0.5;
    var busur = Math.sin(Math.PI * tc);

    /* ── gaya "rotasi": satu bidang, sesuai spek ───────────────────────
       Bayangan tetap ikut sudutnya, jadi halaman tetap terasa berpaling
       dari cahaya walau bentuknya tidak melengkung. */
    if (GAYA === "rotasi") {
      lepasRig();
      var el = lembar[i];
      /* Titik pegang tetap berpengaruh: seluruh lembar dimiringkan sedikit
         ke arah tangan, paling besar di tengah putaran lalu kembali rata
         saat mendarat. Bidang tunggal tidak bisa melipat diagonal seperti
         gaya "bilah", tapi tanpa kemiringan ini memegang sudut atas dan
         memegang tengah menghasilkan gerakan yang sama persis — dan
         seretannya terasa tidak dijawab. */
      el.style.transform =
        "rotateY(" + (-180 * tc).toFixed(2) + "deg)" +
        " rotateZ(" + (MIRING_MAKS * g * Math.pow(busur, 0.7)).toFixed(2) + "deg)";
      if (redupPolos[i]) {
        redupPolos[i].style.opacity = halus(jepit(tc * 1.7)).toFixed(3);
      }
      var belakang = lembar[i].querySelector(".belakang > .redup");
      if (belakang) {
        belakang.style.opacity = halus(jepit((1 - tc) * 1.7)).toFixed(3);
      }
      if (jatuhnya[i + 1]) {
        jatuhnya[i + 1].style.opacity = (busur * 0.9).toFixed(3);
      }
      return;
    }

    // Di kedua ujung tidak ada yang melengkung, jadi rig tidak dipakai:
    // lembar aslinya sendiri yang dipasang rata atau terbalik. Ini juga
    // yang mengembalikan interaksi editor begitu putaran selesai.
    if (hemat || tc <= 0.0008 || tc >= 0.9992) {
      lepasRig();
      lembar[i].style.transform = "rotateY(" + (-180 * tc).toFixed(2) + "deg)";
      if (redupPolos[i]) redupPolos[i].style.opacity = "0";
      if (jatuhnya[i + 1]) jatuhnya[i + 1].style.opacity = "0";
      return;
    }

    pakaiRig(i);
    if (!rigAktif) return;

    /* A = sudut ujung bebas. p = ketajaman lipatan: besar di awal berarti
       hanya bilah paling kanan yang membelok dan sisi punggung masih rata;
       mengecil seiring putaran, dan itulah yang membuat lipatan MERAMBAT
       dari tepi kanan ke punggung buku. */
    /* A = sudut ujung bebas. `tinggal` = seberapa jauh punggung TERTINGGAL
       di belakang ujungnya — inilah kelengkungannya, dan yang dikendalikan
       langsung di sini, bukan lewat eksponen.

       Kenapa langsung: sebaran sudut dibagi sepuluh bilah, jadi sebaran
       120 derajat berarti tiap bilah melompat 12 derajat dari tetangganya —
       dan lompatan sebesar itu terlihat sebagai kisi-kisi jendela, bukan
       kertas. Dengan dikendalikan begini, sebarannya tidak pernah lewat
       ~46 derajat, jadi tiap bilah paling jauh 5 derajat dari tetangganya.

       Bentuknya juga benar secara fisik: kertas paling melengkung di
       PERTENGAHAN, waktu jari menekuknya. Di awal ia masih rata, di akhir
       ia sudah mendatar lagi dan tinggal berayun. Karena `tinggal` menuju
       nol, lembarnya MENDARAT RATA di sisi kiri — bukan berhenti dalam
       keadaan tergulung setengah lingkaran. */
    var A = 180 * tc;
    /* Dulu: (1 - halus(tc)) * 0.85, yang puncak sebarannya cuma ~40 derajat
       di tc sekitar 0,42 — dan 40 derajat itulah yang terbaca sebagai papan
       kaku. Menaikkan pengali 0,85 saja tidak menolong: pada tinggal = 1
       (batas mutlaknya, punggung belum bergerak sama sekali saat ujung sudah
       di sudut A) puncaknya masih cuma ~56 derajat.

       Yang harus diubah adalah BENTUK peluruhannya. Dengan pangkat < 1,
       `tinggal` bertahan tinggi lebih lama, sehingga puncak sebaran bergeser
       ke tc yang lebih besar — di mana A sudah jauh lebih lebar. LURUH = 1
       mengembalikan perilaku lama.

       Angka di bawah DIUKUR dari fungsi ini sendiri (200 cuplikan sepanjang
       putaran), bukan diperkirakan dari rumus pokoknya — SIMPANG dan
       GELOMBANG ikut menyumbang lompatan, dan sumbangannya besar:

           LURUH  bilah   puncak sebaran   di tc   lompatan maks
           1,0×0,85  10        40,3°        0,41       7,74°   <- lama
           0,30      10        71,3°        0,67      12,32°
           0,30      12        72,2°        0,67      10,12°
           0,30      14        73,6°        0,67       9,14°
           0,30      16        74,5°        0,67       7,94°   <- dipakai
           0,25      16        80,1°        0,70       8,34°

       Yang penting dari tabel itu: pada 16 bilah, sebarannya naik 85%
       (40,3 -> 74,5 derajat) sementara lompatannya justru sedikit LEBIH
       KECIL daripada versi lama (7,94 vs 7,74 — praktis sama). Jadi
       lengkungnya jauh lebih dalam tanpa menambah faceting sedikit pun.

       Perhatikan juga lompatan sudah 7,74 derajat pada setelan LAMA — ia
       memang selalu duduk tepat di bawah ambang 8, dan itu bukan kebetulan:
       lompatan didominasi SIMPANG, bukan lengkung dasarnya. Karena itu
       menambah bilah menurunkannya jauh lebih pelan daripada dugaan
       "lompatan = sebaran / N".

       tinggal tetap MENUJU NOL saat tc -> 1 (pow(0, LURUH) = 0 untuk LURUH
       positif), jadi lembarnya tetap MENDARAT RATA — tidak berhenti dalam
       keadaan tergulung setengah lingkaran.

       Yang diawasi: makin kecil LURUH, makin curam pendataran di ujung
       putaran, dan itu bisa terbaca sebagai "menjepret" di detik terakhir.
       Tidak bisa diputuskan dari rumus — setel sambil membalik halamannya
       sendiri, lalu ukur dengan tools/cek_valentine_balik.js. */
    var tinggal = Math.pow(1 - halus(tc), LURUH);

    var x = 0, z = 0;
    for (var k = 0; k < N_BILAH; k++) {
      var u = (BATAS[k] + BATAS[k + 1]) / 2;
      var d = sudutDi(u, A, tinggal, busur) + SIMPANG[k] * busur;
      var r = d * Math.PI / 180;
      var lb = lebarBilah(k);

      /* Pangkal bilah ini = ujung bilah sebelumnya. Justru penjumlahan
         inilah yang membedakan kurva sungguhan dari sepuluh kotak yang
         kebetulan miring: lembarnya tersambung ujung ke ujung. */
      var el = bilah[k].el;
      /* Bilah sudah duduk di tempatnya lewat CSS `left`, jadi geseran di
         sini dihitung relatif terhadap itu — kalau tidak, rantainya dobel. */
      el.style.transform =
        "translate3d(" + (x - kiriBilah(k)).toFixed(2) + "px,0," + z.toFixed(2) + "px)" +
        " rotateY(" + (-d).toFixed(2) + "deg)" +
        /* Pelintiran ke arah tangan TUMBUH sepanjang lembar: nol di
           punggung, penuh di ujung bebas. Itu yang membuat lipatannya
           MIRING waktu dipegang di sudut — dipukul rata ke semua bilah,
           yang terjadi cuma seluruh lembar ikut doyong, dan titik
           pegangnya tidak terasa berpengaruh. */
        " rotateZ(" + (MIRING_MAKS * g * Math.pow(busur, 0.7) * u).toFixed(2) + "deg)";
      x += lb * Math.cos(r);
      z += lb * Math.sin(r);

      /* Cahaya dihitung dari sudut bilah itu sendiri, jadi bagian yang
         membelok menjauhi cahaya benar-benar menggelap dan yang menghadapnya
         tampil pada kecerahan penuh. Inilah "bayangan mengikuti
         kelengkungan" — mustahil waktu halamannya masih satu bidang. */
      var rKi = sudutDi(BATAS[k], A, tinggal, busur) * Math.PI / 180;
      var rKa = sudutDi(BATAS[k + 1], A, tinggal, busur) * Math.PI / 180;
      bilah[k].depan.redup.style.background = gelap(rKi, rKa, 0.72);
      // Kilau per bilah DICABUT. Bukan karena tidak indah — karena tepinya
      // jatuh persis di batas potongan tiap bilah, dan sisa antialias putih
      // di situ menumpuk di atas isi bilah tetangganya. Sepuluh batas =
      // sepuluh garis terang tegak, dan itulah "retakan kaca" yang terlihat
      // di kartu. Sudah diuji: mengurangi tumpang-tindih, melandaikan
      // pangkatnya, dan menambah titik gradien semuanya tidak
      // menghilangkannya; mencabutnya menghilangkannya sepenuhnya.
      //
      // Sisi terangnya tidak hilang: gradasi gelap di bawah ini justru
      // MENGHILANG di bagian yang menghadap cahaya, jadi kertasnya tampil
      // pada kecerahan penuh di sana — itu sisi terangnya.
      var pi = Math.PI;
      bilah[k].belakang.redup.style.background = gelap(rKi + pi, rKa + pi, 0.72);
    }

    /* Bayangan yang jatuh ke halaman di bawahnya. Lebarnya diambil dari
       ujung lipatan (x bilah terakhir), bukan dari t — jadi bayangannya
       melebar mengikuti lipatan yang merambat, bukan mengembang sendiri. */
    var bawah = jatuhnya[i + 1];
    if (bawah) {
      bawah.style.opacity = (busur * 0.92).toFixed(3);
      bawah.style.width = jepit(x / W0 * 1.15).toFixed(3) * 100 + "%";
    }
  }

  /* ── menyesuaikan teks pembeli yang lebih panjang dari bawaannya ───────
     Tiap teks duduk di kotak berukuran tetap di atas pelat gambar. Nama
     "ROCKY & RIANA" muat dua baris; "MUHAMMAD RIZKI PRATAMA & SITI
     NURHALIZA RAHMAWATI" tidak — tanpa penyesuai ini ia melimpah ke bawah,
     menabrak tulisan lain, dan keluar dari halaman.

     Yang dikecilkan hanya ukuran hurufnya, dan HANYA kalau perlu: selama
     teksnya sepanjang bawaan, --muat tetap 1 dan desain aslinya tidak
     berubah satu piksel pun. Garis alas baris pertama tetap di tempatnya
     karena jangkarnya dihitung dalam em (lihat .tx di valentine.css), jadi
     teks yang mengecil tumbuh ke bawah, bukan melayang. */
  var MUAT_MIN = 0.5;   // di bawah ini hurufnya tidak terbaca lagi
  // Surat yang mengalir bebas (data-maks) berhenti mengecil lebih awal; kalau
  // masih kepanjangan, ia DIGULIR di tempatnya, bukan dipotong halaman. Batas
  // teks naik ke 3.000 karakter (14 Okt 2026) — dikecilkan terus, surat
  // sepanjang itu keluar dari halaman dan sisanya hilang.
  var MUAT_MIN_SURAT = 0.65;

  function jatah(el) {
    // data-baris = berapa baris yang disediakan desainnya untuk teks ini.
    // data-maks  = batas dalam persen tinggi halaman (untuk surat yang
    //              memang mengalir bebas, bukan dijatah per baris).
    var g = getComputedStyle(el);
    var fs = parseFloat(g.fontSize);
    var muat = parseFloat(g.getPropertyValue("--muat")) || 1;
    var fs1 = fs / muat;                       // ukuran huruf saat --muat 1
    if (el.dataset.maks) return parseFloat(el.dataset.maks) / 100 * 551.6;
    var baris = parseFloat(el.dataset.baris) || 1;
    return baris * (parseFloat(g.lineHeight) / fs) * fs1;
  }

  function muatkan(el) {
    if (!el.dataset.baris && !el.dataset.maks) return;
    var surat = !!el.dataset.maks;
    var min = surat ? MUAT_MIN_SURAT : MUAT_MIN;
    el.classList.remove("gulir", "di-ujung");
    el.style.maxHeight = "";
    el.style.setProperty("--muat", 1);
    var batas = jatah(el);
    var m = 1;
    // offsetHeight mengabaikan transform panggung, jadi angkanya px tata
    // letak yang sama di layar mana pun.
    for (var putaran = 0; putaran < 10 && el.offsetHeight > batas + 0.5; putaran++) {
      if (m <= min) break;
      // Tinggi kira-kira sebanding kuadrat ukuran huruf (barisnya berkurang
      // DAN tiap baris memendek), jadi akar rasionya tebakan awal yang
      // bagus; dibatasi supaya tidak melompat terlalu jauh sekali langkah.
      var langkah = Math.max(0.85, Math.sqrt(batas / el.offsetHeight));
      m = Math.max(min, m * langkah);
      el.style.setProperty("--muat", m.toFixed(4));
    }
    if (surat && el.offsetHeight > batas + 0.5) {
      el.style.maxHeight = batas + "px";
      el.classList.add("gulir");
    }
  }

  // Pudar bawah surat yang digulir hilang begitu sampai di ujungnya.
  document.addEventListener("scroll", function (e) {
    var el = e.target;
    if (!el.classList || !el.classList.contains("gulir")) return;
    el.classList.toggle("di-ujung", el.scrollTop + el.clientHeight >= el.scrollHeight - 2);
  }, true);

  var semuaTeks = [].slice.call(document.querySelectorAll(".tx"));
  function muatkanSemua() { semuaTeks.forEach(muatkan); }

  // Diukur SETELAH font terpasang — kalau tidak, yang terukur metrik font
  // cadangan dan hasilnya meleset di semua teks sekaligus.
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(muatkanSemua);
  }
  muatkanSemua();

  // Saat menyunting, teksnya diganti langsung di DOM oleh card-frame.js.
  // Tanpa pengamat ini, pembeli mengetik nama panjang dan baru melihat
  // akibatnya setelah memuat ulang.
  if (window.MutationObserver) {
    var pengamat = new MutationObserver(function (daftar) {
      var kena = [];
      daftar.forEach(function (m) {
        var el = (m.target.nodeType === 1 ? m.target : m.target.parentElement);
        var tx = el && el.closest && el.closest(".tx");
        if (tx && kena.indexOf(tx) < 0) kena.push(tx);
      });
      kena.forEach(muatkan);
    });
    semuaTeks.forEach(function (el) {
      pengamat.observe(el, { childList: true, characterData: true, subtree: true });
    });
  }

  /* ── keadaan diam: tiap lembar rata di kiri atau di kanan ────────────── */
  function pasang(n, halus) {
    idx = Math.max(0, Math.min(lembar.length - 1, n));
    lembar.forEach(function (el, i) {
      if (!seret || seret.i !== i) taruh(i, i < idx ? 1 : 0, 0.5);
      el.classList.toggle("active", i === idx);
      el.classList.toggle("dekat", i >= idx - DEKAT && i <= idx + DEPAN);
    });
    if (dotsEl) {
      [].forEach.call(dotsEl.children, function (d, i) {
        d.classList.toggle("on", i === idx);
      });
    }
    if (prevBtn) prevBtn.disabled = idx === 0;
    if (nextBtn) nextBtn.disabled = idx === lembar.length - 1;

    /* Warna debu dicuplik DI MUKA, bukan saat peralihan mulai.

       Mencuplik butuh men-decode pelatnya lalu getImageData, dan itu
       terukur menahan 157 ms — tepat di frame pertama gerakan, tempat
       tersendat paling kentara. Dipanaskan di sini, ongkosnya jatuh saat
       halaman sedang dibaca dan tidak ada yang bergerak. Panggilan kedua
       untuk halaman yang sama langsung pulang dari cache. */
    if (GAYA === "partikel" && !hemat) {
      [idx, idx + 1, idx - 1].forEach(function (j) {
        if (lembar[j] && lembar[j].classList.contains("dekat")) {
          warnaHalaman(j, function () {});
        }
      });
    }
    if (halus !== false && petunjuk && idx > 0) {
      petunjuk.classList.add("pergi");
    }
  }

  /* ── pegas: satu integrator untuk seret DAN lepas ─────────────────────
     Selama diseret, sasarannya posisi jari; lembarnya mengejar, tidak
     menempel mati. Saat dilepas, sasarannya jadi 0 atau 1 dan kecepatan
     jari diteruskan jadi kecepatan awal pegas. Karena rumusnya sama untuk
     dua keadaan itu, tidak ada patahan di detik jari diangkat. */
  var jalan = null;     // { i, sasaran, pegang, selesai, seret }
  var pos = 0, laju = 0, waktuAkhir = 0, rafId = 0;
  var pegangTerakhir = 0.16;   // sudut kanan atas — bawaan untuk tombol

  function selesaikanSeketika() {
    if (!jalan) return;
    var j = jalan;
    jalan = null;
    pos = j.sasaran;
    laju = 0;
    taruh(j.i, j.sasaran, j.pegang);
    if (j.selesai) j.selesai();
  }

  /* Animasi yang sedang berjalan DISELESAIKAN, bukan dibatalkan. Dulu
     dibatalkan, dan akibatnya penerima yang menekan tombol dua kali
     meninggalkan lembar menggantung di tengah tanpa halamannya pernah
     tercatat pindah. */
  function hentikanAnimasi() {
    if (!jalan) return;
    cancelAnimationFrame(rafId);
    clearTimeout(jamTransisi);
    buku.classList.remove("melayang");
    selesaikanSeketika();
  }

  function langkah(waktu) {
    if (!jalan) return;
    // dt dijepit: kalau tab sempat tidak aktif, satu lompatan besar bisa
    // membuat pegasnya meledak melewati sasaran.
    var dt = waktuAkhir ? Math.min((waktu - waktuAkhir) / 1000, 0.05) : 1 / 60;
    waktuAkhir = waktu;

    var a = PEGAS_K * (jalan.sasaran - pos) - PEGAS_REDAM * laju;
    laju += a * dt;
    pos += laju * dt;
    taruh(jalan.i, pos, jalan.pegang);

    var diam = Math.abs(jalan.sasaran - pos) < DIAM_POSISI
            && Math.abs(laju) < DIAM_LAJU;
    if (jalan.seret || !diam) {
      rafId = requestAnimationFrame(langkah);
      return;
    }
    selesaikanSeketika();
  }

  /* Pendaratan gaya "rotasi": transisi CSS, bukan pegas per frame.
     Kelasnya dipasang di #buku, bukan di lembarnya, karena bayangan yang
     ikut beralih (.jatuh) tinggal di halaman BERIKUTNYA — dari lembar yang
     berputar, ia tidak terjangkau selektor mana pun. */
  var jamTransisi = null;

  function luncurTransisi() {
    var j = jalan;
    var el = lembar[j.i];
    buku.classList.add("melayang");
    // Satu frame jeda supaya nilai awalnya sempat tercatat browser; tanpa
    // itu transisinya tidak pernah berjalan, halaman langsung meloncat.
    requestAnimationFrame(function () {
      if (jalan !== j) return;
      taruh(j.i, j.sasaran, j.pegang);
    });

    function beres() {
      if (jalan !== j) return;
      el.removeEventListener("transitionend", beres);
      clearTimeout(jamTransisi);
      buku.classList.remove("melayang");
      pos = j.sasaran;
      laju = 0;
      jalan = null;
      if (j.selesai) j.selesai();
    }
    el.addEventListener("transitionend", beres);
    // Jaring pengaman: transitionend tidak dijamin datang (tab tersembunyi,
    // nilai yang ternyata sama), dan tanpa ini halamannya tidak pernah
    // tercatat pindah.
    jamTransisi = setTimeout(beres, LAMA_ROTASI + 120);
  }

  function mulaiPutaran(i, dari, sasaran, pegang, lajuAwal, seret, selesai) {
    hentikanAnimasi();
    pos = dari;
    laju = lajuAwal || 0;
    waktuAkhir = 0;
    jalan = { i: i, sasaran: sasaran, pegang: pegang, seret: !!seret,
              selesai: selesai };
    if (hemat) { selesaikanSeketika(); return; }
    if (GAYA === "rotasi") {
      // Selama diseret halaman mengikuti jari langsung, tanpa transisi —
      // transisi CSS tidak bisa mengejar jari, ia cuma untuk mendarat.
      if (seret) { taruh(i, dari, pegang); return; }
      luncurTransisi();
      return;
    }
    rafId = requestAnimationFrame(langkah);
  }

  function ke(n) {
    hentikanAnimasi();
    if (n === idx || n < 0 || n > lembar.length - 1) return;
    var maju = n > idx;
    var i = maju ? idx : idx - 1;
    seret = null;

    /* Mode "partikel": tidak ada lembar yang diputar, jadi tidak ada rig,
       klon, maupun pegas. Halaman lama memudar sambil melepas debu, halaman
       baru menyusul. pasang() dipanggil DULU supaya kelas .active dan dots
       sudah benar sejak frame pertama peralihan — kalau dipanggil di akhir,
       titik penanda halaman baru melompat setelah animasinya selesai. */
    if (GAYA === "partikel") {
      var lama = idx;
      pasang(n);
      larutkan(lama, n);
      if (petunjuk) petunjuk.classList.add("pergi");
      return;
    }
    // Klon disiapkan SEBELUM gerakan mulai. Sepuluh klon memakan beberapa
    // milidetik, dan milidetik itu paling kentara tepat di awal gerakan.
    isiRig(i);
    mulaiPutaran(i, maju ? 0 : 1, maju ? 1 : 0, pegangTerakhir,
                 maju ? 0.4 : -0.4, false, function () { pasang(n); });
    // Halaman tujuan sudah boleh memuat gambarnya sekarang, bukan nanti
    // setelah putarannya selesai — kalau menunggu, lembar mendarat di
    // halaman yang masih kosong.
    lembar.forEach(function (el, j) {
      if (j >= n - DEKAT && j <= n + DEPAN) el.classList.add("dekat");
    });
    if (petunjuk) petunjuk.classList.add("pergi");
  }

  /* ── seretan ───────────────────────────────────────────────────────── */

  function lebarBuku() { return buku.getBoundingClientRect().width || 1; }

  /* Seretan ditangkap di SELURUH layar, bukan cuma di atas halamannya.
     Di HP tegak, halaman A4 menyisakan pita kosong di atas dan di bawah;
     kalau jari kebetulan mendarat di situ, kartu terasa mati. Yang
     dikecualikan cuma tombol — menyeret dari atas tombol navigasi atau
     tombol musik jelas bukan maksudnya membalik halaman. */
  // .gulir: surat panjang yang sedang digulir (lihat muatkan) — jari yang
  // menggulirnya tidak boleh ikut menarik lembar atau tersapu jadi pindah halaman.
  var BUKAN_SERETAN = ".nav, #bgmFab, #fsFab, .preview-bar, a, button, .gulir";

  /* Mode "partikel": tidak ada lembar yang bisa ditarik, jadi seluruh
     mesin seret di bawah dilewati. Yang tersisa cuma SAPUAN — geser
     mendatar untuk pindah halaman, karena di HP itu gerakan yang paling
     dinanti orang. Ambangnya jarak ATAU kecepatan: sapuan pendek tapi
     cepat tetap terbaca, sama seperti lemparan di mode balik lembar. */
  var sapu = null;
  var SAPU_JARAK = 46;      // px
  var SAPU_LAJU = 0.45;     // px/ms

  document.addEventListener("pointerdown", function (e) {
    if (e.target.closest && e.target.closest(BUKAN_SERETAN)) return;
    if (GAYA === "partikel") {
      sapu = { x0: e.clientX, y0: e.clientY, waktu: e.timeStamp };
      return;
    }
    // Menyelesaikan animasi yang berjalan, bukan membatalkannya: jari yang
    // menyentuh lembar di tengah putaran tidak boleh meninggalkan halaman
    // menggantung tanpa pernah tercatat pindah.
    hentikanAnimasi();
    var kotak = buku.getBoundingClientRect();
    seret = {
      x0: e.clientX,
      y0: e.clientY,
      // Titik pegang dalam tinggi halaman — inilah yang membedakan membuka
      // dari atas, tengah, atau bawah.
      pegang: Math.min(Math.max((e.clientY - kotak.top) / (kotak.height || 1), 0), 1),
      i: -1,
      terkunci: false,
      batal: false,
      t: 0,
      waktu: e.timeStamp,
      laju: 0,
      xAkhir: e.clientX,
    };
    pegangTerakhir = seret.pegang;
    // Klon disiapkan di sini, saat jari baru menyentuh dan belum bergerak:
    // beberapa milidetik di detik ini tidak terasa, di awal gerakan terasa.
    isiRig(idx);
  });

  document.addEventListener("pointermove", function (e) {
    if (!seret || seret.batal) return;
    var dx = e.clientX - seret.x0;
    var dy = e.clientY - seret.y0;

    if (!seret.terkunci) {
      if (Math.abs(dx) < KUNCI && Math.abs(dy) < KUNCI) return;
      if (Math.abs(dx) <= Math.abs(dy)) { seret.batal = true; return; }
      seret.mundur = dx > 0;
      seret.i = seret.mundur ? idx - 1 : idx;
      if (seret.i < 0 || seret.i > lembar.length - 2) { seret.batal = true; return; }
      seret.terkunci = true;
      seret.x0 = e.clientX;          // hitung dari titik kunci, tanpa lompatan
      lembar[seret.i].classList.add("dekat");
      if (lembar[seret.i + 1]) lembar[seret.i + 1].classList.add("dekat");
      isiRig(seret.i);
      mulaiPutaran(seret.i, seret.mundur ? 1 : 0, seret.mundur ? 1 : 0,
                   seret.pegang, 0, true, null);
      try { buku.setPointerCapture(e.pointerId); } catch (_) {}
    }

    var dt = e.timeStamp - seret.waktu;
    if (dt > 0) seret.laju = (e.clientX - seret.xAkhir) / dt;
    seret.waktu = e.timeStamp;
    seret.xAkhir = e.clientX;

    var maju = (seret.x0 - e.clientX) / lebarBuku();
    seret.t = seret.mundur
      ? Math.min(Math.max(1 + maju, 0), 1)
      : Math.min(Math.max(maju, 0), 1);
    if (jalan && jalan.seret) {
      jalan.sasaran = seret.t;
      // Gaya "rotasi": halaman menempel pada jari. Gaya "bilah": jari
      // menggeser SASARAN pegas dan lembarnya mengejar — selisih kecil
      // itulah yang memberi rasa hambatan kertas.
      if (GAYA === "rotasi") { pos = seret.t; taruh(jalan.i, pos, jalan.pegang); }
    }
    e.preventDefault();
  });

  function selesaiSeret(e) {
    /* Sapuan mode "partikel". Ditimbang di sini, bukan di pointermove:
       tidak ada yang perlu digambar selama jarinya bergerak, jadi menunggu
       sampai diangkat lebih murah dan tidak pernah salah menebak arah. */
    if (GAYA === "partikel") {
      var s2 = sapu; sapu = null;
      if (!s2 || !e) return;
      var dx2 = e.clientX - s2.x0, dy2 = e.clientY - s2.y0;
      // Gerakan yang lebih tegak daripada mendatar itu menggulir, bukan
      // menyapu — jangan diambil alih.
      if (Math.abs(dx2) <= Math.abs(dy2)) return;
      var laju2 = Math.abs(dx2) / Math.max(1, e.timeStamp - s2.waktu);
      if (Math.abs(dx2) < SAPU_JARAK && laju2 < SAPU_LAJU) return;
      abaikanKlik = true;
      geser(dx2 < 0 ? 1 : -1);
      return;
    }
    if (!seret) return;
    var s = seret;
    seret = null;
    if (!s.terkunci) return;
    if (e) { try { buku.releasePointerCapture(e.pointerId); } catch (_) {} }
    abaikanKlik = true;

    // Lemparan cepat menang atas posisi: jari yang menyentak ke kiri di
    // sepertiga awal jelas bermaksud membuka, walau lembarnya baru sedikit.
    var lempar = Math.abs(s.laju) > LAJU_LEMPAR ? (s.laju < 0 ? 1 : 0) : null;
    var tujuan = lempar !== null ? lempar : (s.t > AMBANG ? 1 : 0);
    var halamanBaru = tujuan === 1 ? s.i + 1 : s.i;

    // Kecepatan jari (px/ms) diteruskan jadi kecepatan pegas (satuan t per
    // detik). Inilah momentumnya: sentakan cepat terbawa sampai selesai,
    // tanpa aturan durasi terpisah.
    if (jalan) {
      jalan.seret = false;
      jalan.sasaran = tujuan;
      jalan.selesai = function () { pasang(halamanBaru); };
      laju = -s.laju * 1000 / lebarBuku();
      if (GAYA === "rotasi") luncurTransisi();
      else if (!rafId) rafId = requestAnimationFrame(langkah);
    } else {
      mulaiPutaran(s.i, s.t, tujuan, s.pegang,
                   -s.laju * 1000 / lebarBuku(), false,
                   function () { pasang(halamanBaru); });
    }
  }

  document.addEventListener("pointerup", selesaiSeret);
  document.addEventListener("pointercancel", selesaiSeret);

  /* Seretan tidak boleh ikut terbaca sebagai klik. Penting saat menyunting:
     di sana klik memilih elemen untuk diedit, dan menyeret halaman lalu
     tiba-tiba membuka panel teks terasa seperti kartunya salah pencet.
     Fase tangkap, dan skrip ini dimuat sebelum card-frame.js, jadi
     penyaringnya berjalan lebih dulu. */
  document.addEventListener("click", function (e) {
    if (!abaikanKlik) return;
    abaikanKlik = false;
    e.preventDefault();
    e.stopPropagation();
  }, true);

  /* Bendera di atas hanya boleh berlaku untuk klik yang lahir dari sapuan
     yang BARU saja selesai — dan di layar sentuh klik itu sering tidak
     pernah lahir sama sekali, karena browser menahannya begitu jarinya
     bergeser jauh. Dulu bendera yang tidak terpakai itu menginap, lalu
     menelan KETUKAN BERIKUTNYA yang sah.

     Terukur di emulasi sentuh 400x800: sapu satu halaman, lalu ketuk tombol
     "›" — halamannya diam. Baru ketukan kedua bekerja. Persis rasa
     "nyangkut" yang dilaporkan, dan paling sering terasa di editor, tempat
     ketukan itu dipakai untuk memilih teks yang mau diubah.

     Dihapus di awal tiap gerakan baru, bukan lewat batas waktu: klik milik
     gerakan sebelumnya sudah pasti lewat pada titik ini, karena urutan
     kejadiannya selalu pointerdown -> pointerup -> click. Fase tangkap
     supaya berjalan sebelum penangan pointerdown di atas. */
  document.addEventListener("pointerdown", function () {
    abaikanKlik = false;
  }, true);

  /* Di halaman contoh (dan saat pemilik situs mengintip kartu yang belum
     dibayar) ada bilah tetap di dasar layar. Tombol balik halaman duduk di
     tempat yang sama, dan yang tertutup adalah tombol "Pakai template ini" —
     tepat tombol yang dituju calon pembeli. Tingginya diukur, bukan
     ditebak, karena isi bilahnya berbeda antara dua keadaan itu. */
  /* Ditunda sampai DOM selesai diurai: skrip ini disisipkan SEBELUM
     {% include _preview_bar.html %}, jadi kalau dijalankan langsung,
     bilahnya belum ada dan pencariannya selalu nihil. */
  document.addEventListener("DOMContentLoaded", function () {
    var bar = document.querySelector(".preview-bar");
    if (!bar) return;
    var naik = bar.offsetHeight + 12;
    var nav = document.querySelector(".nav");
    if (nav) nav.style.bottom = naik + "px";
    if (petunjuk) petunjuk.style.bottom = naik + 44 + "px";
  });

  /* ── kalender halaman 5: memilih tanggal yang dilingkari ─────────────
     Hatinya dipindah SEKETIKA di sini, tidak menunggu balasan editor —
     kalau menunggu, ada jeda antara jari menekan dan hati berpindah, dan
     jeda itu terbaca sebagai klik yang tidak masuk. */
  var lingkaran = document.querySelector(".lingkaran");
  [].forEach.call(document.querySelectorAll(".hari"), function (b) {
    b.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      var n = b.dataset.hari;
      // setAttribute, bukan .className: pada elemen SVG className itu
      // SVGAnimatedString dan tidak bisa ditulis begitu saja.
      if (lingkaran) lingkaran.setAttribute("class", "lingkaran hh" + n);
      if (window.simpanTeks) window.simpanTeks("hari", n);
    });
  });

  /* ── tombol, titik, papan ketik ─────────────────────────────────────── */

  if (dotsEl) {
    lembar.forEach(function (_, i) {
      var d = document.createElement("i");
      d.addEventListener("click", function () { ke(i); });
      dotsEl.appendChild(d);
    });
  }
  /* ── TIDAK ADA suara membalik halaman ───────────────────────────────
     Dicabut 18 Agu 2026 atas permintaan pemilik situs: satu-satunya suara
     di kartu ini adalah lagu YouTube yang dipilih pembeli (_bgm.html).
     Efek gesekan kertasnya bertumpuk di atas lagu itu.

     Yang ikut hilang: unduhan klip dari data-suara, penguraiannya,
     desis cadangan Web Audio (suaraSintetis), tombol ♪, dan kunci
     localStorage "kartuku-suara-halaman".

     Catatan lama di CLAUDE.md berbunyi "jangan hapus sintesisnya, itu
     jalur cadangannya". Aturan itu SUDAH DIBATALKAN — ia menjaga
     cadangan bagi suara yang sekarang memang tidak dikehendaki. Kalau
     suatu hari suaranya diminta lagi, ambil dari riwayat git, jangan
     tulis ulang dari nol. */

  /* ── ketuk tepi kanan / kiri ─────────────────────────────────────────
     Hanya ada di kartu terbit (lihat valentine.html): saat menyunting,
     zona ini akan menelan klik pada teks dan bingkai foto yang dekat tepi. */
  [].forEach.call(document.querySelectorAll(".zona"), function (z) {
    var arah = Number(z.dataset.arah) || 1;
    z.addEventListener("click", function () { geser(arah); });
    z.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); geser(arah); }
    });
  });

  /* Tombol menyatakan MAKSUD ("berikutnya"), bukan nomor halaman. Bedanya
     penting sejak satu putaran memakan 1,4 detik: penerima yang menekan dua
     kali beruntun menekan yang kedua saat idx masih halaman lama, jadi
     nomor yang dihitung sama dengan yang sedang dituju — dan tekanan kedua
     diam-diam tidak melakukan apa-apa. Di sini putaran yang berjalan
     diselesaikan dulu, baru nomornya dihitung. */
  function geser(langkah) {
    hentikanAnimasi();
    ke(idx + langkah);
  }
  if (prevBtn) prevBtn.addEventListener("click", function () { geser(-1); });
  if (nextBtn) nextBtn.addEventListener("click", function () { geser(1); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "ArrowRight" || e.key === "PageDown") geser(1);
    if (e.key === "ArrowLeft" || e.key === "PageUp") geser(-1);
  });

  /* ── jalan masuk editor ────────────────────────────────────────────── */
  window.show = function (id) {
    var i = -1;
    lembar.forEach(function (el, j) { if (el.id === id) i = j; });
    if (i < 0) return;
    hentikanAnimasi();
    seret = null;
    pasang(i, false);
  };

  // ?scene= dibaca sendiri di sini, bukan diserahkan ke card-frame.js:
  // di sana yang dipasang cuma class .active, sementara buku juga harus
  // tahu lembar mana yang sudah terbalik ke kiri.
  var awal = new URLSearchParams(location.search).get("scene");
  var mulai = 0;
  if (awal) {
    lembar.forEach(function (el, j) { if (el.id === awal) mulai = j; });
  }
  pasang(mulai, false);
})();
