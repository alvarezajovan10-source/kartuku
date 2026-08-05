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
