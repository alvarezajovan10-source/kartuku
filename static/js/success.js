/* Halaman "kartu siap dibagikan" — pasangan dari cards/success.html.
 * Alamat gambar QR dibaca dari data-attribute, dulu dicetak Django ke sini. */
document.getElementById("copy").addEventListener("click", async function () {
  const input = document.getElementById("share-link");
  input.select();
  try { await navigator.clipboard.writeText(input.value); } catch (e) { document.execCommand("copy"); }
  this.textContent = "Tersalin";
});

// Pemilih gaya QR — cukup ganti query string gambarnya.
(function () {
  const picker = document.getElementById("qr-pick");
  const base = picker.dataset.qrUrl;
  let style = "kotak", warna = "hitam";
  function refresh() {
    document.getElementById("qr-img").src = base + "?style=" + style + "&warna=" + warna;
    document.getElementById("qr-dl").href = base + "?style=" + style + "&warna=" + warna + "&download=1";
  }
  document.querySelectorAll("[data-style]").forEach(b => b.addEventListener("click", () => {
    style = b.dataset.style;
    document.querySelectorAll("[data-style]").forEach(x => x.classList.toggle("is-on", x === b));
    refresh();
  }));
  document.querySelectorAll("[data-warna]").forEach(b => b.addEventListener("click", () => {
    warna = b.dataset.warna;
    document.querySelectorAll("[data-warna]").forEach(x => x.classList.toggle("is-on", x === b));
    refresh();
  }));
})();
