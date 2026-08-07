"""Gambar kue ulang tahun dua tingkat sebagai <symbol> SVG piksel.

Kisinya dibangun lewat kode, bukan diketik sebagai ASCII: kue ini 40x30 dan
setiap baris harus persis 40 karakter — mengetiknya tangan berarti salah
hitung satu kolom akan menggeser separuh gambar tanpa ketahuan.

Lilin TIDAK ikut digambar di sini. Tiap lilin harus bisa diketuk sendiri-
sendiri dan padam sendiri-sendiri, jadi lilinnya elemen HTML terpisah yang
ditumpuk di atas kue.
"""

L, T = 40, 30

K = "#2b0f22"   # garis luar
W = "#ffffff"   # krim
P = "#ff6bb5"   # badan kue
D = "#e0348c"   # bayangan kue
Y = "#ffd9ec"   # piring

kanvas = [[None] * L for _ in range(T)]


def kotak(x0, y0, x1, y1, isi, garis=K):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            tepi = x in (x0, x1) or y in (y0, y1)
            kanvas[y][x] = garis if tepi else isi


def baris(y, x0, x1, warna):
    for x in range(x0, x1 + 1):
        kanvas[y][x] = warna


def tetes(y, x0, lidah, warna=W):
    """Krim yang meleleh ke bawah.

    Lidahnya sengaja beda-beda lebar dan jaraknya. Versi pertama memakai pola
    berulang selebar satu piksel dengan jarak sama — dan yang keluar bukan
    krim meleleh, melainkan benteng bergerigi.
    """
    for geser, lebar, dalam in lidah:
        for d in range(dalam):
            for x in range(x0 + geser, x0 + geser + lebar):
                kanvas[y + d][x] = warna


# SATU tingkat, lebar dan pendek. Versi dua tingkat sempat dipakai dan gagal
# karena alasan yang tidak kelihatan di gambar diam: puncaknya cuma separuh
# lebar kue, jadi lima lilin tidak muat berjajar di sana dan dua di antaranya
# harus turun ke bahu tingkat bawah — tepat di tempat kedua karakter berdiri.
# Satu tingkat memberi seluruh lebar kue untuk lilin.
kotak(2, 6, 37, 25, P)

# Krim di puncak, lalu lidah lelehan dengan panjang berbeda-beda.
for y in range(7, 10):
    baris(y, 3, 36, W)
tetes(10, 3, [(0, 3, 2), (5, 2, 4), (9, 3, 1), (14, 2, 3), (18, 3, 5),
              (23, 2, 2), (26, 3, 3), (30, 2, 4)])

# Bayangan di dasar — tanpa ini badan kue jadi bidang pink rata yang terbaca
# seperti kotak, bukan kue.
for y in (23, 24):
    baris(y, 3, 36, D)

# Manik-manik krim di pinggang.
for x in range(5, 35, 5):
    kanvas[21][x] = W
    kanvas[21][x + 1] = W

# Piring: lebih lebar dari kuenya supaya kuenya terbaca BERDIRI di atasnya,
# bukan melayang.
kotak(0, 26, 39, 29, Y)
baris(27, 1, 38, W)

# ── Rakit jadi <rect>, deretan mendatar sewarna digabung jadi satu ──────────
bagian = []
for y in range(T):
    x = 0
    while x < L:
        c = kanvas[y][x]
        if c is None:
            x += 1
            continue
        n = 1
        while x + n < L and kanvas[y][x + n] == c:
            n += 1
        bagian.append(f'<rect x="{x}" y="{y}" width="{n}" height="1" fill="{c}"/>')
        x += n

simbol = f'<symbol id="s-kue-besar" viewBox="0 0 {L} {T}">' + "".join(bagian) + "</symbol>"
print(simbol)
print(f"\n<!-- {len(bagian)} rect, {len(simbol)} bita -->", flush=True)

# Pratinjau PNG supaya bisa dilihat mata, bukan cuma dipercaya.
try:
    from PIL import Image

    def rgba(h):
        h = h.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)

    im = Image.new("RGBA", (L, T), (0, 0, 0, 0))
    im.putdata([rgba(c) if c else (0, 0, 0, 0) for row in kanvas for c in row])
    import pathlib
    import tempfile

    # Pratinjau ditulis ke folder sementara, bukan ke direktori kerja: skrip
    # ini biasa dijalankan dari akar repo, dan PNG yang mendarat di sana ikut
    # ter-commit tanpa disadari.
    keluar = pathlib.Path(tempfile.gettempdir()) / "cek-kue-8bit.png"
    im.resize((L * 10, T * 10), Image.NEAREST).save(keluar)
    print(f"\n<!-- pratinjau: {keluar} -->")
except ImportError:
    pass


# ── Api lilin, simbol terpisah ─────────────────────────────────────────────
# Kecil, jadi diketik tangan; kuenya tidak, karena 40 kolom mustahil dihitung
# tanpa salah.
API = """
...K...
..KOK..
..KOK..
.KOYOK.
.KOYOK.
KOYYYOK
KOYYYOK
.KOOOK.
..KKK..
"""
PETA_API = {"K": "#2b0f22", "O": "#ff8a1f", "Y": "#ffd23f"}
b_api = [b for b in API.strip("\n").split("\n") if b]
LA, TA = len(b_api[0]), len(b_api)
assert all(len(b) == LA for b in b_api)
pot = []
for y, b in enumerate(b_api):
    x = 0
    while x < LA:
        c = b[x]
        if c == ".":
            x += 1
            continue
        n = 1
        while x + n < LA and b[x + n] == c:
            n += 1
        pot.append(f'<rect x="{x}" y="{y}" width="{n}" height="1" fill="{PETA_API[c]}"/>')
        x += n
print()
print(f'<symbol id="s-api" viewBox="0 0 {LA} {TA}">' + "".join(pot) + "</symbol>")
