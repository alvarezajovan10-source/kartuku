from django.db import models


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
