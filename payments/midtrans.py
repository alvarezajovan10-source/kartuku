"""Client Midtrans Core API (metode QRIS) + verifikasi signature.

Hanya dua hal yang keluar dari modul ini:
  - create_qris_charge(): buat transaksi, kembalikan data QR.
  - verify_signature(): validasi webhook. JANGAN pernah dilewati.
"""

import base64
import hashlib
import hmac
import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger(__name__)

SANDBOX_BASE = "https://api.sandbox.midtrans.com"
PRODUCTION_BASE = "https://api.midtrans.com"

TIMEOUT_SECONDS = 20


class MidtransError(Exception):
    """Gagal memanggil Midtrans, atau Midtrans menolak transaksi."""


@dataclass
class QrisCharge:
    order_id: str
    transaction_id: str
    transaction_status: str
    qr_string: str
    qr_image_url: str
    expiry_time: str
    raw: dict


def _base_url() -> str:
    return PRODUCTION_BASE if settings.MIDTRANS_IS_PRODUCTION else SANDBOX_BASE


def _auth_header() -> str:
    if not settings.MIDTRANS_SERVER_KEY:
        raise MidtransError("MIDTRANS_SERVER_KEY belum diisi di .env")
    token = base64.b64encode(f"{settings.MIDTRANS_SERVER_KEY}:".encode()).decode()
    return f"Basic {token}"


def _post(path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        f"{_base_url()}{path}",
        data=json.dumps(payload).encode(),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": _auth_header(),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        logger.error("Midtrans HTTP %s pada %s: %s", exc.code, path, body)
        raise MidtransError(f"Midtrans menolak permintaan (HTTP {exc.code}).") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.error("Midtrans tidak terjangkau pada %s: %s", path, exc)
        raise MidtransError("Tidak bisa menghubungi Midtrans. Coba lagi.") from exc


def create_qris_charge(order_id: str, gross_amount: int, expiry_minutes: int) -> QrisCharge:
    payload = {
        "payment_type": "qris",
        "transaction_details": {"order_id": order_id, "gross_amount": gross_amount},
        "qris": {"acquirer": "gopay"},
        "custom_expiry": {"unit": "minute", "expiry_duration": expiry_minutes},
    }
    data = _post("/v2/charge", payload)

    # status_code "201" = transaksi dibuat, "200" = sukses. Selain itu → gagal.
    if data.get("status_code") not in {"200", "201"}:
        message = data.get("status_message", "tidak diketahui")
        logger.error("Charge gagal untuk %s: %s", order_id, data)
        raise MidtransError(f"Gagal membuat QRIS: {message}")

    qr_image_url = ""
    for action in data.get("actions", []):
        if action.get("name") in {"generate-qr-code", "generate-qr-code-v2"}:
            qr_image_url = action.get("url", "")
            break

    return QrisCharge(
        order_id=data.get("order_id", order_id),
        transaction_id=data.get("transaction_id", ""),
        transaction_status=data.get("transaction_status", "pending"),
        qr_string=data.get("qr_string", ""),
        qr_image_url=qr_image_url,
        expiry_time=data.get("expiry_time", ""),
        raw=data,
    )


def compute_signature(order_id: str, status_code: str, gross_amount: str) -> str:
    """SHA512(order_id + status_code + gross_amount + ServerKey) — spesifikasi Midtrans."""
    payload = f"{order_id}{status_code}{gross_amount}{settings.MIDTRANS_SERVER_KEY}"
    return hashlib.sha512(payload.encode()).hexdigest()


def verify_signature(notification: dict) -> bool:
    """True kalau signature_key di notifikasi cocok dengan hitungan kita.

    gross_amount dibandingkan apa adanya (string dari Midtrans, mis. "15000.00").
    """
    # Tanpa server key, signature-nya cuma SHA512 dari tiga nilai yang semuanya
    # ada di payload — siapa pun bisa menghitungnya dan mengaku "sudah bayar".
    # Jadi konfigurasi yang belum lengkap harus MENOLAK, bukan meloloskan.
    if not settings.MIDTRANS_SERVER_KEY:
        logger.error(
            "MIDTRANS_SERVER_KEY kosong — webhook ditolak. Tanpa key, signature "
            "tidak bisa diverifikasi dan kartu bisa dibuka tanpa bayar."
        )
        return False

    expected = compute_signature(
        str(notification.get("order_id", "")),
        str(notification.get("status_code", "")),
        str(notification.get("gross_amount", "")),
    )
    received = str(notification.get("signature_key", ""))
    return hmac.compare_digest(expected, received)
