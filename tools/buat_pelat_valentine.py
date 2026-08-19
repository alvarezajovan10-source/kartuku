"""Bongkar LOVESTORY.pdf jadi bahan template Valentine Story.

JALANKAN ULANG kalau desain Canva-nya berubah. Butuh PyMuPDF + Pillow, yang
SENGAJA bukan dependensi situs — ini alat sekali pakai, bukan bagian dari
yang berjalan di server:

    uv venv /tmp/pdfenv && uv pip install --python /tmp/pdfenv/bin/python pymupdf pillow
    /tmp/pdfenv/bin/python tools/buat_pelat_valentine.py

Sesudahnya, koordinat lubang fotonya berubah: salin angka slots.json ke
style --kiri/--atas/--lebar/--tinggi di valentine.html, lalu jalankan
tools/cek_valentine.js untuk mengukur ulang --cf tiap teks.

Menghasilkan, per halaman:
  * hal01.webp .. hal10.webp — SELURUH karya Canva apa adanya, dengan dua
    perubahan: teks yang nanti bisa disunting pembeli dihapus, dan area foto
    dilubangi jadi transparan.
  * slots.json — letak tiap lubang foto (persen terhadap halaman) dan warna
    dasar halaman.

Kenapa dilubangi, bukan foto ditempel di atas pelat: di beberapa halaman ada
benda yang digambar DI ATAS foto — pita halaman 8, logam liontin halaman 7,
coretan merah halaman 4, penjepit halaman 6. Kalau foto ditaruh di atas
pelat, benda-benda itu tertutup. Dengan dilubangi, urutan aslinya terjaga:
foto di belakang, sisanya tetap di depan.

Bentuk lubangnya TIDAK ditebak. Halaman dirender dua kali — gambar pengisi
Canva diganti putih rata sekali, hitam rata sekali — dan selisih kedua render
itu adalah nilai alfa foto di tiap piksel, persis sampai ke tepi melengkung
hati di liontin.
"""
import json
import os
from collections import deque

import pymupdf
from PIL import Image, ImageChops

SRC = "/Users/jepa/Downloads/LOVESTORY-2.pdf"
KELUARAN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "static", "img", "valentine")
DPI = 150                      # 1240 px lebar — pas untuk HP 3x dan laptop
ABAIKAN_KECIL = 0.0006         # komponen < 0,06% halaman = derau, bukan foto

# ── Gambar mana yang jadi lubang foto ────────────────────────────────────
#
# JANGAN kembali ke daftar nomor xref. Versi pertama berkas ini menghafal
# {1: [289], 4: [323], ...} dan itu SALAH DIAM-DIAM: Canva memberi nomor
# xref baru tiap kali file diekspor ulang. Terbukti saat LOVESTORY-2.pdf
# datang — foto sampul yang sama persis (md5 identik, posisi identik)
# berpindah dari xref 289 ke 319. Nomor lama tetap ada di PDF-nya, jadi
# skripnya tidak error; ia cuma melubangi gambar yang keliru, dan yang
# menemukan adalah pembeli.
#
# Dua cara mengenali, keduanya bertahan lintas ekspor:
PENGISI_UKURAN = (1438, 560)   # gambar pengisi bawaan Canva ("langit & bukit")
PENGISI_SATU_SATUNYA = {1}     # sampul: satu-satunya gambar di halaman = fotonya

# Halaman 2 dan 6 memakai kotak vektor, bukan gambar, jadi tidak bisa
# diprobe dengan cara yang sama — dilubangi langsung dari koordinatnya.
# Kotak halaman 6 miring mengikuti polaroidnya; sudut kanan atasnya
# disisakan karena penjepit kertas menutupi bagian itu di desain aslinya.
KOTAK_VEKTOR = {
    2: [(334.8, 156.1, 470.8, 311.0),
        (334.8, 327.4, 470.8, 482.3),
        (334.8, 498.7, 470.8, 653.6)],
    6: [(179.1, 346.7, 392.1, 551.1)],
}
LUBANG_DIKECUALIKAN = {6: [(374.0, 330.0, 402.0, 392.0)]}   # penjepit kertas

