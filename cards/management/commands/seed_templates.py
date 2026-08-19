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
                # Lima belas bingkai, bukan enam belas. "f_akhir" — foto
                # pembeli sehalaman penuh di halaman 11 — dicabut 18 Agu 2026:
                # halaman itu sekarang kolase kiriman pemilik situs dengan dua
                # teks di atasnya, dan tidak ada lagi tempat untuk foto.
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
                # Halaman 11. Judulnya menggantikan huruf potongan koran
                # "HAPPY BIRTHDAY" yang sudah dihapus dari pelatnya —
                # permintaan pemilik situs, sekalian karena kartu ini kartu
                # Love Story, bukan kartu ulang tahun.
                {"key": "wish", "label": "Judul halaman penutup",
                 "default": "My wish for you"},
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
