"""Penjaga template Birthday Magazine (renderer "bdaymag").

bdaymag.html, pelat static/img/bdaymag/*.webp, dan entri seed-nya
diturunkan dari desain Canva yang sama oleh dua skrip di tools/. Yang dijaga
di sini adalah sambungan di antara ketiganya — tempat yang bisa bergeser
sendiri-sendiri tanpa satu pun tes lain merah.
"""
import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from cards.management.commands.seed_templates import SEEDS
from cards.models import Template

AKAR = Path(settings.BASE_DIR)
HTML = AKAR / "cards" / "templates" / "cards" / "render" / "bdaymag.html"


def config():
    for slug, _nama, _kategori, cfg in SEEDS:
        if slug == "birthday-magazine":
            return cfg
    raise AssertionError("birthday-magazine tidak ada di SEEDS")


class SambunganTests(TestCase):
    def setUp(self):
        self.html = HTML.read_text(encoding="utf-8")
        self.cfg = config()

    def test_tiap_bingkai_dan_teks_di_config_ada_di_html(self):
        for f in self.cfg["frames"]:
            self.assertIn(f'{{% frame card editing "{f["key"]}" %}}', self.html, f["key"])
        for t in self.cfg["texts"]:
            self.assertIn(f'{{% t card "{t["key"]}" %}}', self.html, t["key"])

    def test_area_bingkai_menunjuk_hamparan_yang_ada(self):
        hamparan = set(re.findall(r'<section class="scene[^"]*" id="([^"]+)"', self.html))
        for f in self.cfg["frames"]:
            self.assertIn(f["area"], hamparan, f["key"])

    def test_id_hamparan_tidak_meminjam_milik_majalah_cinta(self):
        """Label tab editor (SCENE_LABELS) dikunci id untuk SEMUA template.

        Dengan id "sp1..sp9" template ini ikut berlabel "Love Note",
        "First Impression", dst. milik Majalah Cinta.
        """
        hamparan = re.findall(r'<section class="scene[^"]*" id="([^"]+)"', self.html)
        self.assertEqual(len(hamparan), 9)
        for sid in hamparan:
            self.assertFalse(sid.startswith("sp"), sid)
        editor = (AKAR / "static" / "js" / "alpine-editor.js").read_text(encoding="utf-8")
        for sid in hamparan:
            self.assertRegex(editor, rf"\b{sid}: \"", f"{sid} tidak punya label di SCENE_LABELS")

    def test_frame_tidak_menempel_di_elemen_yang_punya_style(self):
        """Di kartu terbit {% frame %} menulis atribut style sendiri (crop pembeli).

        Elemen dengan dua atribut style membuang yang kedua, jadi zoom & geser
        foto pembeli lenyap diam-diam. Posisi bingkai karena itu di .slot.
        """
        for tag in re.findall(r"<[a-z]+[^>]*\{% frame card editing[^>]*>", self.html):
            self.assertNotIn("style=", tag)
        for tag in re.findall(r"<[a-z]+[^>]*\{% el card editing[^>]*>", self.html):
            self.assertNotIn("style=", tag)

    def test_semua_pelat_ada(self):
        for nama in re.findall(r"img/bdaymag/([a-z0-9]+\.webp)", self.html):
            self.assertTrue((AKAR / "static" / "img" / "bdaymag" / nama).exists(), nama)

    def test_bawaan_teks_tidak_kosong(self):
        for t in self.cfg["texts"]:
            self.assertTrue(t["default"].strip(), t["key"])


