"""Tulis cards/templates/cards/render/bdaymag.html dari koordinat Canva.

    python3 tools/buat_html_bdaymag.py          # (Pillow perlu untuk polaroid hal 8)

JANGAN sunting bdaymag.html langsung: berkas itu KELUARAN skrip ini. Hampir
seratus kotak di dalamnya diturunkan dari tools/bdaymag/canva_struktur.json
(read-design Canva), dan menyalinnya dengan tangan pasti meleset — sedangkan
pelat gambarnya (tools/buat_pelat_bdaymag.py) diturunkan dari desain yang
sama persis. Kotak foto dan lubang pelatnya HARUS dari sumber yang sama.

Juga mencetak tools/bdaymag/seed_config.json: daftar "frames" dan "texts"
untuk entri "birthday-magazine" di seed_templates.py.

Satuan: halaman Canva 793,5 x 1123 px (separuh hamparan 1587 px), halaman
kanonis kartu 390 x 551,6 px. Posisi ditulis dalam PERSEN halaman, ukuran
huruf dalam px kanonis (= px Canva x 390/793,5).
"""
import json
import math
import os
import re
import sys

AKAR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAHAN = os.path.join(AKAR, "tools", "bdaymag")
sys.path.insert(0, BAHAN)
import spek  # noqa: E402

SEPARUH = 1587 / 2
TINGGI = 1123
SKALA = 390 / SEPARUH
KELUARAN = os.path.join(AKAR, "cards", "templates", "cards", "render", "bdaymag.html")


def pct(v):
    return f"{v:.3f}".rstrip("0").rstrip(".") + "%"


def angka(v, n=3):
    return f"{v:.{n}f}".rstrip("0").rstrip(".")


def muat():
    with open(os.path.join(BAHAN, "canva_struktur.json")) as f:
        d = json.load(f)
    return d.get("design_content", d)["pages"]


def sisi_dan_x(e):
    """Halaman tempat elemen duduk (dari titik tengahnya) dan x lokalnya."""
    tengah = e["left"] + e["width"] / 2
    if tengah < SEPARUH:
        return "kiri", e["left"]
    return "kanan", e["left"] - SEPARUH


def kotak_jalur(e):
    """Kotak klip foto (pecahan 0..1 dari kotak elemen), dari path bentuknya.

    Bingkai foto Canva bisa berupa persegi penuh ("M0 0H64V64H0z") atau
    persegi yang menjorok ke dalam ("M12.5 12.5H286v330.2H12.5z" pada
    viewBox 298.5x355.2 — bingkai bawaan berbingkai tipis). Jalur lengkung
    (oval cermin halaman 9) tidak diurai: kotaknya dipakai utuh, dan bentuk
    ovalnya datang dari lubang di pelat.
    """
    vb = e.get("viewBox") or {}
    jalur = None
    for pa in e.get("paths", []):
        isi = pa.get("fill", {})
        if "media" in isi or (isi.get("isMediaReplaceable") and "color" not in isi):
            jalur = pa["d"]
    if not jalur or not vb or re.search(r"[cCsSaAqQtT]", jalur):
        return (0, 0, 1, 1)
    xs, ys, x, y = [], [], 0.0, 0.0
    for perintah, isi in re.findall(r"([MLHVZmlhvz])([^MLHVZmlhvz]*)", jalur):
        n = [float(t) for t in re.findall(r"-?\d*\.?\d+(?:e-?\d+)?", isi)]
        if perintah in "ML":
            x, y = n[0], n[1]
        elif perintah == "H":
            x = n[0]
        elif perintah == "V":
            y = n[0]
        elif perintah == "h":
            x += n[0]
        elif perintah == "v":
            y += n[0]
        elif perintah in "ml":
            x, y = x + n[0], y + n[1]
        else:
            continue
        xs.append(x)
        ys.append(y)
    w, h = vb["width"], vb["height"]
    return (min(xs) / w, min(ys) / h, max(xs) / w, max(ys) / h)


