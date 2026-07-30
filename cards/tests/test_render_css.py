"""Penjaga invarian tampilan kartu.

Ada karena bug nyata dan mahal: kartu yang disunting di HP berubah tata
letaknya saat dibuka di laptop — huruf pindah baris. Penyebabnya font memakai
satuan viewport sementara lebar kontainer tidak, jadi keduanya tumbuh dengan
laju berbeda.

Perbaikannya struktural (kanvas kanonis 390px + penskalaan), tapi mudah
dirusak lagi tanpa sengaja oleh satu baris CSS. Tes di sini mengunci
aturannya supaya kalau ada yang menambahkan `vw` atau media query lebar,
suite langsung merah — bukan pembeli yang menemukannya.
"""

import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase

CSS_KARTU = [
    "css/render/birthday.css",
    "css/render/scrapbook.css",
    "css/kanvas.css",
]


def baca(nama):
    return (Path(settings.BASE_DIR) / "static" / nama).read_text()


class InvarianCssKartuTests(TestCase):
    def test_tidak_ada_satuan_viewport_untuk_tata_letak(self):
        """`vw`/`vh` membuat ukuran ikut lebar layar — itu akar bugnya.

        Pengecualian: `100vh` pada latar <body> yang memang harus memenuhi
        layar dan berada di luar kanvas kartu.
        """
        pola = re.compile(r"[\d.]+(vw|vh|dvh|svh|lvh)\b")
        for nama in CSS_KARTU:
            for nomor, baris in enumerate(baca(nama).splitlines(), 1):
                if not pola.search(baris):
                    continue
                boleh = "min-height:100vh" in baris.replace(" ", "")
                self.assertTrue(
                    boleh,
                    f"{nama}:{nomor} memakai satuan viewport — pakai "
                    f"calc(N*var(--w0)) supaya tata letaknya tetap sama "
                    f"di semua perangkat.\n  {baris.strip()}",
                )

    def test_tidak_ada_media_query_berbasis_lebar(self):
        """Media query dievaluasi terhadap layar NYATA, bukan kanvas kanonis.

        Jadi ia menyala di HP dan mati di laptop — persis ketidaksesuaian
        yang sedang dihilangkan. Hanya prefers-reduced-motion yang boleh.
        """
        for nama in CSS_KARTU:
            for nomor, baris in enumerate(baca(nama).splitlines(), 1):
                if "@media" not in baris:
                    continue
                self.assertNotIn(
                    "width",
                    baris,
                    f"{nama}:{nomor} memakai media query lebar — lipat isinya "
                    f"jadi permanen.\n  {baris.strip()}",
                )

    def test_ukuran_font_dasar_dikunci(self):
        """Tanpa ini, setelan ukuran teks di browser penerima dan font
        boosting Chrome Android mengubah pemenggalan baris."""
        for nama in CSS_KARTU:
            isi = baca(nama).replace(" ", "")
            self.assertIn("font-size:16px", isi, f"{nama}: ukuran font dasar tidak dikunci")
            self.assertIn("text-size-adjust:100%", isi, f"{nama}: text-size-adjust hilang")

    def test_lebar_kanonis_terdefinisi(self):
        for nama in CSS_KARTU:
            self.assertIn("--w0", baca(nama), f"{nama}: --w0 tidak terdefinisi")

    def test_lebar_kanonis_sama_dengan_di_javascript(self):
        """Kalau CSS dan JS berbeda, kartu terpotong atau ada celah kosong."""
        js = (Path(settings.BASE_DIR) / "static" / "js" / "card-stage.js").read_text()
        self.assertRegex(js, r"W0\s*=\s*390")
        for nama in CSS_KARTU:
            self.assertRegex(baca(nama).replace(" ", ""), r"--w0:390px")

    def test_gaya_pilihan_user_tidak_dikalahkan_spesifisitas(self):
        """Aturan ber-id sempat mengalahkan lapisan gaya user, sehingga
        pilihan ukuran & warna pembeli untuk judul babak tidak pernah
        berlaku — di semua lebar layar, bukan cuma di HP."""
        isi = baca("css/render/birthday.css")
        for selector in [
            "#message .scene-head",
            "#flower .scene-head",
            "#cake .scene-head",
            "#song .scene-head",
            "#gallery .scene-head",
        ]:
            cocok = re.search(re.escape(selector) + r"\{([^}]*)\}", isi)
            self.assertIsNotNone(cocok, f"{selector} hilang dari CSS")
            blok = cocok.group(1)
            self.assertNotIn(
                "font-size",
                blok,
                f"{selector} menyetel font-size dan mengalahkan .scene-head "
                f"milik lapisan gaya user",
            )
            self.assertNotIn("color:", blok, f"{selector} menyetel color dan mengalahkan gaya user")

    def test_ukuran_font_yang_bisa_disunting_memakai_fs(self):
        """Tiap elemen yang ukurannya bisa diatur user wajib mengalikan --fs."""
        isi = baca("css/render/birthday.css")
        for selector in ["#cover h1", "#hub .hub-title", ".scene-head"]:
            aturan = re.findall(
                re.escape(selector) + r"\{([^}]*font-size[^}]*)\}", isi
            )
            self.assertTrue(aturan, f"{selector}: tidak ada aturan font-size")
            self.assertIn(
                "var(--fs",
                aturan[-1],
                f"{selector}: aturan font-size terakhir mengabaikan pilihan "
                f"ukuran user",
            )


