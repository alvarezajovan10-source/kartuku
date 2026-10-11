"""Thumbnail kisi untuk Birthday Magazine, dari sampul berfoto kiriman
pemilik situs (11 Okt 2026). Polanya sama dengan buat_thumb_valentine.py:
sampul kartu KOSONG cuma gradasi pengisi, jadi etalasenya memakai sampul yang
fotonya terisi.

    python tools/buat_thumb_bdaymag.py      # perlu Pillow

Sumber 888x1264 (A4) -> lebar 1000 = tinggi 1423; slot .tpl-art 3:4 = 1333,
jadi 90 px harus dibuang. Terukur: tinta putih teratas (masthead BIRTHDAY) di
y=52 dan tepi bawah stiker barcode di y=1392 — isinya 1340 px, tujuh lebih
tinggi dari slotnya. Dipotong mulai y=50: masthead utuh, yang hilang cuma
9 px tepi bawah stiker barcode (di bawah angkanya).

Sumbernya (tools/bdaymag/asli/sampul_galeri.png) TIDAK di-commit, sama seperti
ekspor Canva lain di folder itu.
"""
import os
import sys

from PIL import Image

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(AKAR, "tools"))
SUMBER = os.path.join(AKAR, "tools", "bdaymag", "asli", "sampul_galeri.png")
KELUARAN = os.path.join(AKAR, "static", "img", "thumb", "birthday-magazine.jpg")

LEBAR = 1000
TINGGI = 1333          # 3:4, bentuk slot .tpl-art
ATAS = 50
MUTU = 86


def main():
    im = Image.open(SUMBER).convert("RGB")
    im = im.resize((LEBAR, round(im.height * LEBAR / im.width)), Image.LANCZOS)
    if im.height < ATAS + TINGGI:
        raise SystemExit(f"sumber terlalu pendek: {im.height} px")
    im = im.crop((0, ATAS, LEBAR, ATAS + TINGGI))
    im.save(KELUARAN, "JPEG", quality=MUTU, optimize=True, progressive=True)
    from cap_gambar import beri_cap  # noqa: PLC0415 - alat sekali pakai
    beri_cap(KELUARAN)
    print(f"tulis {KELUARAN}  {im.width}x{im.height}  {os.path.getsize(KELUARAN) // 1024} KB")


if __name__ == "__main__":
    main()
