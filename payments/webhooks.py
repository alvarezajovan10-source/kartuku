import json
import logging

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import services
from .midtrans import verify_signature

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
