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

    def public_url(self):
        return reverse("cards:public", args=[self.slug or self.id])

    def youtube_embed_url(self):
        if not self.youtube_video_id:
            return ""
        return f"https://www.youtube-nocookie.com/embed/{self.youtube_video_id}"

    def spotify_embed_url(self):
        if not self.spotify_track_id:
            return ""
        return f"https://open.spotify.com/embed/track/{self.spotify_track_id}"

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
