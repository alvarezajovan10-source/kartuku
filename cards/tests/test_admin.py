"""Admin dipakai untuk menolong pelanggan, jadi pencariannya harus menemukan
apa yang benar-benar mereka kirim.

Pelanggan yang minta bantuan menyebut potongan link kartunya ("kartuku.../
untuk-nadia") atau nama di kartunya. Mereka tidak memegang UUID maupun nomor
gateway. Sebelumnya `slug` dan `sender_name` tidak ada di `search_fields`,
sehingga justru di kasus tersulit pencariannya buntu.
"""

from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from cards.models import CardType, GiftCard, Template


class PencarianKartuAdminTests(TestCase):
    def setUp(self):
        template = Template.objects.create(
            slug="t", name="T", category=CardType.BIRTHDAY
        )
        self.target = GiftCard.objects.create(
            template=template, category=CardType.BIRTHDAY,
            sender_name="Raka", recipient_name="Nadia", slug="untuk-nadia",
        )
        # Pengecoh: harus TIDAK ikut terjaring.
        GiftCard.objects.create(
            template=template, category=CardType.BIRTHDAY,
            sender_name="Budi", recipient_name="Siti", slug="buat-siti",
        )
        self.admin = site._registry[GiftCard]
        self.request = RequestFactory().get("/")
        self.request.user = get_user_model()(is_staff=True, is_superuser=True)

    def cari(self, kata):
        qs, _ = self.admin.get_search_results(
            self.request, GiftCard.objects.all(), kata
        )
        return list(qs)

    def test_ketemu_lewat_slug(self):
        self.assertEqual(self.cari("untuk-nadia"), [self.target])

    def test_ketemu_lewat_potongan_slug(self):
        """Pelanggan sering menempel seluruh link, bukan slug-nya saja."""
        self.assertEqual(self.cari("nadia"), [self.target])

    def test_ketemu_lewat_nama_pengirim(self):
        self.assertEqual(self.cari("Raka"), [self.target])

    def test_ketemu_lewat_nama_penerima(self):
        self.assertEqual(self.cari("Nadia"), [self.target])

    def test_kata_asing_tidak_menjaring_apa_pun(self):
        self.assertEqual(self.cari("zzzzzz"), [])
