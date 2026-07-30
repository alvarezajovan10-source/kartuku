import logging
import secrets
from functools import lru_cache
from uuid import UUID

from django.conf import settings
from django.contrib.staticfiles import finders
from django.db import IntegrityError, transaction
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
from payments.models import LynkOrder

from .models import AccessCode, CardType, GiftCard, Template

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
    ("youtube_url", "Lagu — link YouTube", "line"),
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
    return render(
        request,
        "cards/landing.html",
        {
            "categories": _category_cards(),
            "price": settings.CARD_PRICE,
            "hero_photo": _static_if_exists("img/hero.jpg"),
        },
    )


def _category_cards():
    """Kartu kategori untuk landing dan halaman Template — satu sumber."""
    active = Template.objects.filter(is_active=True)
    first_by_category = {}
    for template in active:
        first_by_category.setdefault(template.category, template)

    categories = []
    for entry in CATEGORY_CARDS:
        template = first_by_category.get(entry["category"])
        photo = _static_if_exists(f"img/cat-{entry['tint']}.jpg")
        # Kategori tanpa template aktif tetap ditampilkan, tapi sebagai
        # "Coming soon" dan tidak bisa diklik. Menyembunyikannya sama sekali
        # membuat situs terlihat cuma punya satu kategori; menampilkannya
        # sebagai tautan hidup membawa pembeli ke galeri kosong.
        categories.append(
            {
                **entry,
                "template": template,
                "photo": photo,
                "coming_soon": template is None,
            }
        )
    return categories


# Halaman statis: tiap bagian landing sekarang punya alamatnya sendiri, supaya
# bisa dibagikan langsung dan muncul terpisah di hasil pencarian.
def page_templates(request):
    return render(
        request,
        "cards/pages/templates.html",
        {"categories": _category_cards(), "price": settings.CARD_PRICE},
    )


def page_how(request):
    return render(request, "cards/pages/how.html", {"price": settings.CARD_PRICE})


def page_pricing(request):
    return render(
        request,
        "cards/pages/pricing.html",
        {
            "price": settings.CARD_PRICE,
            "max_photos": settings.MAX_PHOTOS_PER_CARD,
        },
    )


def page_testimonials(request):
    return render(request, "cards/pages/testimonials.html", {})


