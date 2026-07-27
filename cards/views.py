import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.staticfiles import finders
from django.core.exceptions import ValidationError
from uuid import UUID

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.templatetags.static import static
from django.utils.text import slugify
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from . import styles
from .forms import GiftCardForm
from .models import CardType, GiftCard, GiftPhoto, Template
from .utils import validate_and_compress_photo

logger = logging.getLogger(__name__)

# Kunci sesi: daftar kartu yang dibuat browser ini. Dipakai untuk mengizinkan
# pemilik melihat preview/halaman bayar kartunya sendiri sebelum lunas.
OWNED_CARDS_KEY = "owned_cards"

# UUID boneka untuk membangun pola URL yang nanti diisi JS.
PLACEHOLDER_UUID = "00000000-0000-0000-0000-000000000000"

# Elemen yang isinya berasal dari kolom database, bukan teks bawaan template.
FIELD_ELEMENTS = [
    ("recipient", "Nama penerima", "line"),
    ("message", "Pesan", "multiline"),
    ("sender", "Nama pengirim", "line"),
    ("favorite_flower", "Nama bunga", "line"),
    ("affirmations", "Kalimat manis", "multiline"),
]


def _mark_owned(request, card):
    owned = request.session.setdefault(OWNED_CARDS_KEY, [])
    if str(card.id) not in owned:
        owned.append(str(card.id))
        request.session.modified = True


def _owns(request, card):
    return str(card.id) in request.session.get(OWNED_CARDS_KEY, [])


# Teks & warna per kategori untuk kartu pilihan di landing.
CATEGORY_CARDS = [
    {
        "category": CardType.BIRTHDAY,
        "title": "Birthday",
        "blurb": "Rayakan hari spesial dengan ucapan penuh cinta.",
        "icon": "cake",
        "tint": "birthday",
    },
    {
        "category": CardType.ANNIVERSARY,
        "title": "Anniversary",
        "blurb": "Kenangan indah kita, dirangkum dalam satu kartu.",
        "icon": "heart",
        "tint": "anniversary",
    },
    {
        "category": CardType.LOVE_STORY,
        "title": "Love Story",
        "blurb": "Ceritakan perjalanan cinta kita dalam kartu yang indah.",
        "icon": "heart",
        "tint": "love",
    },
    {
        "category": CardType.PROPOSAL,
        "title": "Proposal",
        "blurb": "Momen paling penting, ucapkan dengan cara istimewa.",
        "icon": "ring",
        "tint": "proposal",
    },
]


def _static_if_exists(path):
    """Kembalikan path static kalau filenya benar-benar ada, kalau tidak None.

    Dipakai supaya halaman jatuh ke ilustrasi SVG bawaan selama foto asli belum
    ditaruh di `static/img/`.
    """
    return path if finders.find(path) else None


def landing(request):
    """Landing: satu kartu per kategori, menunjuk ke template aktif pertamanya."""
    active = Template.objects.filter(is_active=True)
    first_by_category = {}
    for template in active:
        first_by_category.setdefault(template.category, template)

    categories = []
    for entry in CATEGORY_CARDS:
        template = first_by_category.get(entry["category"])
        if template is None:
            continue  # kategori tanpa template aktif tidak ditampilkan
        photo = _static_if_exists(f"img/cat-{entry['tint']}.jpg")
        categories.append({**entry, "template": template, "photo": photo})

    return render(
        request,
        "cards/landing.html",
        {
            "categories": categories,
            "price": settings.CARD_PRICE,
            "hero_photo": _static_if_exists("img/hero.jpg"),
        },
    )


def template_gallery(request, category):
    """Semua template aktif untuk satu kategori, siap di-preview atau dipakai."""
    label = dict(CardType.choices).get(category)
    if label is None:
        raise Http404("Kategori tidak dikenal.")

    templates = Template.objects.filter(category=category, is_active=True)
    entries = [
        {
            "template": template,
            "thumb": _static_if_exists(f"img/thumb/{template.slug}.jpg"),
            "accent": (template.config or {}).get("accent", "#c9736e"),
        }
        for template in templates
    ]

    blurb = next(
        (c["blurb"] for c in CATEGORY_CARDS if c["category"] == category), ""
    )
    return render(
        request,
        "cards/gallery.html",
        {
            "category": category,
            "category_label": label,
            "blurb": blurb,
            "entries": entries,
            "price": settings.CARD_PRICE,
        },
    )


