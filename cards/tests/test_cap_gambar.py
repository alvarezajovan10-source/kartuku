"""Cap VORTEIZ pada gambar yang dibuat PIL benar-benar menempel.

Ada karena satu cacat DIAM yang lolos: alfa cap sempat dikalikan dua kali —
sekali sebagai warna, sekali lagi sebagai topeng paste() — sehingga 13% jadi
1,6%. Berkasnya tetap tertulis, ukurannya wajar, dan skripnya melapor sukses;
yang salah cuma tidak terlihat. Terukur waktu itu: 7 piksel berubah dari 1,3
juta. Tanpa tes ini, satu-satunya yang bisa menangkapnya adalah mata yang
kebetulan curiga.
"""
import os
import sys
import unittest

from django.conf import settings
from django.test import TestCase

sys.path.insert(0, os.path.join(settings.BASE_DIR, "tools"))

try:
    from PIL import Image

    import cap_gambar

    ADA_FONT = any(os.path.exists(j) for j in cap_gambar.FONT_CALON)
except Exception:  # pragma: no cover - alat sekali pakai, bukan bagian situs
    ADA_FONT = False


@unittest.skipUnless(ADA_FONT, "font tebal tidak ada di mesin ini")
class CapGambarTests(TestCase):
    def _kanvas(self, warna=(128, 128, 128)):
        import tempfile

        jalur = os.path.join(tempfile.mkdtemp(), "uji.jpg")
        Image.new("RGB", (900, 1200), warna).save(jalur, quality=95)
        return jalur

    def _beda(self, sebelum, sesudah):
        a = Image.open(sebelum).convert("L")
        b = Image.open(sesudah).convert("L")
        kena = sum(1 for x, y in zip(a.getdata(), b.getdata()) if abs(x - y) > 2)
        return kena / (a.width * a.height)

    def test_cap_benar_benar_mengubah_gambarnya(self):
        asal = self._kanvas()
        hasil = cap_gambar.beri_cap(asal, asal + ".cap.jpg")
        porsi = self._beda(asal, hasil)
        self.assertGreater(
            porsi, 0.015,
            "cap nyaris tidak mengubah apa pun — kemungkinan alfanya "
            "terkalikan dua kali lagi",
        )

    def test_cap_tidak_menutupi_gambarnya(self):
        """Batas atasnya sama pentingnya: galeri yang tertutup berhenti menjual."""
        asal = self._kanvas()
        hasil = cap_gambar.beri_cap(asal, asal + ".cap.jpg")
        self.assertLess(self._beda(asal, hasil), 0.35)

    def test_polanya_berulang_bukan_satu_cap(self):
        """Permintaan pemilik situs: banyak tanda seperti monogram."""
        self.assertGreaterEqual(cap_gambar.KOLOM, 3)
        asal = self._kanvas()
        hasil = cap_gambar.beri_cap(asal, asal + ".cap.jpg")
        b = Image.open(hasil).convert("L")
        # Tanda tersebar di sepertiga atas MAUPUN sepertiga bawah — satu cap
        # di tengah tidak akan memenuhi keduanya.
        atas = b.crop((0, 0, b.width, b.height // 3))
        bawah = b.crop((0, b.height * 2 // 3, b.width, b.height))
        for nama, potong in (("atas", atas), ("bawah", bawah)):
            with self.subTest(bagian=nama):
                self.assertGreater(max(potong.getdata()), 132)
