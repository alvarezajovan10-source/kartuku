"""Susun sprite sheet dua karakter penemani dari bagian tubuh.

Karakter TIDAK digambar per-frame satu per satu — itu 10 animasi x 2 karakter
x beberapa frame, mustahil dijaga konsistensinya. Yang digambar hanya
BAGIAN tubuhnya (kepala, badan, lengan, kaki), lalu tiap frame disusun dari
bagian yang sama dengan pergeseran berbeda. Konsekuensinya penting: kalau
nanti kepalanya diganti supaya persis gambar aslinya, SELURUH animasi ikut
berubah — tidak ada frame yang perlu digambar ulang.

Keluaran: satu PNG per karakter, kisi 6 kolom x 10 baris, latar transparan,
kaki selalu menempel di garis yang sama (BASELINE) supaya tidak naik-turun
saat berjalan.
"""

import pathlib

from PIL import Image

LEBAR, TINGGI = 34, 46
BASELINE = 45          # baris tempat telapak kaki menempel
KOLOM = 6              # frame terbanyak dalam satu animasi

# Urutan baris di sheet. JS membaca urutan yang SAMA — kalau diubah di sini,
# ubah juga ANIM di static/js/render/game8bit.js.
URUTAN = ["idle", "walk", "run", "wave", "happy", "surprised",
          "sit", "sleep", "jump", "celebrate", "hug", "blow"]

T = (0, 0, 0, 0)       # transparan


def warna(hexs):
    h = hexs.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def grid(seni, peta):
    """ASCII -> daftar baris berisi warna RGBA."""
    baris = [b for b in seni.strip("\n").split("\n") if b]
    lebar = max(len(b) for b in baris)
    for i, b in enumerate(baris):
        assert len(b) == lebar, f"baris {i + 1}: {len(b)} kolom, harusnya {lebar}"
    return [[T if c == "." else warna(peta[c]) for c in b] for b in baris]


def tempel(kanvas, bagian, x, y):
    for dy, baris in enumerate(bagian):
        for dx, c in enumerate(baris):
            if c[3] == 0:
                continue
            px, py = x + dx, y + dy
            if 0 <= px < LEBAR and 0 <= py < TINGGI:
                kanvas[py][px] = c


# ── COWOK: hoodie pink bertudung, poni hitam, hati di dada ────────────────
PETA_COWOK = {
    "K": "#1a1a1a",   # garis luar & rambut
    "P": "#f4a8c8",   # hoodie pink
    "D": "#e087ae",   # bayangan hoodie
    "C": "#fce8cf",   # kulit
    "M": "#e8637f",   # mulut
    "R": "#f6b0b8",   # pipi
    "H": "#e02d6a",   # hati
    "W": "#ffffff",   # tali hoodie
    "N": "#3a3f5c",   # celana
}

COWOK_KEPALA = """
.......KKKKKKKKKK.......
.....KKPPPPPPPPPPKK.....
....KPPPPPPPPPPPPPPK....
...KPPPPPPPPPPPPPPPPK...
..KPPPPKKKKKKKKKKPPPPK..
..KPPPKKKKKKKKKKKKPPPK..
.KPPPKKKKKKKKKKKKKKPPPK.
.KPPKKCCCCCCCCCCKKKPPPK.
.KPPKCCCCCCCCCCCCKKPPPK.
.KPPKCCCCCCCCCCCCCKPPPK.
.KPPKCCKKCCCCKKCCCKPPPK.
.KPPKCCKKCCCCKKCCCKPPPK.
.KPPKCRCCCCCCCCRCCKPPPK.
.KPPKCRCCCMMCCCRCCKPPPK.
.KPPKCCCCCMMCCCCCCKPPPK.
.KPPKCCCCCCCCCCCCCKPPPK.
..KPPKCCCCCCCCCCCKPPPK..
..KPPPKCCCCCCCCCKPPPPK..
...KPPPKKKKKKKKKPPPPK...
....KPPPPPPPPPPPPPPK....
.....KKPPPPPPPPPPKK.....
.......KKKKKKKKKK.......
"""

