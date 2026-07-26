import json

from django import forms
from django.conf import settings

from .models import GiftCard
from .styles import sanitize_style
from .utils import extract_youtube_id

MAX_TEXT_KEYS = 60
MAX_TEXT_LENGTH = 300


class GiftCardForm(forms.ModelForm):
    # Diisi oleh editor lewat JavaScript; user tidak pernah mengetiknya langsung.
    style_json = forms.CharField(required=False, widget=forms.HiddenInput())
    texts_json = forms.CharField(required=False, widget=forms.HiddenInput())

    youtube_url = forms.CharField(
        label="Link YouTube (opsional)",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "https://youtu.be/..."}),
    )

    class Meta:
        model = GiftCard
        fields = [
            "sender_name",
            "recipient_name",
            "message",
            "favorite_flower",
            "affirmations",
        ]
        labels = {
            "sender_name": "Dari",
            "recipient_name": "Untuk",
            "message": "Pesanmu",
            "favorite_flower": "Bunga kesukaannya (opsional)",
            "affirmations": "Kalimat manis (opsional)",
        }
        help_texts = {
            "favorite_flower": "Contoh: Sunflower, Tulip, Mawar.",
            "affirmations": "Satu kalimat per baris, maksimal 4.",
        }
        widgets = {
            "message": forms.Textarea(attrs={"rows": 6}),
            "affirmations": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Kamu berharga, dengan cara yang jarang orang sadari.\nKamu kuat, bahkan di hari-hari yang berat.",
                }
            ),
        }

    def __init__(self, *args, template_config=None, **kwargs):
        # Dipakai clean_texts_json untuk tahu kunci teks apa yang sah.
        self.template_config = template_config or {}
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.youtube_video_id:
            self.fields["youtube_url"].initial = (
                f"https://youtu.be/{self.instance.youtube_video_id}"
            )
        self.fields["style_json"].initial = json.dumps(
            sanitize_style(getattr(self.instance, "style", None))
        )

    def clean_style_json(self):
        """Terima JSON dari editor, tapi selalu saring lewat daftar putih.

        Isi yang rusak atau iseng tidak pernah membuat form gagal — cukup jatuh
        ke gaya bawaan, supaya user tidak terjebak di halaman error.
        """
        raw = self.cleaned_data.get("style_json") or ""
        try:
            parsed = json.loads(raw) if raw else {}
        except (json.JSONDecodeError, TypeError):
            parsed = {}
        return sanitize_style(parsed)

    def clean_texts_json(self):
        """Teks bebas per template. Hanya kunci yang template izinkan yang disimpan.

        Panjang dibatasi supaya tata letak kartu tidak bisa dirusak dengan teks
        raksasa. Isinya di-escape Django saat render, jadi aman dari HTML.
        """
        raw = self.cleaned_data.get("texts_json") or ""
        try:
            parsed = json.loads(raw) if raw else {}
        except (json.JSONDecodeError, TypeError):
            return {}
        if not isinstance(parsed, dict):
            return {}

        allowed = {
            spec["key"]
            for spec in (self.template_config or {}).get("texts", [])
            if isinstance(spec, dict) and spec.get("key")
        }
        clean = {}
        for key, value in list(parsed.items())[:MAX_TEXT_KEYS]:
            if key in allowed and isinstance(value, str):
                clean[key] = value.strip()[:MAX_TEXT_LENGTH]
        return clean

    def clean_affirmations(self):
        """Batasi jumlah baris supaya tata letak kartu tidak berantakan."""
        value = self.cleaned_data["affirmations"]
        lines = [line.strip() for line in value.splitlines() if line.strip()]
        if len(lines) > GiftCard.MAX_AFFIRMATIONS:
            raise forms.ValidationError(
                f"Maksimal {GiftCard.MAX_AFFIRMATIONS} kalimat."
            )
        return "\n".join(lines)

    def clean_youtube_url(self):
        # extract_youtube_id raise ValidationError → otomatis jadi field error.
        return extract_youtube_id(self.cleaned_data["youtube_url"])

    def save(self, commit=True):
        card = super().save(commit=False)
        card.youtube_video_id = self.cleaned_data["youtube_url"]
        card.style = self.cleaned_data["style_json"]
        card.texts = self.cleaned_data["texts_json"]
        if commit:
            card.save()
        return card


class MultipleFileInput(forms.FileInput):
    """Django melarang `multiple` di widget bawaan; opt-in eksplisit di sini."""

    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """FileField yang menerima banyak file.

    Widget dengan `allow_multiple_selected` mengirim LIST ke clean(), sedangkan
    FileField bawaan hanya mengerti satu file dan menolaknya dengan pesan
    "Tidak ada berkas yang dikirimkan". Tanpa kelas ini, semua unggahan gagal.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        clean_one = super().clean
        if isinstance(data, (list, tuple)):
            return [clean_one(item, initial) for item in data if item]
        return clean_one(data, initial)


class PhotoUploadForm(forms.Form):
    photos = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={"multiple": True, "accept": "image/*"}),
        label=f"Foto (maks {settings.MAX_PHOTOS_PER_CARD})",
    )
