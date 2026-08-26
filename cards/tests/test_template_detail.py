"""Halaman produk per template, dan satu alamat yang melayani dua isi.

/template/<slug>/ menjawab DUA hal: kisi kategori kalau slug-nya kategori,
halaman produk kalau slug-nya template. Itu disengaja supaya alamat halaman
produk tetap pendek dan enak dibagikan — lihat template_or_gallery().

Yang membuatnya aman bukan urutan pengecekan, melainkan bentuk slug-nya:
kategori memakai GARIS BAWAH, template memakai TANDA HUBUNG. Kalau suatu hari
ada yang menamai template "proposal", pemisahnya runtuh diam-diam dan halaman
produk itu tidak akan pernah bisa dibuka. Tes pertama di bawah yang menjaganya.
"""
from django.test import TestCase
from django.urls import reverse

from cards.models import CardType, Template
from cards.views import _isi_renderer


def buat(slug, nama, kategori=CardType.LOVE_STORY, config=None):
    return Template.objects.create(
        slug=slug, name=nama, category=kategori, is_active=True, config=config or {}
    )


class PemisahAlamatTests(TestCase):
    def test_slug_kategori_dan_slug_template_tidak_pernah_bertabrakan(self):
        """Kategori pakai garis bawah, template pakai tanda hubung."""
        buat("valentine-story", "Valentine Story")
        buat("scrapbook-cerita", "Scrapbook Cerita", CardType.BIRTHDAY)
        kategori = set(dict(CardType.choices))
        template = set(Template.objects.values_list("slug", flat=True))
        self.assertEqual(kategori & template, set())
        for slug in template:
            with self.subTest(slug=slug):
                self.assertNotIn("_", slug, "slug template tidak boleh pakai garis bawah")

    def test_slug_kategori_membuka_kisi_kategori(self):
        buat("valentine-story", "Valentine Story")
        r = self.client.get(f"/template/{CardType.LOVE_STORY}/")
        self.assertEqual(r.status_code, 200)

    def test_slug_template_membuka_halaman_produk(self):
        buat("valentine-story", "Valentine Story")
        r = self.client.get("/template/valentine-story/")
        self.assertEqual(r.status_code, 200)
        self.assertTemplateUsed(r, "cards/pages/template_detail.html")
        self.assertContains(r, "Valentine Story")

    def test_slug_ngawur_tetap_404(self):
        self.assertEqual(self.client.get("/template/tidak-ada-ini/").status_code, 404)

    def test_template_nonaktif_tidak_bisa_dibuka(self):
        t = buat("rahasia", "Rahasia")
        Template.objects.filter(pk=t.pk).update(is_active=False)
        self.assertEqual(self.client.get("/template/rahasia/").status_code, 404)


class IsiHalamanProdukTests(TestCase):
    def setUp(self):
        self.t = buat(
            "valentine-story", "Valentine Story",
            config={
                "renderer": "valentine",
                "frames": [{"key": f"f{i}"} for i in range(16)],
                "texts": [{"key": f"t{i}"} for i in range(31)],
            },
        )

    def test_angka_isinya_dihitung_dari_template_sungguhan(self):
        r = self.client.get("/template/valentine-story/")
        isi = dict((sebutan, angka) for angka, sebutan in r.context["isi"])
        self.assertEqual(isi["foto bisa diganti"], "16")
        self.assertEqual(isi["tulisan bisa diubah"], "31")
        self.assertEqual(isi["halaman"], "12")

    def test_harga_dan_dua_tombol_ada(self):
        r = self.client.get("/template/valentine-story/")
        self.assertContains(r, "Rp15.000")
        self.assertContains(r, reverse("cards:editor", args=["valentine-story"]))
        self.assertContains(r, reverse("cards:preview", args=["valentine-story"]))

    def test_kartunya_disematkan_hidup_tanpa_bilah_contoh(self):
        """Nyawa halaman ini: kartunya bisa dibalik sendiri sebelum bayar."""
        r = self.client.get("/template/valentine-story/")
        self.assertContains(r, "?sematan=1")

    def test_bilah_contoh_mati_saat_disematkan(self):
        polos = self.client.get("/preview/valentine-story/?sematan=1")
        biasa = self.client.get("/preview/valentine-story/")
        self.assertFalse(polos.context["preview"])
        self.assertTrue(biasa.context["preview"])

    def test_pratinjau_boleh_disematkan_sameorigin_saja(self):
        r = self.client.get("/preview/valentine-story/")
        self.assertEqual(r.headers.get("X-Frame-Options"), "SAMEORIGIN")


class HitungHalamanTests(TestCase):
    def test_contoh_markup_di_dalam_komentar_tidak_ikut_dihitung(self):
        """valentine.html menulis satu contoh <section class="scene"> di komentar.

        Sebelum blok komentar dibuang, halamannya dilaporkan 13 padahal 12 —
        angka yang muncul di halaman jualan dan tidak akan ada yang curigai.
        """
        self.assertEqual(_isi_renderer("valentine"), (12, "buku"))

    def test_renderer_tak_dikenal_tidak_meledak(self):
        self.assertEqual(_isi_renderer("tidak-ada"), (0, ""))
        self.assertEqual(_isi_renderer(""), (0, ""))


