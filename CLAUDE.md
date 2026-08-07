# CLAUDE.md — Kartu Ucapan Digital (Working Title)

Blueprint proyek untuk website pembuatan kartu ucapan/hadiah digital berbayar,
dengan pembayaran QRIS otomatis. Dokumen ini adalah sumber kebenaran arsitektur.
Ikuti keputusan yang sudah dikunci di bawah — jangan diubah tanpa alasan eksplisit.

---

## 1. Tujuan Produk

Pasangan membuat kartu digital (Birthday, Anniversary, Love Story, Proposal),
mengisi teks + foto + link YouTube ke dalam template, membayar Rp15.000 lewat
QRIS, lalu mendapat **link publik unik** yang bisa dibagikan ke pasangannya.

Kartu hanya bisa diakses versi final-nya **setelah pembayaran terkonfirmasi**.

---

## 2. Keputusan yang Dikunci (JANGAN diubah)

- **Harga flat Rp15.000** untuk semua template. Tidak ada tier harga.
- **Tidak ada upload video.** Video = embed link YouTube. Simpan hanya `video_id`,
  render lewat iframe `youtube-nocookie.com/embed/<id>`. Validasi & ekstrak ID dari
  URL yang ditempel user.
  > **Ditunda, bukan ditolak (2026-07-29).** Ide "pesan video di akhir kartu"
  > disetujui secara konsep, tapi ditahan sampai pindah ke VPS/hosting berbayar.
  > Penghalangnya bukan biaya penyimpanan (R2 murah), melainkan: paket gratis
  > hanya 512 MB disk, dan video HP berformat HEVC/`.mov` tidak bisa diputar
  > Chrome/Firefox tanpa dikonversi `ffmpeg` — yang butuh CPU dan proses latar
  > belakang. Syarat sebelum dibangun: sudah di VPS, simpan di R2, batas 30
  > detik / 25 MB, konversi otomatis ke H.264. Jalur murah untuk menguji minat
  > lebih dulu: kolom YouTube kedua (unlisted) khusus pesan video penutup.
- **Tidak ada iklan** di seluruh situs. Ini produk emosional/estetik; iklan merusak
  brand dan konversi.
- **Foto boleh di-upload**, tapi dibatasi (lihat §7). Simpan di object storage
  (Cloudflare R2), bukan di server.
- **Sumber kebenaran status pembayaran = webhook gateway.** Frontend TIDAK PERNAH
  boleh membuka kartu final berdasarkan tebakan sisi klien.

---

## 3. Tech Stack

- Backend: **Django 5 + Django REST Framework** (Python 3.12)
- DB: **PostgreSQL**
- Object storage: **Cloudflare R2** (S3-compatible; egress gratis) via `django-storages` + `boto3`
- Payment gateway: **Midtrans** (Core API, metode QRIS)
- Frontend: Django templates + HTMX/Alpine.js untuk polling status (cukup, tanpa SPA)
  — atau React terpisah jika kamu mau; blueprint ini asumsikan server-rendered.
- Deploy: VPS (gunicorn + nginx), sertifikat Let's Encrypt

---

## 4. User Journey

1. User pilih tipe kartu / template → halaman editor.
2. User isi konten (nama, pesan, foto, link YT) → **simpan draft** (`status=draft`).
3. User klik "Bayar Rp15.000".
4. Backend `create charge` ke Midtrans (QRIS, amount 15000, order_id = kode kartu).
   → dapat QR string/URL → tampilkan ke user.
5. Halaman pembayaran **polling** `GET /api/cards/<uuid>/status/` tiap 3–5 detik.
6. User scan QRIS dengan e-wallet / m-banking apa pun.
7. Midtrans kirim **webhook** ke `/api/webhooks/midtrans/` → verifikasi signature →
   set `status=paid`, isi `paid_at`.
8. Polling mendeteksi `paid` → redirect ke halaman sukses + tampilkan link publik
   `/g/<uuid>`.
9. Link publik render kartu final (bisa dibuka berkali-kali oleh penerima).

---

## 5. Data Model (Django)

