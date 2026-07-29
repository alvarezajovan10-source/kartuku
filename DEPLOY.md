# Deploy ke PythonAnywhere (gratis)

Panduan ini menaruh Kartuku di `https://kartuku.pythonanywhere.com` — alamat
tetap yang tidak berubah, tidak tidur, dan tidak butuh laptop menyala.

Alur pembayaran: pembeli membayar di **Lynk.id**, Lynk memberi tahu situs ini
lewat **webhook**, lalu pembeli mengaktifkan kartunya sendiri dengan menempelkan
**REF ID** dari email strukmu. Tidak ada kode yang perlu kamu kirim manual, dan
situs tidak perlu mengirim email sama sekali. Midtrans dibiarkan kosong.

---

## 1. Siapkan akun

1. Daftar gratis di **pythonanywhere.com** (paket *Beginner*, $0)
2. Catat username — itu jadi bagian alamat situsmu

## 2. Naikkan kodenya

Buka **Consoles → Bash** di PythonAnywhere, lalu:

```bash
git clone <url-repo-mu> giftcard
cd giftcard
```

Kalau kodenya belum ada di GitHub, buat repo privat dulu dan push dari laptop.
Alternatif tanpa git: zip foldernya, unggah lewat tab **Files**, lalu `unzip`.

Jangan sertakan `.env`, `db.sqlite3`, `media/`, dan `.venv/` — semuanya sudah
diabaikan `.gitignore`.

## 3. Virtualenv & dependensi

```bash
mkvirtualenv kartuku --python=python3.12   # pakai versi tertinggi yang tersedia
pip install -r requirements.txt
```

Catat path virtualenv-nya: `/home/kartuku/.virtualenvs/kartuku`

## 4. Buat `.env` produksi

```bash
cd ~/giftcard
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
nano .env
```

Yang **wajib** diubah:

```
DJANGO_SECRET_KEY=<hasil perintah di atas>
DJANGO_DEBUG=False
ALLOWED_HOSTS=kartuku.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://kartuku.pythonanywhere.com
YOUTUBE_API_KEY=<key-mu>
LYNK_MERCHANT_KEY=          # diisi nanti di langkah 9
LYNK_MIN_AMOUNT=15000       # turunkan sementara kalau sedang uji produk murah
```

> `DJANGO_DEBUG=False` bukan formalitas. Kalau tertinggal `True`, dashboard
> `/kartu-saya/` dan tombol "Aktifkan tanpa bayar" terbuka untuk umum —
> siapa pun bisa membaca kartu pelangganmu dan membuat kartu gratis.
>
> Kunci lama dari fase dev sudah bocor ke riwayat percakapan dan laptop.
> **Selalu buat kunci baru untuk produksi.**

## 5. Siapkan database & file statis

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_templates
python manage.py createsuperuser
```

## 6. Konfigurasi web app

Tab **Web → Add a new web app → Manual configuration → Python 3.12**

Isi tiga kolom:

| Kolom | Nilai |
|---|---|
| Source code | `/home/kartuku/giftcard` |
| Working directory | `/home/kartuku/giftcard` |
| Virtualenv | `/home/kartuku/.virtualenvs/kartuku` |

Klik link **WSGI configuration file**, hapus seluruh isinya, ganti dengan:

```python
import os
import sys

path = "/home/kartuku/giftcard"
if path not in sys.path:
    sys.path.insert(0, path)

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## 7. Petakan folder media — jangan dilewati

File statis (CSS/JS) sudah ditangani WhiteNoise, tapi **foto unggahan pembeli
tidak**. Tanpa langkah ini, semua foto di kartu akan gagal dimuat.

Di tab **Web → Static files**, tambahkan satu baris:

| URL | Directory |
|---|---|
| `/media/` | `/home/kartuku/giftcard/media` |

## 8. Nyalakan

Klik tombol hijau **Reload**, lalu buka `https://kartuku.pythonanywhere.com`.

---

## 9. Sambungkan webhook Lynk.id — ini yang membuat semuanya otomatis

Di dashboard Lynk: **Settings → Integrations → Webhook**