class PencarianTests(TestCase):
    """Kolom cari di header harus benar-benar mencari.

    Kotak cari itu benda paling dominan di header, dan yang membuat halaman
    terbaca sebagai toko. Kalau ia tidak melakukan apa-apa, kebohongannya
    ketahuan pada percobaan pertama — dan yang mencobanya calon pembeli.
    """

    def setUp(self):
        buat("valentine-story", "Valentine Story", CardType.LOVE_STORY)
        buat("game-8bit", "Game 8-Bit", CardType.BIRTHDAY)

    def test_cocok_pada_nama(self):
        r = self.client.get("/cari/", {"q": "valentine"})
        self.assertEqual(len(r.context["entries"]), 1)
        self.assertContains(r, "Valentine Story")

    def test_cocok_pada_nama_kategori(self):
        """Orang mencari "ulang tahun", bukan "game-8bit"."""
        r = self.client.get("/cari/", {"q": "ulang tahun"})
        self.assertEqual([e["template"].slug for e in r.context["entries"]], ["game-8bit"])

    def test_tanpa_kata_kunci_menampilkan_semua(self):
        r = self.client.get("/cari/")
        self.assertEqual(len(r.context["entries"]), 2)

    def test_hasil_kosong_tetap_menawarkan_seluruh_katalog(self):
        """Yang mencari lalu tidak menemukan apa-apa paling dekat dengan pergi."""
        r = self.client.get("/cari/", {"q": "zzz tidak ada"})
        self.assertEqual(len(r.context["entries"]), 0)
        self.assertEqual(len(r.context["semua"]), 2)
        self.assertContains(r, "Valentine Story")

    def test_kolom_cari_ada_di_setiap_halaman(self):
        for path in ("/", "/template/", "/faq/"):
            with self.subTest(path=path):
                self.assertContains(self.client.get(path), 'action="/cari/"')


class HalamanListingTests(TestCase):
    """Halaman produk disusun mengikuti tata letak listing (23 Agu 2026)."""

    def setUp(self):
        self.t = buat(
            "valentine-story", "Valentine Story",
            config={"renderer": "valentine",
                    "frames": [{"key": f"f{i}"} for i in range(16)],
                    "texts": [{"key": f"t{i}"} for i in range(31)]},
        )

    def test_harga_promo_dan_harga_coret(self):
        r = self.client.get("/template/valentine-story/")
        self.assertContains(r, "Rp15.000")
        self.assertContains(r, "Rp89.000")
        self.assertEqual(r.context["potongan"], 83)

    def test_harga_coret_hilang_kalau_harga_normal_dikosongkan(self):
        """Coretan HANYA muncul kalau ada harga normal yang sungguhan.

        Harga coret yang tidak pernah berlaku adalah harga palsu. Dengan
        CARD_LIST_PRICE dikosongkan, halaman harus kembali menampilkan satu
        harga saja — bukan coretan Rp0 atau potongan 100%.
        """
        with self.settings(CARD_LIST_PRICE=0):
            r = self.client.get("/template/valentine-story/")
        self.assertEqual(r.context["potongan"], 0)
        self.assertEqual(r.context["harga_normal"], 0)
        self.assertNotContains(r, "lst-potongan")

    def test_harga_coret_hilang_kalau_tidak_lebih_mahal(self):
        with self.settings(CARD_LIST_PRICE=15_000):
            r = self.client.get("/template/valentine-story/")
        self.assertEqual(r.context["potongan"], 0)

    def test_lencana_menempel_pada_template_yang_ditunjuk(self):
        r = self.client.get("/template/valentine-story/")
        self.assertEqual(r.context["lencana_kode"], "bestseller")
        buat("scrapbook-cerita", "Scrapbook Cerita", CardType.BIRTHDAY)
        r2 = self.client.get("/template/scrapbook-cerita/")
        self.assertEqual(r2.context["lencana_kode"], "star")

    def test_template_tanpa_lencana_tidak_menampilkan_apa_apa(self):
        buat("tanpa-lencana", "Tanpa Lencana")
        r = self.client.get("/template/tanpa-lencana/")
        self.assertEqual(r.context["lencana_kode"], "")
        self.assertNotContains(r, "lst-lencana")

    def test_kartu_hidup_selalu_jadi_isi_pertama_galeri(self):
        """Nyawa halaman ini: kartunya bisa dicoba sebelum dibayar."""
        r = self.client.get("/template/valentine-story/")
        self.assertContains(r, "?sematan=1")
        self.assertContains(r, 'data-i="0"')

    def test_template_tanpa_foto_galeri_tetap_terbuka(self):
        """Template baru belum punya potret halaman; halamannya tidak boleh mati."""
        buat("belum-ada-galeri", "Belum Ada Galeri")
        r = self.client.get("/template/belum-ada-galeri/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["galeri"], [])

    def test_blok_ulasan_menampilkan_keadaan_kosong(self):
        r = self.client.get("/template/valentine-story/")
        self.assertContains(r, "Belum ada ulasan")
