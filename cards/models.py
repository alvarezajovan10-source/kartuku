from uuid import uuid4

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class CardType(models.TextChoices):
    BIRTHDAY = "birthday", "Ulang Tahun"
    ANNIVERSARY = "anniversary", "Anniversary"
    LOVE_STORY = "love_story", "Love Story"
    PROPOSAL = "proposal", "Lamaran"


class Template(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CardType.choices)
    config = models.JSONField(default=dict, blank=True)  # layout, warna, field tersedia
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Template"
        verbose_name_plural = "Template"
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class GiftCard(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Menunggu bayar"
        PAID = "paid", "Lunas"
        EXPIRED = "expired", "Kedaluwarsa"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    template = models.ForeignKey(Template, on_delete=models.PROTECT)
    category = models.CharField(max_length=20, choices=CardType.choices)

    sender_name = models.CharField(max_length=80, blank=True)
    recipient_name = models.CharField(max_length=80, blank=True)
    message = models.TextField(blank=True)
    youtube_video_id = models.CharField(max_length=20, blank=True)
    spotify_track_id = models.CharField(max_length=30, blank=True)

    # Metadata lagu hasil oEmbed, diisi otomatis saat link disimpan (lihat
    # cards.utils.fetch_track_meta). Dicache di DB supaya halaman publik tidak
    # memanggil YouTube/Spotify tiap kali dibuka. Kosong = jangan ditampilkan.
    track_title = models.CharField(max_length=200, blank=True)
    track_artist = models.CharField(max_length=120, blank=True)
    track_cover_url = models.URLField(max_length=500, blank=True)

    # Link cantik pilihan user setelah bayar: /g/<slug>. Kode UUID tetap jalan.
    slug = models.SlugField(max_length=60, unique=True, null=True, blank=True)

    # Isian khusus template yang punya bagian "bunga" (mis. Birthday).
    favorite_flower = models.CharField(max_length=40, blank=True)
    affirmations = models.TextField(blank=True, help_text="Satu kalimat per baris.")

    # Pilihan font/warna/ukuran/perataan dari editor. Selalu dibersihkan lewat
    # cards.styles.sanitize_style sebelum dipakai — jangan pernah dipercaya mentah.
    style = models.JSONField(default=dict, blank=True)

    # Teks bebas per template: {"cover_title": "Happy Birthday!", ...}.
    # Kunci berasal dari Template.config["texts"]; nilai lain diabaikan.
    texts = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    amount = models.PositiveIntegerField(default=settings.CARD_PRICE)

    # Payment tracking
    gateway_order_id = models.CharField(max_length=64, blank=True, db_index=True)
    gateway_txn_id = models.CharField(max_length=64, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    qr_expires_at = models.DateTimeField(null=True, blank=True)

    # QR dari Midtrans disimpan supaya bisa DITAMPILKAN ULANG. Midtrans menolak
    # order_id yang dipakai ulang, jadi tanpa ini user yang me-refresh halaman
    # bayar tidak bisa melihat QR apa pun sampai yang lama kedaluwarsa.
    qr_string = models.TextField(blank=True)
    qr_image_url = models.URLField(max_length=500, blank=True)

    # True = diaktifkan gratis oleh pemilik situs, bukan hasil pembayaran.
    # Dipisahkan supaya kartu uji coba tidak terhitung sebagai penjualan.
    comped = models.BooleanField(default=False, verbose_name="Gratis (pemilik)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kartu"
        verbose_name_plural = "Kartu"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_category_display()} → {self.recipient_name or '?'} [{self.status}]"

    @property
    def is_paid(self):
        return self.status == self.Status.PAID

    @property
    def qr_is_expired(self):
        return bool(self.qr_expires_at and timezone.now() >= self.qr_expires_at)

    @property
    def qr_is_live(self):
        """QR lama masih bisa dipakai — tampilkan itu, jangan buat yang baru."""
        return bool(
            self.status == self.Status.PENDING
            and not self.qr_is_expired
            and (self.qr_image_url or self.qr_string)
        )

    def public_url(self):
        return reverse("cards:public", args=[self.slug or self.id])

    def youtube_embed_url(self):
        if not self.youtube_video_id:
            return ""
        return f"https://www.youtube-nocookie.com/embed/{self.youtube_video_id}"

    def track_link_url(self):
        """Tujuan klik piringan hitam: buka lagunya di sumber aslinya."""
        if self.spotify_track_id:
            return f"https://open.spotify.com/track/{self.spotify_track_id}"
        if self.youtube_video_id:
            return f"https://www.youtube.com/watch?v={self.youtube_video_id}"
        return ""

    def track_source_name(self):
        if self.spotify_track_id:
            return "Spotify"
        if self.youtube_video_id:
            return "YouTube"
        return ""

    def spotify_embed_url(self):
        if not self.spotify_track_id:
            return ""
        # theme=0 = varian gelap, lebih menyatu dengan latar merah kartu
        return f"https://open.spotify.com/embed/track/{self.spotify_track_id}?theme=0"

    MAX_AFFIRMATIONS = 4

    def affirmation_list(self):
        """Afirmasi sebagai list, baris kosong dibuang, dibatasi MAX_AFFIRMATIONS."""
        lines = [line.strip() for line in self.affirmations.splitlines()]
        return [line for line in lines if line][: self.MAX_AFFIRMATIONS]

    def style_clean(self):
        """Gaya yang sudah lolos daftar putih."""
        from .styles import sanitize_style

        return sanitize_style(self.style)

    def colors_css(self):
        """Var warna permukaan untuk elemen pembungkus kartu."""
        from .styles import colors_css

        return colors_css(self.style_clean()["colors"])

    def fonts_used(self):
        """Kunci font yang benar-benar dipakai kartu ini.

        Halaman kartu hanya memuat font ini, bukan seluruh katalog — 20+ font
        akan memperlambat kartu di HP penerima tanpa guna.
        """
        elements = self.style_clean()["elements"]
        return sorted({conf["font"] for conf in elements.values() if "font" in conf})

    def renderer(self):
        """Nama template render kartu final, dari `Template.config["renderer"]`."""
        return (self.template.config or {}).get("renderer", "")

    def text_specs(self):
        """Teks yang boleh diubah: [{"key","label","default"}, ...]."""
        raw = (self.template.config or {}).get("texts", [])
        return [t for t in raw if isinstance(t, dict) and t.get("key")]

    def text_defaults(self):
        return {t["key"]: t.get("default", "") for t in self.text_specs()}

    def text(self, key):
        """Isi teks: pilihan user kalau ada, kalau tidak bawaan template."""
        override = (self.texts or {}).get(key)
        if isinstance(override, str) and override.strip():
            return override
        return self.text_defaults().get(key, "")

    def element_specs(self):
        """Elemen yang bisa disunting: [{"key","label","type"}, ...].

        type: "text" (teks + gaya), "photo" (bingkai foto), "surface" (warna).
        """
        raw = (self.template.config or {}).get("elements", [])
        return [e for e in raw if isinstance(e, dict) and e.get("key")]

    def surface_specs(self):
        """Permukaan berwarna yang boleh diganti: [{"key","label","default"}, ...]."""
        raw = (self.template.config or {}).get("surfaces", [])
        return [s for s in raw if isinstance(s, dict) and s.get("key")]

    def frames(self):
        """Bingkai foto yang disediakan template: [{"key","label"}, ...]."""
        raw = (self.template.config or {}).get("frames", [])
        return [f for f in raw if isinstance(f, dict) and f.get("key")]

    def frame_keys(self):
        return {frame["key"] for frame in self.frames()}

    def photo_by_slot(self):
        """{slot: GiftPhoto} untuk foto yang menempati bingkai."""
        return {p.slot: p for p in self.photos.all() if p.slot}

    def gallery_photos(self):
        """Foto tanpa bingkai — galeri bebas."""
        return [p for p in self.photos.all() if not p.slot]


class GiftPhoto(models.Model):
    card = models.ForeignKey(GiftCard, related_name="photos", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="cards/%Y/%m/")
    caption = models.CharField(max_length=40, blank=True)
    # Kunci bingkai dari Template.config["frames"]. Kosong = masuk galeri bebas.
    slot = models.CharField(max_length=32, blank=True, db_index=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = "Foto Kartu"
        verbose_name_plural = "Foto Kartu"
        ordering = ["order", "id"]

    @property
    def element_key(self):
        """Kunci elemen untuk foto galeri, supaya bisa diklik & di-crop sendiri."""
        return f"photo_{self.pk}"

    def __str__(self):
        return f"Foto #{self.order} — {self.card_id}"


class AccessCode(models.Model):
    """Kode sekali pakai untuk mengaktifkan satu kartu.

    Dipakai saat pembayaran ditangani di luar situs (mis. Lynk.id): pembeli
    membayar di sana, pemilik situs mengirimkan kode lewat email, pembeli
    menukarnya di halaman bayar.

    Yang sekali pakai adalah KODE-nya, bukan kartunya. Kartu yang sudah aktif
    tetap bisa dibuka berkali-kali oleh penerima — itu inti produknya.
    """

    # Tanpa huruf/angka yang mudah tertukar saat dibaca atau diketik ulang:
    # I, L, O, 0, 1 sengaja dibuang.
    ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    PREFIX = "KRT"

    code = models.CharField(max_length=20, unique=True, db_index=True)
    # Jejak ke pembelian aslinya: nama/email pembeli atau nomor order Lynk.
    note = models.CharField(
        max_length=120, blank=True, verbose_name="Catatan pembeli"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    card = models.OneToOneField(
        GiftCard,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="access_code",
    )

    class Meta:
        verbose_name = "Kode Akses"
        verbose_name_plural = "Kode Akses"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.code} ({'terpakai' if self.is_used else 'belum dipakai'})"

    @property
    def is_used(self):
        return self.used_at is not None

    @classmethod
    def generate_code(cls):
        """Kode acak baru yang belum ada di database."""
        import secrets

        while True:
            body = "".join(secrets.choice(cls.ALPHABET) for _ in range(8))
            code = f"{cls.PREFIX}-{body[:4]}-{body[4:]}"
            if not cls.objects.filter(code=code).exists():
                return code

    @classmethod
    def claim(cls, code, card):
        """Pakai kode ini untuk `card`, secara atomik. True kalau berhasil.

        Sengaja UPDATE bersyarat, bukan select_for_update(): SQLite tidak
        mendukung penguncian baris dan Django mengabaikannya diam-diam, jadi
        dua permintaan bersamaan bisa sama-sama lolos. Satu
        `UPDATE ... WHERE used_at IS NULL` aman di semua database.
        """
        from django.utils import timezone

        return (
            cls.objects.filter(code=code, used_at__isnull=True).update(
                used_at=timezone.now(), card=card
            )
            > 0
        )

    @classmethod
    def normalize(cls, raw):
        """Rapikan ketikan user jadi bentuk baku, atau "" kalau bentuknya salah.

        Menerima huruf kecil, tanpa tanda hubung, dengan spasi, dan dengan atau
        tanpa awalan KRT — pembeli menyalin kode dari email, bentuknya
        bermacam-macam dan itu bukan salah mereka.
        """
        import re

        cleaned = re.sub(r"[^A-Z0-9]", "", (raw or "").upper())
        if cleaned.startswith(cls.PREFIX):
            cleaned = cleaned[len(cls.PREFIX) :]
        if len(cleaned) != 8 or any(c not in cls.ALPHABET for c in cleaned):
            return ""
        return f"{cls.PREFIX}-{cleaned[:4]}-{cleaned[4:]}"