```python
class Template(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CARD_TYPES)  # birthday/anniversary/love_story/proposal
    config = models.JSONField(default=dict)   # layout, warna, field yang tersedia
    is_active = models.BooleanField(default=True)


class GiftCard(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft"
        PENDING = "pending"     # QR sudah dibuat, menunggu bayar
        PAID = "paid"
        EXPIRED = "expired"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)  # dipakai jadi slug URL publik
    template = models.ForeignKey(Template, on_delete=models.PROTECT)
    category = models.CharField(max_length=20, choices=CARD_TYPES)

    sender_name = models.CharField(max_length=80, blank=True)
    recipient_name = models.CharField(max_length=80, blank=True)
    message = models.TextField(blank=True)
    youtube_video_id = models.CharField(max_length=20, blank=True)  # ID saja, bukan URL penuh

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    amount = models.PositiveIntegerField(default=15000)

    # Payment tracking
    gateway_order_id = models.CharField(max_length=64, blank=True, db_index=True)  # order_id dikirim ke Midtrans
    gateway_txn_id = models.CharField(max_length=64, blank=True)                   # transaction_id dari Midtrans
    paid_at = models.DateTimeField(null=True, blank=True)
    qr_expires_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class GiftPhoto(models.Model):
    card = models.ForeignKey(GiftCard, related_name="photos", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="cards/%Y/%m/")  # ke R2 via django-storages
    order = models.PositiveSmallIntegerField(default=0)


class PaymentEvent(models.Model):
    """Log tiap webhook masuk — untuk idempotency & audit."""
    card = models.ForeignKey(GiftCard, on_delete=models.CASCADE, related_name="events")
    gateway_txn_id = models.CharField(max_length=64, db_index=True)
    transaction_status = models.CharField(max_length=30)
    raw_payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # cegah proses dobel dari webhook yang dikirim berkali-kali
        unique_together = ("gateway_txn_id", "transaction_status")
```

---

## 6. Integrasi Pembayaran (Midtrans QRIS) — INTI SISTEM

### 6.1 Buat transaksi (create charge)

Saat user klik bayar, panggil Midtrans **Core API `/v2/charge`** dengan
`payment_type = "qris"`:

- `order_id` = string unik, mis. `CARD-<uuid-pendek>-<timestamp>`. Simpan ke
  `gateway_order_id`. **Satu order_id per percobaan bayar** (jika user bayar ulang
  setelah expired, buat order_id baru).
- `gross_amount` = 15000.
- Respons berisi `actions` dengan URL gambar QR / `qr_string`. Tampilkan QR ini.
- Set `status = pending` dan `qr_expires_at` (mis. now + 15 menit).

### 6.2 Webhook / Notification handler — WAJIB BENAR

Endpoint: `POST /api/webhooks/midtrans/` (CSRF exempt, tapi tetap terverifikasi).

Langkah wajib, berurutan:

1. **Verifikasi signature.** Midtrans mengirim `signature_key`. Hitung ulang:
   `SHA512(order_id + status_code + gross_amount + ServerKey)`.
   Kalau tidak cocok → **tolak 403, jangan proses.** Ini mencegah orang memalsukan
   "sudah bayar".
2. **Idempotency.** Sebelum memproses, cek `PaymentEvent` — kalau
   `(gateway_txn_id, transaction_status)` sudah ada, balas `200 OK` dan berhenti.
   Webhook bisa dikirim berkali-kali; jangan sampai dobel proses.
3. **Cari GiftCard** lewat `gateway_order_id`. Kalau tidak ada → log & `200 OK`.
4. **Petakan status Midtrans:**
   - `settlement` atau `capture` (fraud_status `accept`) → `status = paid`,
     isi `paid_at`, `gateway_txn_id`.
   - `pending` → biarkan `pending`.
   - `expire` / `cancel` / `deny` → `status = expired`.
5. Simpan `PaymentEvent`. Balas `200 OK` (selalu 200 untuk event yang sudah dihandle,
   supaya Midtrans berhenti retry).

> **Aturan emas:** kartu final HANYA dibuka jika `GiftCard.status == "paid"` di DB.
> Jangan pernah percaya parameter dari redirect browser.

### 6.3 Status endpoint (untuk polling frontend)

`GET /api/cards/<uuid>/status/` → `{ "status": "pending" | "paid" | "expired" }`.
Frontend polling ini; begitu `paid`, redirect ke `/g/<uuid>`.

---

## 7. Aturan Keamanan & Batasan

- **Foto:** maksimal N foto/kartu (mis. 5), ukuran ≤ 3MB, hanya `jpg/png/webp`.
  Validasi MIME sesungguhnya (bukan cuma ekstensi). Kompres/resize sebelum simpan.
- **YouTube:** ekstrak & simpan `video_id` saja. Regex terhadap format
  `youtube.com/watch?v=`, `youtu.be/`, `youtube.com/shorts/`. Tolak yang tidak valid.
  Render lewat `youtube-nocookie.com/embed/<id>`.
