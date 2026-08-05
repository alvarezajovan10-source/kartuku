"""Pratinjau link saat dibagikan.

Sebagian besar pembeli datang dari link yang diteruskan teman, bukan dari bio
TikTok — dan penerima kartu SELALU menerimanya lewat WhatsApp/DM. Tanpa tag
Open Graph yang sampai cuma URL telanjang, dan kejutan yang sudah dibayar
pembeli jatuh sebelum kartunya dibuka.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cards.models import CardType, GiftCard, Template


class PratinjauHalamanJualanTests(TestCase):
    def test_halaman_depan_punya_kartu_pratinjau(self):
        isi = self.client.get(reverse("cards:landing")).content.decode()
        for tag in ['property="og:title"', 'property="og:description"',
                    'property="og:image"', 'name="twitter:card"']:
            with self.subTest(tag=tag):
                self.assertIn(tag, isi)

    def test_url_gambar_mutlak(self):
        """Pengambil pratinjau memuatnya dari servernya sendiri — jalur relatif
        tidak akan ketemu, dan pratinjaunya muncul tanpa gambar."""
        isi = self.client.get(reverse("cards:landing")).content.decode()
        awal = isi.index('property="og:image" content="') + len('property="og:image" content="')
        self.assertTrue(isi[awal:awal + 60].startswith("http"))

    def test_favicon_tidak_jatuh_ke_pencarian_kartu(self):
        """Tanpa rute sendiri, /favicon.ico disambar rute tangkap-semua
        `<str:ref>` dan dicari sebagai slug kartu — query sia-sia tiap
        kunjungan, lalu 404."""
        response = self.client.get("/favicon.ico")
        self.assertEqual(response.status_code, 301)
        self.assertIn("favicon.ico", response["Location"])
        self.assertNotEqual(response["Location"], "/favicon.ico/")


class PratinjauKartuTests(TestCase):
    def setUp(self):
        # `config` wajib menyebut renderer. Tanpa itu `_render_card` jatuh ke
        # cards/public.html, dan yang teruji bukan renderer sungguhan.
        template = Template.objects.create(
            slug="klasik-ulang-tahun", name="Klasik", category=CardType.BIRTHDAY,
            config={"renderer": "birthday"},
        )
        self.card = GiftCard.objects.create(
            template=template, category=CardType.BIRTHDAY,
            sender_name="Raka", recipient_name="Nadia",
            status=GiftCard.Status.PAID, paid_at=timezone.now(),
        )

    def isi(self):
        return self.client.get(f"/{self.card.id}/").content.decode()

    def test_judul_menyebut_penerima(self):
        self.assertIn("Ada kartu untuk Nadia", self.isi())

    def test_keterangan_menyebut_pengirim(self):
        self.assertIn("Dari Raka", self.isi())

    def test_kartu_tanpa_nama_tetap_punya_pratinjau_wajar(self):
        self.card.recipient_name = ""
        self.card.sender_name = ""
        self.card.save(update_fields=["recipient_name", "sender_name"])
        isi = self.isi()
        self.assertIn("Ada kartu untuk kamu", isi)
        self.assertIn("Sebuah kartu ucapan digital", isi)

    def test_pratinjau_tidak_memakai_foto_pembeli(self):
        """Keputusan privasi yang disengaja.

        Foto di dalam kartu milik pembeli dan pasangannya. Menaruhnya di
        og:image berarti server WhatsApp/Instagram/Facebook ikut mengambil dan
        menyimpannya, dan kalau linknya diteruskan ke grup, fotonya terpampang
        di daftar chat semua orang. Nama penerima sudah cukup personal.
        """
        isi = self.isi()
        awal = isi.index('property="og:image" content="') + len('property="og:image" content="')
        gambar = isi[awal:isi.index('"', awal)]
        self.assertIn("og-default", gambar)
        self.assertNotIn("/media/", gambar)

    def test_halaman_kartu_tetap_tidak_diindeks(self):
        """Pratinjau saat dibagikan tidak sama dengan muncul di Google."""
        self.assertIn('content="noindex, nofollow"', self.isi())

    def test_template_cadangan_juga_dapat_pratinjau_personal(self):
        """Template tanpa `renderer` di config jatuh ke cards/public.html.

        Jalur itu memakai base.html, jadi tanpa penanganan khusus penerima
        kartunya menerima pratinjau iklan halaman depan — bukan kartunya.
        """
        self.card.template.config = {}
        self.card.template.save(update_fields=["config"])
        self.assertIn("Ada kartu untuk Nadia", self.isi())
