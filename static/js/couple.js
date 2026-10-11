/* Animasi pasangan piksel — pasangan dengan cards/_couple.html & css/couple.css.
 *
 * Gerak mendatar dikerjakan JS (transform, satu rAF untuk keduanya); frame
 * sprite dikerjakan CSS (steps). Begitu terlihat, keduanya berjalan saling
 * mendekat. Ketuk cowok = gelembung "...", ketuk cewek = ia menjawab dengan
 * gelembung hati, tombol hati = mereka merapat, berpelukan, hati naik.
 */
(function () {
  "use strict";

  var hemat = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function Pasangan(akar) {
    this.akar = akar;
    this.panggung = akar.querySelector(".pasangan-panggung");
    this.cowok = { el: akar.querySelector(".tokoh-px.cowok"), x: 0, ke: 0 };
    this.cewek = { el: akar.querySelector(".tokoh-px.cewek"), x: 0, ke: 0 };
    this.peluk = akar.querySelector(".peluk-px");
    this.hati = akar.querySelector(".hati-lapis");
    this.tombol = akar.querySelector(".tombol-hati");
    this.sibuk = false;
    this.lalu = 0;
    this.selesai = null;
    this.gerak = this.gerak.bind(this);
    this.ukur();
    this.cowok.x = 0;
    this.cewek.x = this.lebar - this.cewek.w;
    this.pasang(this.cowok);
    this.pasang(this.cewek);
    this.pasangKendali();
  }

  Pasangan.prototype.ukur = function () {
    this.lebar = this.panggung.clientWidth;
    this.skala = parseFloat(getComputedStyle(this.akar).getPropertyValue("--s")) || 1;
    this.cowok.w = this.cowok.el.offsetWidth;
    this.cewek.w = this.cewek.el.offsetWidth;
    this.pelukW = 208 * this.skala;
  };

  // Tempat berdiri saat "bertemu": berjarak, di tengah panggung.
  Pasangan.prototype.titikTemu = function (rapat) {
    var tengah = this.lebar / 2;
    var celah = rapat ? -18 * this.skala : 26 * this.skala;
    return { cowok: tengah - celah / 2 - this.cowok.w, cewek: tengah + celah / 2 };
  };

  Pasangan.prototype.pasang = function (t) {
    t.el.style.setProperty("--x", t.x.toFixed(1) + "px");
  };

  Pasangan.prototype.jalanKe = function (titik, lalu) {
    this.cowok.ke = titik.cowok;
    this.cewek.ke = titik.cewek;
    this.selesai = lalu || null;
    if (hemat) {
      this.cowok.x = this.cowok.ke;
      this.cewek.x = this.cewek.ke;
      this.pasang(this.cowok);
      this.pasang(this.cewek);
      if (this.selesai) this.selesai();
      return;
    }
    this.lalu = 0;
    requestAnimationFrame(this.gerak);
  };

  Pasangan.prototype.gerak = function (t) {
    var dt = this.lalu ? Math.min((t - this.lalu) / 1000, 1 / 20) : 0;
    this.lalu = t;
    var laju = 78 * this.skala;
    var masih = false;
    [this.cowok, this.cewek].forEach(function (tk) {
      var beda = tk.ke - tk.x;
      if (Math.abs(beda) > .5) {
        masih = true;
        tk.x += Math.sign(beda) * Math.min(Math.abs(beda), laju * dt);
        tk.el.dataset.anim = "jalan";
      } else {
        tk.x = tk.ke;
        if (tk.el.dataset.anim === "jalan") delete tk.el.dataset.anim;
      }
      this.pasang(tk);
    }, this);
    if (masih) {
      requestAnimationFrame(this.gerak);
    } else if (this.selesai) {
      var f = this.selesai;
      this.selesai = null;
      f();
    }
  };

  Pasangan.prototype.bicara = function (tk, lama) {
    if (this.sibuk) return;
    tk.el.classList.add("bicara");
    tk.el.dataset.anim = "reaksi";
    clearTimeout(tk.jam);
    tk.jam = setTimeout(function () {
      tk.el.classList.remove("bicara");
      if (tk.el.dataset.anim === "reaksi") delete tk.el.dataset.anim;
    }, lama);
  };

  Pasangan.prototype.pelukan = function () {
    if (this.sibuk) return;
    var self = this;
    this.sibuk = true;
    this.tombol.disabled = true;
    [this.cowok, this.cewek].forEach(function (tk) {
      tk.el.classList.remove("bicara");
      delete tk.el.dataset.anim;
    });
    this.jalanKe(this.titikTemu(true), function () {
      var tengah = (self.cowok.x + self.cewek.x + self.cewek.w) / 2;
      self.peluk.style.setProperty("--x", (tengah - self.pelukW / 2).toFixed(1) + "px");
      self.akar.classList.add("memeluk");
      setTimeout(function () { self.hujanHati(tengah); }, hemat ? 0 : 1300);
      setTimeout(function () {
        self.akar.classList.remove("memeluk");
        self.jalanKe(self.titikTemu(false), function () {
          self.sibuk = false;
          self.tombol.disabled = false;
        });
      }, hemat ? 1800 : 4200);
    });
  };

  Pasangan.prototype.hujanHati = function (tengah) {
    if (hemat) return;
    var src = this.tombol.querySelector("img").src;
    for (var i = 0; i < 7; i++) {
      var h = document.createElement("img");
      h.src = src;
      h.alt = "";
      h.style.left = (tengah - 17 * this.skala + (Math.random() - .5) * 90 * this.skala).toFixed(0) + "px";
      h.style.bottom = (262 * this.skala).toFixed(0) + "px";   // di atas kepala
      h.style.setProperty("--dx", ((Math.random() - .5) * 60).toFixed(0) + "px");
      h.style.setProperty("--t", (1.4 + Math.random() * .9).toFixed(2) + "s");
      h.style.animationDelay = (i * .14).toFixed(2) + "s";
      h.addEventListener("animationend", function () { this.remove(); });
      this.hati.appendChild(h);
    }
  };

  Pasangan.prototype.pasangKendali = function () {
    var self = this;
    this.cowok.el.addEventListener("click", function () { self.bicara(self.cowok, 1800); });
    this.cewek.el.addEventListener("click", function () { self.bicara(self.cewek, 1800); });
    this.tombol.addEventListener("click", function () { self.pelukan(); });
    window.addEventListener("resize", function () {
      if (self.sibuk) return;
      self.ukur();
      var t = self.titikTemu(false);
      self.cowok.x = self.cowok.ke = t.cowok;
      self.cewek.x = self.cewek.ke = t.cewek;
      self.pasang(self.cowok);
      self.pasang(self.cewek);
    });
    // Berjalan mendekat begitu terlihat (bukan saat halaman dimuat di luar layar).
    var mulai = function () { self.jalanKe(self.titikTemu(false)); };
    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (isi) {
        if (isi[0].isIntersecting) { io.disconnect(); mulai(); }
      }, { threshold: .4 });
      io.observe(this.akar);
    } else {
      mulai();
    }
  };

  function nyalakan() {
    [].forEach.call(document.querySelectorAll("[data-pasangan]"), function (el) {
      if (!el.__pasangan) el.__pasangan = new Pasangan(el);
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", nyalakan);
  else nyalakan();
})();