- **URL publik pakai UUID**, bukan ID increment — supaya tidak bisa ditebak/di-enumerate.
- **Rate limit** endpoint create-charge & upload untuk cegah abuse.
- **Webhook**: CSRF-exempt tapi signature-verified. Jangan pernah lewatkan verifikasi.
- Draft yang tidak dibayar > 24 jam → boleh dibersihkan (management command / cron).

---

## 8. Struktur Direktori (usulan)

```
project/
├── config/                 # settings, urls, wsgi
├── cards/                  # app utama
│   ├── models.py
│   ├── views.py            # editor, halaman bayar, halaman publik
│   ├── api.py              # status endpoint (DRF)
│   ├── templates_engine.py # render config template -> HTML
│   └── templates/
├── payments/               # app pembayaran
│   ├── midtrans.py         # client: create_charge(), verify_signature()
│   ├── webhooks.py         # handler notification
│   └── models.py           # PaymentEvent (atau taruh di cards)
├── templates/              # HTML global
├── static/
└── CLAUDE.md
```

---

## 9. Environment Variables

```
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
ALLOWED_HOSTS=

DATABASE_URL=postgres://...

# Midtrans
MIDTRANS_SERVER_KEY=
MIDTRANS_CLIENT_KEY=
MIDTRANS_IS_PRODUCTION=False      # True saat live
MIDTRANS_MERCHANT_ID=

# Cloudflare R2
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET_NAME=
R2_PUBLIC_URL=
```

---

## 10. API Endpoints

| Method | Path | Fungsi |
|---|---|---|
| GET | `/` | Landing + pilih template |
| GET/POST | `/create/<template_slug>/` | Editor & simpan draft |
| POST | `/api/cards/<uuid>/pay/` | Create charge Midtrans → balas QR |
| GET | `/api/cards/<uuid>/status/` | Polling status pembayaran |
| POST | `/api/webhooks/midtrans/` | Notification handler (signature-verified) |
| GET | `/g/<uuid>/` | Halaman kartu publik (hanya render penuh jika `paid`) |

---

## 11. Fase Build (kerjakan berurutan)

**Fase 1 — Fondasi:** setup Django, PostgreSQL, model `Template` & `GiftCard`,
1 template hardcoded, editor sederhana yang menyimpan draft. Belum ada bayar.

**Fase 2 — Pembayaran (paling kritis):** integrasi Midtrans sandbox — create charge
QRIS, tampilkan QR, webhook handler + verifikasi signature + idempotency, status
polling. Uji sampai alur draft→pending→paid mulus di sandbox.

**Fase 3 — Halaman publik:** render kartu final di `/g/<uuid>` (gated by `paid`),
embed YouTube, tampilkan foto & pesan. Preview terkunci sebelum bayar.

**Fase 4 — Konten & polish:** beberapa template per kategori, upload+resize foto ke
R2, validasi input, desain UI.

**Fase 5 — Produksi:** ganti Midtrans ke production, set webhook URL production,
deploy VPS + nginx + SSL, cron pembersih draft, rate limiting.

---

## 12. Gotchas / Edge Cases

- **QR expired:** user buka halaman lama → cek `qr_expires_at`; jika lewat, tawarkan
  buat QR baru (order_id baru).
- **Webhook telat/duluan:** kadang webhook datang sebelum respons charge selesai
  diproses. Pastikan `gateway_order_id` sudah tersimpan sebelum menampilkan QR.
- **Double payment:** idempotency via `PaymentEvent.unique_together` menahan ini.
- **User tutup tab setelah bayar:** status tetap `paid` di DB; mereka bisa buka
  ulang `/g/<uuid>` kapan saja. Simpan/kirim link-nya (mis. tampilkan + opsi salin).
- **Testing webhook lokal:** pakai tunnel (mis. `cloudflared`/`ngrok`) supaya
  Midtrans sandbox bisa menjangkau localhost.
- **Minimum transaksi & kategori merchant:** konfirmasi ke Midtrans bahwa 15.000 di
  atas minimum, dan cek kategori MDR-mu saat pendaftaran (mikro ≤500k bisa 0%).