# Halaman yang SELURUH isinya foto pembeli: tidak ada karya Canva sedikit pun
# di atasnya, jadi tidak ada pelat yang perlu dibuat — cukup warna dasar
# halaman untuk keadaan sebelum fotonya dipasang. Halaman 11 (penutup) dibuat
# begitu atas permintaan pemilik situs: sama seperti sampul, tapi tanpa teks
# dan tanpa elemen apa pun.
TANPA_PELAT = {11}

# Halaman yang lubangnya SATU foto walau terpecah beberapa gugus. Coretan
# merah halaman 4 melintasi fotonya, jadi lubangnya terbelah tiga; tanpa
# ini, satu bingkai foto terbaca sebagai tiga.
GABUNG = {4}

# Halaman yang hiasannya digambar DI ATAS teks. Di halaman 4 tangkai bunga
# merah melintasi paragraf; kalau teks HTML ditaruh di atas pelat, bunganya
# pindah ke belakang huruf dan susunannya berubah. Latarnya warna rata, jadi
# hiasannya bisa dipisah dengan membuang warna itu — hasilnya dipasang lagi
# sebagai lapisan paling atas.
ATAS_DIKUNCI = {4: (255, 250, 241)}
TOLERANSI_KUNCI = 12

# Hiasan yang dicabut dari pelat karena akan digambar ulang sebagai elemen
# HTML yang bisa berpindah. Sejauh ini cuma satu: hati yang melingkari
# tanggal di kalender halaman 5 — pembeli harus bisa memindahkannya ke
# tanggal mereka sendiri.
#
# Menimpa kotaknya begitu saja tidak bisa: hati itu MELINGKARI angka "13",
# jadi angkanya ikut terhapus. Yang dilakukan di sini: halaman dirender
# sekali lagi dengan SELURUH teksnya diredaksi, sehingga di dalam kotak itu
# satu-satunya yang bukan warna latar adalah garis hatinya. Piksel itulah
# yang ditimpa balik dengan warna latar di pelat final — angka kalendernya
# tidak pernah ikut tersentuh.
CABUT_HIASAN = {
    5: {"kotak": (414.0, 451.0, 513.0, 558.0), "latar": (117, 9, 9)},
}

# Teks yang dihapus dari pelat karena akan digambar ulang sebagai HTML yang
# bisa disunting. Angka kalender halaman 5 sengaja DIBIARKAN menyatu dengan
# pelat: ia hiasan, dan dibiarkan begitu hurufnya tetap persis font Canva
# aslinya.
#
# Halaman 3 (daftar isi) SEBAGIAN. Sampai 18 Agu 2026 ia dibiarkan utuh
# seperti angka kalender, lalu pemilik situs meminta isinya bisa disunting
# pembeli. Yang diredaksi cuma kelima baris daftarnya (indeks 1..15, tiga
# span per baris: label, garis titik-titik, nomor halaman); judul "Contents"
# di indeks 0 TETAP menyatu dengan gambar karena fontnya Brightwall 102pt —
# font Canva berbayar yang tidak punya padanan bebas, dan satu-satunya di
# halaman ini.
#
# Ketiga span satu baris harus ikut semuanya, tidak bisa cuma labelnya:
# garis titik-titiknya dimulai persis di tempat label bawaan berakhir, jadi
# label pembeli yang lebih pendek meninggalkan celah dan yang lebih panjang
# menabraknya. Di HTML garis itu digambar ulang sebagai batas yang memuai
# sendiri (.pimpin di valentine.css).
#
# Baris kelima ("MUSIC ____ 11-12") diredaksi dan TIDAK ditulis ulang:
# majalahnya cuma sebelas halaman, jadi halaman 11-12 yang ditunjuknya tidak
# pernah ada. Ini permintaan pemilik situs 18 Agu 2026.
TEKS_DIHAPUS = {1: "semua", 2: "semua", 4: "semua", 6: "semua", 7: "semua",
                5: [0], 3: list(range(1, 16))}

