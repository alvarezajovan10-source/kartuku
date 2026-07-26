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
    get frameSrc() {
      return this.urls.frame + (this.cardId ? "?card=" + this.cardId : "");
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
          self.pushColors();
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

    /* ── Sunting ──────────────────────────────────────────────────────── */
    setContent: function (value) {
      if (this.kind === "field") this.fields[this.sel] = value;
      else if (this.kind === "text") this.texts[this.sel] = value;
      this.post({ type: "text", key: this.sel, value: value });
    },

    setStyle: function (prop, value) {
      if (!this.sel) return;
      var current = this.style.elements[this.sel] || {};
      if (value === null || value === undefined) delete current[prop];
      else current[prop] = value;
      this.style.elements[this.sel] = current;
      this.pushStyle();
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
    },

    setSurface: function (key, value) {
      this.style.colors[key] = value;
      this.pushColors();
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
      return this.ensureCard().then(function (cardId) {
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
          self.post({ type: "reload" });
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
          self.post({ type: "reload" });
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
          self.post({ type: "reload" });
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
          self.post({ type: "reload" });
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
