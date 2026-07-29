"""Tes webhook Lynk.id + penukaran REF ID.

Payload di sini disalin dari dokumentasi resmi Lynk (event `payment.received`),
supaya bentuk yang diuji sama persis dengan yang akan datang sungguhan.
"""

import hashlib
import json

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from cards.models import AccessCode, CardType, GiftCard, Template
from payments.models import LynkOrder

KEY = "mk_live_KUNCIUJI"
REF = "13f8d23beeb2aacbbc01c94060cc88d7"
MSG = "API_CALL_1744270275143115_4624014"


def payload(ref=REF, message_id=MSG, total_price=15000, grand_total=12000,
            qty=1, event="payment.received", action="SUCCESS", email="user@lynk.id"):
    return {
        "event": event,
        "data": {
            "message_action": action,
            "message_code": "0",
            "message_data": {
                "createdAt": "2026-07-29T14:30:45",
                "customer": {"email": email, "name": "Lynk User", "phone": "08123"},
                "items": [{"price": total_price, "qty": qty, "title": "Kartu Ucapan",
                           "uuid": "abc-123", "addons": [], "stock": 1}],
                "refId": ref,
                "totals": {
                    "affiliate": 0, "convenienceFee": -3000, "discount": 0,
                    "grandTotal": grand_total, "totalAddon": 0, "totalItem": 1,
                    "totalPrice": total_price, "totalShipping": 0,
                },
                "voucherCode": "",
            },
            "message_desc": "",
            "message_id": message_id,
            "message_title": "",
        },
    }


def sign(body, key=KEY):
    """Rumus resmi Lynk: sha256(amount + refId + message_id + merchant_key)."""
    d = body["data"]
    amount = d["message_data"]["totals"]["grandTotal"]
    raw = f"{amount}{d['message_data']['refId']}{d['message_id']}{key}"
    return hashlib.sha256(raw.encode()).hexdigest()


