from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cards.models import GiftCard


class Command(BaseCommand):
    help = (
        "Hapus kartu yang tidak jadi dibeli beserta fotonya. "
        "Kartu lunas TIDAK PERNAH disentuh."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours", type=int, default=24, help="Ambang draft & kedaluwarsa."
        )
        parser.add_argument(
            "--pending-hours",
            type=int,
            default=72,
            help=(
                "Ambang kartu yang menunggu pembayaran. Sengaja lebih longgar: "
                "pembeli bisa saja baru menyelesaikan transfernya besok."
            ),
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        now = timezone.now()
        # Patokannya updated_at, bukan created_at: kartu yang dibuat tiga hari
        # lalu tapi masih disunting tadi pagi jelas belum ditinggalkan, dan
        # menghapusnya berarti membuang kerja user beserta fotonya.
        stale = GiftCard.objects.filter(
            status__in=[GiftCard.Status.DRAFT, GiftCard.Status.EXPIRED],
            updated_at__lt=now - timedelta(hours=options["hours"]),
        )
        # PENDING dulu tidak pernah tersapu. Di alur pembayaran luar situs
        # (Lynk.id) webhook Midtrans tidak pernah datang, jadi status ini tidak
        # pernah berubah jadi EXPIRED dan kartunya menumpuk selamanya.
        pending = GiftCard.objects.filter(
            status=GiftCard.Status.PENDING,
            updated_at__lt=now - timedelta(hours=options["pending_hours"]),
        )

        jumlah_stale = stale.count()
        jumlah_pending = pending.count()
        total = jumlah_stale + jumlah_pending

        if options["dry_run"]:
            self.stdout.write(
                f"{total} kartu akan dihapus (dry-run) — "
                f"{jumlah_stale} draft/kedaluwarsa, {jumlah_pending} menunggu bayar."
            )
            return

        # Berkas fotonya ikut terhapus lewat signal post_delete
        # (cards/signals.py), jadi tidak perlu diurus manual di sini lagi.
        stale.delete()
        pending.delete()
        self.stdout.write(
            f"{total} kartu dihapus — "
            f"{jumlah_stale} draft/kedaluwarsa, {jumlah_pending} menunggu bayar."
        )
