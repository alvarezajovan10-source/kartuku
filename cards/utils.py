"""Helper validasi input user: YouTube ID & foto."""

import io
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request

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

# Bingkai bertanda "asli": foto yang memenuhi satu halaman penuh. Dikecilkan
# ke 1600 px, foto seperti itu terlihat pecah — di kartu buku, satu foto bisa
# merentang selebar halaman pada layar retina.
MAX_DIMENSION_BESAR = 2400
# Batas atas untuk "sisi" yang diminta bingkai di config template.
MAX_DIMENSION_PINTA = 3600
JPEG_QUALITY_BESAR = 92


def validate_and_compress_photo(uploaded, besar: bool = False,
                                sisi_pinta: int | None = None) -> InMemoryUploadedFile:
    """Validasi MIME asli (lewat Pillow, bukan ekstensi), resize, lalu kompres.

    Semua foto dinormalisasi ke JPEG supaya ukuran & rendering konsisten.

    `besar=True` untuk bingkai yang fotonya memenuhi halaman: batas berkasnya
    lebih longgar dan sisi panjangnya dibiarkan sampai 2400 px. Validasinya
    TIDAK dilonggarkan — berkas tetap dibuka Pillow dulu, dan itu yang
    menahan berkas yang menyamar sebagai gambar.
    """
    batas = settings.MAX_PHOTO_BYTES_BESAR if besar else settings.MAX_PHOTO_BYTES
    sisi = MAX_DIMENSION_BESAR if besar else MAX_DIMENSION
    mutu = JPEG_QUALITY_BESAR if besar else JPEG_QUALITY

    # Bingkai boleh meminta sisi lebih panjang lewat "sisi" di config-nya.
    # Alasannya diukur, bukan selera: foto LATAR kartu mendatar dibentangkan
    # memenuhi jendela tanpa batas pembesaran, jadi di laptop retina satu
    # piksel foto harus mengisi 3.398 piksel layar. Pada 2400 px rasionya 0,71
    # — masih terlihat lembut; pada 3200 px jadi 0,94, praktis tajam.
    #
    # Dibatasi MAX_DIMENSION_PINTA supaya config yang salah ketik tidak
    # membuat server menyimpan foto raksasa. Kartu lain tidak terpengaruh:
    # tanpa "sisi", angkanya tetap seperti sebelumnya.
    if sisi_pinta:
        sisi = max(sisi, min(int(sisi_pinta), MAX_DIMENSION_PINTA))

    if uploaded.size > batas:
        limit_mb = batas // (1024 * 1024)
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
    image.thumbnail((sisi, sisi), Image.LANCZOS)

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=mutu, optimize=True)
    buffer.seek(0)

    name = (uploaded.name or "foto").rsplit(".", 1)[0][:40] + ".jpg"
    return InMemoryUploadedFile(
        buffer, "ImageField", name, "image/jpeg", buffer.getbuffer().nbytes, None
    )


_SPOTIFY = re.compile(r"open\.spotify\.com/(?:intl-[a-z]{2}/)?track/([A-Za-z0-9]{22})")


def extract_spotify_id(value: str) -> str:
    """ID track dari link Spotify. Kosong → "". Tidak valid → ValidationError."""
    value = (value or "").strip()
    if not value:
        return ""
    match = _SPOTIFY.search(value)
    if match:
        return match.group(1)
    raise ValidationError("Link Spotify tidak dikenali.")


def parse_music_link(value: str):
    """Kolom lagu hanya menerima YouTube.

    Spotify sengaja ditolak: embed-nya tidak bisa diputar otomatis sebagai
    musik latar (batasan Spotify), jadi kartu berlagu Spotify akan bisu —
    lebih baik ditolak di depan dengan penjelasan daripada pembeli kecewa.
    Kembalikan (youtube_id, spotify_id); spotify_id selalu "" untuk input
    baru, field-nya dipertahankan demi kartu lama.
    """
    value = (value or "").strip()
    if not value:
        return "", ""
    if "spotify.com" in value or "spotify:" in value:
        raise ValidationError(
            "Spotify tidak bisa diputar otomatis di kartu. "
            "Cari lagunya di YouTube lalu tempel link YouTube-nya di sini."
        )
    try:
        return extract_youtube_id(value), ""
    except ValidationError:
        raise ValidationError(
            "Link lagu tidak dikenali. Tempel link YouTube "
            "(youtu.be/... atau youtube.com/watch?v=...)."
        )


logger = logging.getLogger(__name__)

_OEMBED_TIMEOUT = 4  # detik — jangan sampai simpan draft ikut menggantung