1. Isi **URL Webhook**: `https://kartuku.pythonanywhere.com/api/webhooks/lynk/`
2. Klik **Save URL**
3. **Merchant Key baru muncul setelah URL disimpan.** Salin, lalu masukkan ke
   `.env` sebagai `LYNK_MERCHANT_KEY=...` dan **Reload** web app-mu
4. Klik **Test URL** — hasilnya muncul di **Webhook History**

> Selama `LYNK_MERCHANT_KEY` kosong, webhook **ditolak** (403) dan tidak ada
> kartu yang bisa diaktifkan lewat REF ID. Ini disengaja: tanpa kunci, tanda
> tangan bisa dihitung siapa pun yang membaca payload, dan orang bisa mengarang
> "pembayaran" untuk mencetak kartu gratis.

Lalu atur produkmu di Lynk. **Isi pengiriman produk** diganti jadi teks, bukan
file:

> Buat kartumu di sini: `https://kartuku.pythonanywhere.com/template/`
> Saat diminta aktivasi, tempel **REF ID** yang ada di email ini.

Saran: pakai beberapa produk kalau mau tiap desain punya etalase sendiri, tapi
**jangan ikat produk ke template tertentu**. Semua produk dihitung sama — "1
kartu" — dan pembeli memilih desainnya di situsmu. Kalau template diikat ke nama
produk, sekali kamu ganti nama produk atau menambah template, pemetaannya patah.

---

## Alur jualan sehari-hari

Setelah webhook tersambung, kamu tidak melakukan apa-apa:

1. Pembeli membayar di Lynk.id
2. Lynk mengirim webhook → situs mencatat "hak pakai" berisi REF ID
3. Pembeli membuka link di email struknya, memilih template, membuat kartunya
4. Pembeli menempel **REF ID** dari email yang sama → kartu langsung aktif
5. Pembeli dapat link permanen + QR untuk dibagikan

Satu REF ID hanya bisa dipakai sebanyak jumlah yang dibelinya (beli 2, dapat 2).
Kartunya sendiri permanen dan bisa dibuka berkali-kali oleh penerima — itu inti
produknya.

Pantau di **admin → Order Lynk**: REF ID mana yang masuk, siapa emailnya,
kuotanya sudah terpakai berapa.

### Kalau webhook gagal

Webhook bisa tidak sampai (situs sempat mati, salah konfigurasi). Cek
**Webhook History** di Lynk. Sebagai jalan keluar, kode manual tetap ada:

```bash
python manage.py buat_kode --catatan "nama/email pembeli"
```

Kirim kodenya ke pembeli; kolom aktivasi yang sama menerima REF ID **maupun**
kode `KRT-...`. Pakai ini juga kalau mau memberi kartu gratis ke teman.

---

## Memperbarui situs setelah ada perubahan kode

```bash
cd ~/giftcard && git pull
python manage.py migrate
python manage.py collectstatic --noinput
```
lalu **Reload** di tab Web.

---

## Batasan yang perlu diketahui

**Koneksi keluar dibatasi.** Paket gratis PythonAnywhere hanya mengizinkan
situsmu menghubungi alamat yang ada di daftar putih mereka. Situs ini memanggil
`youtube.com` (judul & cover lagu) dan `googleapis.com` (cek lagu boleh
di-embed). Kalau ternyata diblokir, kartunya **tetap jalan** — hanya judul dan
cover lagu yang kosong, karena `fetch_track_meta` sengaja dibuat gagal-aman.

**Kuota CPU harian.** Cukup untuk lalu lintas awal. Kalau TikTok-mu ramai,
naikkan paket — saat itu kamu sudah punya pemasukan.

**SQLite.** Aman di sini karena penyimpanan PythonAnywhere permanen. Pindah ke
Postgres kalau penjualan sudah rutin.

**Backup.** Unduh `db.sqlite3` dan folder `media/` secara berkala lewat tab
Files. Tidak ada backup otomatis di paket gratis, dan di dalamnya ada kartu
pelanggan yang sudah mereka bayar.
