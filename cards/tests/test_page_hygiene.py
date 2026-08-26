"""Halaman pembeli tidak boleh membocorkan hal internal.

Tiga kebocoran nyata pernah tayang di situs live:

1. `{# ... #}` yang ditulis lebih dari satu baris. Sintaks itu hanya berlaku
   satu baris, jadi sisanya tercetak apa adanya — catatan TODO sempat terbaca
   pengunjung di halaman Testimoni.
2. Galeri kategori kosong menampilkan "Tambahkan lewat admin" lengkap dengan
   tautan ke /admin/ — instruksi untuk developer, dibaca calon pembeli.
3. Kategori yang templatenya belum jadi tampil seperti siap dipakai, membawa
   pembeli ke galeri kosong.
"""

from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from cards.models import CardType, Template


class SintaksKomentarTests(TestCase):
    """`{# ... #}` hanya berlaku SATU baris. Ditulis lebih dari itu, sisanya
    tercetak apa adanya ke halaman.

    Kesalahan ini sudah terjadi empat kali di proyek ini — catatan TODO terbaca
    pengunjung di halaman Testimoni, dan sebuah komentar panjang muncul di panel
    editor yang dilihat pembeli saat memilih foto.

    Test per-halaman tidak cukup: ia hanya menjaga halaman yang sempat
    didaftarkan, dan justru halaman yang terlupa itulah yang bocor. Yang ini
    membaca SEMUA berkas template, jadi halaman baru ikut terlindungi tanpa
    perlu diingat.
    """

    def berkas_template(self):
        akar = Path(settings.BASE_DIR)
        for folder in sorted(akar.glob("**/templates")):
            if ".venv" in folder.parts or "staticfiles" in folder.parts:
                continue
            yield from sorted(folder.rglob("*.html"))

    def test_tidak_ada_komentar_pendek_yang_melewati_satu_baris(self):
        bocor = []
        for berkas in self.berkas_template():
            teks = berkas.read_text(encoding="utf-8")
            posisi = 0
            while True:
                buka = teks.find("{#", posisi)
                if buka == -1:
                    break
                tutup = teks.find("#}", buka)
                baris = teks.count("\n", 0, buka) + 1
                if tutup == -1 or "\n" in teks[buka:tutup]:
                    bocor.append(f"{berkas.relative_to(settings.BASE_DIR)}:{baris}")
                posisi = buka + 2

        self.assertFalse(
            bocor,
            "Komentar {# #} melewati satu baris — isinya akan tercetak ke "
            "halaman. Pakai {% comment %}...{% endcomment %} di:\n  "
            + "\n  ".join(bocor),
        )

    def test_penjaga_ini_memang_memindai_sesuatu(self):
        """Kalau pencarian berkasnya rusak, test di atas lolos tanpa memeriksa
        apa pun — kegagalan paling berbahaya untuk sebuah penjaga."""
        jumlah = len(list(self.berkas_template()))
        self.assertGreater(jumlah, 10, f"hanya {jumlah} template ditemukan")

HALAMAN = ["landing", "page_templates", "page_how", "page_pricing",
           "page_faq", "page_testimonials"]


class KebocoranTemplateTests(TestCase):
    def setUp(self):
        Template.objects.create(
            slug="uji-ulang-tahun", name="Uji", category=CardType.BIRTHDAY,
            is_active=True,
        )

    def _semua_halaman(self):
        for nama in HALAMAN:
            yield nama, self.client.get(reverse(f"cards:{nama}")).content.decode()
        for kategori, _ in CardType.choices:
            yield (f"gallery:{kategori}",
                   self.client.get(reverse("cards:gallery", args=[kategori])).content.decode())

    def test_tidak_ada_komentar_django_yang_bocor(self):
        for nama, isi in self._semua_halaman():
            with self.subTest(halaman=nama):
                self.assertNotIn("{#", isi)
                self.assertNotIn("{%", isi)

    def test_tidak_menautkan_ke_admin(self):
        for nama, isi in self._semua_halaman():
            with self.subTest(halaman=nama):
                self.assertNotIn("/admin/", isi)

    def test_tidak_ada_catatan_pengembang(self):
        for nama, isi in self._semua_halaman():
            with self.subTest(halaman=nama):
                self.assertNotIn("TODO", isi)


