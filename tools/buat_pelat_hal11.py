"""Bikin pelat halaman 11 (surat penutup) dari PDF kiriman pemilik situs.

SUMBER KEEMPAT template ini. Halaman 1-10 lahir dari LOVESTORY-2.pdf lewat
tools/buat_pelat_valentine.py, halaman 12 dari sebuah PDF lewat
tools/buat_pelat_hal12.py, dan halaman 11 dari PDF ini.

    /tmp/pdfenv/bin/python tools/buat_pelat_hal11.py

Karena itu halaman 11 TETAP terdaftar di TANPA_PELAT pada skrip yang pertama:
kalau dicabut dari sana, skrip itu akan menimpa hasil kerja skrip ini dengan
halaman krem kosong dari PDF-nya.

> Ganti desain, 21 Agu 2026. Sebelumnya halaman ini sebuah kolase JPG —
> merah tua bersequin dengan bibir, bintang perak, dan sobekan koran "love".
> Diganti atas permintaan pemilik situs oleh LOVESTORY-4.pdf: kertas krem
> bergaris tepi putus-putus, anggrek merah di pojok kiri atas, dan satu
> catatan merah tua berselotip tempat suratnya ditulis. Versi kolasenya
> tidak dipakai lagi di mana pun.

Yang dikerjakan skrip ini:

1. Judul "Letter For You" DIHAPUS dari gambarnya. Di kartu ini judul itu
   jadi teks HTML yang bisa disunting pembeli (.t-wish), jadi huruf
   bawaannya tidak boleh ikut tergambar. Dihapus dengan redaksi PyMuPDF yang
   hanya menyentuh objek TEKS — gambar dan vektor di bawahnya dibiarkan
   utuh, dan itu penting: kotak judulnya bertumpang tindih dengan gambar
   anggrek di pojok kiri atas (terukur: judul x 141,6..535,9 pt, anggrek
   x 10,0..203,6 pt). Mengecat ulang kotaknya akan memakan kelopak.

2. Dirender 150 dpi. Halaman PDF-nya 595,5 x 842,25 pt, jadi hasilnya persis
   1241 x 1755 — ukuran yang sama dengan sebelas pelat lain, tanpa perlu
   dipotong maupun diregangkan sedikit pun. Rasionya 0,7070, sama dengan A4
   kanonis template ini (390/551,6). Kebetulan yang menyenangkan, tapi tetap
   DIPERIKSA di bawah, bukan diandaikan.

3. Mengukur ulang angka yang dibutuhkan valentine.css dan mencetaknya:
   warna kertas (--kertas-bg) dan kotak merah bersih terbesar di dalam
   catatan (tempat .t-pesan boleh duduk). Salin angkanya ke CSS kalau
   PDF-nya berganti lagi.
"""
import os

import numpy as np
import pymupdf
from PIL import Image

SUMBER = "/Users/jepa/Downloads/LOVESTORY-4.pdf"
KELUARAN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "static", "img", "valentine", "hal11.webp")

LEBAR, TINGGI = 1241, 1755        # sama dengan sebelas pelat lain (A4 @150dpi)
PT_LEBAR, PT_TINGGI = 595.5, 842.25   # ukuran halaman PDF-nya, dalam poin
DPI = 150
RASIO_A4 = 390 / 551.6

# Warna merah catatan, DIUKUR: median (91,13,27) di seluruh badannya. Jangan
# dikira-kira dari tampilan — garis tepi putus-putus halamannya merah LAIN
# (118,10,10) dan ambang yang longgar akan menganggap keduanya satu benda,
# lalu melaporkan "kotak catatan" selebar halaman.
MERAH_CATATAN = (91, 13, 27)
TOLERANSI = 55                    # jumlah |selisih| per kanal; menampung gradasi halus


