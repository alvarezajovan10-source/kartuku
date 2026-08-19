"""Empat bug editor yang ditemukan user saat uji coba sungguhan.

Keempatnya lolos dari test yang ada karena semuanya soal perilaku di browser,
bukan respons server. Test di sini menjaga kondisi yang bisa diperiksa dari
sumbernya — tidak sempurna, tapi menangkap justru cara masing-masing bug bisa
kembali.
"""

import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from cards.models import CardType, Template


def baca(nama):
    return (Path(settings.BASE_DIR) / nama).read_text(encoding="utf-8")


def tanpa_komentar_django(html):
    """Buang {% comment %}…{% endcomment %} sebelum memeriksa isi halaman.

    Komentar Django tidak ikut ke browser, tapi ADA di berkas template —
    dan komentar yang menjelaskan kenapa sesuatu dicabut hampir selalu
    menyebut nama benda itu. Tanpa penyaring ini, assertNotIn justru gagal
    karena penjelasannya sendiri.
    """
    return re.sub(r"{%\s*comment\s*%}.*?{%\s*endcomment\s*%}", "", html, flags=re.S)


def tanpa_komentar_css(css):
    """Buang /* … */ sebelum memeriksa isi CSS.

    Komentar di berkas ini panjang dan menyebut nilai-nilai yang justru sudah
    TIDAK dipakai lagi ("dulu calc(100vh - 72px), sekarang …"). Memeriksa CSS
    mentah membuat penjelasan itu sendiri yang menggagalkan tesnya.
    """
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def di_luar_media(css, selektor):
    """True kalau `selektor` berada di tingkat teratas, bukan di dalam @media.

    Dihitung dari keseimbangan kurung kurawal sebelum selektornya — cara yang
    tidak peduli pada spasi, urutan, atau komentar yang disisipkan belakangan.
    """
    bersih = tanpa_komentar_css(css)
    posisi = bersih.index(selektor)
    depan = bersih[:posisi]
    return depan.count("{") == depan.count("}")


class HeaderEditorTests(TestCase):
    """Bug 1 — chrome situs mencuri ruang & perhatian di halaman editor.

    Dua keluhan berbeda, satu akar: header dan tautan keluar sama-sama duduk
    di jalur yang dipakai orang untuk mengedit.
    """

    def setUp(self):
        Template.objects.create(
            slug="uji", name="Uji", category=CardType.BIRTHDAY,
            config={"renderer": "birthday"},
        )

    def test_halaman_editor_menandai_dirinya(self):
        isi = self.client.get(reverse("cards:editor", args=["uji"])).content.decode()
        self.assertIn('<body class="is-editor"', isi)

    def test_halaman_lain_tidak_ikut_tertandai(self):
        """Hook body_class harus kosong di tempat lain — kalau bocor, header
        situs ikut hilang di halaman jualan."""
        for nama in ["landing", "page_templates", "page_pricing"]:
            with self.subTest(halaman=nama):
                isi = self.client.get(reverse(f"cards:{nama}")).content.decode()
                self.assertNotIn("is-editor", isi)

    def test_header_disembunyikan_di_semua_lebar(self):
        """Bukan cuma di desktop — itu versi lamanya.

        Ambang 941px dulu dipakai karena pemicunya dianggap tombol "Buat
        Kartu" (.header-cta), yang memang sudah display:none di bawah 941px.
        Ternyata di HP masalahnya lain dan lebih besar: .site-header
        position:sticky, jadi pilnya MENGAMBANG di atas pratinjau — dan di HP
        (.ed column-reverse) pratinjau justru yang duduk paling atas. Kalau
        aturan ini kembali terkurung di dalam @media, pil itu balik menutupi
        kartu yang sedang dikerjakan.
        """
        css = baca("static/css/app.css")
        self.assertIn("body.is-editor .site-header { display: none; }", css)
        self.assertTrue(
            di_luar_media(css, "body.is-editor .site-header"),
            "aturan header editor terkurung di dalam @media lagi",
        )

    def test_tinggi_editor_tidak_lagi_menyisihkan_ruang_header(self):
        """Pasangan yang wajib. Selama header masih mungkin muncul, `.ed`
        memakai calc(100vh - 72px) supaya footer tidak menyembul. Karena
        header sekarang tidak pernah ada di halaman ini, sisa 72px itu jadi
        pita kosong di bawah editor — dan itu regresi yang tidak terlihat di
        test lain."""
        css = baca("static/css/app.css")
        blok = css[css.index("\n.ed {"):]
        blok = blok[:blok.index("\n}")]
        self.assertIn("height: 100vh;", blok)
        self.assertNotIn("calc(100vh - 72px)", tanpa_komentar_css(css))

    def test_footer_disembunyikan_di_desktop(self):
        """Footer punya masalah yang sama persis dengan header: dirender di
        luar {% block body %}. Di desktop tanpa baris ini editor bukan layar
        penuh — ada footer gelap menggantung di bawah dan halaman bisa digulir
        menjauh dari kartunya.

        Di HP footer sengaja DIBIARKAN: ia tidak mengambang, duduk setelah
        tombol "Generate Link", dan catatan pembayarannya berguna dibaca tepat
        sebelum tombol itu ditekan.
        """
        css = baca("static/css/app.css")
        self.assertIn("body.is-editor .site-footer { display: none; }", css)
        self.assertFalse(
            di_luar_media(css, "body.is-editor .site-footer"),
            "footer editor kini disembunyikan di HP juga — disengaja?",
        )

    def test_tautan_keluar_dicabut_dari_panel(self):
        """Kebalikan dari test lamanya, dan itu memang keputusan yang berubah.

        Dulu "← Template lain" dipertahankan sebagai satu-satunya jalan keluar
        setelah header disembunyikan. Di HP tautan itu duduk paling atas di
        panel — yaitu TEPAT DI BAWAH pratinjau, persis di jalur jempol yang
        menggulir turun dari kartu ke kontrolnya — jadi ia lebih sering
        tertekan tanpa sengaja daripada dipakai. Ongkos salah tekannya besar:
        drafnya tersimpan, tapi tidak ada jalan kembali ke draf itu.

        Jalan keluar sekarang tombol Back browser. Kalau suatu saat pintu
        keluar di dalam halaman dibutuhkan lagi, tempatnya di BAWAH tombol
        "Generate Link".
        """
        isi = self.client.get(reverse("cards:editor", args=["uji"])).content.decode()
        self.assertNotIn("Template lain", tanpa_komentar_django(isi))
        self.assertNotIn('class="ed-back"', isi)