COWOK_BADAN = """
.KKPPPPPPPPPPKK.
KPPWPPPPPPPPWPPK
KPPWPPPHHPPPWPPK
KPPPPPHHHHPPPPPK
KPPPPPHHHHPPPPPK
KPPPPPPHHPPPPPPK
KPPPPPPPPPPPPPPK
KDPPPPPPPPPPPPDK
KNNNNNNNNNNNNNNK
KNNNNNNNNNNNNNNK
.KKKNNNNNNNNKKK.
"""

COWOK_LENGAN = """
KDDK
KDDK
KDDK
KDDK
KDDK
KCCK
KKKK
"""

COWOK_KAKI = """
KNNNK
KNNNK
KNNNK
KKKKK
KKKKK
"""

# ── CEWEK: rambut cokelat berponi, pita pink, gaun berkerah putih ──────────
PETA_CEWEK = {
    "K": "#1a1a1a",
    "B": "#6b4030",   # rambut cokelat
    "S": "#96604a",   # kilau rambut
    "C": "#fce8cf",
    "M": "#e8637f",
    "R": "#f6b0b8",
    "P": "#f4a8c8",   # gaun
    "D": "#e087ae",
    "W": "#ffffff",   # kerah & renda
    "N": "#4a2c22",   # sepatu
    "Y": "#f27fae",   # pita
}

CEWEK_KEPALA = """
......KKKKKKKK..........
....KKBBBBBBBBKK........
...KBSBBBBBBBBBBK..KK...
..KBSSBBBBBBBBBBBKKYYK..
..KBBSBBBBBBBBBBBKKYKK..
.KBBBBBBBBBBBBBBBBKYYK..
.KBBBKKKKKKKKKKBBBK.KK..
.KBBKCCCCCCCCCCKBBK.....
.KBBKCCCCCCCCCCKBBK.....
.KBBKCCKKCCCCKKCKBBK....
.KBBKCCKKCCCCKKCKBBK....
.KBBKCRCCCCCCCCRKBBK....
.KBBKCRCCCMMCCCRKBBK....
.KBBKCCCCCMMCCCCKBBK....
.KBBKCCCCCCCCCCKBBK.....
.KBBBKCCCCCCCCKBBBK.....
..KBBBKKKKKKKKBBBK......
...KBBBBBBBBBBBBK.......
....KKBBBBBBBBKK........
......KKKKKKKK..........
"""

CEWEK_BADAN = """
.KKWWWWWWWWWWKK.
KWWWWWWWWWWWWWWK
KPPPPPPPPPPPPPPK
KPPPPPPPPPPPPPPK
KPPPPPDDDDPPPPPK
KPPPPPPPPPPPPPPK
KPPPPPPPPPPPPPPK
KPPPPPPPPPPPPPPK
KWWWWWWWWWWWWWWK
KWWWWWWWWWWWWWWK
.KKKKKKKKKKKKKK.
"""

CEWEK_LENGAN = """
KCCK
KCCK
KCCK
KCCK
KCCK
KCCK
KKKK
"""

CEWEK_KAKI = """
KCCCK
KCCCK
KNNNK
KKKKK
KKKKK
"""

def kepala_tiup(seni):
    """Kepala versi meniup, DITURUNKAN dari kepala biasa — bukan digambar ulang.

    Alasannya sama dengan alasan seluruh berkas ini memakai bagian tubuh:
    kalau nanti wajahnya diperbaiki, versi meniupnya ikut berubah sendiri.
    Menyalin 22 baris ASCII kedua kalinya berarti dua wajah yang pelan-pelan
    saling menyimpang.

    Yang diubah cuma mulut dan pipi: mulut jadi cincin gelap dengan lubang
    kecil di tengah (mengerucut), pipi digembungkan satu piksel ke luar.
    """
    baris = [b for b in seni.strip("\n").split("\n") if b]
    mulut = [i for i, b in enumerate(baris) if "M" in b]
    assert len(mulut) == 2, f"mulut harus 2 baris, dapat {len(mulut)}"
    atas, bawah = mulut
    kolom = [i for i, c in enumerate(baris[atas]) if c == "M"]
    kiri, kanan = kolom[0], kolom[-1]

    def ganti(b, ubah):
        c = list(b)
        for i, v in ubah:
            if 0 <= i < len(c):
                c[i] = v
        return "".join(c)

    def gembung(b):
        pipi = [i for i, c in enumerate(b) if c == "R"]
        if not pipi:
            return b
        return ganti(b, [(pipi[0] - 1, "R"), (pipi[-1] + 1, "R")])

    # Bibir atas: langit-langit mulut, sekalian pipi menggembung.
    baris[atas - 1] = gembung(ganti(baris[atas - 1], [(kiri, "K"), (kanan, "K")]))
    # Baris mulut: sisi kiri-kanan digelapkan supaya lubangnya bulat.
    baris[atas] = gembung(ganti(baris[atas], [(kiri - 1, "K"), (kanan + 1, "K")]))
    # Bibir bawah.
    baris[bawah] = ganti(baris[bawah], [(kiri, "K"), (kanan, "K")])
    return "\n".join(baris)


