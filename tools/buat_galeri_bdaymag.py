"""Galeri halaman produk Birthday Magazine dari ekspor JPG Canva pemilik situs.

Template lain dipotret dari kartunya sendiri (tools/buat_galeri_template.js);
yang ini atas permintaan pemilik situs (11 Okt 2026) memakai ekspor desain
Canva DAHTj9DbLAg — sembilan hamparan 2400x1697 — supaya foto contohnya
(sampul, daftar isi) ikut tampil. Dicap VORTEIZ seperti galeri lain.

    python tools/buat_galeri_bdaymag.py <folder-ekspor>   # berisi 01.jpg..09.jpg
"""
import os
import shutil
import sys

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(AKAR, "tools"))
from cap_gambar import beri_cap  # noqa: E402

KELUARAN = os.path.join(AKAR, "static", "img", "galeri", "birthday-magazine")


def main():
    sumber = sys.argv[1]
    os.makedirs(KELUARAN, exist_ok=True)
    for i in range(1, 10):
        tujuan = os.path.join(KELUARAN, f"{i:02d}.jpg")
        shutil.copyfile(os.path.join(sumber, f"{i:02d}.jpg"), tujuan)
        beri_cap(tujuan)
        print(f"tulis {tujuan}  {os.path.getsize(tujuan) // 1024} KB")


if __name__ == "__main__":
    main()
