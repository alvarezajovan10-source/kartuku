import json
import logging

from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import lynk, services
from .midtrans import verify_signature
from .models import LynkOrder

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def midtrans_notification(request):
    """POST /api/webhooks/midtrans/ — CSRF-exempt tapi signature-verified.

    Selalu balas 200 untuk event yang sudah kita tangani (termasuk yang diabaikan),
    supaya Midtrans berhenti retry. 403 hanya untuk signature yang tidak cocok.
    """
    try:
        payload = json.loads(request.body.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": "payload bukan JSON"}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"detail": "payload bukan objek"}, status=400)

    if not verify_signature(payload):
        logger.warning(
            "Signature webhook tidak cocok untuk order_id=%s", payload.get("order_id")
        )
        return JsonResponse({"detail": "signature tidak valid"}, status=403)

    result = services.process_notification(payload)
    logger.info("Webhook %s → %s", payload.get("order_id"), result)
    return HttpResponse("OK", status=200)


@csrf_exempt
@require_POST
def lynk_notification(request):
    """POST /api/webhooks/lynk/ — CSRF-exempt tapi tanda-tangan-terverifikasi.

    Lynk mengirim `payment.received` setiap pembayaran berhasil. Dari situ kita
    catat "hak pakai" berisi refId, yang nanti ditukar pembeli di halaman
    aktivasi. Kartunya belum ada saat webhook tiba — pembeli membayar dulu,
    baru membuat kartunya — jadi yang disimpan adalah ordernya, bukan kartunya.

    Selalu balas 200 untuk event yang sudah ditangani (termasuk yang sengaja
    diabaikan) supaya Lynk berhenti mengulang. 403 hanya untuk tanda tangan
    yang tidak cocok.
    """
    try:
        payload = json.loads(request.body.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"detail": "payload bukan JSON"}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"detail": "payload bukan objek"}, status=400)

    if not lynk.verify_signature(payload, request.headers.get("X-Lynk-Signature", "")):
        logger.warning("Tanda tangan webhook Lynk tidak cocok — ditolak.")
        return JsonResponse({"detail": "signature tidak valid"}, status=403)

    if not lynk.is_successful_payment(payload):
        logger.info("Webhook Lynk diabaikan (event=%s)", payload.get("event"))
        return HttpResponse("OK", status=200)

    order = lynk.read_order(payload)
    if not order["ref_id"]:
        logger.error("Webhook Lynk tanpa refId — tidak bisa dipakai.")
        return HttpResponse("OK", status=200)

    # Nominal diperiksa dengan totalPrice (yang dibayar pembeli), BUKAN
    # grandTotal (yang diterima penjual setelah potongan Lynk) — lihat
    # lynk.read_order. Ini menahan orang membeli produk murah lalu memakainya
    # untuk kartu penuh.
    if order["item_total"] < settings.LYNK_MIN_AMOUNT:
        logger.error(
            "Order Lynk %s nominalnya kurang: %s < %s",
            order["ref_id"], order["item_total"], settings.LYNK_MIN_AMOUNT,
        )
        return HttpResponse("OK", status=200)

    try:
        # atomic() di DALAM try, bukan sebaliknya: IntegrityError yang ditangkap
        # di dalam blok atomic meninggalkan transaksi dalam keadaan rusak, dan
        # query berikutnya ikut gagal.
        with transaction.atomic():
            LynkOrder.objects.create(
                ref_id=order["ref_id"],
                message_id=order["message_id"],
                customer_email=order["email"],
                customer_name=order["name"],
                items=order["items"],
                item_total=order["item_total"],
                grand_total=order["grand_total"],
                credits_total=order["credits"],
                raw_payload=payload,
            )
    except IntegrityError:
        # Lynk mengulang kiriman kalau balasan kita bukan 200. refId-nya unik,
        # jadi pengulangan berhenti di sini tanpa menggandakan kuota.
        logger.info("Order Lynk %s sudah tercatat — diabaikan.", order["ref_id"])
        return HttpResponse("OK", status=200)

    logger.info(
        "Order Lynk %s tercatat: %s kuota, Rp%s, %s",
        order["ref_id"], order["credits"], order["item_total"], order["email"],
    )
    return HttpResponse("OK", status=200)
