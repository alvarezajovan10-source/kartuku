from django.contrib import admin

from .models import LynkOrder, PaymentEvent


@admin.register(LynkOrder)
class LynkOrderAdmin(admin.ModelAdmin):
    """Daftar pembelian Lynk yang sudah dikonfirmasi webhook.

    Ini tempatmu mencocokkan saat ada pembeli komplain: cari REF ID-nya, lihat
    kuotanya sudah terpakai atau belum, dan email siapa yang membelinya.
    """

    list_display = [
        "ref_id", "customer_email", "items", "item_total",
        "credits_used", "credits_total", "received_at",
    ]
    search_fields = ["ref_id", "customer_email", "customer_name", "items"]
    list_filter = ["received_at"]
    readonly_fields = [f.name for f in LynkOrder._meta.fields]

    def has_add_permission(self, request):
        # Hak pakai hanya boleh lahir dari webhook yang terverifikasi. Kalau
        # perlu memberi akses manual, pakai Kode Akses (KRT-...).
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PaymentEvent)
class PaymentEventAdmin(admin.ModelAdmin):
    list_display = ["gateway_txn_id", "transaction_status", "card", "received_at"]
    list_filter = ["transaction_status"]
    search_fields = ["gateway_txn_id", "card__id"]
    readonly_fields = [f.name for f in PaymentEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False  # log audit — jangan diedit
