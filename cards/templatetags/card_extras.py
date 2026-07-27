"""Tag untuk template render kartu.

Penulis template cukup tahu tiga tag:

  {% el card editing "cover_title" %}  → atribut elemen (data-edit + gaya user)
  {% t  card "cover_title" %}          → isi teksnya
  {% bg card editing "cover_bg" %}     → atribut permukaan/latar yang bisa diklik

Sisanya (penyimpanan, pembersihan, editor) tidak perlu dipikirkan.
"""

from django import template
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
    css = styles.element_css((card.style or {}).get("elements", {}).get(key, {}))
    out = ""
    if editing:
        out += format_html(' data-edit="{}"', key)
    if css:
        out += format_html(' style="{}"', css)
    return mark_safe(out)


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
    css = styles.element_css((card.style or {}).get("elements", {}).get(key, {}))
    out = ""
    if editing:
        out += format_html(' data-frame="{}"', key)
    if css:
        out += format_html(' style="{}"', css)
    return mark_safe(out)


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


@register.filter
def split(value, sep=","):
    return str(value).split(sep)