def kotak_polaroid(e, halaman_n):
    """Bidang foto di dalam polaroid grup halaman 8, diukur dari ekspor PNG.

    Ketiga polaroid itu satu grup yang tidak bisa dibaca read-design
    ("unsupported"), jadi tidak ada kotak foto di datanya. Bidangnya dicari
    di ekspor 2x Canva: piksel bersaturasi (langit biru & bukit hijau gambar
    pengisi) di dalam kotak elemen, diputar balik ke sumbu elemen. Bingkai
    polaroid putih/kelabu dan bayangannya bersaturasi rendah, jadi tidak ikut.
    """
    from PIL import Image
    im = Image.open(os.path.join(BAHAN, "asli", f"hal{halaman_n}.png")).convert("RGB")
    px = im.load()
    cx, cy = e["left"] + e["width"] / 2, e["top"] + e["height"] / 2
    sudut = math.radians(-e["rotation"])
    cos, sin = math.cos(sudut), math.sin(sudut)
    r = math.hypot(e["width"], e["height"]) / 2
    lx, ly = [], []
    for Y in range(int((cy - r) * 2), int((cy + r) * 2)):
        for X in range(int((cx - r) * 2), int((cx + r) * 2)):
            if not (0 <= X < im.width and 0 <= Y < im.height):
                continue
            rr, gg, bb = px[X, Y]
            mx, mn = max(rr, gg, bb), min(rr, gg, bb)
            if mx < 40 or (mx - mn) / mx < 0.18:
                continue
            dx, dy = X / 2 - cx, Y / 2 - cy
            ux, uy = dx * cos - dy * sin, dx * sin + dy * cos
            if abs(ux) <= e["width"] / 2 and abs(uy) <= e["height"] / 2:
                lx.append(ux + e["width"] / 2)
                ly.append(uy + e["height"] / 2)
    tepi = 1.0   # px Canva: tutup sisa antialias tepi langit
    return ((min(lx) - tepi) / e["width"], (min(ly) - tepi) / e["height"],
            (max(lx) + tepi) / e["width"], (max(ly) + tepi) / e["height"])


def html_foto(e, kunci, opsi, n):
    sisi, x = sisi_dan_x(e)
    f0x, f0y, f1x, f1y = kotak_polaroid(e, n) if opsi.get("polaroid") else kotak_jalur(e)
    # Kotak foto sesungguhnya (sebelum diputar), dalam px Canva lokal halaman.
    gx, gy = x + f0x * e["width"], e["top"] + f0y * e["height"]
    gw, gh = (f1x - f0x) * e["width"], (f1y - f0y) * e["height"]
    gaya = (f"--x:{pct(gx / SEPARUH * 100)};--y:{pct(gy / TINGGI * 100)};"
            f"--w:{pct(gw / SEPARUH * 100)};--h:{pct(gh / TINGGI * 100)}")
    if abs(e["rotation"]) > 0.05:
        gaya += f";--r:{angka(e['rotation'], 2)}deg"
    kelas = ("bingkai" + (" di-atas" if opsi.get("polaroid") else "") + (" gelap" if opsi.get("gelap") else "")
             + (" latar" if opsi.get("latar") else ""))
    rasio = round(gw / gh, 3)
    # Posisi di .slot, BUKAN di .bingkai: di kartu terbit {% frame %} menulis
    # atribut style sendiri (zoom & geser foto pilihan pembeli), dan elemen
    # yang punya dua atribut style membuang yang kedua — crop pembeli lenyap
    # diam-diam di kartu yang sudah dibayar.
    return sisi, rasio, f'''    {{% with photo=frame_photos|get:"{kunci}" %}}
    <div class="slot" style="{gaya}">
      <div class="{kelas}{{% if editing and not photo %}} is-empty{{% endif %}}" {{% frame card editing "{kunci}" %}}>
        <span class="gbr">{{% if photo %}}<img src="{{{{ photo.image.url }}}}" alt="">{{% endif %}}</span>
        {{% if editing %}}<span class="ketuk"></span>{{% endif %}}
      </div>
    </div>
    {{% endwith %}}'''


def bersihkan(teks):
    # Spasi sebelum ganti baris dan baris kosong di ujung adalah sisa
    # penyuntingan di Canva, bukan bagian desain.
    teks = re.sub(r"[ \t]+\n", "\n", teks).strip("\n")
    return teks.rstrip()


