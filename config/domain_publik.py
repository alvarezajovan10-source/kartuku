"""Membuat Django memakai nama domain yang dilihat pengunjung.

Kartuku disajikan di yourdigitalcard.my.id lewat perantara PHP di hosting
Rumahweb, karena paket gratis PythonAnywhere tidak mengizinkan domain sendiri.
Aplikasinya sendiri tetap berjalan di kartuku.pythonanywhere.com.

Akibatnya setiap alamat lengkap yang disusun Django memakai nama host aslinya.
Untuk halaman HTML itu masih bisa ditambal perantara dengan mengganti teksnya,
tapi **QR code tidak bisa**: alamatnya sudah jadi piksel di dalam gambar PNG,
dan pelanggan yang memindainya akan dibawa ke alamat yang salah.

Cara baku Django untuk ini, USE_X_FORWARDED_HOST, sudah dicoba dan tidak
bekerja di sini — nginx milik PythonAnywhere menimpa X-Forwarded-Host dengan
host aslinya sebelum permintaan sampai ke aplikasi. Header apa pun yang dikirim
perantara akan kalah.

Jadi nama domainnya diambil dari setelan, bukan dari header. Setelan tidak bisa
ditimpa siapa pun di tengah jalan.

PUBLIC_HOST kosong = middleware ini tidak melakukan apa-apa, jadi pemasangan
yang tidak di balik perantara tidak berubah perilakunya.
"""

from django.conf import settings


class DomainPublik:
    """Menetapkan nama host permintaan ke PUBLIC_HOST, kalau diisi.

    Harus berada di urutan PERTAMA pada MIDDLEWARE: SecurityMiddleware di
    bawahnya sudah memakai get_host() untuk mengalihkan ke https, dan kalau
    nama hostnya diganti setelah itu, pengalihannya menunjuk alamat yang salah.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.nama = getattr(settings, "PUBLIC_HOST", "")

    def __call__(self, request):
        if self.nama:
            # Django mendahulukan HTTP_HOST di atas SERVER_NAME saat menyusun
            # get_host(), jadi satu baris ini cukup — termasuk untuk
            # build_absolute_uri() yang dipakai pembuat QR.
            request.META["HTTP_HOST"] = self.nama
        return self.get_response(request)