# Isi contoh untuk preview — tidak pernah disimpan ke database.
SAMPLE_PHOTO_CAPTIONS = ["liburan", "konser", "tawa", "senja"]


def _sample_card(template):
    """GiftCard yang tidak disimpan, berisi contoh, untuk merender preview."""
    return GiftCard(
        template=template,
        category=template.category,
        recipient_name="Nadia",
        sender_name="Raka",
        message=(
            "Selamat ulang tahun! Terima kasih sudah jadi orang yang bikin "
            "hari-hari biasa terasa istimewa.\n\n"
            "Semoga tahun ini kamu dikelilingi hal-hal yang kamu cintai."
        ),
        youtube_video_id="dQw4w9WgXcQ",
        favorite_flower="Sunflower",
        affirmations=(
            "Kamu berharga, dengan cara yang jarang orang sadari.\n"
            "Kamu kuat, bahkan di hari-hari yang berat.\n"
            "Kamu bikin ruang jadi lebih hangat begitu masuk.\n"
            "Kamu pantas dapat semua hal baik tahun ini."
        ),
        status=GiftCard.Status.PAID,
    )


def _sample_photos():
    """Foto contoh sebagai dict — template mengaksesnya seperti objek biasa."""
    photos = []
    for index, caption in enumerate(SAMPLE_PHOTO_CAPTIONS, start=1):
        path = f"img/sample/{index}.jpg"
        if not finders.find(path):
            continue
        photos.append({"image": {"url": static(path)}, "caption": caption})
    return photos


def preview(request, template_slug):
    """Tampilkan template dengan isi contoh. Tidak membuat kartu, tidak menyimpan."""
    template = get_object_or_404(Template, slug=template_slug, is_active=True)
    card = _sample_card(template)
    renderer = (template.config or {}).get("renderer", "")

    candidates = []
    if renderer:
        candidates.append(f"cards/render/{renderer}.html")
    candidates.append("cards/public.html")

    return render(
        request,
        candidates,
        {
            "card": card,
            "photos": _sample_photos(),
            "affirmations": card.affirmation_list(),
            "preview": True,
            "template": template,
            "fonts_url": styles.google_fonts_url(card.fonts_used()),
        },
    )


def _render_card(request, card, extra=None):
    """Render kartu memakai renderer templatenya, dengan fallback."""
    candidates = []
    if card.renderer():
        candidates.append(f"cards/render/{card.renderer()}.html")
    candidates.append("cards/public.html")

    context = {
        "card": card,
        "photos": list(card.photos.all()),
        "affirmations": card.affirmation_list(),
        "fonts_url": styles.google_fonts_url(card.fonts_used()),
        "frame_photos": card.photo_by_slot(),
        "gallery_photos": card.gallery_photos(),
    }
    context.update(extra or {})
    return render(request, candidates, context)


@xframe_options_sameorigin
def editor_frame(request, template_slug):
    """Isi iframe editor: kartu asli yang elemennya bisa diklik.

    Sengaja memakai renderer yang sama persis dengan kartu final, supaya yang
    dilihat user saat mengedit tidak mungkin berbeda dari hasil akhirnya.

    HANYA halaman ini yang boleh masuk iframe (sameorigin). Sisa situs tetap
    X-Frame-Options: DENY, supaya kartu orang tidak bisa disematkan di situs lain.
    """
    template = get_object_or_404(Template, slug=template_slug, is_active=True)
    card_id = request.GET.get("card")
    card = None
    if card_id:
        card = GiftCard.objects.filter(pk=card_id).first()
        if card and not _owns(request, card):
            card = None
    if card is None:
        card = GiftCard(template=template, category=template.category)

    return _render_card(request, card, {"editing": True})


