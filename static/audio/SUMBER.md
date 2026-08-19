# Asal-usul berkas suara

**Kartu ini dijual.** Setiap berkas di folder ini harus punya lisensi yang
membolehkan pemakaian komersial, dan asal-usulnya harus bisa dibuktikan
belakangan. Jangan menaruh berkas di sini tanpa mengisi barisnya di tabel
bawah — termasuk berkas yang "cuma buat coba-coba", karena yang begitu yang
paling sering ikut ter-deploy.

## Yang TIDAK boleh

- **Audio yang diambil dari YouTube / TikTok / Instagram.** Mengunduhnya
  melanggar ToS platformnya, dan status hak ciptanya hampir selalu tidak
  jelas — kanal "sound effect" pun banyak yang mengunggah ulang milik orang.
- **Lisensi CC-BY-NC** (non-commercial). Kartunya dijual, jadi ini terlarang
  betul, bukan sekadar berisiko.
- **CC-BY tanpa mencantumkan atribusi.** Boleh dipakai, tapi nama pembuatnya
  wajib muncul di suatu tempat yang dilihat pembeli. Kalau tidak siap
  melakukan itu, pilih CC0 saja.

## Yang dipakai sekarang

| Berkas | Sumber | Pembuat | Lisensi | Diunduh |
|---|---|---|---|---|
| _(belum ada)_ | | | | |

Selama tabel ini kosong, kartu memakai **suara sintetis** yang dibangkitkan
Web Audio di `valentine.js` (`suaraSintetis()`) — bukan berkas. Itu memang
jalur cadangannya, dan kartunya tidak rusak tanpa berkas apa pun di sini.

## Cara memasang

1. Unduh berkasnya, potong satu balikan halaman saja (0,3–1 detik).
2. Ekspor MP3 mono, sasaran di bawah 30 KB per klip.
3. Simpan sebagai `balik1.mp3`, `balik2.mp3`, `balik3.mp3` di folder ini.
   Nama itu yang dibaca `data-suara` di `cards/templates/cards/render/valentine.html`.
4. Isi tabel di atas.
5. Muat ulang kartunya. Tidak perlu mengubah kode: `static_ada` menerbitkan
   URL hanya untuk berkas yang benar-benar ada, dan `valentine.js` memilih
   satu klip secara acak tiap balikan.

Tiga klip, bukan satu: satu klip yang sama diulang terus terdengar mekanis
setelah beberapa halaman. Kalau cuma punya satu rekaman panjang berisi
banyak balikan, potong tiga bagian yang berbeda darinya.

## Kandidat CC0 yang sudah diperiksa

Lisensi keempatnya diperiksa langsung di halaman sumbernya, bukan dari
ringkasan mesin pencari — di Freesound lisensinya berbeda per berkas.

| Sumber | Pembuat | Durasi | Catatan |
|---|---|---|---|
| [freesound 136778](https://freesound.org/people/davidbain/sounds/136778/) | davidbain | 1,98 s | Satu balikan, sudah bersih (noise gate −21,1 dB) |
| [freesound 431871](https://freesound.org/people/stumpbutt/sounds/431871/) | stumpbutt | 1,35 s | Satu balikan, stereo |
| [freesound 256475](https://freesound.org/people/Kodack/sounds/256475/) | Kodack | 9,36 s | Banyak balikan — bisa dipotong jadi 3 varian sekaligus |
| [freesound 519102](https://freesound.org/people/Mateusz_Chenc/sounds/519102/) | Mateusz_Chenc | 6,40 s | Banyak balikan, mono |

Mengunduh dari Freesound perlu akun gratis.

Alternatif tanpa akun: [Pixabay page-turn](https://pixabay.com/sound-effects/search/page-turn/)
— lisensinya seragam untuk seluruh situs (bebas royalti, boleh komersial,
tanpa atribusi), jadi tidak perlu diperiksa satu per satu.
