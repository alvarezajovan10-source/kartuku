"""Tag untuk template render kartu.

Penulis template cukup tahu tiga tag:

  {% el card editing "cover_title" %}  → atribut elemen (data-edit + gaya user)
  {% t  card "cover_title" %}          → isi teksnya
  {% bg card editing "cover_bg" %}     → atribut permukaan/latar yang bisa diklik

Sisanya (penyimpanan, pembersihan, editor) tidak perlu dipikirkan.
"""

from django import template
from django.conf import settings
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from cards import styles

register = template.Library()


@register.filter
def get(mapping, key):
    """Ambil nilai dari dict dengan kunci dinamis: {{ frame_photos|get:frame.key }}."""
    if hasattr(mapping, "get"):
        return mapping.get(key)
    return None


@register.simple_tag
def el(card, editing, key):
    """Atribut untuk satu elemen: penanda edit + gaya pilihan user.

    Gaya diemit sebagai var lokal (--f, --fs, --c, ...) sehingga CSS template
    cukup menulis var(--f, <bawaan>) dan desain aslinya tetap utuh kalau user
    belum mengubah apa-apa.
    """
    if editing:
        # Saat mengedit, gaya diterapkan editor lewat stylesheet suntikan —
        # gaya inline dari server justru menimpanya dan membuat pilihan font
        # user "tidak berefek". Jadi inline hanya untuk kartu asli.
        return format_html(' data-edit="{}"', key)
    css = styles.element_css((card.style or {}).get("elements", {}).get(key, {}))
    return format_html(' style="{}"', css) if css else ""


@register.simple_tag
def bg(card, editing, key):
    """Dulu membuat latar bisa diklik; fitur ganti latar dihapus atas
    permintaan user (mengganggu, gampang salah klik). Tag dipertahankan agar
    template lama tidak rusak."""
    return ""


@register.simple_tag
def t(card, key):
    """Isi teks: pilihan user kalau ada, kalau tidak bawaan template."""
    return card.text(key)


@register.simple_tag
def frame(card, editing, key):
    """Atribut bingkai foto: penanda edit + gaya (bentuk sudut, cara mengisi)."""
    if editing:
        return format_html(' data-frame="{}"', key)
    css = styles.element_css((card.style or {}).get("elements", {}).get(key, {}))
    return format_html(' style="{}"', css) if css else ""


@register.simple_tag
def frames_in(card, area):
    """Bingkai foto untuk satu area saja.

    Ada karena bug nyata: bagian Surat dulu me-loop SEMUA bingkai, sehingga
    bingkai latar Ucapan ikut tampil di sana sebagai polaroid — foto yang
    ditaruh di situ malah jadi latar.
    """
    return [f for f in card.frames() if f.get("area", "") == area]


import os

from django.contrib.staticfiles import finders as _finders
from django.templatetags.static import static as _static


@register.simple_tag
def static_v(path):
    """URL static + penanda waktu ubah file (?v=mtime).

    Tanpa ini, browser memakai JS/CSS lama dari cache setelah file berubah —
    gejalanya editor 'kosong' atau berperilaku versi lama.
    """
    url = _static(path)
    found = _finders.find(path)
    if found:
        url += f"?v={int(os.path.getmtime(found))}"
    return url


@register.simple_tag
def static_ada(*paths):
    """URL static ber-versi untuk berkas yang BENAR-BENAR ada, dipisah "|".

    Bedanya dengan static_v: berkas yang tidak ditemukan tidak menghasilkan
    URL sama sekali, bukan URL yang nanti 404.

    Dipakai untuk aset pelengkap yang boleh belum dipasang — sekarang klip
    suara membalik halaman di kartu Valentine. Kalau URL-nya tetap
    diterbitkan, tiap pengunjung melihat baris 404 merah di console untuk
    berkas yang kita sendiri tahu belum ada, dan itu menutupi kesalahan
    sungguhan waktu sedang mencari masalah lain.

    Mengembalikan string kosong kalau tidak satu pun berkas ada; sisi JS
    membuang bagian kosong, jadi hasilnya "tidak ada suara berkas" dan
    kartunya jatuh ke suara sintetis.
    """
    ada = []
    for path in paths:
        found = _finders.find(path)
        if found:
            ada.append(f"{_static(path)}?v={int(os.path.getmtime(found))}")
    return "|".join(ada)


@register.filter
def split(value, sep=","):
    return str(value).split(sep)


@register.simple_tag
def harga_coret():
    """Harga normal untuk dicoret, atau 0 kalau tidak ada promo.

    Ada sebagai tag, bukan dikirim tiap view: kisi template dipakai lima
    halaman (beranda, /template/, galeri kategori, hasil cari, dan halaman
    produk), dan menambahkan satu nilai ke lima context adalah lima tempat
    yang bisa lupa. Yang lupa tidak akan error — kartunya cuma diam-diam
    kehilangan coretannya di satu halaman, dan tidak ada yang menyadarinya.

    Aturan "cuma tampil kalau memang lebih mahal" juga tinggal di sini, satu
    tempat. Lihat catatan hukum di CARD_LIST_PRICE pada settings.py.
    """
    normal = getattr(settings, "CARD_LIST_PRICE", 0)
    return normal if normal and normal > settings.CARD_PRICE else 0


@register.simple_tag
def potongan_persen():
    """Besar potongan dalam persen bulat, atau 0 kalau tidak ada promo.

    Dipakai lencana di sudut gambar. Dibulatkan, bukan dipotong: 82,9% yang
    ditulis "82%" mengecilkan tawaran sendiri tanpa alasan.
    """
    normal = harga_coret()
    if not normal:
        return 0
    return round(100 * (1 - settings.CARD_PRICE / normal))
