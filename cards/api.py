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

    Selalu buat order_id baru per percobaan (Midtrans menolak yang dipakai ulang),
    tapi kalau QR yang lama masih hidup, minta user memakai yang itu.
    """
    card = get_object_or_404(GiftCard, pk=card_id)
    if not _owns(request, card):
        return Response({"detail": "Kartu ini bukan milik sesi ini."}, status=403)
    if card.is_paid:
        return Response({"status": "paid", "redirect": card.public_url()})

    if card.status == GiftCard.Status.PENDING and not card.qr_is_expired:
        return Response(
            {"detail": "QR sebelumnya masih berlaku.", "reuse": True}, status=409
        )

    try:
        charge = services.start_payment(card)
    except MidtransError as exc:
        return Response({"detail": str(exc)}, status=502)

    card.refresh_from_db()
    return Response(
        {
            "status": card.status,
            "order_id": charge.order_id,
            "qr_string": charge.qr_string,
            "qr_image_url": charge.qr_image_url,
            "amount": card.amount,
            "expires_at": card.qr_expires_at,
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
