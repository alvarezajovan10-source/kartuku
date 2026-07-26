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