@override_settings(LYNK_MERCHANT_KEY=KEY, LYNK_MIN_AMOUNT=15000)
class LynkWebhookTests(TestCase):
    def setUp(self):
        self.url = reverse("lynk_webhook")

    def post(self, body, signature=None):
        return self.client.post(
            self.url,
            data=json.dumps(body),
            content_type="application/json",
            headers={"X-Lynk-Signature": signature or sign(body)},
        )

    def test_pembayaran_sukses_tercatat_sebagai_hak_pakai(self):
        response = self.post(payload())
        self.assertEqual(response.status_code, 200)

        order = LynkOrder.objects.get()
        self.assertEqual(order.ref_id, REF)
        self.assertEqual(order.customer_email, "user@lynk.id")
        self.assertEqual(order.item_total, 15000)
        self.assertEqual(order.credits_total, 1)
        self.assertEqual(order.credits_used, 0)

    def test_tanda_tangan_palsu_ditolak(self):
        response = self.post(payload(), signature="palsu")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(LynkOrder.objects.exists())

    @override_settings(LYNK_MERCHANT_KEY="")
    def test_ditolak_saat_merchant_key_belum_diisi(self):
        """Tanpa kunci, tanda tangan bisa dihitung siapa pun yang baca payload."""
        body = payload()
        response = self.post(body, signature=sign(body, key=""))
        self.assertEqual(response.status_code, 403)
        self.assertFalse(LynkOrder.objects.exists())

    def test_pengiriman_ulang_tidak_menggandakan_kuota(self):
        self.post(payload())
        response = self.post(payload())  # Lynk mengulang
        self.assertEqual(response.status_code, 200)
        self.assertEqual(LynkOrder.objects.count(), 1)
        self.assertEqual(LynkOrder.objects.get().credits_total, 1)

    def test_nominal_kurang_ditolak(self):
        """Produk murah tidak boleh menghasilkan kartu penuh."""
        response = self.post(payload(total_price=1000, grand_total=800))
        self.assertEqual(response.status_code, 200)  # 200 supaya Lynk berhenti ulang
        self.assertFalse(LynkOrder.objects.exists())

    def test_grand_total_kecil_tetap_diterima(self):
        """grandTotal = yang DITERIMA penjual setelah potongan, jadi selalu
        lebih kecil dari harga jual. Memakainya untuk cek nominal akan menolak
        semua pembayaran sah — pastikan yang dipakai totalPrice."""
        response = self.post(payload(total_price=15000, grand_total=12000))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(LynkOrder.objects.filter(ref_id=REF).exists())

    def test_qty_dua_memberi_dua_kuota(self):
        self.post(payload(qty=2))
        self.assertEqual(LynkOrder.objects.get().credits_total, 2)

    def test_event_selain_pembayaran_diabaikan(self):
        response = self.post(payload(event="order.created"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(LynkOrder.objects.exists())

    def test_status_bukan_sukses_diabaikan(self):
        response = self.post(payload(action="PENDING"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(LynkOrder.objects.exists())

    def test_payload_bukan_json_ditolak(self):
        response = self.client.post(
            self.url, data="bukan json", content_type="application/json",
            headers={"X-Lynk-Signature": "x"},
        )
        self.assertEqual(response.status_code, 400)

    def test_get_ditolak(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)


@override_settings(LYNK_MERCHANT_KEY=KEY, LYNK_MIN_AMOUNT=15000)
class RedeemRefIdTests(TestCase):
    """Penukaran REF ID di halaman aktivasi."""

    def setUp(self):
        self.template = Template.objects.create(
            slug="klasik", name="Klasik", category=CardType.BIRTHDAY
        )
        self.client.post(
            reverse("cards:editor", args=["klasik"]),
            {"sender_name": "A", "recipient_name": "B", "message": "halo"},
        )
        self.card = GiftCard.objects.get()
        self.url = reverse("cards:redeem_code", args=[self.card.id])

    def bayar(self, **kwargs):
        body = payload(**kwargs)
        self.client.post(
            reverse("lynk_webhook"), data=json.dumps(body),
            content_type="application/json",
            headers={"X-Lynk-Signature": sign(body)},
        )

    def test_ref_id_dari_struk_mengaktifkan_kartu(self):
        self.bayar()
        self.client.post(self.url, {"code": REF})
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PAID)
        self.assertIsNotNone(self.card.paid_at)
        # Penjualan asli — bukan kartu gratis pemilik.
        self.assertFalse(self.card.comped)
        self.assertEqual(LynkOrder.objects.get().credits_used, 1)

    def test_ref_id_tersalin_dengan_spasi_dan_ganti_baris(self):
        """Di email struk, REF ID tercetak terpotong dua baris."""
        self.bayar()
        berantakan = f"  {REF[:24]}\n{REF[24:]}  ".upper()
        self.client.post(self.url, {"code": berantakan})
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PAID)

    def test_ref_id_tidak_bisa_dipakai_dua_kartu(self):
        self.bayar()
        self.client.post(self.url, {"code": REF})

        kartu2 = GiftCard.objects.create(
            template=self.template, category=CardType.BIRTHDAY
        )
        sesi = self.client.session
        sesi["owned_cards"] = sesi.get("owned_cards", []) + [str(kartu2.id)]
        sesi.save()
        self.client.post(reverse("cards:redeem_code", args=[kartu2.id]), {"code": REF})

        kartu2.refresh_from_db()
        self.assertEqual(kartu2.status, GiftCard.Status.DRAFT)

    def test_qty_dua_bisa_mengaktifkan_dua_kartu(self):
        self.bayar(qty=2)
        self.client.post(self.url, {"code": REF})

        kartu2 = GiftCard.objects.create(
            template=self.template, category=CardType.BIRTHDAY
        )
        sesi = self.client.session
        sesi["owned_cards"] = sesi.get("owned_cards", []) + [str(kartu2.id)]
        sesi.save()
        self.client.post(reverse("cards:redeem_code", args=[kartu2.id]), {"code": REF})

        kartu2.refresh_from_db()
        self.assertEqual(kartu2.status, GiftCard.Status.PAID)
        self.assertEqual(LynkOrder.objects.get().credits_used, 2)

    def test_ref_id_karangan_tidak_mengaktifkan(self):
        """Tanpa webhook lebih dulu, nomor apa pun tidak berlaku."""
        self.client.post(self.url, {"code": "a" * 32})
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.DRAFT)

    def test_kode_manual_masih_jalan_sebagai_cadangan(self):
        kode = AccessCode.objects.create(code=AccessCode.generate_code())
        self.client.post(self.url, {"code": kode.code})
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PAID)
        kode.refresh_from_db()
        self.assertTrue(kode.is_used)

    def test_percobaan_benar_tidak_ikut_dihitung_sebagai_gagal(self):
        """Pembeli yang kodenya benar tidak boleh terhukum oleh percobaannya."""
        self.bayar()
        self.client.post(self.url, {"code": REF})
        self.assertEqual(self.client.session.get("code_attempts", []), [])
