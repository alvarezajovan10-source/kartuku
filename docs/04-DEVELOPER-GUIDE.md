# Developer Guide — Kartuku

> Panduan onboarding untuk programmer baru **atau AI baru** yang melanjutkan proyek ini.
> Format checklist. Kerjakan berurutan — urutannya disusun supaya kamu tidak membaca
> sesuatu sebelum punya konteks untuk memahaminya.

---

## 1. Langkah Orientasi Awal

### 1.1 Urutan baca (dan kenapa urutan itu)

Jangan langsung buka `views.py`. Ia 894 baris dan tidak akan masuk akal tanpa
memahami `Template.config` lebih dulu.

- [ ] **1. `docs/01-PROJECT-BIBLE.md` §1–2** — apa produknya dan fitur apa saja yang ada.
      *Kenapa pertama:* setiap keputusan aneh di kode ini punya alasan produk. Tanpa
      tahu produknya, kamu akan mengira banyak hal sebagai bug.

- [ ] **2. `docs/01-PROJECT-BIBLE.md` §5 (Database)** — skema lengkap.
      *Kenapa kedua:* `GiftCard` punya 27 kolom dan tiga di antaranya JSON. Semua kode
      berputar di sekitar tabel ini.

- [ ] **3. `cards/models.py`** (336 baris) — baca utuh.
      *Kenapa ketiga:* di sinilah `Template.config` diterjemahkan jadi perilaku
      (`text_specs()`, `frames()`, `renderer()`). Ini **jantung sistem**. Method-method
      itu yang dipanggil view, API, dan template render.

- [ ] **4. `cards/management/commands/seed_templates.py`** — lihat `Template.config`
      sungguhan untuk dua template yang ada.
      *Kenapa keempat:* setelah membaca models, kamu butuh melihat isinya yang nyata.
      Ini contoh konkret dari yang baru kamu baca secara abstrak.

- [ ] **5. `docs/01-PROJECT-BIBLE.md` §6 (Rute)** — 30 rute, dan **catatan urutan rute**.
      *Kenapa kelima:* pola `<str:ref>/` tangkap-semua di posisi terakhir adalah hal
      paling mudah dirusak tanpa sadar di proyek ini.

- [ ] **6. `cards/views.py`** — sekarang baru masuk akal.
      Mulai dari `public_card` → `_render_card` (jalur terpendek), lalu `editor`.

- [ ] **7. `cards/styles.py`** — gerbang keamanan CSS.
      *Kenapa:* kamu akan menyentuhnya begitu ada permintaan "bisa nggak fontnya…".

- [ ] **8. `docs/02-TECHNICAL-DOCUMENTATION.md` §2.3** — protokol editor↔iframe.
      *Kenapa terakhir:* ini bagian tersulit, dan butuh semua konteks di atas.

- [ ] **9. `payments/lynk.py` + `payments/webhooks.py`** — hanya kalau tugasmu menyentuh uang.

- [ ] **10. `CLAUDE.md` §2, §6.2, §7, §12, §13** — keputusan yang dikunci, aturan
      webhook, batasan keamanan, edge case, dan jebakan lingkungan.
      ⚠️ **Lewati §5 dan §10** — dua bagian itu sudah usang; yang benar ada di Bible.

### 1.2 Menjalankan pertama kali

- [ ] Pastikan Python 3.12 dan `uv` tersedia
      (`brew python@3.12` di Mac ini rusak — `uv` adalah jalur yang bekerja)
- [ ] ```bash
      cd ~/giftcard
      uv venv .venv --python 3.12        # kalau .venv belum ada
      uv pip install -r requirements.txt
      cp .env.example .env
      ```
- [ ] Isi `.env` minimal: `DJANGO_SECRET_KEY` (apa saja untuk dev), `DJANGO_DEBUG=True`
- [ ] ```bash
      .venv/bin/python manage.py migrate
      .venv/bin/python manage.py seed_templates
      .venv/bin/python manage.py createsuperuser
      .venv/bin/python manage.py runserver
      ```