```

---

## 13. Status Saat Ini (29 Juli 2026)

Ringkasan untuk sesi berikutnya. Perbarui bagian ini kalau keadaannya berubah.

### Sudah jadi

- **Musik latar** di semua template (`cards/_bgm.html`) — lagu YouTube diputar
  lewat IFrame Player API resmi, ada tombol putar/jeda mengambang. Spotify
  ditolak di editor karena tidak bisa diputar otomatis.
- **Validasi lagu**: `check_youtube_embeddable()` pakai YouTube Data API +
  uji putar sungguhan di browser dari editor (`probeSong` di alpine-editor.js).
  Keduanya perlu, karena API mengatakan `embeddable: True` untuk video yang
  ternyata diblokir label musik.
- **Halaman informasi terpisah**: `/template/`, `/cara-kerja/`, `/harga/`,
  `/testimoni/`, `/faq/`.
- **Dashboard pemilik** `/kartu-saya/` — daftar semua kartu + link. Terbuka saat
  `DEBUG`, atau untuk staff.
- **Kode akses sekali pakai** (`AccessCode`) — pengganti Midtrans selama bayar
  ditangani di luar situs. Buat lewat admin atau `manage.py buat_kode`.
  Ditukar di halaman bayar; blok QRIS otomatis disembunyikan kalau
  `MIDTRANS_SERVER_KEY` kosong.
- **Slug bentrok** tidak lagi ditolak — diberi akhiran acak (`halo-k3f`).
  Akhirannya acak, bukan berurutan, supaya kartu orang lain tidak bisa
  di-enumerate.
- **`DEPLOY.md`** — panduan deploy ke PythonAnywhere gratis.
- **Situs sudah TAYANG** di `kartuku.pythonanywhere.com`. Deploy dijalankan
  `python3 tools/pa.py --deploy` (pull + migrate + collectstatic + reload).
  **`--deploy` TIDAK menjalankan `seed_templates`.** Tiap kali daftar teks
  atau bingkai template berubah, jalankan sendiri sesudahnya:
  `python3 tools/pa.py "cd ~/giftcard && /home/kartuku/.virtualenvs/kartuku/bin/python manage.py seed_templates"`
  — tanpa itu produksi masih memakai config lama dan template baru tidak
  pernah muncul.
- **Template Game 8-Bit** (5 Agu 2026) — kartu MENDATAR 16:9 pertama
  (`data-stage="lebar"`), 8 babak, dua karakter piksel yang berjalan
  menemani penerima, babak tiup lilin, dan ubin Momen yang bisa dibalik ke
  keterangan fotonya. Lembar sprite & simbol kue adalah keluaran
  `tools/buat_sprite_8bit.py` dan `tools/buat_kue_8bit.py` — jangan sunting
  PNG-nya langsung. Skrip pemeriksa di `tools/cek_*.js` (perlu
  `NODE_PATH` ke node_modules berisi puppeteer-core).
  > **Latarnya gambar unduhan, bukan buatan sendiri.** Risiko hak ciptanya
  > diangkat sebelum deploy dan pemilik situs memilih tetap memakainya.
  > Versi latar gambar-sendiri ada di branch `template-8bit` (tertinggal
  > jauh). Jangan angkat lagi sebagai risiko baru — sudah diputuskan.

### Sedang berjalan

1. **Webhook Lynk.id** — Lynk punya webhook (Settings → Integrations → Webhook).
   Rencana: Lynk memberi tahu situs saat ada order → situs membuat `AccessCode`
   → email otomatis ke pembeli. **Butuh situs online lebih dulu.**
   Langkah berikutnya: tangkap contoh payload pakai webhook.site + tombol
   "Test URL" di Lynk, baru tulis handler-nya. Wajib ada verifikasi keamanan
   seperti aturan webhook Midtrans di §6.2. Situsnya sekarang SUDAH online,
   jadi penghalangnya hilang.
2. **Jualan lewat TikTok → Lynk.id.** Midtrans sengaja ditunda.

### Jebakan lingkungan — mahal kalau lupa

- **Buka situs lewat `http://localhost:8000`, JANGAN `127.0.0.1`.** YouTube
  menolak memutar video kalau halaman diakses lewat alamat IP mentah
  (`127.0.0.1`, `192.168.x.x`). Nama host seperti `localhost`, `*.local`, dan
  domain publik diterima. Ini pernah memakan waktu sehari penuh untuk ketemu.
- **`SECURE_REFERRER_POLICY`** harus `strict-origin-when-cross-origin`. Bawaan
  Django (`same-origin`) membuat pemutar YouTube gagal dengan "Error 153".
- **Setelah mengubah `.env`, wajib restart penuh**:
  `launchctl kickstart -k gui/$UID/com.kartuku.server`. Autoreload Django
  hanya memantau file `.py` dan mewarisi environment lama.
- **Server dijalankan `launchd`** (`~/Library/LaunchAgents/com.kartuku.server.plist`),
  otomatis menyala saat login. Log di `~/giftcard/server.log`.
- **Venv dibuat dengan `uv`**, tanpa `pip` bawaan. Pasang paket:
  `uv pip install <nama>`. Jalankan: `.venv/bin/python manage.py ...`
