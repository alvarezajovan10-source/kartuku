"""Sprite sheet dua karakter Game 8-Bit dari lembar sprite chibi pemilik situs.

Menggantikan tools/buat_sprite_8bit.py (karakter 34x46 yang dirakit dari
bagian tubuh ASCII) sejak 12 Okt 2026, atas permintaan pemilik situs. Yang
lama TIDAK dihapus: kalau keputusannya berbalik, jalankan saja skrip itu dan
kembalikan ukuran di game8bit.css/js (102x138).

    python tools/buat_sprite_8bit_chibi.py     # perlu Pillow, numpy, scipy

Sumber: tools/8bit/lembar_chibi.png (1536x1024, "Lembar Sprite Pixel Chibi
Romantis"; tidak di-commit — 2,8 MB). Latar kotak-kotaknya BAGIAN dari
gambar, bukan transparansi: dibuang dengan mencari piksel terang tak berwarna
(saturasi < 14, terang > 222) yang tersambung ke tepi gambar. Putih di dalam
badan (sweter, kaus kaki) selamat karena dikurung garis luar.

Keluaran: static/img/render/8bit-{cowok,cewek}.png, kisi 6 kolom x 12 baris,
sel 128x256 (tampil 85x170, lihat game8bit.css). Kaki menempel di BASELINE;
posisi mendatar diratakan dari KEPALA (40% atas), bukan seluruh badan — badan
jalan bergeser maju-mundur tiap langkah, kepalanya tidak, jadi kepala yang
diam itulah yang membuat jalannya tidak bergoyang.

Gambar sumber tidak punya semua gerakan template ini (lompat, rayakan, tiup
lilin, peluk). Yang tidak ada dirakit: KEPALA ekspresi ditempel ke badan
berdiri ("+"), dan lompatan = frame yang sama diangkat ("^n").
"""
import pathlib

import numpy as np
from PIL import Image
from scipy import ndimage as nd

AKAR = pathlib.Path(__file__).resolve().parent.parent
SUMBER = AKAR / "tools" / "8bit" / "lembar_chibi.png"
KELUAR = AKAR / "static" / "img" / "render"

SEL_L, SEL_T = 128, 256
BASELINE = 252
KOLOM = 6

# Urutan baris = ANIM di static/js/render/game8bit.js. Jangan diubah sendiri.
URUTAN = ["idle", "walk", "run", "wave", "happy", "surprised",
          "sit", "sleep", "jump", "celebrate", "hug", "blow"]

# Kotak tiap frame di lembar sumber (x0, x1, y0, y1) — hasil belah kolom kosong.
KOTAK = {
    "b_idle1": (16, 109, 62, 300),
    "b_idle2": (116, 210, 62, 300),
    "b_idle3": (216, 312, 62, 300),
    "b_walk1": (323, 435, 62, 300),
    "b_walk2": (435, 540, 62, 300),
    "b_walk3": (540, 639, 62, 300),
    "b_walk4": (639, 737, 62, 300),
    "b_walk5": (737, 837, 62, 300),
    "b_walk6": (837, 933, 62, 300),
    "b_pose1": (1189, 1298, 62, 300),
    "b_pose2": (1313, 1419, 62, 300),
    "b_pose3": (1427, 1525, 62, 300),
    "b_ex1": (955, 1053, 62, 180),
    "b_ex2": (1059, 1163, 62, 180),
    "b_ex3": (955, 1053, 180, 300),
    "b_ex4": (1059, 1163, 180, 300),
    "g_idle1": (4, 119, 380, 640),
    "g_idle2": (119, 231, 380, 640),
    "g_idle3": (235, 349, 380, 640),
    "g_walk1": (356, 480, 380, 640),
    "g_walk2": (480, 599, 380, 640),
    "g_walk3": (599, 716, 380, 640),
    "g_walk4": (716, 829, 380, 640),
    "g_walk5": (829, 943, 380, 640),
    "g_pose1": (1181, 1301, 380, 640),
    "g_pose2": (1301, 1417, 380, 640),
    "g_pose3": (1417, 1535, 380, 640),
    "g_ex1": (952, 1058, 380, 505),
    "g_ex2": (1066, 1176, 380, 505),
    "g_ex3": (952, 1058, 505, 640),
    "g_ex4": (1066, 1176, 505, 640),
    "c_1": (22, 227, 712, 1010),
    "c_2": (244, 433, 712, 1010),
    "c_3": (443, 632, 712, 1010),
    "c_4": (637, 815, 712, 1010),
    "c_5": (828, 986, 712, 1010),
    "c_6": (1001, 1160, 712, 1010),
    "x_heart": (1352, 1393, 720, 770),
}

