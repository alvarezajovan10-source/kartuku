"""Topeng bentuk bingkai foto, untuk kotak crop di editor.

MASALAHNYA. Kotak crop di editor dibentuk dari satu angka: `rasio`
(lebar/tinggi). Untuk bingkai persegi panjang itu cukup. Untuk bingkai HATI
tidak: pembeli menyusun fotonya di dalam kotak, lalu yang tampil di kartu
adalah potongan hati — dan bagian yang tadi ia atur baik-baik di sudut kotak
ternyata terbuang. Terukur, tiga bingkai template ini cuma terisi ~67% dari
kotak pembatasnya, jadi sepertiga dari yang dilihat pembeli saat memotong
adalah bagian yang tidak akan pernah muncul.

    /tmp/pdfenv/bin/python tools/buat_topeng_bingkai.py

YANG DIKERJAKAN. Bentuk hatinya TIDAK digambar ulang. Ia sudah ada, sebagai
LUBANG beralfa di pelat halamannya — sumber kebenaran yang sama persis dengan
yang memotong foto di kartu sungguhan. Skrip ini memotong lubang itu pada
kotak bingkainya, membaliknya jadi topeng (pekat DI DALAM lubang, tembus di
luar), dan menyimpannya sebagai PNG kecil.

Editor memakainya sebagai lapisan peredup di atas kanvas crop: bagian yang
akan terbuang jadi gelap, bagian yang akan tampil tetap terang. Foto yang
diunggah TIDAK ikut ditopengi — pemotongnya tetap lubang di pelat, sama
seperti sebelumnya. Lihat catatan di drawCrop() pada alpine-editor.js.

Yang bukan kotak ditentukan dengan MENGUKUR, bukan didaftar tangan: bingkai
yang lubangnya mengisi >= AMBANG_KOTAK dari kotaknya dianggap persegi panjang
dan dilewati. Dengan begitu, bingkai berbentuk baru yang ditambahkan nanti
ikut terlayani tanpa ada yang perlu ingat menyunting berkas ini.
"""
import os
import re

import numpy as np
from PIL import Image

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(AKAR, "cards", "templates", "cards", "render", "valentine.html")
PELAT = os.path.join(AKAR, "static", "img", "valentine")
KELUARAN = os.path.join(PELAT, "topeng")

AMBANG_KOTAK = 0.90     # >= segini dianggap kotak; tidak perlu topeng
SISI_MAKS = 512         # topeng cuma lapisan peredup, tidak perlu resolusi pelat
TEMBUS = 128            # alfa di bawah ini = lubang foto

POLA = re.compile(
    r'--kiri:([\d.]+)%;--atas:([\d.]+)%;--lebar:([\d.]+)%;--tinggi:([\d.]+)%"\s*'
    r'\{%\s*frame card editing "([a-z0-9_]+)"'
)


def bingkai():
    """(halaman, kunci, kiri, atas, lebar, tinggi) tiap bingkai di valentine.html."""
    with open(HTML, encoding="utf-8") as f:
        html = f.read()
    keluar = []
    bagian = re.split(r'<section class="scene lembar" id="hal(\d+)"', html)
    for i in range(1, len(bagian), 2):
        nomor, isi = int(bagian[i]), bagian[i + 1]
        for kiri, atas, lebar, tinggi, kunci in POLA.findall(isi):
            keluar.append((nomor, kunci, float(kiri), float(atas),
                           float(lebar), float(tinggi)))
    if not keluar:
        raise SystemExit("tidak ada bingkai terbaca — pola markupnya berubah?")
    return keluar


def main():
    os.makedirs(KELUARAN, exist_ok=True)
    dibuat, dilewati = [], []

    for nomor, kunci, kiri, atas, lebar, tinggi in bingkai():
        berkas = os.path.join(PELAT, f"hal{nomor:02d}.webp")
        im = Image.open(berkas)
        if im.mode not in ("RGBA", "LA"):
            dilewati.append((kunci, f"hal{nomor:02d} tanpa alfa"))
            continue

        a = np.asarray(im.convert("RGBA"))[..., 3]
        H, W = a.shape
        x0, y0 = round(kiri / 100 * W), round(atas / 100 * H)
        x1, y1 = round((kiri + lebar) / 100 * W), round((atas + tinggi) / 100 * H)
        potong = a[y0:y1, x0:x1]
        if potong.size == 0:
            dilewati.append((kunci, "kotak kosong"))
            continue

        isi = float((potong < TEMBUS).mean())
        if isi >= AMBANG_KOTAK:
            dilewati.append((kunci, f"kotak ({isi * 100:.1f}% terisi)"))
            continue

        # Topeng: pekat DI DALAM lubang. Editor memakai alfa ini dengan
        # composite "destination-out", jadi yang pekat itulah yang tetap
        # terang di kanvas crop.
        topeng = np.zeros(potong.shape + (4,), dtype=np.uint8)
        topeng[..., 0:3] = 255
        topeng[..., 3] = 255 - potong

        keluar = Image.fromarray(topeng, "RGBA")
        keluar.thumbnail((SISI_MAKS, SISI_MAKS), Image.LANCZOS)
        tujuan = os.path.join(KELUARAN, f"{kunci}.png")
        keluar.save(tujuan, "PNG", optimize=True)
        dibuat.append((kunci, isi, keluar.size, os.path.getsize(tujuan)))

    print("topeng dibuat:")
    for kunci, isi, ukuran, byte in dibuat:
        print(f"  {kunci:14} lubang {isi * 100:5.1f}%  {ukuran[0]}x{ukuran[1]}  {byte // 1024} KB")
    print("\ndilewati (tidak butuh topeng):")
    for kunci, sebab in dilewati:
        print(f"  {kunci:14} {sebab}")


if __name__ == "__main__":
    main()