- [ ] **Buka `http://localhost:8000/` — BUKAN `http://127.0.0.1:8000/`**
- [ ] Cek `/admin/` bisa dibuka dengan superuser yang baru dibuat
- [ ] Cek `/preview/klasik-ulang-tahun/` menampilkan kartu contoh dengan bar "Contoh"
- [ ] (opsional) Foto contoh untuk preview: `.venv/bin/python manage.py make_sample_photos`

**Di mesin dev ini, server sudah dijalankan `launchd`** — otomatis menyala saat login.
Kalau `runserver` gagal dengan "port already in use", server itu sudah jalan. Cukup
buka `http://localhost:8000/`.

```bash
launchctl kickstart -k gui/$UID/com.kartuku.server   # restart penuh
tail -f ~/giftcard/server.log                        # lihat log
```

### 1.3 Verifikasi kamu sudah paham (uji diri, 10 menit)

Kalau bisa menjawab kelimanya tanpa membuka kode, kamu siap kerja:

- [ ] Di mana daftar teks yang bisa diedit user untuk sebuah template disimpan?
- [ ] Apa yang terjadi kalau user memilih slug `harga` untuk kartunya?
- [ ] Kenapa halaman `/pay/<uuid>/` boleh dibuka orang yang bukan pemilik sesi?
- [ ] Kenapa `card.save()` polos berbahaya di `api_photos.save_content`?
- [ ] Kenapa `verify_signature` mengembalikan `False` saat merchant key kosong,
      bukannya melewatkan pemeriksaan?

> Jawabannya: (1) `Template.config["texts"]`; (2) ditolak — `reserved_slugs()`
> membangun daftar terlarang dari `urlpatterns` nyata; (3) sesi bisa hilang, dan
> buktinya (REF ID) yang menjaga, bukan sesi; (4) bisa menimpa status `paid` kembali
> jadi `pending` dan menghapus `paid_at`; (5) tanpa kunci, tanda tangannya bisa
> dihitung siapa pun yang membaca payload.

---

## 2. Aturan Main / Konvensi Proyek

### 2.1 Coding style

**Tidak ada linter, formatter, atau CI di repo ini.** Tidak ada `pyproject.toml`,
`setup.cfg`, `ruff.toml`, `.flake8`, `.pre-commit-config.yaml`, maupun `.github/`.
Konvensi ditegakkan lewat **test dan review**, bukan alat otomatis.

Gaya yang konsisten di seluruh kode:

| Aturan | Contoh |
|---|---|
| Indentasi 4 spasi, panjang baris ~88–90 char | — |
| Import dikelompokkan: stdlib → Django → pihak ketiga → lokal | lihat `cards/views.py:1-22` |
| Nama fungsi/variabel Inggris; **nama command & sebagian helper Indonesia** | `buat_kode`, `hapus_template`, `_aktifkan`, `gagal()`, `hapus_berkas_foto` |
| Docstring & komentar **bahasa Indonesia** | — |
| Nama test method & class boleh Indonesia | `test_kategori_tanpa_template_ditandai_coming_soon` |

**Aturan komentar yang paling penting di proyek ini:**

> Komentar menjelaskan **KENAPA**, bukan **APA**. Sebagian besar komentar panjang di
> kode ini adalah catatan bug nyata yang pernah terjadi dan biaya yang ditimbulkannya.
> **Baca sebelum "merapikan".** Menghapus komentar itu = menghapus satu-satunya catatan
> kenapa kodenya ditulis begitu.

Contoh yang menunjukkan standarnya (`config/urls.py:12-23`):

