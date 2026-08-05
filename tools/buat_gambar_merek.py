"""Hasilkan favicon dan gambar preview (Open Graph) dari warna merek Kartuku.

Dijalankan sekali di laptop; hasilnya di-commit ke static/img/. Server tidak
perlu Pillow maupun font apa pun untuk menyajikannya.

    python3 tools/buat_gambar_merek.py

Font diambil dari macOS (Georgia). Kalau dijalankan di mesin lain tanpa font
itu, Pillow jatuh ke font bawaan — hasilnya tetap jadi, cuma kurang cantik.
"""

import pathlib

from PIL import Image, ImageDraw, ImageFont

KELUAR = pathlib.Path(__file__).resolve().parent.parent / "static" / "img"

CREAM = (253, 249, 245)
CREAM_DEEP = (247, 237, 228)
ROSE = (201, 115, 110)
ROSE_SOFT = (221, 151, 145)
INK = (59, 47, 42)
INK_SOFT = (111, 95, 87)

GEORGIA = "/System/Library/Fonts/Supplemental/Georgia.ttf"
GEORGIA_ITALIC = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"


def font(path, ukuran):
    try:
        return ImageFont.truetype(path, ukuran)
    except OSError:
        return ImageFont.load_default(ukuran)


def hati(draw, cx, cy, lebar, warna):
    """Hati dari dua lingkaran + satu segitiga.

    Bentuk kasar tapi terbaca jelas pada ukuran favicon 32px, yang justru
    ukuran paling menentukan — di situ detail apa pun hilang.
    """
    r = lebar / 3.6
    atas = cy - lebar * 0.12
    draw.ellipse([cx - r * 1.55, atas - r, cx + r * 0.05, atas + r], fill=warna)
    draw.ellipse([cx - r * 0.05, atas - r, cx + r * 1.55, atas + r], fill=warna)
    draw.polygon(
        [(cx - lebar * 0.43, atas + r * 0.28),
         (cx + lebar * 0.43, atas + r * 0.28),
         (cx, cy + lebar * 0.5)],
        fill=warna,
    )


def buat_favicon():
    """Digambar 512px lalu diperkecil — tepinya jadi halus tanpa antialias manual."""
    besar = 512
    img = Image.new("RGBA", (besar, besar), CREAM + (255,))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, besar, besar], fill=CREAM_DEEP)
    hati(d, besar / 2, besar / 2, besar * 0.62, ROSE)

    (KELUAR / "favicon-512.png").parent.mkdir(parents=True, exist_ok=True)
    img.save(KELUAR / "favicon-512.png")
    img.resize((180, 180), Image.LANCZOS).save(KELUAR / "apple-touch-icon.png")
    img.save(KELUAR / "favicon.ico",
             sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    return ["favicon-512.png", "apple-touch-icon.png", "favicon.ico"]


def buat_og():
    """1200x630 — ukuran yang dipakai WhatsApp, Instagram, dan Facebook."""
    L, T = 1200, 630
    img = Image.new("RGB", (L, T), CREAM)
    d = ImageDraw.Draw(img)

    # Pita lembut di tepi bawah supaya tidak terlihat kosong.
    d.rectangle([0, T - 96, L, T], fill=CREAM_DEEP)
    for i, x in enumerate(range(80, L, 190)):
        hati(d, x, T - 48, 34 if i % 2 else 26, ROSE_SOFT)

    hati(d, L / 2, 176, 122, ROSE)

    judul = font(GEORGIA, 92)
    tag = font(GEORGIA_ITALIC, 40)
    harga = font(GEORGIA, 33)

    def tengah(teks, f, y, warna):
        kiri, atas, kanan, bawah = d.textbbox((0, 0), teks, font=f)
        d.text(((L - (kanan - kiri)) / 2 - kiri, y - atas), teks, font=f, fill=warna)

    tengah("Kartuku", judul, 268, INK)
    tengah("Ucapan tulus, hadiah berkesan", tag, 392, ROSE)
    tengah("Kartu ucapan digital · Rp15.000 sekali bayar", harga, 462, INK_SOFT)

    img.save(KELUAR / "og-default.jpg", quality=88, optimize=True)
    return ["og-default.jpg"]


if __name__ == "__main__":
    dibuat = buat_favicon() + buat_og()
    for nama in dibuat:
        p = KELUAR / nama
        print(f"  {nama:<22} {p.stat().st_size / 1024:6.1f} KB")