class GulirPratinjauTests(TestCase):
    """Bug 2 — kartu melompat balik ke sampul tiap kali foto diunggah.

    Halamannya tidak pernah refresh; yang dimuat ulang adalah iframe pratinjau.
    `?scene=` hanya menolong template berbabak — Scrapbook dan Kanvas adalah
    kartu gulir panjang, jadi posisinya hilang.
    """

    def test_posisi_gulir_disimpan_sebelum_memuat_ulang(self):
        js = baca("static/js/alpine-editor.js")
        blok = js.split("reloadFrame: function", 1)[1][:900]
        self.assertIn("scrollY", blok, "posisi gulir tidak dibaca sebelum reload")
        self.assertIn("scrollTo", blok, "posisi gulir tidak dikembalikan")

    def test_pemulihan_menunggu_muatan_baru(self):
        """Memanggil scrollTo sebelum iframe selesai memuat tidak berpengaruh —
        dokumennya masih yang lama, lalu ditimpa."""
        js = baca("static/js/alpine-editor.js")
        blok = js.split("reloadFrame: function", 1)[1][:900]
        self.assertIn('addEventListener("load"', blok)


class CaptionFotoTests(TestCase):
    """Bug 3 — caption ada tapi tidak pernah muncul sendiri setelah unggah.

    `specByKey` adalah variabel closure di luar x-data, jadi Alpine tidak
    melacaknya: menulis foto baru ke sana tidak memicu render ulang. Panel tetap
    menampilkan 'Pilih foto' tanpa thumbnail dan tanpa kolom caption sampai user
    kebetulan memilih elemen lain lalu kembali — dan tidak ada yang
    mengisyaratkan itu. Hampir tidak ada pembeli yang menemukannya.
    """

    def test_foto_bingkai_disimpan_di_state_reaktif(self):
        js = baca("static/js/alpine-editor.js")
        self.assertIn("framePhotos", js)
        self.assertIn("get photo() { return this.framePhotos[this.sel]", js)

    def test_tidak_ada_lagi_penulisan_ke_objek_tak_reaktif(self):
        """Penulis mana pun yang tertinggal di specByKey akan membuat panel
        basi lagi — persis bug ini kembali, tanpa gejala di test lain."""
        js = baca("static/js/alpine-editor.js")
        baris_kode = [
            b for b in js.splitlines()
            if "specByKey" in b and not b.strip().startswith(("*", "/*", "//"))
        ]
        for baris in baris_kode:
            with self.subTest(baris=baris.strip()[:70]):
                self.assertNotIn(".photo =", baris)

    def test_kata_opsional_tidak_dipakai_lagi(self):
        """'(opsional)' terbaca sebagai izin melewatinya."""
        isi = baca("cards/templates/cards/editor.html")
        self.assertNotIn("Caption (opsional)", isi)

    def test_kolom_caption_didekatkan_ke_mata_user_di_hp(self):
        """Membuat kolomnya ter-render saja belum cukup di HP.

        Di bawah 900px `.ed` memakai column-reverse, jadi panel berada DI BAWAH
        pratinjau. Sesudah menekan "Pakai foto" mata user ada di kartu, dan
        kolom caption yang baru muncul berada di luar layar — bug yang sama
        terasa, walau penyebab aslinya sudah hilang.
        """
        js = baca("static/js/alpine-editor.js")
        self.assertIn("scrollIntoView", js)
        self.assertIn("cap-bingkai", js)
        self.assertIn(
            'id="cap-bingkai"', baca("cards/templates/cards/editor.html")
        )

    def test_user_diberi_tahu_keterangan_muncul_di_mana(self):
        Template.objects.create(
            slug="uji", name="Uji", category=CardType.BIRTHDAY,
            config={"renderer": "birthday"},
        )
        isi = self.client.get(reverse("cards:editor", args=["uji"])).content.decode()
        self.assertIn("Muncul sebagai tulisan tangan", isi)


