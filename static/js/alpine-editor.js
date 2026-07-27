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
  };

  var specByKey = {};
  init.elements.forEach(function (spec) { specByKey[spec.key] = spec; });

  return {
    cardId: init.cardId,
    style: init.style,
    fields: init.fields,
    texts: init.texts,
    gallery: init.gallery,
    palettes: init.palettes,
    swatches: init.swatches,
    urls: init.urls,
    maxPhotos: init.maxPhotos,

    sel: null,
    device: "phone",
    scenes: [],
    currentScene: "",
    busy: false,
    error: "",
    dragging: false,
    dragFrom: null,
    saveTimer: null,
    saveState: "",   // "" | "saving" | "saved"
    fontOpen: false,
    colorOpen: false,
    moreOpen: false,
    fontQuery: "",

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
      return this.kind === "text" ? "Kosongkan = pakai bawaan template" : "Tulis di sini...";
    },
    get content() {
      if (this.kind === "field") return this.fields[this.sel] || "";
      if (this.kind === "text") return this.texts[this.sel] || "";
      return "";
    },
    get photo() { return this.spec ? this.spec.photo : null; },
    /* Alamat iframe dibangun saat DIBUTUHKAN, bukan diikat reaktif —
       dulu :src reaktif membuat preview memuat ulang (dan balik ke sampul)
       begitu draft pertama kali dibuat di server. */
    frameUrl: function () {
      var q = [];
      if (this.cardId) q.push("card=" + this.cardId);
      if (this.currentScene) q.push("scene=" + encodeURIComponent(this.currentScene));
      return this.urls.frame + (q.length ? "?" + q.join("&") : "");
    },

    reloadFrame: function () {
      if (this.$refs.frame) this.$refs.frame.src = this.frameUrl();
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
      if (!this.style.elements) this.style.elements = {};
      if (!this.style.colors) this.style.colors = {};
      // Warna bawaan template jadi titik awal supaya pemilih warna tidak kosong.
      init.elements.forEach(function (spec) {
        if (spec.type === "surface" && !self.style.colors[spec.key]) {
          self.style.colors[spec.key] = spec.value;
        }
      });

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

    /* ── Crop: geser & perbesar di dalam bingkai ──────────────────────
       Foto aslinya tidak disentuh; yang disimpan cuma posisi & perbesaran,
       jadi user bisa mengatur ulang kapan saja tanpa unggah ulang. */
    cropStart: function (event) {
      this.dragging = true;
      this.dragFrom = {
        x: event.clientX,
        y: event.clientY,
        ox: this.st.ox === undefined ? 50 : this.st.ox,
        oy: this.st.oy === undefined ? 50 : this.st.oy,
      };
      event.currentTarget.setPointerCapture(event.pointerId);
    },

    cropMove: function (event) {
      if (!this.dragging) return;
      var box = event.currentTarget.getBoundingClientRect();
      // Makin besar zoom, makin kecil geseran per pixel — terasa wajar.
      var reach = Math.max((this.st.zoom || 1) - 1, 0.35);
      var dx = ((event.clientX - this.dragFrom.x) / box.width) * (100 / reach);
      var dy = ((event.clientY - this.dragFrom.y) / box.height) * (100 / reach);
      var current = this.style.elements[this.sel] || {};
      current.ox = Math.min(Math.max(this.dragFrom.ox - dx, 0), 100);
      current.oy = Math.min(Math.max(this.dragFrom.oy - dy, 0), 100);
      this.style.elements[this.sel] = current;
      this.pushStyle();
    },

    cropEnd: function () {
      this.dragging = false;
      this.queueSave();
    },

    resetCrop: function () {
      this.queueSave();
      var current = this.style.elements[this.sel] || {};
      delete current.zoom;
      delete current.ox;
      delete current.oy;
      this.style.elements[this.sel] = current;
      this.pushStyle();
    },

    cropStyle: function () {
      if (!this.photo) return "";
      return (
        "background-image:url(" + this.photo.url + ");" +
        "background-size:" + ((this.st.zoom || 1) * 100) + "% auto;" +
        "background-position:" +
        (this.st.ox === undefined ? 50 : this.st.ox) + "% " +
        (this.st.oy === undefined ? 50 : this.st.oy) + "%;" +
        "background-repeat:no-repeat"
      );
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
      var self = this;
      this.busy = true;
      this.error = "";
      this.sendPhoto(file, slot)
        .then(function (photo) {
          specByKey[slot].photo = photo;
          self.reloadFrame();
        })
        .catch(function (err) { self.error = err.message; })
        .finally(function () { self.busy = false; });
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
      if (!files.length) return;

      var self = this;
      this.busy = true;
      files
        .reduce(function (chain, file) {
          return chain.then(function () {
            return self.sendPhoto(file, "").then(function (photo) {
              self.gallery.push(photo);
            });
          });
        }, Promise.resolve())
        .catch(function (err) { self.error = err.message; })
        .finally(function () {
          self.busy = false;
          self.reloadFrame();
        });
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
          Object.keys(specByKey).forEach(function (key) {
            var spec = specByKey[key];
            if (spec.photo && spec.photo.id === photo.id) spec.photo = photo;
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
          Object.keys(specByKey).forEach(function (key) {
            var spec = specByKey[key];
            if (spec.photo && spec.photo.id === photoId) spec.photo = null;
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
