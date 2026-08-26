"""Thumbnail kisi untuk Valentine Story, dari PDF sampul kiriman pemilik situs.

Satu-satunya thumbnail yang TIDAK dipotret tools/buat_thumb.js. Alasannya
bukan selera: yang dipotret skrip itu adalah kartu dalam keadaan KOSONG, dan
sampul Valentine Story hampir seluruhnya lubang foto — jadi yang tertangkap
cuma gradasi pengisi dengan tulisan di atasnya. Sebagai gambar etalase itu
menjual kartu yang salah: pembeli melihat bidang kosong, bukan majalah.

PDF ini sampul yang sama persis, tapi dengan fotonya terisi — dikirim pemilik
situs 21 Agu 2026 sebagai LOVESTORY-5.pdf.

    /tmp/pdfenv/bin/python tools/buat_thumb_valentine.py

Ukurannya 1000x1333 (3:4), sama dengan dua thumbnail lain, dan itu memang
bentuk slot .tpl-art di app.css. Halaman PDF-nya A4 (0,7070), jadi supaya
menjadi 3:4 ada yang harus dibuang — dan lebih baik dibuang DI SINI, di mana
hasilnya bisa dilihat, daripada diserahkan ke object-fit:cover yang memotong
dari tengah tanpa ada yang pernah memeriksanya. Terukur: 41 px di atas dan 41
px di bawah, dan pada potongan itu "LOVESTORY" maupun "MATCH" masih utuh.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pymupdf
from PIL import Image

SUMBER = "/Users/jepa/Downloads/LOVESTORY-5.pdf"
KELUARAN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "static", "img", "thumb", "valentine-story.jpg")

LEBAR = 1000              # sama dengan game-8bit.jpg dan scrapbook-cerita.jpg
RASIO = 3 / 4             # bentuk slot .tpl-art
MUTU = 86                 # cukup untuk foto, dan berkasnya tetap di bawah 300 KB


def main():
    dok = pymupdf.open(SUMBER)
    if dok.page_count != 1:
        raise SystemExit(f"PDF ini {dok.page_count} halaman, harusnya 1")
    hal = dok[0]

    z = LEBAR / hal.rect.width
    pm = hal.get_pixmap(matrix=pymupdf.Matrix(z, z))
    im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)

    tinggi = round(LEBAR / RASIO)
    if im.height < tinggi:
        raise SystemExit(f"halaman terlalu pendek: {im.height} px, butuh {tinggi}")
    atas = (im.height - tinggi) // 2
    im = im.crop((0, atas, LEBAR, atas + tinggi))

    im.save(KELUARAN, "JPEG", quality=MUTU, optimize=True, progressive=True)

    # Cap VORTEIZ. Thumbnail dua template lain mendapatkannya sendiri karena
    # dipotret dari halaman contoh yang memang sudah bercap; yang ini dirender
    # dari PDF dan tidak pernah melewati browser, jadi capnya dipasang di sini.
    # Kalau langkah ini terlewat, satu-satunya thumbnail tanpa cap justru
    # thumbnail template yang paling laku.
    from cap_gambar import beri_cap  # noqa: PLC0415 - alat sekali pakai
    beri_cap(KELUARAN)
    print(f"tulis {KELUARAN}")
    print(f"  {im.width}x{im.height}  rasio {im.width / im.height:.4f}"
          f"  {os.path.getsize(KELUARAN) // 1024} KB")
    print(f"  dipotong {atas} px atas + {pm.height - tinggi - atas} px bawah")


if __name__ == "__main__":
    main()