```python
def favicon(request):
    """Browser meminta /favicon.ico sendiri, tanpa diminta halaman.

    Rute tangkap-semua `<str:ref>` di cards/urls.py menyambarnya dan mencarinya
    sebagai slug kartu di database — satu query sia-sia tiap kunjungan, lalu
    404. Rutenya harus di ATAS include cards.urls supaya tertangkap lebih dulu.

    Alamat statisnya dihitung saat permintaan datang, BUKAN saat modul di-import.
    …
    """
```

### 2.2 Aturan template

| Aturan | Kenapa |
|---|---|
| **`{% comment %}…{% endcomment %}` untuk komentar >1 baris** | `{# … #}` hanya berlaku satu baris; sisanya **tercetak ke halaman**. Sudah bocor 4× ke situs live |
| **`{% static_v 'path' %}`, bukan `{% static %}`** untuk CSS/JS | Cache-busting `?v=mtime`. Tanpa itu browser memakai versi lama |
| Template render (`cards/render/*.html`) **berdiri sendiri**, bukan `{% extends %}` | Kartu bukan halaman situs — tidak boleh ada header/footer/nav |
| Template render **wajib** `{% include "cards/_preview_bar.html" %}` sebelum `</body>` | Tanpa itu halaman preview tidak menandai dirinya sebagai contoh |
| Bungkus tiap bagian dengan `{% if %}` | Pengirim boleh mengosongkan foto/video/bunga; template tidak boleh menyisakan kotak kosong |
| CSS baca dari var dengan fallback: `var(--f, <bawaan>)` | Var hanya diemit kalau user mengubahnya |

### 2.3 Git workflow

Diamati dari riwayat commit — **belum pernah ditulis sebagai aturan formal**:

| Hal | Praktik saat ini |
|---|---|
| Branch | Satu branch: `main`. Ada `remotes/origin/main`. Tidak ada branch fitur di riwayat |
| Commit message | **Bahasa Indonesia, deskriptif, ~48–74 karakter**, menjelaskan **dampak** bukan mekanisme |
| Prefix | **Tidak ada** conventional-commits (`feat:`, `fix:`) |
| PR / review | Tidak ada `.github/`, tidak ada template PR, tidak ada CI |
| Yang tidak di-commit | `.env`, `db.sqlite3`, `media/`, `staticfiles/`, `.venv/`, `*.log`, `design/coquette-uji.html` |

Contoh commit yang mewakili gayanya:

```
Pembeli yang kehilangan sesinya bisa mengambil kartunya lagi
Teks pembayaran ikut metode yang aktif, sisakan 2 template Birthday
Hitung alamat favicon saat permintaan, bukan saat import
Komentar bocor ke panel editor, dan penjaganya diperluas ke semua template
```

Perhatikan: subjeknya menyebutkan **siapa yang terbantu** atau **apa yang berubah
bagi pengguna**, bukan berkas apa yang disentuh.

> ⚠️ **Perlu konfirmasi dari developer:** apakah gaya di atas memang aturan yang
> disengaja dan harus diikuti, atau sekadar kebiasaan satu orang? Dan apakah proses
> PR akan diperkenalkan kalau ada kontributor kedua?

### 2.4 Hal yang HARUS dihindari

Semua di bawah ini adalah **anti-pattern yang benar-benar pernah terjadi** di proyek
ini, diambil dari komentar kode dan docstring test.

- [ ] ❌ **`{# … #}` untuk komentar lebih dari satu baris.**
      Bocor ke situs live 4×; catatan TODO sempat terbaca pengunjung di halaman
      Testimoni, dan komentar panjang muncul di panel editor yang dilihat pembeli.
      → Dijaga `cards/tests/test_page_hygiene.py`.

- [ ] ❌ **`card.save()` polos di jalur editor.**
      Menulis SELURUH kolom dari objek yang sudah basi. Kalau webhook menandai kartu
      `paid` di antara pembacaan dan penyimpanan, autosave menimpanya kembali jadi
      `pending` dan menghapus `paid_at`. **Pembeli sudah bayar, kartunya tetap terkunci.**
      → Pakai `save(update_fields=[…])`.

