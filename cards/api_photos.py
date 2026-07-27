"""Endpoint editor: draft, unggah foto seketika, hapus foto.

Foto diunggah begitu dipilih (bukan menunggu tombol simpan) supaya pilihan user
tidak pernah hilang saat halaman dimuat ulang — browser tidak bisa mengisi ulang
input file, dan itulah akar masalah unggahan yang hilang.

Kepemilikan diperiksa lewat sesi: hanya browser yang membuat draft yang boleh
menambah atau menghapus fotonya.
"""

import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .forms import MAX_TEXT_KEYS, MAX_TEXT_LENGTH
from .models import GiftCard, GiftPhoto, Template
from .styles import sanitize_style
from .utils import parse_music_link, validate_and_compress_photo
from .views import OWNED_CARDS_KEY, _mark_owned, _owns

logger = logging.getLogger(__name__)


class UploadThrottle(AnonRateThrottle):
    scope = "upload"


def _photo_payload(photo):
    return {
        "id": photo.id,
        "url": photo.image.url,
        "caption": photo.caption,
        "slot": photo.slot,
        "order": photo.order,
    }


@api_view(["POST"])
def ensure_draft(request, template_slug):
    """Buat draft kosong untuk template ini, atau pakai yang sudah ada di sesi."""
    template = get_object_or_404(Template, slug=template_slug, is_active=True)

    card_id = request.data.get("card")
    if card_id:
        card = GiftCard.objects.filter(
            pk=card_id, status=GiftCard.Status.DRAFT
        ).first()
        if card and _owns(request, card):
            return Response({"card": str(card.id), "created": False})

    card = GiftCard.objects.create(
        template=template,
        category=template.category,
        amount=settings.CARD_PRICE,
    )
    _mark_owned(request, card)
    return Response({"card": str(card.id), "created": True}, status=201)


@api_view(["POST"])
@throttle_classes([UploadThrottle])
def upload_photo(request, card_id):
    """Terima satu foto. `slot` kosong = galeri, terisi = menempati bingkai."""
    card = get_object_or_404(GiftCard, pk=card_id)
    if not _owns(request, card):
        return Response({"detail": "Kartu ini bukan milik sesi ini."}, status=403)
    if card.is_paid:
        return Response({"detail": "Kartu sudah dibayar, tidak bisa diubah."}, status=409)

    upload = request.FILES.get("photo")
    if upload is None:
        return Response({"detail": "Tidak ada berkas."}, status=400)

    slot = (request.data.get("slot") or "").strip()[:32]
    if slot and slot not in card.frame_keys():
        return Response({"detail": "Bingkai tidak dikenal."}, status=400)

    if not slot and len(card.gallery_photos()) >= settings.MAX_PHOTOS_PER_CARD:
        return Response(
            {"detail": f"Maksimal {settings.MAX_PHOTOS_PER_CARD} foto galeri."},
            status=409,
        )

    try:
        processed = validate_and_compress_photo(upload)
    except ValidationError as exc:
        return Response({"detail": " ".join(exc.messages)}, status=400)

    if slot:
        # Satu bingkai hanya memuat satu foto — yang lama diganti.
        existing = card.photos.filter(slot=slot).first()
        if existing:
            existing.image.delete(save=False)
            existing.delete()
        order = 0
    else:
        order = len(card.gallery_photos())

    photo = GiftPhoto.objects.create(
        card=card, image=processed, slot=slot, order=order
    )
    return Response(_photo_payload(photo), status=201)


@api_view(["POST"])
def delete_photo(request, card_id, photo_id):
    card = get_object_or_404(GiftCard, pk=card_id)
    if not _owns(request, card):
        return Response({"detail": "Kartu ini bukan milik sesi ini."}, status=403)
    if card.is_paid:
        return Response({"detail": "Kartu sudah dibayar."}, status=409)

    photo = get_object_or_404(GiftPhoto, pk=photo_id, card=card)
    photo.image.delete(save=False)
    photo.delete()
    return Response(status=204)


@api_view(["POST"])
def set_caption(request, card_id, photo_id):
    card = get_object_or_404(GiftCard, pk=card_id)
    if not _owns(request, card):
        return Response({"detail": "Kartu ini bukan milik sesi ini."}, status=403)

    photo = get_object_or_404(GiftPhoto, pk=photo_id, card=card)
    photo.caption = (request.data.get("caption") or "").strip()[:40]
    photo.save(update_fields=["caption"])
    return Response(_photo_payload(photo))


@api_view(["POST"])
def save_content(request, card_id):
    """Simpan teks & gaya draft otomatis, tanpa menunggu tombol bayar.

    Ada karena bug nyata: preview dimuat ulang setelah unggah foto, dan semua
    editan yang baru ada di memori browser ikut hilang. Dengan disimpan lebih
    dulu, preview memuat ulang pun isinya sudah lengkap — dan draft tidak
    hilang kalau tab ditutup.
    """
    card = get_object_or_404(GiftCard, pk=card_id)
    if not _owns(request, card):
        return Response({"detail": "Kartu ini bukan milik sesi ini."}, status=403)
    if card.is_paid:
        return Response({"detail": "Kartu sudah dibayar."}, status=409)

    data = request.data if isinstance(request.data, dict) else {}

    card.style = sanitize_style(data.get("style"))

    allowed_texts = {spec["key"] for spec in card.text_specs()}
    incoming = data.get("texts")
    card.texts = (
        {
            key: str(value).strip()[:MAX_TEXT_LENGTH]
            for key, value in list(incoming.items())[:MAX_TEXT_KEYS]
            if key in allowed_texts and isinstance(value, str)
        }
        if isinstance(incoming, dict)
        else {}
    )

    fields = data.get("fields")
    if isinstance(fields, dict):
        card.recipient_name = str(fields.get("recipient", ""))[:80]
        card.sender_name = str(fields.get("sender", ""))[:80]
        card.message = str(fields.get("message", ""))[:4000]
        card.favorite_flower = str(fields.get("favorite_flower", ""))[:40]
        card.affirmations = "\n".join(
            line.strip()
            for line in str(fields.get("affirmations", "")).splitlines()
            if line.strip()
        )[:1000]
        try:
            card.youtube_video_id, card.spotify_track_id = parse_music_link(
                fields.get("youtube_url", "")
            )
        except ValidationError:
            pass  # link belum benar — biarkan yang lama, jangan gagalkan simpan

    card.save()
    return Response({"saved": True})