def editor(request, template_slug):
    """Editor: panel kiri kontekstual + iframe berisi kartu asli.

    Foto TIDAK lewat sini — sudah diunggah lebih dulu lewat api_photos, supaya
    pilihan foto tidak hilang saat halaman dimuat ulang. Di sini hanya teks & gaya.
    """
    template = get_object_or_404(Template, slug=template_slug, is_active=True)

    card_id = request.POST.get("card") or request.GET.get("card")
    card = None
    if card_id:
        card = GiftCard.objects.filter(
            pk=card_id, status=GiftCard.Status.DRAFT
        ).first()
        if card and not _owns(request, card):
            card = None

    if request.method == "POST":
        form = GiftCardForm(
            request.POST, instance=card, template_config=template.config
        )
        if form.is_valid():
            card = form.save(commit=False)
            card.template = template
            card.category = template.category
            card.amount = settings.CARD_PRICE
            card.save()
            _mark_owned(request, card)
            return redirect("cards:pay", card_id=card.id)
    else:
        form = GiftCardForm(instance=card, template_config=template.config)

    # Kartu boneka untuk membaca spesifikasi template saat draft belum dibuat.
    probe = card or GiftCard(template=template, category=template.category)
    current_colors = styles.sanitize_style(card.style if card else None)["colors"]

    by_slot = card.photo_by_slot() if card else {}

    # Satu daftar elemen untuk editor. Urutannya = urutan panel kalau perlu.
    element_specs = []
    for key, label, kind in FIELD_ELEMENTS:
        element_specs.append({"key": key, "label": label, "type": "field", "input": kind})
    for spec in probe.text_specs():
        element_specs.append(
            {"key": spec["key"], "label": spec.get("label", spec["key"]), "type": "text"}
        )
    for spec in probe.frames():
        element_specs.append(
            {
                "key": spec["key"],
                "label": spec.get("label", spec["key"]),
                "type": "photo",
                "photo": _photo_payload(by_slot[spec["key"]])
                if spec["key"] in by_slot
                else None,
            }
        )
    for spec in probe.surface_specs():
        element_specs.append(
            {
                "key": spec["key"],
                "label": spec.get("label", spec["key"]),
                "type": "surface",
                "value": current_colors.get(spec["key"], spec.get("default", "#FFFFFF")),
            }
        )

    # Tiap foto galeri jadi elemen sendiri supaya bisa diklik & di-crop.
    for photo in card.gallery_photos() if card else []:
        element_specs.append(
            {
                "key": photo.element_key,
                "label": "Foto kenangan",
                "type": "photo",
                "photo": _photo_payload(photo),
            }
        )

    field_values = {
        "recipient": form["recipient_name"].value() or "",
        "sender": form["sender_name"].value() or "",
        "message": form["message"].value() or "",
        "favorite_flower": form["favorite_flower"].value() or "",
        "affirmations": form["affirmations"].value() or "",
        "youtube_url": form["youtube_url"].value() or "",
    }
    text_values = {spec["key"]: probe.text(spec["key"]) for spec in probe.text_specs()}

    frames = []
    for frame in (template.config or {}).get("frames", []):
        if not isinstance(frame, dict) or not frame.get("key"):
            continue
        photo = by_slot.get(frame["key"])
        frames.append(
            {
                "key": frame["key"],
                "label": frame.get("label", frame["key"]),
                "photo": _photo_payload(photo) if photo else None,
            }
        )

    gallery = [_photo_payload(p) for p in (card.gallery_photos() if card else [])]

    return render(
        request,
        "cards/editor.html",
        {
            "template": template,
            "form": form,
            "price": settings.CARD_PRICE,
            # Editor memuat SELURUH katalog font supaya pemilihnya bisa
            # menampilkan contoh tulisan tiap font.
            "fonts_url": styles.google_fonts_url(),
            "max_photos": settings.MAX_PHOTOS_PER_CARD,
            "editor_init": {
                "cardId": str(card.id) if card else "",
                "style": styles.sanitize_style(card.style if card else None),
                "fields": field_values,
                "texts": text_values,
                "elements": element_specs,
                "gallery": gallery,
                "fontCatalog": styles.font_catalog(),
                "fonts": {key: value[2] for key, value in styles.FONTS.items()},
                    "swatches": styles.SWATCHES,
                "maxPhotos": settings.MAX_PHOTOS_PER_CARD,
                "urls": {
                    "frame": reverse("cards:editor_frame", args=[template.slug]),
                    "draft": reverse("cards:api_draft", args=[template.slug]),
                    "content": reverse(
                        "cards:api_content", args=[PLACEHOLDER_UUID]
                    ).replace(PLACEHOLDER_UUID, "CARD"),
                    "upload": reverse(
                        "cards:api_photo_upload", args=[PLACEHOLDER_UUID]
                    ).replace(PLACEHOLDER_UUID, "CARD"),
                    "remove": reverse(
                        "cards:api_photo_delete", args=[PLACEHOLDER_UUID, 0]
                    ).replace(PLACEHOLDER_UUID, "CARD").replace("/0/", "/PHOTO/"),
                    "caption": reverse(
                        "cards:api_photo_caption", args=[PLACEHOLDER_UUID, 0]
                    ).replace(PLACEHOLDER_UUID, "CARD").replace("/0/", "/PHOTO/"),
                },
            },
        },
    )


