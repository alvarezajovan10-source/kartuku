import json

from django.test import TestCase
from django.urls import reverse

from cards import styles
from cards.models import CardType, GiftCard, Template


class SanitizeElementTests(TestCase):
    """Gaya elemen masuk ke CSS kartu, jadi tidak ada nilai mentah yang lolos."""

    def test_empty_when_nothing_set(self):
        # Penting: kunci yang tidak diisi DIBUANG, bukan diberi bawaan —
        # itulah yang membuat desain asli template tetap utuh.
        self.assertEqual(styles.sanitize_element({}), {})

    def test_garbage_input_returns_empty(self):
        for junk in [None, "bukan dict", 42, []]:
            with self.subTest(junk=junk):
                self.assertEqual(styles.sanitize_element(junk), {})

    def test_valid_values_kept(self):
        clean = styles.sanitize_element(
            {"font": "playfair", "size": 1.4, "color": "#112233",
             "align": "left", "bold": True, "italic": True,
             "spacing": 0.1, "line": 1.6}
        )
        self.assertEqual(clean["font"], "playfair")
        self.assertEqual(clean["size"], 1.4)
        self.assertEqual(clean["color"], "#112233")
        self.assertEqual(clean["align"], "left")
        self.assertTrue(clean["bold"])
        self.assertTrue(clean["italic"])

    def test_css_injection_via_color_rejected(self):
        clean = styles.sanitize_element({"color": "#fff; position:fixed; top:0"})
        self.assertNotIn("color", clean)

    def test_unknown_font_rejected(self):
        self.assertNotIn("font", styles.sanitize_element({"font": "../../etc/passwd"}))

    def test_size_clamped(self):
        self.assertEqual(styles.sanitize_element({"size": 99})["size"], styles.SIZE_MAX)
        self.assertEqual(styles.sanitize_element({"size": -5})["size"], styles.SIZE_MIN)
        self.assertNotIn("size", styles.sanitize_element({"size": "abc"}))

    def test_align_must_be_known(self):
        self.assertNotIn("align", styles.sanitize_element({"align": "justify;x:1"}))

    def test_bold_only_accepts_true(self):
        self.assertNotIn("bold", styles.sanitize_element({"bold": "yes"}))
        self.assertNotIn("bold", styles.sanitize_element({"bold": False}))

    def test_element_css_emits_only_what_is_set(self):
        css = styles.element_css({"size": 1.2})
        self.assertEqual(css, "--fs:1.2")

    def test_element_css_rejects_injected_values(self):
        css = styles.element_css({"color": "red;} body{display:none}", "size": 1.1})
        self.assertNotIn("display", css)
        self.assertEqual(css, "--fs:1.1")


class SanitizeStyleTests(TestCase):
    def test_element_keys_must_match_pattern(self):
        for key in ["Cover", "1bad", "a-b; x", "../x", "a" * 40]:
            with self.subTest(key=key):
                clean = styles.sanitize_style({"elements": {key: {"size": 1.2}}})
                self.assertEqual(clean["elements"], {})

    def test_good_key_kept(self):
        clean = styles.sanitize_style({"elements": {"cover_title": {"size": 1.2}}})
        self.assertEqual(clean["elements"], {"cover_title": {"size": 1.2}})

    def test_element_count_capped(self):
        many = {f"k{i}": {"size": 1.1} for i in range(200)}
        clean = styles.sanitize_style({"elements": many})
        self.assertLessEqual(len(clean["elements"]), styles.MAX_ELEMENTS)

    def test_colors_validated(self):
        clean = styles.sanitize_style(
            {"colors": {"scene_bg": "#AABBCC", "bad key": "#AABBCC", "x": "merah"}}
        )
        self.assertEqual(clean["colors"], {"scene_bg": "#AABBCC"})

    def test_colors_css(self):
        self.assertEqual(
            styles.colors_css({"scene_bg": "#AABBCC"}), "--c-scene_bg:#AABBCC"
        )


class FontCatalogTests(TestCase):
    def test_catalog_covers_every_font(self):
        listed = {f["key"] for group in styles.font_catalog() for f in group["fonts"]}
        self.assertEqual(listed, set(styles.FONTS))

    def test_card_loads_only_fonts_it_uses(self):
        url = styles.google_fonts_url(["playfair"])
        self.assertIn("Playfair+Display", url)
        self.assertNotIn("Great+Vibes", url)

    def test_no_fonts_means_no_request(self):
        self.assertEqual(styles.google_fonts_url([]), "")

    def test_editor_url_has_all_fonts(self):
        url = styles.google_fonts_url()
        self.assertEqual(url.count("family="), len(styles.FONTS))


