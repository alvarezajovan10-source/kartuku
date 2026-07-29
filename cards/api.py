from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from payments import services
from payments.midtrans import MidtransError

from .models import GiftCard
from .views import OWNED_CARDS_KEY


class PayThrottle(AnonRateThrottle):
    scope = "pay"


class StatusThrottle(AnonRateThrottle):
    scope = "status"


def _owns(request, card):
    return str(card.id) in request.session.get(OWNED_CARDS_KEY, [])


@api_view(["POST"])
@throttle_classes([PayThrottle])
def create_charge(request, card_id):
    """POST /api/cards/<uuid>/pay/ → data QRIS.

    Order_id baru dibuat per percobaan (Midtrans menolak yang dipakai ulang).
    Kalau QR sebelumnya masih hidup, yang ITU yang dikirim balik — bukan error.
    Dulu jalur ini membalas 409, jadi user yang me-refresh halaman bayar tidak
    bisa melihat QR apa pun sampai yang lama kedaluwarsa (±15 menit).
    """
    card = get_object_or_404(GiftCard, pk=card_id)
    if not _owns(request, card):
        return Response({"detail": "Kartu ini bukan milik sesi ini."}, status=403)
    if card.is_paid:
        return Response({"status": "paid", "redirect": card.public_url()})

    if card.qr_is_live:
        return _charge_payload(card, card.gateway_order_id, reused=True)

    try:
        charge = services.start_payment(card)
    except MidtransError as exc:
        return Response({"detail": str(exc)}, status=502)

    card.refresh_from_db()
    return _charge_payload(card, charge.order_id)


def _charge_payload(card, order_id, reused=False):
    """Bentuk balasan yang sama untuk QR baru maupun QR yang dipakai ulang."""
    return Response(
        {
            "status": card.status,
            "order_id": order_id,
            "qr_string": card.qr_string,
            "qr_image_url": card.qr_image_url,
            "amount": card.amount,
            "expires_at": card.qr_expires_at,
            "reused": reused,
        }
    )


@api_view(["GET"])
@throttle_classes([StatusThrottle])
def card_status(request, card_id):
    """GET /api/cards/<uuid>/status/ → status dari DB (sumber kebenaran)."""
    card = get_object_or_404(GiftCard, pk=card_id)

    status = card.status
    # Tampilkan expired kalau QR lewat waktu walau webhook `expire` belum tiba.
    if (
        status == GiftCard.Status.PENDING
        and card.qr_expires_at
        and timezone.now() >= card.qr_expires_at
    ):
        status = GiftCard.Status.EXPIRED

    payload = {"status": status}
    if card.is_paid:
        payload["redirect"] = card.public_url()
    return Response(payload)
