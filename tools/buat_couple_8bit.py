"""Aset animasi pasangan piksel (komponen _couple.html) dari lembar chibi.

    python tools/buat_couple_8bit.py      # perlu Pillow, numpy, scipy

Sumber dan cara memotongnya sama dengan tools/buat_sprite_8bit_chibi.py (kotak
frame diambil dari sana). Bedanya: di sini TIDAK ada pose rakitan. Spesifikasi
pemilik situs: frame yang tidak ada di lembar sumber dilaporkan, bukan
dikarang. Satu-satunya olahan adalah CERMIN langkah cewek (lembarnya cuma
punya langkah menghadap kanan, padahal ia berjalan dari kanan ke kiri).

Keluaran static/img/couple/:
  cowok.png  sel 112x240, baris: diam(1) | jalan ke kanan(6) | melambai(1)
  cewek.png  sel 128x240, baris: diam(1) | jalan ke kiri(5, dicermin) | respons(1)
  peluk.png  sel 208x272, satu baris: tiga pose pelukan dari lembar "COUPLE"
  gelembung-titik.png, gelembung-hati.png, hati.png
Kaki semua sel menempel di dasar sel dikurangi 4 px.
"""
import pathlib
import sys

import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage as nd

AKAR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AKAR / "tools"))
import buat_sprite_8bit_chibi as chibi  # noqa: E402

KELUAR = AKAR / "static" / "img" / "couple"

LEMBAR = {
    "cowok": ((112, 240), [["b_idle1"],
                           ["b_walk1", "b_walk2", "b_walk3", "b_walk4", "b_walk5", "b_walk6"],
                           ["b_pose2"]]),
    "cewek": ((128, 240), [["g_idle1"],
                           ["~g_walk1", "~g_walk2", "~g_walk3", "~g_walk4", "~g_walk5"],
                           ["g_pose2"]]),
    "peluk": ((208, 272), [["c_4", "c_5", "c_6"]]),
}
# Kotak yang dipersempit dari milik chibi: tepi kanan g_pose2 ikut memotong
# sejumput rambut cewek duduk (g_pose3) di sebelahnya, dan ujung rambut itu
# menyambung ke badannya sehingga lolos dari saringan "komponen terbesar".
KOTAK_KHUSUS = {"g_pose2": (1301, 1408, 380, 640)}

EKSTRA = {
    "gelembung-titik": (1268, 1343, 723, 786),
    "gelembung-hati": (1189, 1258, 724, 786),
    "hati": (1355, 1390, 731, 767),
}


def pusat(im, pecahan):
    a = np.asarray(im)[..., 3] > 0
    atas = a[: max(1, int(a.shape[0] * pecahan))]
    return np.where(atas.any(0))[0].mean()


def sel(im, lebar, tinggi, pecahan):
    if im.width > lebar or im.height > tinggi - 4:
        raise SystemExit(f"{im.size} tidak muat di sel {lebar}x{tinggi}")
    s = Image.new("RGBA", (lebar, tinggi), (0, 0, 0, 0))
    x = min(max(int(round(lebar / 2 - pusat(im, pecahan))), 0), lebar - im.width)
    s.alpha_composite(im, (x, tinggi - 4 - im.height))
    return s


def main():
    rgba = np.asarray(Image.open(chibi.SUMBER).convert("RGBA")).copy()
    fg = nd.binary_opening(~chibi.topeng_latar(rgba[..., :3].astype(int)), iterations=1)
    KELUAR.mkdir(parents=True, exist_ok=True)

    def ambil(nama):
        cermin = nama.startswith("~")
        im = chibi.potong(rgba, fg, KOTAK_KHUSUS.get(nama.lstrip("~")) or chibi.KOTAK[nama.lstrip("~")])
        return ImageOps.mirror(im) if cermin else im

    for berkas, ((lebar, tinggi), baris) in LEMBAR.items():
        kolom = max(len(b) for b in baris)
        lembar = Image.new("RGBA", (lebar * kolom, tinggi * len(baris)), (0, 0, 0, 0))
        # Tokoh tunggal diratakan dari kepala (badan jalan bergeser tiap langkah,
        # kepalanya tidak); pelukan dari seluruh tubuh (dua kepala, tak ada satu pusat).
        pecahan = 1.0 if berkas == "peluk" else 0.4
        for r, frames in enumerate(baris):
            for k, nama in enumerate(frames):
                lembar.alpha_composite(sel(ambil(nama), lebar, tinggi, pecahan), (k * lebar, r * tinggi))
        tujuan = KELUAR / f"{berkas}.png"
        lembar.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE).save(tujuan, optimize=True)
        print(f"{tujuan.relative_to(AKAR)}  {lembar.size}  {tujuan.stat().st_size // 1024} KB")

    for nama, kotak in EKSTRA.items():
        x0, x1, y0, y1 = kotak
        c = rgba[y0:y1, x0:x1].copy()
        c[..., 3] = np.where(fg[y0:y1, x0:x1], 255, 0)
        tujuan = KELUAR / f"{nama}.png"
        Image.fromarray(c).save(tujuan, optimize=True)
        print(f"{tujuan.relative_to(AKAR)}  {c.shape[1]}x{c.shape[0]}")


if __name__ == "__main__":
    main()
