from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.templatetags.static import static as static_url
from django.urls import include, path
from django.views.generic.base import RedirectView

from payments.webhooks import lynk_notification, midtrans_notification

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/webhooks/midtrans/", midtrans_notification, name="midtrans_webhook"),
    # Browser meminta /favicon.ico sendiri, tanpa diminta halaman. Rute
    # tangkap-semua `<str:ref>` di cards/urls.py menyambarnya dan mencarinya
    # sebagai slug kartu di database — satu query sia-sia tiap kunjungan, lalu
    # 404. Harus di ATAS include cards.urls supaya tertangkap lebih dulu.
    path(
        "favicon.ico",
        RedirectView.as_view(url=static_url("img/favicon.ico"), permanent=True),
    ),
    path("api/webhooks/lynk/", lynk_notification, name="lynk_webhook"),
    path("", include("cards.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