- [ ] ❌ **Widget dengan `allow_multiple_selected` tanpa field pasangannya.**
      Membuat SEMUA unggahan gagal diam-diam sementara test lain tetap hijau.
      → `cards/forms.py:MultipleFileField`.

- [ ] ❌ **Satuan viewport untuk font sementara lebar kontainer tidak.**
      Kartu yang disunting di HP berubah pemenggalan barisnya saat dibuka di laptop.
      → Kanvas kanonis 390 px + penskalaan (`card-stage.js`). Dijaga `test_render_css.py`.

- [ ] ❌ **Memanggil `static()` di tingkat modul.**
      Memaksa backend staticfiles disiapkan sebelum Django selesai memuat — `manage.py
      migrate` pun gagal, dan pesan errornya menuding `urls.py`, jauh dari penyebabnya.
      → Hitung di dalam fungsi view.

- [ ] ❌ **`:src` reaktif pada iframe preview.**
      Preview memuat ulang dan balik ke sampul begitu draft pertama dibuat.
      → `reloadFrame()` manual.

- [ ] ❌ **Menyimpan state di variabel closure luar objek Alpine.**
      Alpine tidak melacaknya; panel tidak pernah render ulang. Akibat nyatanya: kolom
      caption tidak muncul, dan hampir tidak ada pembeli yang tahu kartunya bisa diberi caption.
      → Taruh di dalam `x-data`.

- [ ] ❌ **`try` di luar `transaction.atomic()` saat menangkap `IntegrityError`.**
      Meninggalkan transaksi dalam keadaan rusak di PostgreSQL — semua query sesudahnya
      gagal. **SQLite memaafkannya, jadi bug ini tidak terlihat di dev.**
      → `atomic()` di DALAM `try`.

- [ ] ❌ **`select_for_update()` untuk klaim kode/kuota.**
      SQLite tidak mendukung row-lock dan Django mengabaikannya **diam-diam** — dua
      permintaan bersamaan bisa sama-sama lolos.
      → Conditional UPDATE (`UPDATE … WHERE used_at IS NULL`).

- [ ] ❌ **Meloloskan verifikasi saat kunci gateway kosong.**
      Tanpa kunci, tanda tangannya bisa dihitung siapa pun yang membaca payload —
      orang bisa mengarang "pembayaran" untuk mencetak kartu gratis.
      → `return False`.

- [ ] ❌ **Daftar literal untuk hal yang bisa diturunkan dari kode.**
      Lima halaman sempat luput dari daftar slug terlarang karena ditambahkan setelah
      daftarnya ditulis. Slug yang menabrak halaman **rusak diam-diam**, tanpa error apa pun.
      → `reserved_slugs()` membangunnya dari `urlpatterns`.

- [ ] ❌ **Menaruh sesuatu di bawah pola `<str:ref>/` di `cards/urls.py`.**
      Tidak akan pernah tercapai.

- [ ] ❌ **Menghapus rute `/g/<ref>/`.**
      Link itu sudah terlanjur dibagikan ke penerima kartu dan tidak boleh mati.

- [ ] ❌ **Menaruh foto pembeli di tag Open Graph.**
      Server WhatsApp/Instagram/Facebook ikut mengambil dan menyimpannya; kalau linknya
      diteruskan ke grup, fotonya terpampang di daftar chat semua orang.
      → Pakai gambar merek. Dijaga `cards/tests/test_social.py`.

- [ ] ❌ **Menautkan ke `/admin/` atau menulis instruksi developer di halaman pembeli.**
      Galeri kategori kosong pernah menampilkan "Tambahkan lewat admin" lengkap dengan
      tautannya — instruksi untuk developer, dibaca calon pembeli.
      → Dijaga `test_page_hygiene.py`.

