from django.contrib import admin

from .models import GiftCard, GiftPhoto, Template


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
    search_fields = ["id", "gateway_order_id", "gateway_txn_id", "recipient_name"]
    readonly_fields = ["id", "created_at", "updated_at", "paid_at", "gateway_txn_id"]
    inlines = [GiftPhotoInline]