# Span yang harus TETAP ADA di pelat walau redaksi di atas ikut membunuhnya.
#
# apply_redactions membuang setiap span yang KOTAKNYA bersinggungan dengan
# kotak redaksi, bukan yang tintanya bertumpuk. Judul "Contents" di halaman 3
# berkotak (122,135)-(472,395) — kotak itu menjulur jauh ke bawah mengikuti
# ekor sapuan huruf C-nya, sampai bersinggungan dengan baris pertama daftar
# yang kotaknya mulai di y=355. Akibatnya meredaksi baris pertama ikut
# menghapus judulnya, TANPA error apa pun: yang keluar cuma halaman tanpa
# judul. Terbukti dengan menjalankan redaksi baris MUSIC saja (judul selamat)
# lalu baris pertama saja (judul hilang).
#
# Tintanya sendiri TIDAK pernah bertumpuk. Jadi judulnya dikembalikan apa
# adanya: halaman dirender dua kali lagi, sekali utuh dan sekali dengan HANYA
# span ini yang diredaksi, dan piksel yang berbeda di antara keduanya
# ditempel balik ke pelat final — sampai ke antialiasnya.
#
# "kotak" WAJIB ada, dan ini pelajaran yang didapat dengan cara mahal:
# tabrakan kotak itu BERLAKU DUA ARAH. Meredaksi span judul juga membunuh
# baris pertama daftar, jadi selisih kedua render itu berisi tinta judul
# DITAMBAH tinta baris pertama — dan menempelkannya bulat-bulat mengembalikan
# baris yang baru saja susah payah dicabut. Gejalanya halus: yang muncul
# kembali cuma potongannya ("HE DAY WE MET___ 4"), karena sebagian hurufnya
# ikut terhapus dari dua arah.
#
# Batasnya bukan tebakan. Profil baris tinta selisih itu diukur: tinta judul
# menempati 170,4..340,3 pt, tinta baris pertama mulai 368,6 pt, dan di
# antaranya ada 60 px kosong bersih. Garis potong ditaruh di tengah jeda itu.
SELAMATKAN_TEKS = {
    3: {"span": [0], "kotak": (0.0, 0.0, 595.5, 354.0)},
}

# Gambar VEKTOR yang dicabut dari pelat.
#
# Kelima bulatan daftar isi halaman 3 bukan teks melainkan vektor, jadi
# redaksi teks tidak menyentuhnya sama sekali. Setelah baris MUSIC dicabut,
# bulatan kelimanya tertinggal sendirian tanpa baris.
#
# WAJIB memakai LINE_ART_REMOVE_IF_COVERED, bukan REMOVE_IF_TOUCHED: kotak
# sekecil apa pun di halaman ini juga bersinggungan dengan DUA persegi latar
# sehalaman penuh — (0,0,595.5,842.2) putih dan (0,0,595.7,842.6) krem — dan
# IF_TOUCHED akan mencabut keduanya, mengosongkan seluruh latar halaman.
# Sudah diuji: dengan IF_COVERED, 43 vektor jadi 42, kedua persegi latar
# selamat, dan yang hilang tepat bulatan kelima.
CABUT_VEKTOR = {3: [(58.0, 558.0, 71.0, 571.0)]}


def polos(doc, xref, nilai):
    """Ubah XObject gambar jadi 4x4 piksel warna rata tanpa filter.

    JPEG aslinya memakai /ColorTransform 0, jadi menulis JPEG baru ke situ
    membuat warnanya dibaca salah. Raw RGB tanpa filter tidak punya
    ambiguitas itu.
    """
    doc.update_stream(xref, bytes([nilai]) * (4 * 4 * 3), compress=False)
    for k, v in (("Filter", "null"), ("ColorTransform", "null"),
                 ("DecodeParms", "null"), ("ColorSpace", "/DeviceRGB"),
                 ("Width", "4"), ("Height", "4"), ("BitsPerComponent", "8")):
        doc.xref_set_key(xref, k, v)


def hapus_teks(page, mana):
    spans = []
    for blk in page.get_text("dict")["blocks"]:
        if blk["type"] != 0:
            continue
        for line in blk["lines"]:
            spans += [s for s in line["spans"] if s["text"].strip()]
    pilih = spans if mana == "semua" else [spans[i] for i in mana]
    for s in pilih:
        # Tanpa fill: teksnya dibuang, latarnya tidak dicat apa pun.
        page.add_redact_annot(pymupdf.Rect(s["bbox"]))
    if pilih:
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                              graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                              text=pymupdf.PDF_REDACT_TEXT_REMOVE)


