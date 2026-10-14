"""Peta desain Canva "magazine template 1" -> template Birthday Magazine.

Satu-satunya tempat yang menentukan elemen Canva mana yang jadi teks atau
foto yang bisa disunting pembeli. Dibaca oleh:

  tools/buat_pelat_bdaymag.py   — teks di TEKS dicabut dari pelat, sisanya
                                  dibiarkan menyatu dengan gambarnya;
  tools/buat_html_bdaymag.py    — menulis render/bdaymag.html dan potongan
                                  seed_templates.py dari koordinat Canva.

Kunci elemen ("LB...") adalah id elemen Canva dari canva_struktur.json
(keluaran read-design). Id itu bertahan selama desainnya tidak dibuat ulang.

TEKS yang TIDAK ada di sini sengaja dibiarkan di pelat dengan huruf Canva
aslinya: judul rubrik (CONTENTS, WHO'S THAT GIRL?, Her iconic moments, ...),
angka besar Things She Loves, dan "Love you". (Masthead sampul BIRTHDAY /
MAGAZINE dulu juga di sini; sejak 11 Okt 2026 jadi teks sunting.)
Fontnya berbayar (The Seasons, Copperplate Gothic, La Luxes, Mak, Bodoni FLF)
dan lisensinya cuma berlaku di dalam Canva — memasangnya di situs tidak boleh,
dan padanan bebasnya tidak secantik aslinya.
"""

# Hamparan (spread) Canva ke-n -> id scene di HTML. BUKAN "sp1..sp9" seperti
# Majalah Cinta: label tab hamparan di editor (SCENE_LABELS di
# alpine-editor.js) dikunci id, untuk SEMUA template sekaligus — id yang sama
# membuat template ini ikut berlabel "Love Note", "First Impression", dst.
SCENE = {n: f"bm{n}" for n in range(1, 10)}

# Font Canva -> font bebas yang dipasang di situs. Montserrat, Poppins, Be
# Vietnam, Pinyon Script, dan Playfair Display memang font Google, jadi
# hurufnya sama persis. Yang ditandai "PENGGANTI" adalah font berbayar.
FONT = {
    # PENGGANTI TheSeasons-Bd. Dipilih dengan MENGUKUR lebar baris teks sampul
    # di Chrome terhadap tinta di ekspor Canva (rata-rata 4 teks): Bellefair
    # 1,016; Marcellus 1,017; Playfair 1,043; Bodoni Moda 400 1,124 (dipakai
    # pertama dan membuat teks bawaan sampul ikut dikecilkan ke 0,88).
    # Bellefair juga padanan BostonAngel di Valentine Story.
    "YAFdJnPX3ZE,0": ("seasons", "'Bellefair', Georgia, serif", 400),
    "YAFdJjbTu24,1": ("poppins", "'Poppins', sans-serif", 400),
    "YAFdtQi73Xs,0": ("montserrat", "'Montserrat', sans-serif", 400),
    "YAFdJvSWHmc,0": ("vietnam", "'Be Vietnam Pro', sans-serif", 400),
    "YAFdJhem5V8,1": ("playfair", "'Playfair Display', serif", 400),
    "YAFcfknkruY,0": ("edwardian", "'Pinyon Script', cursive", 400),          # PENGGANTI ITC Edwardian Script
    "YACgEQzTJgs,0": ("pinyon", "'Pinyon Script', cursive", 400),
    # PENGGANTI Copperplate Gothic ("MAGAZINE" di bawah masthead sampul).
    "YAFcfoWfqbc,1": ("magazine", "'Cinzel', serif", 400),
    "YAD87jbyiH0,0": ("ttd", "'Allura', cursive", 400),                     # PENGGANTI Amsterdam-Four (sama dengan Valentine Story)
}

# Jarak huruf TAMBAHAN (em) untuk pengganti yang jauh lebih sempit dari
# aslinya. Copperplate Gothic sangat lebar: tinta "MAGAZINE" di ekspor Canva
# 6,39 x ukuran huruf, Cinzel 5,51 (diukur 11 Okt 2026; Tenor Sans 5,84,
# Josefin Sans 5,56, Marcellus SC 5,26 — semuanya sempit). Selisihnya dibagi
# rata ke 8 huruf = 0,11 em.
SPASI_PENGGANTI = {"YAFcfoWfqbc,1": 0.11}

