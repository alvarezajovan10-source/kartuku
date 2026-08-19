"""Bikin pelat halaman 12 (penutup hati renda) dari PDF kiriman pemilik situs.

SUMBER KETIGA. Sepuluh halaman pertama lahir dari LOVESTORY-2.pdf lewat
tools/buat_pelat_valentine.py, halaman 11 dari sebuah JPG lewat
tools/buat_pelat_hal11.py, dan halaman 12 dari PDF ini. Karena itu halaman 12
sama sekali tidak dikenal skrip yang pertama — tidak ada halaman ke-12 di
LOVESTORY-2.pdf yang bisa menimpanya.

    /tmp/pdfenv/bin/python tools/buat_pelat_hal12.py

Yang membedakan halaman ini dari semua pelat lain: LUBANG FOTONYA TIDAK BISA
DIUKUR DARI PDF-NYA. Di LOVESTORY-2.pdf tiap foto pengisi adalah objek gambar
tersendiri, jadi bentuk lubangnya didapat dengan merender halaman dua kali —
pengisi diganti putih rata sekali, hitam rata sekali — dan selisihnya persis
nilai alfa foto di tiap piksel. PDF ini tidak bisa diperlakukan begitu:
seluruh halamannya SATU bitmap 736x1308 yang sudah rata (diperiksa:
page.get_images() mengembalikan tepat satu, dan tidak ada objek teks maupun
vektor sama sekali). Jadi bentuk hatinya harus dipulihkan dari pikselnya.

Yang dikerjakan skrip ini, semuanya dari angka yang DIUKUR di gambarnya:

1. Foto pasangan di dalam bingkai renda dilubangi jadi transparan, supaya
   foto pembeli bisa duduk di belakangnya. Rendanya tetap utuh DI ATAS foto —
   itu sebabnya foto ditaruh di belakang pelat, sama seperti pita halaman 8
   dan logam liontin halaman 7.

2. Gambarnya 736x1308 (rasio 0,5627) sedangkan halaman kartu ini A4 (0,707).
   Dipotong dari ATAS dan BAWAH, bukan diregangkan: hati rendanya terukur
   duduk tepat di tengah gambar (kotaknya y 389..920, titik tengah 654,5;
   tengah gambar 654,0), jadi memotong sama banyak di kedua ujung membuatnya
   tetap di tengah dan tidak menyentuh satu pun hiasan.

3. Diperbesar ke 1241x1755, ukuran yang sama dengan sebelas pelat lain.

Skrip ini MEMERIKSA HASILNYA SENDIRI sebelum menyimpan — lihat catatan di
periksa_tanpa_sisa_foto() soal kenapa itu tidak bisa ditawar di sini.
"""
import os
from collections import deque

import numpy as np
import pymupdf
from PIL import Image

SUMBER = "/Users/jepa/Downloads/Merah Putih Ilustratif Kafe Kisah Anda.pdf"
KELUARAN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "static", "img", "valentine", "hal12.webp")

LEBAR, TINGGI = 1241, 1755        # sama dengan sebelas pelat lain (A4 @150dpi)
RASIO_A4 = 390 / 551.6

# ── Angka hasil ukur ────────────────────────────────────────────────────────
# Sumbu simetri hati. Kotak hati terukur x 160..575, titik tengahnya 367,5 —
# dan lebar gambarnya 736, jadi tengah gambar 368,0. Meleset 0,5 px. Dipakai
# menambal cacat yang dijelaskan di simetrikan().
SUMBU = 367.5

# Titik yang PASTI di dalam foto, dipakai sebagai benih semua penelusuran.
# Diambil di tengah hati, jauh dari renda mana pun.
BENIH = (640, 368)                # (y, x)

# Batas saturasi pemisah renda dari foto. Ini kunci seluruh skrip, dan
# angkanya bukan tebakan — lihat catatan panjang di sidik().
AMBANG_FOTO = 0.065

# Kertas merah: jenuh, cukup terang, dan R jauh di atas G.
AMBANG_KERTAS = 0.35
MIN_MERAH = 90
MIN_BEDA_RG = 45

# Lubang dilebarkan 2 px sebelum dipakai. Cincin 1 px tepat di luar batas
# terukur masih menyimpan ~10% campuran foto (saturasi 0,051 lawan 0,047
# rendanya) — sisa antialias di perbatasan. Dua piksel dari pita renda selebar
# ~60 px tidak terlihat; segaris bayangan pasangan lama sangat terlihat.
LEBARKAN_LUBANG = 2


