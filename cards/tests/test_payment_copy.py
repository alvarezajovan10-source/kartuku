"""Teks pembayaran harus mengikuti metode yang benar-benar aktif.

Selama MIDTRANS_SERVER_KEY kosong, tidak ada QRIS di situs ini — pembeli
membeli di Lynk.id lalu menempel REF ID. Halaman yang menjanjikan "scan QRIS"
membuat pembeli menunggu QR yang tidak akan pernah muncul, dan itu berakhir di
DM-mu, bukan di penjualan.

Test ini menjaga dua arah sekaligus: janji QRIS hilang saat Midtrans mati, dan
kembali sendiri saat dinyalakan.
"""

from django.test import TestCase, override_settings
from django.urls import reverse

HALAMAN_PEMBELI = ["landing", "page_how", "page_pricing", "page_faq", "page_templates"]


@override_settings(MIDTRANS_SERVER_KEY="")
class TanpaMidtransTests(TestCase):
    """Keadaan produksi sekarang: pembayaran ditangani Lynk.id."""

    def test_tidak_menjanjikan_scan_qris(self):
        for nama in HALAMAN_PEMBELI:
            with self.subTest(halaman=nama):
                isi = self.client.get(reverse(f"cards:{nama}")).content.decode()
                self.assertNotIn("Scan dengan e-wallet", isi)
                self.assertNotIn("Bayar mudah dengan QRIS", isi)
                self.assertNotIn("QRIS terverifikasi", isi)

    def test_menyebut_lynk_sebagai_tempat_bayar(self):
        for nama in ["page_how", "page_pricing", "page_faq"]:
            with self.subTest(halaman=nama):
                isi = self.client.get(reverse(f"cards:{nama}")).content.decode()
                self.assertIn("Lynk.id", isi)

    def test_footer_tidak_menyebut_midtrans(self):
        """Midtrans tidak memproses apa pun sekarang — menyebutnya menyesatkan."""
        isi = self.client.get(reverse("cards:landing")).content.decode()
        self.assertNotIn("Midtrans", isi)

    def test_harga_pakai_pemisah_ribuan(self):
        """"Rp15000" terlihat seperti situs setengah jadi."""
        isi = self.client.get(reverse("cards:page_pricing")).content.decode()
        self.assertIn("15.000", isi)
        self.assertNotIn("15000", isi)


@override_settings(MIDTRANS_SERVER_KEY="SB-Mid-server-contoh")
class DenganMidtransTests(TestCase):
    """Kalau QRIS dinyalakan, kalimatnya harus balik sendiri tanpa sunting ulang."""

    def test_janji_qris_kembali(self):
        isi = self.client.get(reverse("cards:page_how")).content.decode()
        self.assertIn("Scan dengan e-wallet", isi)
        self.assertNotIn("Pembelian lewat Lynk.id", isi)

    def test_footer_menyebut_midtrans_lagi(self):
        isi = self.client.get(reverse("cards:landing")).content.decode()
        self.assertIn("Midtrans", isi)
