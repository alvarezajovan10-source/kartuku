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
                {"key": "harapan_label", "label": "Judul bab harapan", "default": "for you"},
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
                # Desain aslinya tidak punya slot foto sama sekali; dua kucing
                # piksel di halaman PLAYER SELECT dijadikan slot pemain, dan
                # empat ubin POWER UPS dijadikan kenangan.
                {"key": "p1", "label": "Foto pemain 1", "area": "player"},
                {"key": "p2", "label": "Foto pemain 2", "area": "player"},
                {"key": "g1", "label": "Power up 1", "area": "powerups"},
                {"key": "g2", "label": "Power up 2", "area": "powerups"},
                {"key": "g3", "label": "Power up 3", "area": "powerups"},
                {"key": "g4", "label": "Power up 4", "area": "powerups"},
            ],
            "texts": [
                # Bawaan = contoh nada yang bisa ditiru pembeli, bukan perintah.
                # Huruf besar disengaja: itu bahasa layar permainan 8-bit.
                {"key": "title_main", "label": "Judul utama", "default": "HAPPY BIRTHDAY"},
                {"key": "title_start", "label": "Tombol mulai", "default": "PRESS START"},
                {"key": "player_head", "label": "Judul pilih pemain", "default": "PLAYER SELECT"},
                {"key": "player_1p", "label": "Label pemain 1", "default": "1P"},
                {"key": "player_2p", "label": "Label pemain 2", "default": "2P"},
                {"key": "level_kick", "label": "Pembuka naik level", "default": "pengalaman bertambah..."},
                {"key": "level_head", "label": "Judul naik level", "default": "LEVEL UP!"},
                {"key": "level_stat", "label": "Statistik level", "default": "HP +100  LOVE +999"},
                {"key": "ach_head", "label": "Judul pencapaian", "default": "ACHIEVEMENT UNLOCKED"},
                {"key": "ach_name", "label": "Nama pencapaian", "default": "SOULMATE FOUND"},
                {"key": "ach_note", "label": "Catatan pencapaian", "default": "dicapai pada hari kita ketemu, dan belum pernah dilepas sejak itu."},
                {"key": "power_head", "label": "Judul power up", "default": "POWER UPS"},
                {"key": "power_note", "label": "Catatan power up", "default": "ketuk tiap kotak buat lihat isinya"},
                {"key": "score_head", "label": "Judul skor", "default": "HIGH SCORES"},
                {"key": "score_l1", "label": "Skor 1: nama", "default": "LOVE"},
                {"key": "score_v1", "label": "Skor 1: angka", "default": "99999"},
                {"key": "score_l2", "label": "Skor 2: nama", "default": "JOY"},
                {"key": "score_v2", "label": "Skor 2: angka", "default": "88888"},
                {"key": "score_l3", "label": "Skor 3: nama", "default": "CUTE"},
                {"key": "score_v3", "label": "Skor 3: angka", "default": "77777"},
                {"key": "over_head", "label": "Judul penutup (dicoret)", "default": "GAME OVER?"},
                {"key": "over_big", "label": "Jawaban penutup", "default": "NEVER!"},
                {"key": "over_note", "label": "Kalimat penutup", "default": "CONTINUE TOGETHER FOREVER"},
                {"key": "over_btn", "label": "Tombol main lagi", "default": "PLAY AGAIN"},
            ],
        },
    ),
    # Anniversary, Love Story, dan Proposal sengaja belum ada isinya.
    # Kategorinya tetap tampil di situs sebagai "Coming soon" — lihat
    # _category_cards() di cards/views.py, yang menandai kategori tanpa
    # template aktif. Tambahkan di sini kalau templatenya sudah jadi.
]


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
                    "is_active": True,
                },
            )
            verb = "dibuat" if created else "diperbarui"
            self.stdout.write(f"{slug} {verb}")