def pay(request, card_id):
    """Halaman QR + polling. Hanya pemilik sesi yang boleh membukanya."""
    card = get_object_or_404(GiftCard, pk=card_id)
    if card.is_paid:
        return redirect("cards:success", card_id=card.id)
    if not _owns(request, card):
        return render(request, "cards/not_yours.html", status=403)
    return render(request, "cards/pay.html", {"card": card, "price": card.amount})


@require_POST
@user_passes_test(lambda user: user.is_staff)
def mark_paid(request, card_id):
    """Aktifkan kartu tanpa bayar. HANYA untuk staff (pemilik situs).

    Izinnya bersandar pada `is_staff` di database, bukan sesi atau parameter URL,
    supaya pengunjung biasa tidak punya cara apa pun memicunya.
    """
    card = get_object_or_404(GiftCard, pk=card_id)
    if not card.is_paid:
        card.status = GiftCard.Status.PAID
        card.paid_at = timezone.now()
        card.comped = True
        card.save(update_fields=["status", "paid_at", "comped", "updated_at"])
        logger.info(
            "Kartu %s diaktifkan gratis oleh staff %s", card.id, request.user
        )
    _mark_owned(request, card)
    return redirect("cards:success", card_id=card.id)


def success(request, card_id):
    card = get_object_or_404(GiftCard, pk=card_id)
    if not card.is_paid:
        return redirect("cards:pay", card_id=card.id)
    return render(
        request,
        "cards/success.html",
        {"card": card, "slug_error": request.session.pop("slug_error", "")},
    )


def _card_by_ref(ref):
    """Cari kartu lewat UUID atau slug pilihan user — dua-duanya tetap jalan."""
    try:
        return get_object_or_404(GiftCard, pk=UUID(str(ref)))
    except (ValueError, AttributeError):
        return get_object_or_404(GiftCard, slug=ref)


def public_card(request, ref):
    """Halaman kartu publik. Aturan emas: hanya render penuh kalau status == paid."""
    card = _card_by_ref(ref)
    # Staff (pemilik situs) boleh mengintip kartu yang belum dibayar untuk
    # mengecek hasil template. Pengunjung biasa tetap terkunci.
    staff_peek = request.user.is_staff and not card.is_paid
    if not card.is_paid and not staff_peek:
        return render(
            request,
            "cards/locked.html",
            {"card": card, "is_owner": _owns(request, card)},
            status=402,
        )
    # Satu jalur render dengan editor & preview, supaya tidak ada konteks yang
    # terlupa di salah satunya (mis. foto galeri hilang di kartu asli).
    return _render_card(request, card, {"staff_peek": staff_peek})


