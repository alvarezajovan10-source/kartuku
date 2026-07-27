from django.core.exceptions import ValidationError
from django.test import TestCase
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
        self.assertContains(response, "youtube-nocookie.com/embed/dQw4w9WgXcQ")

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
        response = self.client.post(self.url)
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PENDING)
        self.assertFalse(self.card.comped)
        self.assertEqual(response.status_code, 302)  # dialihkan ke login
        self.assertNotIn(reverse("cards:success", args=[self.card.id]), response["Location"])

    def test_logged_in_non_staff_cannot_activate(self):
        self.client.force_login(self.biasa)
        self.client.post(self.url)
        self.card.refresh_from_db()
        self.assertEqual(self.card.status, GiftCard.Status.PENDING)
        self.assertFalse(self.card.comped)

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

    def test_slug_must_be_unique(self):
        GiftCard.objects.create(
            template=self.template, category=CardType.BIRTHDAY,
            status=GiftCard.Status.PAID, slug="untuk-nadia",
        )
        self.set_slug("untuk-nadia")
        self.card.refresh_from_db()
        self.assertIsNone(self.card.slug)

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

    def test_spotify_link_parsed(self):
        from cards.utils import parse_music_link

        yt, sp = parse_music_link("https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC")
        self.assertEqual((yt, sp), ("", "4uLU6hMCjMI75M1A2tKUQC"))
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