# (id elemen, kunci, label editor, teks bawaan yang DIPERBAIKI kalau perlu)
# Bawaan None = pakai teks Canva apa adanya.
TEKS = [
    # ── 1. Sampul ──
    ("LBfBZszdnY413RlB", "cover_kicker", "Judul kecil sampul", None),
    ("LBp22SfGBwXwkGJf", "cover_age", "Umur", None),
    ("LB6Tv3vf2SpnykXP", "cover_name", "Nama di sampul", None),
    ("LBR0WFjhjqFn79Hv", "cover_tag", "Kalimat sampul", None),
    # Empat teks sampul ini DULU sengaja di pelat (huruf Canva asli). Sejak
    # 11 Okt 2026 bisa disunting atas permintaan pemilik situs — semua teks
    # di halaman awal harus bisa diganti pembeli.
    ("LBYgNjBMmpwFBXqn", "cover_masthead", "Judul besar sampul", None),
    ("LBM2WSvpLcSSGlPP", "cover_magazine", "Tulisan di bawah judul", None),
    ("LB3vf2mDv2t6FqXD", "cover_edition", "Edisi di sampul", None),
    ("LBXVL3QZ8Qy8cKZ8", "cover_hbd", "Ucapan di sampul", None),
    # ── 3. Editor's Notes ──
    # Judul "The Editors Notes" dicabut dari pelat 11 Okt 2026 supaya bisa
    # bertulisan tangan (lihat FONT_ELEMEN).
    ("LBr4mNq4v6RJ0CL4", "editor_title", "Judul Editor's Notes", None),
    ("LBjXQM6YHgfCvJc2", "editor_title2", "Judul Editor's Notes — kata kedua", None),
    ("LBNP0h6Q0MBlghPN", "editor_note", "Catatan editor", None),
    # ── 4. Who's That Girl ──
    ("LBS3JG1LbZN7tNJ6", "girl_body", "Cerita Who's That Girl", None),
    # ── 5. Our Journey ──
    ("LBx1fMNmm4FQYm6x", "j1_title", "Perjalanan 1 — judul", None),
    ("LBDcXS9LmP8CCnRm", "j1_body", "Perjalanan 1 — cerita", None),
    ("LB1HbtD4kBdbSr85", "j2_title", "Perjalanan 2 — judul", None),
    ("LBJBlX2xcxVdmZZP", "j2_body", "Perjalanan 2 — cerita", None),
    ("LBctHV8HCywBXm0z", "j3_title", "Perjalanan 3 — judul", None),
    ("LBlkCTMyhCl6jJLk", "j3_body", "Perjalanan 3 — cerita", None),
    ("LBcRRByYDdvs225M", "j4_title", "Perjalanan 4 — judul", None),
    ("LBBRqD5qBGZxxLJr", "j4_body", "Perjalanan 4 — cerita", None),
    # ── 6. Her Iconic Moments ──
    ("LBCCPxS7d4BXc56H", "m1_cap", "Momen 1 — keterangan", None),
    ("LBW2D0sbFHtyk7dx", "m2_cap", "Momen 2 — keterangan", None),
    ("LBcg0yMF8WvGz5nf", "m3_cap", "Momen 3 — keterangan", "Walking pinterest board"),
    ("LBYnQsm8HtDpS2WL", "m4_cap", "Momen 4 — keterangan", None),
    ("LB0NSKTg51K9xTNp", "m5_cap", "Momen 5 — keterangan", None),
    ("LBBCxVQbpjQWZF09", "m6_cap", "Momen 6 — keterangan", None),
    # ── 7. Playlist ──
    ("LBv64gQZzZnCY5P0", "playlist_name", "Nama di judul playlist", None),
    ("LBYXqCyWk0crcPjT", "playlist_word", "Judul playlist — kata kedua", None),
    ("LB4M9rvcL3qRg3XG", "s1_title", "Lagu 1 — judul", None),
    ("LB08j8ZhRVpN5ZlM", "s1_artist", "Lagu 1 — penyanyi", None),
    ("LBPDvSgPjwSb0y1Q", "s2_title", "Lagu 2 — judul", None),
    ("LBJqPjCKk8Nq5T4G", "s2_artist", "Lagu 2 — penyanyi", None),
    ("LBZK8H7XG78SjsMf", "s3_title", "Lagu 3 — judul", "Damned"),
    ("LBcCS1V5G7WDzMmx", "s3_artist", "Lagu 3 — penyanyi", None),
    # ── 8. Things She Loves ──
    ("LBLLQ7sltcR0cKJ6", "l1_title", "Kesukaan 1 — judul", None),
    ("LBrfv52Hvp2xy9jG", "l1_body", "Kesukaan 1 — cerita", "Her daily ritual, her comfort, her little moment of peace in a busy world."),
    ("LBtV2zG8TzmNXnjw", "l2_title", "Kesukaan 2 — judul", None),
    ("LBPyVX46StzS89Y6", "l2_body", "Kesukaan 2 — cerita", None),
    ("LBwzN0695yR10tJN", "l3_title", "Kesukaan 3 — judul", None),
    ("LBCR3d1sh3mjpB95", "l3_body", "Kesukaan 3 — cerita", None),
    ("LBycrJjLmWRxtWC9", "l4_title", "Kesukaan 4 — judul", None),
    ("LBf7Bd9z9M4l0t96", "l4_body", "Kesukaan 4 — cerita", None),
    ("LBLTwNrJRFgTfqXl", "l5_title", "Kesukaan 5 — judul", None),
    ("LBZ24mcLFHLtkZGV", "l5_body", "Kesukaan 5 — cerita", None),
    ("LBvLDM3D2cK64v48", "l6_title", "Kesukaan 6 — judul", None),
    ("LBTmn81tvN6SwKvQ", "l6_body", "Kesukaan 6 — cerita", None),
    ("LB0gnyg89Jmj31mK", "l7_title", "Kesukaan 7 — judul", None),
    ("LBbl2jjY461T6Nw5", "l7_body", "Kesukaan 7 — cerita", "Escaping reality and feeling everything a little deeper."),
    ("LBwPl8HDCDymBV3m", "l8_title", "Kesukaan 8 — judul", None),
    ("LBbsYD7Pt2bXZQPD", "l8_body", "Kesukaan 8 — cerita", "Because life is always better with a little sugar."),
    ("LBWmnVqZPtHQBLcS", "l9_title", "Kesukaan 9 — judul", None),
    ("LB9CPdCxgYrJMcL8", "l9_body", "Kesukaan 9 — cerita", None),
    ("LBC34gWfWCQSWB57", "l10_title", "Kesukaan 10 — judul", None),
    ("LBGqJp24r0wC7fRm", "l10_body", "Kesukaan 10 — cerita", None),
    # ── 9. Surat ──
    ("LBzcW6KLvjGysTVf", "letter_title", "Judul surat", "A Letter to Keelya"),
    ("LBWHsxl0HqGW1T2F", "letter_body", "Isi surat", None),
    ("LBmrRcb6j7B8p4N3", "letter_close", "Salam penutup", None),
]

