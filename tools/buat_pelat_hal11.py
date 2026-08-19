"""Bikin pelat halaman 11 (penutup) dari kolase kiriman pemilik situs.

BEDA SUMBER dari sepuluh halaman lain. Yang lain lahir dari LOVESTORY-2.pdf
lewat tools/buat_pelat_valentine.py; halaman 11 desainnya tidak ada di PDF itu
— di sana halamannya krem polos. Kolase ini dikirim terpisah sebagai JPG
(18 Agu 2026), dan skrip inilah yang mengubahnya jadi pelat.

Karena itu halaman 11 TETAP terdaftar di TANPA_PELAT pada skrip yang satu
lagi: kalau dicabut dari sana, skrip itu akan menimpa hasil kerja skrip ini
dengan halaman krem kosong dari PDF-nya.

    /tmp/pdfenv/bin/python tools/buat_pelat_hal11.py

Tiga hal yang dikerjakannya, semuanya dari angka yang DIUKUR di gambarnya:

1. Huruf potongan koran "HAPPY BIRTHDAY" dihapus. Di kartu ini tulisannya
   jadi teks HTML yang bisa disunting pembeli ("My wish for you"), jadi huruf
   bawaannya harus hilang dari gambarnya.

2. Gambarnya 675x1200 (rasio 0,5625) sedangkan halaman kartu ini A4 (0,707).
   TIDAK diregangkan dan TIDAK dipotong dari tepi — dua-duanya merusak
   hiasannya. Yang dibuang satu pita mendatar dari tengah, yang di situ
   warnanya merah tua rata sempurna sepanjang 518 px (y 325..842, terukur).
   Membuang 245 px dari dalam pita itu tidak menyentuh satu pun hiasan.

3. Diperbesar ke 1241x1755, ukuran yang sama dengan sepuluh pelat lain.
"""
import os

from PIL import Image

SUMBER = "/Users/jepa/Downloads/ -18.jpg"
KELUARAN = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "static", "img", "valentine", "hal11.webp")

# Warna dasar kolase. DIUKUR, dan hasilnya mengejutkan enak: merahnya persis
# (68,4,2) di SETIAP piksel latar yang diperiksa — nol ragam, nol derau JPEG,
# nol gradasi. Itu yang membuat penghapusan huruf di bawah bisa sesederhana
# ini: mengecat ulang dengan warna ini tidak meninggalkan tambalan.
MERAH = (68, 4, 2)
TOLERANSI = 6           # hanya untuk MENCARI batas sequin, bukan untuk mengecat

# Batas penghapusan huruf. Angkanya dari peta piksel, bukan kira-kira:
#
#   * Huruf paling kiri ada di x=232 (baris "Birthday").
#   * Bintang perak mulai di y=224, dan di seluruh pita y 224..255 ia tidak
#     pernah lewat x=238.
#   * Bibir merah berhenti di x=215.
#
# Jadi di ATAS bintang boleh menyapu dari x=228, dan sejajar bintang harus
# mundur ke x=240. Tanpa pemisahan itu, ujung bintangnya ikut terhapus.
# Mulai dari y=40, jauh di atas huruf paling atas (y~90). Bukan kelonggaran
# asal: ubin potongan korannya punya bayangan jatuh yang menjulur ke atas
# hurufnya, dan pita yang mulai tepat di tepi huruf MEMOTONG bayangan itu —
# yang tersisa satu garis gelap mendatar tipis di tepi atas pita. Naik ke
# y=40 aman karena tiap baris tetap mulai mengecat dari tepi sequin-nya
# sendiri; di baris setinggi itu tepinya ada di x~460-510, jadi yang dicat
# cuma merah di atas merah.
ATAS_Y = (40, 223)
ATAS_X = 228
SAMPING_Y = (224, 255)
SAMPING_X = 240
KANAN_X = 660

