"""Logika pembayaran. View & webhook handler hanya memanggil fungsi di sini."""

import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from cards.models import GiftCard

from . import midtrans
from .models import PaymentEvent

logger = logging.getLogger(__name__)

# Status Midtrans → status kartu kita.
PAID_STATUSES = {"settlement", "capture"}
FAILED_STATUSES = {"expire", "cancel", "deny", "failure"}


def build_order_id(card: GiftCard) -> str:
    """Unik per percobaan bayar — Midtrans menolak order_id yang dipakai ulang."""
    return f"CARD-{str(card.id)[:8]}-{int(timezone.now().timestamp())}"


def start_payment(card: GiftCard) -> midtrans.QrisCharge:
    """Buat charge QRIS baru untuk kartu. Kartu jadi `pending`.

    order_id disimpan SEBELUM memanggil Midtrans, karena webhook kadang tiba
    sebelum respons charge selesai diproses.
    """
    if card.is_paid:
        raise midtrans.MidtransError("Kartu ini sudah dibayar.")

    order_id = build_order_id(card)
    expires_at = timezone.now() + timedelta(minutes=settings.QR_TTL_MINUTES)

    GiftCard.objects.filter(pk=card.pk).update(
        gateway_order_id=order_id,
        status=GiftCard.Status.PENDING,
        qr_expires_at=expires_at,
        amount=settings.CARD_PRICE,
    )
    card.refresh_from_db()

    try:
        charge = midtrans.create_qris_charge(
            order_id=order_id,
            gross_amount=settings.CARD_PRICE,
            expiry_minutes=settings.QR_TTL_MINUTES,
        )
    except midtrans.MidtransError:
        # Charge gagal → kembalikan ke draft supaya user bisa coba lagi bersih.
        GiftCard.objects.filter(pk=card.pk, status=GiftCard.Status.PENDING).update(
            status=GiftCard.Status.DRAFT, gateway_order_id="", qr_expires_at=None
        )
        raise

    if charge.transaction_id:
        GiftCard.objects.filter(pk=card.pk).update(gateway_txn_id=charge.transaction_id)
        card.refresh_from_db()

    return charge


def _amount_matches(card: GiftCard, gross_amount) -> bool:
    """Midtrans mengirim gross_amount sebagai string seperti "15000.00"."""
    try:
        return Decimal(str(gross_amount)) == Decimal(card.amount)
    except (InvalidOperation, TypeError):
        return False


def process_notification(payload: dict) -> str:
    """Proses satu notifikasi webhook yang SUDAH lolos verifikasi signature.

    Kembalikan string keterangan singkat untuk logging. Selalu selesai tanpa
    exception untuk kondisi yang sudah diantisipasi — caller membalas 200 supaya
    Midtrans berhenti retry.
    """
    order_id = str(payload.get("order_id", ""))
    txn_id = str(payload.get("transaction_id", ""))
    txn_status = str(payload.get("transaction_status", ""))
    fraud_status = str(payload.get("fraud_status", ""))

    card = GiftCard.objects.filter(gateway_order_id=order_id).first()
    if card is None:
        logger.warning("Webhook untuk order_id tak dikenal: %s", order_id)
        return "kartu tidak ditemukan"

    with transaction.atomic():
        try:
            PaymentEvent.objects.create(
                card=card,
                gateway_txn_id=txn_id,
                transaction_status=txn_status,
                raw_payload=payload,
            )
        except IntegrityError:
            # (txn_id, status) sudah pernah masuk → duplikat, jangan proses lagi.
            logger.info("Webhook duplikat diabaikan: %s/%s", txn_id, txn_status)
            return "duplikat"

        # Kunci baris kartu supaya dua webhook bersamaan tidak saling menimpa.
        card = GiftCard.objects.select_for_update().get(pk=card.pk)

        if txn_status in PAID_STATUSES:
            if txn_status == "capture" and fraud_status not in {"accept", ""}:
                logger.warning("Capture dengan fraud_status=%s ditahan", fraud_status)
                return f"fraud_status {fraud_status}"
            if not _amount_matches(card, payload.get("gross_amount")):
                logger.error(
                    "Nominal tidak cocok untuk %s: %s vs %s",
                    order_id,
                    payload.get("gross_amount"),
                    card.amount,
                )
                return "nominal tidak cocok"
            if not card.is_paid:
                card.status = GiftCard.Status.PAID
                card.paid_at = timezone.now()
                card.gateway_txn_id = txn_id
                card.save(update_fields=["status", "paid_at", "gateway_txn_id", "updated_at"])
            return "paid"

        if txn_status in FAILED_STATUSES:
            # Kartu yang sudah lunas tidak boleh diturunkan lagi statusnya.
            if not card.is_paid:
                card.status = GiftCard.Status.EXPIRED
                card.save(update_fields=["status", "updated_at"])
            return "expired"

        return f"diabaikan ({txn_status})"