class DaftarTemplateRataTests(TestCase):
    """Lapisan tema dilewati sementara (19 Agu 2026, keputusan pemilik situs).

    Menggantikan KategoriBelumJadiTests, yang mengunci perilaku sebaliknya:
    dulu keempat tema selalu tampil, yang kosong ditandai "Coming soon" dan
    tidak bisa diklik. Itu benar selama temanya jadi pintu masuk.

    Sekarang aritmetikanya tidak mendukung lagi: empat tema, hanya dua
    berisi, dan isinya timpang (tiga template di Birthday, satu di Love
    Story). Separuh pintu buntu, dan yang hidup pun menyembunyikan barangnya
    di balik satu klik. Templatenya sendiri cuma tiga di produksi.
    """

    def setUp(self):
        Template.objects.create(
            slug="uji-ulang-tahun", name="Uji Ultah", category=CardType.BIRTHDAY,
            is_active=True,
        )
        Template.objects.create(
            slug="uji-cinta", name="Uji Cinta", category=CardType.LOVE_STORY,
            is_active=True,
        )

    def test_beranda_menampilkan_template_bukan_tema(self):
        isi = self.client.get(reverse("cards:landing")).content.decode()
        self.assertIn("Uji Ultah", isi)
        self.assertIn("Uji Cinta", isi)
        self.assertNotIn("Coming soon", isi,
                         "kartu tema kosong muncul lagi di beranda")

    def test_halaman_template_menampilkan_semua_template(self):
        isi = self.client.get(reverse("cards:page_templates")).content.decode()
        for nama in ("Uji Ultah", "Uji Cinta"):
            with self.subTest(template=nama):
                self.assertIn(nama, isi)

    def test_tiap_kartu_satu_tautan_ke_halaman_produk(self):
        """Satu kartu = satu tujuan, dan harganya terbaca tanpa mengklik.

        Riwayatnya dua langkah. Sampai 22 Agu 2026 tiap kartu punya dua tombol
        ("Preview" dan "Pakai Ini") dan yang kiri melempar orang ke kartu
        contoh selayar penuh. 23 Agu 2026 kisinya disusun ulang mengikuti pola
        Etsy: tombolnya dicabut seluruhnya, kartunya sendiri jadi tautannya,
        dan HARGA dituliskan di tiap kartu.

        Alasan harga itu yang paling penting dijaga: orang yang menimbang
        membeli mencari harga lebih dulu, dan kalau tidak ketemu di kartunya
        sebagian besar pergi alih-alih mengklik.
        """
        isi = self.client.get(reverse("cards:page_templates")).content.decode()
        self.assertIn("Rp15.000", isi)
        for slug in ("uji-ulang-tahun", "uji-cinta"):
            with self.subTest(slug=slug):
                self.assertIn(reverse("cards:template_detail", args=[slug]), isi)
                self.assertNotIn(
                    reverse("cards:editor", args=[slug]), isi,
                    "tombol di kartu sudah dicabut; jalan ke editor lewat halaman produk",
                )

    def test_nama_tema_tetap_tertulis_di_tiap_kartu(self):
        """Tanpa lapisan tema, tidak ada lagi yang memberi tahu pembeli bahwa
        sebuah template itu kartu Love Story dan bukan kartu ulang tahun.
        Labelnya karena itu pindah ke kartunya."""
        isi = self.client.get(reverse("cards:page_templates")).content.decode()
        self.assertIn("Love Story", isi)
        self.assertIn("Ulang Tahun", isi)

    def test_rute_galeri_per_tema_tetap_hidup(self):
        """SENGAJA tidak dicabut. Tautan lama yang sudah tersebar tidak boleh
        mati, dan lapisan temanya akan dikembalikan begitu minimal tiga tema
        terisi — biar itu tinggal menyambung, bukan membangun ulang."""
        for kategori in (CardType.BIRTHDAY, CardType.LOVE_STORY):
            with self.subTest(kategori=kategori):
                r = self.client.get(reverse("cards:gallery", args=[kategori]))
                self.assertEqual(r.status_code, 200)

    def test_galeri_kosong_menawarkan_jalan_keluar(self):
        """Pembeli yang tersesat ke kategori kosong harus diarahkan, bukan
        buntu — dan sekarang diarahkan ke daftar rata, bukan ke galeri
        Birthday seperti dulu."""
        isi = self.client.get(
            reverse("cards:gallery", args=[CardType.PROPOSAL])
        ).content.decode()
        self.assertIn("Coming soon", isi)
        self.assertIn(reverse("cards:page_templates"), isi)