ANIMASI = {
    "cowok": {
        "idle": ["b_idle1", "b_idle2"],
        "walk": ["b_walk1", "b_walk2", "b_walk3", "b_walk4", "b_walk5", "b_walk6"],
        "run": ["b_walk1", "b_walk2", "b_walk3", "b_walk4", "b_walk5", "b_walk6"],
        "wave": ["b_pose2", "b_idle1"],
        "happy": ["b_idle1+b_ex3", "b_idle1+b_ex1"],
        "surprised": ["b_idle1+b_ex2", "b_idle1"],
        "sit": ["b_pose1", "b_pose1^1"],
        "sleep": ["b_pose3", "b_pose3^1"],
        "jump": ["b_idle1", "b_idle1^16", "b_idle1^6"],
        "celebrate": ["b_pose2", "b_pose2^14", "b_idle1+b_ex1", "b_idle1+b_ex1^14"],
        "hug": ["b_pose3", "b_idle3"],
        "blow": ["b_idle1+b_ex4", "b_idle1", "b_idle1+b_ex3"],
    },
    "cewek": {
        "idle": ["g_idle1", "g_idle2"],
        "walk": ["g_walk1", "g_walk2", "g_walk3", "g_walk4", "g_walk5"],
        "run": ["g_walk1", "g_walk2", "g_walk3", "g_walk4", "g_walk5"],
        "wave": ["g_idle1+g_ex1", "g_idle1"],
        "happy": ["g_idle1+g_ex1", "g_pose2"],
        "surprised": ["g_idle1+g_ex2", "g_idle1"],
        "sit": ["g_pose3", "g_pose3^1"],
        "sleep": ["g_pose1", "g_pose1^1"],
        "jump": ["g_idle1", "g_idle1^16", "g_idle1^6"],
        "celebrate": ["g_pose2", "g_pose2^14", "g_idle1+g_ex1", "g_idle1+g_ex1^14"],
        "hug": ["g_idle1+g_ex4", "g_pose2"],
        "blow": ["g_idle1+g_ex3", "g_idle1", "g_idle1+g_ex3"],
    },
}


def topeng_latar(a):
    sat = a.max(2) - a.min(2)
    terang = a.mean(2)
    lab, _ = nd.label((sat < 14) & (terang > 222))
    tepi = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    return np.isin(lab, list(tepi))


def potong(rgba, fg, kotak):
    x0, x1, y0, y1 = kotak
    sub = fg[y0:y1, x0:x1]
    lab, n = nd.label(nd.binary_dilation(sub, iterations=2))
    if n > 1:  # buang serpihan frame tetangga yang ikut terbelah
        besar = nd.sum(sub, lab, range(1, n + 1))
        sub = (lab == np.argmax(besar) + 1) & sub
    potongan = rgba[y0:y1, x0:x1].copy()
    potongan[..., 3] = np.where(sub, 255, 0)
    b = np.where(sub.any(1))[0]
    k = np.where(sub.any(0))[0]
    return Image.fromarray(potongan[b[0]:b[-1] + 1, k[0]:k[-1] + 1])


def pusat_kepala(im):
    a = np.asarray(im)[..., 3] > 0
    atas = a[: max(1, int(a.shape[0] * 0.4))]
    return np.where(atas.any(0))[0].mean()


def tempel_kepala(badan, kepala):
    """Kepala ekspresi (80% atas potongannya) ditempel di atas badan berdiri."""
    hasil = badan.copy()
    k = kepala.crop((0, 0, kepala.width, int(kepala.height * 0.8)))
    a_b = np.asarray(badan)[..., 3] > 0
    a_k = np.asarray(k)[..., 3] > 0
    x = int(round(np.where(a_b[:30].any(0))[0].mean() - np.where(a_k[:30].any(0))[0].mean()))
    if x < 0:
        k = k.crop((-x, 0, k.width, k.height))
        x = 0
    hasil.alpha_composite(k, (x, 0))
    return hasil


def frame(nama, bagian):
    angkat = 0
    if "^" in nama:
        nama, n = nama.split("^")
        angkat = int(n)
    if "+" in nama:
        badan, kepala = nama.split("+")
        im = tempel_kepala(bagian[badan], bagian[kepala])
    else:
        im = bagian[nama]
    sel = Image.new("RGBA", (SEL_L, SEL_T), (0, 0, 0, 0))
    if im.width > SEL_L or im.height > BASELINE - angkat:
        raise SystemExit(f"{nama}: {im.size} tidak muat di sel {SEL_L}x{SEL_T}")
    x = int(round(SEL_L / 2 - pusat_kepala(im)))
    x = min(max(x, 0), SEL_L - im.width)
    sel.alpha_composite(im, (x, BASELINE - angkat - im.height))
    return sel


def main():
    rgba = np.asarray(Image.open(SUMBER).convert("RGBA")).copy()
    fg = nd.binary_opening(~topeng_latar(rgba[..., :3].astype(int)), iterations=1)
    bagian = {k: potong(rgba, fg, v) for k, v in KOTAK.items()}
    for siapa, anim in ANIMASI.items():
        lembar = Image.new("RGBA", (SEL_L * KOLOM, SEL_T * len(URUTAN)), (0, 0, 0, 0))
        for baris, nama_anim in enumerate(URUTAN):
            for kolom, nama in enumerate(anim[nama_anim]):
                lembar.alpha_composite(frame(nama, bagian), (kolom * SEL_L, baris * SEL_T))
        tujuan = KELUAR / f"8bit-{siapa}.png"
        # 256 warna tanpa dither: dari 1,2-1,35 MB ke ~230-280 KB. Aman karena
        # alfanya cuma 0/255 dan gambarnya bergaya piksel (warnanya sedikit).
        lembar.quantize(256, method=Image.Quantize.FASTOCTREE,
                        dither=Image.Dither.NONE).save(tujuan, optimize=True)
        print(f"{tujuan.relative_to(AKAR)}  {lembar.size}  {tujuan.stat().st_size // 1024} KB  "
              + " ".join(f"{a}:{len(anim[a])}" for a in URUTAN))


if __name__ == "__main__":
    main()