class TampilTests(TestCase):
    def setUp(self):
        _slug, nama, kategori, cfg = next(s for s in SEEDS if s[0] == "birthday-magazine")
        Template.objects.create(slug="birthday-magazine", name=nama, category=kategori,
                                config=cfg, is_active=True)

    def test_halaman_contoh_dan_editor_terbuka(self):
        r = self.client.get(reverse("cards:preview", args=["birthday-magazine"]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'data-stage="majalah"')
        self.assertContains(r, "bdaymag.js")
        r = self.client.get(reverse("cards:editor_frame", args=["birthday-magazine"]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'data-frame="f_sampul"')
        self.assertContains(r, 'data-edit="cover_name"')


JS = AKAR / "static" / "js" / "render" / "bdaymag.js"
CSS = AKAR / "static" / "css" / "render" / "bdaymag.css"
EDITOR = AKAR / "static" / "js" / "alpine-editor.js"


class BalikHalamanTests(TestCase):
    """Revisi 11 Okt 2026: halaman yang balik ke sampul, pelat yang hilang
    di halaman 8-9, kedipan halaman lama, dan muka lembar tercermin di Safari.
    Semuanya lolos tes lain karena sumbernya urutan skrip & mesin browser."""

    def setUp(self):
        self.js = JS.read_text(encoding="utf-8")
        self.css = CSS.read_text(encoding="utf-8")

    def test_hamparan_awal_dibaca_sendiri_dari_url(self):
        # card-frame.js dimuat `defer` = jalan SESUDAH bdaymag.js. Kalau mesin
        # menunggu .active darinya, ia mengira sampul yang terbuka: pelat
        # hamparan yang tampil tidak di-decode dan panah melompat ke hal 2.
        self.assertIn('new URLSearchParams(location.search).get("scene")', self.js)
        self.assertIn("pasangAktif(hamparanAwal())", self.js)

    def test_halaman_diingat_untuk_muat_ulang(self):
        self.assertIn("sessionStorage.setItem(KUNCI", self.js)

    def test_editor_diberi_tahu_halaman_yang_dibuka(self):
        # Tanpa ini pratinjau yang dimuat ulang sesudah simpan foto/teks
        # kembali ke sampul (editor memakai ?scene= miliknya sendiri).
        self.assertIn('type: "halaman"', self.js)
        self.assertIn('data.type === "halaman"', EDITOR.read_text(encoding="utf-8"))

    def test_tetangga_digambar_supaya_tidak_berkedip(self):
        self.assertIn(".scene.dekat:not(.active)", self.css)

    def test_sisi_lembar_ditukar_sendiri_bukan_backface(self):
        # WebKit tidak mematuhi backface-visibility di sini: muka lembar
        # tampak TERCERMIN dari belakang. Pertukaran di 90 derajat dijaga JS.
        self.assertIn("muka: a > -90 ? 1 : 0", self.js)
        self.assertIn("ctx.sisi[1].style.opacity = g.balik", self.js)

    def test_putaran_hanya_menggerakkan_transform_dan_opacity(self):
        # Custom property per bingkai (--gelap lama) memaksa repaint halaman
        # penuh tiap bingkai — sumber "tidak smooth".
        self.assertNotIn("--gelap", self.js)
        self.assertNotIn("--gelap", self.css)


class Revisi11OktTests(TestCase):
    """Semua teks sampul bisa disunting; latar playlist redup dan penanda
    "+ foto"-nya tidak menimpa kartu lagu."""

    def test_semua_teks_sampul_bisa_disunting(self):
        kunci = {t["key"] for t in config()["texts"]}
        for k in ("cover_masthead", "cover_magazine", "cover_edition", "cover_hbd",
                  "cover_kicker", "cover_age", "cover_name", "cover_tag"):
            self.assertIn(k, kunci)

    def test_latar_playlist_redup_dan_penandanya_di_bawah_pelat(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertRegex(html, r'class="bingkai[^"]*\blatar\b[^"]*"[^>]*\{% frame card editing "f_lagu_latar" %\}')
        css = CSS.read_text(encoding="utf-8")
        self.assertIn(".bingkai.latar img { filter: brightness(", css)
        # Di bawah pelat (z 2), bukan di atasnya (z 3 milik .ketuk biasa).
        self.assertIn(".bingkai.latar .ketuk { z-index: 1; }", css)

    def test_surat_berfont_tangan_dan_tidak_menimpa_penutup(self):
        html = HTML.read_text(encoding="utf-8")
        for k in ("letter_title", "letter_body", "letter_close", "sender"):
            self.assertRegex(html, r'class="tx f-tangan"\{% el card editing "' + k + '"')
        m = re.search(r'--y:([\d.]+)%;--w:[\d.]+%;--h:([\d.]+)%[^"]*"><p class="tx f-tangan"\{% el card editing "letter_body"', html)
        self.assertLessEqual(float(m.group(1)) + float(m.group(2)), 85.5)

    def test_judul_editor_dan_playlist_bertulisan_tangan(self):
        html = HTML.read_text(encoding="utf-8")
        for k in ("editor_title", "editor_title2", "playlist_name", "playlist_word"):
            self.assertRegex(html, r'--d-w:700[^"]*"><p class="tx f-tangan"\{% el card editing "' + k + '"')


class HalamanProdukTests(TestCase):
    """Halaman produk Birthday Magazine tanpa kartu hidup (12 Okt 2026):
    galeri langsung dari potret ekspor Canva."""

    def setUp(self):
        _slug, nama, kategori, cfg = next(s for s in SEEDS if s[0] == "birthday-magazine")
        Template.objects.create(slug="birthday-magazine", name=nama, category=kategori,
                                config=cfg, is_active=True)

    def test_galeri_langsung_tanpa_pratinjau_hidup(self):
        self.assertTrue(config().get("galeri_saja"))
        r = self.client.get(reverse("cards:template_detail", args=["birthday-magazine"]))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "?sematan=1")
        self.assertNotContains(r, "data-catatan-hidup")
        self.assertContains(r, '<span class="lst-kini">1</span> / 9')
        self.assertContains(r, 'class="lst-slide is-on" data-i="0"')


class FotoGagalDimuatTests(TestCase):
    """14 Okt 2026: hosting perantara menolak sebagian dari puluhan gambar
    kartu (507). Kepala kartu wajib membawa skrip coba-ulang."""

    def test_kepala_kartu_membawa_coba_ulang_gambar(self):
        kepala = (AKAR / "cards" / "templates" / "cards" / "_card_head.html").read_text(encoding="utf-8")
        self.assertIn('window.addEventListener("error"', kepala)
        # load milik elemen tidak sampai ke window — harus di document.
        self.assertIn('document.addEventListener("load"', kepala)
        self.assertIn('--pelat', kepala)
