import json

from django.test import TestCase
from django.urls import reverse

from cards import styles
from cards.models import CardType, GiftCard, Template


class SanitizeStyleTests(TestCase):
    """Gaya dari user masuk ke CSS, jadi tidak ada nilai mentah yang lolos."""

    def test_defaults_when_empty(self):
        clean = styles.sanitize_style({})
        self.assertEqual(clean, styles.DEFAULT_STYLE)

    def test_garbage_input_falls_back(self):
        for junk in [None, "bukan dict", 42, [], {"title": "bukan dict"}]:
            with self.subTest(junk=junk):
                clean = styles.sanitize_style(junk)
                self.assertEqual(clean["title"], styles.DEFAULT_STYLE["title"])

    def test_css_injection_via_color_is_rejected(self):
        evil = {
            "bg": "red; background-image: url(https://jahat.example/x.png)",
            "title": {"color": "#fff; position:fixed; top:0"},
        }
        clean = styles.sanitize_style(evil)
        self.assertEqual(clean["bg"], styles.DEFAULT_STYLE["bg"])
        self.assertEqual(clean["title"]["color"], styles.DEFAULT_STYLE["title"]["color"])

    def test_unknown_font_key_is_rejected(self):
        clean = styles.sanitize_style({"title": {"font": "../../etc/passwd"}})
        self.assertEqual(clean["title"]["font"], styles.DEFAULT_STYLE["title"]["font"])

    def test_size_is_clamped(self):
        self.assertEqual(styles.sanitize_style({"title": {"size": 99}})["title"]["size"], styles.SIZE_MAX)
        self.assertEqual(styles.sanitize_style({"title": {"size": -5}})["title"]["size"], styles.SIZE_MIN)
        self.assertEqual(styles.sanitize_style({"title": {"size": "abc"}})["title"]["size"], 1.0)

    def test_align_must_be_known(self):
        clean = styles.sanitize_style({"title": {"align": "justify; content:'x'"}})
        self.assertEqual(clean["title"]["align"], "center")

    def test_valid_input_is_kept(self):
        clean = styles.sanitize_style(
            {"title": {"font": "sans", "color": "#ABCDEF", "size": 1.25, "align": "left"}}
        )
        self.assertEqual(
            clean["title"],
            {"font": "sans", "color": "#ABCDEF", "size": 1.25, "align": "left"},
        )

    def test_css_variables_contain_no_semicolon_from_user(self):
        css = styles.css_variables({"bg": "#fff; evil: 1", "title": {"color": "#000"}})
        # Nilai jahat tidak muncul; jumlah deklarasi tetap sesuai jumlah kunci.
        self.assertNotIn("evil", css)
        self.assertIn("--bg:#FAF2E4", css)

    def test_every_font_has_label_and_css(self):
        for key in styles.FONTS:
            self.assertIn(key, styles.FONT_LABELS)
            self.assertTrue(styles.FONTS[key][1])


