"""Katalog font & pembersih gaya.

Nilai dari editor berakhir di dalam CSS kartu, jadi TIDAK ADA nilai mentah dari
user yang dipakai langsung: semuanya dicocokkan dengan daftar putih di sini.
Yang tidak cocok dibuang, bukan diperbaiki diam-diam.

Model gayanya per ELEMEN, bukan per slot tetap. Setiap elemen yang ditandai
template punya gaya sendiri, dan nilai yang tidak diisi berarti "pakai bawaan
template" — karena itu var CSS-nya tidak diemit sama sekali.
"""

import re

# key → (nama Google Fonts, spesifikasi bobot untuk URL, css font-family, kelompok)
FONTS = {
    # — Serif klasik —
    "cormorant": ("Cormorant Garamond", "wght@400;600;700", "'Cormorant Garamond', Georgia, serif", "Serif"),
    "playfair": ("Playfair Display", "wght@400;600;700", "'Playfair Display', Georgia, serif", "Serif"),
    "lora": ("Lora", "wght@400;600;700", "'Lora', Georgia, serif", "Serif"),
    "baskerville": ("Libre Baskerville", "wght@400;700", "'Libre Baskerville', Georgia, serif", "Serif"),
    "garamond": ("EB Garamond", "wght@400;600;700", "'EB Garamond', Georgia, serif", "Serif"),
    "prata": ("Prata", "", "'Prata', Georgia, serif", "Serif"),
    # — Sans —
    "inter": ("Inter", "wght@400;600;700", "'Inter', system-ui, sans-serif", "Sans"),
    "poppins": ("Poppins", "wght@400;600;700", "'Poppins', system-ui, sans-serif", "Sans"),
    "montserrat": ("Montserrat", "wght@400;600;700", "'Montserrat', system-ui, sans-serif", "Sans"),
    "raleway": ("Raleway", "wght@400;600;700", "'Raleway', system-ui, sans-serif", "Sans"),
    "nunito": ("Nunito", "wght@400;600;700", "'Nunito', system-ui, sans-serif", "Sans"),
    "worksans": ("Work Sans", "wght@400;600;700", "'Work Sans', system-ui, sans-serif", "Sans"),
    # — Tulisan tangan —
    "caveat": ("Caveat", "wght@400;600;700", "'Caveat', cursive", "Tulisan tangan"),
    "dancing": ("Dancing Script", "wght@400;600;700", "'Dancing Script', cursive", "Tulisan tangan"),
    "satisfy": ("Satisfy", "", "'Satisfy', cursive", "Tulisan tangan"),
    "sacramento": ("Sacramento", "", "'Sacramento', cursive", "Tulisan tangan"),
    "shadows": ("Shadows Into Light", "", "'Shadows Into Light', cursive", "Tulisan tangan"),
    # — Kaligrafi —
    "pinyon": ("Pinyon Script", "", "'Pinyon Script', cursive", "Kaligrafi"),
    "greatvibes": ("Great Vibes", "", "'Great Vibes', cursive", "Kaligrafi"),
    "parisienne": ("Parisienne", "", "'Parisienne', cursive", "Kaligrafi"),
    "allura": ("Allura", "", "'Allura', cursive", "Kaligrafi"),
    # — Tegas —
    "bebas": ("Bebas Neue", "", "'Bebas Neue', Impact, sans-serif", "Tegas"),
    "abril": ("Abril Fatface", "", "'Abril Fatface', Georgia, serif", "Tegas"),
    "lobster": ("Lobster", "", "'Lobster', cursive", "Tegas"),
}

FONT_GROUPS = ["Serif", "Sans", "Tulisan tangan", "Kaligrafi", "Tegas"]

ALIGNMENTS = ("left", "center", "right")
PHOTO_FITS = ("cover", "contain")

SIZE_MIN, SIZE_MAX = 0.5, 3.0
ZOOM_MIN, ZOOM_MAX = 1.0, 4.0
SPACING_MIN, SPACING_MAX = -0.05, 0.6
LINE_MIN, LINE_MAX = 0.8, 2.6

HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
# Kunci elemen ikut jadi nama atribut & kunci JSON — pola ketat.
ELEMENT_KEY = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
MAX_ELEMENTS = 80

# Palet siap pakai supaya user tidak harus meracik warna sendiri.
PALETTES = [
    {"name": "Merah Klasik", "bg": "#9E1B32", "ink": "#FBF4E6"},
    {"name": "Pastel Manis", "bg": "#F3C9D4", "ink": "#6E3B48"},
    {"name": "Senja", "bg": "#C9724A", "ink": "#FFF3E9"},
    {"name": "Laut Tenang", "bg": "#4E7C8C", "ink": "#F0F7F9"},
    {"name": "Malam", "bg": "#20191C", "ink": "#F3E7DC"},
    {"name": "Taman", "bg": "#6E8C5A", "ink": "#F4F8EF"},
    {"name": "Gading", "bg": "#FAF2E4", "ink": "#5A4634"},
    {"name": "Lavender", "bg": "#8D7BA5", "ink": "#F7F3FA"},
]

# Warna cepat untuk pemilih warna teks.
SWATCHES = [
    "#FFFFFF", "#F5EDE2", "#E8C9A0", "#C9A24C",
    "#E78EA0", "#C9736E", "#9E1B32", "#7A1526",
    "#8D7BA5", "#4E7C8C", "#6E8C5A", "#3B2F2A",
    "#7C6A60", "#B9AFA6", "#2B2320", "#000000",
]


def _num(value, lo, hi, fallback=None):
    try:
        return round(min(max(float(value), lo), hi), 3)
    except (TypeError, ValueError):
        return fallback