# Tekstur sequin menjorok ke kanan di baris-baris teratas (di y=85 batas
# merahnya masih di x=286). Menyapu dengan x tetap akan mengecat sequin itu
# jadi merah dan merusak lengkung batasnya. Karena itu tiap baris mencari
# sendiri di mana merahnya mulai, lalu menyapu dari situ + jarak aman.
JARAK_AMAN = 8
RUN_MERAH = 10          # sepanjang ini harus merah semua sebelum disebut batas
# Pencarian batas sequin berhenti di sini. Dua angka ini (RUN_MERAH dan
# BATAS_MAKS) saling menjepit, dan salah satu terlalu ketat = cacat DIAM.
#
# Tepi sequin cuma menjorok lewat x=228 pada baris paling atas (terukur:
# x=286 di y=85, x=265 di y=100, x=244 di y=115, dan sudah di kiri 228 sejak
# y=130). Tapi bibir merah di x 135..215 memecah bidang merah pada baris
# y 162..226, dan di baris itu celah merah antara sequin dan bibir cuma 19 px
# — lebih pendek daripada RUN_MERAH. Pencarian tanpa batas karena itu lolos
# melewati bibirnya, lolos melewati hurufnya, dan baru menemukan deret merah
# di KANAN huruf; baris itu lalu tidak dicat sama sekali.
#
# Gejalanya bukan area yang jelas gagal, melainkan beberapa baris tipis sisa
# huruf yang setelah diperkecil terbaca sebagai garis-garis mendatar samar.
# Karena itu RUN_MERAH 10, bukan 25.
#
# Ke arah sebaliknya, jendela yang terlalu SEMPIT sama buruknya: di baris
# teratas tepi sequin ada di x~512, jadi jendela 300 tidak pernah menemukan
# apa pun, batasnya dilaporkan 0, dan pengecatan mulai dari x=228 — memakan
# takik persegi dari tekstur sequin-nya. Karena itu jendelanya 600.
#
# Diuji: pada run 6, 10, dan 14 batas yang terdeteksi sama persis di
# kelima belas baris contoh, jadi 10 tidak duduk di tepi jurang.
BATAS_MAKS = 600

# Pita merah rata yang dibuang untuk membawa rasionya ke A4.
PITA = (500, 745)       # dibuang y 500..744 = 245 baris
LEBAR, TINGGI = 1241, 1755


def merah_di(p):
    return (abs(p[0] - MERAH[0]) + abs(p[1] - MERAH[1]) + abs(p[2] - MERAH[2])) <= TOLERANSI


def batas_merah(px, y, W):
    """x pertama di baris ini yang benar-benar sudah masuk bidang merah.

    Bukan sekadar piksel merah PERTAMA: sequin punya keping gelap yang
    kebetulan sewarna merah tua, dan satu keping saja sudah cukup untuk
    melaporkan batas yang jauh terlalu ke kiri — lalu separuh tekstur sequin
    ikut dicat merah. Karena itu yang dicari deretan RUN_MERAH piksel merah
    berturut-turut.
    """
    for x in range(min(BATAS_MAKS, W - RUN_MERAH)):
        if all(merah_di(px[x + i, y]) for i in range(RUN_MERAH)):
            return x
    # Tidak ketemu di dalam jendela = tepi sequin sudah jauh di kiri xkiri
    # pada baris ini, jadi tidak ada yang perlu dihindari.
    return 0


def periksa_batas(mulai, px, W):
    """Penjaga tepi sequin — kegagalan ke arah SEBALIKNYA dari periksa_bersih.

    periksa_bersih cuma bertanya "hurufnya sudah hilang?". Ia meloloskan
    pengecatan yang terlalu rakus, dan itu pernah terjadi: jendela pencarian
    yang terlalu sempit membuat batas dilaporkan 0 di baris teratas, lalu
    pengecatan mulai dari x=228 dan MEMAKAN TAKIK PERSEGI dari tekstur
    sequin. Hurufnya memang bersih, dan hasilnya tetap rusak.

    Dua invarian yang dijaga di sini:

      1. Batasnya tidak boleh pernah 0. Nol berarti pencarian tidak menemukan
         apa pun, bukan berarti tepinya di kolom nol.
      2. Tepi sequin itu kurva yang turun ke kiri seiring y. Jitter kecil
         wajar — tepinya mosaik keping, bukan garis — tapi lompatan besar ke
         KANAN berarti deteksinya baru saja runtuh di baris itu.
    """
    b = {y: batas_merah(px, y, W) for y in mulai}
    nol = [y for y, v in b.items() if v == 0]
    if nol:
        raise SystemExit(
            f"batas sequin gagal terdeteksi di {len(nol)} baris ({nol[:5]}) — "
            "BATAS_MAKS terlalu sempit; pengecatan akan memakan sequin-nya"
        )
    urut = sorted(b)
    lompat = [(y, b[y] - b[y - 1]) for y in urut[1:] if b[y] - b[y - 1] > 24]
    if lompat:
        raise SystemExit(
            f"batas sequin melompat ke kanan di {lompat[:5]} — kurvanya "
            "seharusnya turun ke kiri; deteksinya runtuh di baris itu"
        )
    print(f"periksa: batas sequin utuh & menurun di {len(b)} baris "
          f"(x {b[urut[0]]} di atas -> {b[urut[-1]]} di bawah)")


