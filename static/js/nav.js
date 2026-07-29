// Tutup menu burger setelah link diklik. Link anchor tidak memicu reload,
// jadi tanpa ini menu tetap terbuka menutupi konten di HP.
(function () {
  var toggle = document.getElementById("nav-toggle");
  document.querySelectorAll(".site-nav a").forEach(function (link) {
    link.addEventListener("click", function () { toggle.checked = false; });
  });
})();
