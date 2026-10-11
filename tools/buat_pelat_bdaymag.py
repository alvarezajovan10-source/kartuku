"""Bongkar ekspor PDF Canva "magazine template 1" jadi pelat Birthday Magazine.

JALANKAN ULANG kalau desain Canva-nya berubah. Butuh PyMuPDF + Pillow +
numpy, yang SENGAJA bukan dependensi situs — ini alat sekali pakai:

    uv venv /tmp/pdfenv && uv pip install --python /tmp/pdfenv/bin/python pymupdf pillow numpy
    /tmp/pdfenv/bin/python tools/buat_pelat_bdaymag.py

Bahan (dua-duanya ekspor dari desain yang sama, tanpa mengubah desainnya):
  tools/bdaymag/asli/majalah.pdf     — ekspor PDF Canva
  tools/bdaymag/canva_struktur.json  — read-design: posisi & id tiap elemen

Hasilnya static/img/bdaymag/sNk.webp & sNn.webp (hamparan N, kiri/kanan):
seluruh karya Canva apa adanya, dengan dua perubahan —

  1. Teks yang bisa disunting pembeli (spek.TEKS + spek.PENGIRIM) dihapus.
     Teks lain SENGAJA dibiarkan, jadi judul rubrik tetap memakai font
     Canva aslinya.
  2. Area foto dilubangi jadi transparan. Foto pembeli dipasang DI BELAKANG
     pelat, jadi benda yang di desain aslinya ada di atas foto — pin,
     bingkai polaroid, bunga lili, bingkai cermin, pemutar musik — tetap di
     atasnya.

Bentuk lubangnya TIDAK ditebak (cara yang sama dengan buat_pelat_valentine.py):
setiap foto diganti putih rata sekali dan hitam rata sekali, lalu selisih
kedua render itu adalah tutupan foto di tiap piksel. Hiasan yang di desainnya
ada DI BAWAH foto (jalan berkelok halaman 5, kartu abu-abu halaman 9) tertutup
foto di kedua render, jadi ikut terlubangi — memang itu yang benar, karena di
desain aslinya pun tidak terlihat.

Foto dikenali dari ciri yang bertahan lintas ekspor: gambar TANPA SMask
(kanal alfa). Semua hiasan Canva berlatar transparan, jadi punya SMask;
foto dan gambar pengisi "langit & bukit" tidak. Jangan pakai nomor xref —
Canva menomori ulang tiap ekspor (lihat buat_pelat_valentine.py).

Pengecualian: tiga polaroid bertumpuk di halaman 8 adalah satu grup gambar
dengan langit pengisi yang sudah DIBAKAR di dalamnya (berSMask), jadi tidak
terlubangi. Fotonya dipasang DI ATAS pelat — lihat spek.FOTO "polaroid".
"""
import json
import os
import sys

import numpy as np
import pymupdf
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "bdaymag"))
import spek  # noqa: E402

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAHAN = os.path.join(AKAR, "tools", "bdaymag")
PDF = os.path.join(BAHAN, "asli", "majalah.pdf")
KELUARAN = os.path.join(AKAR, "static", "img", "bdaymag")

PX_KE_PT = 0.75   # Canva px -> PDF pt (1587 px = 1190,25 pt)
ZOOM = 2.0        # 2380 px per hamparan, 1190 px per halaman — pas untuk HP 3x
MUTU = 84


def muat_struktur():
    with open(os.path.join(BAHAN, "canva_struktur.json")) as f:
        d = json.load(f)
    return d.get("design_content", d)["pages"]


def kotak_teks_sunting(halaman):
    """Kotak (pt) tiap elemen teks yang harus dicabut dari pelat."""
    dicabut = {i for i, *_ in spek.TEKS} | {spek.PENGIRIM}
    kotak = []
    for e in halaman["elements"]:
        if e["type"] == "text" and e["id"] in dicabut:
            x0, y0 = e["left"] * PX_KE_PT, e["top"] * PX_KE_PT
            kotak.append((e["id"], pymupdf.Rect(x0, y0, x0 + e["width"] * PX_KE_PT,
                                                y0 + e["height"] * PX_KE_PT)))
    return kotak


def cabut_teks(page, kotak):
    """Redaksi span teks yang TITIK TENGAHNYA ada di kotak elemen sunting.

    Titik tengah, bukan persinggungan kotak: kotak span yang bersentuhan
    dengan kotak tetangga akan ikut membunuh teks tetangga yang harus tetap
    tinggal (jebakan yang sudah dibayar mahal di Valentine Story). Kotak
    redaksinya juga dikecilkan ke tinta span itu sendiri.
    """
    dicabut, tinggal = 0, []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                if not s["text"].strip():
                    continue
                r = pymupdf.Rect(s["bbox"])
                tengah = pymupdf.Point((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)
                if any(k.contains(tengah) for _, k in kotak):
                    tinggi = r.height
                    page.add_redact_annot(pymupdf.Rect(r.x0, r.y0 + tinggi * .2,
                                                       r.x1, r.y1 - tinggi * .2))
                    dicabut += 1
                else:
                    tinggal.append(s["text"].strip())
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                          graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                          text=pymupdf.PDF_REDACT_TEXT_REMOVE)
    return dicabut, tinggal


