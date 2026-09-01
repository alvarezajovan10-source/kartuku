"""Ajakan memutar HP untuk kartu MENDATAR.

Yang dijaga di sini satu bug yang SUDAH TAYANG sebelum ketahuan.

Gerbang Game 8-Bit cuma memakai `@media (orientation: portrait)`. Halaman
produk menyematkan kartu contoh di iframe berukuran 678x848 — tegak, tapi itu
bukan HP penerima. Akibatnya halaman jualan menampilkan "MIRINGKAN HP-MU"
menutupi kartu contohnya, tepat di halaman yang paling menjual, dan tidak ada
yang menyadarinya karena di HP maupun di laptop halaman KARTU-nya benar.

Penjaganya harus di JS, bukan di template: kartunya bisa disematkan di halaman
mana pun, termasuk yang belum ada.
"""

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from cards.management.commands.seed_templates import SEEDS
from cards.models import CardType, GiftCard, Template


def berkas(jalur):
    with open(settings.BASE_DIR / jalur) as fh:
        return fh.read()


class PenjagaIframeTests(TestCase):
    """Kedua kartu mendatar harus punya penjaga yang sama."""

    def test_gerbang_bersama_menjaga_iframe(self):
        isi = berkas("cards/templates/cards/_orientasi.html")
        self.assertIn("window.self !== window.top", isi)
        self.assertIn("pergi", isi)

    def test_game8bit_ikut_dijaga(self):
        """Template inilah yang bug-nya tayang."""
        isi = berkas("static/js/render/game8bit.js")
        self.assertIn("window.self !== window.top", isi)

    def _z(self, berkas_css):
        import re
        return [int(z) for z in re.findall(r"z-index:\s*(\d+)", berkas(berkas_css))]

    def test_gerbang_menembus_tombol_lagu_dan_cap(self):
        """Tombol lagu duduk di z-index 80. Gerbang di bawah itu ditembus, dan
        penerima melihat tombol mengambang di atas layar yang menyuruhnya
        memutar HP."""
        gerbang = self._z("static/css/orientasi.css")[0]
        tertinggi = max(self._z("static/css/bgm.css")
                        + self._z("static/css/watermark.css"))
        self.assertGreater(gerbang, tertinggi,
                           f"gerbang {gerbang} tidak di atas perkakas {tertinggi}")

    def test_tombol_layar_penuh_justru_DI_ATAS_gerbang(self):
        """Satu-satunya perkakas yang dikecualikan, dan disengaja.

        Memilih lagu sambil disuruh memutar HP tidak masuk akal, jadi tombol
        lagu memang ditembus. Layar penuh kebalikannya: menekannya DULU lalu
        memutar HP adalah urutan yang wajar. Dan karena Sweetflix satu-satunya
        template bergerbang, tanpa pengecualian ini ia jadi satu-satunya kartu
        yang kehilangan tombol layar penuhnya di HP tegak sementara tujuh
        lainnya punya — persis yang dilaporkan pemilik situs."""
        gerbang = self._z("static/css/orientasi.css")[0]
        tombol = max(self._z("static/css/fullscreen.css"))
        self.assertGreater(tombol, gerbang,
                           f"tombol {tombol} tertelan gerbang {gerbang}")

    def test_semua_kartu_mendatar_punya_tombol_layar_penuh(self):
        """Penjaga arah sebaliknya: gerbang boleh ditambahkan ke template lain,
        asal tidak ada yang kehilangan tombolnya."""
        import pathlib
        akar = settings.BASE_DIR / "cards/templates/cards/render"
        for f in sorted(pathlib.Path(akar).glob("*.html")):
            if f.name.startswith("_"):
                continue
            isi = f.read_text()
            if "_orientasi.html" in isi:
                with self.subTest(kartu=f.name):
                    self.assertIn("_fullscreen.html", isi)


class SweetflixMemakaiGerbangTests(TestCase):
    def setUp(self):
        config = next(c for s, _n, _k, c in SEEDS if s == "sweetflix")
        self.template = Template.objects.create(
            slug="sweetflix", name="Sweetflix", category=CardType.LOVE_STORY, config=config)
        self.kartu = GiftCard.objects.create(
            template=self.template, category=CardType.LOVE_STORY,
            status=GiftCard.Status.PAID, paid_at=timezone.now(),
            recipient_name="Riana", sender_name="Rocky")

    def test_kartu_terbit_memuat_gerbang_dan_tombol_layar_penuh(self):
        isi = self.client.get(f"/{self.kartu.id}/").content.decode()
        self.assertIn('id="putarLayar"', isi)
        self.assertIn('id="fsFab"', isi)      # tombol layar penuh, kiri bawah

    def test_tombol_layar_penuh_tidak_ditelan_bar_pratinjau(self):
        """Bar pratinjau melintang di dasar layar dengan z-index 9999, dan di
        HP ia membungkus jadi dua-tiga baris. Terukur di 780x390:
        elementFromPoint di titik tombol mengembalikan .preview-bar — tombolnya
        ada, terlihat, tapi tidak bisa disentuh sama sekali.

        Tingginya tidak bisa ditebak dari media query karena bergantung pada
        jumlah baris, jadi diukur di JS dan dikirim lewat --bar-h."""
        css = (settings.BASE_DIR / "static/css/preview-bar.css").read_text()
        blok = css.split(".fs-fab{", 1)
        self.assertEqual(len(blok), 2, ".fs-fab tidak diangkat di atas bar")
        self.assertIn("var(--bar-h", blok[1].split("}", 1)[0])

        html = (settings.BASE_DIR
                / "cards/templates/cards/_preview_bar.html").read_text()
        self.assertIn('setProperty(\n      "--bar-h"', html)
        # Putar HP = jumlah baris berubah = tinggi bar berubah.
        for peristiwa in ("resize", "orientationchange"):
            self.assertIn(f'"{peristiwa}", ukur', html)

    def test_gerbang_menyarankan_tablet_atau_laptop(self):
        """Kartu 16:9 di HP tetap kecil walau sudah dimiringkan — 693x390 di
        iPhone, dan cuma 533x300 begitu bilah Safari muncul. Gerbang ini titik
        satu-satunya tempat penerima masih mau membaca sebelum masuk kartu."""
        isi = self.client.get(f"/{self.kartu.id}/").content.decode()
        self.assertIn("putar-saran", isi)
        self.assertIn("tablet atau laptop", isi)

    def test_saran_lebih_redup_daripada_ajakan_utama(self):
        """Ini SARAN, bukan syarat: tombol "Lanjut saja" tetap ada. Kalau
        ukurannya menyamai `.putar-sub`, gerbangnya terbaca seperti dua
        perintah dan penerima ber-HP merasa kartunya memang bukan untuknya."""
        import re
        css = berkas("static/css/orientasi.css")

        def ukuran(kelas):
            blok = re.search(rf"\.{kelas}\s*{{([^}}]*)}}", css).group(1)
            return float(re.search(r"font-size:\s*([\d.]+)px", blok).group(1))

        self.assertLess(ukuran("putar-saran"), ukuran("putar-sub"))

    def test_kartu_terbit_tidak_memuat_bar_pratinjau(self):
        """Penjaga untuk perbaikan di atas: kalau bar itu suatu saat ikut
        terbit di kartu berbayar, --bar-h jadi 0 dan tombolnya tertelan lagi."""
        isi = self.client.get(f"/{self.kartu.id}/").content.decode()
        self.assertNotIn("preview-bar", isi)
