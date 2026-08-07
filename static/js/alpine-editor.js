/* Editor kartu.

   Prinsip panel kiri: DIAM sampai ada yang diklik, lalu tampilkan hanya kontrol
   untuk elemen yang diklik. Tidak ada bagian yang nongkrong terus-menerus.

   Preview adalah kartu ASLI di dalam iframe, jadi yang dilihat saat mengedit
   tidak mungkin berbeda dari hasil akhirnya. Perubahan gaya dikirim lewat
   postMessage dan langsung ditempel sebagai var CSS di elemen yang sama —
   tidak ada duplikasi tampilan antara editor dan kartu.

   Semua di sini hanya untuk tampilan. Server menyaring ulang seluruh gaya dan
   teks (cards/styles.py, cards/forms.py); JS ini bukan lapisan keamanan. */

window.cardEditor = function () {
  var init = JSON.parse(document.getElementById("editor-init").textContent);

  var SCENE_LABELS = {
    cover: "Sampul", hero: "Ucapan", hub: "Hadiah", message: "Surat",
    flower: "Bunga", cake: "Kue", song: "Lagu", gallery: "Kenangan",
    // Game 8-Bit. Tanpa entri di sini, pemilih babak di editor menampilkan
    // id mentah ("powerups") alih-alih nama yang bisa dibaca pembeli.
    title: "Layar Judul", player: "Pilih Pemain", levelup: "Naik Level",
    dialog: "Surat", wishes: "Wishes", powerups: "Power Ups",
    kue: "Tiup Lilin", gameover: "Penutup",
  };

  var specByKey = {};
  init.elements.forEach(function (spec) { specByKey[spec.key] = spec; });

  return {
    cardId: init.cardId,
    style: init.style,
    fields: init.fields,
    texts: init.texts,
    gallery: init.gallery,
    /* Foto per bingkai, DI DALAM x-data supaya reaktif.
       Dulu foto disimpan di `specByKey[key].photo`. `specByKey` adalah variabel
       closure di luar objek ini, jadi Alpine tidak pernah melacaknya: menulis
       foto baru ke sana tidak memicu render ulang, dan panel tetap menampilkan
       tombol "Pilih foto" tanpa thumbnail dan TANPA kolom caption sampai user
       kebetulan memilih elemen lain lalu kembali. Akibatnya hampir tidak ada
       pembeli yang tahu kartunya bisa diberi caption.
       `specByKey` tetap dipakai untuk metadata (label, jenis) yang tidak berubah. */
    framePhotos: {},
    palettes: init.palettes,
    swatches: init.swatches,
    urls: init.urls,
    maxPhotos: init.maxPhotos,

    sel: null,
    scenes: [],
    currentScene: "",
    busy: false,
    error: "",
    saveTimer: null,

    /* Crop sebelum masuk template: antrean file menunggu dipotong */
    cropOpen: false,
    cropQueue: [],
    crop: { img: null, slot: "", zoom: 1, dx: 0, dy: 0, base: 1, drag: null },
    saveState: "",   // "" | "saving" | "saved"
    fontOpen: false,
    colorOpen: false,
    moreOpen: false,
    fontQuery: "",
    songStatus: "",      // hasil uji putar lagu; "" = belum diuji
    songOk: true,
    probePlayer: null,
    confirmOpen: false,  // dialog "yakin buat link?"

    /* ── Turunan dari elemen terpilih ─────────────────────────────────── */
    get spec() { return specByKey[this.sel] || null; },
    get kind() {
      if (this.sel === "gallery") return "gallery";
      return this.spec ? this.spec.type : null;
    },
    get label() { return this.spec ? this.spec.label : "Galeri foto"; },
    get st() { return (this.style.elements && this.style.elements[this.sel]) || {}; },
    get colors() { return this.style.colors || {}; },
    get multiline() {
      return this.kind === "text" || (this.spec && this.spec.input === "multiline");
    },
    get placeholder() {
      if (this.sel === "youtube_url")
        return "https://youtu.be/... (lagunya jadi musik latar kartu)";
      return this.kind === "text" ? "Kosongkan = pakai bawaan template" : "Tulis di sini...";
    },
    get content() {
      if (this.kind === "field") return this.fields[this.sel] || "";
      if (this.kind === "text") return this.texts[this.sel] || "";
      return "";
    },
    get photo() { return this.framePhotos[this.sel] || null; },
    /* Alamat iframe dibangun saat DIBUTUHKAN, bukan diikat reaktif —
       dulu :src reaktif membuat preview memuat ulang (dan balik ke sampul)
       begitu draft pertama kali dibuat di server. */
    frameUrl: function () {
      var q = [];
      if (this.cardId) q.push("card=" + this.cardId);
      if (this.currentScene) q.push("scene=" + encodeURIComponent(this.currentScene));
      return this.urls.frame + (q.length ? "?" + q.join("&") : "");
    },

    /* Mengganti src memuat ulang kartu dari nol, dan posisi gulirnya hilang.
       `?scene=` hanya menolong template berbabak (Birthday); Scrapbook dan
       Kanvas adalah kartu gulir panjang tanpa babak, jadi tiap kali foto
       diunggah atau caption disimpan, kartunya melompat balik ke sampul —
       user membacanya sebagai "halaman refresh sendiri".

       Posisi gulir disimpan lalu dikembalikan setelah muatan baru siap.
       Dipulihkan dua kali: saat `load` (isi sudah ada) dan sekali lagi setelah
       gambar menambah tinggi halaman, karena pemulihan pertama bisa terpotong
       oleh halaman yang saat itu masih lebih pendek. */
    reloadFrame: function () {
      var frame = this.$refs.frame;
      if (!frame) return;

      var y = 0;
      try {
        y = (frame.contentWindow && frame.contentWindow.scrollY) || 0;
      } catch (e) {
        y = 0; // beda origin — tidak akan terjadi di sini, tapi jangan sampai melempar
      }

      frame.src = this.frameUrl();
      if (!y) return;

      frame.addEventListener("load", function pulihkan() {
        frame.removeEventListener("load", pulihkan);
        var kembalikan = function () {
          try { frame.contentWindow.scrollTo(0, y); } catch (e) {}
        };
        kembalikan();
        setTimeout(kembalikan, 180);
      });
    },
    get filteredFonts() {
      var q = this.fontQuery.toLowerCase().trim();
      if (!q) return init.fontCatalog;
      return init.fontCatalog
        .map(function (group) {
          return {
            group: group.group,
            fonts: group.fonts.filter(function (f) {
              return f.name.toLowerCase().indexOf(q) !== -1;
            }),
          };
        })
        .filter(function (group) { return group.fonts.length; });
    },

    fontName: function (key) {
      return key && init.fonts[key] ? specFontName(key) : "Bawaan template";
    },
    fontCss: function (key) { return key ? init.fonts[key] : "inherit"; },
    sceneLabel: function (id) { return SCENE_LABELS[id] || id; },

    /* ── Siklus hidup ─────────────────────────────────────────────────── */
    init: function () {
      var self = this;
      // Src dipasang sekali di sini; selanjutnya hanya reloadFrame().
      this.$nextTick(function () { self.reloadFrame(); });
      // Foto yang sudah tersimpan di server dipindahkan ke state reaktif.
      init.elements.forEach(function (spec) {
        if (spec.photo) self.framePhotos[spec.key] = spec.photo;
      });
      if (!this.style.elements) this.style.elements = {};
      if (!this.style.colors) this.style.colors = {};
      // Warna bawaan template jadi titik awal supaya pemilih warna tidak kosong.
      init.elements.forEach(function (spec) {
        if (spec.type === "surface" && !self.style.colors[spec.key]) {
          self.style.colors[spec.key] = spec.value;
        }
      });

      /* Bentuk bingkai pratinjau MENGIKUTI kartunya, bukan sebaliknya.
         Sebelumnya bingkainya dipaku 390x844 (proporsi HP) untuk semua
         template. Itu benar selama semua kartu tegak, dan diam-diam salah
         begitu ada kartu mendatar 16:9: kartunya diperas jadi pita 390x219
         di tengah kotak HP — sekitar 0,4x ukuran sebenarnya. Akibatnya bukan
         cuma "kelihatan kecil". Detail sehalus nyala lilin, yang digambar
         7 piksel dan dirender crispEdges, menyusut sampai di bawah satu
         piksel per satuan gambar dan HILANG SAMA SEKALI di editor, padahal
         di kartu aslinya menyala terang. */
      var frame = this.$refs.frame;
      if (frame) {
        frame.addEventListener("load", function () {
          var wadah = frame.parentElement;
          if (!wadah) return;
          var bentuk = "";
          try {
            bentuk = frame.contentDocument.documentElement.dataset.stage || "";
          } catch (e) {
            bentuk = "";
          }
          wadah.classList.toggle("is-lebar", bentuk === "lebar");
        });
      }

      window.addEventListener("message", function (event) {
        var data = event.data || {};
        if (data.source !== "card-frame") return;

        if (data.type === "ready") {
          self.scenes = data.scenes || [];
          if (!self.currentScene) self.currentScene = self.scenes[0] || "";
          // Preview baru saja dimuat dari server, jadi hanya berisi data yang
          // SUDAH tersimpan. Editan yang masih di memori dipasang ulang di
          // sini — tanpa ini, mengunggah foto akan menghapus tampilan editan.
          self.replay();
        }
        if (data.type === "select") {
          self.sel = data.key;
          self.error = "";
          self.fontOpen = self.colorOpen = self.moreOpen = false;
          if (data.scene) self.currentScene = data.scene;
        }
      });
    },

    /* ── Kirim ke iframe ──────────────────────────────────────────────── */
    post: function (message) {
      var frame = this.$refs.frame;
      if (frame && frame.contentWindow) {
        frame.contentWindow.postMessage(
          Object.assign({ source: "card-editor" }, message), "*"
        );
      }
    },
    pushStyle: function () {
      this.post({ type: "style", key: this.sel, css: elementCss(this.st) });
    },
    pushColors: function () {
      this.post({ type: "colors", colors: this.style.colors });
    },

    replay: function () {
      var self = this;
      this.pushColors();
      Object.keys(this.style.elements).forEach(function (key) {
        self.post({ type: "style", key: key, css: elementCss(self.style.elements[key]) });
      });
      Object.keys(this.fields).forEach(function (key) {
        if (self.fields[key]) self.post({ type: "text", key: key, value: self.fields[key] });
      });
      Object.keys(this.texts).forEach(function (key) {
        self.post({ type: "text", key: key, value: self.texts[key] });
      });
      // Babak sudah dipulihkan lewat ?scene= di URL iframe.
      if (this.sel) this.post({ type: "select", key: this.sel });
    },

    /* ── Sunting ──────────────────────────────────────────────────────── */
    /* Link lagu baru terlihat efeknya setelah tersimpan — muat ulang
       preview begitu user selesai mengetik (blur). */
    /* ── Lagu: kontrol tetap di panel kiri (bukan elemen di kartu) ────── */
    songInput: function (value) {
      this.fields.youtube_url = value;
      this.songStatus = "";
      this.queueSave();
    },
    songDone: function () {
      // Link diproses server (validasi + ambil cover/judul via oEmbed),
      // jadi efeknya baru terlihat setelah tersimpan → muat ulang preview.
      var self = this;
      clearTimeout(this.saveTimer);
      this.saveNow().then(function () {
        self.reloadFrame();
        self.probeSong();
      });
    },

    /* Uji putar sungguhan di browser.
       Wajib dilakukan di sini, bukan di server: blokir dari pemilik hak cipta
       (error 150) tidak terlihat di YouTube Data API — field `embeddable` di
       sana hanya mencerminkan setelan pengunggah. Cuma pemutar asli yang tahu. */
    probeSong: function () {
      var self = this;
      var id = this.youtubeIdFrom(this.fields.youtube_url || "");
      if (!id) { this.songStatus = ""; return; }

      this.songStatus = "Menguji lagu…";
      this.songOk = true;

      var start = function () {
        if (self.probePlayer) { self.probePlayer.destroy(); }
        var host = document.createElement("div");
        document.getElementById("songProbe").appendChild(host);
        self.probePlayer = new YT.Player(host, {
          height: "1", width: "1", videoId: id,
          playerVars: { playsinline: 1 },
          events: {
            onReady: function () {
              self.songStatus = "✓ Lagu bisa diputar di kartu.";
              self.songOk = true;
            },
            onError: function (e) {
              self.songOk = false;
              if (e.data === 101 || e.data === 150) {
                // YouTube juga membalas 150 kalau editor dibuka lewat alamat
                // IP mentah — hasil uji jadi tidak bisa dipercaya di sana.
                if (/^\d+\.\d+\.\d+\.\d+$/.test(window.location.hostname)) {
                  self.songStatus =
                    "⚠ Tidak bisa diuji lewat alamat IP. Buka editor lewat " +
                    "localhost untuk memastikan lagunya bisa diputar.";
                  return;
                }
                self.songStatus =
                  "✕ Lagu ini diblokir pemiliknya, kartu akan bisu. " +
                  'Cari versi dari channel berakhiran "- Topic".';
              } else if (e.data === 100) {
                self.songStatus = "✕ Video tidak ditemukan.";
              } else {
                self.songStatus = "✕ Lagu gagal dimuat (kode " + e.data + ").";
              }
            }
          }
        });
      };

      if (window.YT && window.YT.Player) { start(); return; }
      window.onYouTubeIframeAPIReady = start;
      if (!document.getElementById("ytapi")) {
        var tag = document.createElement("script");
        tag.id = "ytapi";
        tag.src = "https://www.youtube.com/iframe_api";
        document.head.appendChild(tag);
      }
    },

    youtubeIdFrom: function (url) {
      var m = String(url).match(
        /(?:youtu\.be\/|v=|\/embed\/|\/shorts\/|\/live\/)([A-Za-z0-9_-]{11})/
      );
      return m ? m[1] : "";
    },

    afterContentChange: function () {
      var self = this;
      if (this.sel !== "youtube_url") return;
      clearTimeout(this.saveTimer);
      this.saveNow().then(function () { self.reloadFrame(); });
    },

    setContent: function (value) {
      if (this.kind === "field") this.fields[this.sel] = value;
      else if (this.kind === "text") this.texts[this.sel] = value;
      this.post({ type: "text", key: this.sel, value: value });
      this.queueSave();
    },

    /* Simpan ke server, ditunda sebentar supaya tiap ketikan tidak jadi satu
       permintaan. Ini yang membuat editan tidak hilang saat preview dimuat
       ulang — dan draft tetap ada kalau tab tertutup. */
    queueSave: function () {
      var self = this;
      this.saveState = "saving";
      clearTimeout(this.saveTimer);
      this.saveTimer = setTimeout(function () { self.saveNow(); }, 600);
    },

    saveNow: function () {
      var self = this;
      this.saveState = "saving";
      return this.ensureCard().then(function (cardId) {
        return fetch(self.urls.content.replace("CARD", cardId), {
          method: "POST",
          headers: { "X-CSRFToken": self.csrf(), "Content-Type": "application/json" },
          body: JSON.stringify({
            style: self.style,
            texts: self.texts,
            fields: self.fields,
          }),
        }).then(function (response) {
          self.saveState = response.ok ? "saved" : "";
          return response;
        });
      }).catch(function (err) {
        self.saveState = "";
        throw err;
      });
    },

    setStyle: function (prop, value) {
      if (!this.sel) return;
      var current = this.style.elements[this.sel] || {};
      if (value === null || value === undefined) delete current[prop];
      else current[prop] = value;
      this.style.elements[this.sel] = current;
      this.pushStyle();
      this.queueSave();
    },

    toggle: function (prop) {
      this.setStyle(prop, this.st[prop] ? null : true);
    },

    bumpSize: function (delta) {
      var next = Math.round(((this.st.size || 1) + delta) * 100) / 100;
      this.setStyle("size", Math.min(Math.max(next, 0.5), 3));
    },

    resetElement: function () {
      delete this.style.elements[this.sel];
      this.pushStyle();
      this.queueSave();
    },

    setSurface: function (key, value) {
      this.style.colors[key] = value;
      this.pushColors();
      this.queueSave();
    },

    goScene: function (id) {
      this.currentScene = id;
      this.post({ type: "scene", value: id });
    },

    /* ── Foto: diunggah begitu dipilih ────────────────────────────────── */
    csrf: function () {
      var field = document.querySelector("[name=csrfmiddlewaretoken]");
      return field ? field.value : "";
    },

    ensureCard: function () {
      var self = this;
      if (this.cardId) return Promise.resolve(this.cardId);
      return fetch(this.urls.draft, {
        method: "POST",
        headers: { "X-CSRFToken": this.csrf(), "Content-Type": "application/json" },
        body: "{}",
      })
        .then(function (r) { return r.json(); })
        .then(function (data) { self.cardId = data.card; return data.card; });
    },

    sendPhoto: function (file, slot) {
      var self = this;
      // Simpan editan DULU: unggah foto memicu preview memuat ulang dari
      // server, jadi server harus sudah memegang teks & gaya terbaru.
      clearTimeout(this.saveTimer);
      return this.saveNow().then(function () {
        return self.cardId;
      }).then(function (cardId) {
        var body = new FormData();
        body.append("photo", file);
        if (slot) body.append("slot", slot);
        return fetch(self.urls.upload.replace("CARD", cardId), {
          method: "POST",
          headers: { "X-CSRFToken": self.csrf() },
          body: body,
        }).then(function (response) {
          return response.json().then(function (data) {
            if (!response.ok) throw new Error(data.detail || "Gagal mengunggah.");
            return data;
          });
        });
      });
    },

    uploadTo: function (slot, event) {
      var file = event.target.files[0];
      event.target.value = "";
      if (!file) return;
      this.cropQueue.push({ file: file, slot: slot });
      this.nextCrop();
    },

    /* ── Modal crop ──────────────────────────────────────────────────── */
    nextCrop: function () {
      if (this.cropOpen || !this.cropQueue.length) return;
      var item = this.cropQueue.shift();
      var self = this;
      var img = new Image();
      img.onload = function () {
        var canvas = self.$refs.cropCanvas;
        // Skala awal = "cover": foto memenuhi kotak, sisa bisa digeser.
        var base = Math.max(canvas.width / img.naturalWidth, canvas.height / img.naturalHeight);
        self.crop = {
          img: img, slot: item.slot, zoom: 1, base: base,
          dx: (canvas.width - img.naturalWidth * base) / 2,
          dy: (canvas.height - img.naturalHeight * base) / 2,
          drag: null,
        };
        self.cropOpen = true;
        self.$nextTick(function () { self.drawCrop(); });
      };
      img.onerror = function () { self.error = "Foto tidak bisa dibaca."; self.nextCrop(); };
      img.src = URL.createObjectURL(item.file);
      this.cropFile = item.file;
    },

    drawCrop: function () {
      var canvas = this.$refs.cropCanvas;
      if (!canvas || !this.crop.img) return;
      var ctx = canvas.getContext("2d");
      var s = this.crop.base * this.crop.zoom;
      ctx.fillStyle = "#eee";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(this.crop.img, this.crop.dx, this.crop.dy,
        this.crop.img.naturalWidth * s, this.crop.img.naturalHeight * s);
    },

    clampCrop: function () {
      var canvas = this.$refs.cropCanvas;
      var s = this.crop.base * this.crop.zoom;
      var w = this.crop.img.naturalWidth * s, h = this.crop.img.naturalHeight * s;
      this.crop.dx = Math.min(0, Math.max(canvas.width - w, this.crop.dx));
      this.crop.dy = Math.min(0, Math.max(canvas.height - h, this.crop.dy));
    },

    cropDown: function (event) {
      this.crop.drag = { x: event.clientX, y: event.clientY, dx: this.crop.dx, dy: this.crop.dy };
      event.currentTarget.setPointerCapture(event.pointerId);
    },
    cropDrag: function (event) {
      if (!this.crop.drag) return;
      var canvas = this.$refs.cropCanvas;
      var scale = canvas.width / canvas.getBoundingClientRect().width;
      this.crop.dx = this.crop.drag.dx + (event.clientX - this.crop.drag.x) * scale;
      this.crop.dy = this.crop.drag.dy + (event.clientY - this.crop.drag.y) * scale;
      this.clampCrop();
      this.drawCrop();
    },
    cropUp: function () { this.crop.drag = null; },

    cropZoom: function (zoom) {
      // Perbesar dari tengah kotak supaya tidak "lari".
      var canvas = this.$refs.cropCanvas;
      var cx = canvas.width / 2, cy = canvas.height / 2;
      var old = this.crop.base * this.crop.zoom;
      var next = this.crop.base * zoom;
      this.crop.dx = cx - (cx - this.crop.dx) * (next / old);
      this.crop.dy = cy - (cy - this.crop.dy) * (next / old);
      this.crop.zoom = zoom;
      this.clampCrop();
      this.drawCrop();
    },

    cancelCrop: function () {
      this.cropOpen = false;
      this.crop.img = null;
      this.nextCrop();
    },

    confirmCrop: function () {
      var self = this;
      var canvas = this.$refs.cropCanvas;
      this.busy = true;
      // Hasil potongan = persis isi canvas. Itu yang diunggah.
      canvas.toBlob(function (blob) {
        var file = new File([blob], "foto.jpg", { type: "image/jpeg" });
        var slot = self.crop.slot;
        self.sendPhoto(file, slot)
          .then(function (photo) {
            if (slot) self.framePhotos[slot] = photo;
            else self.gallery.push(photo);
            self.cropOpen = false;
            self.crop.img = null;
            self.reloadFrame();
            /* Di HP panel berada DI BAWAH pratinjau (column-reverse di bawah
               900px), jadi kolom caption yang baru muncul ada di luar layar —
               mata user sedang di kartu. Tanpa ini perbaikan reaktivitas di
               atas tetap tidak terlihat oleh pembeli yang datang dari TikTok. */
            if (slot) {
              self.$nextTick(function () {
                var kolom = document.getElementById("cap-bingkai");
                if (kolom && window.innerWidth <= 900) {
                  kolom.scrollIntoView({ block: "center", behavior: "smooth" });
                }
              });
            }
            self.nextCrop();
          })
          .catch(function (err) { self.error = err.message; self.cropOpen = false; })
          .finally(function () { self.busy = false; });
      }, "image/jpeg", 0.9);
    },

    uploadGallery: function (event) {
      var files = Array.prototype.slice.call(event.target.files || []);
      event.target.value = "";
      if (!files.length) return;

      var room = this.maxPhotos - this.gallery.length;
      this.error = "";
      if (files.length > room) {
        this.error = "Maksimal " + this.maxPhotos + " foto; sisanya diabaikan.";
        files = files.slice(0, Math.max(room, 0));
      }
      var self = this;
      files.forEach(function (file) { self.cropQueue.push({ file: file, slot: "" }); });
      this.nextCrop();
    },

    saveCaption: function (photoId, caption) {
      var self = this;
      fetch(this.urls.caption.replace("CARD", this.cardId).replace("PHOTO", photoId), {
        method: "POST",
        headers: { "X-CSRFToken": this.csrf(), "Content-Type": "application/json" },
        body: JSON.stringify({ caption: caption }),
      })
        .then(function (r) { return r.json(); })
        .then(function (photo) {
          self.gallery.forEach(function (p, i) {
            if (p.id === photo.id) self.gallery[i] = photo;
          });
          Object.keys(self.framePhotos).forEach(function (key) {
            var ada = self.framePhotos[key];
            if (ada && ada.id === photo.id) self.framePhotos[key] = photo;
          });
          self.reloadFrame();
        });
    },

    removePhoto: function (photoId) {
      var self = this;
      this.busy = true;
      fetch(this.urls.remove.replace("CARD", this.cardId).replace("PHOTO", photoId), {
        method: "POST",
        headers: { "X-CSRFToken": this.csrf() },
      })
        .then(function () {
          self.gallery = self.gallery.filter(function (p) { return p.id !== photoId; });
          Object.keys(self.framePhotos).forEach(function (key) {
            var ada = self.framePhotos[key];
            if (ada && ada.id === photoId) delete self.framePhotos[key];
          });
          self.reloadFrame();
        })
        .finally(function () { self.busy = false; });
    },
  };

  /* Nama font untuk tombol pemilih. */
  function specFontName(key) {
    var found = "";
    init.fontCatalog.forEach(function (group) {
      group.fonts.forEach(function (font) {
        if (font.key === key) found = font.name;
      });
    });
    return found || "Bawaan template";
  }

  /* Susun var CSS satu elemen — cerminan cards/styles.py:element_css().
     Nama var sengaja sama supaya preview dan kartu asli tidak bisa berbeda. */
  function elementCss(conf) {
    var parts = [];
    if (conf.font) parts.push("--f:" + init.fonts[conf.font]);
    if (conf.size) parts.push("--fs:" + conf.size);
    if (conf.color) parts.push("--c:" + conf.color);
    if (conf.align) parts.push("--al:" + conf.align);
    if (conf.bold) parts.push("--fw:700");
    if (conf.italic) parts.push("--fi:italic");
    if (conf.spacing !== undefined) parts.push("--ls:" + conf.spacing + "em");
    if (conf.line !== undefined) parts.push("--lh:" + conf.line);
    if (conf.fit) parts.push("--fit:" + conf.fit);
    if (conf.radius !== undefined) parts.push("--br:" + conf.radius + "px");
    return parts.join(";");
  }
};