# Font yang dipaksakan per ELEMEN, menimpa pemetaan FONT di atas. Halaman 17
# (surat) seluruhnya tulisan tangan Indie Flower atas permintaan pemilik situs
# (11 Okt 2026, contoh gambarnya "JarvisHand" — bukan font sungguhan; Indie
# Flower padanan terdekat dari 16 font tangan Google yang dibandingkan:
# garis tipis rata, tegak, "a" & "g" satu tingkat, spasi lega).
TANGAN = ("tangan", "'Indie Flower', cursive", 400)
FONT_ELEMEN = {
    "LBzcW6KLvjGysTVf": TANGAN,   # judul surat
    "LBWHsxl0HqGW1T2F": TANGAN,   # isi surat
    "LBmrRcb6j7B8p4N3": TANGAN,   # salam penutup
    "LBTVHxlMHrC1gfS2": TANGAN,   # tanda tangan (nama pengirim)
    # Judul hal 4 & hal 13 ikut tulisan tangan (permintaan yang sama).
    "LBr4mNq4v6RJ0CL4": TANGAN,   # "The Editors"
    "LBjXQM6YHgfCvJc2": TANGAN,   # "Notes"
    "LBv64gQZzZnCY5P0": TANGAN,   # "Keelya's"
    "LBYXqCyWk0crcPjT": TANGAN,   # "Playlist"
}

