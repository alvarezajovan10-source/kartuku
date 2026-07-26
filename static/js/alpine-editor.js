/* Editor kartu: panel kiri berubah mengikuti elemen yang diklik di preview.

   Preview adalah kartu ASLI yang dimuat di dalam iframe, jadi yang dilihat saat
   mengedit tidak mungkin berbeda dari hasil akhirnya. Komunikasi dua arah lewat
   postMessage (lihat static/js/card-frame.js).

   Foto diunggah begitu dipilih. Teks & gaya baru tersimpan saat tombol
   "Lanjut bayar" ditekan. */

window.cardEditor = function () {
  var init = JSON.parse(document.getElementById("editor-init").textContent);

  // Elemen teks yang punya pengaturan gaya, dan slot gaya mana yang dipakai.
  var TEXT_SLOTS = {
    recipient: "title",
    message: "message",
    sender: "signature",
    favorite_flower: "title",
    affirmations: "message",
  };

  var LABELS = {
    recipient: "Nama penerima",
    message: "Pesan",
    sender: "Nama pengirim",
    favorite_flower: "Nama bunga",
    affirmations: "Kalimat manis",
    gallery: "Galeri foto",
  };

  var SCENE_LABELS = {
    cover: "Sampul", hero: "Ucapan", hub: "Hadiah", message: "Surat",
    flower: "Bunga", cake: "Kue", song: "Lagu", gallery: "Kenangan",
  };

  return {
    s: init.style,
    text: init.text,
    frames: init.frames,
    texts: init.texts,
    textValues: init.textValues,
    surfaces: init.surfaces,
    framesById: {},
    gallery: init.gallery,
    cardId: init.cardId,
    templateSlug: init.templateSlug,
    urls: init.urls,
    maxPhotos: init.maxPhotos,

    sel: null,
    device: "phone",
    scenes: [],
    currentScene: "",
    busy: false,
    error: "",

    get frameSrc() {
      return this.urls.frame + (this.cardId ? "?card=" + this.cardId : "");
    },

    get kind() {
      if (!this.sel) return null;
      if (this.sel === "gallery") return "gallery";
      if (this.framesById[this.sel]) return "frame";
      if (this.textValues.hasOwnProperty(this.sel)) return "free";
      return "text";
    },

    get styleSlot() {
      return TEXT_SLOTS[this.sel] || null;
    },

    init: function () {
      var self = this;
      this.frames.forEach(function (f) { self.framesById[f.key] = f; });
      // Warna permukaan template masuk ke style.colors supaya ikut tersimpan.
      if (!this.s.colors) this.s.colors = {};
      this.surfaces.forEach(function (surface) {
        if (!self.s.colors[surface.key]) self.s.colors[surface.key] = surface.value;
      });

      window.addEventListener("message", function (event) {
        var data = event.data || {};
        if (data.source !== "card-frame") return;

        if (data.type === "ready") {
          self.scenes = data.scenes || [];
          self.currentScene = self.scenes[0] || "";
          self.pushStyle();
        }
        if (data.type === "select") {
          self.sel = data.key;
          self.error = "";
        }
      });
    },

    /* ── Bantuan tampilan ─────────────────────────────────────────────── */
    labelFor: function (key) {
      if (this.framesById[key]) return this.framesById[key].label;
      if (LABELS[key]) return LABELS[key];
      var spec = this.texts.filter(function (t) { return t.key === key; })[0];
      return spec ? spec.label : key;
    },

    pushFreeText: function (key) {
      this.post({ type: "text", key: key, value: this.textValues[key] });
    },

    setSurface: function (key, value) {
      this.s.colors[key] = value;
      this.post({ type: "colors", colors: this.s.colors });
    },
    sceneLabel: function (id) { return SCENE_LABELS[id] || id; },
    clearSel: function () { this.sel = null; },
    cur: function () {
      return this.s[this.styleSlot] || { font: "serif", color: "#000000", size: 1, align: "left" };
    },
    framePhoto: function (key) {
      return this.frames.filter(function (f) { return f.key === key; })[0].photo || null;
    },

    /* ── Kirim perubahan ke iframe ────────────────────────────────────── */
    post: function (message) {
      var frame = this.$refs.frame;
      if (frame && frame.contentWindow) {
        frame.contentWindow.postMessage(
          Object.assign({ source: "card-editor" }, message), "*"
        );
      }
    },

    cssVars: function () {
      var vars = { "--bg": this.s.bg, "--accent": this.s.accent };
      var self = this;
      ["title", "message", "signature"].forEach(function (slot) {
        var conf = self.s[slot];
        vars["--" + slot + "-font"] = init.fonts[conf.font] || init.fonts.serif;
        vars["--" + slot + "-color"] = conf.color;
        vars["--" + slot + "-size"] = conf.size;
        vars["--" + slot + "-align"] = conf.align;
      });
      return vars;
    },

    pushStyle: function () {
      this.post({ type: "style", vars: this.cssVars() });
      this.post({ type: "colors", colors: this.s.colors || {} });
    },
    pushText: function (key) { this.post({ type: "text", key: key, value: this.text[key] }); },

    setStyle: function (prop, value) {
      if (!this.styleSlot) return;
      this.s[this.styleSlot][prop] = value;
      this.pushStyle();
    },

    goScene: function (id) {
      this.currentScene = id;
      this.post({ type: "scene", value: id });
    },

    /* ── Foto: langsung diunggah ──────────────────────────────────────── */
    ensureCard: function () {
      var self = this;
      if (this.cardId) return Promise.resolve(this.cardId);
      return fetch(this.urls.draft, {
        method: "POST",
        headers: { "X-CSRFToken": this.csrf(), "Content-Type": "application/json" },
        body: JSON.stringify({}),
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          self.cardId = data.card;
          return data.card;
        });
    },

    csrf: function () {
      var field = document.querySelector("[name=csrfmiddlewaretoken]");
      return field ? field.value : "";
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
          self.frames.forEach(function (f) { if (f.key === slot) f.photo = photo; });
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
      if (files.length > room) {
        this.error = "Maksimal " + this.maxPhotos + " foto galeri; sisanya diabaikan.";
        files = files.slice(0, Math.max(room, 0));
      } else {
        this.error = "";
      }
      if (!files.length) return;

      var self = this;
      this.busy = true;
      // Berurutan, bukan serentak — supaya urutan foto sesuai pilihan user.
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
          self.frames.forEach(function (f) {
            if (f.photo && f.photo.id === photo.id) f.photo = photo;
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
          self.frames.forEach(function (f) {
            if (f.photo && f.photo.id === photoId) f.photo = null;
          });
          self.post({ type: "reload" });
        })
        .finally(function () { self.busy = false; });
    },

    syncBeforeSubmit: function () { return true; },
  };
};
