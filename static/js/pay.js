/* Halaman QRIS — pasangan dari cards/pay.html.
 *
 * Alamat endpoint dan token CSRF dibaca dari data-attribute #pay-root; dulu
 * semuanya dicetak Django langsung ke dalam skrip ini.
 */
(function () {
  const root = document.getElementById("pay-root");
  // Blok QRIS tidak dirender kalau Midtrans belum dikonfigurasi — halaman
  // hanya menampilkan penukaran kode akses, dan skrip ini tidak ada gunanya.
  if (!root) return;
  const payUrl = root.dataset.payUrl;
  const statusUrl = root.dataset.statusUrl;
  const successUrl = root.dataset.successUrl;
  const csrfToken = root.dataset.csrf;

  const qrArea = document.getElementById("qr-area");
  const statusLine = document.getElementById("status-line");
  const retryBtn = document.getElementById("retry");

  let pollTimer = null;

  // Isi #qr-area lewat DOM, bukan innerHTML: nilainya datang dari respons
  // gateway, jadi jangan pernah ditempel sebagai HTML mentah.
  function setHint(message) {
    const hint = document.createElement("p");
    hint.className = "hint";
    hint.textContent = message;
    qrArea.replaceChildren(hint);
  }

  function showError(message) {
    setHint(message);
    retryBtn.hidden = false;
  }

  function showQr(url) {
    const img = document.createElement("img");
    img.alt = "Kode QRIS";
    img.src = url;
    qrArea.replaceChildren(img);
  }

  async function createCharge() {
    retryBtn.hidden = true;
    setHint("Menyiapkan kode QR…");
    try {
      const response = await fetch(payUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
      });
      const data = await response.json();

      if (data.redirect) { window.location = data.redirect; return; }
      if (!response.ok) { showError(data.detail || "Gagal membuat QR."); return; }

      if (!data.qr_image_url) {
        showError("Midtrans tidak mengirim gambar QR.");
        return;
      }
      showQr(data.qr_image_url);
      // QR yang dipakai ulang = halaman ini dimuat ulang saat QR lama masih
      // hidup. Katakan apa adanya supaya user tidak mengira ada yang gagal.
      statusLine.textContent = data.reused
        ? "Kode QR sebelumnya masih berlaku — silakan scan."
        : "Menunggu pembayaran…";
      startPolling();
    } catch (err) {
      showError("Koneksi bermasalah. Coba lagi.");
    }
  }

  async function poll() {
    try {
      const response = await fetch(statusUrl);
      const data = await response.json();
      if (data.status === "paid") {
        clearInterval(pollTimer);
        statusLine.textContent = "Pembayaran diterima. Mengalihkan…";
        window.location = successUrl;
      } else if (data.status === "expired") {
        clearInterval(pollTimer);
        statusLine.textContent = "QR sudah kedaluwarsa.";
        showError("Kode QR kedaluwarsa.");
      }
    } catch (err) {
      /* jaringan sesaat bermasalah — coba lagi di tick berikutnya */
    }
  }

  function startPolling() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(poll, 4000);
  }

  retryBtn.addEventListener("click", createCharge);
  createCharge();
})();