class StrukturKanvasTests(TestCase):
    """Kanvas kanonis harus terpasang di SEMUA renderer, bukan sebagian.

    Kalau satu renderer terlewat, kartu dari template itu diam-diam kembali
    berperilaku lama — berubah tata letaknya antar perangkat.
    """

    RENDERER = [
        ("birthday", "frame"),
        ("scrapbook", "flow"),
        ("kanvas", "flow"),
    ]

    def setUp(self):
        from cards.models import CardType, GiftCard, Template

        self.kartu = {}
        for nama, _mode in self.RENDERER:
            template = Template.objects.create(
                slug=f"t-{nama}", name=nama, category=CardType.BIRTHDAY,
                config={"renderer": nama},
            )
            self.kartu[nama] = GiftCard.objects.create(
                template=template, category=CardType.BIRTHDAY,
                youtube_video_id="dQw4w9WgXcQ",
                status=GiftCard.Status.PAID,
            )

    def _html(self, nama):
        from django.urls import reverse

        return self.client.get(
            reverse("cards:public", args=[self.kartu[nama].id])
        ).content.decode()

    def test_semua_renderer_memakai_kanvas_kanonis(self):
        for nama, mode in self.RENDERER:
            with self.subTest(renderer=nama):
                html = self._html(nama)
                self.assertIn(f'data-stage="{mode}"', html)
                self.assertIn('id="card-viewport"', html)
                self.assertIn('id="card-stage"', html)
                self.assertIn("card-stage.js", html)

    def test_tombol_melayang_di_luar_kanvas(self):
        """Tombol musik & layar penuh tidak boleh ikut diskalakan — kalau di
        dalam kanvas, ukurannya mengecil bersama kartu di layar sempit."""
        for nama, _mode in self.RENDERER:
            with self.subTest(renderer=nama):
                html = self._html(nama)
                tutup = html.rindex("</div></div>")
                for tombol in ['id="bgmFab"', 'id="fsFab"']:
                    self.assertIn(tombol, html)
                    self.assertGreater(
                        html.index(tombol), tutup,
                        f"{tombol} berada di dalam kanvas — akan ikut terskala",
                    )


