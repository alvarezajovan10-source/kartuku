"""Teks bawaan Scrapbook.

Bawaan di sini bukan isian sementara: itulah yang dilihat pembeli saat pertama
membuka editor, jadi tugasnya memberi contoh nada yang bisa mereka tiru. Bab
yang bawaannya cuma perintah ("Tulis harapanmu di sini...") terbukti dilewati —
8 dari 12 kartu lunas mengosongkannya.

Yang dijaga di sini adalah hal yang gampang rusak diam-diam saat teksnya diubah
lagi nanti, bukan bunyi kalimatnya.
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cards.management.commands.seed_templates import SEEDS
from cards.models import CardType, GiftCard, Template


def konfigurasi_scrapbook():
    for slug, _nama, _kategori, config in SEEDS:
        if slug == "scrapbook-cerita":
            return config
    raise AssertionError("seed scrapbook-cerita hilang")


class BawaanTeksTests(TestCase):
    def setUp(self):
        self.config = konfigurasi_scrapbook()
        self.bawaan = {t["key"]: t.get("default", "") for t in self.config["texts"]}

    def test_semua_slot_masih_ada(self):
        """Menghapus slot berarti menghapus teks yang sudah ditulis pembeli dari
        kartu yang terbit — isinya disimpan per-kunci, jadi kunci yang hilang
        membuat tulisan mereka tidak pernah dirender lagi."""
        wajib = {
            "cover_title", "cover_sub", "bab1_label", "bab1_note",
            "bab2_label", "bab2_note", "momen_label", "momen_strip",
            "cinta_label", "cinta_note", "harapan_label",
            "closing_label", "closing_line", "from_line",
        }
        self.assertEqual(wajib - set(self.bawaan), set())

    def test_label_bab_cukup_pendek_untuk_huruf_tempelan(self):
        """Label bab dirender sebagai .ransom — tiap huruf dapat kotaknya
        sendiri. Kalimat panjang memenuhi layar dan memecah tata letaknya."""
        for kunci in ["cover_title", "bab1_label", "bab2_label", "momen_label",
                      "cinta_label", "harapan_label", "closing_label"]:
            with self.subTest(kunci=kunci):
                self.assertLessEqual(
                    len(self.bawaan[kunci]), 20,
                    f"{kunci} terlalu panjang untuk huruf tempelan",
                )

    def test_cerita_bab_memberi_contoh_bukan_perintah(self):
        """Bab yang bawaannya perintah akan dilewati pembeli — itu yang terjadi
        pada bab Harapan. Cerita bab harus berupa kalimat jadi yang bisa ditiru."""
        for kunci in ["bab1_note", "bab2_note", "cinta_note", "momen_strip"]:
            with self.subTest(kunci=kunci):
                isi = self.bawaan[kunci]
                self.assertGreater(len(isi), 20, f"{kunci} terlalu pendek")
                self.assertNotIn("Tulis", isi)
                self.assertNotIn("di sini", isi)


class KalimatPenutupKosongTests(TestCase):
    """closing_line sengaja dikosongkan supaya nama penerima berdiri sendiri."""

    def setUp(self):
        self.template = Template.objects.create(
            slug="scrapbook-cerita", name="Scrapbook", category=CardType.BIRTHDAY,
            config=konfigurasi_scrapbook(),
        )

    def kartu(self, **kwargs):
        return GiftCard.objects.create(
            template=self.template, category=CardType.BIRTHDAY,
            status=GiftCard.Status.PAID, paid_at=timezone.now(),
            recipient_name="Nadia", sender_name="Raka", **kwargs
        )

    def test_kartu_terbit_hanya_menampilkan_nama(self):
        isi = self.client.get(f"/{self.kartu().id}/").content.decode()
        self.assertIn(
            '<p class="big-script reveal"><span></span> <span>Nadia</span></p>', isi
        )

    def test_editor_tetap_bisa_diklik(self):
        """Span kosong tidak punya lebar dan tidak bisa diklik — pembeli yang
        ingin menambahkan kalimatnya kembali kehilangan jalan masuk. Karena itu
        saat mengedit slotnya diisi placeholder."""
        isi = self.client.get(
            reverse("cards:editor_frame", args=["scrapbook-cerita"])
        ).content.decode()
        self.assertIn('data-edit="closing_line"', isi)
        self.assertIn('data-placeholder="Kalimat penutup"', isi)
        self.assertIn(">Kalimat penutup</span>", isi)

    def test_kalimat_yang_sudah_ditulis_pembeli_tetap_tampil(self):
        """Mengubah bawaan tidak boleh menghapus tulisan orang. Bawaan hanya
        dipakai kalau pembeli tidak pernah mengisi slotnya."""
        kartu = self.kartu(texts={"closing_line": "Selamat ulang tahun,"})
        isi = self.client.get(f"/{kartu.id}/").content.decode()
        self.assertIn("Selamat ulang tahun,", isi)
