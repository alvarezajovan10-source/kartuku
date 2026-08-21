from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from cards.models import GiftCard


class Command(BaseCommand):
    help = (
        "Hapus kartu yang tidak jadi dibeli beserta fotonya. "
        "Kartu lunas TIDAK PERNAH disentuh."
    )

    # 30 hari, dinaikkan dari 24 jam (draft) dan 72 jam (menunggu bayar) atas
    # keputusan pemilik situs, 21 Agu 2026.
    #
    # Angka lama dipilih waktu belum ada datanya. Sesudah tiga minggu tayang,
    # datanya bilang begini: 57 draft menganggur, 8 di antaranya baru
    # ditinggalkan hari itu dan 36 berumur 7-30 hari — dan seluruh media situs
    # cuma 11 MB dari jatah 512 MB. Jadi ambang 24 jam membuang kerja orang
    # yang mungkin masih mau kembali, demi menghemat ruang yang tidak sedang
    # sempit. Pembeli yang menyusun kartu ulang tahun tiga minggu sebelum
    # harinya adalah pembeli yang wajar, bukan sampah.
    #
    # Kedua ambang kini SAMA. Dulu "menunggu bayar" sengaja lebih longgar
    # daripada draft karena 24 jam terlalu galak untuk orang yang transfernya
    # baru selesai besok — alasan yang habis dengan sendirinya begitu
    # keduanya jadi 30 hari. Tidak ada yang menyelesaikan transfer sebulan
    # kemudian lalu berharap drafnya masih ada.
    #
    # Yang TIDAK berubah: kartu lunas tidak pernah disentuh, dan patokannya
    # tetap updated_at.
    TENGGANG_JAM = 30 * 24

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours", type=int, default=self.TENGGANG_JAM,
            help="Ambang draft & kedaluwarsa, dalam jam. Bawaan 30 hari.",
        )
        parser.add_argument(
            "--pending-hours",
            type=int,
            default=self.TENGGANG_JAM,
            help="Ambang kartu yang menunggu pembayaran, dalam jam. Bawaan 30 hari.",
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
