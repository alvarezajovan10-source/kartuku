"""Tes alur create-charge QRIS.

Ada karena bug nyata: halaman bayar yang dimuat ulang membalas 409 ("QR
sebelumnya masih berlaku") dan TIDAK menampilkan QR apa pun, sehingga pembeli
tidak bisa membayar sampai QR lama kedaluwarsa (±15 menit). Midtrans menolak
order_id yang dipakai ulang, jadi jalan keluarnya adalah menyimpan QR-nya dan
menyajikannya kembali.

Midtrans dipalsukan di sini — tes tidak boleh menyentuh jaringan.
"""

from datetime import timedelta
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from cards.models import CardType, GiftCard, Template
from payments import midtrans


def fake_charge(order_id="CARD-abc-1", txn="txn-1"):
    return midtrans.QrisCharge(
        order_id=order_id,
        transaction_id=txn,
        transaction_status="pending",
        qr_string="00020101021226",
        qr_image_url="https://api.sandbox.midtrans.com/v2/qris/abc/qr-code",
        expiry_time="2026-07-28 12:00:00",
        raw={},
    )


class CreateChargeTests(TestCase):
    def setUp(self):
        self.template = Template.objects.create(
            slug="klasik", name="Klasik", category=CardType.BIRTHDAY
        )
        # Draft dibuat lewat editor supaya sesi menandai kepemilikannya.
        self.client.post(
            reverse("cards:editor", args=["klasik"]),
            {"sender_name": "Jepa", "recipient_name": "Rara", "message": "halo"},
        )
        self.card = GiftCard.objects.get()
        self.url = reverse("cards:api_pay", args=[self.card.id])

    def test_charge_stores_qr_so_it_can_be_shown_again(self):
        with patch.object(midtrans, "create_qris_charge", return_value=fake_charge()):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "pending")
        self.assertTrue(body["qr_image_url"])
        self.assertFalse(body["reused"])

        card = GiftCard.objects.get(pk=self.card.pk)
        self.assertEqual(card.status, GiftCard.Status.PENDING)
        self.assertEqual(card.qr_string, "00020101021226")
        self.assertTrue(card.qr_image_url)
        self.assertEqual(card.gateway_txn_id, "txn-1")

    def test_reload_returns_the_same_live_qr_instead_of_an_error(self):
        """Inti bugnya: dulu ini 409 dan pembeli terkunci ±15 menit."""
        with patch.object(midtrans, "create_qris_charge", return_value=fake_charge()):
            first = self.client.post(self.url)

        # Midtrans TIDAK boleh dipanggil lagi — order_id lama masih hidup.
        with patch.object(midtrans, "create_qris_charge") as charge_again:
            second = self.client.post(self.url)
        charge_again.assert_not_called()

        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json()["reused"])
        self.assertEqual(
            second.json()["qr_image_url"], first.json()["qr_image_url"]
        )

    def test_expired_qr_gets_a_brand_new_order_id(self):
        with patch.object(midtrans, "create_qris_charge", return_value=fake_charge()):
            first = self.client.post(self.url)

        GiftCard.objects.filter(pk=self.card.pk).update(
            qr_expires_at=timezone.now() - timedelta(minutes=1)
        )

        second_charge = fake_charge(order_id="CARD-abc-2", txn="txn-2")
        with patch.object(
            midtrans, "create_qris_charge", return_value=second_charge
        ) as charge_again:
            second = self.client.post(self.url)
        charge_again.assert_called_once()

        self.assertEqual(second.status_code, 200)
        self.assertFalse(second.json()["reused"])
        self.assertNotEqual(second.json()["order_id"], first.json()["order_id"])

    def test_failed_charge_returns_card_to_draft_and_clears_qr(self):
        with patch.object(
            midtrans,
            "create_qris_charge",
            side_effect=midtrans.MidtransError("Midtrans menolak permintaan."),
        ):
            response = self.client.post(self.url)

        self.assertEqual(response.status_code, 502)
        card = GiftCard.objects.get(pk=self.card.pk)
        self.assertEqual(card.status, GiftCard.Status.DRAFT)
        self.assertEqual(card.gateway_order_id, "")
        self.assertEqual(card.qr_string, "")
        self.assertEqual(card.qr_image_url, "")

    def test_paid_card_redirects_instead_of_charging_again(self):
        GiftCard.objects.filter(pk=self.card.pk).update(status=GiftCard.Status.PAID)
        with patch.object(midtrans, "create_qris_charge") as charge:
            response = self.client.post(self.url)
        charge.assert_not_called()
        self.assertEqual(response.json()["status"], "paid")
        self.assertIn("redirect", response.json())

    def test_stranger_cannot_start_a_payment(self):
        stranger = Client()
        with patch.object(midtrans, "create_qris_charge") as charge:
            response = stranger.post(self.url)
        charge.assert_not_called()
        self.assertEqual(response.status_code, 403)