def cari_pengisi(doc, pno):
    """Nomor xref gambar yang jadi lubang foto di halaman ini.

    Dihitung ulang tiap kali dijalankan — lihat catatan panjang di
    PENGISI_UKURAN soal kenapa nomornya tidak boleh dihafal.
    """
    gambar = doc[pno].get_images(full=True)
    if (pno + 1) in PENGISI_SATU_SATUNYA:
        if len(gambar) != 1:
            raise SystemExit(
                f"hal {pno + 1}: diharapkan tepat satu gambar (fotonya), "
                f"ketemu {len(gambar)}. Desainnya berubah — periksa dulu."
            )
        return [gambar[0][0]]
    # urut & unik: satu gambar pengisi bisa dipasang berkali-kali di satu
    # halaman (tiga bingkai halaman 8 memakai xref yang sama).
    return sorted({g[0] for g in gambar if (g[2], g[3]) == PENGISI_UKURAN})


_BAWAAN = object()   # penanda: pakai TEKS_DIHAPUS halaman ini


def render(pno, nilai_pengisi=None, semua_teks=False, teks=_BAWAAN):
    """`teks` menimpa TEKS_DIHAPUS halaman ini — dipakai pulihkan_teks()
    untuk merender halaman yang sama dengan redaksi yang berbeda."""
    doc = pymupdf.open(SRC)
    page = doc[pno]
    if teks is _BAWAAN:
        mana = "semua" if semua_teks else TEKS_DIHAPUS.get(pno + 1)
    else:
        mana = teks
    if mana:
        hapus_teks(page, mana)
    kotak_vektor = CABUT_VEKTOR.get(pno + 1)
    if kotak_vektor:
        for r in kotak_vektor:
            page.add_redact_annot(pymupdf.Rect(*r))
        page.apply_redactions(
            images=pymupdf.PDF_REDACT_IMAGE_NONE,
            graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
            text=pymupdf.PDF_REDACT_TEXT_NONE,
        )
    if nilai_pengisi is not None:
        for xref in cari_pengisi(doc, pno):
            polos(doc, xref, nilai_pengisi)
    pix = page.get_pixmap(dpi=DPI)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    return img


def pulihkan_teks(pelat, hal):
    """Tempel balik tinta span yang ikut terhapus sebagai efek samping.

    Lihat catatan panjang di SELAMATKAN_TEKS soal kenapa ini perlu.
    """
    spek = SELAMATKAN_TEKS[hal]
    penuh = render(hal - 1, teks=None)          # tak satu pun span diredaksi
    tanpa = render(hal - 1, teks=spek["span"])  # HANYA span ini yang diredaksi
    beda = ImageChops.difference(penuh, tanpa).convert("L")
    mask = beda.point(lambda v: 255 if v > 8 else 0)

    # Dibatasi ke kotaknya — tanpa ini, tinta yang ikut mati dari arah
    # sebaliknya ikut terpulihkan. Lihat catatan di SELAMATKAN_TEKS.
    skala = pelat.width / 595.5
    batas = Image.new("L", pelat.size, 0)
    from PIL import ImageDraw
    ImageDraw.Draw(batas).rectangle(
        [round(v * skala) for v in spek["kotak"]], fill=255)
    mask = ImageChops.darker(mask, batas)

    pelat.paste(penuh, mask=mask)
    n = sum(mask.point(lambda v: 1 if v else 0).getdata())
    print(f"        - teks diselamatkan hal {hal}: {n} piksel")
    return pelat


