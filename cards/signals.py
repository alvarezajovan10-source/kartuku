"""Pembersih berkas foto yang tertinggal di storage.

`FileField` Django TIDAK menghapus berkas fisiknya sendiri saat baris database
dihapus. Sebelum ada modul ini, berkas hanya terhapus di tiga tempat yang
memanggilnya secara eksplisit (ganti foto di slot, endpoint hapus foto, dan
perintah purge_drafts). Semua jalur lain — hapus lewat admin, cascade dari
GiftCard, atau `.delete()` pada queryset — meninggalkan berkas yatim yang tidak
pernah bisa ditemukan lagi, tapi tetap memakan kuota disk.

Itulah kebocoran penyimpanan yang sebenarnya: bukan foto kartu lunas (yang
memang harus disimpan selamanya), melainkan sisa yang tidak terlacak.
"""

import logging

from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import GiftPhoto

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=GiftPhoto)
def hapus_berkas_foto(sender, instance, **kwargs):
    """Hapus berkas fisiknya begitu barisnya hilang, lewat jalur apa pun.

    `save=False` wajib: barisnya sudah tidak ada, menyimpannya kembali akan
    membuat baris baru. Kegagalan dicatat tapi tidak dilempar — berkas yang
    gagal dihapus tidak boleh menggagalkan penghapusan kartu.
    """
    if not instance.image:
        return
    try:
        instance.image.delete(save=False)
    except Exception as exc:  # storage bisa apa saja (lokal, S3/R2)
        logger.warning("Gagal menghapus berkas %s: %s", instance.image.name, exc)
