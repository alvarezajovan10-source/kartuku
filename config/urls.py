from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.templatetags.static import static as static_url
from django.urls import include, path

from payments.webhooks import lynk_notification, midtrans_notification


def favicon(request):
    """Browser meminta /favicon.ico sendiri, tanpa diminta halaman.

    Rute tangkap-semua `<str:ref>` di cards/urls.py menyambarnya dan mencarinya
    sebagai slug kartu di database — satu query sia-sia tiap kunjungan, lalu
    404. Rutenya harus di ATAS include cards.urls supaya tertangkap lebih dulu.

    Alamat statisnya dihitung saat permintaan datang, BUKAN saat modul di-import.
    Memanggil static() di tingkat modul memaksa backend staticfiles disiapkan
    sebelum Django selesai memuat, sehingga `manage.py migrate` pun gagal kalau
    backend itu tidak bisa di-import — dan pesan errornya menuding urls.py, jauh
    dari penyebab sebenarnya.
    """
    return redirect(static_url("img/favicon.ico"), permanent=True)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/webhooks/midtrans/", midtrans_notification, name="midtrans_webhook"),
    path("api/webhooks/lynk/", lynk_notification, name="lynk_webhook"),
    path("favicon.ico", favicon),
    path("", include("cards.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