- [ ] ❌ **Menyalakan `DJANGO_DEBUG=True` di produksi.**
      Dashboard `/kartu-saya/` (memuat nama penerima dan link kartu orang lain) dan
      tombol "Aktifkan tanpa bayar" langsung terbuka untuk umum.

- [ ] ❌ **Memakai `grandTotal` untuk memeriksa kecukupan pembayaran Lynk.**
      Itu yang **diterima penjual setelah potongan** — selalu lebih kecil dari harga
      jual, jadi semua pembayaran sah akan ditolak.
      → `totalPrice` untuk nominal, `grandTotal` hanya untuk tanda tangan.

---

## 3. Checklist Sebelum Mulai Kerja

- [ ] Sudah baca **Project Bible** (`docs/01-PROJECT-BIBLE.md`)
- [ ] Sudah baca **Technical Documentation** (`docs/02-TECHNICAL-DOCUMENTATION.md`)
- [ ] Sudah setup environment lokal & proyek berhasil jalan
      (`http://localhost:8000/` terbuka, `/admin/` bisa login, `/preview/klasik-ulang-tahun/`
      menampilkan kartu)
- [ ] Sudah paham struktur database (bisa menjawab: berapa model, mana yang PK-nya UUID,
      kenapa `LynkOrder` tidak punya FK ke `GiftCard`)
- [ ] Sudah jalankan `python manage.py test` **dan tahu berapa yang lolos**
      ⚠️ Suite berisi 267 test di 12 berkas; status lolos/gagal belum diverifikasi
      saat dokumen ini ditulis — kamu orang pertama yang harus memastikannya
- [ ] Sudah cek daftar known issues / TODO di §4 di bawah
- [ ] Sudah tahu di mana log berada (`~/giftcard/server.log`) dan cara restart penuh
      (`launchctl kickstart -k gui/$UID/com.kartuku.server`)

---

## 4. Known Issues & TODO

Hasil sapuan `grep -rn "TODO\|FIXME\|XXX\|HACK\|BUG:"` di seluruh repo (tanpa `.venv/`,
`staticfiles/`, `.git/`) pada 6 Agustus 2026.

### 4.1 TODO yang benar-benar ada di kode

**Hanya satu.** Repo ini luar biasa bersih dari TODO — sebagian besar catatan
ditulis sebagai komentar penjelas, bukan penanda pekerjaan tertunda.

| Lokasi | Isi | Status |
|---|---|---|
| `cards/templates/cards/pages/testimonials.html:10` | "TODO: ganti dengan testimoni asli dari pengguna sungguhan" | **Keputusan produk, bukan utang teknis.** Halaman sengaja kosong dan jujur — testimoni karangan merusak kepercayaan dan berisiko secara hukum. Aman ditulis di `{% comment %}` karena tidak ikut ke HTML |

Empat hit lain dari `grep` adalah **false positive**: `if not DEBUG` /`if settings.DEBUG`
(kata "BUG" di dalam "DEBUG"), `KRT-XXXX-XXXX` (contoh format kode), dan penyebutan
kata "TODO" di dalam `test_page_hygiene.py` yang justru **menjaganya** agar tidak bocor.

### 4.2 Temuan dari pembacaan kode (bukan ditandai TODO)

| Temuan | Lokasi | Dampak |
|---|---|---|
| `init.palettes` selalu `undefined` | `static/js/alpine-editor.js:40` | `styles.PALETTES` (8 palet) tidak pernah dikirim `views.editor` ke `editor_init`. Kalau ada UI yang meng-iterasinya, ia diam-diam kosong |
| `PhotoUploadForm` / `MultipleFileField` / `MultipleFileInput` tidak dipakai | `cards/forms.py:146-176` | Tidak diimpor di mana pun, tidak disentuh test mana pun. Sisa dari era sebelum unggah pindah ke `api_photos.py`. Docstring-nya masih berharga sebagai catatan sejarah |
| `transaction` diimpor tapi tidak dipakai | `cards/views.py:8` | Kosmetik |
| Renderer `kanvas` tidak dirujuk template mana pun | `cards/templates/cards/render/kanvas.html` | Hanya dibuat di `test_render_css.py` |
| `qr_png` tidak punya test | `cards/views.py:844` | Fitur pasca-bayar yang dilihat setiap pembeli, tanpa penjaga |

