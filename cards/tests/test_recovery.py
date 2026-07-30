"""Pembeli yang kehilangan sesinya harus tetap bisa mengambil kartunya.

Sesi hanya menyimpan daftar UUID kartu di cookie. Cookie itu hilang kalau
pembeli ganti perangkat, memakai browser lain, membersihkan riwayat, atau
sekadar kembali setelah cookienya kedaluwarsa. Dulu halaman aktivasi menjawab
403 dalam semua keadaan itu — pembeli sudah membayar di Lynk, lalu terkunci dari
kartunya sendiri tanpa jalan keluar apa pun.

Yang menjaga sekarang bukan sesi, melainkan bukti bayarnya: REF ID hanya sah
kalau webhook Lynk sudah melaporkan pembayarannya, dan sekali pakai.

Batas yang TETAP dijaga: kartu yang sudah lunas. Link publik memakai UUID yang
sama dengan URL bayar (lihat `_card_by_ref`), jadi UUID kartu lunas sudah ada di
tangan penerima kartu — membuka halaman aktivasi untuk mereka berarti penerima
bisa merebut kartu pengirimnya.
"""

import hashlib
import json

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from cards.models import CardType, GiftCard, Template

KUNCI = "mk_live_KUNCIUJI"
REF = "13f8d23beeb2aacbbc01c94060cc88d7"


def payload_lynk(ref=REF, total=15000):
    return {
        "event": "payment.received",
        "data": {
            "message_action": "SUCCESS",
            "message_code": "0",
            "message_id": "API_CALL_UJI",
            "message_desc": "",
            "message_title": "",
            "message_data": {
                "createdAt": "2026-07-30T10:00:00",
                "customer": {"email": "pembeli@contoh.id", "name": "Pembeli", "phone": "08"},
                "items": [{"price": total, "qty": 1, "title": "Kartu", "uuid": "u",
                           "addons": [], "stock": 1}],
                "refId": ref,
                "totals": {"affiliate": 0, "convenienceFee": -3000, "discount": 0,
                           "grandTotal": total - 3000, "totalAddon": 0, "totalItem": 1,
                           "totalPrice": total, "totalShipping": 0},
                "voucherCode": "",
            },
        },
    }


@override_settings(LYNK_MERCHANT_KEY=KUNCI, LYNK_MIN_AMOUNT=15000)
class PemulihanKartuTests(TestCase):
    def setUp(self):
        self.template = Template.objects.create(
            slug="klasik", name="Klasik", category=CardType.BIRTHDAY
        )
        # Pembeli membuat kartunya di HP.
        self.hp = self.client
        self.hp.post(
            reverse("cards:editor", args=["klasik"]),
            {"sender_name": "A", "recipient_name": "B", "message": "halo"},
        )
        self.card = GiftCard.objects.get()
        self.bayar()

    def bayar(self, ref=REF, total=15000):
        """Webhook Lynk masuk — pembayarannya tercatat."""
        body = payload_lynk(ref, total)
        d = body["data"]
        mentah = (f"{d['message_data']['totals']['grandTotal']}"
                  f"{d['message_data']['refId']}{d['message_id']}{KUNCI}")
        self.client_class().post(
            reverse("lynk_webhook"), data=json.dumps(body),
            content_type="application/json",
            headers={"X-Lynk-Signature": hashlib.sha256(mentah.encode()).hexdigest()},
        )

    def test_laptop_bisa_mengaktifkan_kartu_yang_dibuat_di_hp(self):
        laptop = self.client_class()          # sesi kosong, tidak kenal kartu ini

        halaman = laptop.get(reverse("cards:pay", args=[self.card.id]))
        self.assertEqual(halaman.status_code, 200)

        laptop.post(reverse("cards:redeem_code", args=[self.card.id]), {"code": REF})
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PAID)
        self.assertIn(str(self.card.id), laptop.session.get("owned_cards", []))

    def test_ref_id_karangan_tetap_tidak_mengaktifkan(self):
        """Terbukanya halaman bukan berarti kartunya bisa diaktifkan gratis."""
        asing = self.client_class()
        asing.post(reverse("cards:redeem_code", args=[self.card.id]),
                   {"code": "f" * 32})
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.DRAFT)

    def test_penerima_kartu_tidak_bisa_merebut_kartu_lunas(self):
        self.hp.post(reverse("cards:redeem_code", args=[self.card.id]), {"code": REF})
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PAID)

        # Penerima membuka link publik, lalu mencoba URL bayar dengan UUID sama.
        penerima = self.client_class()
        self.assertRedirects(
            penerima.get(reverse("cards:pay", args=[self.card.id])),
            reverse("cards:success", args=[self.card.id]),
        )
        self.assertRedirects(
            penerima.post(reverse("cards:redeem_code", args=[self.card.id]),
                          {"code": REF}),
            reverse("cards:success", args=[self.card.id]),
        )
        self.assertNotIn(str(self.card.id), penerima.session.get("owned_cards", []))

    def test_menyunting_tetap_butuh_kepemilikan(self):
        """Halaman aktivasi terbuka, editor tidak.

        Editor tidak menjawab 403 melainkan memulai kartu kosong — pengunjung
        yang bukan pemilik tidak boleh melihat isi kartu orang.
        """
        asing = self.client_class()
        isi = asing.get(
            reverse("cards:editor", args=["klasik"]) + f"?card={self.card.id}"
        ).content.decode()
        self.assertNotIn("halo", isi)


class SesiTahanLamaTests(TestCase):
    def test_cookie_sesi_tidak_kedaluwarsa_dalam_hitungan_minggu(self):
        """Bawaan Django 2 minggu, dihitung sejak cookie dibuat.

        Kartu yang sudah dibayar berumur panjang — pembeli membukanya lagi
        berbulan-bulan kemudian untuk mengganti link atau menyunting.
        """
        self.assertGreaterEqual(settings.SESSION_COOKIE_AGE, 60 * 60 * 24 * 180)

    def test_sesi_disegarkan_tiap_kunjungan(self):
        """Tanpa ini umurnya dihitung sejak dibuat, bukan sejak kunjungan
        terakhir — pengunjung rutin pun tetap terputus di hari yang sama."""
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