def _fmt(value):
    """1.0 → "1", 1.50 → "1.5". Supaya CSS-nya bersih dan mudah dibaca."""
    text = f"{float(value):g}"
    return text


def _color_or_none(value):
    value = str(value or "")
    return value if HEX_COLOR.match(value) else None


def sanitize_element(raw):
    """Gaya satu elemen. Kunci yang tidak diisi DIBUANG, bukan diberi bawaan.

    Itu penting: tidak ada nilai = pakai bawaan template, dan var CSS-nya tidak
    diemit sama sekali sehingga desain asli template tetap utuh.
    """
    if not isinstance(raw, dict):
        return {}

    clean = {}
    if raw.get("font") in FONTS:
        clean["font"] = raw["font"]

    size = _num(raw.get("size"), SIZE_MIN, SIZE_MAX)
    if size is not None:
        clean["size"] = size

    color = _color_or_none(raw.get("color"))
    if color:
        clean["color"] = color

    if raw.get("align") in ALIGNMENTS:
        clean["align"] = raw["align"]

    if raw.get("bold") is True:
        clean["bold"] = True
    if raw.get("italic") is True:
        clean["italic"] = True

    spacing = _num(raw.get("spacing"), SPACING_MIN, SPACING_MAX)
    if spacing is not None:
        clean["spacing"] = spacing

    line = _num(raw.get("line"), LINE_MIN, LINE_MAX)
    if line is not None:
        clean["line"] = line

    if raw.get("fit") in PHOTO_FITS:
        clean["fit"] = raw["fit"]

    radius = _num(raw.get("radius"), 0, 50)
    if radius is not None:
        clean["radius"] = radius

    # Crop = geser + perbesar di dalam bingkai. Foto aslinya tidak diubah,
    # jadi user bisa mengatur ulang kapan saja tanpa mengunggah lagi.
    zoom = _num(raw.get("zoom"), ZOOM_MIN, ZOOM_MAX)
    if zoom is not None:
        clean["zoom"] = zoom
    for axis in ("ox", "oy"):
        pos = _num(raw.get(axis), 0, 100)
        if pos is not None:
            clean[axis] = pos

    return clean


def sanitize_style(raw):
    """Seluruh gaya kartu: {"elements": {key: {...}}, "colors": {key: "#hex"}}."""
    if not isinstance(raw, dict):
        raw = {}

    elements = {}
    incoming = raw.get("elements")
    if isinstance(incoming, dict):
        for key, conf in list(incoming.items())[:MAX_ELEMENTS]:
            if not ELEMENT_KEY.match(str(key)):
                continue
            cleaned = sanitize_element(conf)
            if cleaned:
                elements[str(key)] = cleaned

    colors = {}
    incoming_colors = raw.get("colors")
    if isinstance(incoming_colors, dict):
        for key, value in list(incoming_colors.items())[:MAX_ELEMENTS]:
            color = _color_or_none(value)
            if ELEMENT_KEY.match(str(key)) and color:
                colors[str(key)] = color

    return {"elements": elements, "colors": colors}


# Nama var sengaja pendek & lokal ke elemen, jadi CSS template cukup menulis
# var(--f, <bawaan>) tanpa perlu tahu kunci elemennya.
def element_css(conf):
    """Deklarasi CSS untuk satu elemen. String kosong kalau tidak ada yang diatur."""
    conf = sanitize_element(conf)
    parts = []
    if "font" in conf:
        parts.append(f"--f:{FONTS[conf['font']][2]}")
    if "size" in conf:
        parts.append(f"--fs:{_fmt(conf['size'])}")
    if "color" in conf:
        parts.append(f"--c:{conf['color']}")
    if "align" in conf:
        parts.append(f"--al:{conf['align']}")
    if conf.get("bold"):
        parts.append("--fw:700")
    if conf.get("italic"):
        parts.append("--fi:italic")
    if "spacing" in conf:
        parts.append(f"--ls:{_fmt(conf['spacing'])}em")
    if "line" in conf:
        parts.append(f"--lh:{_fmt(conf['line'])}")
    if "fit" in conf:
        parts.append(f"--fit:{conf['fit']}")
    if "radius" in conf:
        parts.append(f"--br:{_fmt(conf['radius'])}px")
    if "zoom" in conf:
        parts.append(f"--zoom:{_fmt(conf['zoom'])}")
    if "ox" in conf:
        parts.append(f"--ox:{_fmt(conf['ox'])}%")
    if "oy" in conf:
        parts.append(f"--oy:{_fmt(conf['oy'])}%")
    return ";".join(parts)


def colors_css(colors):
    """Warna permukaan sebagai var global: --c-<kunci>."""
    parts = [f"--c-{key}:{value}" for key, value in (colors or {}).items()]
    return ";".join(parts)


def google_fonts_url(font_keys=None):
    """URL Google Fonts. Tanpa argumen = seluruh katalog (dipakai editor).

    Halaman kartu asli hanya memuat font yang benar-benar dipakai, supaya
    kartunya cepat dibuka di HP penerima.
    """
    keys = list(FONTS) if font_keys is None else [k for k in font_keys if k in FONTS]
    if not keys:
        return ""
    families = []
    for key in keys:
        name, weights, _css, _group = FONTS[key]
        family = name.replace(" ", "+")
        families.append(f"family={family}:{weights}" if weights else f"family={family}")
    return "https://fonts.googleapis.com/css2?" + "&".join(families) + "&display=swap"


def font_catalog():
    """Untuk pemilih font di editor, dikelompokkan."""
    return [
        {
            "group": group,
            "fonts": [
                {"key": key, "name": FONTS[key][0], "css": FONTS[key][2]}
                for key in FONTS
                if FONTS[key][3] == group
            ],
        }
        for group in FONT_GROUPS
    ]