class PenggeserSentuhTests(TestCase):
    """Bug 5 — bulatan perbesaran foto "sering kali tidak tergeser" di HP.

    Dilaporkan pemilik situs 19 Agu 2026 tentang modal crop. Range bawaan
    hanya setinggi batangnya sendiri, jadi jempol yang meleset sedikit ke atas
    atau ke bawah tidak mengenai input sama sekali — dan tidak ada umpan balik
    apa pun yang memberi tahu kenapa tidak terjadi apa-apa.
    """

    def blok(self, selektor):
        css = baca("static/css/app.css")
        awal = css.index(selektor + " {")
        return css[awal:css.index("}", awal)]

    def test_kotak_sentuh_setinggi_target_sentuh_minimum(self):
        """44px = batas minimum Apple HIG (Material menyarankan 48dp).

        Angka ini yang menyelesaikan keluhannya, BUKAN besar bulatannya:
        yang meleset hampir selalu meleset secara vertikal, dan sebelum ini
        seluruh kotak sentuhnya cuma setebal batang.
        """
        blok = self.blok('.ed-slider input[type="range"]')
        self.assertIn("height: 44px;", blok)

    def test_gerakan_menyerong_tidak_direbut_gulir(self):
        """Tanpa touch-action:none, gerakan yang sedikit menyerong ditafsirkan
        browser sebagai gulir halaman di tengah menggeser — penggesernya
        berhenti mengikuti jari. Kanvas crop sudah memakai penjaga yang sama."""
        self.assertIn("touch-action: none;", self.blok('.ed-slider input[type="range"]'))

    def test_bulatan_cukup_besar_untuk_jempol(self):
        blok = self.blok('.ed-slider input[type="range"]::-webkit-slider-thumb')
        self.assertIn("width: 28px;", blok)
        self.assertIn("height: 28px;", blok)

    def test_thumb_dipusatkan_dengan_aritmetika_pasti(self):
        """Trek dibuat setinggi kotaknya (44px) lalu batang 6px-nya dicat
        sebagai background gradient yang dipusatkan. Cara yang lebih lazim —
        trek setipis 6px lalu thumb digeser margin-top negatif — bergantung
        pada apakah mesin render memusatkan kotak trek secara vertikal, dan
        itu tidak sama di semua mesin. Dengan trek setinggi kotak,
        margin-top = (44 - 28) / 2 = 8, dan itu berlaku di mana pun."""
        trek = self.blok('.ed-slider input[type="range"]::-webkit-slider-runnable-track')
        self.assertIn("height: 44px;", trek)
        self.assertIn("no-repeat", trek)
        self.assertIn("margin-top: 8px;", self.blok(
            '.ed-slider input[type="range"]::-webkit-slider-thumb'))

    def test_firefox_ikut_diurus(self):
        """-webkit-appearance:none mematikan tampilan bawaan di WebKit/Blink
        saja. Tanpa pasangan -moz-, Firefox menampilkan penggeser bawaannya
        yang kecil — persis bug ini, hanya di browser lain."""
        for bagian in ("::-moz-range-track", "::-moz-range-thumb"):
            with self.subTest(bagian=bagian):
                self.blok('.ed-slider input[type="range"]' + bagian)

    def test_penggeser_perbesaran_memakai_kelas_yang_sama(self):
        """Keluhannya soal penggeser di modal crop. Kalau suatu saat ia
        diberi kelas sendiri, aturan di atas berhenti menyentuhnya tanpa satu
        pun tes lain yang gagal."""
        isi = baca("cards/templates/cards/editor.html")
        blok = isi[isi.index('class="crop-box"'):isi.index("crop-actions")]
        self.assertIn('class="ed-slider"', blok)
        self.assertIn('type="range"', blok)