# Penyesuaian kotak per elemen akibat font pengganti.
#   "huruf": pengali ukuran huruf;  "bawah": batas bawah kotak (persen tinggi
#   halaman) — kotaknya juga jadi "ketat": tanpa kelonggaran 4% pengecil
#   otomatis, karena tepat di bawahnya ada teks lain. Isi surat: kotak Canva-nya memanjang sampai 88,8% — MENIMPA
#   "With love, always." (86,3%) dan tanda tangan. Tak terlihat selama hurufnya
#   Pinyon yang ramping; Indie Flower jauh lebih lebar dan barisnya turun ke
#   salam penutup. Kotak dihentikan di 85,4% dan huruf x0,92 supaya surat
#   bawaan muat tanpa dikecilkan; surat pembeli yang lebih panjang dikecilkan
#   --muat di dalam kotak itu, jadi tidak pernah menabrak penutupnya.
SESUAI_ELEMEN = {
    #   "gulir": huruf hanya boleh mengecil sampai 80%; kalau masih kepanjangan,
    #   kotaknya bisa digulir. Surat pembeli boleh sampai 3.000 karakter
    #   (MAX_TEXT_LENGTH) — dikecilkan terus sampai muat, hurufnya jatuh ke
    #   ~7 px dan tidak terbaca di HP (14 Okt 2026).
    "LBWHsxl0HqGW1T2F": {"huruf": 0.92, "bawah": 85.4, "gulir": True},
    # "Notes" (hal 4): kotak Canva selebar tinta huruf skrip yang ramping;
    # dalam Indie Flower kata itu dikecilkan ke 0,89 dan jadi lebih kecil
    # daripada "The Editors" di sebelahnya. Dilebarkan ke kanan (ruang kosong).
    #   "lebar": pengali lebar kotak.
    "LBjXQM6YHgfCvJc2": {"lebar": 1.5},
    # "Keelya's" (hal 12): dalam Indie Flower kata ini menempel ke "Playlist".
    #   "geser": geser mendatar, persen lebar halaman (negatif = ke kiri).
    "LBv64gQZzZnCY5P0": {"geser": -3},
}

# Tanda tangan di bawah surat = nama pengirim kartu (card.sender_name),
# bukan teks template — sama seperti Majalah Cinta.
PENGIRIM = "LBTVHxlMHrC1gfS2"

