# Teks siap tempel untuk Lynk.id

Dua tulisan di bawah ini BUKAN bagian dari kode situs — keduanya disalin
tangan ke Lynk.id. Disimpan di sini supaya tidak tercecer dan supaya kalau
alurnya berubah, ketahuan mana yang ikut harus diubah.

**Kalau alur aktivasi berubah, dua tulisan ini WAJIB ikut diperbarui**, dan
perubahannya harus disalin ulang ke Lynk. Tidak ada yang menyalinnya secara
otomatis: situs tidak bisa menyunting halaman produk orang lain.

Nama tombol di bawah ditulis persis seperti yang terlihat pembeli. Kalau
tombolnya kelak diganti nama, kalimat ini ikut bohong.

---

## 1. Pesan setelah checkout

Tempel di Lynk.id → produk → kolom pesan terima kasih / konten digital yang
dikirim ke pembeli.

Sengaja dibuka dengan REF ID, bukan dengan ucapan terima kasih: pembeli yang
baru selesai membayar sedang mencari satu hal — apa yang harus saya lakukan
sekarang. Ucapan basa-basi di baris pertama mendorong jawabannya turun.

```
Terima kasih! Pembayaranmu sudah kami terima.

Simpan REF ID di email struk ini — itu kunci untuk mengaktifkan kartumu.

Cara membuat kartumu:

1. Buka kartuku.pythonanywhere.com
2. Pilih template yang kamu suka, tekan "Pakai template ini"
3. Isi kartunya: nama, pesan, foto, dan lagu
4. Tekan "Generate Link" lalu "Ya, buat link"
5. Di halaman "Aktifkan kartumu", tempel REF ID dari email ini
6. Tekan "Aktifkan" — link kartumu langsung jadi

Catatan penting:
- Periksa isinya sebelum menekan "Generate Link". Setelah link dibuat, isi
  kartunya tidak bisa diubah lagi.
- REF ID sekali pakai untuk satu kartu. Beli 2, dapat 2 kartu.
- Kartunya aktif selamanya. Linknya bisa dibuka berkali-kali oleh penerima,
  tanpa biaya perpanjangan.
- Tidak perlu buru-buru. Kartumu bisa dibuat kapan saja, REF ID-nya tidak
  kedaluwarsa.

Bingung atau REF ID ditolak? Balas pesan ini, sebutkan email yang kamu
pakai saat membeli.
```

---

## 2. Deskripsi produk di Lynk

Tempel di Lynk.id → produk → deskripsi. Tugasnya menjawab keberatan SEBELUM
orang membayar, jadi urutannya: apa yang didapat, lalu apa yang sering
dikhawatirkan.

```
Kartu ucapan digital yang bisa dibuka lewat link — ada foto, pesan, musik,
dan animasi. Bukan gambar diam, tapi halaman yang bisa disentuh dan
dimainkan penerima.

Yang kamu dapat:
- 1 kartu digital, link aktif selamanya
- Pilih template: Amplop Merah, Scrapbook Cerita, atau Game 8-Bit
- Foto, pesan, dan lagu YouTube sebagai musik latar
- Tanpa iklan, tanpa watermark, tanpa biaya perpanjangan

Cara pakai setelah membeli:
Kamu dapat REF ID di email struk. Buka kartuku.pythonanywhere.com, buat
kartunya, lalu tempel REF ID untuk mengaktifkan. Panduan lengkapnya ikut
terkirim setelah pembayaran.

Sering ditanyakan:

Bisa dibuka di HP?
Bisa, di HP maupun laptop. Penerima tidak perlu memasang aplikasi apa pun.

Kartunya aktif berapa lama?
Selamanya. Tidak ada biaya perpanjangan.

Bisa upload lagu sendiri?
Belum. Lagu dipakai lewat link YouTube supaya kartunya ringan dibuka.
Link Spotify tidak bisa — Spotify melarang lagunya diputar otomatis di luar
aplikasinya, jadi kartunya akan bisu.

Bisa diedit setelah jadi?
Periksa dulu sebelum membuat link. Setelah link dibuat, isinya dikunci.

Kartunya bisa dilihat orang lain?
Hanya yang punya linknya. Alamatnya memakai kode acak yang tidak bisa
ditebak.

Saya beli 2, dapat 2 kartu?
Ya. REF ID yang sama bisa dipakai sebanyak jumlah yang kamu beli.
```

---

## Hal yang gampang salah saat menulis ulang teks ini

- **REF ID bukan kode KRT.** REF ID datang dari Lynk dan lahir dari webhook
  yang tanda tangannya diverifikasi. Kode `KRT-...` dibuat manual lewat
  `manage.py buat_kode` dan cuma jalan keluar kalau webhook gagal atau untuk
  kartu gratis. Jangan menyuruh pembeli mencari "kode" — yang mereka punya
  namanya REF ID.
- **Jangan menjanjikan email dari Kartuku.** Situs ini tidak mengirim email
  apa pun. Satu-satunya email yang pembeli terima adalah struk dari Lynk.
- **Jangan menulis "kartunya langsung jadi setelah bayar".** Membayar hanya
  memberi hak pakai; kartunya tetap harus dibuat sendiri oleh pembeli.
- **Jangan menjanjikan kartunya bisa disunting setelah aktif.** Tidak bisa —
  ketiga endpoint penyimpanan menolak kartu yang sudah lunas. Kalimat "nanti
  bisa diperbaiki" akan langsung terbukti bohong pada orang yang salah ketik.
- **Draft terikat ke satu browser**, bukan ke akun. Menyuntingnya harus dari
  browser yang sama. Yang bebas perangkat cuma aktivasinya: link halaman
  aktivasi + REF ID sudah cukup dari mana pun.
