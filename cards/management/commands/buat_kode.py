"""Buat kode akses sekali pakai untuk dikirim ke pembeli.

Contoh:
    manage.py buat_kode                       # 1 kode
    manage.py buat_kode 10                    # 10 kode sekaligus
    manage.py buat_kode 5 --catatan "TikTok Juli"
"""

from django.core.management.base import BaseCommand

from cards.models import AccessCode


class Command(BaseCommand):
    help = "Buat kode akses sekali pakai untuk mengaktifkan kartu."

    def add_arguments(self, parser):
        parser.add_argument(
            "jumlah", nargs="?", type=int, default=1, help="Berapa kode (default 1)."
        )
        parser.add_argument(
            "--catatan",
            default="",
            help="Jejak pembeli: nama, email, atau nomor order.",
        )

    def handle(self, *args, **options):
        jumlah = options["jumlah"]
        if jumlah < 1 or jumlah > 200:
            self.stderr.write("Jumlah harus antara 1 dan 200.")
            return

        codes = [
            AccessCode.objects.create(
                code=AccessCode.generate_code(), note=options["catatan"]
            )
            for _ in range(jumlah)
        ]

        self.stdout.write(self.style.SUCCESS(f"{len(codes)} kode dibuat:\n"))
        for entry in codes:
            self.stdout.write(f"  {entry.code}")

        belum = AccessCode.objects.filter(used_at__isnull=True).count()
        self.stdout.write(f"\nTotal kode belum terpakai: {belum}")
