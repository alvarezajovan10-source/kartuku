"""Tag untuk template render kartu.

Dua alat utama:
  {% t card "cover_title" %}     → isi teks (pilihan user, atau bawaan template)
  {% ed editing "cover_title" %} → atribut data-edit, hanya saat mode edit

Dengan ini penulis template tidak perlu tahu apa pun soal cara penyimpanan.
"""

from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
def get(mapping, key):
    """Ambil nilai dari dict dengan kunci dinamis: {{ frame_photos|get:frame.key }}."""
    if hasattr(mapping, "get"):
        return mapping.get(key)
    return None


@register.simple_tag
def t(card, key):
    """Isi teks untuk sebuah kunci. Di-escape otomatis oleh Django."""
    return card.text(key)


@register.simple_tag
def ed(editing, key):
    """`data-edit="<key>"` saat mode edit, kosong saat kartu asli.

    format_html meng-escape key, jadi kunci aneh tidak bisa menyuntik atribut.
    """
    if not editing:
        return ""
    return format_html(' data-edit="{}"', key)


@register.simple_tag
def frame_attr(editing, key):
    """`data-frame="<key>"` saat mode edit."""
    if not editing:
        return ""
    return format_html(' data-frame="{}"', key)


@register.simple_tag
def surface(card, key, fallback):
    """Warna permukaan: pilihan user kalau ada, kalau tidak bawaan template."""
    return card.style_clean()["colors"].get(key, fallback)