### 4.3 Pekerjaan besar yang tertunda (dari `CLAUDE.md` §13)

| Pekerjaan | Status per catatan terakhir | ⚠️ |
|---|---|---|
| Deploy PythonAnywhere | "belum dikerjakan, tertahan: repo belum punya remote GitHub" | Sudah usang — `remotes/origin/main` sekarang ada, dan `tools/pa.py` mengasumsikan user `kartuku` sudah aktif. **Konfirmasi apakah situs sudah online** |
| Webhook Lynk.id | "butuh situs online lebih dulu" | Handler sudah ditulis lengkap + 18 test. **Konfirmasi apakah `LYNK_MERCHANT_KEY` sudah terisi di produksi** |
| Midtrans QRIS | "sengaja ditunda" | Kode lengkap & teruji, gateway tidur. **Konfirmasi kapan diaktifkan** |
| Fitur pesan video | "ditunda, bukan ditolak" — syarat: sudah di VPS, simpan di R2, batas 30 dtk/25 MB, konversi H.264 | **Konfirmasi masih di rencana atau dibatalkan** |
| Template Anniversary / Love Story / Proposal | Belum ada; tampil "Coming soon" di situs | Menambah 1 template = §3.2 di Technical Documentation |
| Cloudflare R2 | Kode lengkap, `USE_R2=False` | Aktif kalau `media/` mulai membebani disk |

---

## 5. Kontak & Sumber Referensi

### 5.1 Dokumentasi eksternal library yang dipakai

| Library | Dokumentasi | Bagian yang paling sering dibuka |
|---|---|---|
| Django 5.2 | https://docs.djangoproject.com/en/5.2/ | Model fields, `update_fields`, `transaction.atomic`, template tags |
| Django REST Framework | https://www.django-rest-framework.org/ | `@api_view`, throttling |
| django-environ | https://django-environ.readthedocs.io/ | `env.db_url`, `env.list`, `env.int` |
| WhiteNoise | https://whitenoise.readthedocs.io/ | `CompressedStaticFilesStorage`, urutan middleware |
| Pillow | https://pillow.readthedocs.io/ | `Image.verify()`, `thumbnail()`, `ImageDraw` |
| django-storages (S3/R2) | https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html | Opsi `S3Storage` untuk R2 |
| python-qrcode | https://github.com/lincolnloop/python-qrcode | `get_matrix()`, error correction |
| Alpine.js | https://alpinejs.dev/ | `x-data`, `x-show`, `x-for`, `@click.outside` |

### 5.2 Dokumentasi gateway & layanan

| Layanan | Dokumentasi | Catatan |
|---|---|---|
| Midtrans Core API | https://docs.midtrans.com/reference/core-api-overview | QRIS charge, format signature, simulator sandbox |
| Lynk.id Webhook | Dashboard Lynk → **Settings → Integrations → Webhook** | **Merchant Key baru muncul setelah URL disimpan.** Ada tombol "Test URL" + Webhook History |
| YouTube IFrame Player API | https://developers.google.com/youtube/iframe_api_reference | Kode error 101/150 (diblokir), 153 (referrer policy) |
| YouTube Data API v3 | https://developers.google.com/youtube/v3/docs/videos | `part=status` → `embeddable`, `privacyStatus` |
| PythonAnywhere API | https://help.pythonanywhere.com/pages/API | Dipakai `tools/pa.py` |

### 5.3 Dokumen internal