def komponen(mask, minimum):
    """Kotak pembatas tiap gugus piksel yang menyambung.

    Dipakai untuk memisahkan lubang yang berbagi satu gambar pengisi —
    tiga bingkai halaman 8 dan empat bingkai halaman 9 semuanya berasal dari
    xref yang sama, jadi tidak bisa dipisah dari data PDF-nya saja.
    """
    kecil = mask.resize((mask.width // 4, mask.height // 4), Image.BILINEAR)
    W, H = kecil.size
    px = kecil.load()
    sudah = bytearray(W * H)
    hasil = []
    for y0 in range(H):
        for x0 in range(W):
            if sudah[y0 * W + x0] or px[x0, y0] < 128:
                continue
            antre, n = deque([(x0, y0)]), 0
            sudah[y0 * W + x0] = 1
            x1 = x2 = x0
            y1 = y2 = y0
            while antre:
                x, y = antre.popleft()
                n += 1
                x1, x2, y1, y2 = min(x1, x), max(x2, x), min(y1, y), max(y2, y)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b = x + dx, y + dy
                    if 0 <= a < W and 0 <= b < H and not sudah[b * W + a] \
                            and px[a, b] >= 128:
                        sudah[b * W + a] = 1
                        antre.append((a, b))
            if n >= minimum * W * H:
                hasil.append((x1 * 4, y1 * 4, (x2 + 1) * 4, (y2 + 1) * 4))
    # Urutan baca: atas ke bawah, lalu kiri ke kanan.
    hasil.sort(key=lambda r: (round(r[1] / (mask.height * 0.06)), r[0]))
    return hasil


def cabut_hiasan(pelat, hal, skala):
    """Timpa hiasan yang akan digambar ulang sebagai HTML dengan warna latar.

    Lihat catatan panjang di CABUT_HIASAN soal kenapa tidak bisa sekadar
    menimpa kotaknya.
    """
    spek = CABUT_HIASAN[hal]
    x0, y0, x1, y1 = [round(v * skala) for v in spek["kotak"]]
    latar = spek["latar"]
    bersih = render(hal - 1, semua_teks=True).crop((x0, y0, x1, y1)).load()
    px = pelat.load()
    n = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b = bersih[x - x0, y - y0]
            if (abs(r - latar[0]) + abs(g - latar[1]) + abs(b - latar[2])) > 24:
                px[x, y] = latar
                n += 1
    print(f"        - hiasan hal {hal} dicabut: {n} piksel")
    return pelat


def koordinat_kalender():
    """Titik tengah tiap angka 1..31 di halaman 5, dalam persen halaman.

    Dipakai menempatkan hati yang bisa dipindah. Diambil per KARAKTER dari
    PDF-nya, bukan per baris teks — di PDF angka-angka itu tersimpan sebagai
    satu deretan panjang ("8         9         10        11"), jadi posisi
    tiap angkanya harus dipisah sendiri.
    """
    doc = pymupdf.open(SRC)
    W, H = doc[0].rect.width, doc[0].rect.height
    hasil = {}
    for blk in doc[4].get_text("rawdict")["blocks"]:
        if blk["type"]:
            continue
        for line in blk["lines"]:
            for sp in line["spans"]:
                if sp["size"] > 50:      # lewati nama bulan
                    continue
                buf, kotak = "", None
                for ch in list(sp["chars"]) + [{"c": " ", "bbox": None}]:
                    if ch["c"].isdigit():
                        buf += ch["c"]
                        b = ch["bbox"]
                        kotak = b if kotak is None else (
                            min(kotak[0], b[0]), min(kotak[1], b[1]),
                            max(kotak[2], b[2]), max(kotak[3], b[3]))
                    else:
                        if buf:
                            hasil[int(buf)] = (
                                round((kotak[0] + kotak[2]) / 2 / W * 100, 3),
                                round((kotak[1] + kotak[3]) / 2 / H * 100, 3),
                            )
                        buf, kotak = "", None
    doc.close()
    return hasil


def main():
    os.makedirs(KELUARAN, exist_ok=True)
    doc = pymupdf.open(SRC)
    lebar_pt, tinggi_pt = doc[0].rect.width, doc[0].rect.height
    n_hal = doc.page_count
    pengisi = {p + 1: cari_pengisi(doc, p) for p in range(n_hal)}
    doc.close()
    print("gambar pengisi terdeteksi:",
          {h: x for h, x in pengisi.items() if x}, "\n")

    ringkas = {"halaman": [], "lebar_pt": lebar_pt, "tinggi_pt": tinggi_pt}

    for pno in range(n_hal):
        hal = pno + 1
        pelat = render(pno)
        W, H = pelat.size
        skala = W / lebar_pt

        # Halaman yang seluruhnya foto: tidak ada pelat, lubangnya sehalaman
        # penuh. Warna dasarnya tetap dicatat — itu yang terlihat di editor
        # selama fotonya belum dipasang.
        if hal in TANPA_PELAT:
            dasar = pelat.getpixel((4, 4))
            ringkas["halaman"].append({
                "hal": hal, "dasar": "#%02x%02x%02x" % dasar, "tanpa_pelat": True,
                "slot": [{"kiri": 0.0, "atas": 0.0, "lebar": 100.0, "tinggi": 100.0}],
            })
            print(f"hal {hal:2d}  {W}x{H}  (tanpa pelat)  slot=1 sehalaman  "
                  f"dasar={dasar}")
            continue

        mask = Image.new("L", (W, H), 0)
        if pengisi[hal]:
            putih, hitam = render(pno, 255), render(pno, 0)
            # Piksel yang berubah dari putih ke hitam = piksel yang
            # digambar oleh gambar pengisi. Besar perubahannya = alfanya.
            beda = Image.new("L", (W, H))
            bp, bh, bd = putih.load(), hitam.load(), beda.load()
            for y in range(H):
                for x in range(W):
                    p, h = bp[x, y], bh[x, y]
                    bd[x, y] = max(p[0] - h[0], p[1] - h[1], p[2] - h[2])
            mask = beda

        if hal in KOTAK_VEKTOR:
            from PIL import ImageDraw
            d = ImageDraw.Draw(mask)
            for r in KOTAK_VEKTOR[hal]:
                d.rectangle([v * skala for v in r], fill=255)
            for r in LUBANG_DIKECUALIKAN.get(hal, []):
                d.rectangle([v * skala for v in r], fill=0)

        kotak = komponen(mask, ABAIKAN_KECIL) if mask.getbbox() else []
        if hal in GABUNG and len(kotak) > 1:
            kotak = [(min(r[0] for r in kotak), min(r[1] for r in kotak),
                      max(r[2] for r in kotak), max(r[3] for r in kotak))]

        if hal in CABUT_HIASAN:
            pelat = cabut_hiasan(pelat, hal, skala)
        if hal in SELAMATKAN_TEKS:
            pelat = pulihkan_teks(pelat, hal)

        # Pelat = karya asli, dengan alfa = 1 - alfa foto.
        pelat = pelat.convert("RGBA")
        alpha = Image.eval(mask, lambda v: 255 - v)
        pelat.putalpha(alpha)
        pelat.save(os.path.join(KELUARAN, f"hal{hal:02d}.webp"),
                   "WEBP", quality=82, method=6)

        if hal in ATAS_DIKUNCI:
            r0, g0, b0 = ATAS_DIKUNCI[hal]
            atas = pelat.copy()
            src, dst = pelat.load(), atas.load()
            for y in range(H):
                for x in range(W):
                    r, g, b, a = src[x, y]
                    if a and abs(r - r0) <= TOLERANSI_KUNCI \
                            and abs(g - g0) <= TOLERANSI_KUNCI \
                            and abs(b - b0) <= TOLERANSI_KUNCI:
                        dst[x, y] = (r, g, b, 0)
            atas.save(os.path.join(KELUARAN, f"hal{hal:02d}atas.webp"),
                      "WEBP", quality=82, method=6)
            kb = os.path.getsize(
                os.path.join(KELUARAN, f"hal{hal:02d}atas.webp")) // 1024
            print(f"        + lapisan atas hal {hal}: {kb}KB")

        # Warna dasar halaman: piksel pojok kiri atas yang tidak dilubangi.
        dasar = pelat.convert("RGB").getpixel((4, 4))
        ringkas["halaman"].append({
            "hal": hal,
            "dasar": "#%02x%02x%02x" % dasar,
            "slot": [{
                "kiri": round(r[0] / W * 100, 3),
                "atas": round(r[1] / H * 100, 3),
                "lebar": round((r[2] - r[0]) / W * 100, 3),
                "tinggi": round((r[3] - r[1]) / H * 100, 3),
            } for r in kotak],
        })
        kb = os.path.getsize(os.path.join(KELUARAN, f"hal{hal:02d}.webp")) // 1024
        print(f"hal {hal:2d}  {W}x{H}  {kb:4d}KB  slot={len(kotak)}  dasar={dasar}")

    kal = koordinat_kalender()
    ringkas["kalender"] = kal
    baris = [f".hh{n} {{ --x: {x}%; --y: {y}%; }}" for n, (x, y) in sorted(kal.items())]
    with open(os.path.join(KELUARAN, "kalender.css"), "w") as f:
        f.write("\n".join(baris) + "\n")
    print(f"\nkoordinat {len(kal)} angka kalender -> keluaran/kalender.css")

    with open(os.path.join(KELUARAN, "slots.json"), "w") as f:
        json.dump(ringkas, f, indent=1)
    print("\n" + json.dumps(ringkas["halaman"], indent=1))


if __name__ == "__main__":
    main()