def page_faq(request):
    return render(
        request,
        "cards/pages/faq.html",
        {
            "price": settings.CARD_PRICE,
            "max_photo_mb": settings.MAX_PHOTO_BYTES // (1024 * 1024),
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
        # Sama seperti editor(): pemilik situs boleh membuka kartu mana pun.
        if card and not (settings.DEBUG or request.user.is_staff or _owns(request, card)):
            card = None
    if card is None:
        card = GiftCard(template=template, category=template.category)

    return _render_card(
        request,
        card,
        {
            "editing": True,
            # Editor memuat seluruh katalog: user sedang memilih-milih font,
            # jadi semua file font harus tersedia di preview. Kartu asli tetap
            # hanya memuat font yang dipakai.
            "fonts_url": styles.google_fonts_url(),
            "start_scene": request.GET.get("scene", ""),
        },
    )


def editor(request, template_slug):
    """Editor: panel kiri kontekstual + iframe berisi kartu asli.

    Foto TIDAK lewat sini — sudah diunggah lebih dulu lewat api_photos, supaya
    pilihan foto tidak hilang saat halaman dimuat ulang. Di sini hanya teks & gaya.
    """
    template = get_object_or_404(Template, slug=template_slug, is_active=True)

    card_id = request.POST.get("card") or request.GET.get("card")
    card = None
    if card_id:
        # Pemilik situs (staff, atau siapa saja saat DEBUG) boleh membuka kartu
        # mana pun dari dashboard "Kartu Saya" — termasuk yang sudah lunas dan
        # yang dibuat di sesi browser lain. Pembeli biasa tetap dibatasi:
        # hanya draft miliknya sendiri, supaya kartu terkirim tidak bisa diubah
        # orang lain.
        owner_mode = settings.DEBUG or request.user.is_staff
        queryset = GiftCard.objects.all()
        if not owner_mode:
            queryset = queryset.filter(status=GiftCard.Status.DRAFT)
        card = queryset.filter(pk=card_id).first()
        if card and not (owner_mode or _owns(request, card)):
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
    """Halaman aktivasi kartu yang belum lunas.

    Kartu BELUM lunas boleh dibuka siapa pun yang memegang UUID-nya, tidak harus
    pemilik sesi. Sesi bisa hilang — cookie kedaluwarsa, pembeli ganti perangkat,
    riwayat browser dibersihkan — dan tanpa jalur ini pembeli yang sudah membayar
    di Lynk tidak punya cara apa pun kembali ke kartunya. UUID kartu yang belum
    lunas belum pernah dibagikan (link publik baru diberikan setelah aktif), dan
    mengaktifkannya tetap menuntut REF ID sah yang harus benar-benar dibayar.

    Kartu SUDAH lunas sengaja dialihkan di baris pertama, sebelum pemeriksaan apa
    pun. Link publik memakai UUID yang sama (lihat _card_by_ref), jadi UUID kartu
    lunas sudah ada di tangan penerima kartu — membuka halaman ini untuk mereka
    berarti penerima bisa mengambil alih kartu pengirimnya.

    Menyunting tetap terkunci `_owns`: `is_owner` dipakai template untuk
    menyembunyikan tautan editor dari pengunjung yang sedang memulihkan kartunya.
    """
    card = get_object_or_404(GiftCard, pk=card_id)
    if card.is_paid:
        return redirect("cards:success", card_id=card.id)
    return render(
        request,
        "cards/pay.html",
        {
            "card": card,
            "price": card.amount,
            "is_owner": _owns(request, card),
            "dev_bypass": settings.DEBUG,
            # Tanpa kunci Midtrans, blok QRIS pasti gagal — jangan ditampilkan
            # supaya pembeli tidak menunggu QR yang tidak akan pernah muncul.
            "payment_ready": bool(settings.MIDTRANS_SERVER_KEY),
            "code_error": request.session.pop("code_error", ""),
        },
    )


# Batas percobaan kode salah per sesi. Ruang kodenya ~8×10^11, jadi ini bukan
# pertahanan utama — hanya penahan supaya log tidak dibanjiri percobaan iseng.
CODE_MAX_ATTEMPTS = 12
CODE_ATTEMPT_WINDOW = 60 * 60  # detik


def _recent_attempts(request):
    now = timezone.now().timestamp()
    return [
        t for t in request.session.get("code_attempts", []) if now - t < CODE_ATTEMPT_WINDOW
    ]


def _code_attempts_exceeded(request):
    """Hanya MEMBACA. Yang dihitung cuma percobaan gagal — pembeli yang kodenya
    benar tidak boleh ikut terhukum oleh percobaannya sendiri."""
    recent = _recent_attempts(request)
    request.session["code_attempts"] = recent
    return len(recent) >= CODE_MAX_ATTEMPTS


def _record_failed_attempt(request):
    recent = _recent_attempts(request)
    recent.append(timezone.now().timestamp())
    request.session["code_attempts"] = recent
    request.session.modified = True


@require_POST
def redeem_code(request, card_id):
    """Aktifkan kartu dengan bukti pembayaran dari luar situs.

    Menerima dua bentuk, satu kolom isian:

      REF ID Lynk   pembeli menyalinnya dari email struknya. Sah hanya kalau
                    webhook Lynk sudah melaporkan pembayarannya lebih dulu,
                    jadi nomor karangan tidak akan pernah ketemu.
      Kode KRT-...  dibuat manual lewat `buat_kode`. Jalan keluar kalau webhook
                    gagal, pembelian lewat kanal lain, atau kartu gratis.

    Klaimnya atomik (lihat AccessCode.claim / LynkOrder.claim), jadi satu bukti
    tidak bisa mengaktifkan dua kartu walau tombolnya diklik berkali-kali.
    """
    card = get_object_or_404(GiftCard, pk=card_id)
    # Kartu lunas dialihkan lebih dulu — lihat alasannya di `pay`.
    if card.is_paid:
        return redirect("cards:success", card_id=card.id)
    # Sengaja TANPA cek `_owns`: pembeli yang sesinya hilang harus tetap bisa
    # mengaktifkan kartunya. Yang menjaga di sini bukan sesi melainkan buktinya
    # sendiri — REF ID hanya sah kalau webhook Lynk sudah melaporkan
    # pembayarannya, dan sekali pakai. `_aktifkan` mencatat kartunya ke sesi
    # yang berhasil, jadi pembeli langsung bisa menyunting lagi sesudahnya.

    if _code_attempts_exceeded(request):
        request.session["code_error"] = (
            "Terlalu banyak percobaan gagal. Coba lagi nanti atau hubungi penjual."
        )
        return redirect("cards:pay", card_id=card.id)

    raw = request.POST.get("code", "")

    def gagal(pesan):
        _record_failed_attempt(request)
        request.session["code_error"] = pesan
        return redirect("cards:pay", card_id=card.id)

    # 1. Kode manual berpola KRT-XXXX-XXXX.
    kode = AccessCode.normalize(raw)
    if kode:
        if not AccessCode.claim(kode, card):
            return gagal(
                "Kode ini sudah pernah dipakai untuk kartu lain."
                if AccessCode.objects.filter(code=kode).exists()
                else "Kode tidak ditemukan. Periksa lagi email dari penjual."
            )
        return _aktifkan(request, card, kode, f"kode {kode}")

    # 2. REF ID dari struk Lynk.
    ref = LynkOrder.normalize(raw)
    if not ref:
        return gagal(
            "Bentuknya tidak dikenali. Tempel REF ID dari email pembelianmu, "
            "atau kode aktivasi seperti KRT-A7K9-M3QP."
        )

    if not LynkOrder.claim(ref):
        pesanan = LynkOrder.objects.filter(ref_id=ref).first()
        if pesanan is None:
            return gagal(
                "Pembayaran dengan REF ID itu belum kami terima. Kalau kamu "
                "baru saja membayar, tunggu sebentar lalu coba lagi."
            )
        return gagal("REF ID ini sudah dipakai untuk kartu lain.")

    return _aktifkan(request, card, ref, f"REF ID Lynk {ref}")


def _aktifkan(request, card, jejak, keterangan):
    """Tandai kartu lunas setelah buktinya berhasil diklaim.

    `comped` sengaja dibiarkan False: ini penjualan asli, cuma pembayarannya
    terjadi di luar situs. Hanya kolom yang berubah yang ditulis, supaya tidak
    menimpa perubahan lain pada baris yang sama.
    """
    card.status = GiftCard.Status.PAID
    card.paid_at = timezone.now()
    card.gateway_order_id = jejak[:64]
    card.save(update_fields=["status", "paid_at", "gateway_order_id", "updated_at"])
    logger.info("Kartu %s diaktifkan dengan %s", card.id, keterangan)
    _mark_owned(request, card)
    return redirect("cards:success", card_id=card.id)


@require_POST
def mark_paid(request, card_id):
    """Aktifkan kartu tanpa bayar. HANYA untuk staff (pemilik situs).

    Izinnya bersandar pada `is_staff` di database, bukan sesi atau parameter URL,
    supaya pengunjung biasa tidak punya cara apa pun memicunya.

    Pengecualian dev: saat DEBUG aktif, siapa pun boleh — pemilik situs sering
    menguji kartu di localhost tanpa mau repot login. JANGAN pernah nyalakan
    DEBUG di produksi; gerbang bayar ikut terbuka.
    """
    if not (request.user.is_staff or settings.DEBUG):
        return render(request, "cards/not_yours.html", status=403)
    card = get_object_or_404(GiftCard, pk=card_id)
    if not card.is_paid:
        card.status = GiftCard.Status.PAID
        card.paid_at = timezone.now()
        card.comped = True
        card.save(update_fields=["status", "paid_at", "comped", "updated_at"])
        logger.info(
            "Kartu %s diaktifkan gratis oleh %s", card.id, request.user if request.user.is_authenticated else "dev-bypass (DEBUG)"
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
        {
            "card": card,
            "slug_error": request.session.pop("slug_error", ""),
            "slug_note": request.session.pop("slug_note", ""),
        },
    )


def my_cards(request):
    """Daftar semua kartu — halaman kerja pemilik situs.

    Terbuka saat DEBUG (dev di laptop) atau untuk staff. Di produksi dengan
    DEBUG mati, pengunjung biasa tidak bisa melihatnya: daftar ini memuat nama
    penerima dan link kartu orang lain.
    """
    if not (settings.DEBUG or request.user.is_staff):
        return render(request, "cards/not_yours.html", status=403)

    rows = []
    for card in GiftCard.objects.select_related("template").order_by("-updated_at"):
        rows.append(
            {
                "card": card,
                "public_url": card.public_url(),
                "share_url": request.build_absolute_uri(card.public_url()),
                "editor_url": reverse("cards:editor", args=[card.template.slug])
                + f"?card={card.id}",
                "pay_url": reverse("cards:pay", args=[card.id]),
            }
        )
    return render(
        request, "cards/my_cards.html", {"cards": rows, "dev_mode": settings.DEBUG}
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


def public_card_legacy(request, ref):
    """Alihkan bentuk lama /g/<ref>/ ke bentuk pendek /<ref>/.

    Permanen (301) supaya browser dan mesin pencari berhenti memakai bentuk
    lama. Kartu yang linknya sudah terlanjur dikirim ke penerima tetap terbuka
    — itu janji produknya, jadi rute ini tidak boleh dihapus.
    """
    return redirect("cards:public", ref=ref, permanent=True)


def _photo_payload(photo):
    """Bentuk foto yang dikirim ke editor. Sama dengan yang dipakai api_photos."""
    return {
        "id": photo.id,
        "url": photo.image.url,
        "caption": photo.caption,
        "slot": photo.slot,
        "order": photo.order,
    }


@lru_cache(maxsize=1)
def reserved_slugs():
    """Segmen URL yang tidak boleh diklaim jadi slug kartu.

    Dibangun dari urlpatterns yang sebenarnya, bukan daftar tulisan tangan.
    Sejak kartu memakai pola satu segmen (/<slug>/), slug yang menabrak halaman
    situs akan RUSAK DIAM-DIAM: Django mencocokkan pola halaman lebih dulu,
    jadi kartunya tidak pernah bisa dibuka dan tidak ada pesan error apa pun.

    Daftar literal terbukti mudah basi — lima halaman (kartu-saya, cara-kerja,
    harga, testimoni, faq) sempat luput karena ditambahkan setelah daftarnya
    ditulis. Dengan dibangun otomatis, halaman baru ikut terlindungi sendiri.
    """
    from django.urls import get_resolver

    reserved = {
        # Bukan dari urlpatterns cards, tapi tetap harus dijaga.
        "admin", "static", "media", "g", "robots.txt", "sitemap.xml", "favicon.ico",
    }
    for pattern in get_resolver().url_patterns:
        for sub in getattr(pattern, "url_patterns", [pattern]):
            route = str(getattr(sub.pattern, "_route", ""))
            head = route.split("/", 1)[0]
            # Lewati segmen bervariabel seperti "<str:ref>" — itu polanya
            # sendiri, bukan halaman yang bisa ditabrak.
            if head and "<" not in head:
                reserved.add(head)
    return frozenset(reserved)


def _free_slug(base, card_pk, tries=12):
    """Slug yang belum terpakai, dengan akhiran acak kalau `base` bentrok.

    Nama yang sama boleh dipakai banyak orang — URL-nya yang harus unik.
    Akhirannya acak, bukan berurutan (halo-2, halo-3, ...), supaya orang tidak
    bisa menebak link kartu orang lain hanya dengan menaikkan angkanya. Ini
    menjaga prinsip URL tidak bisa di-enumerate.
    """
    taken = GiftCard.objects.exclude(pk=card_pk)
    if not taken.filter(slug=base).exists():
        return base

    alphabet = "abcdefghijkmnpqrstuvwxyz23456789"  # tanpa l/o/0/1 yang mirip
    room = 60 - 1 - 4  # sisakan tempat untuk "-xxxx"
    stem = base[:room]
    for _ in range(tries):
        candidate = f"{stem}-{''.join(secrets.choice(alphabet) for _ in range(4))}"
        if not taken.filter(slug=candidate).exists():
            return candidate
    # Sangat tidak mungkin sampai sini; UUID kartu tetap jadi link cadangan.
    return f"{stem}-{secrets.token_hex(4)}"


@require_POST
def set_slug(request, card_id):
    """Ganti link kartu jadi nama pilihan user. Hanya setelah bayar, pemilik saja."""
    card = get_object_or_404(GiftCard, pk=card_id)
    if not (_owns(request, card) or request.user.is_staff):
        return render(request, "cards/not_yours.html", status=403)
    if not card.is_paid:
        return redirect("cards:pay", card_id=card.id)

    wanted = slugify(request.POST.get("slug", ""))[:60]
    error = ""
    if not wanted or len(wanted) < 3:
        error = "Minimal 3 karakter (huruf, angka, tanda minus)."
    elif wanted in reserved_slugs():
        error = "Nama itu tidak bisa dipakai."
    else:
        # _free_slug memeriksa lalu menyimpan, jadi dua permintaan bersamaan
        # bisa memilih slug yang sama dan menabrak batasan unique. Tanpa
        # penanganan ini user melihat error 500; dengan retry, akhiran acak
        # berikutnya hampir pasti lolos.
        slug = ""
        for _ in range(3):
            candidate = _free_slug(wanted, card.pk)
            try:
                card.slug = candidate
                card.save(update_fields=["slug", "updated_at"])
            except IntegrityError:
                card.refresh_from_db()
                continue
            slug = candidate
            break

        if not slug:
            error = "Link itu baru saja diambil orang lain. Coba nama lain."
        elif slug != wanted:
            request.session["slug_note"] = (
                f"“{wanted}” sudah dipakai kartu lain, jadi linkmu jadi "
                f"“{slug}”. Nama yang sama boleh dipakai banyak orang — "
                "yang membedakan cuma akhiran ini."
            )

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