def muat():
    """Ambil bitmap rata dari PDF-nya, pada resolusi aslinya.

    Sengaja mengambil gambar yang TERTANAM, bukan merender halaman. Halamannya
    810x1440pt sedangkan bitmapnya 736x1308 px, jadi merender pada dpi berapa
    pun hanya memperbesar piksel yang sama — dan pengklasifikasian di bawah
    bekerja jauh lebih bersih pada tepi yang belum diperhalus.

    (Bitmapnya terpasang di y 0..1439,2 dari halaman setinggi 1440pt. Sisa
    0,8pt itu jatuh di dalam pita yang toh dipotong di potong_ke_a4().)
    """
    dok = pymupdf.open(SUMBER)
    if dok.page_count != 1:
        raise SystemExit(f"PDF-nya {dok.page_count} halaman, diharapkan 1.")
    xref = dok[0].get_images(full=True)[0][0]
    data = dok.extract_image(xref)
    from io import BytesIO
    return Image.open(BytesIO(data["image"])).convert("RGB")


def sidik(a):
    """Kembalikan (saturasi, mask kertas merah).

    Saturasi HSV, dan itu pilihan yang dipikirkan. Kecerahan TIDAK bisa
    dipakai memisahkan renda dari foto: diukur di gambarnya, renda
    RGB(225,220,214) dan baju putih si lelaki di dalam foto RGB(226,216,206) —
    praktis sama terangnya. Yang membedakan keduanya nada hangat: fotonya
    sepia (R-B = 20..25), rendanya netral (R-B = 4..13). Dinormalkan terhadap
    kecerahan, itu jadi saturasi, dan jaraknya melebar:

        renda        0,04 .. 0,05
        foto         0,09 .. 0,43   (0,09 = baju putih, kasus tersulitnya)
        kertas merah 0,55 .. 0,66

    AMBANG_FOTO 0,065 duduk di tengah celah renda-foto. Disapu 0,055 sampai
    0,080 dan hasilnya nyaris tidak bergerak (luas 108.887 -> 103.519 px,
    kotaknya bergeser paling banyak 3 px), jadi ambangnya tidak genting.
    """
    x = a.astype(np.int16)
    mx, mn = x.max(2), x.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0.0)
    kertas = (sat > AMBANG_KERTAS) & (x[..., 0] > MIN_MERAH) \
        & ((x[..., 0] - x[..., 1]) > MIN_BEDA_RG)
    return sat, kertas


def komponen(mask, benih):
    """Bagian mask yang tersambung ke benih."""
    H, W = mask.shape
    vis = np.zeros_like(mask)
    if not mask[benih]:
        raise SystemExit(f"Benih {benih} tidak jatuh di dalam mask.")
    vis[benih] = True
    q = deque([benih])
    while q:
        y, x = q.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < H and 0 <= nx < W and not vis[ny, nx] and mask[ny, nx]:
                vis[ny, nx] = True
                q.append((ny, nx))
    return vis


