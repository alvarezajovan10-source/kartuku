from django.core.management.base import BaseCommand

from cards.models import CardType, Template

SEEDS = [
    # renderer → cards/templates/cards/render/<nama>.html
    (
        "klasik-ulang-tahun",
        "Amplop Merah",
        CardType.BIRTHDAY,
        {
            "accent": "#9e1b32",
            "renderer": "birthday",
            "frames": [
                {"key": "hero", "label": "Foto latar ucapan", "area": "hero"},
                {"key": "p1", "label": "Polaroid kiri", "area": "letter"},
                {"key": "p2", "label": "Polaroid tengah", "area": "letter"},
                {"key": "p3", "label": "Polaroid kanan", "area": "letter"},
            ],
            "texts": [
                {"key": "cover_title", "label": "Judul sampul", "default": "Happy Birthday!"},
                {"key": "cover_hint", "label": "Petunjuk sampul", "default": "ketuk segel untuk membuka"},
                {"key": "hero_sub", "label": "Kalimat pembuka", "default": "semoga hadiah kecil ini bikin harimu makin hangat"},
                {"key": "hero_button", "label": "Tombol buka", "default": "buka hadiahnya"},
                {"key": "hub_title", "label": "Judul daftar hadiah", "default": "Ini untukmu"},
                {"key": "hub_sub", "label": "Sub daftar hadiah", "default": "pilih satu per satu, ya"},
                {"key": "gift_message", "label": "Label hadiah: Pesan", "default": "Pesan"},
                {"key": "gift_flower", "label": "Label hadiah: Bunga", "default": "Bunga"},
                {"key": "gift_cake", "label": "Label hadiah: Kue", "default": "Kue"},
                {"key": "gift_song", "label": "Label hadiah: Lagu", "default": "Lagu"},
                {"key": "gift_gallery", "label": "Label hadiah: Kenangan", "default": "Kenangan"},
                {"key": "letter_head", "label": "Judul surat", "default": "Sepucuk surat"},
                {"key": "flower_head", "label": "Judul bunga", "default": "untukmu, sekuntum"},
                {"key": "flower_sub", "label": "Sub bunga", "default": "bunga kesukaanmu"},
                {"key": "cake_head", "label": "Judul kue", "default": "Make a wish"},
                {"key": "cake_hint", "label": "Petunjuk kue", "default": "ketuk kuenya untuk meniup lilin"},
                {"key": "cake_wish", "label": "Kalimat harapan", "default": "semoga terkabul"},
                {"key": "song_head", "label": "Judul lagu", "default": "Lagu ini mengingatkanku padamu"},
                {"key": "song_caption", "label": "Sub lagu", "default": "putar, dan ingat kita"},
                {"key": "gallery_head", "label": "Judul kenangan", "default": "Kenangan kita"},
            ],
        },
    ),
    (
        "scrapbook-cerita",
        "Scrapbook Cerita",
        CardType.BIRTHDAY,
        {
            "accent": "#2c2420",
            "renderer": "scrapbook",
            "frames": [
                {"key": "b1a", "label": "Foto bab Awal (kiri)", "area": "bab1"},
                {"key": "b1b", "label": "Foto bab Awal (kanan)", "area": "bab1"},
                {"key": "b2a", "label": "Foto bab Tumbuh", "area": "bab2"},
                {"key": "m1", "label": "Momen 1", "area": "momen"},
                {"key": "m2", "label": "Momen 2", "area": "momen"},
                {"key": "m3", "label": "Momen 3", "area": "momen"},
                {"key": "c1", "label": "Foto bab Cinta", "area": "cinta"},
            ],
            "texts": [
                # Bawaan ini bukan sekadar isian sementara — inilah yang dilihat
                # pembeli saat pertama membuka editor, jadi tugasnya memberi
                # contoh nada yang bisa mereka tiru. Huruf kecil disengaja:
                # itu gaya yang dipakai pemilik situs untuk template ini.
                {"key": "cover_title", "label": "Judul sampul", "default": "Hi Sayang"},
                {"key": "cover_sub", "label": "Sub sampul", "default": "i got something for you"},
                {"key": "bab1_label", "label": "Judul bab 1", "default": "Happy Birthday"},
                {"key": "bab1_note", "label": "Cerita bab 1", "default": "happy birthday to my favorite person in the world."},
                {"key": "bab2_label", "label": "Judul bab 2", "default": "Wishes for you"},
                {"key": "bab2_note", "label": "Cerita bab 2", "default": "i want you to know how loved you are, not just because it's your birthday but because every single day you deserve the world, and i never want to lose you."},
                {"key": "momen_label", "label": "Judul bab momen", "default": "Random Pict"},
                {"key": "momen_strip", "label": "Keterangan momen", "default": "my fav random things with you"},
                {"key": "cinta_label", "label": "Judul bab cinta", "default": "our first date"},
                {"key": "cinta_note", "label": "Cerita bab cinta", "default": "Thank you for always loving me and being there for me."},
                {"key": "closing_label", "label": "Judul penutup", "default": "Happy Birthday"},
                # Sengaja kosong — lihat catatan di bab CLOSING scrapbook.html.
                {"key": "closing_line", "label": "Kalimat penutup", "default": ""},
                {"key": "from_line", "label": "Kata pengantar nama", "default": "with love,"},
            ],
        },
    ),
    (
        "game-8bit",
        "Game 8-Bit",
        CardType.BIRTHDAY,
        {
            "accent": "#ff2d8a",
            # Satu-satunya renderer MENDATAR 16:9 (data-stage="lebar"),
            # mengikuti desain Canva aslinya yang 1376x768.
            "renderer": "game8bit",
            "frames": [
                # Desain aslinya tidak punya slot foto sama sekali; keempat
                # ubin POWER UPS dijadikan kenangan. Keterangan di balik ubin
                # memakai GiftPhoto.caption — kotak yang sudah ada di panel
                # foto — bukan kolom teks tersendiri. "cap_note" cuma mengganti
                # kalimat penjelas di bawah kotak itu, karena kalimat bawaannya
                # ("tulisan tangan di bawah foto") tidak berlaku di sini. Halaman PLAYER SELECT
                # sempat punya slot foto juga, lalu dicabut: kotak di sana
                # memajang potret kedua karakter supaya jelas kolom nama mana
                # milik siapa, dan foto pembeli menghapus petunjuk itu.
                {"key": "g1", "label": "Momen 1", "area": "powerups",
                 "cap_note": "Muncul di balik ubinnya waktu penerima membaliknya."},
                {"key": "g2", "label": "Momen 2", "area": "powerups",
                 "cap_note": "Muncul di balik ubinnya waktu penerima membaliknya."},
                {"key": "g3", "label": "Momen 3", "area": "powerups",
                 "cap_note": "Muncul di balik ubinnya waktu penerima membaliknya."},
                {"key": "g4", "label": "Momen 4", "area": "powerups",
                 "cap_note": "Muncul di balik ubinnya waktu penerima membaliknya."},
            ],
            "texts": [
                # Bawaan = contoh nada yang bisa ditiru pembeli, bukan perintah.
                # Huruf besar disengaja: itu bahasa layar permainan 8-bit.
                {"key": "title_main", "label": "Judul utama", "default": "HAPPY BIRTHDAY"},
                {"key": "title_start", "label": "Tombol mulai", "default": "PRESS START"},
                {"key": "player_head", "label": "Judul pilih pemain", "default": "PLAYER SELECT"},
                {"key": "player_1p", "label": "Tulisan kotak kiri", "default": "1P"},
                {"key": "player_2p", "label": "Tulisan kotak kanan", "default": "2P"},
                # Nama karakter, TERPISAH dari nama penerima di layar judul.
                # Sempat memakai kolom yang sama, dan akibatnya mengetik nama
                # di layar judul ikut mengubah nama pemain 1 — dua hal beda
                # yang tidak boleh saling menyeret.
                {"key": "nama1", "label": "Nama karakter cowok", "default": "PLAYER 1"},
                {"key": "nama2", "label": "Nama karakter cewek", "default": "PLAYER 2"},
                {"key": "level_kick", "label": "Pembuka naik level", "default": "there's a suprise for you"},
                {"key": "level_head", "label": "Judul naik level", "default": "LEVEL UP!"},
                {"key": "level_stat", "label": "Statistik level", "default": "HP +100  LOVE +999"},
                {"key": "wish_head", "label": "Judul wishes", "default": "WISHES"},
                # Satu kolom untuk seluruh harapan. Sempat dua (judul + catatan),
                # dan yang di luar kotak tumpah keluar kartu kalau panjang.
                {"key": "wish_note", "label": "Isi harapan", "default": "semoga tahun ini sebaik kamu memperlakukan orang lain, dan semoga aku masih di sampingmu waktu itu terjadi."},
                {"key": "peluk_btn", "label": "Tombol peluk", "default": "HUG"},
                {"key": "power_head", "label": "Judul momen", "default": "MOMENTS"},
                {"key": "power_note", "label": "Catatan momen", "default": "ketuk tiap kotak buat lihat isinya"},
                # Dulu HIGH SCORES: tiga baris angka karangan. Dicabut atas
                # permintaan pemilik kartu — angkanya tidak menyumbang apa
                # pun, cuma membuat template terlihat sibuk.
                {"key": "kue_head", "label": "Judul tiup lilin", "default": "MAKE A WISH"},
                {"key": "kue_note", "label": "Petunjuk tiup lilin", "default": "ketuk tiap api lilinnya"},
                {"key": "over_head", "label": "Judul penutup (dicoret)", "default": "GAME OVER?"},
                {"key": "over_big", "label": "Jawaban penutup", "default": "NEVER!"},
                {"key": "over_note", "label": "Kalimat penutup", "default": "CONTINUE TOGETHER FOREVER"},
                {"key": "over_btn", "label": "Tombol main lagi", "default": "PLAY AGAIN"},
            ],
        },
    ),
    (
        "valentine-story",
        "Valentine Story",
        CardType.LOVE_STORY,
        {
            "accent": "#aa1717",
            # Satu-satunya renderer berbentuk BUKU (data-stage="buku"):
            # halaman A4 tegak yang dibalik satu per satu dengan jari.
            #
            # Halamannya tidak digambar ulang di CSS. Tiap halaman adalah
            # pelat hasil ekspor Canva pemilik situs (static/img/valentine/),
            # dengan teks yang boleh disunting dihapus dari gambarnya dan
            # area foto dilubangi. Karena itu koordinat teks & bingkai di
            # valentine.css TIDAK boleh digeser sendiri — pasangannya adalah
            # pelat gambar, bukan tata letak yang bebas diatur.
            "renderer": "valentine",
            # "rasio" = lebar/tinggi bingkai. Kotak crop di editor mengikuti
            # angka ini, supaya pembeli memilih bagian foto di bentuk yang
            # sama dengan bentuk tampilannya nanti.
            # "asli" = foto disimpan besar (2400 px, batas berkas 8MB).
            # Dipakai dua bingkai yang fotonya memenuhi satu halaman penuh
            # (sampul & penutup); pada batas biasa hasilnya terlihat pecah.
            "frames": [
                {"key": "f_sampul", "label": "Foto sampul", "area": "hal1", "rasio": 0.707, "asli": True},
                {"key": "f_film1", "label": "Strip film — atas", "area": "hal2", "rasio": 0.8764},
                {"key": "f_film2", "label": "Strip film — tengah", "area": "hal2", "rasio": 0.8764},
                {"key": "f_film3", "label": "Strip film — bawah", "area": "hal2", "rasio": 0.8764},
                {"key": "f_temu", "label": "Foto “The Day We Met”", "area": "hal4", "rasio": 0.7547},
                {"key": "f_polaroid", "label": "Foto polaroid", "area": "hal6", "rasio": 1.0373},
                {"key": "f_liontin_a", "label": "Liontin — hati kanan", "area": "hal7", "rasio": 0.9823},
                {"key": "f_liontin_b", "label": "Liontin — hati kiri", "area": "hal7", "rasio": 0.9903},
                {"key": "f_pita1", "label": "Galeri pita 1", "area": "hal8", "rasio": 1.4726},
                {"key": "f_pita2", "label": "Galeri pita 2", "area": "hal8", "rasio": 1.4726},
                {"key": "f_pita3", "label": "Galeri pita 3", "area": "hal8", "rasio": 1.4726},
                {"key": "f_klip1", "label": "Galeri jepitan — kiri atas", "area": "hal9", "rasio": 0.847},
                {"key": "f_klip2", "label": "Galeri jepitan — kanan atas", "area": "hal9", "rasio": 0.847},
                {"key": "f_klip3", "label": "Galeri jepitan — kiri bawah", "area": "hal9", "rasio": 0.847},
                {"key": "f_klip4", "label": "Galeri jepitan — kanan bawah", "area": "hal9", "rasio": 0.847},
                # Bentuk hatinya datang dari LUBANG di pelat halaman 12,
                # bukan dari CSS — bingkainya sendiri persegi, yaitu kotak
                # pembatas hatinya. "rasio" 1,0825 karena hatinya memang
                # sedikit lebih lebar daripada tinggi (416x384 px terukur di
                # gambar sumbernya), jadi kotak crop di editor pun begitu.
                {"key": "f_hati", "label": "Foto penutup — hati renda", "area": "hal12", "rasio": 1.0825},
                # Enam belas bingkai. Sempat lima belas: "f_akhir" — foto
                # pembeli sehalaman penuh di halaman 11 — dicabut 18 Agu 2026
                # waktu halaman itu jadi kolase bertulisan "My wish for you".
                # Halaman 12 (19 Agu 2026) mengembalikan satu bingkai penutup,
                # tapi bukan yang itu: bentuknya hati, bukan sehalaman penuh,
                # jadi TIDAK bertanda "asli" dan tidak memakai batas 8MB.
            ],
            # Bawaan di bawah ini disalin PERSIS dari desain Canva-nya,
            # termasuk pemenggalan barisnya. Jangan "dirapikan": pembeli
            # memilih template ini karena melihat halaman itu, dan bawaan
            # yang berbeda dari contohnya membuat kartunya terasa salah
            # sebelum sempat diisi.
            "texts": [
                {"key": "mast", "label": "Judul majalah", "default": "LOVESTORY"},
                {"key": "mast_script", "label": "Kata sambung judul", "default": "Magazine"},
                # Desain Canva-nya tertulis "4ND"; dibetulkan jadi "4TH" atas
                # keputusan pemilik situs (11 Agu 2026). Aman diubah di sini
                # karena teks sampul memang HTML — pelatnya tidak memuatnya.
                {"key": "edisi", "label": "Edisi", "default": "4TH\nANNIVERSARY\nEDITION"},
                {"key": "tanggal", "label": "Bulan & tahun sampul", "default": "JULY 2026"},
                {"key": "nama", "label": "Nama kalian", "default": "ROCKY &\nRIANA"},
                {"key": "tagline", "label": "Tagline sampul", "default": "THE PERFECT\nMATCH"},
                {"key": "kata2", "label": "Kalimat strip film", "default": "i love you endlessly."},
                # Daftar isi halaman 3. Sampai 18 Agu 2026 keempatnya menyatu
                # dengan pelat dan tidak bisa disunting sama sekali.
                #
                # "OUR LOVE LANGUANGE" di desain Canva-nya salah ketik, dan
                # sampai sekarang menunggu PDF perbaikan dari pemilik situs
                # karena hurufnya terkunci di dalam gambar. Begitu barisnya
                # jadi HTML, penantian itu selesai dengan sendirinya:
                # dibetulkan jadi "LANGUAGE" di sini, persis seperti "4ND" ->
                # "4TH" di sampul. Pelatnya tidak lagi memuat teks ini, jadi
                # tidak ada yang perlu diekspor ulang.
                #
                # Nomor halamannya (4-5, 6, 7-9, 10) ada di valentine.html
                # dan memang tidak bisa disunting — angka itu menunjuk
                # halaman yang benar-benar ada di majalah ini.
                {"key": "isi1", "label": "Daftar isi — baris 1", "default": "THE DAY WE MET"},
                {"key": "isi2", "label": "Daftar isi — baris 2", "default": "OUR LOVE LANGUAGE"},
                {"key": "isi3", "label": "Daftar isi — baris 3", "default": "PHOTO GALLERY"},
                {"key": "isi4", "label": "Daftar isi — baris 4", "default": "THINGS I LOVE ABOUT U"},
                {"key": "judul4", "label": "Judul bab pertemuan", "default": "T H E DAY\nW E M E T"},
                {"key": "body4a", "label": "Cerita pertemuan — alinea 1",
                 "default": "The day we met, I had no idea that you would become such an important part of my life. It started as an ordinary day, just another moment in time, yet somehow it became the beginning of so many of my favorite memories."},
                {"key": "body4b", "label": "Cerita pertemuan — alinea 2",
                 "default": "Looking back now, it’s strange to think that two strangers could meet and end up meaning so much to each other. Since that day, you’ve brought laughter to my quiet moments, comfort to my difficult days, and happiness in ways I never expected."},
                {"key": "body4c", "label": "Cerita pertemuan — alinea 3",
                 "default": "If I could go back and relive one moment, I think I’d choose the day we met—because it led me to you, and that’s something I’ll always be grateful for."},
                {"key": "bulan", "label": "Bulan di kalender", "default": "J u l y"},
                # Diatur dengan MENGKLIK angkanya di kalender, bukan diketik.
                # Tetap disimpan sebagai teks karena itu satu-satunya tempat
                # pilihan pembeli bisa bertahan.
                {"key": "hari", "label": "Tanggal yang dilingkari", "default": "13"},
                {"key": "judul6", "label": "Judul bab bahasa cinta", "default": "Our Love"},
                {"key": "h6a", "label": "Bahasa cinta 1 — judul", "default": "Physical Touch"},
                {"key": "t6a", "label": "Bahasa cinta 1 — kalimat",
                 "default": "My favorite place has always\nbeen right next to you."},
                {"key": "h6b", "label": "Bahasa cinta 2 — judul", "default": "Words Of Affirmation"},
                {"key": "t6b", "label": "Bahasa cinta 2 — kalimat",
                 "default": "The right words from the right person can heal\nalmost anything."},
                {"key": "eternal", "label": "Kalimat liontin", "default": "eternal love."},
                {"key": "pasangan", "label": "Nama di bawah liontin", "default": "rocky & riana"},
                {"key": "tutup7", "label": "Kalimat penutup liontin",
                 "default": "From strangers to memories, from memories to\nforever—look how far we’ve come."},
                # PENGECUALIAN dari aturan "bawaan disalin persis dari Canva"
                # di atas: keempat elips halaman 10 KOSONG di desain aslinya,
                # tidak ada satu pun contoh tulisan untuk ditiru. Empat
                # kalimat di bawah karangan sendiri, dibuat pendek supaya
                # muat dua baris di dalam oval tanpa perlu dikecilkan.
                {"key": "love1", "label": "Hal yang disukai 1",
                 "default": "the way you laugh at your own jokes"},
                {"key": "love2", "label": "Hal yang disukai 2",
                 "default": "how you always make time for me"},
                {"key": "love3", "label": "Hal yang disukai 3",
                 "default": "your hugs after a long day"},
                {"key": "love4", "label": "Hal yang disukai 4",
                 "default": "that you make me feel safe"},
                # Halaman 11. Judulnya menggantikan tulisan "Letter For
                # You" yang sudah dihapus dari pelatnya, jadi bawaannya
                # sengaja kata yang sama persis: pembeli yang tidak menyentuh
                # apa pun harus mendapat desainnya utuh seperti di Canva.
                # (Sampai 21 Agu 2026 desainnya lain dan bawaannya "My wish
                # for you" — menggantikan huruf potongan koran "HAPPY
                # BIRTHDAY".)
                {"key": "wish", "label": "Judul halaman penutup",
                 "default": "Letter For You"},
                {"key": "pesan11", "label": "Pesan penutup",
                 "default": "i want you to know how loved you are, not just "
                            "because of today but because every single day "
                            "you deserve the world, and i never want to lose you."},
            ],
        },
    ),
    # Anniversary dan Proposal sengaja belum ada isinya.
    # Kategorinya tetap tampil di situs sebagai "Coming soon" — lihat
    # _category_cards() di cards/views.py, yang menandai kategori tanpa
    # template aktif. Tambahkan di sini kalau templatenya sudah jadi.
    (
        "sweetflix",
        "Sweetflix",
        CardType.LOVE_STORY,
        {
            # Merah streaming, tapi SENGAJA bukan #E50914 milik Netflix.
            "accent": "#e11d3c",
            # Renderer MENDATAR kedua (data-stage="lebar"), mengikuti tangkapan
            # layar rujukan pemilik situs.
            "renderer": "sweetflix",
            # SATU profil. Sempat empat (butuh 41 foto — di atas
            # MAX_PHOTOS_PER_CARD 30 dan ~82MB per kartu), lalu dua, dan
            # akhirnya satu atas permintaan pemilik situs. Sekarang 11 foto.
            # Menambah profil berarti menghitung ulang jatah fotonya.
            # "rasio" = lebar/tinggi bingkai. Kotak crop di editor
            # mengikuti angka ini (alpine-editor.js:574); tanpa itu ia
            # selalu bujur sangkar, dan pembeli memilih bagian fotonya di
            # bentuk yang bukan bentuk tampilannya. "asli" menaikkan sisi
            # panjang hasil potongan dari 1100 ke 2400 px — untuk foto yang
            # memenuhi satu layar penuh, 1100 px terlihat pecah.
            # "sisi" hanya di dua bingkai LATAR. Kartu mendatar dibentangkan
            # memenuhi jendela tanpa batas pembesaran, jadi di laptop retina
            # satu piksel foto harus mengisi 3.398 piksel layar: pada 2400 px
            # rasionya 0,71 (masih lembut), pada 3200 px jadi 0,94. Poster dan
            # avatar TIDAK diubah — mereka tampil kecil dan sudah tajam.
            "frames": [
                {"key": "f_buka", "label": "Foto layar pembuka", "rasio": 1.7778, "asli": True, "sisi": 3200},
                {"key": "a_avatar", "label": "KAMU · Foto profil", "rasio": 1.0},
                {"key": "a_hero", "label": "KAMU · Foto latar", "rasio": 1.7778, "asli": True, "sisi": 3200},
                {"key": "a_p1", "label": "KAMU · Poster 1", "rasio": 1.7778},
                {"key": "a_p2", "label": "KAMU · Poster 2", "rasio": 1.7778},
                {"key": "a_p3", "label": "KAMU · Poster 3", "rasio": 1.7778},
                {"key": "a_p4", "label": "KAMU · Poster 4", "rasio": 1.7778},
                {"key": "a_p5", "label": "KAMU · Poster 5", "rasio": 1.7778},
                {"key": "a_p6", "label": "KAMU · Poster 6", "rasio": 1.7778},
                {"key": "a_p7", "label": "KAMU · Poster 7", "rasio": 1.7778},
                {"key": "a_p8", "label": "KAMU · Poster 8", "rasio": 1.7778},
            ],
            "texts": [
                # Bawaan ini yang pertama dilihat pembeli waktu membuka editor,
                # jadi tugasnya memberi contoh nada yang bisa ditiru.
                #
                # Cerita tiap poster TIDAK ada di sini: ia diambil dari caption
                # fotonya (GiftPhoto.caption), supaya pembeli cukup mengetik di
                # satu tempat. Batas caption 40 karakter, dan pemilik situs
                # menerima batas itu apa adanya — lihat models.py:229.
                {"key": "merek", "label": "Nama layanan", "default": "SWEETFLIX"},
                {"key": "buka_judul", "label": "Judul halaman pertama", "default": "Who's watching?"},
                {"key": "buka_sub", "label": "Sub halaman pertama", "default": "Let's start with your name."},
                {"key": "judul_pilih", "label": "Judul layar pilih profil", "default": "Choose"},
                {"key": "putar_teks", "label": "Teks saat foto diputar", "default": "I love you forever and ever!"},
                {"key": "a_cap", "label": "KAMU · Nama profil", "default": "KAMU"},
                {"key": "a_judul", "label": "KAMU · Judul banner", "default": "Love of My Life"},
                {"key": "a_meta", "label": "KAMU · Baris keterangan", "default": "Serial · Romantis · 2024 · 12 Episode"},
                {"key": "a_desk", "label": "KAMU · Ucapan singkat", "default": "happy birthday to my favorite person in the world. you're the best person i could ever ask for, and i don't know where i'd be without you. you're the funniest, sweetest, and most loving person ever"},
                {"key": "a_baris1", "label": "KAMU · Judul baris", "default": "Our Pictures"},
            ],
        },
    ),
    (
        "birthday-magazine",
        "Birthday Magazine",
        CardType.BIRTHDAY,
        {
            "accent": "#c2185b",
            # Majalah ulang tahun TERBUKA dari desain Canva "magazine template 1"
            # (6 Okt 2026): rangka & balik hamparan dari Majalah Cinta, halaman
            # berupa PELAT berlubang seperti Valentine Story.
            #
            # Daftar di bawah ini KELUARAN tools/buat_html_bdaymag.py
            # (tools/bdaymag/seed_config.json) — kotak foto, "rasio", dan teks
            # bawaannya diturunkan dari koordinat Canva yang sama dengan
            # pelatnya. Jangan disunting di sini; ubah tools/bdaymag/spek.py
            # lalu jalankan ulang skripnya dan salin hasilnya.
            "renderer": "bdaymag",
            "frames": [
                {"key": "f_sampul", "label": "Foto sampul", "area": "bm1", "rasio": 0.689, "asli": True},
                {"key": "f_isi1", "label": "Daftar isi — foto 1", "area": "bm2", "rasio": 1.234},
                {"key": "f_isi2", "label": "Daftar isi — foto 2", "area": "bm2", "rasio": 1.173},
                {"key": "f_isi3", "label": "Daftar isi — foto 3", "area": "bm2", "rasio": 1.256},
                {"key": "f_isi4", "label": "Daftar isi — foto 4", "area": "bm2", "rasio": 1.415},
                {"key": "f_editor", "label": "Foto Editor's Notes", "area": "bm3", "rasio": 1.711},
                {"key": "f_cheers", "label": "Polaroid Cheers", "area": "bm3", "rasio": 1.471},
                {"key": "f_girl", "label": "Potret Who's That Girl", "area": "bm4", "rasio": 0.363, "asli": True},
                {"key": "f_girl1", "label": "Galeri dia — besar 1", "area": "bm4", "rasio": 0.778},
                {"key": "f_girl2", "label": "Galeri dia — besar 2", "area": "bm4", "rasio": 1.484},
                {"key": "f_girl3", "label": "Galeri dia — besar 3", "area": "bm4", "rasio": 1.071},
                {"key": "f_girl4", "label": "Galeri dia — kecil 1", "area": "bm4", "rasio": 1.132},
                {"key": "f_girl5", "label": "Galeri dia — kecil 2", "area": "bm4", "rasio": 1.132},
                {"key": "f_girl6", "label": "Galeri dia — kecil 3", "area": "bm4", "rasio": 1.132},
                {"key": "f_girl7", "label": "Galeri dia — kecil 4", "area": "bm4", "rasio": 1.132},
                {"key": "f_j1", "label": "Polaroid perjalanan 1", "area": "bm5", "rasio": 0.93},
                {"key": "f_j2", "label": "Polaroid perjalanan 2", "area": "bm5", "rasio": 0.935},
                {"key": "f_j3", "label": "Polaroid perjalanan 3", "area": "bm5", "rasio": 1.075},
                {"key": "f_j4", "label": "Polaroid perjalanan 4", "area": "bm5", "rasio": 0.977},
                {"key": "f_j6", "label": "Polaroid perjalanan 6", "area": "bm5", "rasio": 0.899},
                {"key": "f_j5", "label": "Polaroid perjalanan 5", "area": "bm5", "rasio": 1.102},
                {"key": "f_love1", "label": "Foto besar Love (atas)", "area": "bm6", "rasio": 1.421},
                {"key": "f_love2", "label": "Foto besar You (bawah)", "area": "bm6", "rasio": 1.432},
                {"key": "f_m1", "label": "Momen 1", "area": "bm6", "rasio": 0.977},
                {"key": "f_m3", "label": "Momen 3", "area": "bm6", "rasio": 0.977},
                {"key": "f_m5", "label": "Momen 5", "area": "bm6", "rasio": 0.977},
                {"key": "f_m2", "label": "Momen 2", "area": "bm6", "rasio": 0.977},
                {"key": "f_m4", "label": "Momen 4", "area": "bm6", "rasio": 0.977},
                {"key": "f_m6", "label": "Momen 6", "area": "bm6", "rasio": 0.977},
                {"key": "f_lagu_latar", "label": "Latar halaman playlist", "area": "bm7", "rasio": 0.782, "asli": True},
                {"key": "f_lagu", "label": "Sampul lagu di pemutar", "area": "bm7", "rasio": 0.939},
                {"key": "f_lagu1", "label": "Sampul lagu 1", "area": "bm7", "rasio": 1.027},
                {"key": "f_lagu2", "label": "Sampul lagu 2", "area": "bm7", "rasio": 1.027},
                {"key": "f_lagu3", "label": "Sampul lagu 3", "area": "bm7", "rasio": 1.027},
                {"key": "f_suka1", "label": "Kesukaan — foto 1", "area": "bm8", "rasio": 0.828},
                {"key": "f_suka2", "label": "Kesukaan — foto 2", "area": "bm8", "rasio": 1.555},
                {"key": "f_suka3", "label": "Kesukaan — foto 3", "area": "bm8", "rasio": 1.339},
                {"key": "f_suka4", "label": "Kesukaan — foto 4", "area": "bm8", "rasio": 0.871},
                {"key": "f_suka5", "label": "Kesukaan — foto 5", "area": "bm8", "rasio": 2.535},
                {"key": "f_suka9", "label": "Kesukaan — foto 9", "area": "bm8", "rasio": 1.369},
                {"key": "f_suka12", "label": "Kesukaan — foto 12", "area": "bm8", "rasio": 0.77},
                {"key": "f_suka11", "label": "Kesukaan — foto 11", "area": "bm8", "rasio": 0.77},
                {"key": "f_suka10", "label": "Kesukaan — foto 10", "area": "bm8", "rasio": 0.871},
                {"key": "f_suka6", "label": "Kesukaan — polaroid kiri", "area": "bm8", "rasio": 0.938},
                {"key": "f_suka7", "label": "Kesukaan — polaroid tengah", "area": "bm8", "rasio": 1.006},
                {"key": "f_suka8", "label": "Kesukaan — polaroid kanan", "area": "bm8", "rasio": 1.072},
                {"key": "f_cermin", "label": "Foto di cermin surat", "area": "bm9", "rasio": 0.698},
            ],
            "texts": [
                {"key": "cover_masthead", "label": "Judul besar sampul", "default": "BIRTHDAY"},
                {"key": "cover_magazine", "label": "Tulisan di bawah judul", "default": "MAGAZINE"},
                {"key": "cover_kicker", "label": "Judul kecil sampul", "default": "THE IT GIRL\nFILES;\nBIRTHDAY\nEDITION"},
                {"key": "cover_age", "label": "Umur", "default": "22"},
                {"key": "cover_edition", "label": "Edisi di sampul", "default": "BIRTHDAY\nEDITION"},
                {"key": "cover_hbd", "label": "Ucapan di sampul", "default": "HAPPY BIRTHDAY."},
                {"key": "cover_name", "label": "Nama di sampul", "default": "KEELYA\nALBEY"},
                {"key": "cover_tag", "label": "Kalimat sampul", "default": "SHE GLOW, SHE LEADS,\nSHE INSPIRES."},
                {"key": "editor_title", "label": "Judul Editor's Notes", "default": "The Editors"},
                {"key": "editor_title2", "label": "Judul Editor's Notes — kata kedua", "default": "Notes"},
                {"key": "editor_note", "label": "Catatan editor", "default": "Today is not only about celebrating a birthday, but also about celebrating the person you have become through every challenge, every achievement, every lesson, and every little moment in between. Looking back, this year has been filled with growth, laughter, unexpected adventures, and countless memories that have shaped your story."},
                {"key": "girl_body", "label": "Cerita Who's That Girl", "default": "She’s the reason this special edition exists—a girl filled with kindness, laughter, and unforgettable memories. Today, we’re celebrating her story, her journey, and everything that makes her unique. From the little moments that often go unnoticed to the milestones that deserve to be remembered forever, every chapter of her life tells a story worth sharing."},
                {"key": "j1_title", "label": "Perjalanan 1 — judul", "default": "SUNSET CHATS"},
                {"key": "j4_title", "label": "Perjalanan 4 — judul", "default": "FESTIVAL FUN"},
                {"key": "j2_title", "label": "Perjalanan 2 — judul", "default": "ROOFTOP BARS"},
                {"key": "j3_title", "label": "Perjalanan 3 — judul", "default": "ARTS GALLERIES"},
                {"key": "j1_body", "label": "Perjalanan 1 — cerita", "default": "Golden skies, meaningful conversations, and the kind of friendship that makes every sunset feel a little more beautiful."},
                {"key": "j2_body", "label": "Perjalanan 2 — cerita", "default": "Good drinks, city lights, and rooftop nights that feel like they could last forever."},
                {"key": "j3_body", "label": "Perjalanan 3 — cerita", "default": "Wandering through art galleries, finding beauty in every corner and inspiration in every brushstroke."},
                {"key": "j4_body", "label": "Perjalanan 4 — cerita", "default": "Bright lights, loud music, good vibes, and unforgettable memories—festival days are always the best days."},
                {"key": "m1_cap", "label": "Momen 1 — keterangan", "default": "Laughing at nothing"},
                {"key": "m2_cap", "label": "Momen 2 — keterangan", "default": "Always hungry"},
                {"key": "m4_cap", "label": "Momen 4 — keterangan", "default": "Human sunshine"},
                {"key": "m3_cap", "label": "Momen 3 — keterangan", "default": "Walking pinterest board"},
                {"key": "m5_cap", "label": "Momen 5 — keterangan", "default": "Delulu but happy"},
                {"key": "m6_cap", "label": "Momen 6 — keterangan", "default": "The memory keeper"},
                {"key": "playlist_name", "label": "Nama di judul playlist", "default": "Keelya’s"},
                {"key": "playlist_word", "label": "Judul playlist — kata kedua", "default": "Playlist"},
                {"key": "s1_title", "label": "Lagu 1 — judul", "default": "Daisies"},
                {"key": "s1_artist", "label": "Lagu 1 — penyanyi", "default": "Justin Bieber"},
                {"key": "s2_title", "label": "Lagu 2 — judul", "default": "Lemonade"},
                {"key": "s2_artist", "label": "Lagu 2 — penyanyi", "default": "Jeremy Passion"},
                {"key": "s3_title", "label": "Lagu 3 — judul", "default": "Damned"},
                {"key": "s3_artist", "label": "Lagu 3 — penyanyi", "default": "Miguel"},
                {"key": "l1_title", "label": "Kesukaan 1 — judul", "default": "COFFEE"},
                {"key": "l1_body", "label": "Kesukaan 1 — cerita", "default": "Her daily ritual, her comfort, her little moment of peace in a busy world."},
                {"key": "l2_title", "label": "Kesukaan 2 — judul", "default": "BOOKSTORE"},
                {"key": "l2_body", "label": "Kesukaan 2 — cerita", "default": "She always leaves with more stories than she came for."},
                {"key": "l3_title", "label": "Kesukaan 3 — judul", "default": "MUSIC"},
                {"key": "l3_body", "label": "Kesukaan 3 — cerita", "default": "Every favorite song holds a memory."},
                {"key": "l4_title", "label": "Kesukaan 4 — judul", "default": "PHOTOS"},
                {"key": "l4_body", "label": "Kesukaan 4 — cerita", "default": "Capturing moments she never wants to forget."},
                {"key": "l5_title", "label": "Kesukaan 5 — judul", "default": "FLOWERS"},
                {"key": "l5_body", "label": "Kesukaan 5 — cerita", "default": "Tiny reminders that beautiful things grow slowly."},
                {"key": "l6_title", "label": "Kesukaan 6 — judul", "default": "SUNSET"},
                {"key": "l6_body", "label": "Kesukaan 6 — cerita", "default": "She could watch the sky change colors forever."},
                {"key": "l7_title", "label": "Kesukaan 7 — judul", "default": "MOVIES"},
                {"key": "l7_body", "label": "Kesukaan 7 — cerita", "default": "Escaping reality and feeling everything a little deeper."},
                {"key": "l8_title", "label": "Kesukaan 8 — judul", "default": "SWEETS"},
                {"key": "l8_body", "label": "Kesukaan 8 — cerita", "default": "Because life is always better with a little sugar."},
                {"key": "l9_title", "label": "Kesukaan 9 — judul", "default": "FRIENDS"},
                {"key": "l9_body", "label": "Kesukaan 9 — cerita", "default": "Her safe place, her laugh, her chosen family."},
                {"key": "l10_title", "label": "Kesukaan 10 — judul", "default": "JEWELRY"},
                {"key": "l10_body", "label": "Kesukaan 10 — cerita", "default": "Small details that make everything feel complete."},
                {"key": "letter_title", "label": "Judul surat", "default": "A Letter to Keelya"},
                {"key": "letter_body", "label": "Isi surat", "default": "Dear Friends,\n\nIf there’s one thing I’ll always be grateful for, it’s having people like you in my life. Thank you for the laughter, the endless conversations, the spontaneous adventures, and all the memories we’ve created together. Some of my favorite moments wouldn’t be the same without you.\n\nThank you for being there during both the good days and the difficult ones. For listening when I needed someone to talk to, celebrating my achievements as if they were your own, and reminding me that I’m never alone. Your kindness, support, and friendship have meant more to me than words can fully express.\n\nLife changes, people grow, and paths may lead us in different directions, but I hope we always carry these memories with us. No matter where we are or how much time passes, I’ll always look back on our friendship with a smile.\n\nThank you for being part of my story. I truly appreciate every moment, every laugh, and every memory we’ve shared. Here’s to all the memories behind us and all the ones still waiting to be made."},
                {"key": "letter_close", "label": "Salam penutup", "default": "With love, always."},
            ],
        },
    ),
]


# Template yang sengaja DIMATIKAN. Ditulis di sini, bukan cuma diklik di
# admin: perintah ini memaksa is_active=True tiap kali dijalankan, jadi tanpa
# daftar ini template yang dimatikan akan hidup lagi diam-diam pada deploy
# berikutnya — dan tidak ada yang menyadarinya sampai muncul lagi di galeri.
#
# Mematikan template TIDAK merusak kartu yang sudah terbit: halaman kartu
# publik merender dari template milik kartunya sendiri dan tidak pernah
# memeriksa is_active. Yang tertutup cuma pintu membuat kartu BARU.
NONAKTIF = {
    "klasik-ulang-tahun",   # Amplop Merah — dimatikan 7 Agustus 2026.
}


class Command(BaseCommand):
    help = "Isi template awal (idempoten — aman dijalankan berulang)."

    def handle(self, *args, **options):
        for slug, name, category, config in SEEDS:
            _, created = Template.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "category": category,
                    "config": config,
                    "is_active": slug not in NONAKTIF,
                },
            )
            verb = "dibuat" if created else "diperbarui"
            self.stdout.write(f"{slug} {verb}")
