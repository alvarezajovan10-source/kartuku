"""Cap "VORTEIZ" pada berkas gambar yang sudah jadi.

Pasangan static/css/watermark.css untuk gambar yang TIDAK lahir dari potret
browser. Dua jalur menghasilkan gambar di situs ini:

  * lewat Chrome — potret galeri dan thumbnail. Capnya sudah ikut sendiri,
    karena halaman contohnya memang sudah bercap (lihat _preview_bar.html).
  * lewat PIL — thumbnail Valentine, yang dirender dari PDF dan tidak pernah
    melewati browser sama sekali. Berkas inilah yang melayaninya.

Sudut, opasitas, dan tracking-nya sengaja disamakan dengan yang di CSS. Kalau
salah satunya diubah, ubah keduanya — cap yang berbeda-beda bentuknya di
halaman yang sama justru terbaca seperti gambar curian dari beberapa sumber.

    from tools.cap_gambar import beri_cap
    beri_cap("static/img/thumb/valentine-story.jpg")
"""
import os

from PIL import Image, ImageDraw, ImageFont

TEKS = "VORTEIZ"
SUDUT = 28              # derajat, sama dengan rotate(-28deg) di watermark.css
ALFA_ISI = 128          # setara rgba(255,255,255,.5) di watermark.css
ALFA_GARIS = 77         # setara -webkit-text-stroke rgba(38,28,26,.30)
TRACKING = 0.34         # em, sama dengan letter-spacing di CSS

# POLA BERULANG, bukan satu cap. Lima tanda per baris, baris ganjil digeser
# seperempat sel — angka yang sama persis dengan yang dihitung JS di
# _preview_bar.html. Kalau salah satunya diubah, ubah keduanya: thumbnail dan
# galeri tampil BERDAMPINGAN di halaman produk, dan pola yang berbeda rapatnya
# di dua gambar bersebelahan justru terbaca seperti gambar curian dari dua
# sumber — kebalikan dari gunanya cap ini.
KOLOM = 5
TINGGI_SEL = 0.45       # terhadap lebar sel; baris LEBIH rapat daripada kolom
# Baris TIDAK digeser. Susunan bata sempat dicoba dan hasilnya terbaca acak:
# pergeseran bertumpuk dengan kemiringan 28 derajat, dan mata kehilangan satu
# pun garis lurus untuk dijadikan patokan. Tanpa geseran, kemiringannya sendiri
# yang membentuk deret diagonal rapi. Angka ini dipertahankan (bukan dihapus)
# supaya jelas ia keputusan, bukan kelupaan.
GESER = 0.0

FONT_CALON = [
    # Bobot BIASA, bukan tebal. Huruf tebal terbaca seperti stempel tanda
    # terima; yang dicari di sini tanda yang terlihat disengaja.
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica.ttf",
    "/Library/Fonts/Arial.ttf",
]


def _font(ukuran):
    for jalur in FONT_CALON:
        if os.path.exists(jalur):
            return ImageFont.truetype(jalur, ukuran)
    raise SystemExit(
        "Tidak ada font tebal yang bisa dipakai. Tambahkan jalurnya ke FONT_CALON."
    )


def _gambar_teks(ukuran):
    """Teks bertracking sebagai gambar RGBA: isi putih bergaris tepi tipis.

    Ditulis huruf demi huruf karena PIL tidak punya letter-spacing, dan tanpa
    tracking capnya terbaca rapat dan murah — beda jauh dengan yang di CSS.

    Garis tepi dan isinya punya alfa SENDIRI-SENDIRI, bukan satu opasitas
    untuk keduanya. Satu opasitas memudarkan garis tepinya juga, dan tanpanya
    cap putih lenyap di kartu berlatar terang.
    """
    font = _font(ukuran)
    jarak = int(ukuran * TRACKING)
    lebar_huruf = [font.getbbox(h)[2] - font.getbbox(h)[0] for h in TEKS]
    lebar = sum(lebar_huruf) + jarak * (len(TEKS) - 1)
    tinggi = int(ukuran * 1.5)

    im = Image.new("RGBA", (lebar + 6, tinggi), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 3
    for i, h in enumerate(TEKS):
        # Garis tepi tipis + isi putih dalam satu panggilan. Bukan dua salinan
        # yang digeser: salinan gelap di belakang huruf putih menghasilkan
        # efek TIMBUL yang terbaca murah, dan itu yang membuat versi
        # sebelumnya ditolak. Garis tepi memberi ketegasan yang sama di latar
        # terang tanpa kesan timbul sama sekali.
        d.text((x, tinggi // 4), h, font=font,
               fill=(255, 255, 255, ALFA_ISI),
               stroke_width=1, stroke_fill=(38, 28, 26, ALFA_GARIS))
        x += lebar_huruf[i] + jarak
    return im


def beri_cap(jalur, keluaran=None):
    dasar = Image.open(jalur).convert("RGBA")
    W, H = dasar.size

    lebar_sel = W / KOLOM
    tinggi_sel = lebar_sel * TINGGI_SEL

    # Ukuran huruf dicari supaya satu tanda mengisi ~70% lebar selnya sesudah
    # dimiringkan. Diukur sekali lalu diskalakan — lebih tepat daripada
    # menebak rumus trigonometrinya, dan tidak bergantung pada font yang
    # kebetulan ada di mesin ini.
    percobaan = max(10, int(lebar_sel / 2))
    coba = _gambar_teks(percobaan).rotate(SUDUT, expand=True)
    # 0,72, bukan 0,88. Pada 0,88 tanda-tanda bersentuhan mendatar dan
    # terbaca "VORTEIZVORTEIZ" sebagai satu kata panjang — polanya hilang,
    # dan yang tersisa cuma garis-garis. Jaraknya harus terlihat supaya tiap
    # tanda terbaca sebagai tanda.
    ukuran = max(8, int(percobaan * (lebar_sel * 0.72) / coba.width))
    tanda = _gambar_teks(ukuran).rotate(SUDUT, expand=True)


    # Tanda ditempel ke LAPISAN transparan seukuran gambar, baru lapisan itu
    # disatukan sekali. Bukan ditempel satu per satu ke gambarnya: baris dan
    # kolom sengaja dimulai dari -1 supaya polanya tidak berhenti di tepi, dan
    # alpha_composite menolak koordinat negatif — sedangkan paste() memotongnya
    # sendiri. Menempel sekali di akhir juga membuat tanda yang bertindihan di
    # tepi tidak menumpuk jadi bercak yang lebih pekat.
    lapisan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    baris = int(H / tinggi_sel) + 2
    for b in range(-1, baris):
        y = int(b * tinggi_sel + (tinggi_sel - tanda.height) / 2)
        geser = int(lebar_sel * GESER) if b % 2 else 0
        for k in range(-1, KOLOM + 1):
            x = int(k * lebar_sel + (lebar_sel - tanda.width) / 2) + geser
            lapisan.paste(tanda, (x, y), tanda)

    dasar.alpha_composite(lapisan)

    tujuan = keluaran or jalur
    dasar.convert("RGB").save(tujuan, "JPEG", quality=88, optimize=True)
    return tujuan


if __name__ == "__main__":
    import sys

    for berkas in sys.argv[1:]:
        print("cap ->", beri_cap(berkas))