# (id elemen, kunci, label editor, opsi tambahan)
FOTO = [
    ("LBrrThKXRvQQMDnj", "f_sampul", "Foto sampul", {"asli": True, "gelap": True}),
    ("LBqpVxH2pBy38rzb", "f_isi1", "Daftar isi — foto 1", {}),
    ("LBgKFJBmK2jqjQyS", "f_isi2", "Daftar isi — foto 2", {}),
    ("LBZD4SHyH2JJCvhj", "f_isi3", "Daftar isi — foto 3", {}),
    ("LB2wPNDmm6hrsHWH", "f_isi4", "Daftar isi — foto 4", {}),
    ("LBZ5GSP8D2P05fs7", "f_editor", "Foto Editor's Notes", {}),
    ("LBR5pP3Cmz8MMvcl", "f_cheers", "Polaroid Cheers", {}),
    ("LB21XgfbX2c0QtkC", "f_girl", "Potret Who's That Girl", {"asli": True}),
    ("LB3RPd4sXwzcSTT7", "f_girl1", "Galeri dia — besar 1", {}),
    ("LB9yYBlxqDbSRHGL", "f_girl2", "Galeri dia — besar 2", {}),
    ("LB5g8NyJws1CV7fd", "f_girl3", "Galeri dia — besar 3", {}),
    ("LB09P5q4lfssSJG9", "f_girl4", "Galeri dia — kecil 1", {}),
    ("LBH8kSZYy8TVXs9T", "f_girl5", "Galeri dia — kecil 2", {}),
    ("LB50vmYPnm7QLYGQ", "f_girl6", "Galeri dia — kecil 3", {}),
    ("LBW4f1M8444VyzKx", "f_girl7", "Galeri dia — kecil 4", {}),
    ("LB0Kss1kLTZy3vV7", "f_j1", "Polaroid perjalanan 1", {}),
    ("LBBspsv68Kc2pKBC", "f_j2", "Polaroid perjalanan 2", {}),
    ("LBhc9bZhN6Y3ykVp", "f_j3", "Polaroid perjalanan 3", {}),
    ("LBXbxysRyXPmPXPl", "f_j4", "Polaroid perjalanan 4", {}),
    ("LBt4XdPXWfWxD9Sg", "f_j5", "Polaroid perjalanan 5", {}),
    ("LBmbcNZBHGT48LSg", "f_j6", "Polaroid perjalanan 6", {}),
    ("LBkF8knyWh0rrrf1", "f_m1", "Momen 1", {}),
    ("LBVj20X7BW8QLJB6", "f_m2", "Momen 2", {}),
    ("LBSNGfhVPKjlllm4", "f_m3", "Momen 3", {}),
    ("LBH3qDyQBVyLDNTX", "f_m4", "Momen 4", {}),
    ("LBpTH9xVtdHYGgXB", "f_m5", "Momen 5", {}),
    ("LBrMrhjB7rTW1pWn", "f_m6", "Momen 6", {}),
    ("LBpkD93Ttm3hCPKY", "f_love1", "Foto besar Love (atas)", {"gelap": True}),
    ("LB0lJnJJ3FrcSl4F", "f_love2", "Foto besar You (bawah)", {"gelap": True}),
    ("LB77Q7w69PGL28TM", "f_lagu", "Sampul lagu di pemutar", {}),
    ("LB47bwbz9swvw853", "f_lagu_latar", "Latar halaman playlist", {"asli": True, "gelap": True, "latar": True}),
    ("LBLL9DwYq02V0J0N", "f_lagu1", "Sampul lagu 1", {}),
    ("LB0ZYl4F9Ss25x9J", "f_lagu2", "Sampul lagu 2", {}),
    ("LB6WBm2w52GGRknR", "f_lagu3", "Sampul lagu 3", {}),
    ("LB5BYcK0jX4DvnCz", "f_suka1", "Kesukaan — foto 1", {}),
    ("LBd1Hp5TPWBkp6D8", "f_suka2", "Kesukaan — foto 2", {}),
    ("LBkC4QHCpSSgnDbx", "f_suka3", "Kesukaan — foto 3", {}),
    ("LB61Pzs8zS4f1sqv", "f_suka4", "Kesukaan — foto 4", {}),
    ("LBTjw3K0Vqd82sCn", "f_suka5", "Kesukaan — foto 5", {}),
    ("LBYqygTKPnNXblPb", "f_suka6", "Kesukaan — polaroid kiri", {"polaroid": True}),
    ("LBWJ78zpHy3khSXp", "f_suka7", "Kesukaan — polaroid tengah", {"polaroid": True}),
    ("LB7Q4bT3cpTQMhFg", "f_suka8", "Kesukaan — polaroid kanan", {"polaroid": True}),
    ("LBsNxD740zPJqx6f", "f_suka9", "Kesukaan — foto 9", {}),
    ("LBclh2qp69XGW8b1", "f_suka10", "Kesukaan — foto 10", {}),
    ("LBrCzhgXkNtZNhp8", "f_suka11", "Kesukaan — foto 11", {}),
    ("LB5C0F9jPKPLnm0c", "f_suka12", "Kesukaan — foto 12", {}),
    ("LBHq12lYM9PRL5Qs", "f_cermin", "Foto di cermin surat", {"oval": True}),
]