def _photo_payload(photo):
    """Bentuk foto yang dikirim ke editor. Sama dengan yang dipakai api_photos."""
    return {
        "id": photo.id,
        "url": photo.image.url,
        "caption": photo.caption,
        "slot": photo.slot,
        "order": photo.order,
    }


RESERVED_SLUGS = {"admin", "api", "create", "pay", "sukses", "template", "preview", "qr", "g", "static", "media"}


@require_POST
def set_slug(request, card_id):
    """Ganti link kartu jadi nama pilihan user. Hanya setelah bayar, pemilik saja."""
    card = get_object_or_404(GiftCard, pk=card_id)
    if not (_owns(request, card) or request.user.is_staff):
        return render(request, "cards/not_yours.html", status=403)
    if not card.is_paid:
        return redirect("cards:pay", card_id=card.id)

    slug = slugify(request.POST.get("slug", ""))[:60]
    error = ""
    if not slug or len(slug) < 3:
        error = "Minimal 3 karakter (huruf, angka, tanda minus)."
    elif slug in RESERVED_SLUGS:
        error = "Nama itu tidak bisa dipakai."
    elif GiftCard.objects.filter(slug=slug).exclude(pk=card.pk).exists():
        error = "Sudah dipakai kartu lain — coba nama lain."
    else:
        card.slug = slug
        card.save(update_fields=["slug", "updated_at"])

    if error:
        request.session["slug_error"] = error
    return redirect("cards:success", card_id=card.id)


# Gaya QR yang ditawarkan: (bentuk modul, warna). Nilai dari user hanya kunci
# dari peta ini — tidak ada warna/bentuk mentah dari luar.
QR_COLORS = {
    "hitam": ("#2B2320", "#FFFFFF"),
    "merah": ("#9E1B32", "#FFF6F0"),
    "pink": ("#E75480", "#FFF4F7"),
    "emas": ("#A9863A", "#FFFBEF"),
}


def qr_png(request, card_id):
    """Gambar QR menuju link kartu. Gaya: kotak / hati, warna dari QR_COLORS."""
    import io as _io

    import qrcode
    from PIL import Image as PILImage, ImageDraw

    card = get_object_or_404(GiftCard, pk=card_id)
    if not card.is_paid:
        raise Http404

    style = request.GET.get("style", "kotak")
    fg, bg_color = QR_COLORS.get(request.GET.get("warna", "hitam"), QR_COLORS["hitam"])

    link = request.build_absolute_uri(card.public_url())
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=2, box_size=16)
    qr.add_data(link)
    qr.make(fit=True)
    matrix = qr.get_matrix()

    n = len(matrix)
    box = 16
    img = PILImage.new("RGB", (n * box, n * box), bg_color)
    draw = ImageDraw.Draw(img)

    def heart(cx, cy, r):
        # Dua lingkaran + segitiga = hati kecil per titik QR.
        draw.ellipse([cx - r, cy - r * 0.9, cx, cy + r * 0.1], fill=fg)
        draw.ellipse([cx, cy - r * 0.9, cx + r, cy + r * 0.1], fill=fg)
        draw.polygon(
            [(cx - r * 0.96, cy - r * 0.25), (cx + r * 0.96, cy - r * 0.25), (cx, cy + r)],
            fill=fg,
        )

    for y, row in enumerate(matrix):
        for x, filled in enumerate(row):
            if not filled:
                continue
            x0, y0 = x * box, y * box
            if style == "hati":
                heart(x0 + box / 2, y0 + box / 2, box / 2 - 1)
            else:
                draw.rounded_rectangle([x0 + 1, y0 + 1, x0 + box - 1, y0 + box - 1], radius=3, fill=fg)

    buffer = _io.BytesIO()
    img.save(buffer, "PNG")
    response = HttpResponse(buffer.getvalue(), content_type="image/png")
    if request.GET.get("download"):
        response["Content-Disposition"] = 'attachment; filename="qr-kartuku.png"'
    return response
