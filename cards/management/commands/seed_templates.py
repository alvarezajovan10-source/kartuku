from django.core.management.base import BaseCommand

from cards.models import CardType, Template

SEEDS = [
    # renderer → cards/templates/cards/render/<nama>.html
    (
        "klasik-ulang-tahun",
        "Amplop Merah",
        CardType.BIRTHDAY,
        {"accent": "#9e1b32", "renderer": "birthday"},
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
                {"key": "cover_title", "label": "Judul sampul", "default": "UNTUKMU"},
                {"key": "cover_sub", "label": "Sub sampul", "default": "sebuah cerita kecil tentang kamu"},
                {"key": "bab1_label", "label": "Judul bab 1", "default": "AWAL"},
                {"key": "bab1_note", "label": "Cerita bab 1", "default": "Sejak kamu hadir, hari-hari biasa mendadak terasa lebih hangat. Aku masih ingat semuanya seperti baru kemarin."},
                {"key": "bab2_label", "label": "Judul bab 2", "default": "TUMBUH"},
                {"key": "bab2_note", "label": "Cerita bab 2", "default": "Kita pelan-pelan bertumbuh — lewat tawa, salah paham kecil, dan ribuan momen yang bikin aku makin memilihmu tiap hari."},
                {"key": "momen_label", "label": "Judul bab momen", "default": "MOMEN"},
                {"key": "momen_strip", "label": "Keterangan momen", "default": "momen-momen yang nggak akan aku lupa"},
                {"key": "cinta_label", "label": "Judul bab cinta", "default": "CINTA"},
                {"key": "cinta_note", "label": "Cerita bab cinta", "default": "Hal-hal kecil yang kamu sukai, cara matamu berbinar waktu cerita soal itu — semuanya aku simpan baik-baik."},
                {"key": "harapan_label", "label": "Judul bab harapan", "default": "HARAPAN"},
                {"key": "closing_label", "label": "Judul penutup", "default": "SELAMAT"},
                {"key": "closing_line", "label": "Kalimat penutup", "default": "Ulang tahun,"},
                {"key": "from_line", "label": "Kata pengantar nama", "default": "dengan cinta,"},
            ],
        },
    ),
    (
        "klasik-anniversary",
        "Kanvas Klasik",
        CardType.ANNIVERSARY,
        {"accent": "#a8586f", "renderer": "kanvas"},
    ),
    (
        "klasik-love-story",
        "Kanvas Klasik",
        CardType.LOVE_STORY,
        {"accent": "#8d5a8f", "renderer": "kanvas"},
    ),
    (
        "klasik-lamaran",
        "Kanvas Klasik",
        CardType.PROPOSAL,
        {"accent": "#5a6b8d", "renderer": "kanvas"},
    ),
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
