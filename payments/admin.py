from django.contrib import admin

from .models import PaymentEvent


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
