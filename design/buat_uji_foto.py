"""Bikin coquette-uji.html: salinan coquette.html dengan semua slot terisi foto asli.

Slot yang kosong menyembunyikan dua bug sekaligus — overlay pastel yang menimpa
foto, dan lightbox yang tidak pernah mengganti gambar. Keduanya cuma kelihatan
kalau ada foto sungguhan di dalamnya.

Jalankan:  python3 design/buat_uji_foto.py
Lalu buka: design/coquette-uji.html
"""

import json
import re
from pathlib import Path

DESIGN = Path(__file__).parent
FOTO_DIR = DESIGN.parent / "media" / "cards" / "2026" / "07"

CAPTIONS = ["awal kita", "ketawa mulu", "jam 2 pagi",
            "hari biasa", "yang kamu benci", "favoritku"]


def main():
    fotos = sorted(p.name for p in FOTO_DIR.glob("*.jpg"))
    if not fotos:
        raise SystemExit(f"Tidak ada foto di {FOTO_DIR}")

    rel = [f"../media/cards/2026/07/{n}" for n in fotos]
    html = (DESIGN / "coquette.html").read_text(encoding="utf-8")

    # 1. Slot statis: ganti placeholder <span>foto</span> dengan foto asli,
    #    berputar kalau fotonya kurang dari jumlah slotnya.
    urutan = iter(range(1000))

    def isi(m):
        src = rel[next(urutan) % len(rel)]
        return f'{m.group(1)}<img src="{src}" alt="">'

    html, n_slot = re.subn(
        r'(<div class="slot"[^>]*>)<span>foto</span>', isi, html)

    # 2. Slot hero di penutup punya teks ajakan sendiri.
    html, n_hero = re.subn(
        r'(<div class="slot">)<span><i>♡</i>foto pasangan kamu<br>di sini</span>',
        lambda m: f'{m.group(1)}<img src="{rel[0]}" alt="">', html)

    # 3. Polaroid dibangun dari JS, jadi datanya yang diisi.
    photos = [{"src": rel[i % len(rel)], "cap": c} for i, c in enumerate(CAPTIONS)]
    baru = "const PHOTOS=" + json.dumps(photos, ensure_ascii=False) + ";"
    html, n_js = re.subn(
        r"const PHOTOS=\[.*?\];", baru, html, flags=re.S)

    keluar = DESIGN / "coquette-uji.html"
    keluar.write_text(html, encoding="utf-8")

    print(f"{len(fotos)} foto tersedia")
    print(f"  slot statis terisi : {n_slot}")
    print(f"  slot hero terisi   : {n_hero}")
    print(f"  daftar polaroid    : {n_js} blok, {len(photos)} foto")
    print(f"\nDitulis: {keluar}")


if __name__ == "__main__":
    main()
