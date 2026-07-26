"""Helper validasi input user: YouTube ID & foto."""

import io
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, UnidentifiedImageError

# Cocokkan format URL yang lazim ditempel user. ID YouTube = 11 karakter.
_YT_PATTERNS = [
    re.compile(r"(?:youtube\.com|youtube-nocookie\.com)/watch\?(?:.*&)?v=([A-Za-z0-9_-]{11})"),
    re.compile(r"youtu\.be/([A-Za-z0-9_-]{11})"),
    re.compile(r"(?:youtube\.com|youtube-nocookie\.com)/shorts/([A-Za-z0-9_-]{11})"),
    re.compile(r"(?:youtube\.com|youtube-nocookie\.com)/embed/([A-Za-z0-9_-]{11})"),
    re.compile(r"(?:youtube\.com|youtube-nocookie\.com)/live/([A-Za-z0-9_-]{11})"),
]

_BARE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_youtube_id(value: str) -> str:
    """Kembalikan video_id dari URL YouTube. String kosong → "" (opsional).

    Raise ValidationError kalau ada isi tapi bukan URL YouTube yang valid.
    """
    value = (value or "").strip()
    if not value:
        return ""

    if _BARE_ID.match(value):
        return value

    for pattern in _YT_PATTERNS:
        match = pattern.search(value)
        if match:
            return match.group(1)

    raise ValidationError(
        "Link YouTube tidak dikenali. Tempel link seperti "
        "https://youtu.be/xxxxxxxxxxx atau https://www.youtube.com/watch?v=xxxxxxxxxxx"
    )


ALLOWED_IMAGE_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
MAX_DIMENSION = 1600
JPEG_QUALITY = 82


def validate_and_compress_photo(uploaded) -> InMemoryUploadedFile:
    """Validasi MIME asli (lewat Pillow, bukan ekstensi), resize, lalu kompres.

    Semua foto dinormalisasi ke JPEG supaya ukuran & rendering konsisten.
    """
    if uploaded.size > settings.MAX_PHOTO_BYTES:
        limit_mb = settings.MAX_PHOTO_BYTES // (1024 * 1024)
        raise ValidationError(f"Ukuran foto maksimal {limit_mb}MB.")

    try:
        image = Image.open(uploaded)
        image.verify()  # deteksi file rusak / bukan gambar
    except (UnidentifiedImageError, OSError):
        raise ValidationError("File bukan gambar yang valid.")

    uploaded.seek(0)
    image = Image.open(uploaded)
    if image.format not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError("Format foto harus JPG, PNG, atau WEBP.")

    image = image.convert("RGB")
    image.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    buffer.seek(0)

    name = (uploaded.name or "foto").rsplit(".", 1)[0][:40] + ".jpg"
    return InMemoryUploadedFile(
        buffer, "ImageField", name, "image/jpeg", buffer.getbuffer().nbytes, None
    )
