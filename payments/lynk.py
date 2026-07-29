"""Webhook Lynk.id — verifikasi tanda tangan & pembacaan payload.

Lynk memanggil situs kita setiap ada pembayaran sukses (`payment.received`).
Notifikasi itulah sumber kebenaran status bayar — persis aturan emas di
CLAUDE.md §2. Pembeli tidak pernah bisa mengaktifkan kartu dengan mengaku
sudah bayar; yang diterima hanya refId yang sudah dilaporkan Lynk lebih dulu.

Rumus tanda tangan (dari dokumentasi resmi Lynk):

    sha256(amount + refId + message_id + merchant_key)

dengan `amount` = `totals.grandTotal`. Perhatikan: ini SHA-256 biasa atas
gabungan string, bukan HMAC.
"""

import hashlib
import hmac
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

SUCCESS_EVENT = "payment.received"
SUCCESS_ACTION = "SUCCESS"


def _amount_candidates(value):
    """Bentuk-string yang mungkin dipakai Lynk untuk `amount` saat menandatangani.

    JSON mengirim grandTotal sebagai ANGKA (mis. 72000), sedangkan contoh kode
    di dokumentasi menggabungkannya sebagai STRING — tanpa memberi tahu cara
    mengubahnya. "72000" dan "72000.0" sama-sama masuk akal, jadi keduanya
    dicoba. Ini tidak melemahkan keamanan: tanpa merchant key, tidak satu pun
    varian bisa dihitung orang luar.
    """
    seen = []

    def add(text):
        if text not in seen:
            seen.append(text)

    add(str(value))
    if isinstance(value, bool):
        return seen
    if isinstance(value, (int, float)):
        if float(value).is_integer():
            add(str(int(value)))
        add(f"{float(value):.2f}")
    return seen


def compute_signature(amount, ref_id: str, message_id: str) -> str:
    """Tanda tangan untuk satu bentuk `amount` tertentu."""
    payload = f"{amount}{ref_id}{message_id}{settings.LYNK_MERCHANT_KEY}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_signature(payload: dict, received: str) -> bool:
    """True kalau X-Lynk-Signature cocok dengan hitungan kita.

    Tanpa merchant key, tanda tangan bisa dihitung siapa saja yang membaca
    payload — jadi konfigurasi yang belum lengkap harus MENOLAK, bukan
    meloloskan. Pelajaran yang sama dengan webhook Midtrans.
    """
    if not settings.LYNK_MERCHANT_KEY:
        logger.error(
            "LYNK_MERCHANT_KEY kosong — webhook ditolak. Tanpa kunci, tanda "
            "tangan tidak bisa diverifikasi dan kartu bisa diaktifkan tanpa bayar."
        )
        return False

    received = str(received or "").strip()
    if not received:
        return False

    data = (payload.get("data") or {}) if isinstance(payload, dict) else {}
    message_data = data.get("message_data") or {}
    totals = message_data.get("totals") or {}

    ref_id = str(message_data.get("refId", ""))
    message_id = str(data.get("message_id", ""))

    for amount in _amount_candidates(totals.get("grandTotal")):
        if hmac.compare_digest(compute_signature(amount, ref_id, message_id), received):
            return True
    return False


def is_successful_payment(payload: dict) -> bool:
    """Hanya event pembayaran sukses yang boleh memberi hak pakai."""
    if not isinstance(payload, dict):
        return False
    if payload.get("event") != SUCCESS_EVENT:
        return False
    data = payload.get("data") or {}
    return str(data.get("message_action", "")).upper() == SUCCESS_ACTION


def read_order(payload: dict) -> dict:
    """Ambil bagian yang kita butuhkan dari payload Lynk.

    Catatan penting soal nominal — dua angka berbeda untuk dua keperluan:

      totals.totalPrice  harga barang yang dibayar pembeli
      totals.grandTotal  yang DITERIMA penjual setelah potongan biaya Lynk

    grandTotal SELALU lebih kecil dari harga jual (convenienceFee negatif),
    jadi memakainya untuk memeriksa "sudah bayar cukup?" akan menolak semua
    pembayaran yang sah. Pemeriksaan nominal memakai totalPrice; grandTotal
    hanya dipakai untuk tanda tangan.
    """
    data = payload.get("data") or {}
    message_data = data.get("message_data") or {}
    totals = message_data.get("totals") or {}
    customer = message_data.get("customer") or {}
    items = message_data.get("items") or []

    def as_int(value):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0

    # Satu order bisa berisi lebih dari satu kartu (qty > 1). Pembeli yang
    # membeli 2 harus dapat 2 aktivasi, bukan 1.
    credits = 0
    titles = []
    for item in items:
        if not isinstance(item, dict):
            continue
        credits += max(1, as_int(item.get("qty")) or 1)
        if item.get("title"):
            titles.append(str(item["title"])[:80])

    return {
        "ref_id": str(message_data.get("refId", "")).strip(),
        "message_id": str(data.get("message_id", ""))[:120],
        "email": str(customer.get("email", ""))[:254],
        "name": str(customer.get("name", ""))[:120],
        "item_total": as_int(totals.get("totalPrice")),
        "grand_total": as_int(totals.get("grandTotal")),
        "credits": credits or 1,
        "items": ", ".join(titles)[:200],
    }
