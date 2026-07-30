"""Halaman pembeli tidak boleh membocorkan hal internal.

Tiga kebocoran nyata pernah tayang di situs live:

1. `{# ... #}` yang ditulis lebih dari satu baris. Sintaks itu hanya berlaku
   satu baris, jadi sisanya tercetak apa adanya — catatan TODO sempat terbaca
   pengunjung di halaman Testimoni.
2. Galeri kategori kosong menampilkan "Tambahkan lewat admin" lengkap dengan
   tautan ke /admin/ — instruksi untuk developer, dibaca calon pembeli.
3. Kategori yang templatenya belum jadi tampil seperti siap dipakai, membawa
   pembeli ke galeri kosong.
"""

from django.test import TestCase
from django.urls import reverse

from cards.models import CardType, Template

HALAMAN = ["landing", "page_templates", "page_how", "page_pricing",
           "page_faq", "page_testimonials"]


class KebocoranTemplateTests(TestCase):
    def setUp(self):
        Template.objects.create(
            slug="uji-ulang-tahun", name="Uji", category=CardType.BIRTHDAY,
            is_active=True,
        )

    def _semua_halaman(self):
        for nama in HALAMAN:
            yield nama, self.client.get(reverse(f"cards:{nama}")).content.decode()
        for kategori, _ in CardType.choices:
            yield (f"gallery:{kategori}",
                   self.client.get(reverse("cards:gallery", args=[kategori])).content.decode())

    def test_tidak_ada_komentar_django_yang_bocor(self):
        for nama, isi in self._semua_halaman():
            with self.subTest(halaman=nama):
                self.assertNotIn("{#", isi)
                self.assertNotIn("{%", isi)

    def test_tidak_menautkan_ke_admin(self):
        for nama, isi in self._semua_halaman():
            with self.subTest(halaman=nama):
                self.assertNotIn("/admin/", isi)

    def test_tidak_ada_catatan_pengembang(self):
        for nama, isi in self._semua_halaman():
            with self.subTest(halaman=nama):
                self.assertNotIn("TODO", isi)


class KategoriBelumJadiTests(TestCase):
    """Hanya Birthday yang punya template; sisanya harus jelas belum siap."""

    def setUp(self):
        Template.objects.create(
            slug="uji-ulang-tahun", name="Uji", category=CardType.BIRTHDAY,
            is_active=True,
        )

    def test_kategori_tanpa_template_ditandai_coming_soon(self):
        isi = self.client.get(reverse("cards:landing")).content.decode()
        self.assertIn("Coming soon", isi)
        # Kategorinya tetap terlihat — bukan disembunyikan diam-diam.
        self.assertIn("Anniversary", isi)

    def test_kategori_belum_jadi_tidak_bisa_diklik(self):
        isi = self.client.get(reverse("cards:landing")).content.decode()
        for kategori in [CardType.ANNIVERSARY, CardType.LOVE_STORY, CardType.PROPOSAL]:
            with self.subTest(kategori=kategori):
                self.assertNotIn(reverse("cards:gallery", args=[kategori]), isi)

    def test_kategori_yang_siap_tetap_bisa_diklik(self):
        isi = self.client.get(reverse("cards:landing")).content.decode()
        self.assertIn(reverse("cards:gallery", args=[CardType.BIRTHDAY]), isi)

    def test_galeri_kosong_menawarkan_jalan_keluar(self):
        """Pembeli yang tersesat ke kategori kosong harus diarahkan, bukan buntu."""
        isi = self.client.get(
            reverse("cards:gallery", args=[CardType.PROPOSAL])
        ).content.decode()
        self.assertIn("Coming soon", isi)
        self.assertIn(reverse("cards:gallery", args=[CardType.BIRTHDAY]), isi)
