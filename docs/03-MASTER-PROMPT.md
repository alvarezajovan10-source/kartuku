# Master Prompt — Kartuku

> Salin **seluruh blok di bawah ini** (dari `---` sampai `---`) dan tempel sebagai
> system prompt / konteks awal ke AI mana pun (Claude, ChatGPT, Gemini) yang akan
> mengerjakan proyek ini. Isi bagian `[TULISKAN TASK SPESIFIK DI SINI]` di akhir.

---

Kamu mengerjakan **Kartuku** (repo: `~/giftcard`), situs pembuatan kartu ucapan
digital berbayar. Pembeli mengisi foto, pesan, dan lagu YouTube ke dalam template,
membayar Rp15.000 sekali, lalu mendapat **link permanen** untuk dibagikan. Mayoritas
pembeli datang dari TikTok dan membuka situs dari HP. Bahasa situs & kode: **Indonesia**.

## Tech stack

Django 5.2 + DRF 3.16 (Python 3.12) · SQLite dev / PostgreSQL prod via `DATABASE_URL` ·
WhiteNoise · django-environ · Pillow · qrcode · django-storages+boto3 (Cloudflare R2,
di balik flag `USE_R2`, saat ini mati) · gunicorn.
Frontend: Django templates + Alpine.js (vendored). **Tanpa build step** — tidak ada
`package.json`, `node_modules`, atau bundler. CSS ditulis tangan.
Venv dibuat dengan **`uv`** — pasang paket dengan `uv pip install`, jalankan lewat
`.venv/bin/python manage.py …`.

## Struktur

```
config/     settings.py (satu berkas, cabang `if not DEBUG`), urls.py
cards/      app utama — models, views (894 baris), api.py, api_photos.py,
            forms.py, styles.py, utils.py, signals.py, templatetags/,
            templates/cards/render/ (renderer kartu), tests/ (10 berkas)
payments/   dua gateway — lynk.py (AKTIF), midtrans.py (kode lengkap, TIDUR),
            services.py, webhooks.py, models.py, tests/ (2 berkas)
templates/  base.html   static/  css + js   tools/  skrip deploy
docs/       dokumentasi (kamu ada di sini)
```

Model: `Template`, `GiftCard` (PK UUID, 27 kolom), `GiftPhoto`, `AccessCode`,
`LynkOrder`, `PaymentEvent`.

## Aturan yang TIDAK boleh dilanggar

1. **Status `paid` hanya lahir dari bukti terverifikasi**: webhook bertanda tangan
   sah, `LynkOrder.claim()`, `AccessCode.claim()`, atau `mark_paid` oleh staff.
   Jangan pernah percaya parameter dari browser.
2. **`verify_signature` wajib `return False` kalau kuncinya kosong** — konfigurasi
   yang belum lengkap harus MENOLAK, bukan meloloskan.
3. **Webhook selalu balas `200` untuk event yang sudah ditangani** (termasuk duplikat
   dan yang sengaja diabaikan) supaya gateway berhenti retry. `403` hanya untuk
   tanda tangan yang tidak cocok.
4. **Nilai gaya dari user WAJIB lewat `cards.styles.sanitize_style()`** sebelum masuk
   CSS. Yang tidak cocok daftar putih dibuang, bukan diperbaiki.
5. **Rute `<str:ref>/` di `cards/urls.py` harus tetap yang TERAKHIR.** Apa pun di
   bawahnya tidak akan pernah tercapai. Rute `/g/<ref>/` tidak boleh dihapus — link
   itu sudah terlanjur dibagikan.
6. **Di jalur editor, pakai `save(update_fields=[…])`, jangan `card.save()` polos.**
   Save polos bisa menimpa status `paid` kembali jadi `pending`.
7. **Kartu berstatus `paid` tidak pernah dihapus.** `purge_drafts` hanya menyentuh
   draft/expired/pending.
8. **`select_for_update()` tidak dipakai untuk klaim** — SQLite mengabaikan row-lock
   diam-diam. Pakai conditional UPDATE.
9. **Jangan tambah `from payments… import …` ke `cards/models.py`** — itu yang menjaga
   graf import tetap asiklik.

## Konvensi proyek

- **Komentar & docstring bahasa Indonesia, menjelaskan KENAPA bukan APA.** Banyak
  komentar mencatat bug nyata yang pernah terjadi. Baca sebelum "merapikan".
- **`{% comment %}…{% endcomment %}`, jangan `{# … #}` multi-baris** — sintaks pendek
  hanya berlaku satu baris; sisanya tercetak ke halaman. Sudah bocor 4×.
- **`{% static_v 'js/x.js' %}`, bukan `{% static %}`** — cache-busting lewat `?v=mtime`.
- **Docstring test menjelaskan bug nyatanya**, bukan mekanisme test-nya.
- Commit: bahasa Indonesia, deskriptif, ~50–75 karakter, menjelaskan **dampak**
  ("Pembeli yang kehilangan sesinya bisa mengambil kartunya lagi"). Tanpa prefix
  conventional-commits. Satu branch `main`.
- Tidak ada linter/formatter/CI. Konvensi dijaga lewat test dan review.
- Menambah teks yang bisa diedit user = **nol baris Python** — cukup entri di
  `Template.config["texts"]` + `{% t card "key" %}` di template render.

## Jebakan lingkungan

- **Buka `http://localhost:8000`, JANGAN `127.0.0.1`.** YouTube menolak memutar
  video dari alamat IP mentah. Ini pernah memakan waktu sehari penuh.
- **Setelah mengubah `.env`, wajib restart penuh**:
  `launchctl kickstart -k gui/$UID/com.kartuku.server`. Autoreload Django hanya
  memantau `.py` dan mewarisi environment lama.
- Log ada di `~/giftcard/server.log`.
- `CLAUDE.md` di root adalah blueprint lama — §5 (Data Model) dan §10 (API Endpoints)
  **sudah usang**. Yang benar ada di `docs/01-PROJECT-BIBLE.md`.

## Sebelum mengerjakan apa pun

**Sebelum mengerjakan task apa pun, baca dulu `docs/01-PROJECT-BIBLE.md` dan
`docs/02-TECHNICAL-DOCUMENTATION.md` untuk detail lebih lanjut.** Bible memuat skema
database lengkap, 30 rute, dan diagram alur; Technical Documentation memuat graf
import, protokol editor↔iframe, panduan menambah fitur, dan tabel gejala→penyebab
untuk debugging. Kalau menambah fitur besar, **wajib** perbarui kedua dokumen itu
di commit yang sama.

---

## Task

[TULISKAN TASK SPESIFIK DI SINI]

---
