import re

from django.db import models
from django.db.models import F


class LynkOrder(models.Model):
    """Satu pembelian di Lynk.id yang sudah dikonfirmasi lewat webhook.

    Ini "hak pakai": bukti bahwa seseorang benar-benar sudah membayar. Pembeli
    menukarnya dengan menempelkan REF ID dari email struknya di halaman
    aktivasi. Karena barisnya hanya lahir dari webhook yang tanda tangannya
    sudah diverifikasi, REF ID palsu tidak akan pernah ketemu.

    Satu order bisa bernilai lebih dari satu kartu kalau pembeli memesan qty>1,
    jadi yang dihitung adalah kuota (`credits_total`), bukan sekadar
    terpakai/belum.
    """

    ref_id = models.CharField(max_length=64, unique=True, db_index=True)
    message_id = models.CharField(max_length=120, blank=True)

    customer_email = models.EmailField(blank=True)
    customer_name = models.CharField(max_length=120, blank=True)
    items = models.CharField(max_length=200, blank=True, verbose_name="Produk")

    # Yang dibayar pembeli. Dipakai untuk memeriksa nominal.
    item_total = models.PositiveIntegerField(default=0, verbose_name="Harga barang")
    # Yang diterima penjual setelah potongan Lynk — bisa lebih kecil dari harga,
    # jadi JANGAN dipakai untuk memeriksa kecukupan pembayaran.
    grand_total = models.IntegerField(default=0, verbose_name="Diterima penjual")

    credits_total = models.PositiveSmallIntegerField(default=1, verbose_name="Kuota")
    credits_used = models.PositiveSmallIntegerField(default=0, verbose_name="Terpakai")

    raw_payload = models.JSONField(default=dict)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Order Lynk"
        verbose_name_plural = "Order Lynk"
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.ref_id} ({self.credits_used}/{self.credits_total} terpakai)"

    @property
    def is_exhausted(self):
        return self.credits_used >= self.credits_total

    @staticmethod
    def normalize(raw):
        """Rapikan REF ID yang ditempel pembeli, atau "" kalau bentuknya mustahil.

        Di email struk, REF ID tercetak terpotong dua baris, jadi hasil salin
        pembeli sering membawa spasi atau ganti baris. Semua karakter di luar
        heksadesimal dibuang lebih dulu — bukan salah mereka.
        """
        cleaned = re.sub(r"[^0-9a-f]", "", (raw or "").lower())
        return cleaned if 16 <= len(cleaned) <= 64 else ""

    @classmethod
    def claim(cls, ref_id):
        """Ambil satu kuota secara atomik. True kalau berhasil.

        Sengaja memakai UPDATE bersyarat, bukan select_for_update(): SQLite
        tidak mendukung penguncian baris dan Django mengabaikannya diam-diam,
        sehingga dua permintaan bersamaan bisa sama-sama lolos. Satu
        `UPDATE ... WHERE credits_used < credits_total` aman di semua database.
        """
        return (
            cls.objects.filter(ref_id=ref_id, credits_used__lt=F("credits_total"))
            .update(credits_used=F("credits_used") + 1)
            > 0
        )


class PaymentEvent(models.Model):
    """Log tiap webhook masuk — untuk idempotency & audit."""

    card = models.ForeignKey(
        "cards.GiftCard", on_delete=models.CASCADE, related_name="events"
    )
    gateway_txn_id = models.CharField(max_length=64, db_index=True)
    transaction_status = models.CharField(max_length=30)
    raw_payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Event Pembayaran"
        verbose_name_plural = "Event Pembayaran"
        ordering = ["-received_at"]
        constraints = [
            # cegah proses dobel dari webhook yang dikirim berkali-kali
            models.UniqueConstraint(
                fields=["gateway_txn_id", "transaction_status"],
                name="unique_txn_status",
            )
        ]

    def __str__(self):
        return f"{self.gateway_txn_id} → {self.transaction_status}"
