# Kartu Ucapan Digital

Blueprint & aturan arsitektur ada di [CLAUDE.md](CLAUDE.md). File ini cuma cara menjalankan.

## Jalankan (dev)

```bash
cd ~/giftcard
source .venv/bin/activate
cp .env.example .env          # sudah dibuat; isi kunci Midtrans sandbox
python manage.py migrate
python manage.py seed_templates
python manage.py createsuperuser
python manage.py runserver
```

Buka http://127.0.0.1:8000/ — admin di `/admin/`.

DB dev = SQLite (`db.sqlite3`). Untuk Postgres, isi `DATABASE_URL` di `.env`.
Foto dev disimpan di `media/`; set `USE_R2=True` + kredensial R2 untuk pakai Cloudflare.

## Tes

```bash
python manage.py test
```

Fokus tes: verifikasi signature, idempotency webhook, gating halaman publik,
ekstraksi ID YouTube.

## Uji webhook Midtrans sandbox

Midtrans harus bisa menjangkau localhost, jadi pakai tunnel:

```bash
cloudflared tunnel --url http://localhost:8000
```

Lalu:
1. Tambahkan host tunnel ke `ALLOWED_HOSTS` dan `CSRF_TRUSTED_ORIGINS` di `.env`.
2. Di dashboard Midtrans sandbox → Settings → Configuration, set
   **Payment Notification URL** ke `https://<host-tunnel>/api/webhooks/midtrans/`.
3. Buat kartu → halaman bayar → scan QR pakai Simulator QRIS Midtrans sandbox.

## Menambah template baru

Alur di situs: landing → `/template/<kategori>/` (galeri) → `/preview/<slug>/` → `/create/<slug>/`.

1. **Buat file render** di `cards/templates/cards/render/<nama>.html`.
   Halaman berdiri sendiri (bukan `{% extends %}`), dan **wajib** diakhiri dengan
   `{% include "cards/_preview_bar.html" %}` tepat sebelum `</body>` — tanpa itu,
   halaman preview tidak menandai dirinya sebagai contoh.

   **Kalau template ingin bisa diatur user** (font/warna/ukuran/perataan), baca
   nilainya dari CSS custom property, jangan tulis warna langsung:

   ```css
   .judul {
     font-family: var(--title-font);
     color: var(--title-color);
     text-align: var(--title-align);
     font-size: calc(3rem * var(--title-size));
   }
   ```

   Variabel yang di-set server: `--bg`, `--accent`, dan untuk tiap slot
   (`title`, `message`, `signature`): `--<slot>-font`, `-color`, `-size`, `-align`.
   Server memasangnya lewat `{{ card.style_css }}` di elemen pembungkus.
   Editor menimpa variabel yang sama lewat Alpine, jadi preview dan kartu asli
   selalu sama. Contohnya ada di `cards/render/_kanvas_body.html` + `static/css/kanvas.css`.

   Daftar font, palet, dan batas ukuran ada di `cards/styles.py`. Nilai apa pun
   dari user **selalu** disaring `sanitize_style()` sebelum masuk CSS — jangan
   pernah melewatinya, itu yang menahan injeksi CSS.

   Variabel yang tersedia:

   | Variabel | Isi |
   |---|---|
   | `card.recipient_name`, `card.sender_name`, `card.message` | teks dari pengirim |
   | `card.favorite_flower` | nama bunga (boleh kosong) |
   | `affirmations` | list kalimat, maksimal 4 |
   | `card.youtube_video_id`, `card.youtube_embed_url` | video (boleh kosong) |
   | `photos` | list foto; tiap item punya `.image.url` dan `.caption` |

   Bungkus tiap bagian dengan `{% if %}` — pengirim boleh mengosongkan foto,
   video, atau bunga, dan template tidak boleh menyisakan kotak kosong.

2. **Daftarkan templatenya** lewat `/admin/cards/template/` atau tambahkan ke
   `SEEDS` di `cards/management/commands/seed_templates.py`:

   ```python
   ("pastel-manis", "Pastel Manis", CardType.BIRTHDAY,
    {"accent": "#e8a0b0", "renderer": "pastel"}),
   ```

   `renderer` menunjuk ke nama file di langkah 1. Tanpa `renderer`, template
   memakai tampilan sederhana `cards/public.html`.

3. **Thumbnail galeri** (opsional): taruh `static/img/thumb/<slug>.jpg`.
   Tanpa file itu, galeri memakai gradasi warna `accent` + nama template.

4. Cek hasilnya di `/preview/<slug>/` sebelum diaktifkan.

## Perintah manajemen

- `python manage.py seed_templates` — isi/segarkan template awal (idempoten).
- `python manage.py make_sample_photos [--force]` — buat foto contoh untuk preview.
- `python manage.py purge_drafts --hours 24 [--dry-run]` — bersihkan draft basi.

## Status

Fase 1–3 selesai (fondasi, pembayaran QRIS + webhook, halaman publik).
Berikutnya: Fase 4 (banyak template + polish UI) dan Fase 5 (produksi).
