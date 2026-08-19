"""Penjaga template Valentine Story.

Template ini beda dari yang lain: halamannya bukan CSS, melainkan pelat
gambar hasil ekspor Canva, dan teks serta bingkai fotonya ditempelkan di
koordinat tetap di atas pelat itu. Konsekuensinya, kesalahan di sini tidak
memunculkan error apa pun — halaman tetap terbuka, cuma isinya meleset atau
kosong, dan yang menemukan adalah pembeli.

Tiga hal yang dikunci di bawah semuanya pernah terjadi sungguhan saat
membangunnya.
"""

import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from cards.models import CardType, GiftCard, Template

RENDER = Path(settings.BASE_DIR) / "cards" / "templates" / "cards" / "render" / "valentine.html"
CSS = Path(settings.BASE_DIR) / "static" / "css" / "render" / "valentine.css"


def config():
    from cards.management.commands.seed_templates import SEEDS

    for slug, _nama, _kategori, conf in SEEDS:
        if slug == "valentine-story":
            return conf
    raise AssertionError("valentine-story hilang dari seed_templates")


class BahanValentineTests(TestCase):
    def test_semua_pelat_halaman_ada_berkasnya(self):
        """Nama berkas yang salah ketik tidak memunculkan error apa pun —
        halamannya cuma terbuka kosong."""
        isi = RENDER.read_text()
        rujukan = re.findall(r"img/valentine/[\w.]+\.webp", isi)
        # 11 pelat halaman + 1 lapisan atas (hal04atas).
        #
        # Halaman 11 SEKARANG punya pelat, dan sampai 18 Agu 2026 justru
        # dikunci sebaliknya di sini — dulu isinya foto pembeli sehalaman
        # penuh. Pelatnya datang dari tools/buat_pelat_hal11.py, BUKAN dari
        # tools/buat_pelat_valentine.py, jadi halaman 11 tetap terdaftar di
        # TANPA_PELAT pada skrip yang satu itu supaya tidak ditimpa halaman
        # krem kosong dari PDF-nya.
        self.assertEqual(len(rujukan), 12, "harus 11 pelat halaman + 1 lapisan atas")
        self.assertIn("hal11.webp", isi, "halaman 11 harus memakai pelat kolasenya")
        for nama in rujukan:
            with self.subTest(pelat=nama):
                self.assertTrue(
                    (Path(settings.BASE_DIR) / "static" / nama).exists(),
                    f"{nama} dirujuk template tapi berkasnya tidak ada",
                )

    def test_kunci_di_config_dan_di_template_cocok(self):
        """Kunci yang ada di satu sisi saja tidak pernah bersuara: teksnya
        tidak bisa disunting, atau kolomnya muncul di editor tanpa pernah
        mengubah apa pun di kartu."""
        isi = RENDER.read_text()
        di_template_teks = set(re.findall(r'editing "(\w+)" %\}>\{% t card', isi))
        di_template_teks |= set(re.findall(r'\{% el card editing "(\w+)" %\}', isi))
        # Teks yang diatur dengan MENGKLIK, bukan diketik: tidak punya
        # {% el %} sendiri, tapi tetap harus terbaca template lewat {% t %}.
        DIKLIK = {"hari"}
        for kunci in DIKLIK:
            self.assertIn(
                '{%% t card "%s" as' % kunci, isi,
                f"{kunci} tidak dibaca template mana pun",
            )
        di_config_teks = {t["key"] for t in config()["texts"]}
        self.assertEqual(di_config_teks - DIKLIK, di_template_teks)

        di_template_bingkai = set(re.findall(r'frame card editing "(\w+)"', isi))
        # Bingkai yang dirender lewat perulangan {% for key in "a,b"|split %}
        for daftar in re.findall(r'for key in "([\w,]+)"\|split', isi):
            di_template_bingkai |= set(daftar.split(","))
        di_config_bingkai = {f["key"] for f in config()["frames"]}
        self.assertEqual(di_config_bingkai, di_template_bingkai)

    def test_setiap_teks_punya_jatah_ruang(self):
        """Tanpa data-baris/data-maks, teks pembeli yang lebih panjang
        daripada bawaannya tumbuh tanpa batas: menabrak tulisan lain dan
        keluar dari halaman. Penyesuainya di valentine.js hanya bekerja
        untuk elemen yang menyatakan jatahnya."""
        isi = RENDER.read_text()
        tanpa_jatah = [
            m for m in re.findall(r'<(?:p|div) class="tx ([^"]+)"([^>]*)>', isi)
            if "data-baris=" not in m[1] and "data-maks=" not in m[1]
        ]
        self.assertEqual(
            tanpa_jatah, [],
            f"teks tanpa jatah ruang: {[m[0] for m in tanpa_jatah]}",
        )

    def test_teks_elips_halaman_10_dipusatkan_bukan_digantung(self):
        """Empat elips halaman 10 KOSONG di desain Canva-nya — tidak ada
        garis alas untuk ditiru seperti teks halaman lain. Yang benar untuk
        bentuk oval adalah dipusatkan, dan itu perlu dua hal yang gampang
        hilang saat orang "merapikan" CSS-nya:

          * transform jangkar garis alas milik .tx harus DITIMPA, kalau
            tidak teksnya melompat ke atas sejauh setengah baris;
          * penimpanya harus .tx.t-love (dua kelas), karena .tx juga dua
            kelas di aturan font — satu kelas kalah dan diam-diam tidak
            pernah berlaku. Jebakan yang sama pernah memakan --cf.

        Penanda data-tengah dipakai tools/cek_valentine.js untuk memilih
        ukuran yang benar; tanpa itu keempatnya selalu dilaporkan meleset.
        """
        css = CSS.read_text().replace(" ", "").replace("\n", "")
        self.assertIn(".tx.t-love{", css,
                      "penimpa harus .tx.t-love — satu kelas kalah spesifisitas")
        blok = css.split(".tx.t-love{", 1)[1].split("}", 1)[0]
        self.assertIn("transform:translateY(-50%)", blok)
        isi = RENDER.read_text()
        self.assertEqual(len(re.findall(r'data-tengah\{% el ', isi)), 4)

    def test_bingkai_foto_tetap_mutlak_di_editor(self):
        """editing.css menyetel [data-frame].is-empty{position:relative} untuk
        template lain, dimuat SESUDAH berkas ini, dan spesifisitasnya lebih
        tinggi daripada .bingkai. Tanpa penahan ber-id, semua bingkai foto
        lepas dari posisinya begitu pembeli membuka editor dengan kartu yang
        masih kosong — dan itu keadaan awal setiap kartu.
        """
        css = CSS.read_text().replace(" ", "")
        self.assertIn("#buku.bingkai{position:absolute", css)

    def test_tidak_ada_suara_membalik_halaman(self):
        """Suara kertas dicabut 18 Agu 2026: satu-satunya suara di kartu ini
        lagu YouTube pilihan pembeli.

        Dikunci karena pencabutannya menyentuh empat berkas sekaligus, dan
        memasang kembali sebagiannya saja gagal DIAM-DIAM ke dua arah:
        tombol ♪ tanpa jalur suara memberi pembeli sakelar yang tidak
        melakukan apa-apa, sedangkan jalur suara tanpa tombol membuat
        efeknya berbunyi tanpa bisa dimatikan sama sekali.
        """
        js = (Path(settings.BASE_DIR) / "static" / "js" / "render" / "valentine.js").read_text()

        # Komentar dilucuti lebih dulu di KEDUA berkas. Catatan yang
        # menerangkan pencabutan ini mau tidak mau menyebut nama barang yang
        # dicabut, dan tanpa pelucutan ini tes gagal justru karena
        # penjelasannya sendiri.
        html = re.sub(r"\{% comment %\}.*?\{% endcomment %\}", "",
                      RENDER.read_text(), flags=re.S)

        self.assertNotIn('id="bisu"', html, "tombol ♪ muncul lagi di bilah navigasi")
        self.assertNotIn("data-suara", html, "daftar klip suara muncul lagi di #buku")
        self.assertNotIn("#bisu {", CSS.read_text())

        tanpa_komentar = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
        for jejak in ("AudioContext", "createBufferSource", "suaraHalaman",
                      "suaraSintetis", "decodeAudioData", "bisuBtn"):
            with self.subTest(jejak=jejak):
                self.assertNotIn(jejak, tanpa_komentar,
                                 f"{jejak} hidup lagi di valentine.js")

    def test_foto_melewati_tepi_lubang_pelat(self):
        """Kotak bingkai di template ini JATUH DI DALAM lubang pelatnya.

        Sebabnya komponen() di tools/buat_pelat_valentine.py: ia mencari
        kotak lubang pada mask yang diperkecil 4x lalu mengembalikannya pada
        kisi 4 px. Terukur pada kesebelas pelat, tepi kanan dan bawah
        konsisten kurang 1-3 px pelat. Selebar itu lubangnya menganga dan
        yang terlihat dari baliknya --kertas-bg — di hal 4, 6, 7, dan 9
        kertasnya krem, jadi hasilnya garis putih tipis di pinggir tiap foto.

        Penutupnya --tembus di .gbr. Aman karena foto ada di BELAKANG pelat,
        jadi kelebihannya tertutup pelat sendiri.
        """
        css = CSS.read_text().replace(" ", "")
        self.assertIn("inset:calc(-1*var(--tembus,1.5px))", css,
                      ".gbr harus melebar keluar; tanpa itu garis putihnya balik")

        # Harus benar-benar melewati celah terlebar yang pernah diukur:
        # 3 px pelat pada pelat 1241 px = 0,94 px desain pada halaman 390 px.
        m = re.search(r"var\(--tembus,\s*([\d.]+)px\)", CSS.read_text())
        self.assertIsNotNone(m, "--tembus harus punya nilai bawaan dalam px")
        self.assertGreaterEqual(
            float(m.group(1)), 0.94,
            "--tembus lebih kecil daripada celah terlebar yang terukur "
            "(3 px pelat = 0,94 px desain) — garis putihnya akan muncul lagi",
        )

        # .ketuk TIDAK boleh ikut melebar: ia sasaran klik di editor, dan
        # sorotan bingkainya akan meleset dari lubang kalau ikut dilebarkan.
        self.assertIn(".bingkai.ketuk{position:absolute;inset:0", css)

    def test_dua_gaya_membalik_tetap_utuh(self):
        """Ada TIGA cara berpindah halaman, dipilih lewat satu kata `GAYA`:

          "partikel" — halaman memudar di tempat sambil melepas debu
                       berpendar yang naik (dipakai sejak 16 Agu 2026)
          "bilah"    — bilah tegak yang melengkung
          "rotasi"   — satu bidang diputar, transisi CSS 0,6 detik

        Ketiganya sengaja dipertahankan, dan ini permintaan eksplisit
        pemilik situs. Alasannya kuat: keputusan animasi di template ini
        sudah berbalik TIGA kali — "rotasi" dinilai seperti keramik kaca,
        lalu tetap dipilih, lalu dikeluhkan lagi sebagai "menarik kayu",
        lalu seluruh mekaniknya diganti jadi partikel. Menghapus salah satu
        jalur tidak memunculkan error apa pun — cuma membuat keputusan itu
        tidak bisa dibalik tanpa membangun ulang berjam-jam pengukuran.
        """
        isi = RENDER.read_text()
        js = (
            Path(settings.BASE_DIR) / "static" / "js" / "render" / "valentine.js"
        ).read_text()
        self.assertRegex(js, r'\bGAYA\s*=\s*"(rotasi|bilah|partikel)"')
        # jalur "bilah" masih lengkap
        self.assertIn('id="rig"', isi, "wadah bilah hilang dari template")
        # Sengaja TIDAK dipaku ke satu angka. Versi sebelumnya menuntut
        # N_BILAH == 10 persis, dan tes itu gagal saat jumlah bilah dinaikkan
        # ke 16 — padahal animasinya justru membaik. Yang dijaga: masih ada
        # cukup bilah untuk menggambar kurva.
        cocok = re.search(r"\bN_BILAH\s*=\s*(\d+)", js)
        self.assertIsNotNone(cocok, "N_BILAH hilang dari valentine.js")
        self.assertGreaterEqual(
            int(cocok.group(1)), 12,
            "bilah terlalu sedikit; lompatan sudut antar bilah akan terlihat "
            "sebagai kisi-kisi jendela",
        )
        # jalur "rotasi" memakai angka persis dari spek yang diminta
        self.assertRegex(js, r"\bLAMA_ROTASI\s*=\s*600")
        self.assertIn("cubic-bezier(.645,.045,.355,1)", js)
        self.assertNotIn('class="kilau"', isi)

    def test_mode_partikel_lengkap(self):
        """Mode "partikel": halaman memudar di tempat sambil melepas debu
        berpendar yang naik, berwarna mengikuti halamannya.

        Yang dijaga di sini adalah hal-hal yang pernah salah waktu dibangun:

        1. **Satu kanvas, bukan elemen DOM per butir.** 260 elemen yang
           digeser tiap frame memaksa browser menghitung ulang tata letak
           enam puluh kali sedetik — persis yang dihindari seluruh template
           ini.
        2. **Warna diangkat jadi berpendar, tidak dipakai mentah.** Dipakai
           mentah, halaman merah tua melepas debu merah tua yang lenyap di
           atas halamannya sendiri, dan halaman gelap melepas bintik kelabu
           yang terbaca sebagai KOTORAN di atas halaman terang berikutnya.
        3. **Ada warna cadangan.** Sampul dan halaman penutup seluruhnya
           lubang foto — terukur 0 piksel opak dari 204 cuplikan — jadi
           pelatnya tidak menyisakan apa pun untuk dicuplik.
        4. **Posisi butir diundi rata, terpisah dari sumber warnanya.**
           Versi pertama menaruh tiap butir di titik cuplikannya, dan di
           halaman yang didominasi lubang foto seluruh debu menggerombol di
           bingkai tepi.

        Foto pembeli TIDAK pernah dicuplik: bisa datang dari R2 yang beda
        asal, dan itu mencemari kanvas sehingga getImageData dilarang.
        """
        js = (
            Path(settings.BASE_DIR) / "static" / "js" / "render" / "valentine.js"
        ).read_text()
        isi = RENDER.read_text()
        css = CSS.read_text().replace(" ", "").replace("\n", "")

        self.assertIn('id="debu"', isi, "kanvas debu hilang dari template")
        self.assertRegex(js, r"\bJUMLAH_DEBU\s*=\s*\d+")
        self.assertRegex(js, r"function\s+pendar\s*\(", "fungsi pengangkat warna hilang")
        self.assertRegex(js, r"function\s+cadanganWarna\s*\(", "warna cadangan hilang")
        # Lantai kecerahan: tanpa ini halaman gelap melepas bintik kotor.
        self.assertIn("205", js, "lantai kecerahan debu hilang dari pendar()")
        # CSS harus ikut bercabang lewat data-gaya, bukan aturan manual.
        self.assertIn('#buku[data-gaya="partikel"].lembar{visibility:hidden', css)
        self.assertRegex(js, r'setAttribute\(\s*["\']data-gaya["\']')

    def test_lembar_terbalik_menampilkan_isinya_tidak_tercermin(self):
        """Lembar yang sudah pindah ke KIRI menampilkan isi halamannya dan
        terbaca normal — permintaan pemilik situs 14 Agu 2026.

        Dua hal dijaga di sini, dan keduanya pernah salah:

        1. Muka yang membelakangi pembaca TIDAK boleh diserahkan ke
           `backface-visibility`. WebKit tidak mematuhinya, dan lembar yang
           sudah dibalik menampilkan isinya TERCERMIN ("Contents" terbaca
           terbalik). Kelas `.terbalik` dipasang valentine.js di taruh().

        2. Isinya ditampilkan dengan MENCERMINKAN BALIK muka depan
           (`scaleX(-1)`), bukan dengan menyalin isi halaman ke punggungnya.
           Penyalinan akan melipatgandakan pelat 1241x1755 yang ter-decode,
           dan itu yang dulu membuat tab tertutup paksa di HP kelas bawah.

        Jalan buntu yang JANGAN diulang: memberi `.muka.depan` transform 3D
        sendiri (`translateZ(0.01px)`) memang membuat WebKit mematuhi
        backface-visibility, tapi sekaligus mengosongkan halamannya —
        terukur, isi halaman tinggal 17 warna dari 8.819.
        """
        css = CSS.read_text().replace(" ", "").replace("\n", "")
        js = (
            Path(settings.BASE_DIR) / "static" / "js" / "render" / "valentine.js"
        ).read_text()

        self.assertRegex(
            js, r'classList\.toggle\(\s*["\']terbalik["\']',
            "valentine.js tidak lagi memasang kelas .terbalik",
        )
        self.assertIn(
            ".lembar.terbalik.muka.depan{backface-visibility:visible;transform:scaleX(-1)",
            css,
            "muka depan lembar terbalik harus dicerminkan balik, bukan disembunyikan",
        )
        # Penyalinan isi halaman ke punggung: yang dihindari.
        self.assertNotIn(
            'class="muka belakang"><div class="kertas"', RENDER.read_text(),
            "isi halaman disalin ke punggung lembar — pelat jadi berlipat",
        )
        # Jalan buntu yang mengosongkan halaman.
        self.assertNotRegex(
            css, r"\.muka\.depan\{transform:translateZ",
            "translateZ pada .muka.depan mengosongkan isi halaman di WebKit",
        )

    def test_rig_disembunyikan_dengan_display_bukan_visibility(self):
        """#rig WAJIB disembunyikan dengan `display`, bukan `visibility`.

        #rig ber-`transform-style: preserve-3d` dan bilah di dalamnya punya
        transform 3D sendiri. Safari merender anak-anak itu ke ruang 3D
        bersama dan TIDAK mewarisi `visibility: hidden` milik induknya —
        jadi begitu satu putaran selesai, keenam belas bilah tetap tergambar
        pada sudut terakhirnya (~180 derajat, terlempar ke kiri halaman)
        sebagai pita tegak berisi potongan isi halaman yang ter-smear.

        Chrome menyembunyikannya dengan benar, jadi cacat ini TIDAK muncul
        di satu pun pemeriksa puppeteer — hanya terlihat kalau kartunya
        dibuka di Safari. Karena itu penjaganya di sini, bukan di sana.

        Tidak pernah terlihat sebelum 14 Agu 2026 karena gaya yang dipakai
        "rotasi": rig-nya ada tapi tidak pernah diberi transform, jadi tidak
        ada yang bisa bocor.
        """
        css = CSS.read_text().replace(" ", "").replace("\n", "")
        self.assertNotIn(
            "#rig{position:absolute;inset:0;transform-style:preserve-3d;visibility:hidden",
            css,
            "#rig kembali disembunyikan dengan visibility — akan bocor di Safari",
        )
        self.assertRegex(
            css, r"#rig\{[^}]*display:none",
            "#rig harus disembunyikan dengan display:none",
        )
        self.assertRegex(
            css, r"#rig\.jalan\{[^}]*display:block",
            "#rig.jalan harus mengembalikannya dengan display:block",
        )

    def test_simpang_dibangkitkan_sepanjang_jumlah_bilah(self):
        """SIMPANG memberi tiap bilah simpangan sudut kecil supaya lipatannya
        tidak terlihat seperti rumus.

        Dulu ia array sepuluh angka yang diketik tangan, dan itu MENGUNCI
        N_BILAH di sepuluh tanpa ada yang menyatakannya. Menaikkan N_BILAH
        membuat SIMPANG[10..] jadi undefined -> sudutnya NaN -> seluruh
        string transform tidak sah -> LEMBARNYA HILANG dari layar, tanpa
        satu pun error di console.

        Tes ini menjaga supaya panjangnya selalu ikut N_BILAH, bukan angka
        tetap. Sekaligus menjaga ia tetap deterministik: simpangan yang
        diundi ulang tiap frame membuat tepi lembarnya bergetar.
        """
        js = (
            Path(settings.BASE_DIR) / "static" / "js" / "render" / "valentine.js"
        ).read_text()
        self.assertNotRegex(
            js, r"var\s+SIMPANG\s*=\s*\[\s*[-\d.]",
            "SIMPANG kembali jadi array angka tetap; ia akan mengunci N_BILAH lagi",
        )
        self.assertRegex(
            js, r"SIMPANG\s*=\s*\[\s*\]", "SIMPANG tidak lagi dibangkitkan",
        )
        self.assertRegex(
            js, r"for\s*\([^)]*<\s*N_BILAH\s*;[^)]*\)\s*\{[^}]*SIMPANG\.push",
            "SIMPANG tidak dibangkitkan sepanjang N_BILAH",
        )
        simpang = re.search(r"SIMPANG\s*=\s*\[\s*\](.{0,400})", js, re.S)
        self.assertNotIn(
            "Math.random", simpang.group(1),
            "SIMPANG harus deterministik — acak tiap frame membuat tepinya bergetar",
        )

    def test_zona_ketuk_tepi_tidak_ada_saat_menyunting(self):
        """Zona ketuk menutupi 22% lebar halaman di kiri dan kanan. Di
        editor ia akan menelan klik pada teks dan bingkai foto yang dekat
        tepi, dan pembeli tidak akan pernah tahu kenapa elemennya tidak
        bisa dipilih — tidak ada pesan error, cuma klik yang tidak
        berbuat apa-apa."""
        isi = RENDER.read_text()
        self.assertIn('class="zona kanan"', isi)
        blok = isi[isi.index("{% if not editing %}"):isi.index("{% endif %}",
                                                              isi.index("{% if not editing %}"))]
        self.assertIn('class="zona kiri"', blok)
        self.assertIn('class="zona kanan"', blok)

    def test_tinggi_kanonis_sama_dengan_javascript(self):
        """Perbandingan halaman meleset = SELURUH teks bergeser dari
        pelatnya sekaligus."""
        js = (Path(settings.BASE_DIR) / "static" / "js" / "card-stage.js").read_text()
        self.assertRegex(js, r"\bH0_BUKU\s*=\s*551\.6")
        self.assertIn("--h0:551.6px", CSS.read_text().replace(" ", ""))

    def test_jatah_navigasi_sama_di_css_dan_javascript(self):
        """JS memotong tinggi layar sebanyak SISA_NAV sebelum menghitung
        skala, lalu CSS memusatkan halamannya. Kalau padding bawah tidak
        sama dengan potongan itu, jatahnya terbagi rata atas-bawah dan
        bilah navigasi menimpa tepi halaman — dan itu hanya terlihat di
        layar yang TINGGINYA jadi penentu skala (laptop, HP mendatar),
        bukan di HP tegak tempat orang biasanya menguji.
        """
        stage_css = (
            Path(settings.BASE_DIR) / "static" / "css" / "card-stage.css"
        ).read_text()
        js = (Path(settings.BASE_DIR) / "static" / "js" / "card-stage.js").read_text()
        sisa = re.search(r"\bSISA_NAV\s*=\s*(\d+)", js)
        self.assertIsNotNone(sisa, "SISA_NAV hilang dari card-stage.js")
        blok = re.search(
            r'\[data-stage="buku"\]\s*#card-viewport\s*\{([^}]*)\}', stage_css
        )
        self.assertIsNotNone(blok, "aturan #card-viewport mode buku hilang")
        self.assertIn(f"padding-bottom: {sisa.group(1)}px", blok.group(1))
        self.assertIn("box-sizing: border-box", blok.group(1))


