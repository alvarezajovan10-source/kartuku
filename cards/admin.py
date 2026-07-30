from django.contrib import admin

from .models import AccessCode, GiftCard, GiftPhoto, Template


@admin.register(AccessCode)
class AccessCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "note", "status_label", "used_at", "created_at"]
    list_filter = ["used_at"]
    search_fields = ["code", "note"]
    readonly_fields = ["used_at", "card", "created_at"]

    @admin.display(description="Status", boolean=True)
    def status_label(self, obj):
        return not obj.is_used

    def get_changeform_initial_data(self, request):
        """Isi kode acak otomatis, jadi tinggal tulis catatan pembelinya."""
        return {"code": AccessCode.generate_code()}


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "category", "is_active"]
    list_filter = ["category", "is_active"]
    prepopulated_fields = {"slug": ("name",)}


class GiftPhotoInline(admin.TabularInline):
    model = GiftPhoto
    extra = 0


@admin.register(GiftCard)
class GiftCardAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "category",
        "recipient_name",
        "status",
        "amount",
        "comped",
        "paid_at",
        "created_at",
    ]
    list_filter = ["status", "category", "comped"]
    # Urutannya mengikuti apa yang paling mungkin dikirim pelanggan saat minta
    # bantuan: potongan link kartunya (slug), lalu nama-nama di kartu. UUID dan
    # nomor gateway jarang mereka pegang — itu untuk pelacakan dari sisi kita.
    search_fields = [
        "slug",
        "recipient_name",
        "sender_name",
        "id",
        "gateway_order_id",
        "gateway_txn_id",
    ]
    readonly_fields = ["id", "created_at", "updated_at", "paid_at", "gateway_txn_id"]
    inlines = [GiftPhotoInline]
