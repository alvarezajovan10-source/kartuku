from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from cards.models import CardType, GiftCard, Template
from cards.utils import extract_youtube_id


class YouTubeExtractionTests(TestCase):
    def test_accepts_common_url_shapes(self):
        cases = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube.com/watch?list=PL123&v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ?t=42",
            "dQw4w9WgXcQ",
        ]
        for url in cases:
            with self.subTest(url=url):
                self.assertEqual(extract_youtube_id(url), "dQw4w9WgXcQ")

    def test_blank_is_allowed(self):
        self.assertEqual(extract_youtube_id(""), "")
        self.assertEqual(extract_youtube_id("   "), "")

    def test_rejects_non_youtube(self):
        for value in ["https://vimeo.com/12345", "https://evil.com/watch?v=abc", "halo"]:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    extract_youtube_id(value)


class PublicPageGatingTests(TestCase):
    def setUp(self):
        self.template = Template.objects.create(
            slug="t", name="T", category=CardType.BIRTHDAY
        )
        self.card = GiftCard.objects.create(
            template=self.template,
            category=CardType.BIRTHDAY,
            recipient_name="Rara",
            message="rahasia banget",
            status=GiftCard.Status.PENDING,
        )

    def test_unpaid_card_hides_content(self):
        response = self.client.get(reverse("cards:public", args=[self.card.id]))
        self.assertEqual(response.status_code, 402)
        self.assertNotContains(response, "rahasia banget", status_code=402)

    def test_paid_card_renders_content(self):
        self.card.status = GiftCard.Status.PAID
        self.card.save()
        response = self.client.get(reverse("cards:public", args=[self.card.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rahasia banget")

    def test_embed_url_uses_nocookie(self):
        self.card.youtube_video_id = "dQw4w9WgXcQ"
        self.assertEqual(
            self.card.youtube_embed_url(),
            "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
        )


class BirthdayRendererTests(TestCase):
    """Kartu birthday memakai render khusus; kategori lain jatuh ke public.html."""

    def setUp(self):
        self.birthday_template = Template.objects.create(
            slug="amplop-merah",
            name="Amplop Merah",
            category=CardType.BIRTHDAY,
            config={"renderer": "birthday"},
        )
        self.card = GiftCard.objects.create(
            template=self.birthday_template,
            category=CardType.BIRTHDAY,
            recipient_name="Nadia",
            sender_name="Raka",
            message="Selamat ulang tahun ya",
            favorite_flower="Sunflower",
            affirmations="Kamu berharga.\nKamu kuat.",
            status=GiftCard.Status.PAID,
        )

    def get(self):
        return self.client.get(reverse("cards:public", args=[self.card.id]))

    def test_uses_birthday_renderer(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cards/render/birthday.html")
        # Nama dibungkus <span data-edit> supaya bisa diklik di editor.
        self.assertContains(response, "Nadia")
        self.assertContains(response, "Sunflower")
        self.assertContains(response, "Kamu berharga.")

    def test_unpaid_birthday_card_still_locked(self):
        self.card.status = GiftCard.Status.PENDING
        self.card.save()
        response = self.get()
        self.assertEqual(response.status_code, 402)
        self.assertTemplateNotUsed(response, "cards/render/birthday.html")
        self.assertNotContains(response, "Sunflower", status_code=402)

    def test_sections_hidden_when_data_missing(self):
        self.card.favorite_flower = ""
        self.card.affirmations = ""
        self.card.youtube_video_id = ""
        self.card.save()
        response = self.get()
        self.assertNotContains(response, 'data-go="flower"')
        self.assertNotContains(response, 'data-go="song"')
        self.assertNotContains(response, 'data-go="gallery"')
        # Kue selalu ada — tidak butuh data dari pengguna.
        self.assertContains(response, 'data-go="cake"')

    def test_song_section_present_with_video(self):
        self.card.youtube_video_id = "dQw4w9WgXcQ"
        self.card.save()
        response = self.get()
        self.assertContains(response, 'data-go="song"')
        # Lagu tidak lagi di-embed; piringan hitam menautkan ke sumbernya.
        self.assertContains(response, "youtube.com/watch?v=dQw4w9WgXcQ")

    def test_song_shows_cover_and_title_when_known(self):
        self.card.youtube_video_id = "dQw4w9WgXcQ"
        self.card.track_title = "Judul Lagu"
        self.card.track_artist = "Nama Artis"
        self.card.track_cover_url = "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
        self.card.save()
        response = self.get()
        self.assertContains(response, "i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg")
        self.assertContains(response, "Judul Lagu")
        self.assertContains(response, "Nama Artis")

    def test_background_music_iframe_for_youtube(self):
        self.card.youtube_video_id = "dQw4w9WgXcQ"
        self.card.save()
        response = self.get()
        self.assertContains(response, 'id="bgm"')
        # Pemutar dibangun IFrame Player API resmi oleh js/bgm.js — HTML cuma
        # membawa id video dan memuat skripnya.
        self.assertContains(response, 'data-vid="dQw4w9WgXcQ"')
        self.assertContains(response, "js/bgm.js")
        self.assertContains(response, 'id="bgmFab"')

    def test_background_music_in_all_renderers(self):
        # Musik latar itu komponen bersama — tiap renderer wajib memuatnya.
        for slug, renderer, category in [
            ("kanvas-tes", "kanvas", CardType.ANNIVERSARY),
            ("scrapbook-tes", "scrapbook", CardType.LOVE_STORY),
        ]:
            template = Template.objects.create(
                slug=slug, name=slug, category=category,
                config={"renderer": renderer},
            )
            card = GiftCard.objects.create(
                template=template, category=category,
                youtube_video_id="dQw4w9WgXcQ",
                status=GiftCard.Status.PAID,
            )
            response = self.client.get(reverse("cards:public", args=[card.id]))
            self.assertContains(
                response, 'id="bgm"',
                msg_prefix=f"renderer {renderer} tidak memuat musik latar",
            )
            self.assertContains(
                response, 'id="fsFab"',
                msg_prefix=f"renderer {renderer} tidak memuat tombol layar penuh",
            )

    def test_no_background_music_for_spotify(self):
        # Spotify tidak bisa dikendalikan dari luar embed-nya.
        self.card.youtube_video_id = ""
        self.card.spotify_track_id = "7HhKuJbtiNbZsEDLNQvOnH"
        self.card.save()
        response = self.get()
        self.assertNotContains(response, 'id="bgm"')

    def test_song_hides_artist_when_unknown(self):
        self.card.youtube_video_id = "dQw4w9WgXcQ"
        self.card.track_title = "Judul Lagu"
        self.card.save()
        response = self.get()
        self.assertNotContains(response, 'class="t-artist"')

    def test_affirmations_capped_at_four(self):
        self.card.affirmations = "a\nb\nc\nd\ne\nf"
        self.card.save()
        self.assertEqual(self.card.affirmation_list(), ["a", "b", "c", "d"])

    def test_other_category_falls_back_to_simple_page(self):
        plain = Template.objects.create(
            slug="klasik-lamaran", name="Klasik", category=CardType.PROPOSAL
        )
        card = GiftCard.objects.create(
            template=plain,
            category=CardType.PROPOSAL,
            message="mau nikah sama aku?",
            status=GiftCard.Status.PAID,
        )
        response = self.client.get(reverse("cards:public", args=[card.id]))
        self.assertTemplateUsed(response, "cards/public.html")
        self.assertContains(response, "mau nikah sama aku?")

    def test_message_is_escaped(self):
        self.card.message = "<script>alert(1)</script>"
        self.card.save()
        response = self.get()
        self.assertNotContains(response, "<script>alert(1)</script>")


class GalleryAndPreviewTests(TestCase):
    def setUp(self):
        self.t1 = Template.objects.create(
            slug="amplop-merah",
            name="Amplop Merah",
            category=CardType.BIRTHDAY,
            config={"renderer": "birthday", "accent": "#9e1b32"},
        )
        self.t2 = Template.objects.create(
            slug="pastel-manis", name="Pastel Manis", category=CardType.BIRTHDAY
        )
        self.hidden = Template.objects.create(
            slug="belum-siap",
            name="Belum Siap",
            category=CardType.BIRTHDAY,
            is_active=False,
        )
        Template.objects.create(
            slug="lamaran-klasik", name="Klasik", category=CardType.PROPOSAL
        )

    def test_gallery_lists_only_active_templates_of_category(self):
        response = self.client.get(reverse("cards:gallery", args=["birthday"]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Amplop Merah")
        self.assertContains(response, "Pastel Manis")
        self.assertNotContains(response, "Belum Siap")
        self.assertNotContains(response, "lamaran-klasik")

    def test_unknown_category_is_404(self):
        response = self.client.get(reverse("cards:gallery", args=["natal"]))
        self.assertEqual(response.status_code, 404)

    def test_landing_points_to_gallery_not_editor(self):
        response = self.client.get(reverse("cards:landing"))
        self.assertContains(response, reverse("cards:gallery", args=["birthday"]))

    def test_preview_renders_sample_without_creating_card(self):
        response = self.client.get(reverse("cards:preview", args=["amplop-merah"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cards/render/birthday.html")
        self.assertContains(response, "preview-bar")
        self.assertContains(response, reverse("cards:editor", args=["amplop-merah"]))
        self.assertEqual(GiftCard.objects.count(), 0)

    def test_preview_of_inactive_template_is_404(self):
        response = self.client.get(reverse("cards:preview", args=["belum-siap"]))
        self.assertEqual(response.status_code, 404)

    def test_real_card_has_no_preview_bar(self):
        card = GiftCard.objects.create(
            template=self.t1,
            category=CardType.BIRTHDAY,
            recipient_name="Nadia",
            message="halo",
            status=GiftCard.Status.PAID,
        )
        response = self.client.get(reverse("cards:public", args=[card.id]))
        self.assertNotContains(response, "preview-bar")


class OwnerBypassTests(TestCase):
    """Jalur gratis pemilik harus mustahil dipicu pengunjung biasa."""

    def setUp(self):
        from django.contrib.auth.models import User

        self.staff = User.objects.create_user(
            "jepa", password="rahasia-panjang-123", is_staff=True
        )
        self.biasa = User.objects.create_user("orang", password="rahasia-panjang-123")
        self.template = Template.objects.create(
            slug="amplop-merah",
            name="Amplop Merah",
            category=CardType.BIRTHDAY,
            config={"renderer": "birthday"},
        )
        self.card = GiftCard.objects.create(
            template=self.template,
            category=CardType.BIRTHDAY,
            recipient_name="Nadia",
            message="rahasia banget",
            status=GiftCard.Status.PENDING,
        )
        self.url = reverse("cards:mark_paid", args=[self.card.id])

    def test_staff_can_activate_for_free(self):
        self.client.force_login(self.staff)
        response = self.client.post(self.url)
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PAID)
        self.assertTrue(self.card.comped)
        self.assertIsNotNone(self.card.paid_at)
        self.assertRedirects(response, reverse("cards:success", args=[self.card.id]))

    def test_anonymous_cannot_activate(self):
        # Test berjalan dengan DEBUG=False — kondisi produksi.
        response = self.client.post(self.url)
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PENDING)
        self.assertFalse(self.card.comped)
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=True)
    def test_debug_mode_allows_anonymous_activation(self):
        # Jalan pintas dev: DEBUG aktif = boleh tanpa login. Tidak pernah
        # berlaku di produksi karena DEBUG wajib mati di sana.
        response = self.client.post(self.url)
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PAID)
        self.assertTrue(self.card.comped)
        self.assertRedirects(response, reverse("cards:success", args=[self.card.id]))

    def test_logged_in_non_staff_cannot_activate(self):
        self.client.force_login(self.biasa)
        self.client.post(self.url)
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PENDING)
        self.assertFalse(self.card.comped)

    @override_settings(DEBUG=False)
    def test_my_cards_blocked_for_public(self):
        # DEBUG mati = kondisi produksi; daftar ini memuat nama penerima
        # dan link kartu orang lain, jadi tidak boleh terbuka.
        response = self.client.get(reverse("cards:my_cards"))
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False)
    def test_my_cards_open_for_staff(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("cards:my_cards"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nadia")

    @override_settings(DEBUG=True)
    def test_my_cards_open_in_debug(self):
        response = self.client.get(reverse("cards:my_cards"))
        self.assertEqual(response.status_code, 200)

    def test_get_request_is_rejected(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.card.refresh_from_db()
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.card.status, GiftCard.Status.PENDING)

    def test_staff_sees_unpaid_card_with_warning_banner(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("cards:public", args=[self.card.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "rahasia banget")
        self.assertContains(response, "Mode pemilik")

    def test_non_staff_still_blocked_from_unpaid_card(self):
        self.client.force_login(self.biasa)
        response = self.client.get(reverse("cards:public", args=[self.card.id]))
        self.assertEqual(response.status_code, 402)
        self.assertNotContains(response, "rahasia banget", status_code=402)

    def test_paid_card_shows_no_owner_banner_to_staff(self):
        self.card.status = GiftCard.Status.PAID
        self.card.save()
        self.client.force_login(self.staff)
        response = self.client.get(reverse("cards:public", args=[self.card.id]))
        self.assertNotContains(response, "Mode pemilik")

    def test_activating_twice_keeps_first_timestamp(self):
        self.client.force_login(self.staff)
        self.client.post(self.url)
        self.card.refresh_from_db()
        first = self.card.paid_at
        self.client.post(self.url)
        self.card.refresh_from_db()
        self.assertEqual(self.card.paid_at, first)

    def test_real_payment_is_not_marked_comped(self):
        self.card.status = GiftCard.Status.PAID
        self.card.save()
        self.assertFalse(self.card.comped)


class StatusEndpointTests(TestCase):
    def setUp(self):
        self.template = Template.objects.create(
            slug="t", name="T", category=CardType.BIRTHDAY
        )
        self.card = GiftCard.objects.create(
            template=self.template, category=CardType.BIRTHDAY
        )

    def test_status_reflects_db(self):
        url = reverse("cards:api_status", args=[self.card.id])
        self.assertEqual(self.client.get(url).json()["status"], "draft")

        self.card.status = GiftCard.Status.PAID
        self.card.save()
        body = self.client.get(url).json()
        self.assertEqual(body["status"], "paid")
        self.assertIn("redirect", body)

    def test_pending_past_expiry_reads_as_expired(self):
        from datetime import timedelta

        from django.utils import timezone

        self.card.status = GiftCard.Status.PENDING
        self.card.qr_expires_at = timezone.now() - timedelta(minutes=1)
        self.card.save()
        url = reverse("cards:api_status", args=[self.card.id])
        self.assertEqual(self.client.get(url).json()["status"], "expired")


class EditorTests(TestCase):
    def setUp(self):
        self.template = Template.objects.create(
            slug="klasik", name="Klasik", category=CardType.BIRTHDAY
        )

    def test_post_creates_draft_and_redirects_to_pay(self):
        response = self.client.post(
            reverse("cards:editor", args=["klasik"]),
            {
                "sender_name": "Jepa",
                "recipient_name": "Rara",
                "message": "Selamat ulang tahun",
                "youtube_url": "https://youtu.be/dQw4w9WgXcQ",
            },
        )
        card = GiftCard.objects.get()
        self.assertEqual(card.status, GiftCard.Status.DRAFT)
        self.assertEqual(card.youtube_video_id, "dQw4w9WgXcQ")
        self.assertEqual(card.amount, 15000)
        self.assertRedirects(response, reverse("cards:pay", args=[card.id]))

    def test_invalid_youtube_url_blocks_save(self):
        self.client.post(
            reverse("cards:editor", args=["klasik"]),
            {"sender_name": "A", "recipient_name": "B", "message": "x",
             "youtube_url": "https://vimeo.com/1"},
        )
        self.assertEqual(GiftCard.objects.count(), 0)

    def test_pay_page_blocked_for_other_session(self):
        card = GiftCard.objects.create(
            template=self.template, category=CardType.BIRTHDAY
        )
        response = self.client.get(reverse("cards:pay", args=[card.id]))
        self.assertEqual(response.status_code, 403)


class SlugAndMusicTests(TestCase):
    def setUp(self):
        self.template = Template.objects.create(
            slug="t", name="T", category=CardType.BIRTHDAY
        )
        self.card = GiftCard.objects.create(
            template=self.template, category=CardType.BIRTHDAY,
            status=GiftCard.Status.PAID, message="halo",
        )
        session = self.client.session
        session["owned_cards"] = [str(self.card.id)]
        session.save()

    def set_slug(self, slug):
        return self.client.post(
            reverse("cards:set_slug", args=[self.card.id]), {"slug": slug}
        )

    def test_slug_sets_and_resolves(self):
        self.set_slug("untuk-nadia")
        self.card.refresh_from_db()
        self.assertEqual(self.card.slug, "untuk-nadia")
        response = self.client.get("/g/untuk-nadia/")
        self.assertContains(response, "halo")
        # UUID lama tetap jalan
        self.assertEqual(self.client.get(f"/g/{self.card.id}/").status_code, 200)

    def test_taken_name_still_accepted_with_suffix(self):
        """Nama boleh kembar; URL-nya yang dibedakan pakai akhiran acak."""
        GiftCard.objects.create(
            template=self.template, category=CardType.BIRTHDAY,
            status=GiftCard.Status.PAID, slug="untuk-nadia",
        )
        self.set_slug("untuk-nadia")
        self.card.refresh_from_db()
        self.assertIsNotNone(self.card.slug)
        self.assertNotEqual(self.card.slug, "untuk-nadia")
        self.assertTrue(self.card.slug.startswith("untuk-nadia-"))
        # Kartu tetap bisa dibuka lewat slug barunya.
        response = self.client.get(reverse("cards:public", args=[self.card.slug]))
        self.assertEqual(response.status_code, 200)

    def test_reserved_slug_rejected(self):
        self.set_slug("admin")
        self.card.refresh_from_db()
        self.assertIsNone(self.card.slug)

    def test_stranger_cannot_set_slug(self):
        from django.test import Client

        response = Client().post(
            reverse("cards:set_slug", args=[self.card.id]), {"slug": "curian"}
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(YOUTUBE_API_KEY="")
    def test_embeddable_check_skipped_without_api_key(self):
        from cards.utils import check_youtube_embeddable

        ok, reason = check_youtube_embeddable("dQw4w9WgXcQ")
        self.assertTrue(ok)
        self.assertEqual(reason, "")

    @override_settings(YOUTUBE_API_KEY="kunci-palsu")
    def test_non_embeddable_video_rejected(self):
        from unittest.mock import patch

        from cards.utils import check_youtube_embeddable

        payload = {"items": [{"status": {"embeddable": False, "privacyStatus": "public"}}]}
        with patch("cards.utils._api_json", return_value=payload):
            ok, reason = check_youtube_embeddable("dQw4w9WgXcQ")
        self.assertFalse(ok)
        self.assertIn("Topic", reason)

    @override_settings(YOUTUBE_API_KEY="kunci-palsu")
    def test_embeddable_video_accepted(self):
        from unittest.mock import patch

        from cards.utils import check_youtube_embeddable

        payload = {"items": [{"status": {"embeddable": True, "privacyStatus": "public"}}]}
        with patch("cards.utils._api_json", return_value=payload):
            ok, _ = check_youtube_embeddable("dQw4w9WgXcQ")
        self.assertTrue(ok)

    @override_settings(YOUTUBE_API_KEY="kunci-palsu")
    def test_api_failure_does_not_block_user(self):
        # Masalah di sisi kita tidak boleh menghalangi user menyimpan kartunya.
        from unittest.mock import patch

        from cards.utils import check_youtube_embeddable

        with patch("cards.utils._api_json", return_value=None):
            ok, _ = check_youtube_embeddable("dQw4w9WgXcQ")
        self.assertTrue(ok)

    def test_same_slug_name_gets_suffix_instead_of_error(self):
        """Nama sama boleh dipakai banyak orang — URL-nya yang dibedakan."""
        from cards.views import _free_slug

        GiftCard.objects.filter(pk=self.card.pk).update(slug="halo")
        other = GiftCard.objects.create(
            template=self.card.template, category=self.card.category,
            status=GiftCard.Status.PAID,
        )
        slug = _free_slug("halo", other.pk)
        self.assertNotEqual(slug, "halo")
        self.assertTrue(slug.startswith("halo-"))
        self.assertFalse(GiftCard.objects.filter(slug=slug).exists())

    def test_free_slug_keeps_name_when_available(self):
        from cards.views import _free_slug

        self.assertEqual(_free_slug("nama-bebas", self.card.pk), "nama-bebas")

    def test_slug_suffix_is_not_sequential(self):
        """Akhiran berurutan bikin link kartu lain gampang ditebak."""
        from cards.views import _free_slug

        GiftCard.objects.filter(pk=self.card.pk).update(slug="halo")
        other = GiftCard.objects.create(
            template=self.card.template, category=self.card.category,
            status=GiftCard.Status.PAID,
        )
        hasil = {_free_slug("halo", other.pk) for _ in range(8)}
        self.assertNotIn("halo-2", hasil)
        self.assertGreater(len(hasil), 1)  # acak, bukan satu nilai tetap

    def test_spotify_link_rejected_with_explanation(self):
        # Spotify tidak bisa jadi musik latar (batasan Spotify) — ditolak
        # di depan supaya kartunya tidak bisu tanpa penjelasan.
        from django.core.exceptions import ValidationError

        from cards.utils import parse_music_link

        with self.assertRaisesMessage(ValidationError, "Spotify"):
            parse_music_link("https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC")
        yt, sp = parse_music_link("https://youtu.be/dQw4w9WgXcQ")
        self.assertEqual((yt, sp), ("dQw4w9WgXcQ", ""))

    def test_qr_png_served_for_paid_card(self):
        for params in ["style=kotak&warna=hitam", "style=hati&warna=pink"]:
            response = self.client.get(
                reverse("cards:qr", args=[self.card.id]) + "?" + params
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "image/png")
            self.assertTrue(response.content.startswith(b"\x89PNG"))

    def test_qr_hidden_for_unpaid_card(self):
        self.card.status = GiftCard.Status.PENDING
        self.card.save()
        response = self.client.get(reverse("cards:qr", args=[self.card.id]))
        self.assertEqual(response.status_code, 404)


class SeedIntegrityTests(TestCase):
    """Seed pernah menimpa config Amplop Merah dengan versi kosong — semua teks
    template lenyap dari kartu. Tes ini menjaga seed selalu lengkap."""

    def test_seeded_templates_with_renderer_have_texts_and_frames(self):
        from django.core.management import call_command

        call_command("seed_templates")
        birthday = Template.objects.get(slug="klasik-ulang-tahun")
        self.assertEqual(len(birthday.config["texts"]), 20)
        self.assertEqual(len(birthday.config["frames"]), 4)
        scrapbook = Template.objects.get(slug="scrapbook-cerita")
        self.assertGreaterEqual(len(scrapbook.config["texts"]), 14)
        self.assertEqual(len(scrapbook.config["frames"]), 7)
        # Tiap frame wajib punya area supaya tidak nyasar ke bagian lain.
        for template in (birthday, scrapbook):
            for frame in template.config["frames"]:
                self.assertIn("area", frame)

    def test_seed_is_idempotent(self):
        from django.core.management import call_command

        call_command("seed_templates")
        first = Template.objects.get(slug="klasik-ulang-tahun").config
        call_command("seed_templates")
        self.assertEqual(Template.objects.get(slug="klasik-ulang-tahun").config, first)


class InfoPagesTests(TestCase):
    """Template, Cara Kerja, Harga, Testimoni, dan FAQ kini halaman terpisah."""

    def setUp(self):
        Template.objects.create(
            slug="klasik-ulang-tahun", name="Amplop Merah",
            category=CardType.BIRTHDAY, config={"renderer": "birthday"},
        )

    def test_semua_halaman_terbuka(self):
        for name in [
            "page_templates", "page_how", "page_pricing",
            "page_testimonials", "page_faq",
        ]:
            with self.subTest(page=name):
                response = self.client.get(reverse(f"cards:{name}"))
                self.assertEqual(response.status_code, 200)

    def test_halaman_template_menampilkan_kategori(self):
        response = self.client.get(reverse("cards:page_templates"))
        self.assertContains(response, "Birthday")
        self.assertContains(response, reverse("cards:gallery", args=[CardType.BIRTHDAY]))

    def test_harga_diambil_dari_setelan(self):
        from django.conf import settings

        response = self.client.get(reverse("cards:page_pricing"))
        self.assertContains(response, f"{settings.CARD_PRICE:,}".replace(",", "."))

    def test_url_template_tidak_bentrok_dengan_galeri(self):
        """/template/ dan /template/<kategori>/ harus menuju view berbeda."""
        daftar = self.client.get(reverse("cards:page_templates"))
        galeri = self.client.get(reverse("cards:gallery", args=[CardType.BIRTHDAY]))
        self.assertEqual(daftar.status_code, 200)
        self.assertEqual(galeri.status_code, 200)
        self.assertNotEqual(daftar.content, galeri.content)

    def test_navigasi_menunjuk_halaman_bukan_anchor(self):
        response = self.client.get(reverse("cards:landing"))
        self.assertContains(response, reverse("cards:page_faq"))
        self.assertNotContains(response, 'href="/#faq"')

    def test_menu_menandai_halaman_yang_dibuka(self):
        response = self.client.get(reverse("cards:page_faq"))
        self.assertContains(response, 'aria-current="page"')


class PurgeDraftsTests(TestCase):
    """Pembersih draft tidak boleh membuang kerja yang masih digarap.

    Patokannya updated_at, bukan created_at: kartu yang dibuat tiga hari lalu
    tapi disunting tadi pagi jelas belum ditinggalkan.
    """

    def setUp(self):
        self.template = Template.objects.create(
            slug="t", name="T", category=CardType.BIRTHDAY
        )

    def make(self, status, created_days, updated_hours):
        from datetime import timedelta

        from django.utils import timezone

        card = GiftCard.objects.create(
            template=self.template, category=CardType.BIRTHDAY, status=status
        )
        # auto_now / auto_now_add hanya bisa dilewati lewat update().
        GiftCard.objects.filter(pk=card.pk).update(
            created_at=timezone.now() - timedelta(days=created_days),
            updated_at=timezone.now() - timedelta(hours=updated_hours),
        )
        return card

    def purge(self):
        from io import StringIO

        from django.core.management import call_command

        call_command("purge_drafts", stdout=StringIO())

    def test_old_draft_still_being_edited_is_kept(self):
        card = self.make(GiftCard.Status.DRAFT, created_days=3, updated_hours=1)
        self.purge()
        self.assertTrue(GiftCard.objects.filter(pk=card.pk).exists())

    def test_abandoned_draft_is_removed(self):
        card = self.make(GiftCard.Status.DRAFT, created_days=3, updated_hours=48)
        self.purge()
        self.assertFalse(GiftCard.objects.filter(pk=card.pk).exists())

    def test_paid_card_is_never_removed(self):
        card = self.make(GiftCard.Status.PAID, created_days=90, updated_hours=90 * 24)
        self.purge()
        self.assertTrue(GiftCard.objects.filter(pk=card.pk).exists())


class AccessCodeTests(TestCase):
    """Kode sekali pakai — pengganti Midtrans saat bayar ditangani di luar situs."""

    def setUp(self):
        from cards.models import AccessCode

        self.template = Template.objects.create(
            slug="t-kode", name="T", category=CardType.BIRTHDAY
        )
        self.card = GiftCard.objects.create(
            template=self.template, category=CardType.BIRTHDAY,
            status=GiftCard.Status.DRAFT,
        )
        self.code = AccessCode.objects.create(code=AccessCode.generate_code())
        self.url = reverse("cards:redeem_code", args=[self.card.id])
        # Tandai kartu sebagai milik sesi ini, seperti setelah dibuat di editor.
        session = self.client.session
        session["owned_cards"] = [str(self.card.id)]
        session.save()

    def test_kode_valid_mengaktifkan_kartu(self):
        response = self.client.post(self.url, {"code": self.code.code})
        self.card.refresh_from_db()
        self.code.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PAID)
        self.assertIsNotNone(self.card.paid_at)
        self.assertFalse(self.card.comped, "penjualan asli, bukan digratiskan")
        self.assertEqual(self.card.gateway_order_id, self.code.code)
        self.assertTrue(self.code.is_used)
        self.assertEqual(self.code.card_id, self.card.id)
        self.assertRedirects(response, reverse("cards:success", args=[self.card.id]))

    def test_kode_tidak_bisa_dipakai_dua_kali(self):
        self.client.post(self.url, {"code": self.code.code})
        kedua = GiftCard.objects.create(
            template=self.template, category=CardType.BIRTHDAY,
            status=GiftCard.Status.DRAFT,
        )
        session = self.client.session
        session["owned_cards"] = [str(kedua.id)]
        session.save()
        self.client.post(
            reverse("cards:redeem_code", args=[kedua.id]), {"code": self.code.code}
        )
        kedua.refresh_from_db()
        self.assertEqual(kedua.status, GiftCard.Status.DRAFT)

    def test_kode_salah_tidak_mengaktifkan(self):
        self.client.post(self.url, {"code": "KRT-ZZZZ-ZZZZ"})
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.DRAFT)

    def test_bentuk_ketikan_bebas_tetap_diterima(self):
        """Pembeli menyalin kode dari email — bentuknya bermacam-macam."""
        from cards.models import AccessCode

        baku = self.code.code                      # KRT-A7K9-M3QP
        tanpa_strip = baku.replace("-", "")
        variasi = [
            baku.lower(),
            tanpa_strip,
            f"  {baku}  ",
            tanpa_strip[3:],                       # tanpa awalan KRT
        ]
        for bentuk in variasi:
            with self.subTest(bentuk=bentuk):
                self.assertEqual(AccessCode.normalize(bentuk), baku)

    def test_bentuk_ngawur_ditolak(self):
        from cards.models import AccessCode

        for buruk in ["", "halo", "KRT-123", "KRT-AAAA-BBBB-CCCC"]:
            with self.subTest(buruk=buruk):
                self.assertEqual(AccessCode.normalize(buruk), "")

    def test_kode_tidak_memakai_huruf_yang_mudah_tertukar(self):
        from cards.models import AccessCode

        for haram in "ILO01":
            self.assertNotIn(haram, AccessCode.ALPHABET)

    def test_orang_lain_tidak_bisa_menukarkan(self):
        other = self.client_class()   # sesi baru, bukan pemilik kartu
        response = other.post(self.url, {"code": self.code.code})
        self.card.refresh_from_db()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.card.status, GiftCard.Status.DRAFT)

    def test_percobaan_dibatasi(self):
        for _ in range(15):
            self.client.post(self.url, {"code": "KRT-ZZZZ-ZZZZ"})
        # Setelah batas terlampaui, kode yang benar pun ditolak sementara.
        self.client.post(self.url, {"code": self.code.code})
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.DRAFT)

    def test_halaman_bayar_sembunyikan_qris_tanpa_midtrans(self):
        with override_settings(MIDTRANS_SERVER_KEY=""):
            response = self.client.get(reverse("cards:pay", args=[self.card.id]))
        self.assertNotContains(response, 'id="pay-root"')
        self.assertContains(response, 'name="code"')

    def test_halaman_bayar_tampilkan_qris_saat_midtrans_aktif(self):
        with override_settings(MIDTRANS_SERVER_KEY="SB-Mid-server-palsu"):
            response = self.client.get(reverse("cards:pay", args=[self.card.id]))
        self.assertContains(response, 'id="pay-root"')

    def test_perintah_buat_kode(self):
        from io import StringIO

        from django.core.management import call_command

        from cards.models import AccessCode

        keluaran = StringIO()
        call_command("buat_kode", 3, catatan="uji", stdout=keluaran)
        dibuat = AccessCode.objects.filter(note="uji")
        self.assertEqual(dibuat.count(), 3)
        for entry in dibuat:
            self.assertIn(entry.code, keluaran.getvalue())
