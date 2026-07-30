"""Tes unggah foto sungguhan lewat API editor, dengan file betulan.

Ada karena bug nyata: dulu widget banyak-file dipasang tanpa field-nya, sehingga
SEMUA unggahan gagal diam-diam sementara tes lain tetap hijau. Sejak itu foto
diunggah lewat API begitu dipilih, bukan menunggu tombol simpan.
"""

import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from cards.models import CardType, GiftCard, GiftPhoto, Template

FRAMES = [
    {"key": "p1", "label": "Polaroid kiri", "area": "letter"},
    {"key": "p2", "label": "Polaroid tengah", "area": "letter"},
]


def make_image(name="foto.jpg", fmt="JPEG", size=(900, 700), color=(200, 150, 160)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, fmt)
    buffer.seek(0)
    content_type = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}[fmt]
    return SimpleUploadedFile(name, buffer.read(), content_type=content_type)


@override_settings(MEDIA_ROOT="/tmp/giftcard-test-media")
class PhotoApiTests(TestCase):
    def setUp(self):
        self.template = Template.objects.create(
            slug="amplop-merah",
            name="Amplop Merah",
            category=CardType.BIRTHDAY,
            config={"renderer": "birthday", "frames": FRAMES},
        )
        # Buat draft lewat API supaya sesi menandai kepemilikannya.
        response = self.client.post(
            reverse("cards:api_draft", args=[self.template.slug]),
            content_type="application/json",
            data="{}",
        )
        self.card_id = response.json()["card"]
        self.upload_url = reverse("cards:api_photo_upload", args=[self.card_id])

    def upload(self, image, slot=""):
        return self.client.post(self.upload_url, {"photo": image, "slot": slot})

    def test_draft_is_created_once_per_session(self):
        again = self.client.post(
            reverse("cards:api_draft", args=[self.template.slug]),
            content_type="application/json",
            data='{"card": "%s"}' % self.card_id,
        )
        self.assertEqual(again.json()["card"], self.card_id)
        self.assertFalse(again.json()["created"])
        self.assertEqual(GiftCard.objects.count(), 1)

    def test_upload_into_frame(self):
        response = self.upload(make_image("a.jpg"), slot="p1")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["slot"], "p1")
        self.assertEqual(GiftPhoto.objects.get().slot, "p1")

    def test_upload_into_gallery_when_no_slot(self):
        self.upload(make_image("a.jpg"))
        self.assertEqual(GiftPhoto.objects.get().slot, "")

    def test_second_upload_replaces_photo_in_same_frame(self):
        self.upload(make_image("a.jpg"), slot="p1")
        self.upload(make_image("b.jpg"), slot="p1")
        self.assertEqual(GiftPhoto.objects.filter(slot="p1").count(), 1)

    def test_unknown_frame_is_rejected(self):
        response = self.upload(make_image("a.jpg"), slot="tidak-ada")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(GiftPhoto.objects.count(), 0)

    def test_png_and_webp_accepted_and_normalised_to_jpeg(self):
        self.upload(make_image("a.png", "PNG"))
        self.upload(make_image("b.webp", "WEBP"))
        self.assertEqual(GiftPhoto.objects.count(), 2)
        for photo in GiftPhoto.objects.all():
            self.assertTrue(photo.image.name.endswith(".jpg"))

    def test_oversized_image_is_resized(self):
        self.upload(make_image("big.jpg", size=(4000, 3000)))
        with Image.open(GiftPhoto.objects.get().image) as image:
            self.assertLessEqual(max(image.size), 1600)

    def test_non_image_is_rejected_with_message(self):
        fake = SimpleUploadedFile("virus.jpg", b"bukan gambar", content_type="image/jpeg")
        response = self.client.post(self.upload_url, {"photo": fake})
        self.assertEqual(response.status_code, 400)
        self.assertIn("gambar", response.json()["detail"].lower())
        self.assertEqual(GiftPhoto.objects.count(), 0)

    def test_missing_file_is_rejected(self):
        self.assertEqual(self.client.post(self.upload_url, {}).status_code, 400)

    @override_settings(MAX_PHOTOS_PER_CARD=2)
    def test_gallery_limit_enforced(self):
        self.upload(make_image("a.jpg"))
        self.upload(make_image("b.jpg"))
        response = self.upload(make_image("c.jpg"))
        self.assertEqual(response.status_code, 409)
        self.assertEqual(GiftPhoto.objects.count(), 2)

    @override_settings(MAX_PHOTOS_PER_CARD=1)
    def test_frame_photos_do_not_count_against_gallery_limit(self):
        self.assertEqual(self.upload(make_image("a.jpg"), slot="p1").status_code, 201)
        self.assertEqual(self.upload(make_image("b.jpg"), slot="p2").status_code, 201)
        self.assertEqual(self.upload(make_image("c.jpg")).status_code, 201)

    def test_caption_can_be_set(self):
        photo_id = self.upload(make_image("a.jpg")).json()["id"]
        response = self.client.post(
            reverse("cards:api_photo_caption", args=[self.card_id, photo_id]),
            content_type="application/json",
            data='{"caption": "senja"}',
        )
        self.assertEqual(response.json()["caption"], "senja")

    def test_photo_can_be_deleted(self):
        photo_id = self.upload(make_image("a.jpg")).json()["id"]
        response = self.client.post(
            reverse("cards:api_photo_delete", args=[self.card_id, photo_id])
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(GiftPhoto.objects.count(), 0)

    def test_other_session_cannot_upload(self):
        from django.test import Client

        stranger = Client()
        response = stranger.post(self.upload_url, {"photo": make_image("a.jpg")})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(GiftPhoto.objects.count(), 0)

    def test_other_session_cannot_delete(self):
        from django.test import Client

        photo_id = self.upload(make_image("a.jpg")).json()["id"]
        stranger = Client()
        response = stranger.post(
            reverse("cards:api_photo_delete", args=[self.card_id, photo_id])
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(GiftPhoto.objects.count(), 1)

    def test_paid_card_cannot_be_changed(self):
        GiftCard.objects.filter(pk=self.card_id).update(status=GiftCard.Status.PAID)
        response = self.upload(make_image("a.jpg"))
        self.assertEqual(response.status_code, 409)

    def test_uploaded_photo_reaches_the_card_page(self):
        self.upload(make_image("a.jpg"), slot="p1")
        photo_id = self.upload(make_image("b.jpg")).json()["id"]
        self.client.post(
            reverse("cards:api_photo_caption", args=[self.card_id, photo_id]),
            content_type="application/json",
            data='{"caption": "senja"}',
        )
        GiftCard.objects.filter(pk=self.card_id).update(status=GiftCard.Status.PAID)
        response = self.client.get(reverse("cards:public", args=[self.card_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "senja")


@override_settings(MEDIA_ROOT="/tmp/giftcard-test-media")
class EditorSavesTextTests(TestCase):
    """Editor menyimpan teks & gaya; foto sudah tersimpan lebih dulu lewat API."""

    def setUp(self):
        self.template = Template.objects.create(
            slug="amplop-merah",
            name="Amplop Merah",
            category=CardType.BIRTHDAY,
            config={"renderer": "birthday", "frames": FRAMES},
        )
        self.url = reverse("cards:editor", args=[self.template.slug])

    def test_photos_survive_saving_the_text(self):
        draft = self.client.post(
            reverse("cards:api_draft", args=[self.template.slug]),
            content_type="application/json",
            data="{}",
        ).json()["card"]
        self.client.post(
            reverse("cards:api_photo_upload", args=[draft]),
            {"photo": make_image("a.jpg"), "slot": "p1"},
        )

        response = self.client.post(
            self.url,
            {
                "card": draft,
                "recipient_name": "Nadia",
                "sender_name": "Raka",
                "message": "halo",
                "youtube_url": "",
                "favorite_flower": "",
                "affirmations": "",
                "style_json": "{}",
            },
        )
        self.assertRedirects(response, reverse("cards:pay", args=[draft]))
        card = GiftCard.objects.get(pk=draft)
        self.assertEqual(card.recipient_name, "Nadia")
        # Inti bug lama: foto tidak boleh hilang saat teks disimpan.
        self.assertEqual(card.photos.count(), 1)

    def test_editor_frame_renders_clickable_markers(self):
        response = self.client.get(
            reverse("cards:editor_frame", args=[self.template.slug])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-edit="recipient"')
        self.assertContains(response, 'data-edit="message"')
        self.assertContains(response, 'data-frame="p1"')
        self.assertContains(response, "card-frame.js")

    def test_real_card_has_no_editing_markers(self):
        card = GiftCard.objects.create(
            template=self.template,
            category=CardType.BIRTHDAY,
            status=GiftCard.Status.PAID,
            message="halo",
        )
        response = self.client.get(reverse("cards:public", args=[card.id]))
        self.assertNotContains(response, "data-edit=")
        self.assertNotContains(response, "card-frame.js")


class FramingHeaderTests(TestCase):
    """Iframe editor harus boleh dimuat; kartu asli tidak boleh disematkan."""

    def setUp(self):
        self.template = Template.objects.create(
            slug="amplop-merah",
            name="Amplop Merah",
            category=CardType.BIRTHDAY,
            config={"renderer": "birthday", "frames": FRAMES},
        )

    def test_editor_frame_allows_sameorigin(self):
        response = self.client.get(
            reverse("cards:editor_frame", args=[self.template.slug])
        )
        # Tanpa ini browser menolak merender iframe dan preview jadi kotak putih.
        self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")

    def test_public_card_still_denies_framing(self):
        card = GiftCard.objects.create(
            template=self.template,
            category=CardType.BIRTHDAY,
            status=GiftCard.Status.PAID,
        )
        response = self.client.get(reverse("cards:public", args=[card.id]))
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")


@override_settings(MEDIA_ROOT="/tmp/giftcard-test-media")
class AutosaveTests(TestCase):
    """Editan tersimpan otomatis, supaya tidak hilang saat preview dimuat ulang."""

    def setUp(self):
        self.template = Template.objects.create(
            slug="amplop-merah",
            name="Amplop Merah",
            category=CardType.BIRTHDAY,
            config={
                "renderer": "birthday",
                "frames": [{"key": "p1", "label": "Polaroid", "area": "letter"}],
                "texts": [
                    {"key": "cover_title", "label": "Judul", "default": "Happy Birthday!"}
                ],
                "surfaces": [{"key": "scene_bg", "label": "Latar", "default": "#9E1B32"}],
            },
        )
        self.card_id = self.client.post(
            reverse("cards:api_draft", args=[self.template.slug]),
            content_type="application/json",
            data="{}",
        ).json()["card"]
        self.url = reverse("cards:api_content", args=[self.card_id])

    def save(self, payload):
        import json

        return self.client.post(
            self.url, content_type="application/json", data=json.dumps(payload)
        )

    def test_text_and_style_saved(self):
        response = self.save(
            {
                "fields": {"recipient": "Nadia", "message": "halo"},
                "texts": {"cover_title": "Selamat!"},
                "style": {"elements": {"cover_title": {"font": "lobster"}},
                          "colors": {"scene_bg": "#123456"}},
            }
        )
        self.assertEqual(response.status_code, 200)
        card = GiftCard.objects.get(pk=self.card_id)
        self.assertEqual(card.recipient_name, "Nadia")
        self.assertEqual(card.text("cover_title"), "Selamat!")
        self.assertEqual(card.style["elements"]["cover_title"]["font"], "lobster")
        self.assertEqual(card.style["colors"]["scene_bg"], "#123456")

    def test_saved_edits_survive_a_preview_reload(self):
        # Inti keluhan: unggah foto memuat ulang preview dan editan hilang.
        self.save({"fields": {"recipient": "Nadia"}, "texts": {}, "style": {}})
        self.client.post(
            reverse("cards:api_photo_upload", args=[self.card_id]),
            {"photo": make_image("a.jpg"), "slot": "p1"},
        )
        response = self.client.get(
            reverse("cards:editor_frame", args=[self.template.slug])
            + "?card=" + self.card_id
        )
        self.assertContains(response, "Nadia")

    def test_malicious_style_sanitised_on_autosave(self):
        evil = {"elements": {"cover_title": {"color": "#fff;} x{}"}}}
        self.save({"style": evil})
        card = GiftCard.objects.get(pk=self.card_id)
        self.assertEqual(card.style["elements"], {})

    def test_unknown_text_key_dropped_on_autosave(self):
        self.save({"texts": {"kunci_asing": "x", "cover_title": "ok"}})
        self.assertEqual(
            GiftCard.objects.get(pk=self.card_id).texts, {"cover_title": "ok"}
        )

    def test_other_session_cannot_autosave(self):
        from django.test import Client

        stranger = Client()
        response = stranger.post(
            self.url, content_type="application/json",
            data='{"fields": {"recipient": "Jahat"}}',
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(GiftCard.objects.get(pk=self.card_id).recipient_name, "")

    def test_paid_card_cannot_be_autosaved(self):
        GiftCard.objects.filter(pk=self.card_id).update(status=GiftCard.Status.PAID)
        response = self.save({"fields": {"recipient": "X"}})
        self.assertEqual(response.status_code, 409)

    def test_bad_youtube_link_does_not_break_saving(self):
        response = self.save({"fields": {"recipient": "Nadia", "youtube_url": "bukan link"}})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(GiftCard.objects.get(pk=self.card_id).recipient_name, "Nadia")

    def test_autosave_never_overwrites_payment_status(self):
        """Bug nyata: autosave menulis SELURUH kolom dari objek yang sudah basi.

        Kalau webhook Midtrans melunasi kartu tepat setelah view membaca
        barisnya, penyimpanan mengembalikannya ke `pending` dan menghapus
        paid_at — pembeli sudah bayar tapi kartunya tetap terkunci.

        Webhook disisipkan lewat patch supaya benar-benar tiba DI TENGAH
        permintaan: setelah view membaca kartu, sebelum ia menyimpan.
        """
        from unittest.mock import patch

        from django.utils import timezone

        from cards import api_photos

        GiftCard.objects.filter(pk=self.card_id).update(
            status=GiftCard.Status.PENDING
        )

        real_sanitize = api_photos.sanitize_style

        def webhook_lands_mid_request(raw):
            GiftCard.objects.filter(pk=self.card_id).update(
                status=GiftCard.Status.PAID,
                paid_at=timezone.now(),
                gateway_txn_id="txn-9",
            )
            return real_sanitize(raw)

        with patch.object(api_photos, "sanitize_style", webhook_lands_mid_request):
            response = self.save({"fields": {"recipient": "Nadia"}})
        self.assertEqual(response.status_code, 200)

        card = GiftCard.objects.get(pk=self.card_id)
        self.assertEqual(card.status, GiftCard.Status.PAID)
        self.assertIsNotNone(card.paid_at)
        self.assertEqual(card.gateway_txn_id, "txn-9")
        # Isi yang dikirim tetap tersimpan — perbaikannya bukan "berhenti menyimpan".
        self.assertEqual(card.recipient_name, "Nadia")


class FrameAreaTests(TestCase):
    """Bingkai hanya muncul di areanya sendiri."""

    def setUp(self):
        self.template = Template.objects.create(
            slug="amplop-merah",
            name="Amplop Merah",
            category=CardType.BIRTHDAY,
            config={
                "renderer": "birthday",
                "frames": [
                    {"key": "hero", "label": "Latar ucapan", "area": "hero"},
                    {"key": "p1", "label": "Polaroid kiri", "area": "letter"},
                    {"key": "p2", "label": "Polaroid tengah", "area": "letter"},
                ],
            },
        )

    def test_letter_shows_only_letter_frames(self):
        response = self.client.get(
            reverse("cards:editor_frame", args=[self.template.slug])
        )
        body = response.content.decode()
        # Bug lama: bingkai latar ucapan ikut tampil sebagai polaroid di Surat,
        # sehingga foto yang ditaruh di situ malah jadi latar.
        letter = body[body.index('class="polastrip"') : body.index("</section>", body.index('class="polastrip"'))]
        self.assertIn('data-frame="p1"', letter)
        self.assertIn('data-frame="p2"', letter)
        self.assertNotIn('data-frame="hero"', letter)

    def test_hero_frame_still_exists_in_its_own_scene(self):
        response = self.client.get(
            reverse("cards:editor_frame", args=[self.template.slug])
        )
        self.assertContains(response, 'data-frame="hero"')


@override_settings(MEDIA_ROOT="/tmp/giftcard-test-media")
class BerkasYatimTests(TestCase):
    """FileField tidak menghapus berkas fisiknya sendiri.

    Sebelum ada signal post_delete, berkas hanya terhapus di tiga jalur yang
    memanggilnya eksplisit. Hapus lewat admin, cascade dari GiftCard, atau
    .delete() pada queryset meninggalkan berkas yatim yang memakan disk
    selamanya — itu kebocoran penyimpanan yang sesungguhnya.
    """

    def setUp(self):
        self.template = Template.objects.create(
            slug="t-yatim", name="T", category=CardType.BIRTHDAY,
            config={"renderer": "birthday"},
        )
        self.card = GiftCard.objects.create(
            template=self.template, category=CardType.BIRTHDAY
        )

    def _foto(self):
        photo = GiftPhoto.objects.create(card=self.card, image=make_image())
        self.assertTrue(photo.image.storage.exists(photo.image.name))
        return photo, photo.image.name

    def test_hapus_foto_menghapus_berkasnya(self):
        photo, path = self._foto()
        storage = photo.image.storage
        photo.delete()
        self.assertFalse(storage.exists(path), "berkas tertinggal setelah baris dihapus")

    def test_hapus_kartu_menghapus_berkas_fotonya(self):
        photo, path = self._foto()
        storage = photo.image.storage
        self.card.delete()   # cascade
        self.assertFalse(storage.exists(path), "cascade meninggalkan berkas yatim")

    def test_hapus_lewat_queryset_menghapus_berkas(self):
        photo, path = self._foto()
        storage = photo.image.storage
        GiftPhoto.objects.filter(pk=photo.pk).delete()
        self.assertFalse(storage.exists(path), "queryset delete meninggalkan berkas yatim")


@override_settings(MEDIA_ROOT="/tmp/giftcard-test-media")
class PurgeDraftsTests(TestCase):
    def setUp(self):
        from datetime import timedelta

        from django.utils import timezone

        self.template = Template.objects.create(
            slug="t-purge", name="T", category=CardType.BIRTHDAY,
            config={"renderer": "birthday"},
        )
        self.lama = timezone.now() - timedelta(days=30)
        self.timedelta = timedelta
        self.timezone = timezone

    def _kartu(self, status, umur_jam):
        card = GiftCard.objects.create(
            template=self.template, category=CardType.BIRTHDAY, status=status
        )
        # updated_at auto_now — harus ditimpa lewat queryset update.
        GiftCard.objects.filter(pk=card.pk).update(
            updated_at=self.timezone.now() - self.timedelta(hours=umur_jam)
        )
        return card

    def _purge(self, **kwargs):
        from io import StringIO

        from django.core.management import call_command

        call_command("purge_drafts", stdout=StringIO(), **kwargs)

    def test_draft_basi_dihapus(self):
        card = self._kartu(GiftCard.Status.DRAFT, 48)
        self._purge()
        self.assertFalse(GiftCard.objects.filter(pk=card.pk).exists())

    def test_draft_baru_dipertahankan(self):
        card = self._kartu(GiftCard.Status.DRAFT, 2)
        self._purge()
        self.assertTrue(GiftCard.objects.filter(pk=card.pk).exists())

    def test_pending_basi_dihapus(self):
        """Dulu PENDING tidak pernah tersapu dan menumpuk selamanya."""
        card = self._kartu(GiftCard.Status.PENDING, 100)
        self._purge()
        self.assertFalse(GiftCard.objects.filter(pk=card.pk).exists())

    def test_pending_diberi_tenggang_lebih_panjang(self):
        """Pembeli yang baru transfer besok tidak boleh kehilangan kartunya."""
        card = self._kartu(GiftCard.Status.PENDING, 48)   # > 24 jam, < 72 jam
        self._purge()
        self.assertTrue(GiftCard.objects.filter(pk=card.pk).exists())

    def test_kartu_lunas_tidak_pernah_disentuh(self):
        card = self._kartu(GiftCard.Status.PAID, 24 * 365)
        self._purge()
        self.assertTrue(GiftCard.objects.filter(pk=card.pk).exists())

    def test_dry_run_tidak_menghapus(self):
        card = self._kartu(GiftCard.Status.DRAFT, 48)
        self._purge(dry_run=True)
        self.assertTrue(GiftCard.objects.filter(pk=card.pk).exists())

    def test_purge_menghapus_berkas_fotonya(self):
        card = self._kartu(GiftCard.Status.DRAFT, 48)
        photo = GiftPhoto.objects.create(card=card, image=make_image())
        storage, path = photo.image.storage, photo.image.name
        self._purge()
        self.assertFalse(storage.exists(path))