def tutup_lubang(mask):
    """Isi rongga di dalam mask — apa pun yang tidak tersambung ke tepi gambar.

    Perlu karena piksel foto yang kelabu MURNI (mis. rambut RGB(5,5,5))
    bersaturasi nol dan lolos sebagai "renda". Tanpa ini, lubangnya berbintik.
    """
    H, W = mask.shape
    luar = np.zeros_like(mask)
    q = deque()
    for y in range(H):
        for x in (0, W - 1):
            if not mask[y, x] and not luar[y, x]:
                luar[y, x] = True
                q.append((y, x))
    for x in range(W):
        for y in (0, H - 1):
            if not mask[y, x] and not luar[y, x]:
                luar[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < H and 0 <= nx < W and not luar[ny, nx] and not mask[ny, nx]:
                luar[ny, nx] = True
                q.append((ny, nx))
    return mask | ~luar


def lebarkan(mask, r):
    out = mask.copy()
    for _ in range(r):
        t = out.copy()
        t[1:, :] |= out[:-1, :]
        t[:-1, :] |= out[1:, :]
        t[:, 1:] |= out[:, :-1]
        t[:, :-1] |= out[:, 1:]
        out = t
    return out


def kikis(mask, r):
    return ~lebarkan(~mask, r)


def simetrikan(mask):
    """Gabungkan mask dengan cerminannya.

    Ini menambal satu-satunya cacat besar pengklasifikasian: baju putih si
    lelaki di lobus kanan bawah bersaturasi 0,09 — di atas ambang, tapi tipis,
    dan sebagian pikselnya tetap jatuh ke sisi renda sehingga tepi kanan
    tergigit. Di sisi KIRI pada ketinggian yang sama isinya rambut dan gaun
    gelap, jadi terbaca sempurna.

    Boleh dilakukan karena hatinya memang simetris, dan itu DIUKUR bukan
    diandaikan: titik tengah tiap baris mask meleset dari SUMBU paling jauh
    4 px, dan hampir semua baris di bawah 1,5 px.

    Lebar gambarnya genap (736), jadi cerminan x adalah 735-x — persis
    mask[:, ::-1], dengan sumbu 367,5. Cocok dengan SUMBU terukur.
    """
    return mask | mask[:, ::-1]


def bentuk_hati(a):
    """Mask piksel foto pasangan di dalam bingkai renda."""
    sat, kertas = sidik(a)
    doily = komponen(~kertas, BENIH)          # renda + foto, tanpa kertas
    kasar = komponen(doily & (sat >= AMBANG_FOTO), BENIH)
    rapi = tutup_lubang(simetrikan(tutup_lubang(kasar)))
    # Tutup morfologis: buang gerigi selebar beberapa piksel di batasnya
    # tanpa menggeser batas itu sendiri.
    rapi = komponen(kikis(lebarkan(rapi, 3), 3), BENIH)
    return rapi, sat


def kotak(mask):
    ys, xs = np.nonzero(mask)
    return xs.min(), ys.min(), xs.max(), ys.max()


# ── Pemeriksaan hasil ───────────────────────────────────────────────────────
def periksa_hati(mask, doily):
    """Bentuknya masih hati yang duduk di dalam rendanya?

    Yang dibandingkan kotak hati terhadap kotak DOILY, bukan keterisian
    kotaknya sendiri. Keterisian sempat dipakai dan ternyata tidak
    membedakan apa pun: hatinya 67,3% dari kotaknya, dan doily selebar
    penuh — persis kegagalan yang mau ditangkap — 66,8%. Dua angka yang
    hampir sama, jadi ambang mana pun akan meloloskan keduanya atau
    menolak keduanya.

    Selisih kotaknya sebaliknya tegas: pita rendanya ~75 px di tiap sisi,
    jadi hati yang benar mengisi ~73% lebar doily. Mask yang bocor ke renda
    akan mendekati 100%, yang terlalu ketat akan jauh di bawah.
    """
    x0, y0, x1, y1 = kotak(mask)
    dx0, dy0, dx1, dy1 = kotak(doily)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    dw, dh = dx1 - dx0 + 1, dy1 - dy0 + 1
    pusat = (x0 + x1) / 2
    print(f"  hati: {w}x{h} px, kotak x {x0}..{x1} y {y0}..{y1}, pusat-x {pusat:.1f}")
    print(f"  terhadap doily {dw}x{dh}: {w / dw:.1%} lebar, {h / dh:.1%} tinggi")
    if not 0.62 <= w / dw <= 0.85 or not 0.62 <= h / dh <= 0.85:
        raise SystemExit("Hati tidak sepadan dengan rendanya — ambang/benih bergeser?")
    if abs(pusat - SUMBU) > 2:
        raise SystemExit(f"Pusat mendatar {pusat:.1f} jauh dari sumbu {SUMBU}.")
    if not 1.0 <= w / h <= 1.2:
        raise SystemExit(f"Perbandingan hati {w / h:.3f} di luar dugaan.")


def periksa_tanpa_sisa_foto(mask, sat):
    """Tidak ada sisa foto pasangan lama di tepi lubang?

    Pemeriksaan yang paling penting di skrip ini. Kalau lubangnya kurang besar
    beberapa piksel, yang tertinggal BUKAN cacat abstrak melainkan segaris
    wajah pasangan orang lain di pinggir foto pembeli — dan itu tidak akan
    terlihat di berkas WebP-nya, cuma di kartu yang sudah jadi.
    """
    cincin = lebarkan(mask, 3) & ~mask
    s = sat[cincin]
    persen = 100 * (s >= 0.075).mean()
    print(f"  cincin 3px di luar lubang: saturasi rata {s.mean():.4f}, "
          f"{persen:.1f}% masih bernada foto")
    if persen > 2:
        raise SystemExit("Masih ada foto lama di tepi lubang — lubangnya kurang besar.")


def periksa_renda_utuh(mask, sat, doily_awal):
    """Rendanya tidak ikut termakan?

    Pasangan wajib dari pemeriksaan di atas: melebarkan lubang sampai bersih
    itu gampang — cukup lebarkan sampai seluruh doily hilang. Yang dijaga di
    sini justru sisi sebaliknya.
    """
    renda = doily_awal & ~mask & (sat < AMBANG_FOTO)
    print(f"  renda tersisa: {renda.sum()} px")
    if renda.sum() < 60_000:
        raise SystemExit("Renda tersisa terlalu sedikit — lubangnya kelewat besar.")


def potong_ke_a4(tinggi_asal, tinggi_baru):
    """Berapa baris dibuang dari atas dan dari bawah."""
    buang = tinggi_asal - tinggi_baru
    atas = buang // 2
    return atas, atas + tinggi_baru


def main():
    asli = muat()
    W, H = asli.size
    print(f"sumber {W}x{H} (rasio {W / H:.4f})")

    a = np.asarray(asli)
    hati, sat = bentuk_hati(a)
    _, kertas = sidik(a)
    doily = komponen(~kertas, BENIH)

    periksa_hati(hati, doily)
    hati = lebarkan(hati, LEBARKAN_LUBANG)
    periksa_tanpa_sisa_foto(hati, sat)
    periksa_renda_utuh(hati, sat, doily)

    # ── Potong 9:16 -> A4 ───────────────────────────────────────────────
    tinggi_a4 = round(W / RASIO_A4)
    y0, y1 = potong_ke_a4(H, tinggi_a4)
    kd = kotak(doily)
    print(f"  potong y {y0}..{y1} ({H - tinggi_a4} baris dibuang: "
          f"{y0} atas, {H - y1} bawah)")
    print(f"  doily y {kd[1]}..{kd[3]} -> {kd[1] - y0}..{kd[3] - y0} "
          f"dari {tinggi_a4}; sisa margin {kd[1] - y0} atas, "
          f"{tinggi_a4 - (kd[3] - y0)} bawah")
    if kd[1] < y0 or kd[3] > y1:
        raise SystemExit("Potongannya memakan bingkai renda.")

    potong = asli.crop((0, y0, W, y1))
    mask = Image.fromarray((hati[y0:y1] * 255).astype(np.uint8))

    # ── Perbesar, lalu lubangi ──────────────────────────────────────────
    # Masknya ikut diperbesar dengan penapis halus, BUKAN NEAREST: nilai
    # antaranya jadi alfa separuh di perbatasan, yang meniru antialias tepi
    # aslinya. Tanpa itu tepi hatinya bergerigi tangga.
    pelat = potong.resize((LEBAR, TINGGI), Image.LANCZOS).convert("RGBA")
    mask_besar = mask.resize((LEBAR, TINGGI), Image.LANCZOS)
    alfa = 255 - np.clip(np.asarray(mask_besar).astype(np.int16), 0, 255)
    pelat.putalpha(Image.fromarray(alfa.astype(np.uint8)))

    pelat.save(KELUARAN, "WEBP", quality=86, method=6, lossless=False)
    print(f"\n{KELUARAN}  {os.path.getsize(KELUARAN) // 1024}KB")

    # ── Angka untuk valentine.html ──────────────────────────────────────
    hx0, hy0, hx1, hy1 = kotak(hati[y0:y1])
    hw, hh = hx1 - hx0 + 1, hy1 - hy0 + 1
    print("\nbingkai foto (tempel ke valentine.html):")
    print(f"  --kiri:{100 * hx0 / W:.3f}%;--atas:{100 * hy0 / tinggi_a4:.3f}%;"
          f"--lebar:{100 * hw / W:.3f}%;--tinggi:{100 * hh / tinggi_a4:.3f}%")
    print(f'  "rasio": {hw / hh:.4f}   (seed_templates.py)')


if __name__ == "__main__":
    main()