class EditorFlowTests(TestCase):
    def setUp(self):
        self.template = Template.objects.create(
            slug="amplop-merah",
            name="Amplop Merah",
            category=CardType.BIRTHDAY,
            config={
                "renderer": "birthday",
                "texts": [
                    {"key": "cover_title", "label": "Judul", "default": "Happy Birthday!"}
                ],
                "surfaces": [
                    {"key": "scene_bg", "label": "Latar", "default": "#9E1B32"}
                ],
                "frames": [{"key": "p1", "label": "Polaroid"}],
            },
        )
        self.url = reverse("cards:editor", args=[self.template.slug])

    def post(self, **extra):
        payload = {
            "recipient_name": "Nadia",
            "sender_name": "Raka",
            "message": "halo",
            "youtube_url": "",
            "favorite_flower": "",
            "affirmations": "",
            "style_json": "{}",
            "texts_json": "{}",
        }
        payload.update(extra)
        return self.client.post(self.url, payload)

    def test_element_style_saved(self):
        self.post(
            style_json=json.dumps(
                {"elements": {"cover_title": {"font": "playfair", "size": 1.5}}}
            )
        )
        card = GiftCard.objects.get()
        self.assertEqual(card.style["elements"]["cover_title"]["font"], "playfair")

    def test_malicious_style_never_reaches_database(self):
        self.post(
            style_json=json.dumps(
                {"elements": {"cover_title": {"color": "#fff;} body{display:none}"}}}
            )
        )
        card = GiftCard.objects.get()
        self.assertEqual(card.style["elements"], {})

    def test_broken_json_does_not_break_form(self):
        response = self.post(style_json="{rusak")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(GiftCard.objects.get().style, {"elements": {}, "colors": {}})

    def test_style_reaches_the_card(self):
        self.post(
            style_json=json.dumps(
                {"elements": {"cover_title": {"color": "#112233", "bold": True}}}
            )
        )
        card = GiftCard.objects.get()
        card.status = GiftCard.Status.PAID
        card.save()
        response = self.client.get(reverse("cards:public", args=[card.id]))
        self.assertContains(response, "--c:#112233")
        self.assertContains(response, "--fw:700")

    def test_surface_color_reaches_the_card(self):
        self.post(style_json=json.dumps({"colors": {"scene_bg": "#123456"}}))
        card = GiftCard.objects.get()
        card.status = GiftCard.Status.PAID
        card.save()
        response = self.client.get(reverse("cards:public", args=[card.id]))
        self.assertContains(response, "--c-scene_bg:#123456")

    def test_card_page_requests_only_used_font(self):
        self.post(
            style_json=json.dumps({"elements": {"cover_title": {"font": "lobster"}}})
        )
        card = GiftCard.objects.get()
        card.status = GiftCard.Status.PAID
        card.save()
        response = self.client.get(reverse("cards:public", args=[card.id]))
        self.assertContains(response, "Lobster")
        self.assertNotContains(response, "Great+Vibes")

    def test_editor_ships_valid_init_json(self):
        response = self.client.get(self.url)
        body = response.content.decode()
        start = body.index('id="editor-init" type="application/json">') + len(
            'id="editor-init" type="application/json">'
        )
        data = json.loads(body[start : body.index("</script>", start)])
        keys = {e["key"] for e in data["elements"]}
        # Kolom data, teks template, bingkai foto, dan permukaan warna
        # semuanya jadi elemen yang bisa dipilih di editor.
        self.assertIn("recipient", keys)
        self.assertIn("cover_title", keys)
        self.assertIn("p1", keys)
        self.assertIn("scene_bg", keys)
        self.assertTrue(data["fontCatalog"])

    def test_every_element_type_is_known(self):
        response = self.client.get(self.url)
        body = response.content.decode()
        start = body.index('id="editor-init" type="application/json">') + len(
            'id="editor-init" type="application/json">'
        )
        data = json.loads(body[start : body.index("</script>", start)])
        for element in data["elements"]:
            self.assertIn(element["type"], {"field", "text", "photo", "surface"})


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
                ],
            },
        )
        self.url = reverse("cards:editor", args=[self.template.slug])

    def post(self, texts_json):
        return self.client.post(
            self.url,
            {
                "recipient_name": "Nadia", "sender_name": "Raka", "message": "halo",
                "youtube_url": "", "favorite_flower": "", "affirmations": "",
                "style_json": "{}", "texts_json": texts_json,
            },
        )

    def test_default_used_when_not_overridden(self):
        self.post("{}")
        self.assertEqual(GiftCard.objects.get().text("cover_title"), "Happy Birthday!")

    def test_override_saved_and_rendered(self):
        self.post(json.dumps({"cover_title": "Selamat Ulang Tahun Sayang"}))
        card = GiftCard.objects.get()
        card.status = GiftCard.Status.PAID
        card.save()
        response = self.client.get(reverse("cards:public", args=[card.id]))
        self.assertContains(response, "Selamat Ulang Tahun Sayang")
        self.assertNotContains(response, "Happy Birthday!")

    def test_unknown_key_dropped(self):
        self.post(json.dumps({"kunci_asing": "x", "cover_title": "ok"}))
        self.assertEqual(GiftCard.objects.get().texts, {"cover_title": "ok"})

    def test_html_escaped_not_executed(self):
        self.post(json.dumps({"cover_title": "<script>alert(1)</script>"}))
        card = GiftCard.objects.get()
        card.status = GiftCard.Status.PAID
        card.save()
        response = self.client.get(reverse("cards:public", args=[card.id]))
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_very_long_text_trimmed(self):
        self.post(json.dumps({"cover_title": "x" * 5000}))
        self.assertLessEqual(len(GiftCard.objects.get().texts["cover_title"]), 300)


class PhotoLimitTests(TestCase):
    def test_limit_is_thirty(self):
        from django.conf import settings

        self.assertEqual(settings.MAX_PHOTOS_PER_CARD, 30)