class HalamanValentineTests(TestCase):
    def setUp(self):
        self.template = Template.objects.create(
            slug="valentine-uji", name="Valentine Story",
            category=CardType.LOVE_STORY, config=config(),
        )
        self.card = GiftCard.objects.create(
            template=self.template, category=CardType.LOVE_STORY,
            recipient_name="Riana", sender_name="Rocky",
            # Tombol musik hanya muncul kalau ada lagunya, dan letaknya
            # (di luar kanvas) termasuk yang dijaga di sini.
            youtube_video_id="dQw4w9WgXcQ",
            status=GiftCard.Status.PAID,
        )

    def test_kartu_terbit_merender_sebelas_halaman(self):
        html = self.client.get(reverse("cards:public", args=[self.card.id])).content.decode()
        for n in range(1, 12):
            self.assertIn(f'id="hal{n}"', html)
        self.assertIn('data-stage="buku"', html)
        # Tombol melayang wajib DI LUAR kanvas — lihat test_render_css.py
        self.assertGreater(html.index('id="bgmFab"'), html.rindex("</div></div>"))

    def test_teks_bawaan_ikut_terender(self):
        html = self.client.get(reverse("cards:public", args=[self.card.id])).content.decode()
        for potongan in ["LOVESTORY", "Magazine", "ANNIVERSARY", "eternal love."]:
            self.assertIn(potongan, html)

    def test_menyunting_memunculkan_permukaan_ketuk_bingkai(self):
        """Tanpa .ketuk, klik bingkai foto ditelan pelat dan pembeli tidak
        pernah bisa memasang fotonya."""
        draf = GiftCard.objects.create(
            template=self.template, category=CardType.LOVE_STORY,
        )
        sesi = self.client.session
        sesi["cards"] = [str(draf.id)]
        sesi.save()
        html = self.client.get(
            reverse("cards:editor_frame", args=[self.template.slug])
            + f"?card={draf.id}"
        ).content.decode()
        self.assertEqual(html.count('class="ketuk"'), len(config()["frames"]))
        self.assertEqual(html.count("data-frame="), len(config()["frames"]))