COWOK_KEPALA_TIUP = kepala_tiup(COWOK_KEPALA)
CEWEK_KEPALA_TIUP = kepala_tiup(CEWEK_KEPALA)

TOKOH = {
    "cowok": (PETA_COWOK, COWOK_KEPALA, COWOK_BADAN, COWOK_LENGAN, COWOK_KAKI,
              COWOK_KEPALA_TIUP),
    "cewek": (PETA_CEWEK, CEWEK_KEPALA, CEWEK_BADAN, CEWEK_LENGAN, CEWEK_KAKI,
              CEWEK_KEPALA_TIUP),
}

# ── Pose ───────────────────────────────────────────────────────────────────
# naik      : geser badan+kepala+lengan (negatif = terangkat)
# kki / kka : geser kaki kiri & kanan, DIHITUNG SENDIRI dari garis tanah —
#             bukan ikut badan. Ini yang membuat "duduk" mungkin: badan turun
#             sementara kaki tetap di tanah. Versi sebelumnya menggeser
#             semuanya sekaligus, jadi pose duduk terdorong keluar frame.
# lki / lka : geser lengan kiri & kanan
# renggang  : jarak kedua kaki (langkah)
# kaki      : False = kaki disembunyikan (dilipat di balik badan saat duduk)
# condong   : geser kepala+badan+lengan ke arah hadap (positif = mencondong
#             ke depan). Kaki TIDAK ikut, jadi badannya benar-benar
#             membungkuk, bukan seluruh tokoh bergeser.
# kepala    : "tiup" memakai kepala bermulut mengerucut
def P(naik=0, kki=0, kka=0, lki=0, lka=0, renggang=0, kaki=True,
      xki=0, xka=0, condong=0, kepala="biasa"):
    return dict(naik=naik, kki=kki, kka=kka, lki=lki, lka=lka,
                renggang=renggang, kaki=kaki, xki=xki, xka=xka,
                condong=condong, kepala=kepala)


POSE = {
    "idle":      [P(), P(naik=1, lki=1, lka=1)],
    "walk":      [P(kka=-3, lki=2, lka=-2, renggang=1), P(naik=1),
                  P(kki=-3, lki=-2, lka=2, renggang=1), P(naik=1)],
    "run":       [P(naik=-1, kki=-2, kka=-6, lki=3, lka=-5, renggang=2), P(naik=1, renggang=1),
                  P(naik=-1, kki=-6, kka=-2, lki=-5, lka=3, renggang=2), P(naik=1, renggang=1)],
    "wave":      [P(lka=-9), P(lka=-13), P(lka=-9)],
    "happy":     [P(naik=-3, kki=-3, kka=-3, lki=-7, lka=-7), P(lki=-5, lka=-5)],
    "surprised": [P(naik=-2, lki=-4, lka=-4, renggang=2), P(lki=-3, lka=-3, renggang=2)],
    # Duduk & tidur: badan turun sampai menyentuh tanah, kaki dilipat.
    "sit":       [P(naik=4, lki=2, lka=2, kaki=False), P(naik=4, lki=3, lka=3, kaki=False)],
    "sleep":     [P(naik=5, lki=3, lka=3, kaki=False), P(naik=6, lki=4, lka=4, kaki=False)],
    "jump":      [P(naik=3, kki=1, kka=1, lki=2, lka=2),
                  P(naik=-11, kki=-8, kka=-8, lki=-9, lka=-9, renggang=1),
                  P(naik=-4, kki=-3, kka=-3, lki=-4, lka=-4)],
    "hug":       [P(lka=-5, xka=3, lki=1, xki=1),
                  P(naik=1, lka=-6, xka=4, lki=1, xki=1)],
    "celebrate": [P(naik=-4, kki=-4, kka=-4, lki=-12, lka=-9, renggang=1),
                  P(lki=-9, lka=-12, renggang=1),
                  P(naik=-4, kki=-4, kka=-4, lki=-12, lka=-9, renggang=1),
                  P(lki=-9, lka=-12, renggang=1)],
    # Meniup lilin: tarik napas dulu (mundur sedikit), baru mengembus jauh ke
    # depan. Tanpa ancang-ancang, tiupannya terbaca seperti tersentak.
    "blow":      [P(condong=-1, naik=-1, kepala="tiup"),
                  P(condong=3, naik=1, lki=1, lka=1, renggang=1, kepala="tiup"),
                  P(condong=2, naik=1, lki=1, lka=1, renggang=1, kepala="tiup")],
}


