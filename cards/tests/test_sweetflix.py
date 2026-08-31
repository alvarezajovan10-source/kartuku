"""Sweetflix — yang dijaga di sini keputusan yang gampang rusak diam-diam.

Tiga di antaranya lahir dari kesalahan atau tawar-menawar yang nyata:

1. JATAH FOTO. Rancangan dengan empat profil dan delapan poster butuh 41 foto
   — di atas MAX_PHOTOS_PER_CARD dan sekitar 82MB untuk SATU kartu, yang akan
   memenuhi disk server gratis setelah kira-kira enam kartu. Pemilik situs
   memilih dua profil. Menambah profil ketiga berarti menghitung ulang ini.

2. BINGKAI FOTO HARUS PUNYA UKURAN EKSPLISIT. `static/css/editing.css` punya
   aturan `[data-frame].is-empty { position: relative }` yang spesifisitasnya
   lebih tinggi dan dimuat belakangan. Bingkai yang cuma mengandalkan
   `inset: 0` kehilangan tinggi di dalam editor dan runtuh ke `min-height:
   .8em` = 12,8px — pembeli melihat bilah tipis, bukan bingkai sepenuh layar.
   Ini benar-benar terjadi dan baru ketahuan setelah diukur.

3. POSTER KOSONG TIDAK DIRENDER. Kalau slot kosong muncul sebagai kotak,
   kartu yang belum lengkap terbaca RUSAK oleh penerimanya.
"""

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from cards.management.commands.seed_templates import SEEDS
from cards.models import CardType, GiftCard, Template

HURUF = ["a"]   # sempat empat, lalu dua, lalu satu
POSTER = range(1, 9)


def konfigurasi():
    for slug, _nama, _kategori, config in SEEDS:
        if slug == "sweetflix":
            return config
    raise AssertionError("seed sweetflix hilang")


def css():
    with open(settings.BASE_DIR / "static/css/render/sweetflix.css") as fh:
        return fh.read()


class KonfigurasiTests(TestCase):
    def setUp(self):
        self.config = konfigurasi()
        self.bingkai = {f["key"] for f in self.config["frames"]}
        self.teks = {t["key"]: t.get("default", "") for t in self.config["texts"]}

    def test_jatah_foto_muat_di_bawah_batas(self):
        """Lihat catatan 1 di kepala berkas."""
        self.assertLessEqual(
            len(self.bingkai), settings.MAX_PHOTOS_PER_CARD,
            f"{len(self.bingkai)} bingkai melewati batas "
            f"{settings.MAX_PHOTOS_PER_CARD} foto per kartu",
        )

    def test_tiap_profil_punya_isi_sendiri(self):
        for h in HURUF:
            self.assertIn(f"{h}_avatar", self.bingkai)
            self.assertIn(f"{h}_hero", self.bingkai)
            for i in POSTER:
                self.assertIn(f"{h}_p{i}", self.bingkai)
                # Ceritanya BUKAN kolom sendiri: ia caption fotonya.
                self.assertNotIn(f"{h}_s{i}", self.teks)
            for akhiran in ["cap", "judul", "meta", "desk", "baris1"]:
                self.assertIn(f"{h}_{akhiran}", self.teks)

    def test_semua_bingkai_punya_rasio(self):
        """Kotak crop di editor dibentuk dari "rasio" (alpine-editor.js:574).
        Bingkai tanpa rasio jatuh ke bujur sangkar, dan pembeli memilih bagian
        fotonya di bentuk yang bukan bentuk tampilannya — potongannya lalu
        tidak pernah sesuai dugaannya. Sempat terjadi di seluruh 21 bingkai."""
        LAYAR = round(960 / 540, 4)
        for f in self.config["frames"]:
            kunci = f["key"]
            with self.subTest(bingkai=kunci):
                self.assertIn("rasio", f, f"{kunci} tidak punya rasio")
                if kunci.endswith("_avatar"):
                    self.assertEqual(f["rasio"], 1.0)
                else:
                    self.assertEqual(f["rasio"], LAYAR)
                # Foto yang memenuhi satu layar penuh butuh potongan besar;
                # 1100 px terlihat pecah dibentang selebar kanvas.
                if kunci == "f_buka" or kunci.endswith("_hero"):
                    self.assertTrue(f.get("asli"), f"{kunci} perlu asli=True")

    def test_hanya_bingkai_latar_yang_minta_potongan_besar(self):
        """Foto LATAR dibentangkan memenuhi jendela tanpa batas pembesaran:
        di laptop retina satu piksel foto harus mengisi 3.398 piksel layar.
        Terukur, pada potongan 2400 px rasionya 0,71 — masih lembut; pada
        3200 px jadi 0,94. Poster dan avatar tampil kecil dan sudah tajam,
        jadi menaikkannya cuma menambah berat berkas tanpa terlihat."""
        latar = {"f_buka", "a_hero"}
        for f in self.config["frames"]:
            with self.subTest(bingkai=f["key"]):
                if f["key"] in latar:
                    self.assertEqual(f.get("sisi"), 3200)
                    self.assertTrue(f.get("asli"))
                else:
                    self.assertIsNone(f.get("sisi"))

    def test_judul_pilih_profil_bisa_disunting(self):
        """Pemilik situs meminta "Choose" bisa diganti pembeli, bukan mati."""
        self.assertEqual(self.teks.get("judul_pilih"), "Choose")

    def test_bawaan_memberi_contoh_bukan_perintah(self):
        """Kolom yang bawaannya perintah terbukti dilewati pembeli — itu yang
        dulu menimpa bab Harapan di Scrapbook sampai akhirnya dihapus."""
        for kunci in ["a_desk", "a_judul", "a_baris1"]:
            isi = self.teks[kunci]
            with self.subTest(kunci=kunci):
                self.assertGreater(len(isi), 3)
                self.assertNotIn("Tulis", isi)
                self.assertNotIn("di sini", isi)

    def test_halaman_pertama_menanyakan_nama(self):
        """Halaman pertama mengikuti rujukan yang dikirim pemilik situs: judul,
        sub, kotak nama, tombol Continue."""
        self.assertEqual(self.teks.get("buka_judul"), "Who's watching?")
        self.assertEqual(self.teks.get("buka_sub"), "Let's start with your name.")

    def test_judul_baris_our_pictures(self):
        self.assertEqual(self.teks.get("a_baris1"), "Our Pictures")


