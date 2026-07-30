"""Hapus template beserta kartu yang memakainya.

`seed_templates` tidak pernah menghapus apa pun — mengeluarkan template dari
daftar seed hanya membuatnya berhenti diperbarui, bukan hilang dari database
yang sudah jalan. Perintah ini menutup celah itu.

Menghapus kartu berarti menghapus kartu orang, jadi bawaannya hanya melapor.
Penghapusan sungguhan butuh --konfirmasi.

    python manage.py hapus_template klasik-anniversary
    python manage.py hapus_template klasik-anniversary --konfirmasi
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from cards.models import GiftCard, GiftPhoto, Template


class Command(BaseCommand):
    help = "Hapus template dan semua kartu yang memakainya (lapor dulu)."

    def add_arguments(self, parser):
        parser.add_argument("slug", nargs="+")
        parser.add_argument(
            "--konfirmasi",
            action="store_true",
            help="Benar-benar hapus. Tanpa ini hanya melapor.",
        )

    def handle(self, *args, **options):
        slugs = options["slug"]
        templates = Template.objects.filter(slug__in=slugs)

        hilang = set(slugs) - {t.slug for t in templates}
        for slug in sorted(hilang):
            self.stdout.write(f"  {slug}: tidak ada di database")

        if not templates:
            self.stdout.write(self.style.WARNING("Tidak ada yang bisa dihapus."))
            return

        total_kartu = total_lunas = total_foto = 0
        for template in templates:
            kartu = GiftCard.objects.filter(template=template)
            lunas = kartu.filter(status=GiftCard.Status.PAID).count()
            foto = GiftPhoto.objects.filter(card__in=kartu).count()
            jumlah = kartu.count()
            total_kartu += jumlah
            total_lunas += lunas
            total_foto += foto
            tanda = self.style.ERROR(" ← ADA KARTU LUNAS") if lunas else ""
            self.stdout.write(
                f"  {template.slug:<24} {jumlah} kartu ({lunas} lunas), {foto} foto{tanda}"
            )

        if not options["konfirmasi"]:
            self.stdout.write("")
            self.stdout.write(
                f"Akan menghapus {total_kartu} kartu ({total_lunas} lunas) "
                f"dan {total_foto} foto."
            )
            if total_lunas:
                self.stdout.write(
                    self.style.ERROR(
                        "Ada kartu LUNAS di antaranya — link yang sudah dibagikan "
                        "pemiliknya akan mati. Pastikan itu memang kartu ujimu."
                    )
                )
            self.stdout.write("Jalankan ulang dengan --konfirmasi untuk menghapus.")
            return

        with transaction.atomic():
            # Kartu lebih dulu: Template dilindungi on_delete=PROTECT, dan
            # berkas fotonya ikut terhapus lewat signal post_delete.
            GiftCard.objects.filter(template__in=templates).delete()
            jumlah_template, _ = templates.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Terhapus: {jumlah_template} template, {total_kartu} kartu, "
                f"{total_foto} foto."
            )
        )