def susun(bagian, pose):
    peta, s_kepala, s_badan, s_lengan, s_kaki, s_kepala_tiup = bagian
    kepala = grid(s_kepala_tiup if pose["kepala"] == "tiup" else s_kepala, peta)
    badan = grid(s_badan, peta)
    lengan = grid(s_lengan, peta)
    kaki = grid(s_kaki, peta)

    kanvas = [[T] * LEBAR for _ in range(TINGGI)]
    x_tengah = LEBAR // 2
    lebar_badan = len(badan[0])

    # Garis tanah dulu, lalu semuanya diukur dari sana.
    kaki_dasar = BASELINE - len(kaki) + 1
    if pose["kaki"]:
        tempel(kanvas, kaki, x_tengah - 5 - pose["renggang"], kaki_dasar + pose["kki"])
        tempel(kanvas, kaki, x_tengah + 0 + pose["renggang"], kaki_dasar + pose["kka"])

    badan_y = kaki_dasar - len(badan) + 1 + pose["naik"]

    # Lengan SEBELUM badan supaya bahunya tertutup rapi, dan agak keluar dari
    # sisi badan — kalau sejajar, warnanya menyatu dan tangannya tidak
    # kelihatan sama sekali.
    condong = pose["condong"]
    lengan_y = badan_y + 2
    tempel(kanvas, lengan, x_tengah - lebar_badan // 2 - 4 + pose["xki"] + condong,
           lengan_y + pose["lki"])
    tempel(kanvas, lengan, x_tengah + lebar_badan // 2 + pose["xka"] + condong,
           lengan_y + pose["lka"])

    tempel(kanvas, badan, x_tengah - lebar_badan // 2 + condong, badan_y)

    kepala_y = badan_y - len(kepala) + 3
    # Kepala dicondongkan SATU piksel lebih jauh dari badan — cukup untuk
    # terbaca membungkuk, tidak lebih. Sempat dua kali lipat, dan kepalanya
    # melorot lepas dari badan: bahu menyembul di satu sisi tanpa leher, dan
    # sisi lain kepalanya terpotong tepi bingkai.
    lebih = (1 if condong > 0 else -1) if condong else 0
    tempel(kanvas, kepala, x_tengah - len(kepala[0]) // 2 + condong + lebih,
           kepala_y)
    return kanvas


def buat(nama):
    bagian = TOKOH[nama]
    sheet = Image.new("RGBA", (LEBAR * KOLOM, TINGGI * len(URUTAN)), (0, 0, 0, 0))
    for baris, anim in enumerate(URUTAN):
        for kolom, pose in enumerate(POSE[anim]):
            kanvas = susun(bagian, pose)
            bingkai = Image.new("RGBA", (LEBAR, TINGGI), (0, 0, 0, 0))
            bingkai.putdata([c for row in kanvas for c in row])
            sheet.paste(bingkai, (kolom * LEBAR, baris * TINGGI))
    keluar = pathlib.Path(f"/Users/jepa/giftcard/static/img/render/8bit-{nama}.png")
    keluar.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(keluar)
    return keluar, sheet.size


if __name__ == "__main__":
    for nama in TOKOH:
        p, ukuran = buat(nama)
        print(f"{p.name}  {ukuran[0]}x{ukuran[1]}  {p.stat().st_size // 1024} KB")
    print("baris:", ", ".join(f"{i}={a}({len(POSE[a])})" for i, a in enumerate(URUTAN)))