# Tinggi baris PERTAMA kotak teks Canva, dalam kali ukuran huruf. Diukur
# dari data desain ini sendiri: kotak teks Canva setinggi
#   (jumlah baris - 1) x line-height + m
# dan m-nya hampir tetap ~1,2 untuk semua font (median per font di bawah).
# CSS tidak bekerja begitu — tiap baris setinggi line-height penuh — jadi
# .tx diberi margin negatif (m - line-height)/2 di atas dan bawah (lihat
# bdaymag.css). Tanpa itu teks bawaan satu baris berukuran besar ("22",
# huruf 100 px, line-height 1,4) terukur 140 px di kotak 122 px, dan
# pengecil otomatis mengecilkan teks yang sebenarnya pas.
TINGGI_BARIS_PERTAMA = 1.2


def tinggi_baris_pertama(halaman):
    per_font = {}
    for hal in halaman:
        for e in hal["elements"]:
            if e["type"] != "text":
                continue
            f = e["textRegions"][0]["formatting"]
            baris = "".join(r["characters"] for r in e["textRegions"]).rstrip("\n").count("\n") + 1
            m = e["height"] / f["fontSize"] - (baris - 1) * f["lineHeight"]
            if 0.8 < m < 1.8:
                per_font.setdefault(f["fontRef"], []).append(m)
    return {k: sorted(v)[len(v) // 2] for k, v in per_font.items()}


def html_teks(e, kunci, bawaan_baru, m_font, pengirim=False):
    sisi, x = sisi_dan_x(e)
    f = e["textRegions"][0]["formatting"]
    kelas, keluarga, _ = spek.FONT_ELEMEN.get(e["id"]) or spek.FONT[f["fontRef"]]
    bawaan = bersihkan(bawaan_baru or "".join(r["characters"] for r in e["textRegions"]))
    # Bellefair cuma punya satu ketebalan; "bold" Canva untuk The Seasons
    # dibiarkan 400 — tebal palsu buatan browser merusak kontras serifnya.
    tebal = {"bold": {"seasons": 400}.get(kelas, 700)}.get(f["fontWeight"], 400)
    # Tulisan tangan (FONT_ELEMEN): di desainnya satu judul memakai dua font
    # dengan ketebalan berbeda ("The Editors" tebal + "Notes" tipis). Dalam
    # satu font tangan itu terbaca sebagai salah ketik — judul (huruf Canva
    # >= 30 px) semuanya tebal, isi semuanya biasa.
    if kelas == "tangan":
        tebal = 700 if f["fontSize"] >= 30 else 400
    rata = {"start": "left", "end": "right"}.get(f["textAlign"], f["textAlign"])
    # "BIRTHDAY / EDITION" sampul: baris pertama rata kanan-kiri, baris
    # terakhir rata kanan. Di CSS baris terakhir justify jatuh ke KIRI, jadi
    # kotaknya dibuat rata kanan seperti yang terlihat di desainnya.
    akhir = e["textRegions"][-1]["formatting"]["textAlign"]
    if rata == "justify" and len(e["textRegions"]) > 1 and akhir == "end":
        rata = "right"
    lebar = e["width"]
    # Teks SATU baris: kotak Canva selebar tintanya persis, jadi beda
    # pembulatan sepersekian piksel di Chrome mematahkannya jadi dua baris.
    # Dilonggarkan 4% ke arah yang tidak mengubah letak tintanya.
    satu_baris = "\n" not in bawaan and e["height"] / f["fontSize"] < f["lineHeight"] + 0.3
    if satu_baris and rata != "justify":
        tambah = lebar * 0.04
        if rata == "center":
            x -= tambah / 2
        elif rata == "right":
            x -= tambah
        lebar += tambah
    m = m_font.get(f["fontRef"], TINGGI_BARIS_PERTAMA)
    sesuai = spek.SESUAI_ELEMEN.get(e["id"], {})
    lebar *= sesuai.get("lebar", 1)
    tinggi = e["height"] / TINGGI * 100
    if "bawah" in sesuai:
        tinggi = min(tinggi, sesuai["bawah"] - e["top"] / TINGGI * 100)
    gaya = (f"--x:{pct(x / SEPARUH * 100 + sesuai.get('geser', 0))};--y:{pct(e['top'] / TINGGI * 100)};"
            f"--w:{pct(lebar / SEPARUH * 100)};--h:{pct(tinggi)};"
            f"--d-s:{angka(f['fontSize'] * SKALA * sesuai.get('huruf', 1), 2)}px;--d-l:{angka(f['lineHeight'], 2)};--d-m:{angka(m, 3)};"
            f"--d-k:{angka(f['letterSpacing'] + spek.SPASI_PENGGANTI.get(f['fontRef'], 0), 3)}em;--d-a:{rata};--d-w:{tebal};"
            f"--d-c:{f['color']}" + (";--d-i:italic" if f["fontStyle"] == "italic" else ""))
    if pengirim:
        isi = ('<p class="tx f-{k}"{{% el card editing "sender" %}}{{% if editing %}} data-placeholder="Namamu"'
               '{{% endif %}}>{{{{ card.sender_name|default:"{b}" }}}}</p>').format(k=kelas, b=bawaan)
    else:
        isi = f'<p class="tx f-{kelas}"{{% el card editing "{kunci}" %}}>{{% t card "{kunci}" %}}</p>'
    kelas_kotak = ("kotak-tx" + (" ketat" if "bawah" in sesuai else "")
                   + (" boleh-gulir" if sesuai.get("gulir") else ""))
    return sisi, bawaan, f'    <div class="{kelas_kotak}" style="{gaya}">{isi}</div>'


def main():
    halaman = muat()
    m_font = tinggi_baris_pertama(halaman)
    foto = {i: (k, l, o) for i, k, l, o in spek.FOTO}
    teks = {i: (k, l, b) for i, k, l, b in spek.TEKS}
    frames, texts, bagian = [], [], []
    terpakai = set()

    for n, hal in enumerate(halaman, 1):
        isi = {"kiri": {"foto": [], "teks": []}, "kanan": {"foto": [], "teks": []}}
        for e in hal["elements"]:
            if e["id"] in foto:
                k, label, opsi = foto[e["id"]]
                sisi, rasio, h = html_foto(e, k, opsi, n)
                isi[sisi]["foto"].append(h)
                frames.append({"key": k, "label": label, "area": spek.SCENE[n], "rasio": rasio,
                               **({"asli": True} if opsi.get("asli") else {})})
                terpakai.add(e["id"])
            elif e["id"] in teks:
                k, label, baru = teks[e["id"]]
                sisi, bawaan, h = html_teks(e, k, baru, m_font)
                isi[sisi]["teks"].append(h)
                texts.append({"key": k, "label": label, "default": bawaan})
                terpakai.add(e["id"])
            elif e["id"] == spek.PENGIRIM:
                sisi, _, h = html_teks(e, "sender", None, m_font, pengirim=True)
                isi[sisi]["teks"].append(h)
                terpakai.add(e["id"])
        bagian.append((n, isi))

    hilang = ({i for i, *_ in spek.FOTO} | {i for i, *_ in spek.TEKS} | {spek.PENGIRIM}) - terpakai
    if hilang:
        sys.exit(f"Id di spek.py tidak ada di desain: {sorted(hilang)}")

    potongan = []
    for n, isi in bagian:
        sid = spek.SCENE[n]
        aktif = " active" if n == 1 else ""
        potongan.append(f"\n  <!-- ═══════════ HAMPARAN {n} ═══════════ -->")
        potongan.append(f'  <section class="scene{aktif}" id="{sid}">')
        for sisi in ("kiri", "kanan"):
            if n == 1 and sisi == "kiri":
                potongan.append('    <div class="hal kiri meja" aria-hidden="true"></div>')
                continue
            potongan.append(f'    <div class="hal {sisi}">')
            potongan.extend(isi[sisi]["foto"])
            pelat = f"s{n}{'k' if sisi == 'kiri' else 'n'}"
            potongan.append(f'''    <div class="pelat" style="--pelat:url('{{% static_v 'img/bdaymag/{pelat}.webp' %}}')"></div>''')
            potongan.extend(isi[sisi]["teks"])
            potongan.append("    </div>")
        potongan.append("  </section>")

    with open(os.path.join(BAHAN, "kerangka.html")) as f:
        kerangka = f.read()
    keluaran = kerangka.replace("{# ISI_HAMPARAN #}", "\n".join(potongan))
    with open(KELUARAN, "w") as f:
        f.write(keluaran)
    with open(os.path.join(BAHAN, "seed_config.json"), "w") as f:
        json.dump({"frames": frames, "texts": texts}, f, ensure_ascii=False, indent=1)
    print(f"{os.path.relpath(KELUARAN, AKAR)}: {len(frames)} bingkai, {len(texts)} teks")


if __name__ == "__main__":
    main()
