import json
from uuid import uuid4

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from cards.models import CardType, GiftCard, Template
from payments import midtrans, services
from payments.models import PaymentEvent

SERVER_KEY = "SB-Mid-server-TESTKEY"


def signed_payload(order_id, transaction_status, txn_id="txn-1", gross="15000.00", **extra):
    status_code = "200"
    payload = {
        "order_id": order_id,
        "status_code": status_code,
        "gross_amount": gross,
        "transaction_id": txn_id,
        "transaction_status": transaction_status,
        "payment_type": "qris",
    }
    payload.update(extra)
    payload["signature_key"] = midtrans.compute_signature(order_id, status_code, gross)
    return payload


@override_settings(MIDTRANS_SERVER_KEY=SERVER_KEY)
class WebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("midtrans_webhook")
        self.template = Template.objects.create(
            slug="t", name="T", category=CardType.BIRTHDAY
        )
        self.card = GiftCard.objects.create(
            template=self.template,
            category=CardType.BIRTHDAY,
            status=GiftCard.Status.PENDING,
            gateway_order_id="CARD-abc-1",
        )

    def post(self, payload):
        return self.client.post(
            self.url, data=json.dumps(payload), content_type="application/json"
        )

    def test_settlement_marks_card_paid(self):
        response = self.post(signed_payload("CARD-abc-1", "settlement"))
        self.assertEqual(response.status_code, 200)
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PAID)
        self.assertIsNotNone(self.card.paid_at)
        self.assertEqual(self.card.gateway_txn_id, "txn-1")

    def test_bad_signature_rejected_and_card_untouched(self):
        payload = signed_payload("CARD-abc-1", "settlement")
        payload["signature_key"] = "palsu"
        response = self.post(payload)
        self.assertEqual(response.status_code, 403)
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PENDING)
        self.assertEqual(PaymentEvent.objects.count(), 0)

    def test_duplicate_webhook_processed_once(self):
        payload = signed_payload("CARD-abc-1", "settlement")
        self.post(payload)
        self.card.refresh_from_db()
        first_paid_at = self.card.paid_at

        response = self.post(payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PaymentEvent.objects.count(), 1)
        self.card.refresh_from_db()
        self.assertEqual(self.card.paid_at, first_paid_at)

    def test_expire_marks_expired(self):
        self.post(signed_payload("CARD-abc-1", "expire", txn_id="txn-2"))
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.EXPIRED)

    def test_expire_after_paid_does_not_downgrade(self):
        self.post(signed_payload("CARD-abc-1", "settlement"))
        self.post(signed_payload("CARD-abc-1", "expire", txn_id="txn-9"))
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PAID)

    def test_wrong_amount_does_not_mark_paid(self):
        self.post(signed_payload("CARD-abc-1", "settlement", gross="1000.00"))
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PENDING)

    def test_capture_with_fraud_challenge_not_paid(self):
        self.post(
            signed_payload("CARD-abc-1", "capture", fraud_status="challenge")
        )
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PENDING)

    def test_unknown_order_id_returns_200(self):
        response = self.post(signed_payload("CARD-tidak-ada", "settlement"))
        self.assertEqual(response.status_code, 200)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_malformed_json_returns_400(self):
        response = self.client.post(
            self.url, data="bukan json", content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)


@override_settings(MIDTRANS_SERVER_KEY=SERVER_KEY)
class SignatureTests(TestCase):
    def test_signature_matches_midtrans_formula(self):
        import hashlib

        expected = hashlib.sha512(
            f"order-1{'200'}{'15000.00'}{SERVER_KEY}".encode()
        ).hexdigest()
        self.assertEqual(
            midtrans.compute_signature("order-1", "200", "15000.00"), expected
        )

    def test_verify_signature_rejects_missing_key(self):
        self.assertFalse(midtrans.verify_signature({"order_id": "x"}))


class UnconfiguredServerKeyTests(TestCase):
    """Tanpa MIDTRANS_SERVER_KEY, webhook harus DITOLAK — bukan diloloskan.

    Signature-nya cuma SHA512 dari tiga nilai yang semuanya ada di payload,
    jadi siapa pun bisa menghitungnya dan mengaku sudah bayar. Deploy yang
    kelupaan mengisi key tidak boleh berarti kartu gratis untuk semua orang.
    """

    def setUp(self):
        self.template = Template.objects.create(
            slug="t3", name="T3", category=CardType.BIRTHDAY
        )
        self.card = GiftCard.objects.create(
            template=self.template,
            category=CardType.BIRTHDAY,
            status=GiftCard.Status.PENDING,
            gateway_order_id="CARD-nokey-1",
        )

    @override_settings(MIDTRANS_SERVER_KEY="")
    def test_forged_settlement_rejected_when_key_missing(self):
        payload = signed_payload("CARD-nokey-1", "settlement")
        response = self.client.post(
            reverse("midtrans_webhook"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PENDING)
        self.assertIsNone(self.card.paid_at)


class OrderIdTests(TestCase):
    def test_order_id_unique_per_attempt(self):
        template = Template.objects.create(
            slug="t2", name="T2", category=CardType.BIRTHDAY
        )
        card = GiftCard.objects.create(
            id=uuid4(), template=template, category=CardType.BIRTHDAY
        )
        first = services.build_order_id(card)
        self.assertTrue(first.startswith("CARD-"))
        self.assertLessEqual(len(first), 64)