class EditorStyleFlowTests(TestCase):
    def setUp(self):
        self.template = Template.objects.create(
            slug="kanvas-klasik",
            name="Kanvas Klasik",
            category=CardType.BIRTHDAY,
            config={"renderer": "kanvas"},
        )
        self.url = reverse("cards:editor", args=[self.template.slug])

    def post(self, style_json):
        return self.client.post(
            self.url,
            {
                "recipient_name": "Nadia",
                "sender_name": "Raka",
                "message": "halo",
                "youtube_url": "",
                "favorite_flower": "",
                "affirmations": "",
                "style_json": style_json,
            },
        )

    def test_style_is_saved_from_editor(self):
        chosen = {
            "title": {"font": "sans", "color": "#112233", "size": 1.4, "align": "left"},
            "bg": "#FFEEDD",
        }
        self.post(json.dumps(chosen))
        card = GiftCard.objects.get()
        self.assertEqual(card.style["title"]["font"], "sans")
        self.assertEqual(card.style["title"]["color"], "#112233")
        self.assertEqual(card.style["bg"], "#FFEEDD")

    def test_malicious_style_does_not_reach_database(self):
        self.post(json.dumps({"bg": "#fff;} body{display:none}"}))
        card = GiftCard.objects.get()
        self.assertEqual(card.style["bg"], styles.DEFAULT_STYLE["bg"])

    def test_broken_json_does_not_break_the_form(self):
        response = self.post("{bukan json")
        self.assertEqual(response.status_code, 302)  # tetap lanjut ke halaman bayar
        card = GiftCard.objects.get()
        self.assertEqual(card.style, styles.DEFAULT_STYLE)

    def test_missing_style_field_uses_defaults(self):
        self.client.post(
            self.url,
            {"recipient_name": "A", "sender_name": "B", "message": "c",
             "youtube_url": "", "favorite_flower": "", "affirmations": ""},
        )
        card = GiftCard.objects.get()
        self.assertEqual(card.style, styles.DEFAULT_STYLE)

    def test_editor_page_ships_valid_init_json(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="editor-init"')
        body = response.content.decode()
        start = body.index('id="editor-init" type="application/json">') + len(
            'id="editor-init" type="application/json">'
        )
        end = body.index("</script>", start)
        data = json.loads(body[start:end])  # gagal kalau escaping-nya salah
        self.assertIn("fonts", data)
        self.assertIn("style", data)
        self.assertEqual(data["maxPhotos"], 30)

    def test_card_page_renders_chosen_style(self):
        self.post(json.dumps({"title": {"font": "sans", "color": "#112233"}}))
        card = GiftCard.objects.get()
        card.status = GiftCard.Status.PAID
        card.save()
        response = self.client.get(reverse("cards:public", args=[card.id]))
        self.assertTemplateUsed(response, "cards/render/kanvas.html")
        self.assertContains(response, "--title-color:#112233")


class PhotoLimitTests(TestCase):
    def test_limit_is_thirty(self):
        from django.conf import settings

        self.assertEqual(settings.MAX_PHOTOS_PER_CARD, 30)


class SurfaceColorTests(TestCase):
    """Warna permukaan jadi bagian nama CSS var, jadi kuncinya harus ketat."""

    def test_valid_colors_kept(self):
        clean = styles.sanitize_style({"colors": {"cover_bg": "#AABBCC"}})
        self.assertEqual(clean["colors"], {"cover_bg": "#AABBCC"})

    def test_bad_key_rejected(self):
        for key in ["cover-bg; x:1", "Cover_BG", "a" * 40, "../x", "bg}"]:
            with self.subTest(key=key):
                clean = styles.sanitize_style({"colors": {key: "#AABBCC"}})
                self.assertEqual(clean["colors"], {})

    def test_bad_value_rejected(self):
        clean = styles.sanitize_style({"colors": {"cover_bg": "red;position:fixed"}})
        self.assertEqual(clean["colors"], {})

    def test_color_count_capped(self):
        many = {f"k{i}": "#000000" for i in range(50)}
        clean = styles.sanitize_style({"colors": many})
        self.assertLessEqual(len(clean["colors"]), styles.MAX_COLORS)

    def test_colors_reach_css(self):
        css = styles.css_variables({"colors": {"cover_bg": "#AABBCC"}})
        self.assertIn("--c-cover_bg:#AABBCC", css)


class FreeTextTests(TestCase):
    """Teks bawaan template boleh diubah, tapi hanya kunci yang diizinkan."""

    def setUp(self):
        self.template = Template.objects.create(
            slug="amplop-merah",
            name="Amplop Merah",
            category=CardType.BIRTHDAY,
            config={
                "renderer": "birthday",
                "texts": [
                    {"key": "cover_title", "label": "Judul", "default": "Happy Birthday!"},
                    {"key": "hub_title", "label": "Hub", "default": "Ini untukmu"},
                ],
            },
        )
        self.url = reverse("cards:editor", args=[self.template.slug])

    def post(self, texts_json):
        return self.client.post(
            self.url,
            {
                "recipient_name": "Nadia",
                "sender_name": "Raka",
                "message": "halo",
                "youtube_url": "",
                "favorite_flower": "",
                "affirmations": "",
                "style_json": "{}",
                "texts_json": texts_json,
            },
        )

    def test_default_used_when_not_overridden(self):
        self.post("{}")
        card = GiftCard.objects.get()
        self.assertEqual(card.text("cover_title"), "Happy Birthday!")

    def test_override_is_saved_and_rendered(self):
        self.post(json.dumps({"cover_title": "Selamat Ulang Tahun Sayang"}))
        card = GiftCard.objects.get()
        self.assertEqual(card.text("cover_title"), "Selamat Ulang Tahun Sayang")

        card.status = GiftCard.Status.PAID
        card.save()
        response = self.client.get(reverse("cards:public", args=[card.id]))
        self.assertContains(response, "Selamat Ulang Tahun Sayang")
        self.assertNotContains(response, "Happy Birthday!")

    def test_unknown_key_is_dropped(self):
        self.post(json.dumps({"kunci_asing": "x", "cover_title": "ok"}))
        card = GiftCard.objects.get()
        self.assertEqual(card.texts, {"cover_title": "ok"})

    def test_html_in_text_is_escaped_not_executed(self):
        self.post(json.dumps({"cover_title": "<script>alert(1)</script>"}))
        card = GiftCard.objects.get()
        card.status = GiftCard.Status.PAID
        card.save()
        response = self.client.get(reverse("cards:public", args=[card.id]))
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_very_long_text_is_trimmed(self):
        self.post(json.dumps({"cover_title": "x" * 5000}))
        card = GiftCard.objects.get()
        self.assertLessEqual(len(card.texts["cover_title"]), 300)

    def test_broken_json_does_not_break_form(self):
        response = self.post("{rusak")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(GiftCard.objects.get().texts, {})

    def test_editor_lists_all_editable_texts(self):
        response = self.client.get(self.url)
        body = response.content.decode()
        start = body.index('id="editor-init" type="application/json">') + len(
            'id="editor-init" type="application/json">'
        )
        data = json.loads(body[start : body.index("</script>", start)])
        self.assertEqual(len(data["texts"]), 2)
        self.assertEqual(data["textValues"]["cover_title"], "Happy Birthday!")