class GayaTests(TestCase):
    def test_bingkai_sepenuh_layar_punya_ukuran_eksplisit(self):
        """Lihat catatan 2 di kepala berkas. Tanpa width/height eksplisit,
        bingkainya runtuh jadi 12,8px di dalam editor."""
        isi = css()
        for pemilih in [".buka-gbr", ".latar"]:
            with self.subTest(pemilih=pemilih):
                blok = isi.split(pemilih + " {", 1)
                self.assertEqual(len(blok), 2, f"{pemilih} hilang dari CSS")
                aturan = blok[1].split("}", 1)[0]
                self.assertIn("width: 100%", aturan)
                self.assertIn("height: 100%", aturan)

    def test_teks_yang_dibuka_tetap_dibatasi_tingginya(self):
        """Membuka teks panjang BUKAN berarti ia bebas tumbuh. Terukur di
        browser: tanpa batas ini tombol Putar terdorong dari y287 ke y399,
        sedangkan baris poster mulai di y377 — tombolnya menabrak poster.
        Yang dibuka digulir di dalam kotaknya sendiri, bukan mendorong
        tetangganya."""
        isi = css()
        blok = isi.split(".hero-desk.terbuka {", 1)
        self.assertEqual(len(blok), 2, ".hero-desk.terbuka hilang dari CSS")
        aturan = blok[1].split("}", 1)[0]
        self.assertIn("max-height", aturan)
        self.assertIn("overflow-y: auto", aturan)

        # Cerita di panel detail SENGAJA tidak dipotong: panelnya sendiri yang
        # menggulir, dan di sana gulir wajar karena isinya jelas berlanjut ke
        # bawah. Yang dijaga di sini panelnya memang bisa digulir.
        blok = isi.split("\n.det {", 1)
        self.assertEqual(len(blok), 2, ".det hilang dari CSS")
        self.assertIn("overflow: hidden auto", blok[1].split("}", 1)[0])

    def test_gaya_foto_pembeli_dihormati(self):
        """Bug yang baru ketahuan: versi pertama menulis `object-fit: cover`
        mati dan mengabaikan --fit/--ox/--oy/--zoom yang dipancarkan
        cards/styles.py:element_css(). Akibatnya kontrol geser dan zoom foto di
        editor TIDAK berefek apa pun, dan pemilik situs melaporkannya sebagai
        "fotonya ke-crop besar". Renderer lain memakai pola yang sama —
        scrapbook.css:96, birthday.css:136, valentine.css:334."""
        isi = css()
        for var in ["var(--fit,", "var(--ox,", "var(--oy,", "var(--zoom,"]:
            with self.subTest(var=var):
                self.assertIn(var, isi, f"{var} tidak dipakai — gaya foto pembeli diabaikan")

    def test_latar_tidak_digeser_atau_diperbesar(self):
        """Foto latar harus tampil PERSIS seperti yang dipotong pembeli.

        Sempat digeser 6,5% dan diperbesar 1,18x supaya wajah keluar dari
        bidang gelap. Terukur, itu memakan 15,5% tepi kanan potongan dan 9%
        atas-bawahnya: yang dipotong bukan yang muncul. Kendali bingkainya
        sekarang milik pembeli lewat kotak crop 16:9."""
        isi = css()
        blok = isi.split(".latar img {", 1)
        self.assertEqual(len(blok), 1,
                         ".latar img dihidupkan lagi — potongan pembeli akan terpangkas")
        self.assertNotIn("--geser", isi)

    def test_babak_memakai_pudar_bukan_display(self):
        """`display` tidak bisa ditransisikan. Selama .layar memakai
        display:none <-> block, perpindahan babak akan selalu jadi potongan
        keras berapa pun durasi yang disetel."""
        isi = css()
        blok = isi.split(".layar {", 1)
        self.assertEqual(len(blok), 2, ".layar hilang dari CSS")
        aturan = blok[1].split("}", 1)[0]
        self.assertIn("opacity", aturan)
        self.assertIn("transition", aturan)
        self.assertNotIn("display: none", aturan)

    def test_tombol_lagu_bawaan_TIDAK_disembunyikan(self):
        """Sempat disembunyikan waktu tombol PLAY merangkap tombol lagu.
        Pemilik situs membatalkannya: lagunya kembali seperti template lain."""
        self.assertNotIn(".bgm-fab", css())

    def test_tidak_memakai_merah_merek_netflix(self):
        self.assertNotIn("#e50914", css().lower())


