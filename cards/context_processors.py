from django.conf import settings


def payment(request):
    """Sediakan `payment_ready` untuk semua template.

    Selama `MIDTRANS_SERVER_KEY` kosong, tidak ada pembayaran QRIS di situs ini:
    pembeli membayar di Lynk.id lalu menempel REF ID dari email struknya. Teks
    yang menjanjikan "scan QRIS" membuat pembeli menunggu QR yang tidak akan
    pernah muncul.

    Dibuat sebagai flag dan bukan teks mati supaya kalimatnya kembali sendiri
    begitu Midtrans diaktifkan — kalau ditulis ulang jadi teks Lynk permanen,
    menyalakan QRIS nanti berarti berburu kalimat yang tersebar di banyak berkas.
    View `pay` sudah memakai nama yang sama, jadi tidak ada yang berubah di sana.
    """
    return {"payment_ready": bool(settings.MIDTRANS_SERVER_KEY)}
