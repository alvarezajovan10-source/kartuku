"""Katalog gaya yang boleh dipilih user, plus pembersihnya.

Nilai dari editor berakhir di dalam CSS kartu. Karena itu TIDAK ADA nilai mentah
dari user yang pernah dipakai langsung: semuanya dicocokkan dengan daftar putih
di sini, dan yang tidak cocok diganti nilai bawaan. Ini yang menahan orang
menyuntikkan CSS lewat kolom warna atau font.
"""

import re

# key → (nama Google Fonts, css font-family)
FONTS = {
    "serif": ("Cormorant Garamond", "'Cormorant Garamond', Georgia, serif"),
    "sans": ("Inter", "'Inter', system-ui, -apple-system, sans-serif"),
    "script": ("Dancing Script", "'Dancing Script', cursive"),
    "hand": ("Caveat", "'Caveat', cursive"),
    "formal": ("Pinyon Script", "'Pinyon Script', cursive"),
    "modern": ("Playfair Display", "'Playfair Display', Georgia, serif"),
}

FONT_LABELS = {
    "serif": "Klasik",
    "sans": "Bersih",
    "script": "Manis",
    "hand": "Tulisan tangan",
    "formal": "Formal",
    "modern": "Elegan",
}

ALIGNMENTS = ("left", "center", "right")
PHOTO_SHAPES = ("rounded", "square", "circle", "polaroid")

# Blok teks yang bisa diatur user.
SLOTS = ("title", "message", "signature")
SLOT_LABELS = {
    "title": "Judul",
    "message": "Pesan",
    "signature": "Tanda tangan",
}

SIZE_MIN, SIZE_MAX = 0.7, 1.8

HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
# Kunci warna bebas dari template. Pola ketat karena kunci ini jadi bagian
# nama CSS custom property (--c-<kunci>).
COLOR_KEY = re.compile(r"^[a-z0-9_]{1,32}$")
MAX_COLORS = 24

DEFAULT_STYLE = {
    "title": {"font": "formal", "color": "#7A1526", "size": 1.0, "align": "center"},
    "message": {"font": "hand", "color": "#4A2530", "size": 1.0, "align": "left"},
    "signature": {"font": "hand", "color": "#8A1F2E", "size": 1.0, "align": "right"},
    "bg": "#FAF2E4",
    "accent": "#9E1B32",
    "photo_shape": "rounded",
    "colors": {},
}

# Palet siap pakai supaya user tidak harus meracik warna sendiri.
PALETTES = [
    {"name": "Merah Klasik", "bg": "#FAF2E4", "accent": "#9E1B32", "ink": "#7A1526"},
    {"name": "Pastel Manis", "bg": "#FDF3F5", "accent": "#D98A9E", "ink": "#7C4A57"},
    {"name": "Senja", "bg": "#FCEFE6", "accent": "#C9724A", "ink": "#6B3B27"},
    {"name": "Laut Tenang", "bg": "#EEF4F6", "accent": "#4E7C8C", "ink": "#2F4A54"},
    {"name": "Malam", "bg": "#20191C", "accent": "#C9A24C", "ink": "#F3E7DC"},
    {"name": "Taman", "bg": "#F1F5EC", "accent": "#6E8C5A", "ink": "#3C4A32"},
]


def _clamp_size(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 1.0
    return round(min(max(number, SIZE_MIN), SIZE_MAX), 2)


def _color(value, fallback):
    value = str(value or "")
    return value if HEX_COLOR.match(value) else fallback


def _pick(value, allowed, fallback):
    return value if value in allowed else fallback


def sanitize_style(raw):
    """Kembalikan struktur gaya yang lengkap & aman, apa pun isi `raw`.

    Selalu mengembalikan semua kunci, jadi template tidak perlu menjaga-jaga.
    """
    if not isinstance(raw, dict):
        raw = {}

    clean = {}
    for slot in SLOTS:
        incoming = raw.get(slot)
        if not isinstance(incoming, dict):
            incoming = {}
        default = DEFAULT_STYLE[slot]
        clean[slot] = {
            "font": _pick(incoming.get("font"), FONTS, default["font"]),
            "color": _color(incoming.get("color"), default["color"]),
            "size": _clamp_size(incoming.get("size", default["size"])),
            "align": _pick(incoming.get("align"), ALIGNMENTS, default["align"]),
        }

    clean["bg"] = _color(raw.get("bg"), DEFAULT_STYLE["bg"])
    clean["accent"] = _color(raw.get("accent"), DEFAULT_STYLE["accent"])
    clean["photo_shape"] = _pick(
        raw.get("photo_shape"), PHOTO_SHAPES, DEFAULT_STYLE["photo_shape"]
    )

    # Warna permukaan yang ditentukan template (latar tiap babak, dsb.).
    colors = raw.get("colors")
    clean["colors"] = {}
    if isinstance(colors, dict):
        for key, value in list(colors.items())[:MAX_COLORS]:
            if COLOR_KEY.match(str(key)) and HEX_COLOR.match(str(value)):
                clean["colors"][str(key)] = str(value)

    return clean


def css_variables(style):
    """Ubah gaya bersih jadi deklarasi CSS custom property.

    Aman ditaruh di atribut `style` karena tiap nilai sudah lolos daftar putih.
    """
    style = sanitize_style(style)
    parts = [
        f"--bg:{style['bg']}",
        f"--accent:{style['accent']}",
    ]
    for key, value in style["colors"].items():
        parts.append(f"--c-{key}:{value}")
    for slot in SLOTS:
        conf = style[slot]
        parts += [
            f"--{slot}-font:{FONTS[conf['font']][1]}",
            f"--{slot}-color:{conf['color']}",
            f"--{slot}-size:{conf['size']}",
            f"--{slot}-align:{conf['align']}",
        ]
    return ";".join(parts)


def google_fonts_url():
    """Satu URL Google Fonts berisi semua font di katalog."""
    families = "&".join(
        "family=" + FONTS[key][0].replace(" ", "+") + ":wght@400;500;600;700"
        for key in FONTS
    )
    return f"https://fonts.googleapis.com/css2?{families}&display=swap"


def font_choices():
    """Untuk dropdown di editor: [(key, label, css font-family), ...]"""
    return [(key, FONT_LABELS[key], FONTS[key][1]) for key in FONTS]