| Berkas | Isi | Keakuratan |
|---|---|---|
| `docs/01-PROJECT-BIBLE.md` | Produk, fitur, struktur, database, rute, alur | Terverifikasi 6 Agu 2026 |
| `docs/02-TECHNICAL-DOCUMENTATION.md` | Justifikasi teknologi, graf import, panduan fitur & debugging, setup | Terverifikasi 6 Agu 2026 |
| `docs/03-MASTER-PROMPT.md` | Prompt siap paste untuk AI lain | Terverifikasi 6 Agu 2026 |
| `docs/04-DEVELOPER-GUIDE.md` | Dokumen ini | — |
| `../CLAUDE.md` | Blueprint + keputusan yang dikunci + catatan status | **§5 dan §10 usang.** §2, §6.2, §7, §12, §13 masih berharga |
| `../README.md` | Cara menjalankan + resep menambah template | Akurat |
| `../DEPLOY.md` | Deploy PythonAnywhere + sambungan webhook Lynk | Akurat |

### 5.4 Di mana menaruh dokumentasi baru

| Jenis | Tempatnya |
|---|---|
| Fitur baru, model baru, rute baru | Perbarui `docs/01-PROJECT-BIBLE.md` di bagian yang sesuai |
| Keputusan teknis, dependency baru, jebakan baru | Perbarui `docs/02-TECHNICAL-DOCUMENTATION.md` |
| Aturan baru yang harus diketahui AI | Perbarui `docs/03-MASTER-PROMPT.md` |
| Anti-pattern baru yang ketahuan menggigit | Tambahkan ke §2.4 dokumen ini **dan** tulis test-nya |
| Alasan sebuah baris kode ditulis begitu | **Komentar di kode itu sendiri**, bukan di `docs/` |
| Langkah operasional deploy | `../DEPLOY.md` |

**Jangan** membuat berkas `docs/05-…`, `docs/06-…` untuk tiap fitur. Empat dokumen
ini sudah punya tempat untuk hampir semua hal. Berkas baru hanya untuk topik besar
yang benar-benar tidak muat, misalnya panduan operasional gateway pembayaran ketiga.

---

## 6. Prinsip Update Dokumentasi

> **Setiap kali menambah fitur besar atau mengubah arsitektur, WAJIB update
> `docs/01-PROJECT-BIBLE.md` dan `docs/02-TECHNICAL-DOCUMENTATION.md` di PR yang sama.**

Bukan "nanti kalau sempat". Alasannya sudah terbukti di proyek ini sendiri: `CLAUDE.md`
ditulis sebagai sumber kebenaran arsitektur, lalu kode berjalan lebih cepat daripada
dokumennya. Sekarang §5 dan §10 di sana **menyesatkan** — orang yang membacanya
mendapat skema database yang salah dan daftar endpoint yang tidak lengkap. Dokumen
yang salah lebih berbahaya daripada tidak ada dokumen, karena orang mempercayainya.

Checklist sebelum commit fitur besar:

- [ ] Bible §2 — fitur baru masuk tabel, dengan lokasi file dan status
- [ ] Bible §5 — kolom/model/migrasi baru masuk tabel skema dan ERD
- [ ] Bible §6 — rute baru masuk tabel, **dan hitungan totalnya diperbarui**
- [ ] Bible §7 — kalau alur penggunanya berubah, diagram mermaid ikut diperbarui
- [ ] Technical §1 — dependency baru: **tulis alasannya**, jangan biarkan orang
      berikutnya menebak
- [ ] Technical §5.3 — env var baru
- [ ] Technical §4.2 — kalau ada gejala bug baru yang layak diingat
- [ ] Master Prompt — kalau ada aturan yang tidak boleh dilanggar
- [ ] Developer Guide §2.4 — kalau menemukan anti-pattern baru
- [ ] Test yang menjaga perilaku barunya, dengan docstring yang menjelaskan **bug
      nyatanya**, bukan mekanisme test-nya