class KanvasMenghormatiGayaTests(TestCase):
    """Kanvas Klasik dulu mengabaikan SEMUA pilihan gaya pembeli.

    Berkas CSS-nya membaca --title-size/--message-font/dst. yang tidak pernah
    dihasilkan siapa pun, dan templatenya membaca card.style_css serta
    card.style_clean.bg yang tidak ada di model. Karena renderer ini dipakai
    tiga dari empat kategori produk, pembeli Anniversary, Love Story, dan
    Lamaran memilih font lalu tidak terjadi apa-apa.
    """

    def setUp(self):
        from cards.models import CardType, GiftCard, Template

        template = Template.objects.create(
            slug="kanvas-gaya", name="Kanvas", category=CardType.ANNIVERSARY,
            config={"renderer": "kanvas"},
        )
        self.card = GiftCard.objects.create(
            template=template, category=CardType.ANNIVERSARY,
            recipient_name="Nadia", sender_name="Raka",
            message="Selamat anniversary",
            status=GiftCard.Status.PAID,
            style={"elements": {
                "recipient": {"size": 1.5, "color": "#112233", "align": "left"},
                "message": {"font": "caveat", "italic": True},
            }},
        )

    def _html(self):
        from django.urls import reverse

        return self.client.get(
            reverse("cards:public", args=[self.card.id])
        ).content.decode()

    def test_ukuran_dan_warna_pilihan_user_ikut_terender(self):
        html = self._html()
        self.assertIn("--fs:1.5", html.replace(" ", ""))
        self.assertIn("--c:#112233", html.replace(" ", ""))

    def test_css_memakai_konvensi_variabel_bersama(self):
        # Komentar dibuang dulu — di sana variabel lama memang masih disebut
        # untuk menjelaskan sejarahnya, dan itu bukan pemakaian.
        isi = re.sub(r"/\*.*?\*/", "", baca("css/kanvas.css"), flags=re.S)
        for lama in ["--title-size", "--message-font", "--signature-color", "--kv-bg"]:
            self.assertNotIn(lama, isi, f"{lama} sudah tidak dihasilkan siapa pun")
        for baru in ["var(--fs", "var(--f,", "var(--c,", "var(--al,"]:
            self.assertIn(baru, isi, f"kanvas.css belum memakai {baru}")

    def test_tidak_membaca_properti_model_yang_tidak_ada(self):
        from pathlib import Path

        from django.conf import settings

        for nama in ["kanvas.html", "_kanvas_body.html"]:
            isi = (
                Path(settings.BASE_DIR) / "cards" / "templates" / "cards" / "render" / nama
            ).read_text()
            for mati in ["card.style_css", "style_clean.bg", "photo_shape"]:
                self.assertNotIn(mati, isi, f"{nama} masih membaca {mati} yang tidak ada")


class KanvasTidakBolehBerumpanBalikTests(TestCase):
    """Pembungkus kanvas tidak boleh meregangkan stage.

    Bug nyata: tinggi pembungkus dihitung DARI tinggi stage, sementara
    flexbox bawaan (align-items: stretch) meregangkan stage setinggi
    pembungkus. Umpan baliknya berputar — ukur, regangkan, ukur lagi —
    mengalikan faktor skala tiap putaran sampai kartunya menyusut habis.

    Hanya muncul saat skala bukan 1, jadi laptop (skala pas 1,0) terlihat
    normal sementara HP gelap total tanpa isi.
    """

    def test_pembungkus_tidak_meregangkan_stage(self):
        css = baca("css/card-stage.css")
        blok = re.search(r"#card-viewport\s*\{([^}]*)\}", css).group(1)
        self.assertIn(
            "align-items: flex-start", blok,
            "#card-viewport harus align-items: flex-start — `stretch` bawaan "
            "membuat tinggi stage dan pembungkus saling mengejar",
        )

    def test_js_berhenti_kalau_tinggi_tidak_berubah(self):
        js = (Path(settings.BASE_DIR) / "static" / "js" / "card-stage.js").read_text()
        self.assertIn("terakhir", js, "penjaga anti-perulangan hilang dari card-stage.js")
