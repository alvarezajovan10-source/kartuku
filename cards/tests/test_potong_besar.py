"""Bingkai boleh minta potongan lebih panjang lewat "sisi" di config.

Ada DUA batas yang harus sepakat, dan itu yang hampir terlewat: kotak crop di
editor (alpine-editor.js) dan pengecil di server (validate_and_compress_photo).
Menaikkan salah satunya saja percuma — editor memotong 3200 px lalu server
mengecilkannya kembali ke 2400, dan tidak ada yang menyadarinya karena
fotonya tetap tampil, cuma lebih lembut.
"""

import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from cards.utils import MAX_DIMENSION, MAX_DIMENSION_BESAR, MAX_DIMENSION_PINTA
from cards.utils import validate_and_compress_photo


def foto(lebar, tinggi):
    buf = io.BytesIO()
    Image.new("RGB", (lebar, tinggi), (120, 90, 70)).save(buf, "JPEG", quality=80)
    return SimpleUploadedFile("f.jpg", buf.getvalue(), content_type="image/jpeg")


def sisi_hasil(berkas):
    return max(Image.open(berkas).size)


class PotongBesarTests(TestCase):
    def test_tanpa_pinta_tetap_seperti_dulu(self):
        """Template lain tidak boleh ikut berubah."""
        self.assertEqual(sisi_hasil(validate_and_compress_photo(foto(4000, 3000))),
                         MAX_DIMENSION)
        self.assertEqual(
            sisi_hasil(validate_and_compress_photo(foto(4000, 3000), besar=True)),
            MAX_DIMENSION_BESAR)

    def test_pinta_dihormati_server(self):
        """Inilah batas kedua. Tanpa ini editor memotong 3200 lalu server
        mengecilkannya lagi ke 2400, dan perbaikannya tidak berefek apa pun."""
        hasil = validate_and_compress_photo(foto(4000, 3000), besar=True, sisi_pinta=3200)
        self.assertEqual(sisi_hasil(hasil), 3200)

    def test_pinta_tidak_bisa_mengecilkan(self):
        """Angka di bawah bawaan diabaikan — "sisi" untuk MENAIKKAN saja."""
        hasil = validate_and_compress_photo(foto(4000, 3000), besar=True, sisi_pinta=800)
        self.assertEqual(sisi_hasil(hasil), MAX_DIMENSION_BESAR)

    def test_pinta_dibatasi_atas(self):
        """Config yang salah ketik tidak boleh membuat server menyimpan foto
        raksasa — disk hosting-nya 512MB."""
        hasil = validate_and_compress_photo(foto(9000, 6000), besar=True, sisi_pinta=99999)
        self.assertEqual(sisi_hasil(hasil), MAX_DIMENSION_PINTA)
