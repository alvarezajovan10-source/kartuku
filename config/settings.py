from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    MIDTRANS_IS_PRODUCTION=(bool, False),
    USE_R2=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

DEV_SECRET_KEY = "dev-only-insecure-key"
SECRET_KEY = env("DJANGO_SECRET_KEY", default=DEV_SECRET_KEY)
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Kunci bawaan hanya boleh untuk dev. Kalau ikut terbawa ke produksi, sesi dan
# token CSRF bisa dipalsukan siapa pun yang membaca repo ini — gagal saat start
# jauh lebih baik daripada situs yang menyala tapi bisa dibobol.
if not DEBUG and SECRET_KEY == DEV_SECRET_KEY:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY belum diisi. Isi dengan string acak panjang di .env "
        "sebelum menjalankan dengan DJANGO_DEBUG=False."
    )
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "cards",
    "payments",
]

# Bawaan Django "same-origin" menahan SELURUH info asal ke domain lain, dan
# pemutar YouTube memakainya untuk memverifikasi situs pemanggil — tanpa itu
# musik latar selalu gagal dengan "Error 153". Nilai ini hanya mengirim origin
# (skema+host), bukan alamat lengkap, jadi kode unik kartu tetap tidak bocor
# ke YouTube. Ini juga nilai bawaan mayoritas browser.
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Menyajikan file di STATIC_ROOT langsung dari Django, jadi hosting tidak
    # perlu dikonfigurasi menunjuk folder static. Wajib tepat di bawah
    # SecurityMiddleware.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cards.context_processors.payment",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Dev pakai SQLite; produksi set DATABASE_URL ke postgres://...
DATABASES = {
    "default": env.db_url(
        "DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "id"
TIME_ZONE = "Asia/Jakarta"
USE_I18N = True
USE_TZ = True
# Tanpa ini harga tampil "Rp15000" di seluruh situs — locale id sudah punya
# titik sebagai pemisah ribuan, tapi Django tidak memakainya sampai disuruh.
# Hanya menyentuh angka >= 1000 di teks; data untuk JavaScript lewat
# json_script (JSON murni), jadi tidak ikut terformat.
USE_THOUSAND_SEPARATOR = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Storage -----------------------------------------------------------------
# Dev: file lokal di MEDIA_ROOT. Produksi: Cloudflare R2 (S3-compatible).
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # WhiteNoise memampatkan file static saat collectstatic. Tanpa manifest
    # hash — cache-busting sudah ditangani tag {% static_v %} lewat ?v=mtime.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

if env("USE_R2"):
    R2_ACCOUNT_ID = env("R2_ACCOUNT_ID")
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": env("R2_ACCESS_KEY_ID"),
            "secret_key": env("R2_SECRET_ACCESS_KEY"),
            "bucket_name": env("R2_BUCKET_NAME"),
            "endpoint_url": f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            "custom_domain": env("R2_PUBLIC_URL").replace("https://", ""),
            "region_name": "auto",
            "default_acl": None,
            "querystring_auth": False,
            "signature_version": "s3v4",
        },
    }

# --- Aplikasi ----------------------------------------------------------------
# Situs ini tidak punya halaman login sendiri — pemilik login lewat admin.
LOGIN_URL = "/admin/login/"

CARD_PRICE = 15_000
QR_TTL_MINUTES = 15
# Batas longgar: cukup untuk pemakaian wajar, menahan orang mengunggah ratusan
# foto dengan sekali bayar Rp15.000.
MAX_PHOTOS_PER_CARD = 30
MAX_PHOTO_BYTES = 3 * 1024 * 1024

# API key YouTube Data v3 — dipakai memeriksa apakah lagu yang ditempel user
# boleh diputar di situs lain. Kosong = pemeriksaan dilewati (kartu tetap bisa
# dibuat, tapi risiko kartu bisu kembali ada).
YOUTUBE_API_KEY = env("YOUTUBE_API_KEY", default="")

# --- Lynk.id -----------------------------------------------------------------
# Pembayaran ditangani di luar situs (link Lynk di bio TikTok). Lynk memanggil
# /api/webhooks/lynk/ setiap pembayaran sukses; dari situ lahir "hak pakai"
# yang ditukar pembeli dengan REF ID di email struknya.
#
# Kunci ini BARU MUNCUL di dashboard Lynk setelah URL webhook disimpan.
# Kosong = webhook ditolak (lihat payments/lynk.verify_signature).
LYNK_MERCHANT_KEY = env("LYNK_MERCHANT_KEY", default="")

# Harga minimal yang dianggap sah untuk satu kartu. Dibuat bisa diatur supaya
# produk uji coba murah bisa dipakai saat mencoba alurnya; naikkan ke
# CARD_PRICE sebelum jualan sungguhan.
LYNK_MIN_AMOUNT = env.int("LYNK_MIN_AMOUNT", default=CARD_PRICE)

MIDTRANS_SERVER_KEY = env("MIDTRANS_SERVER_KEY", default="")
MIDTRANS_CLIENT_KEY = env("MIDTRANS_CLIENT_KEY", default="")
MIDTRANS_IS_PRODUCTION = env("MIDTRANS_IS_PRODUCTION")
MIDTRANS_MERCHANT_ID = env("MIDTRANS_MERCHANT_ID", default="")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_THROTTLE_RATES": {
        "pay": "20/hour",
        "status": "240/min",
        "upload": "120/hour",
    },
}

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_HSTS_PRELOAD sengaja dibiarkan mati. Preload itu pintu satu arah:
    # sekali masuk daftar browser, sulit dicabut, dan tidak pantas dinyalakan
    # untuk subdomain milik bersama seperti *.pythonanywhere.com. Nyalakan
    # nanti kalau situs sudah pindah ke domain sendiri.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