# Saran yang dilampirkan tiap kali sebuah lagu ditolak. Unggahan "- Topic"
# (auto-generated YouTube Music) hampir selalu mengizinkan embed, beda dengan
# unggahan channel resmi label yang sering menguncinya.
EMBED_TIP = (
    "Coba cari lagu yang sama di YouTube dari channel yang namanya "
    'berakhiran "- Topic" — versi itu hampir selalu bisa diputar di kartu.'
)


def _api_json(url: str):
    """GET JSON. Kembalikan None kalau gagal — dipisah supaya mudah diuji."""
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "giftcard/1.0"})
        with urllib.request.urlopen(request, timeout=_OEMBED_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError, TimeoutError, OSError) as exc:
        logger.warning("Panggilan API gagal (%s): %s", url.split("?")[0], exc)
        return None


def check_youtube_embeddable(video_id: str):
    """Periksa apakah video boleh diputar di situs lain.

    Kembalikan (ok, alasan). `ok=True` juga dipakai saat pemeriksaan tidak bisa
    dilakukan (tanpa API key, atau jaringan gagal) — memblokir user karena
    masalah di sisi kita jauh lebih buruk daripada melewatkan satu kartu bisu.

    Butuh YOUTUBE_API_KEY; tanpa itu tidak ada cara andal memeriksanya —
    halaman embed membalas error yang sama untuk semua video kalau diminta
    dari server (tidak ada origin browser).
    """
    key = getattr(settings, "YOUTUBE_API_KEY", "")
    if not key or not video_id:
        return True, ""

    url = (
        "https://www.googleapis.com/youtube/v3/videos"
        f"?part=status&id={urllib.parse.quote(video_id)}"
        f"&key={urllib.parse.quote(key)}"
    )
    data = _api_json(url)
    if data is None:
        return True, ""  # jangan hukum user karena API-nya yang bermasalah

    items = data.get("items") or []
    if not items:
        return False, "Video tidak ditemukan — mungkin sudah dihapus atau privat."

    status = items[0].get("status") or {}
    if status.get("privacyStatus") == "private":
        return False, "Video ini privat, jadi tidak bisa diputar di kartu."
    if status.get("embeddable") is False:
        return False, (
            "Pemilik video ini melarang pemutaran di luar YouTube, "
            "jadi kartunya akan bisu. " + EMBED_TIP
        )
    return True, ""

# Channel unggahan lagu di YouTube sering berakhiran " - Topic" (auto-generated
# YouTube Music). Untuk itu nama channel = nama artis sebenarnya. Di luar itu
# nama channel belum tentu artis, jadi tidak dipakai.
_YT_TOPIC = re.compile(r"\s+-\s+Topic$")


def _oembed(url: str) -> dict:
    """Ambil JSON oEmbed. Gagal apa pun → dict kosong, bukan exception.

    Metadata lagu itu pemanis; kegagalan jaringan tidak boleh membuat user
    gagal menyimpan kartunya.
    """
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "giftcard/1.0"})
        with urllib.request.urlopen(request, timeout=_OEMBED_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, ValueError, TimeoutError, OSError) as exc:
        logger.warning("oEmbed gagal untuk %s: %s", url, exc)
        return {}


def fetch_track_meta(youtube_id: str = "", spotify_id: str = "") -> dict:
    """Judul, artis, dan cover lagu lewat oEmbed — tanpa API key.

    Kembalikan {"title", "artist", "cover"}; field yang tidak tersedia = "".
    Artis sengaja dibiarkan kosong kalau sumbernya tidak bisa dipercaya
    (lihat _YT_TOPIC) — lebih baik tidak tampil daripada salah.
    """
    empty = {"title": "", "artist": "", "cover": ""}

    if spotify_id:
        link = f"https://open.spotify.com/track/{spotify_id}"
        data = _oembed(
            "https://open.spotify.com/oembed?url=" + urllib.parse.quote(link, safe="")
        )
        if not data:
            return empty
        # oEmbed Spotify hanya memberi judul track, tidak ada nama artis.
        return {
            "title": (data.get("title") or "").strip(),
            "artist": "",
            "cover": (data.get("thumbnail_url") or "").strip(),
        }

    if youtube_id:
        link = f"https://www.youtube.com/watch?v={youtube_id}"
        data = _oembed(
            "https://www.youtube.com/oembed?format=json&url="
            + urllib.parse.quote(link, safe="")
        )
        if not data:
            return empty
        author = (data.get("author_name") or "").strip()
        artist = _YT_TOPIC.sub("", author) if _YT_TOPIC.search(author) else ""
        return {
            "title": (data.get("title") or "").strip(),
            "artist": artist,
            # hqdefault selalu ada; dipotong jadi lingkaran lewat object-fit.
            "cover": f"https://i.ytimg.com/vi/{youtube_id}/hqdefault.jpg",
        }

    return empty
