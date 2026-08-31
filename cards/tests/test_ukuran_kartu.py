"""Kartu harus diukur dari bidang yang BENAR-BENAR terlihat.

Di Safari iPhone bilah alamat memakan tinggi layar tanpa mengubah
clientHeight. Kartu yang dihitung dari clientHeight jadi lebih besar
daripada yang muat, dan bagian bawahnya bersembunyi di balik bilah.
Terhitung untuk iPhone 15 mendatar (844x390): lebar TIDAK PERNAH jadi
pembatas (844/960 = 0,879 lawan 390/540 = 0,722), jadi satu-satunya yang
menentukan besar kartu di sana adalah tinggi yang tersisa.
"""
from django.conf import settings
from django.test import SimpleTestCase


def js():
    return (settings.BASE_DIR / "static/js/card-stage.js").read_text()


class UkuranDariBidangTerlihatTests(SimpleTestCase):
    def test_tinggi_diambil_dari_visual_viewport(self):
        isi = js()
        self.assertIn("window.visualViewport", isi)
        self.assertIn("vv.height", isi)
        # clientHeight tetap jadi cadangan — visualViewport tidak ada di
        # peramban lama, dan kartu tidak boleh ikut hilang bersamanya.
        self.assertIn("root.clientHeight", isi)

    def test_mendengar_visual_viewport_bukan_cuma_window(self):
        """Bilah alamat Safari yang menyusut TIDAK memicu resize pada window.
        Tanpa pendengar ini, ruang yang baru dilepas Safari dibiarkan kosong
        dan kartunya tetap kecil sampai layar diputar."""
        isi = js().split("window.addEventListener(\"resize\", fit)", 1)[1]
        self.assertIn('visualViewport.addEventListener("resize", fit)', isi)

    def test_semua_babak_memakai_tinggi_yang_sama(self):
        """Kalau satu babak lupa dan tetap membaca clientHeight, cacatnya
        muncul cuma di satu bentuk kartu dan paling sulit ditemukan."""
        isi = js()
        self.assertNotIn("root.clientHeight || window.innerHeight || H0", isi)
        self.assertIn("hNyata", isi)
