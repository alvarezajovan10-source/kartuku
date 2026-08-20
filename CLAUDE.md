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
- **Lapisan tema DILEWATI sementara** (19 Agu 2026, keputusan pemilik situs).
  Beranda dan `/template/` sekarang langsung menampilkan seluruh template
  aktif dalam satu kisi rata; tidak ada lagi kartu tema sebagai pintu masuk.

  > Alasannya aritmetika katalognya, bukan "biar sedikit klik": ada EMPAT
  > tema tapi cuma DUA yang berisi, dan isinya timpang — di produksi tiga
  > template di Birthday dan satu di Love Story. Jadi separuh pintu di
  > beranda buntu ("Coming soon", tidak bisa diklik), dan pintu yang hidup
  > pun membuka halaman berisi satu barang. Penyaring berguna kalau
  > pilihannya banyak; dengan tiga template ia bukan menyaring melainkan
  > menyembunyikan.
  >
  > **Rute `/template/<kategori>/` dan `_category_cards()` SENGAJA
  > DIBIARKAN HIDUP.** Tautan lama yang sudah tersebar tidak boleh mati, dan
  > lapisan temanya akan dikembalikan begitu minimal tiga tema terisi — biar
  > itu tinggal menyambung, bukan membangun ulang. `_category_cards()`
  > karena itu tidak dipanggil siapa pun untuk sementara; jangan dicabut
  > sebagai "kode mati".
  >
  > Nama tema pindah ke tiap kartu (`.tpl-tema`). Tanpa itu tidak ada lagi
  > yang memberi tahu pembeli bahwa Valentine Story kartu Love Story dan
  > bukan kartu ulang tahun.
  >
  > Markah kartunya diangkat jadi satu partial, `cards/_template_grid.html`,
  > dipakai BERTIGA — beranda, `/template/`, dan galeri per-tema — supaya
  > rupanya tidak bisa berbeda di antara ketiganya.
  >
  > **Belum ada satu pun gambar contoh.** `static/img/thumb/` tidak ada, jadi
  > yang tampil `.tpl-fallback`: nama template di atas warna aksennya.
  > Begitu `img/thumb/<slug>.jpg` ada, kartunya otomatis memakainya tanpa
  > menyentuh berkas mana pun. Ini pengungkit terbesar berikutnya untuk
  > halaman ini — pembeli sekarang masih harus mengklik untuk tahu wujud
  > kartunya.
  >
  > Dijaga `DaftarTemplateRataTests` di `cards/tests/test_page_hygiene.py`,
  > yang menggantikan `KategoriBelumJadiTests` — tes lama itu mengunci
  > perilaku sebaliknya (keempat tema selalu tampil, yang kosong ditandai
  > "Coming soon").
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
- **Halaman editor tanpa chrome situs** (19 Agu 2026, permintaan pemilik
  situs). Tiga hal dicabut/diperbesar; ketiganya soal jempol di HP.

  - **Header situs disembunyikan di SEMUA lebar**, bukan cuma >=941px.
    Ambang lama dipasang karena pemicunya dianggap tombol "Buat Kartu"
    (`.header-cta`), yang memang sudah `display:none` di bawah 941px. Yang
    luput: `.site-header` itu `position:sticky` + `z-index:50`, jadi pil
    putih "KARTUKU" MENGAMBANG menutupi bagian atas layar — dan di HP `.ed`
    memakai `column-reverse`, artinya yang duduk paling atas justru
    pratinjau kartunya.
    Pasangannya wajib: `.ed` sekarang `height:100vh` di aturannya sendiri.
    `calc(100vh - 72px)` yang lama menyisihkan ruang untuk header yang tidak
    pernah ada lagi, dan sisanya jadi pita kosong di bawah editor.
  - **Tautan "← Template lain" dicabut dari panel.** Ia duduk paling atas di
    `.ed-panel`, yaitu TEPAT DI BAWAH pratinjau di HP — persis di jalur
    jempol yang menggulir turun dari kartu ke kontrolnya.

    > **Ini membatalkan aturan lama "harus tetap ada jalan keluar di dalam
    > halaman".** Sekarang TIDAK ADA: satu-satunya jalan kembali adalah
    > tombol Back browser. Ongkos salah tekannya memang tidak nol — drafnya
    > tersimpan otomatis, tapi tidak ada jalan kembali ke draf itu (URL
    > editor tidak membawa `?card=`, `/kartu-saya/` tertutup untuk pembeli
    > biasa). Pemilik situs sudah diberi tahu dan tetap memilih mencabutnya.
    > Kalau suatu saat dipasang lagi, taruh di BAWAH tombol "Generate Link",
    > jangan di atas panel. Dijaga `test_tautan_keluar_dicabut_dari_panel`.

    Footer sengaja TIDAK ikut disembunyikan di HP: ia tidak mengambang,
    duduk setelah tombol "Generate Link", dan catatan pembayarannya berguna
    dibaca tepat sebelum tombol itu ditekan.
  - **Penggeser `.ed-slider` diperbesar** — keluhannya "bulatan zoom foto
    sering kali tidak tergeser di HP".

    > Yang menyelesaikannya BUKAN besar bulatannya, melainkan **kotak
    > sentuhnya**. Range bawaan cuma setinggi batangnya sendiri. Diukur A/B
    > di perender sungguhan, seret dimulai sekian piksel di atas garis
    > tengah: aturan lama (kotak 16px) sudah MELESET pada 12px, aturan baru
    > (kotak 44px) masih ikut pada 20px. Jatah melesetnya naik dari +-8px ke
    > +-22px. Bulatannya sendiri 22px + cincin putih 3px = 28px, terukur
    > dari piksel hasil render.
    >
    > Treknya sengaja dibuat setinggi kotaknya (44px) lalu batang 6px-nya
    > dicat sebagai background gradient yang dipusatkan. Cara yang lebih
    > lazim — trek setipis 6px lalu thumb digeser `margin-top` negatif —
    > bergantung pada apakah mesin render memusatkan kotak trek secara
    > vertikal, dan itu tidak sama di semua mesin.
    >
    > `-webkit-appearance:none` mematikan tampilan bawaan di WebKit/Blink
    > saja; pasangan `::-moz-range-*` WAJIB ikut ditulis, kalau tidak
    > Firefox menampilkan penggeser bawaannya yang kecil — bug yang sama,
    > hanya di browser lain.
    >
    > Aturan ini kena SEMUA penggeser di editor (jarak huruf, jarak baris,
    > sudut membulat), bukan cuma yang di modal crop. Itu disengaja: widget
    > dan masalahnya sama.

    Penjaganya `PenggeserSentuhTests` di `cards/tests/test_editor_ux.py`.

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
- **Template Valentine Story** (7 Agu 2026, kategori **Love Story**;
  diperbarui ke desain 11 halaman 11 Agu 2026) — majalah A4 **sebelas
  halaman** yang **dibalik lembar demi lembar dengan jari**.
  Stage baru `data-stage="buku"`: sama seperti "lebar", halamannya harus muat
  UTUH, hanya perbandingannya A4 (390 × 551,6). **DUA BELAS halaman sejak
  19 Agu 2026** — halaman 12 ditambahkan atas permintaan pemilik situs, lihat
  bloknya di bawah. **16 bingkai foto, 31 teks.**

  > Jumlah halaman TIDAK di-hardcode di mana pun: `valentine.js` menghitung
  > `document.querySelectorAll(".lembar")`, dan titik-titik penunjuk halaman
  > ikut dari situ. Menambah satu `<section class="scene lembar">` sudah cukup.

  Cara kerjanya beda sendiri dari template lain, dan ini WAJIB dipahami
  sebelum menyentuhnya:

  - **Halamannya bukan CSS, melainkan gambar.** Tiap halaman satu pelat WebP
    di `static/img/valentine/`, hasil ekspor Canva milik pemilik situs.
    Jangan sunting WebP-nya langsung; jalankan ulang skripnya. **Sumbernya
    tiga, dan tiap skrip cuma tahu miliknya sendiri:**

    | halaman | sumber | skrip |
    |---------|--------|-------|
    | 1-10 | `~/Downloads/LOVESTORY-2.pdf` | `tools/buat_pelat_valentine.py` |
    | 11 | `~/Downloads/LOVESTORY-4.pdf` | `tools/buat_pelat_hal11.py` |
    | 12 | PDF hati renda | `tools/buat_pelat_hal12.py` |

    > **Nomor `xref` gambar BERUBAH tiap ekspor ulang Canva.** Versi pertama
    > skrip itu menghafal `PENGISI = {1: [289], 4: [323], ...}`. Saat ekspor
    > kedua datang, foto sampul yang sama persis (md5 identik, posisi
    > identik) sudah bernomor 319 — dan nomor 289 masih ada di PDF-nya, jadi
    > skripnya TIDAK error, cuma melubangi gambar yang keliru. Sekarang
    > pengisi dikenali dari isinya (`PENGISI_UKURAN` 1438×560 untuk gambar
    > pengisi bawaan Canva, `PENGISI_SATU_SATUNYA` untuk sampul). Jangan
    > kembali ke daftar nomor.
  - **Teks yang bisa disunting DIHAPUS dari pelat**, lalu ditulis ulang
    sebagai HTML di koordinat yang sama. Yang sengaja dibiarkan menyatu
    dengan gambarnya — huruf Canva aslinya tetap utuh, tapi tidak bisa
    diubah pembeli: judul "Contents" (hal 3), angka kalender (hal 5), dan
    judul "THINGS I LOVE ABOUT YOU" (hal 10).

    > **ISI daftar isi hal 3 SEKARANG BISA DISUNTING** (19 Agu 2026,
    > permintaan pemilik situs; sebelumnya seluruh halaman itu menyatu dengan
    > pelat). Empat barisnya jadi teks HTML `isi1..isi4`; judul "Contents"
    > tetap gambar karena fontnya Brightwall 102pt, satu-satunya di halaman
    > itu dan tanpa padanan bebas.
    >
    > Baris kelima desainnya, "MUSIC ____ 11-12", **dicabut** — majalahnya
    > cuma 11 halaman, jadi halaman yang ditunjuknya tidak pernah ada.
    >
    > Dua jebakan yang sudah dibayar mahal, keduanya di
    > `tools/buat_pelat_valentine.py`:
    >
    > 1. **Redaksi membunuh span yang KOTAKNYA bersinggungan, bukan yang
    >    tintanya bertumpuk.** Kotak "Contents" menjulur ke bawah sampai
    >    y=395 mengikuti ekor sapuan huruf C-nya, dan kotak baris pertama
    >    daftar mulai di y=355 — jadi meredaksi baris pertama IKUT menghapus
    >    judulnya, tanpa error apa pun. Judulnya dikembalikan lewat
    >    `SELAMATKAN_TEKS`: dua render tambahan, dan piksel yang berbeda di
    >    antara keduanya ditempel balik. Tabrakan itu berlaku DUA ARAH, jadi
    >    pemulihannya WAJIB dibatasi kotak — tanpa itu baris pertama ikut
    >    hidup lagi sebagai potongan ("HE DAY WE MET___ 4"). Batasnya diukur:
    >    tinta judul berhenti di 340,3pt, tinta baris mulai 368,6pt.
    > 2. **Bulatan daftarnya VEKTOR, bukan teks** — redaksi teks tidak
    >    menyentuhnya, dan bulatan kelima tertinggal sendirian. Dicabut lewat
    >    `CABUT_VEKTOR`, dan HARUS dengan
    >    `PDF_REDACT_LINE_ART_REMOVE_IF_COVERED`. `IF_TOUCHED` akan ikut
    >    mencabut dua persegi latar sehalaman penuh dan mengosongkan seluruh
    >    halaman.
    >
    > Ukuran hurufnya **19,0px, hasil sapuan**, bukan 21,59px (= 33pt desain).
    > Bellefair merender 3-10% lebih lebar daripada BostonAngel-Light, dan
    > dari 20,2px ke atas baris terpanjang sudah dikecilkan `--muat` PADA
    > TEKS BAWAANNYA — nol kelonggaran begitu pembeli mengetik. Tabel
    > sapuannya ada di komentar `.t-isi` di valentine.css.
    Yang hal 10 bukan pilihan gaya melainkan keharusan: efek glow-nya sudah
    dibakar Canva jadi gambar. **Sudah diuji** — meredaksi objek teksnya
    tidak membuat hurufnya hilang sedikit pun; yang tersisa di PDF cuma
    lapisan teks tak terlihat. Satu-satunya cara mencabutnya adalah menimpa
    kelopak bunga dan sobekan koran di belakangnya. Jangan coba lagi.
  - **Halaman 10 & 11 (11 Agu 2026).** Hal 10 "Things I Love About You":
    empat elips merah muda yang di desainnya KOSONG — tidak ada contoh
    tulisan untuk ditiru. Teksnya karena itu **dipusatkan** di titik tengah
    elips (`data-tengah`, `.tx.t-love{transform:translateY(-50%)}`), bukan
    digantung pada garis alas seperti semua teks lain, karena di dalam oval
    satu baris dan dua baris dua-duanya harus duduk di tengah. Kotak teksnya
    72% × 46% dari elipsnya: sebuah kotak muat di dalam elips kalau
    `(w/a)² + (h/b)² ≤ 1`, dan 0,72/0,46 memberi 0,73.
    Hal 11 **dirombak total 19 Agu 2026** — lihat blok "Halaman 11" di bawah.
    Ia tidak lagi foto pembeli sehalaman penuh.
  - **Foto ada DI BELAKANG pelat**, lewat lubang transparan yang bentuknya
    diukur dari render, bukan ditebak. Itu yang membuat pita halaman 8,
    logam liontin halaman 7, dan coretan halaman 4 tetap berada di ATAS
    foto seperti desain aslinya. Jangan pindahkan foto ke atas pelat.
  - **Font Canva-nya berbayar** (BostonAngel-Light, Amsterdam-Four,
    MadelynFill, BurguesScript) dan lisensinya cuma berlaku di dalam Canva —
    tidak boleh dipasang di situs. Penggantinya Bellefair, Allura, Kaushan
    Script, Pinyon Script, dipilih dengan mengukur lebar barisnya. Ukuran
    tiap teks lalu disetel supaya LEBAR barisnya sama persis dengan desain,
    bukan supaya tinggi hurufnya sama — itu yang menjaga tata letaknya.
  - **Teks pembeli yang lebih panjang dari bawaannya dikecilkan otomatis**
    (`--muat` di valentine.js). Tiap teks menyatakan jatah ruangnya lewat
    `data-baris` (atau `data-maks` untuk surat halaman 4). Selama teksnya
    sepanjang bawaan, pengalinya tetap 1 dan desainnya tidak berubah
    sepiksel pun. Tanpa ini, nama panjang seperti "MUHAMMAD RIZKI PRATAMA &
    SITI NURHALIZA RAHMAWATI" menabrak tulisan lain dan keluar halaman.
    Teks baru WAJIB diberi `data-baris` — ada tesnya.
  - **Angka `--cf` di valentine.css hasil UKUR, bukan hitung.** Setelah
    mengubah font, ukuran teks, atau pelatnya, jalankan ulang
    `tools/cek_valentine.js` dan salin lagi angkanya. Enam pemeriksa lain:
    `cek_valentine_lebar.js` (lebar baris), `cek_valentine_balik.js` (balik
    lembar), `cek_valentine_debu.js` (peralihan debu), `cek_valentine_editor.js`
    (klik teks & foto), `cek_valentine_ukuran.js` (muat di semua layar),
    `cek_valentine_hal11.js` (surat halaman 11 tidak keluar dari catatannya).
    Semuanya perlu `NODE_PATH` ke node_modules berisi puppeteer-core.

    > `cek_valentine_debu.js` punya `LARUT` di kepalanya yang **harus sama
    > dengan `LAMA_LARUT` di valentine.js**. Pernah basi diam-diam sekali
    > (1100 -> 2500 ms tanpa berkas itu ikut disetel), dan akibatnya dua
    > kegagalan palsu yang menetap.
  - **DUA gaya membalik, dipilih lewat satu kata `GAYA` di valentine.js.**
    `"bilah"` (**dipakai sekarang, sejak 14 Agu 2026**) = enam belas bilah
    melengkung (dijelaskan di bawah). `"rotasi"` = satu bidang diputar
    rotateY dengan transisi CSS 600 ms `cubic-bezier(.645,.045,.355,1)`,
    mengikuti spek gaya heyzine. Dua-duanya lengkap dan bisa dipakai;
    JANGAN hapus salah satunya — keputusannya sudah berbalik **dua kali**,
    dan membangun ulang jalur bilah memakan berjam-jam pengukuran.

    > **Pembalikan kedua (14 Agu 2026).** Keluhan pemilik situs: "seperti
    > menarik kayu". Itu keluhan yang SAMA dengan "seperti keramik kaca"
    > yang dulu melahirkan jalur bilah — bidang datar yang diputar
    > siluetnya memang selalu segi empat bertepi lurus, dan tidak ada nilai
    > transisi yang memperbaikinya. Karena itu jalurnya yang diganti, bukan
    > angkanya. Anggap keputusan ini akan berbalik lagi.
    >
    > Kelengkungannya sekaligus **diperdalam** atas permintaan "seperti
    > membuka kain", lewat satu konstanta baru `LURUH` (pangkat peluruhan
    > kelengkungan; 1 = perilaku lama). Dengan `LURUH = 0,30` puncak sebaran
    > sudut naik dari **40,3° ke ~72°**. Angka-angka itu diukur dari
    > fungsinya sendiri (200 cuplikan sepanjang putaran); tabel lengkapnya
    > di komentar `taruh()`.
    >
    > **Jumlah bilah = 12, dan itu hasil tawar-menawar DUA artefak yang
    > tarik-menarik.** Diukur di WebKit:
    >
    > | bilah | seam Safari/baris | faceting |
    > |---|---|---|
    > | 10 | 5,45 | 12,32° |
    > | **12** | **5,99** | **10,12°** |
    > | 14 | 7,97 | 9,14° |
    > | 16 | 8,99 | 7,94° |
    >
    > Menambah bilah menghaluskan lengkungnya tapi MENAMBAH garis gelap
    > tegak antar bilah di Safari — satu garis per batas bilah. Sempat
    > dipasang 16, dan itulah "pecah pecah" yang dikeluhkan pemilik situs.
    > **Kelengkungan tidak berpengaruh sama sekali pada seam**: 16 bilah
    > pada `LURUH` 1,0 dan 0,30 sama-sama 8,96. Jadi lengkung dalam itu
    > gratis; yang mahal cuma jumlah bilahnya.
    >
    > Pemilik situs memberi kelonggaran lompatan sampai 15°, dan ambang di
    > `cek_valentine_balik.js` dinaikkan 8 → 15 mengikuti itu. Pada 12 bilah
    > lompatannya 10,12° — di dalam jatah, tapi memang di atas 8° yang lama.
    >
    > `TINDIH` tetap **1,5**, dan ini sudah diuji DUA KALI dengan kesimpulan
    > berbeda — perhatikan bedanya. Di Chrome menaikkannya tidak berpengaruh
    > (Laplacian 2,900 → 2,957 pada 1,5 → 6). Di WebKit, menaikkan ke
    > 3/5/8/12 juga tidak menutup seam (9,03 → 8,25) tapi MEMPERDALAMnya
    > (15,8 → 18,4), sedangkan menurunkannya ke 0 jelas lebih buruk
    > (10,26 garis, kedalaman 24,6). Sebabnya: tumpang-tindih menukar celah
    > dengan salah-jajar — di daerah tindihan, dua bilah menggambar isi yang
    > sama pada SUDUT berbeda. Makin lebar tindihannya, makin lebar pita
    > salah-jajarnya. 1,5 adalah titik terbaiknya. **Membuang bayangan per
    > bilah tidak menolong sama sekali** (9,00 vs 9,03) — jadi seam-nya
    > geometri, bukan gradasi.

  - **`SIMPANG` dibangkitkan, jangan dikembalikan jadi array angka tetap.**
    Dulu ia sepuluh angka yang diketik tangan, dan itu MENGUNCI `N_BILAH`
    di sepuluh tanpa ada yang menyatakannya di mana pun. Menaikkan
    `N_BILAH` membuat `SIMPANG[10..]` jadi `undefined` → sudutnya `NaN` →
    seluruh string `transform` tidak sah → **lembarnya hilang dari layar**,
    tanpa satu pun error di console. Sekarang dibangkitkan sepanjang
    `N_BILAH` dari deret sin-fract yang tetap deterministik (simpangan yang
    diundi ulang tiap frame membuat tepi lembarnya bergetar). Dijaga
    `test_simpang_dibangkitkan_sepanjang_jumlah_bilah`.

  - **MEKANIK BERPINDAH HALAMAN SEKARANG "partikel"** (16 Agu 2026).
    Halaman **memudar di tempat** sambil melepas **debu berpendar yang
    naik**, berwarna mengikuti halamannya. Tidak ada lembar yang dibalik.
    Permintaan pemilik situs, menggantikan mekanik balik lembar sepenuhnya.

    > **Jalur "bilah" dan "rotasi" TETAP UTUH** dan bisa dihidupkan dengan
    > mengganti satu kata `GAYA` di `valentine.js`. Ini permintaan eksplisit
    > pemilik situs — keputusan animasi template ini sudah berbalik **tiga
    > kali**. Yang tidak dipakai tidak berjalan sama sekali.
    >
    > **Warna debu dicuplik dari PELAT halamannya**, kisi 12×17, disimpan
    > per halaman. Tiga hal yang pernah salah dan sudah dijaga tesnya:
    >
    > 1. **Warna diangkat jadi berpendar, jangan dipakai mentah.** Debu yang
    >    berpendar selalu lebih terang daripada permukaan asalnya. Dipakai
    >    mentah, halaman merah tua melepas debu merah tua yang lenyap di
    >    atas halamannya sendiri; halaman gelap melepas bintik kelabu yang
    >    terbaca sebagai KOTORAN di atas halaman terang berikutnya. Diangkat
    >    55% + lantai kecerahan 205 (`pendar()`).
    > 2. **Sampul dan penutup TIDAK menyisakan apa pun untuk dicuplik** —
    >    terukur 0 piksel opak dari 204 cuplikan, karena seluruh pelatnya
    >    lubang foto. `cadanganWarna()` mengambil `--kertas-bg` lalu
    >    menyebarnya jadi beberapa nuansa.
    > 3. **Posisi butir diundi RATA, terpisah dari sumber warnanya.** Versi
    >    pertama menaruh tiap butir di titik cuplikannya, dan di halaman
    >    yang didominasi lubang foto seluruh debu menggerombol di bingkai
    >    tepi.
    >
    > **Foto pembeli tidak pernah dicuplik** — bisa dari R2 yang beda asal,
    > dan itu mencemari kanvas sehingga `getImageData` dilarang.
    >
    > **Warna dipanaskan di muka** (di `pasang()`, untuk halaman `.dekat`).
    > Men-decode pelat lalu `getImageData` terukur menahan **157 ms** tepat
    > di frame pertama gerakan. Sesudah dipanaskan: jeda terlama 18,7 ms,
    > 60 fps dan 98–100% pengisian frame sampai CPU dicekik 6×.
    >
    > **Satu kanvas, bukan elemen DOM per butir.** 260 elemen yang digeser
    > tiap frame memaksa hitung ulang tata letak enam puluh kali sedetik.
    >
    > **Peralihan yang DISUSUL harus dibereskan, bukan cuma dihentikan.**
    > Tiga cacat sekaligus muncul dari sini waktu penerima menekan lanjut
    > lebih cepat daripada peralihannya (dilaporkan pemilik situs 16 Agu):
    >
    > 1. `opacity` inline yang sudah terlanjur dipasang ditinggalkan
    >    menempel. Gaya inline **tidak bisa** ditimpa aturan CSS
    >    `.lembar{opacity:0}`, jadi tiap tekanan menambah satu halaman
    >    setengah transparan sampai layarnya jadi bubur berlapis.
    >    `bersihkanSisa()` menyapu SEMUA lembar, bukan cuma dua yang
    >    terlibat.
    > 2. Nomor peralihan dulu dinaikkan SETELAH warna selesai diambil.
    >    Pengambilan warna menunggu gambar ter-decode, jadi dua peralihan
    >    beruntun bisa selesai dengan urutan terbalik dan yang LAMA mengira
    >    dirinya terbaru. Sekarang dinaikkan sinkron di awal `larutkan()`.
    > 3. Halaman tujuan dulu dipaksa mulai dari nol tiap peralihan. Pada
    >    tekanan beruntun ia tidak pernah sempat muncul dan layar justru
    >    **kosong** — terukur 66% frame di bawah 0,35 opasitas.
    >
    > **Yang dianimasikan HANYA halaman lama.** Halaman tujuan diam di
    > bawahnya pada opasitas penuh dan tersingkap seiring yang di atas
    > larut. Itu yang membuatnya terbaca sebagai halaman menghilang, bukan
    > dua gambar saling silang — dan sebagai bonus, skip beruntun jadi tegas.
    >
    > Halaman yang larut WAJIB diberi kelas `.keluar`: tanpa itu ia bukan
    > `.active` dan bukan `.masuk`, jadi tersembunyi, dan `opacity` inline
    > pada elemen tersembunyi tidak berpengaruh apa pun — halaman lama
    > LENYAP SEKETIKA alih-alih memudar. `.keluar` juga memberinya
    > `z-index: 25`; tanpa itu arah MUNDUR tidak simetris karena urutan
    > tumpukan menaruhnya di bawah halaman tujuan.
    >
    > **Digarap ulang 19 Agu 2026** atas permintaan pemilik situs: lebih
    > cantik, lebih santai, dan tidak berhamburan ke luar kartu. Tiga hal:
    >
    > 1. **Kanvas debu dulu kena skala DUA KALI, dan cacatnya cuma bergejala
    >    di layar lebar.** `ukurKanvas()` memakai `getBoundingClientRect()`,
    >    yang mengembalikan piksel SESUDAH `#card-stage` diskalakan, lalu
    >    memasang angka itu balik sebagai `style.width` — yang berlaku
    >    SEBELUM penskalaan. Terukur: pada 1440x900 skala panggungnya 1,534
    >    dan kanvasnya jadi 1,53x halaman, meluber 53% ke kanan dan bawah.
    >    Di HP skalanya kebetulan tepat 1,000, jadi salahnya TIDAK bergejala
    >    sama sekali di sana — itu sebabnya ia lolos berbulan-bulan dan
    >    seluruh pemeriksa. Sekarang `offsetWidth`/`offsetHeight`, yang
    >    satuannya sama dengan `style.width`. Dijaga
    >    `test_kanvas_debu_diukur_dalam_piksel_lokal`.
    >
    > 2. **1100 -> 2500 ms, dan kecepatan debunya WAJIB ikut turun.** Ini
    >    pasangan yang gampang terlewat: pada kecepatan lama (0,34 px/ms)
    >    dan durasi baru, butir tercepat menempuh 850 px sedangkan halamannya
    >    cuma 551,6 px — seluruh debu sudah keluar layar sebelum peralihan
    >    separuh jalan, dan paruh keduanya jadi halaman memudar tanpa debu.
    >    Tidak ada error, tidak ada yang merah; efeknya saja yang hilang.
    >    Dijaga `test_debu_tidak_pernah_menempuh_lebih_dari_satu_halaman`.
    >
    >    Halamannya juga habis pada **72%** peralihan, bukan 100%: seperempat
    >    waktu terakhir yang dihabiskan menonton halaman bersisa beberapa
    >    persen opasitas tidak terlihat berubah, cuma terasa lambat. Sisa
    >    waktunya jadi milik debu yang masih melayang di atas halaman baru.
    >
    > 3. **Butirnya digambar dari SPRITE, bukan `arc()` rata.** Nyala
    >    bergradasi butuh `createRadialGradient`, dan membuatnya 260 kali per
    >    frame pada 60 fps berarti 15.600 gradien per detik. Sprite dibuat
    >    sekali per warna (dibulatkan ke 16 tingkat per kanal) lalu dipakai
    >    ulang lewat `drawImage`. Terukur sesudahnya: 60 fps dan jeda frame
    >    terlama 17,7 ms, bahkan saat CPU dicekik 6x — tidak ada tersendat di
    >    frame pertama. Dijaga
    >    `test_nyala_butir_dari_sprite_bukan_gradien_tiap_frame`.
    >
    >    Sepersepuluh butir berbentuk **hati** (`PORSI_HATI`), sisanya tetap
    >    debu bulat. Porsinya sengaja kecil: pada porsi besar efeknya berhenti
    >    terbaca sebagai "halaman larut jadi debu" dan berubah jadi hujan
    >    hiasan yang menempel di depan kartu.
    >
    > **Debu boleh melayang SEDIKIT ke luar kertas** (pilihan pemilik situs),
    > dan ruang itu harus dibuat: kertas dan bingkai kartu adalah kotak yang
    > sama persis (390x552 lokal, terukur sama di pratinjau berdiri sendiri
    > MAUPUN iframe editor), jadi kanvasnya yang dilebarkan `TEPI_DEBU` px ke
    > keempat sisi. Angkanya cuma hidup di JS — `#debu` di CSS sengaja tanpa
    > `inset`, karena angka yang hidup di dua tempat akan bergeser sendiri.
    >
    > Butirnya **meredup melintasi tepi kertas**, tidak berhenti di situ.
    > Perlu karena di layar lebar tepi atas kertas berimpit dengan tepi
    > `#card-viewport` yang `overflow:hidden` (terukur: pada 1440x900 halaman
    > menempati y 0..846 dari 900), jadi tanpa peredupan debu yang naik
    > tergunting rata di garis yang persis lurus.
    >
    > Penjaganya `tools/cek_valentine_debu.js` (14 uji). `cek_valentine_balik.js`
    > **melewati dirinya sendiri** kalau GAYA bukan mekanik balik lembar,
    > dan sebaliknya — jadi keduanya bisa dijalankan berurutan tanpa merah
    > palsu. Keduanya membaca `#buku[data-gaya]`, bukan menebak dari DOM.

  - **UJI DI WEBKIT, BUKAN CUMA CHROME.** Ini pelajaran terbesar dari 14
    Agu 2026, dan berlaku untuk seluruh template ini. Tiga cacat berturut-turut
    lolos SEMUA pemeriksa `tools/cek_valentine_*.js` karena semuanya jalan di
    Chrome, lalu langsung terlihat begitu kartunya dibuka di Safari.

    > Pasang sekali: `npm i playwright && npx playwright install webkit`.
    > WebKit-nya mesin yang sama dengan Safari, tidak perlu izin otomasi,
    > dan mereproduksi ketiga cacat itu persis. Otomasi Safari sungguhan
    > lewat AppleScript/`screencapture` **nge-hang** di Mac ini (dialog izin);
    > jangan buang waktu di situ.
    >
    > **Metrik gambar WAJIB dua sisi.** Dua "perbaikan" sempat dinyatakan
    > berhasil padahal mengosongkan halamannya: metriknya menghitung
    > *hilangnya artefak* dan tidak bisa membedakannya dari *hilangnya isi*.
    > Selalu ukur juga ragam warna wilayahnya — halaman berisi punya ribuan
    > warna, halaman kosong belasan. Dan selalu ukur **kontrol halaman
    > diam**: di WebKit kontrolnya 0,00–0,15 garis/baris, jadi apa pun di
    > atas itu memang artefak, bukan tekstur foto.

  - **Muka lembar yang membelakangi pembaca diurus KELAS, bukan
    `backface-visibility`.** WebKit tidak mematuhi `backface-visibility` di
    sini: lembar yang sudah dibalik ke kiri menampilkan isi halamannya
    TERCERMIN ("Contents" terbaca terbalik). `valentine.js` memasang kelas
    `.terbalik` di `taruh()` begitu lembarnya lewat setengah putaran —
    tepat saat lembarnya tegak lurus layar, jadi pertukarannya tak
    kasatmata.

    > **Lembar yang sudah pindah ke kiri menampilkan ISI halamannya,
    > terbaca normal** (permintaan pemilik situs: "yg disebelah kiri itu
    > jadi halaman sebelumnya yg dibagian kanan, tidak mirror"). Caranya
    > muka depannya tetap ditampilkan lalu **dicerminkan balik**
    > `scaleX(-1)` — dilihat dari belakang ia sudah tercermin sekali, jadi
    > cerminan kedua mengembalikannya terbaca.
    >
    > **JANGAN menyalin isi halaman ke punggung lembar.** Itu melipatgandakan
    > pelat 1241x1755 yang ter-decode, dan itulah yang dulu membuat tab
    > tertutup paksa di HP kelas bawah. Cara scaleX ini nol tambahan memori.
    >
    > **Jalan buntu, jangan diulang:** memberi `.muka.depan` transform 3D
    > sendiri (`translateZ(0.01px)`) MEMANG membuat WebKit mematuhi
    > backface-visibility — dan sekaligus mengosongkan halamannya. Terukur:
    > isi halaman tinggal **17 warna, dari 8.819**. Sempat lolos karena
    > metriknya cuma menghitung tinta yang bocor, dan halaman kosong tentu
    > saja nol. Dijaga `test_lembar_terbalik_menampilkan_isinya_tidak_tercermin`.

  - **`#rig` disembunyikan dengan `display`, JANGAN `visibility`.**
    Ini cacat pertama yang lolos seluruh pemeriksa. `#rig` ber-`preserve-3d`
    dan bilah di dalamnya punya transform 3D sendiri; Safari merender
    anak-anak itu ke ruang 3D bersama dan **tidak mewarisi**
    `visibility: hidden` induknya. Akibatnya setelah tiap putaran selesai,
    keenam belas bilah tetap tergambar pada sudut terakhirnya (~180°, yaitu
    terlempar ke KIRI halaman) sebagai pita tegak berisi potongan isi
    halaman yang ter-smear — persis seperti yang dilaporkan pemilik situs.

    > **Chrome menyembunyikannya dengan benar**, jadi cacat ini tidak
    > muncul di satu pun `tools/cek_valentine_*.js` — semuanya jalan di
    > Chrome. Penjaganya karena itu ditaruh di
    > `test_rig_disembunyikan_dengan_display_bukan_visibility`, bukan di
    > pemeriksa puppeteer. **Pelajarannya lebih besar dari satu properti
    > CSS: untuk template ini, lolos pemeriksa Chrome BUKAN bukti tampilan
    > benar.** Apa pun yang menyentuh preserve-3d, backface, atau
    > visibility wajib dilihat langsung di Safari sebelum dianggap beres.
    >
    > `display:none` aman dipasang-lepas tiap putaran: `pakaiRig()` tidak
    > pernah MENGUKUR apa pun dari rig. Diukur setelah perubahan: lama
    > putaran 1434 ms, lompatan antar frame 0,0319, 87 frame — identik
    > dengan sebelum perubahan, dan beban tetap 60 fps @ cekik 6×.
    >
    > Efek sampingnya di pemeriksa: elemen `display:none` mengembalikan
    > `transform: none` dari getComputedStyle, jadi perekam yang membaca
    > `.pias` membabi buta melihat t terjun dari ~1 ke 0 dan melaporkan
    > "patah" yang tidak ada di layar. Kedua perekam sekarang membaca rig
    > **hanya kalau ia ber-kelas `.jalan`**, selain itu membaca `.lembar`.

  - **Ambang `cek_valentine_beban.js` sekarang DISKALAKAN ke fps menganggur**,
    menyusul `cek_valentine_balik.js` yang sudah lebih dulu. Ambang tetap
    (45/28 fps) melaporkan "cukup/TERSENDAT" untuk animasi yang sebenarnya
    mengisi 95–96% frame yang tersedia, semata karena mesin penguji sedang
    tercekik — pernah terukur 31 fps menganggur di **halaman kosong**.
    Skripnya sekarang mengukur itu lebih dulu dan menilai persentase
    pengisian, bukan angka fps mutlak. Kalau ia melapor tersendat, **lihat
    baris `fps menganggur` dulu** sebelum menyalahkan animasinya.

  - **Pemeriksa harus membaca elemen yang BENAR-BENAR bergerak.**
    `cek_valentine_balik.js` dan `cek_valentine_beban.js` dulu sama-sama
    membaca `#hal1`. Itu sah untuk gaya "rotasi", tapi di gaya "bilah"
    `.lembar` DIAM dan digantikan rig — yang berputar `.pias`. Akibatnya
    `lamaMs` dan `frame` keluar **nol**, dan tiga uji lolos palsu sekaligus
    (lompatan terbesar 0 lolos ambang apa pun; "cukup banyak frame" jadi
    `0 >= 70% dari 0`); di pemeriksa beban ia melaporkan "fps 96 saat CPU
    dicekik 6×" — angka mustahil yang terbaca sebagai lulus. Keduanya
    sekarang memilih elemen menurut gayanya. Jangan hardcode `#hal1` lagi,
    dan jangan hardcode jumlah bilah di mana pun.
  - Ketuk tepi kiri/kanan, sudut kertas terangkat saat kursor mendekat,
    tumpukan lembar di kedua tepi, dan suara kertas (tombol ♪ untuk
    membisukan, pilihannya disimpan localStorage).

    > **SELURUH SUARA MEMBALIK HALAMAN DICABUT** (19 Agu 2026, permintaan
    > pemilik situs). Satu-satunya suara di kartu ini sekarang lagu YouTube
    > pilihan pembeli lewat `_bgm.html`; efek gesekan kertasnya bertumpuk di
    > atas lagu itu.
    >
    > Yang hilang sekaligus: atribut `data-suara`, tombol ♪, aturan `#bisu`,
    > dan seluruh blok Web Audio di `valentine.js` — klip berkas MAUPUN
    > `suaraSintetis()`. **Aturan lama "jangan hapus sintesisnya, itu jalur
    > cadangannya" DIBATALKAN**: ia menjaga cadangan bagi suara yang memang
    > tidak dikehendaki lagi. Kalau suatu hari diminta kembali, ambil dari
    > riwayat git — jangan tulis ulang dari nol.
    >
    > Jangan memasang kembali sebagiannya saja: tombol tanpa jalur suara
    > memberi pembeli sakelar yang tidak melakukan apa-apa, jalur suara tanpa
    > tombol berbunyi tanpa bisa dimatikan. Dijaga
    > `test_tidak_ada_suara_membalik_halaman`.
    >
    > `static/audio/SUMBER.md` sengaja DIBIARKAN: di situ tercatat kandidat
    > klip yang lisensinya sudah diperiksa satu per satu, plus keputusan
    > menolak audio dari YouTube Shorts (melanggar ToS, hak ciptanya tidak
    > jelas, sedangkan kartu ini dijual). Berguna kalau keputusannya berbalik.
    > Tag `{% static_ada %}` di `card_extras.py` sekarang tidak dipakai
    > siapa pun.
    Zona ketuk SENGAJA tidak ada saat menyunting: ia menutupi 22% lebar
    halaman di tiap sisi dan akan menelan klik pada teks serta bingkai foto
    yang dekat tepi. Tumpukan lembar duduk di LUAR tepi halaman, jadi ia
    hanya terlihat di layar yang lebih lebar daripada halamannya — di dalam
    berarti menutupi karya Canva.
  - **Catatan jalur "bilah": halamannya MELENGKUNG, tidak diputar.** Satu bidang datar yang diputar (`rotateY` pada `.lembar`) selalu
    terbaca sebagai kaca: siluetnya tetap segi empat bertepi lurus, betapa
    pun pelan dan berbayangnya. Memperlambat, memberi pita cahaya, dan
    memberi skew sudah dicoba dan semuanya gagal — hiasan di atas geometri
    yang salah.

    Sekarang halaman dipecah **sepuluh bilah tegak** (`#rig`), dan posisi
    tiap bilah DIAKUMULASI dari bilah sebelumnya, jadi siluetnya kurva
    sungguhan. Tiga angka di `valentine.js` saling terikat dan jangan
    diubah sendiri-sendiri:
      * `BATAS` pakai `(k/N)^0.5` — kelengkungan sebanding u kuadrat, jadi
        pangkat itu yang membuat SUDUT tiap bilah kira-kira sama, bukan
        lebarnya;
      * `tinggal` dikali 0,85 — batas kelengkungan yang masih bisa digambar
        sepuluh bidang datar tanpa terlihat berkisi;
      * lompatan sudut antar bilah harus tetap **di bawah 8 derajat**; di
        atas itu faceting-nya terlihat sebagai kisi-kisi jendela.
    Semua dijaga `tools/cek_valentine_balik.js`.

    > **JANGAN tambahkan lapisan kilau putih per bilah.** Pernah ada dan
    > dicabut: tepinya jatuh persis di batas potongan tiap bilah, dan sisa
    > antialias putih di situ menumpuk di atas isi bilah tetangganya —
    > sepuluh batas jadi sepuluh garis terang tegak yang terbaca sebagai
    > "retakan kaca". Terukur dengan Laplacian pada halaman abu rata:
    > dengan kilau 4,11; tanpa kilau 0,49; halaman diam sendiri 0,80.
    > Mengurangi tumpang-tindih, melandaikan pangkat kilaunya, dan menambah
    > titik gradien semuanya sudah dicoba dan TIDAK menolong. Sisi terang
    > sekarang datang dari gradasi gelap yang menghilang di bagian yang
    > menghadap cahaya.
    >
    > Catatan cara mengukurnya: metrik pertama saya membandingkan tiap kolom
    > dengan tetangga 4 px — dan itu ikut menangkap huruf serta gradien
    > tirai, jadi halaman DIAM pun terukur 17. Empat percobaan perbaikan
    > terbuang karena metrik itu. Pakai Laplacian pada pita halaman yang
    > bebas teks, dan selalu ukur halaman diam sebagai kontrol.

    Isinya diklon dari `.kertas`, dan atribut `id`/`data-edit`/`data-frame`
    WAJIB dibuang dari klon — kalau tidak, card-frame.js melihat elemen
    kembar dan sorotan editor mendarat di klon.

    Sisi belakang bilah memakai warna kertas tetap, BUKAN `--kertas-bg`
    halamannya: sampul yang fotonya gelap membuat separuh lembar terlihat
    seperti lubang hitam begitu lipatannya lewat 90 derajat.

  - **Satu pegas untuk seret DAN lepas.** Saat diseret, sasaran pegas adalah
    posisi jari — lembarnya mengejar, tidak menempel mati, dan dari situlah
    hambatan serta kelambanannya. Saat dilepas, kecepatan jari jadi
    kecepatan awal pegas. Satu rumus untuk dua keadaan = tidak ada patahan
    di detik jari diangkat. Konsekuensinya lamanya TIDAK persis tetap
    (±1,4 detik, tergantung jarak dan lemparan) — itu memang sifat benda
    fisik, bukan bug.

  - Semua ditulis LANGSUNG ke `style.transform`/`style.opacity`, bukan lewat
    custom property. Custom property diwariskan, jadi mengubahnya di
    `.lembar` tiap frame memaksa browser memeriksa ulang gaya seluruh isi
    halaman enam puluh kali sedetik. Terukur 60 fps bahkan dengan CPU
    dicekik 6x (`tools/cek_valentine_beban.js`).
  - **Tombol menyatakan maksud, bukan nomor halaman** (`geser(±1)`). Dengan
    putaran 1,4 detik, penerima menekan dua kali beruntun; kalau nomornya
    dihitung sebelum putaran berjalan selesai, tekanan kedua tidak
    melakukan apa-apa.
  - **Hati di kalender halaman 5 bisa dipindah** dengan mengklik angkanya
    saat menyunting. Angkanya tetap menyatu dengan pelat (huruf Canva asli);
    yang dicabut cuma hatinya. Pilihannya disimpan di teks `hari`, lewat
    pesan `settext` — jalur baru dari dalam kartu ke editor
    (`window.simpanTeks` di card-frame.js).
  - **Kotak crop mengikuti bentuk bingkai** lewat `"rasio"` di config tiap
    bingkai, dan bingkai bertanda `"asli"` (sampul) disimpan sampai 2400 px
    dengan batas berkas `MAX_PHOTO_BYTES_BESAR` (8 MB). Sebelumnya kanvas
    crop selalu 640x640, dan itu — bukan pengecilan di server — yang
    membuat foto sampul terlihat pecah.
  - Pemeriksa tambahan: `cek_valentine_kalender.js`, `cek_valentine_crop.js`,
    `cek_valentine_ukuran.js`. `cek_valentine_balik.js` sekarang juga
    mengukur lamanya putaran dan lompatan antar frame — itu ukuran
    "kaku/patah" yang objektif.

    > **Ambang kemulusannya DISKALAKAN ke kecepatan frame browsernya.**
    > Chrome headless di mesin ini hanya memberi ~32 fps saat MENGANGGUR,
    > tanpa animasi apa pun. Putaran 0,6 detik karena itu cuma bisa berisi
    > ~19 frame, dan ambang lama yang dipatok ke 60 fps (lompatan < 0,08,
    > frame > 25) melaporkan "patah" untuk animasi yang di layar sungguhan
    > mulus. Pemeriksa sekarang mengukur `fpsMenganggur` lebih dulu. Kalau
    > kedua penjaga itu gagal lagi, ukur fps-nya dulu sebelum menyalahkan
    > animasinya.
  - **Garis putih di pinggir foto: sebabnya kotak bingkai, bukan crop-nya**
    (19 Agu 2026). Dilaporkan pemilik situs sebagai "foto yang sudah dicrop
    ada garis putih di pinggirnya".

    > Tersangka pertama salah, dan bagus dicek dulu: kanvas crop di
    > `alpine-editor.js` memang dicat `#eee` sebelum fotonya digambar. Tapi
    > kedelapan puluh delapan foto yang sudah diunggah diperiksa satu per
    > satu — **nol** yang punya baris piksel se-`#eee` di tepinya. Bukan dari
    > sana.
    >
    > Sebabnya `komponen()` di `tools/buat_pelat_valentine.py`: ia mencari
    > kotak lubang pada mask yang diperkecil 4x lalu mengembalikannya pada
    > kisi 4 px. Kotaknya karena itu JATUH DI DALAM lubang pelat yang
    > sebenarnya — terukur di kesebelas pelat, tepi kanan dan bawah
    > konsisten kurang 1-3 px pelat (0,94 px desain). Selebar itu lubangnya
    > menganga dan yang mengintip dari baliknya latar `.muka` (#fffaf1).
    > Di halaman berkertas krem — 4, 6, 7, 9 — itulah garis putihnya.
    >
    > Ditutup dengan `--tembus` di `.gbr`: fotonya digambar 1,5 px desain
    > lebih besar ke segala arah. Aman justru karena foto ada DI BELAKANG
    > pelat — kelebihannya tertutup pelat sendiri, dan yang sehalaman penuh
    > dipotong `.muka` yang sudah `overflow:hidden`. Lubang terdekat
    > berjarak 24 px pelat, jadi tidak ada foto yang bisa bocor ke tetangga.
    > Dibuktikan A/B di perender sungguhan: garis krem itu muncul pada
    > `--tembus:0` dan hilang pada 1,5px, pada foto yang sama persis.
    >
    > Yang diperbaiki GEJALANYA. Sebabnya di `komponen()`; membetulkannya
    > berarti menghitung ulang kelima belas koordinat di valentine.html.
    > Kalau itu suatu hari dikerjakan, `--tembus` boleh dinolkan — tapi
    > jangan sebelum itu. Dijaga `test_foto_melewati_tepi_lubang_pelat`.

  - **Halaman 11 — "Letter For You"** (desain baru 21 Agu 2026). Kertas krem
    bergaris tepi putus-putus, anggrek merah di pojok kiri atas, dan satu
    catatan merah tua berselotip tempat suratnya ditulis. **Tidak punya
    bingkai foto sama sekali** — dulu foto pembeli sehalaman penuh
    (`f_akhir`), dicabut 18 Agu 2026 dan tidak pernah kembali. Penutup
    berfoto ada di halaman 12, tapi bukan bingkai yang sama: bentuknya hati
    dan tidak sehalaman penuh, jadi TIDAK bertanda `"asli"`.

    > **Riwayat desainnya sudah tiga kali.** Foto sehalaman penuh (sampai 18
    > Agu) -> kolase merah bersequin dengan bibir, bintang perak, dan sobekan
    > koran "love" bertajuk "My wish for you" (18-21 Agu) -> surat ini.
    > Kolasenya tidak dipakai lagi di mana pun, dan `buat_pelat_hal11.py`
    > sudah ditulis ulang untuk sumber yang baru — jadi seluruh catatan lama
    > soal menghapus huruf potongan koran, mencari tepi sequin, dan membuang
    > pita merah di tengah gambar **sudah tidak berlaku**. Kalau butuh, ia
    > ada di riwayat git, bukan di sini.

    > **Pelatnya BUKAN dari `LOVESTORY-2.pdf`.** Di PDF itu halaman 11 krem
    > polos. Desain ini datang sebagai PDF satu halaman tersendiri
    > (`LOVESTORY-4.pdf`) dan diolah `tools/buat_pelat_hal11.py`. Halaman 11
    > karena itu TETAP terdaftar di `TANPA_PELAT` pada `buat_pelat_valentine.py`;
    > kalau dicabut dari sana, skrip itu akan menimpa hasilnya dengan halaman
    > krem kosong dari PDF-nya.
    >
    > **Rasionya kebetulan sudah benar.** Halaman PDF-nya 595,5 x 842,25 pt
    > (0,7070), sama dengan A4 kanonis template ini (390/551,6). Dirender 150
    > dpi hasilnya persis 1241x1755 — ukuran yang sama dengan sebelas pelat
    > lain, tanpa dipotong maupun diregangkan sedikit pun. Skripnya tetap
    > MEMERIKSA ini, tidak mengandaikannya.
    >
    > **Judul "Letter For You" dihapus dari pelatnya** supaya bisa diganti
    > teks HTML (`.t-wish`, kunci `wish`) — perlakuan yang sama dengan
    > "HAPPY BIRTHDAY" pada desain sebelumnya, dan bawaannya sengaja kata
    > yang sama persis supaya pembeli yang tidak menyentuh apa pun tetap
    > mendapat desainnya utuh. Dihapus dengan **redaksi PyMuPDF yang hanya
    > menyentuh objek teks** (`PDF_REDACT_IMAGE_NONE`, `fill=False`), bukan
    > dengan mengecat ulang kotaknya: kotak judul (x 141,6..535,9 pt)
    > bertumpang tindih dengan gambar anggrek (x 10,0..203,6 pt), dan cat
    > akan memakan kelopaknya.
    >
    > **Fontnya dua, dan keduanya keputusan sadar.** Judul memakai **Kaushan
    > Script**, padanan MadelynFill seperti di seluruh template ini. Isi
    > suratnya memakai **Caveat** — DIPERTAHANKAN dari desain kolase atas
    > permintaan pemilik situs, bukan warisan yang terlewat.
    >
    > **Yang disamakan LEBAR BARIS judulnya, bukan ukuran hurufnya.** Aturan
    > yang sama dengan `.t-judul6` ("Our Love", 186,93pt Madelyn -> 83,20px
    > Kaushan). Di sini: 99,58pt Madelyn -> 45,40px Kaushan, terbukti rasio
    > 1,000 di `cek_valentine_lebar.js`. Kotaknya sengaja **2,283% lebih
    > lebar** daripada barisnya, dengan kiri digeser setengahnya supaya titik
    > tengahnya tidak berubah — pada ukuran yang persis pas, pembulatan
    > sub-piksel Chrome sesekali memecahnya jadi "Letter For / You".
    >
    > **`.t-pesan` dikurung di kotak merah POLOS, bukan kotak pembatas
    > catatannya.** Catatan merahnya digambar sedikit miring, sudut kanan
    > atas dan kiri bawahnya ditimpa selotip, dan dua sudut sisanya punya
    > goresan hias. `buat_pelat_hal11.py` mencari persegi panjang TERBESAR
    > yang seluruhnya merah catatan (algoritma "persegi terbesar di dalam
    > histogram") dan mencetak angkanya; teks yang dipasang pada kotak
    > pembatas akan jatuh di atas selotip. Diuji sampai surat 464 huruf:
    > `--muat` turun ke 0,924 dan tepi bawahnya masih 50 px di dalam kotak.
    >
    > **`--kertas-bg` berubah dari merah tua ke krem (`#ede9e1`).** Ia warna
    > kertas halamannya dan gunanya menahan kedipan sebelum pelatnya
    > ter-decode. Membawa angka merah lama ke desain baru akan membuat
    > halaman berkedip GELAP dulu di sambungan peralihan — persis di halaman
    > yang seharusnya terasa paling tenang.

  - **Halaman 12 — penutup hati renda** (19 Agu 2026, permintaan pemilik
    situs). Kertas kraft merah dengan bingkai renda putih berbentuk hati;
    foto di dalam hatinya bisa diganti pembeli (`f_hati`). **Tidak ada teks
    sama sekali** di halaman ini — desainnya memang tidak punya, dan tidak
    ada yang ditambahkan.

    > **Sumber terpisah lagi**, sesudah `LOVESTORY-2.pdf` (hal 1-10) dan
    > `LOVESTORY-4.pdf` (hal 11): sebuah PDF satu halaman kiriman pemilik
    > situs, diolah `tools/buat_pelat_hal12.py`. Tidak seperti halaman 11, halaman
    > ini TIDAK perlu didaftarkan di `TANPA_PELAT` — `LOVESTORY-2.pdf` cuma
    > 11 halaman, jadi tidak ada apa pun di sana yang bisa menimpanya.
    >
    > **Lubang fotonya tidak bisa diukur dari PDF-nya**, dan itu yang
    > membedakannya dari sepuluh halaman pertama. Di sana tiap foto pengisi
    > adalah objek gambar tersendiri, jadi bentuk lubangnya didapat dengan
    > merender halaman dua kali (pengisi putih rata / hitam rata) dan
    > mengambil selisihnya. PDF ini seluruh halamannya SATU bitmap 736x1308
    > yang sudah rata — nol objek teks, nol vektor. Bentuk hatinya karena itu
    > dipulihkan dari pikselnya sendiri.
    >
    > **Yang memisahkan renda dari foto adalah SATURASI, bukan kecerahan.**
    > Cara yang paling jelas justru yang gagal: renda RGB(225,220,214) dan
    > baju putih si lelaki di dalam foto RGB(226,216,206) praktis sama
    > terangnya. Yang berbeda nada hangatnya — fotonya sepia (R-B = 20..25),
    > rendanya netral (R-B = 4..13). Dinormalkan terhadap kecerahan itu jadi
    > saturasi, dan jaraknya melebar: renda 0,04-0,05, foto 0,09-0,43,
    > kertas merah 0,55-0,66. Ambangnya 0,065; disapu 0,055-0,080 dan
    > hasilnya nyaris tidak bergerak, jadi tidak genting.
    >
    > **Sisa cacatnya ditambal dengan CERMIN, bukan dengan menurunkan
    > ambang.** Baju putih itu tetap menggigit tepi kanan sedikit; di sisi
    > kiri pada ketinggian yang sama isinya rambut dan gaun gelap, jadi
    > terbaca sempurna. Boleh dicerminkan karena hatinya terukur simetris:
    > titik tengah tiap baris mask meleset dari sumbu paling jauh 4 px, dan
    > hampir semua baris di bawah 1,5 px.
    >
    > **Lubangnya sengaja 2 px lebih besar** daripada tepi foto aslinya.
    > Cincin 1 px tepat di luar batas terukur masih menyimpan ~10% campuran
    > foto lama (saturasi 0,051 lawan 0,047 rendanya). Dua piksel dari pita
    > renda selebar ~60 px tidak terlihat; segaris wajah pasangan orang lain
    > di pinggir foto pembeli sangat terlihat.
    >
    > **Rasio dibetulkan dengan memotong ATAS dan BAWAH** (267 baris: 133
    > atas, 134 bawah), bukan diregangkan dan bukan dipotong dari samping.
    > Aman karena hatinya terukur duduk tepat di tengah gambar: kotak doily
    > y 389..920, titik tengahnya 654,5; tengah gambar 654,0.
    >
    > Bentuk hatinya datang dari LUBANG di pelat, BUKAN dari CSS. `.bingkai`
    > di template tetap persegi — kotak pembatas hatinya — dan fotonya duduk
    > di belakang pelat seperti pita halaman 8 dan logam liontin halaman 7.
    > **Jangan memberi bingkai ini `clip-path` hati sendiri**: yang memotong
    > sudah pelatnya, dan dua potongan akan saling menggerogoti.
    >
    > Skripnya **memeriksa hasilnya sendiri** sebelum menyimpan, dan harus
    > dua arah: `periksa_tanpa_sisa_foto` (tidak ada sisa foto lama di tepi
    > lubang) dan `periksa_renda_utuh` (rendanya tidak ikut termakan).
    > Perlu dua-duanya karena melebarkan lubang sampai bersih itu gampang —
    > cukup lebarkan sampai seluruh rendanya hilang.
    >
    > Satu pemeriksa sempat salah rancang dan itu instruktif: keterisian
    > kotak dipakai untuk menilai "bentuknya masih hati?", padahal hatinya
    > mengisi 67,3% kotaknya dan doily selebar penuh — persis kegagalan yang
    > mau ditangkap — 66,8%. Dua angka yang hampir sama tidak membedakan apa
    > pun. Diganti perbandingan kotak hati terhadap kotak doily (~73%).
    >
    > Penjaga di sisi situs: `Halaman12Tests`. Yang terpenting di sana
    > mencocokkan koordinat persen `.bingkai` di `valentine.html` dengan
    > kotak alfa yang sesungguhnya di `hal12.webp` — dua benda di berkas
    > berbeda yang bisa bergeser sendiri-sendiri tanpa satu pun tes lain
    > merah, dan kalau meleset yang muncul di sisi yang kurang bukan foto
    > melainkan `--kertas-bg` merah.

  - Penjaganya di `cards/tests/test_valentine.py`.

  > **Perubahan desain 11 Agu 2026** (`LOVESTORY-2.pdf`), hasil banding
  > piksel demi piksel dengan ekspor lama. Hal 1, 2, 5, 7, 9 **identik**
  > (0 piksel beda). Yang berubah: hal 3 daftar isi ("Table Of Contents" →
  > "Contents", baris LOVE COUPONS dicabut, nomor disesuaikan); hal 4 warna
  > bingkai coretan (merah terang → merah tua); hal 6 latar (bulatan hitam →
  > tekstur rajut krem); hal 10 halaman baru; hal 11 penutup krem.
  >
  > **Gema putih di teks hal 6 ikut dicabut.** Dulu `.t-t6a/.t-t6b` punya
  > `text-shadow: 0 .17em 0 #fff` (efek "lift" Canva), dan itu memang perlu
  > selama latarnya bulatan hitam. Di ekspor baru pemilik situs mematikan
  > efeknya — terbukti dari PDF-nya: dulu tiap baris tertulis TIGA kali
  > (satu salinan putih digeser 4,8pt), sekarang sekali. Jangan pasang lagi
  > tanpa memeriksa Canva-nya dulu.

  > **Salah ketik desain: SUDAH SELESAI KEDUANYA.** "4ND" → "4TH" diubah di
  > `seed_templates` (11 Agu 2026). "OUR LOVE LANGUANGE" dulu terkunci di
  > dalam gambar dan menunggu PDF perbaikan; penantian itu **selesai dengan
  > sendirinya 19 Agu 2026** begitu daftar isinya jadi teks HTML — sekarang
  > tertulis "OUR LOVE LANGUAGE" sebagai bawaan `isi2`. Tidak ada lagi PDF
  > yang perlu ditunggu.
  >
  > Catatan: `LOVESTORY-3.pdf` (16 Agu 2026) yang ada di ~/Downloads BUKAN
  > perbaikan — kesebelas halamannya identik piksel demi piksel dengan
  > `LOVESTORY-2.pdf`. `SRC` di skripnya boleh tetap menunjuk yang -2.
  > **Satu-satunya yang ditambahkan** ke desainnya: bayangan lipatan
  > punggung buku di tepi kiri dan efek cahaya saat lembar dibalik.

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