def render_tanpa_judul():
    """Halaman PDF tanpa objek teks apa pun, sebagai gambar RGB."""
    dok = pymupdf.open(SUMBER)
    if dok.page_count != 1:
        raise SystemExit(f"PDF ini {dok.page_count} halaman, harusnya 1")
    hal = dok[0]

    teks = [s for b in hal.get_text("dict")["blocks"]
            for l in b.get("lines", []) for s in l["spans"]]
    if not teks:
        raise SystemExit("tidak ada objek teks — apakah judulnya sudah jadi gambar?")
    for s in teks:
        # fill=False: kotaknya TIDAK dicat ulang. Yang dibuang cuma gliflnya;
        # kertas dan anggrek di bawahnya tetap seperti aslinya.
        hal.add_redact_annot(pymupdf.Rect(s["bbox"]), fill=False)
    hal.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                         graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                         text=pymupdf.PDF_REDACT_TEXT_REMOVE)
    if hal.get_text().strip():
        raise SystemExit("masih ada teks tersisa sesudah redaksi")

    pm = hal.get_pixmap(dpi=DPI)
    if (pm.width, pm.height) != (LEBAR, TINGGI):
        raise SystemExit(f"render {pm.width}x{pm.height}, harusnya {LEBAR}x{TINGGI}")
    rasio = pm.width / pm.height
    if abs(rasio - RASIO_A4) > 0.002:
        raise SystemExit(f"rasio {rasio:.4f} jauh dari A4 kartu ({RASIO_A4:.4f})")
    return Image.frombytes("RGB", (pm.width, pm.height), pm.samples), teks


def kotak_bersih(a):
    """Persegi panjang TERBESAR yang seluruhnya merah catatan.

    Dipakai untuk menaruh .t-pesan. Bukan sekadar kotak pembatas catatannya:
    catatan itu digambar sedikit miring dan sudutnya ditimpa selotip serta
    goresan hias, jadi kotak pembatasnya memuat piksel yang bukan merah.
    Yang dicari di sini kotak yang dijamin polos, supaya suratnya tidak
    pernah jatuh di atas selotip.

    Algoritmanya "persegi terbesar di dalam histogram", dijalankan sekali per
    baris: untuk tiap kolom disimpan berapa piksel merah beruntun ke atas,
    lalu dicari persegi terluas di bawah profil itu.
    """
    beda = np.abs(a - np.array(MERAH_CATATAN)).sum(2)
    merah = beda < TOLERANSI
    H, W = merah.shape
    terbaik = (0, None)
    tinggi = np.zeros(W, dtype=int)
    for y in range(H):
        tinggi = np.where(merah[y], tinggi + 1, 0)
        tumpuk = []
        h = np.append(tinggi, 0)
        i = 0
        while i < len(h):
            if not tumpuk or h[i] >= h[tumpuk[-1]]:
                tumpuk.append(i)
                i += 1
            else:
                t = tumpuk.pop()
                lebar = i if not tumpuk else i - tumpuk[-1] - 1
                if h[t] * lebar > terbaik[0]:
                    kanan = i - 1
                    terbaik = (h[t] * lebar,
                               (kanan - lebar + 1, y - h[t] + 1, kanan, y))
    x0, y0, x1, y1 = terbaik[1]
    if not merah[y0:y1 + 1, x0:x1 + 1].all():
        raise SystemExit("kotak yang ditemukan ternyata tidak polos")
    return x0, y0, x1, y1


def main():
    im, teks = render_tanpa_judul()
    a = np.asarray(im).astype(int)
    H, W, _ = a.shape

    im.save(KELUARAN, "WEBP", quality=88, method=6)
    print(f"tulis {KELUARAN}  ({W}x{TINGGI}, {os.path.getsize(KELUARAN)//1024} KB)")

    print("\n── angka untuk valentine.css ──")
    # Kertas: median pita 40 px di keempat tepi, jauh dari catatan & anggrek.
    tepi = np.concatenate([a[6:46, 60:W - 60].reshape(-1, 3),
                           a[H - 46:H - 6, 60:W - 60].reshape(-1, 3)])
    kertas = np.median(tepi, axis=0).astype(int)
    print("  #hal11 --kertas-bg : #%02x%02x%02x" % tuple(kertas))

    x0, y0, x1, y1 = kotak_bersih(a)
    print("  kotak merah polos  : left %.3f%%  top %.3f%%  width %.3f%%  height %.3f%%"
          % (100 * x0 / W, 100 * y0 / H, 100 * (x1 - x0 + 1) / W, 100 * (y1 - y0 + 1) / H))

    for s in teks:
        bb, o = s["bbox"], s["origin"]
        print(f"  judul {s['text']!r}: font {s['font']} {s['size']:.2f}pt "
              f"warna #{s['color']:06x}")
        print("    kotak  left %.3f%%  width %.3f%%   garis alas top %.3f%%"
              % (100 * bb[0] / PT_LEBAR, 100 * (bb[2] - bb[0]) / PT_LEBAR,
                 100 * o[1] / PT_TINGGI))
        print("    ukuran di kanvas kanonis 390px: %.2fpx" % (s["size"] * 390 / 595.5))


if __name__ == "__main__":
    main()
