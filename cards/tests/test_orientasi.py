"""Ajakan memutar HP untuk kartu MENDATAR.

Yang dijaga di sini satu bug yang SUDAH TAYANG sebelum ketahuan.

Gerbang Game 8-Bit cuma memakai `@media (orientation: portrait)`. Halaman
produk menyematkan kartu contoh di iframe berukuran 678x848 — tegak, tapi itu
bukan HP penerima. Akibatnya halaman jualan menampilkan "MIRINGKAN HP-MU"
menutupi kartu contohnya, tepat di halaman yang paling menjual, dan tidak ada
yang menyadarinya karena di HP maupun di laptop halaman KARTU-nya benar.

Penjaganya harus di JS, bukan di template: kartunya bisa disematkan di halaman
mana pun, termasuk yang belum ada.
"""

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from cards.management.commands.seed_templates import SEEDS
from cards.models import CardType, GiftCard, Template


def berkas(jalur):
    with open(settings.BASE_DIR / jalur) as fh:
        return fh.read()


class PenjagaIframeTests(TestCase):
    """Kedua kartu mendatar harus punya penjaga yang sama."""

    def test_gerbang_bersama_menjaga_iframe(self):
        isi = berkas("cards/templates/cards/_orientasi.html")
        self.assertIn("window.self !== window.top", isi)
        self.assertIn("pergi", isi)

    def test_game8bit_ikut_dijaga(self):
        """Template inilah yang bug-nya tayang."""
        isi = berkas("static/js/render/game8bit.js")
        self.assertIn("window.self !== window.top", isi)

    def test_gerbang_di_atas_semua_perkakas(self):
        """Tombol lagu duduk di z-index 80. Gerbang di bawah itu ditembus, dan
        penerima melihat tombol mengambang di atas layar yang menyuruhnya
        memutar HP."""
        import re

        orientasi = berkas("static/css/orientasi.css")
        m = re.search(r"z-index:\s*(\d+)", orientasi)
        self.assertTrue(m, "z-index gerbang tidak terbaca")
        gerbang = int(m.group(1))
        tertinggi = max(int(z) for z in re.findall(r"z-index:\s*(\d+)",
                        berkas("static/css/bgm.css") + berkas("static/css/fullscreen.css")
                        + berkas("static/css/watermark.css")))
        self.assertGreater(gerbang, tertinggi,
                           f"gerbang {gerbang} tidak di atas perkakas tertinggi {tertinggi}")


class SweetflixMemakaiGerbangTests(TestCase):
    def setUp(self):
        config = next(c for s, _n, _k, c in SEEDS if s == "sweetflix")
        self.template = Template.objects.create(
            slug="sweetflix", name="Sweetflix", category=CardType.LOVE_STORY, config=config)
        self.kartu = GiftCard.objects.create(
            template=self.template, category=CardType.LOVE_STORY,
            status=GiftCard.Status.PAID, paid_at=timezone.now(),
            recipient_name="Riana", sender_name="Rocky")

    def test_kartu_terbit_memuat_gerbang_dan_tombol_layar_penuh(self):
        isi = self.client.get(f"/{self.kartu.id}/").content.decode()
        self.assertIn('id="putarLayar"', isi)
        self.assertIn('id="fsFab"', isi)      # tombol layar penuh, kiri bawah