class RenderTests(TestCase):
    def setUp(self):
        self.template = Template.objects.create(
            slug="sweetflix", name="Sweetflix", category=CardType.LOVE_STORY,
            config=konfigurasi(),
        )
        self.kartu = GiftCard.objects.create(
            template=self.template, category=CardType.LOVE_STORY,
            status=GiftCard.Status.PAID, paid_at=timezone.now(),
            recipient_name="Riana", sender_name="Rocky",
        )

    def isi(self):
        return self.client.get(f"/{self.kartu.id}/").content.decode()

    def test_semua_babak_ada(self):
        """Editor hanya bisa melompat ke elemen yang berada di dalam .scene
        ber-id (kontrak di static/js/card-frame.js). Babak yang hilang berarti
        kolomnya tidak akan pernah bisa disunting pembeli."""
        isi = self.isi()
        # "intro" (animasi huruf S) dibuang atas permintaan pemilik situs
        # bersama profil kedua.
        wajib = ["buka", "profil", "warp"]
        wajib += [f"home_{h}" for h in HURUF] + [f"detail_{h}" for h in HURUF]
        for babak in wajib:
            with self.subTest(babak=babak):
                self.assertIn(f'id="{babak}"', isi)

    def test_poster_kosong_tidak_dirender(self):
        """Lihat catatan 3. Kartu ini belum punya satu foto pun."""
        self.assertNotIn('class="kartu-poster', self.isi())

    def test_baris_top_10_sudah_dibuang(self):
        """Dibuang atas permintaan pemilik situs — hanya satu baris tersisa."""
        isi = self.isi()
        self.assertNotIn("top-item", isi)
        self.assertNotIn("baris-top", isi)

    def test_ada_jalan_kembali_ke_pemilih_profil(self):
        """Pemilik situs tidak menemukan cara kembali memilih profil."""
        isi = self.isi()
        for h in HURUF:
            with self.subTest(profil=h):
                blok = isi.split(f'id="home_{h}"', 1)[1].split("</section>", 1)[0]
                self.assertIn('data-ke="profil"', blok)

    def test_nama_penerima_dipasang_sebagai_teks_biasa(self):
        """Nama diketik PENERIMA, jadi ia masukan tak tepercaya. Dipasang lewat
        textContent; innerHTML akan membuat tanda kurung siku yang diketik
        merusak tata letak kartunya sendiri."""
        isi = self.isi()
        self.assertIn('id="namaTamu"', isi)
        self.assertIn("data-nama-tamu", isi)
        with open(settings.BASE_DIR / "static/js/render/sweetflix.js") as fh:
            js = fh.read()
        self.assertIn("el.textContent = nama", js)
        self.assertNotIn("innerHTML = nama", js)

    def test_teks_panjang_punya_pemotong(self):
        """Kanvas mendatar tingginya mati dan tidak menggulir, jadi teks
        panjang harus dibatasi — kalau tidak ia menembus atap kanvas."""
        isi = self.isi()
        self.assertIn("hero-desk potong", isi)

    def test_babak_pemutar_disembunyikan_dari_tab_editor(self):
        """Babak pemutar foto isinya dibangun JS dan tidak punya satu pun kolom
        untuk disunting. Tab yang tidak bisa diapa-apakan cuma membingungkan
        pembeli, jadi ia ditandai data-tanpa-tab dan disaring di
        static/js/card-frame.js."""
        isi = self.isi()
        blok = isi.split('id="warp"', 1)
        self.assertEqual(len(blok), 2, "babak warp hilang")
        self.assertIn("data-tanpa-tab", blok[1].split(">", 1)[0])

        with open(settings.BASE_DIR / "static/js/card-frame.js") as fh:
            self.assertIn(":not([data-tanpa-tab])", fh.read())

    def test_halaman_pertama_punya_kotak_nama_dan_continue(self):
        """Halaman pertama sempat berupa kotak merah "PLAY", lalu pil putih
        "Putar", dan akhirnya diganti kotak nama + tombol Continue mengikuti
        rujukan yang dikirim pemilik situs. Yang lama tidak boleh tertinggal."""
        isi = self.isi()
        self.assertIn('id="namaTamu"', isi)
        self.assertIn('id="tblLanjut"', isi)
        self.assertIn("Continue", isi)
        for usang in ['class="tbl-play"', 'class="tbl-putar besar"', 'id="tblPlay"']:
            with self.subTest(usang=usang):
                self.assertNotIn(usang, isi)

    def test_panel_detail_mengambang_di_atas_beranda(self):
        """Panel detail mengikuti rujukan yang dikirim pemilik situs: kartu
        mengambang di atas beranda yang diredupkan, bukan layar penuh. Kalau
        berandanya ikut dimatikan, panelnya cuma melayang di atas hitam dan
        kehilangan seluruh maksudnya sebagai lapisan."""
        isi = self.isi()
        for h in HURUF:
            with self.subTest(profil=h):
                blok = isi.split(f'id="detail_{h}"', 1)[1].split("</section>", 1)[0]
                self.assertIn("det-tabir", blok)       # peredup beranda
                self.assertIn("det-tutup", blok)       # tombol tutup di kartu
                self.assertIn("det-lencana", blok)     # lencana TOP 10
                self.assertIn("Pemeran:", blok)

        with open(settings.BASE_DIR / "static/js/render/sweetflix.js") as fh:
            js = fh.read()
        self.assertIn('tetap.push("home_"', js,
                      "beranda tidak dibiarkan aktif di belakang panel")

    def test_kolom_kanan_panel_tidak_menambah_kolom_isian(self):
        """Pemeran diambil dari nama penerima dan pengirim yang SUDAH ada, dan
        peringkat dari nomor poster. Menambah kolom isian untuk itu berarti
        menambah pekerjaan pembeli demi hiasan."""
        kunci = {t["key"] for t in konfigurasi()["texts"]}
        for h in HURUF:
            for i in range(1, 9):
                self.assertNotIn(f"{h}_judul{i}", kunci)
                self.assertNotIn(f"{h}_cast{i}", kunci)
        self.assertIn("Riana", self.isi())   # dari recipient_name

    def test_tidak_memakai_merek_netflix(self):
        self.assertNotIn("netflix", self.isi().lower())

    def test_nama_wajib_diisi_sebelum_masuk(self):
        """Layar pembuka meniru Netflix: pilih dulu siapa yang menonton. Kalau
        Continue tetap jalan dengan kotak kosong, seluruh sapaan bernama di
        kartu ini jatuh ke kosong dan layar pembukanya jadi pajangan."""
        with open(settings.BASE_DIR / "static/js/render/sweetflix.js") as fh:
            js = fh.read()
        badan = js.split("function lanjut()", 1)[1].split("\n  }", 1)[0]
        self.assertIn("tandaiKosong()", badan,
                      "lanjut() tidak menahan apa pun saat nama kosong")
        self.assertIn(".trim()", badan,
                      "spasi saja harus dihitung kosong, bukan diterima")
        # Penjaga yang paling gampang hilang: saat menyunting kotaknya DIMATIKAN,
        # jadi ia selalu kosong. Tanpa jalan pintas ini pembeli terkunci di
        # layar pembuka dan tidak pernah bisa melihat halaman berikutnya.
        self.assertIn("if (menyunting)", badan,
                      "pembeli akan terkunci di layar pembuka saat menyunting")
        self.assertLess(badan.index("if (menyunting)"), badan.index("tandaiKosong()"),
                        "jalan pintas menyunting harus DI ATAS penahannya")

    def test_alasan_ditahan_terbaca_bukan_cuma_warna(self):
        """Tepi memerah saja tidak menjelaskan apa-apa, dan tidak terbaca oleh
        yang sulit membedakan warna maupun pembaca layar."""
        isi = self.isi()
        self.assertIn('id="bukaGalat"', isi)
        self.assertIn('role="alert"', isi)
        self.assertIn("hidden", isi.split('id="bukaGalat"', 1)[1].split(">", 1)[0],
                      "pesan galat tampil sebelum ada yang salah")
        with open(settings.BASE_DIR / "static/js/render/sweetflix.js") as fh:
            js = fh.read()
        self.assertIn('addEventListener("input"', js,
                      "peringatan tidak hilang saat ia mulai mengetik")