def xref_foto(doc, page):
    hasil = set()
    for inf in page.get_image_info(xrefs=True):
        x = inf["xref"]
        if x and doc.xref_get_key(x, "SMask")[1] in ("null", ""):
            hasil.add(x)
    return hasil


def render(warna, cabut=True):
    """Render semua halaman dengan foto diganti `warna` (dan teks sunting dicabut)."""
    halaman = muat_struktur()
    doc = pymupdf.open(PDF)
    hasil, laporan = [], []
    for n, page in enumerate(doc, 1):
        if cabut:
            dicabut, tinggal = cabut_teks(page, kotak_teks_sunting(halaman[n - 1]))
            laporan.append((n, dicabut, tinggal))
        pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 8, 8), False)
        pix.set_rect(pix.irect, warna)
        for x in xref_foto(doc, page):
            page.replace_image(x, pixmap=pix)
        p = page.get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM), alpha=False)
        hasil.append(np.frombuffer(p.samples, np.uint8).reshape(p.h, p.w, 3).astype(np.float32))
    return hasil, laporan


def selamatkan_teks_tetap(hasil, utuh):
    """Kembalikan tinta teks TETAP yang ikut terhapus oleh redaksi tetangganya.

    Redaksi PDF membuang setiap huruf yang kotaknya bersinggungan dengan
    kotak redaksi — dan kotak huruf besar jauh lebih tinggi daripada
    tintanya. Terbukti di hamparan 8: angka "10" kehilangan "1"-nya karena
    kotak hurufnya menjulur ke paragraf JEWELRY yang dicabut. Piksel yang
    berbeda antara render utuh dan render teredaksi, di dalam kotak teks
    tetap tapi DI LUAR kotak teks sunting mana pun, ditempel balik. Batas
    kotak itu wajib: tanpa itu, teks sunting di sebelahnya ikut hidup lagi.
    """
    dicabut = {i for i, *_ in spek.TEKS} | {spek.PENGIRIM}
    s = PX_KE_PT * ZOOM
    for n, halaman in enumerate(muat_struktur()):
        a, b = hasil[n], utuh[n]
        beda = np.abs(a - b).max(axis=2) > 8
        boleh = np.zeros(beda.shape, bool)
        for e in halaman["elements"]:
            if e["type"] != "text":
                continue
            x0, y0 = int(e["left"] * s), int(e["top"] * s)
            x1, y1 = int((e["left"] + e["width"]) * s) + 1, int((e["top"] + e["height"]) * s) + 1
            x0, y0 = max(x0, 0), max(y0, 0)
            if e["id"] not in dicabut:
                boleh[y0:y1, x0:x1] = True
        for e in halaman["elements"]:
            if e["type"] == "text" and e["id"] in dicabut:
                x0, y0 = max(int(e["left"] * s), 0), max(int(e["top"] * s), 0)
                boleh[y0:int((e["top"] + e["height"]) * s) + 1, x0:int((e["left"] + e["width"]) * s) + 1] = False
        pulih = beda & boleh
        if pulih.any():
            a[pulih] = b[pulih]
            print(f"hamparan {n + 1}: {int(pulih.sum())} piksel teks tetap dipulihkan")


def main():
    os.makedirs(KELUARAN, exist_ok=True)
    putih, laporan = render((255, 255, 255))
    hitam, _ = render((0, 0, 0))
    selamatkan_teks_tetap(putih, render((255, 255, 255), cabut=False)[0])
    selamatkan_teks_tetap(hitam, render((0, 0, 0), cabut=False)[0])

    for n, dicabut, tinggal in laporan:
        print(f"hamparan {n}: {dicabut} span dicabut; tetap di pelat: {' | '.join(tinggal)[:150]}")

    for n, (a, b) in enumerate(zip(putih, hitam), 1):
        tutup = np.clip((a - b).mean(axis=2) / 255.0, 0, 1)      # tutupan foto
        alfa = 1.0 - tutup
        # Kembalikan warna asli hiasan yang menumpang di atas foto (tepi
        # bunga, bayangan polaroid): render hitam = hiasan x alfa.
        aman = np.maximum(alfa, 1e-3)[..., None]
        warna = np.clip(b / aman, 0, 255)
        rgba = np.dstack([warna, alfa[..., None] * 255]).round().astype(np.uint8)
        gambar = Image.fromarray(rgba, "RGBA")
        lebar = gambar.width // 2
        for sisi, kotak in (("k", (0, 0, lebar, gambar.height)),
                            ("n", (gambar.width - lebar, 0, gambar.width, gambar.height))):
            jalur = os.path.join(KELUARAN, f"s{n}{sisi}.webp")
            gambar.crop(kotak).save(jalur, "WEBP", quality=MUTU, alpha_quality=90, method=6)
            print(f"  {os.path.relpath(jalur, AKAR)}  {os.path.getsize(jalur) // 1024} KB")


if __name__ == "__main__":
    main()
