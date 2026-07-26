from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cards.models import GiftCard


class Command(BaseCommand):
    help = "Hapus draft yang tidak dibayar lebih dari N jam. Kartu lunas tidak disentuh."

    def add_arguments(self, parser):
        parser.add_argument("--hours", type=int, default=24)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(hours=options["hours"])
        stale = GiftCard.objects.filter(
            status__in=[GiftCard.Status.DRAFT, GiftCard.Status.EXPIRED],
            created_at__lt=cutoff,
        )
        count = stale.count()

        if options["dry_run"]:
            self.stdout.write(f"{count} kartu akan dihapus (dry-run).")
            return

        # Hapus file foto dulu; FileField tidak menghapus objek storage sendiri.
        for card in stale.prefetch_related("photos"):
            for photo in card.photos.all():
                photo.image.delete(save=False)
        stale.delete()
        self.stdout.write(f"{count} kartu dihapus.")