def rencana(px, W):
    """Dari kolom mana tiap baris boleh dicat. Satu sumber kebenaran.

    Dipakai OLEH pengecatan DAN oleh pemeriksanya. Versi pertama pemeriksanya
    memakai batas tetap x=320 dan langsung melaporkan "sisa huruf" di baris
    teratas — padahal di situ x=320 memang masih sequin, dan yang salah
    pemeriksanya.
    """
    hasil = {}
    for y0, y1, xkiri in ((*ATAS_Y, ATAS_X), (*SAMPING_Y, SAMPING_X)):
        for y in range(y0, y1 + 1):
            hasil[y] = max(xkiri, batas_merah(px, y, W) + JARAK_AMAN)
    return hasil


def hapus_huruf(im):
    px = im.load()
    W, _ = im.size
    mulai = rencana(px, W)
    periksa_batas(mulai, px, W)
    n = 0
    for y, x0 in mulai.items():
        for x in range(x0, KANAN_X + 1):
            # Dicat TANPA syarat. Versi pertama cuma mengecat piksel yang
            # "cukup beda dari merah", dan itu meninggalkan bayangan tiap
            # ubin huruf: halo lembut di sekeliling potongan korannya jatuh
            # DI DALAM toleransi, jadi ia lolos, dan yang tersisa persis
            # berbentuk hurufnya. Terlihat jelas di kartu jadi. Karena
            # latarnya (68,4,2) rata sempurna, mengecat semuanya tidak
            # berisiko apa pun dan tidak menyisakan apa pun.
            if px[x, y] != MERAH:
                n += 1
            px[x, y] = MERAH
    print(f"huruf dihapus: {n} piksel dicat ulang")

    periksa_bersih(px, mulai)
    return im


def periksa_bersih(px, mulai):
    """Pastikan tidak ada sisa huruf. Alat ini pernah gagal DIAM-DIAM.

    Versi sebelumnya melewatkan sebagian baris (lihat BATAS_MAKS) dan yang
    tersisa cuma garis tipis — tidak kelihatan di gambar pelat sebesar layar,
    tapi jelas di kartunya. Karena itu hasilnya diperiksa di sini, bukan
    dipercaya begitu saja.
    """
    sisa = [(x, y) for y, x0 in mulai.items()
            for x in range(x0, KANAN_X + 1) if px[x, y] != MERAH]
    if sisa:
        raise SystemExit(
            f"masih ada {len(sisa)} piksel bersisa, contoh {sisa[:5]} — "
            "periksa BATAS_MAKS / ATAS_X / SAMPING_X sebelum memakai hasilnya"
        )
    print(f"periksa: {len(mulai)} baris bekas huruf bersih seluruhnya")


def main():
    im = Image.open(SUMBER).convert("RGB")
    print(f"sumber {im.size}  rasio {im.size[0] / im.size[1]:.4f}")
    im = hapus_huruf(im)

    atas = im.crop((0, 0, im.width, PITA[0]))
    bawah = im.crop((0, PITA[1], im.width, im.height))
    gabung = Image.new("RGB", (im.width, atas.height + bawah.height))
    gabung.paste(atas, (0, 0))
    gabung.paste(bawah, (0, atas.height))
    print(f"pita {PITA[1] - PITA[0]} px dibuang -> {gabung.size}  "
          f"rasio {gabung.size[0] / gabung.size[1]:.4f}  (A4 = {595.5 / 842.25:.4f})")

    pelat = gabung.resize((LEBAR, TINGGI), Image.LANCZOS)
    pelat.save(KELUARAN, "WEBP", quality=86, method=6)
    print(f"{KELUARAN}  {os.path.getsize(KELUARAN) // 1024}KB")


if __name__ == "__main__":
    main()
