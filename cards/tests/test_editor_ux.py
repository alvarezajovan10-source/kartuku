"""Empat bug editor yang ditemukan user saat uji coba sungguhan.

Keempatnya lolos dari test yang ada karena semuanya soal perilaku di browser,
bukan respons server. Test di sini menjaga kondisi yang bisa diperiksa dari
sumbernya — tidak sempurna, tapi menangkap justru cara masing-masing bug bisa
kembali.
"""

from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from cards.models import CardType, Template


def baca(nama):
    return (Path(settings.BASE_DIR) / nama).read_text(encoding="utf-8")


class HeaderEditorTests(TestCase):
    """Bug 1 — tombol 'Buat Kartu' di header melempar user keluar dari editor.

    Di desktop tombol itu terbaca sebagai 'selesai'/'buat link'; yang mengkliknya
    kembali ke daftar template di tengah pekerjaannya.
    """

    def setUp(self):
        Template.objects.create(
            slug="uji", name="Uji", category=CardType.BIRTHDAY,
            config={"renderer": "birthday"},
        )

    def blok_editor_desktop(self):
        """Isi @media yang memuat aturan editor desktop.

        Dibaca sebagai satu blok utuh, bukan sekian karakter setelah selektor —
        menambah satu aturan atau komentar di dalamnya tidak boleh membuat test
        ini gagal palsu.
        """
        css = baca("static/css/app.css")
        awal = css.index("body.is-editor .site-header")
        buka = css.rindex("@media", 0, awal)
        tutup = css.index("\n}", awal)
        return css[buka:tutup]

    def test_halaman_editor_menandai_dirinya(self):
        isi = self.client.get(reverse("cards:editor", args=["uji"])).content.decode()
        self.assertIn('<body class="is-editor"', isi)

    def test_halaman_lain_tidak_ikut_tertandai(self):
        """Hook body_class harus kosong di tempat lain — kalau bocor, header
        situs ikut hilang di halaman jualan."""
        for nama in ["landing", "page_templates", "page_harga" if False else "page_pricing"]:
            with self.subTest(halaman=nama):
                isi = self.client.get(reverse(f"cards:{nama}")).content.decode()
                self.assertNotIn("is-editor", isi)

    def test_header_disembunyikan_hanya_di_desktop(self):
        """Ambangnya 941px, bukan 900px.

        Pemicunya adalah .header-cta ("Buat Kartu"), yang sudah display:none di
        dalam @media (max-width: 940px). Di bawah 941px jebakannya tidak ada dan
        header masih berguna sebagai navigasi — menyembunyikannya di sana
        merugikan tanpa alasan. Breakpoint tata letak editor (900px) sengaja
        BERBEDA dan tidak boleh dipakai di sini.
        """
        css = baca("static/css/app.css")
        self.assertIn("body.is-editor .site-header { display: none; }", css)

        potong = css.split("body.is-editor .site-header")[0]
        media_terdekat = potong.rsplit("@media", 1)[1].split(")")[0]
        self.assertIn("min-width: 941px", media_terdekat)

    def test_tinggi_editor_ikut_disesuaikan(self):
        """Pasangan yang wajib. `.ed` memakai calc(100vh - 72px) karena
        memperhitungkan header. Menyembunyikan header tanpa mengubah tinggi
        membuat editor 72px lebih pendek dari layar dan footer menyembul —
        regresi halus yang tidak akan terlihat di test lain."""
        blok = self.blok_editor_desktop()
        self.assertIn("body.is-editor .ed", blok)
        self.assertIn("100vh", blok)

    def test_footer_ikut_disembunyikan(self):
        """Footer punya masalah yang sama persis dengan header: dirender di luar
        {% block body %}. Menyembunyikan header saja tidak cukup — editor tetap
        bukan layar penuh, ada footer gelap menggantung di bawah dan halaman
        bisa digulir menjauh dari kartunya."""
        css = baca("static/css/app.css")
        self.assertIn("body.is-editor .site-footer { display: none; }", css)

    def test_masih_ada_jalan_keluar_dari_editor(self):
        """Header disembunyikan, jadi satu-satunya jalan kembali adalah tautan
        di panel kiri. Kalau itu ikut hilang, user terjebak."""
        isi = self.client.get(reverse("cards:editor", args=["uji"])).content.decode()
        self.assertIn("Template lain", isi)


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
