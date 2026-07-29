from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from payments.webhooks import lynk_notification, midtrans_notification

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/webhooks/midtrans/", midtrans_notification, name="midtrans_webhook"),
    path("api/webhooks/lynk/", lynk_notification, name="lynk_webhook"),
    path("", include("cards.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
