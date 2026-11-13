(function (root) {
  "use strict";
  const KEY = "samantha-book-inventory-pending-v1";
  function normalizeISBN(value) {
    let code = String(value || "").replace(/^\s*ISBN(?:-1[03])?\s*:?/i, "").replace(/[^0-9xX]/g, "").toUpperCase();
    if (/^[0-9]{9}[0-9X]$/.test(code)) {
      if ([...code].reduce((sum, x, i) => sum + (10 - i) * (x === "X" ? 10 : Number(x)), 0) % 11) throw Error("Neplatné ISBN.");
      code = "978" + code.slice(0, 9);
      code += String((10 - [...code].reduce((sum, x, i) => sum + Number(x) * (i % 2 ? 3 : 1), 0) % 10) % 10);
    }
    if (!/^(978|979)[0-9]{10}$/.test(code) || [...code].reduce((sum, x, i) => sum + Number(x) * (i % 2 ? 3 : 1), 0) % 10) throw Error("Zadej platné knižní ISBN-10 nebo ISBN-13.");
    return code;
  }
  function safeCover(value) { return /^https:\/\/covers\.openlibrary\.org\/b\/isbn\/(978|979)[0-9]{10}-S\.jpg\?default=false$/.test(value || ""); }
  class PendingWrite {
    constructor(storage, send, read, uuid) { this.storage = storage; this.send = send; this.read = read; this.uuid = uuid; this.busy = false; }
    pending() { const s = this.storage.getItem(KEY); return s ? JSON.parse(s) : null; }
    async save(kind, fields) {
      if (this.busy) return {ok: false, state: "busy"};
      this.busy = true;
      try {
        let request = this.pending();
        if (!request) {
          request = {kind, payload: {...fields, request_id: this.uuid()}};
          this.storage.setItem(KEY, JSON.stringify(request));
          if (!this.pending()) throw Error("Identitu zápisu se nepodařilo uchovat.");
        }
        const result = await this.send(request.kind, request.payload);
        if ((result.ok && result.state === "done") || result.state === "duplicate" || result.accepted === false) this.storage.removeItem(KEY);
        return result;
      } finally { this.busy = false; }
    }
    async recover() {
      const p = this.pending();
      if (!p) return {ok: true, state: "idle"};
      const result = await this.read(p.payload.request_id);
      if (result.ok && result.state === "done") this.storage.removeItem(KEY);
      return result;
    }
  }
  class Camera {
    constructor(media, video, decode, found, error) { Object.assign(this, {media, video, decode, found, error}); this.token = 0; this.stream = null; this.timer = null; }
    stop() {
      this.token++;
      clearTimeout(this.timer);
      if (this.stream) this.stream.getTracks().forEach(t => t.stop());
      this.stream = null; this.video.srcObject = null;
    }
    async start() {
      this.stop(); const token = this.token;
      try {
        const stream = await this.media.getUserMedia({video: {facingMode: {ideal: "environment"}, width: {ideal: 1280}}, audio: false});
        if (this.token !== token) { stream.getTracks().forEach(t => t.stop()); return; }
        this.stream = stream; this.video.srcObject = stream;
        await this.video.play();
        const tick = async () => {
          if (this.token !== token) return;
          try {
            const code = await this.decode(this.video);
            if (this.token !== token) return;
            if (code) { this.stop(); this.found(code); return; }
          } catch (_) { /* A frame without a readable ISBN is ordinary. */ }
          if (this.token === token) this.timer = setTimeout(tick, 250);
        };
        if (this.token === token) tick();
      } catch (_) { if (this.token === token) { this.stop(); this.error(); } }
    }
  }
  let decoderPromise;
  function decoder() {
    if (!decoderPromise) decoderPromise = new Promise((resolve, reject) => {
      const s = document.createElement("script"); s.src = "/assets/book-scanner/3.1.6/reader.js";
      s.onload = () => { root.ZXingWASM.prepareZXingModule({overrides: {locateFile: () => "/assets/book-scanner/3.1.6/zxing_reader.wasm"}}); resolve(root.ZXingWASM); };
      s.onerror = () => { decoderPromise = null; reject(Error("Čtečku nelze načíst. ISBN můžeš zadat ručně.")); };
      document.head.append(s);
    });
    return decoderPromise;
  }
  async function decodeImage(source) {
    const api = await decoder();
    const width = source.videoWidth || source.width, height = source.videoHeight || source.height;
    if (!width || !height) return "";
    const scale = Math.min(1, 1400 / width, 1400 / height);
    const canvas = document.createElement("canvas"); canvas.width = Math.round(width * scale); canvas.height = Math.round(height * scale);
    const ctx = canvas.getContext("2d", {willReadFrequently: true}); ctx.drawImage(source, 0, 0, canvas.width, canvas.height);
    const codes = await api.readBarcodes(ctx.getImageData(0, 0, canvas.width, canvas.height), {formats: ["EAN13", "ISBN"], tryHarder: true, maxNumberOfSymbols: 4});
    for (const code of codes) { try { return normalizeISBN(code.text); } catch (_) { /* Ignore non-book codes. */ } }
    return "";
  }
  async function request(url, payload) {
    const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 30000);
    try {
      const r = await root.fetch(url, {method: payload ? "POST" : "GET", signal: controller.signal, cache: "no-store",
        headers: payload ? {"Content-Type": "application/json"} : {}, body: payload ? JSON.stringify(payload) : undefined});
      const data = await r.json(); if (!r.ok && data.ok !== false) throw Error("Neověřená odpověď knihovny."); return data;
    } finally { clearTimeout(timeout); }
  }
  function boot(doc) {
    const el = id => doc.getElementById(id);
    const panel = el("quickBookPanel"); if (!panel) return null;
    const status = el("quickBookStatus"), isbn = el("quickBookISBN"), title = el("quickBookTitle"), author = el("quickBookAuthor"), year = el("quickBookYear");
    const open = el("quickBookOpen"), save = el("quickBookSave"), scan = el("quickBookScan"), video = el("quickBookVideo");
    const image = el("quickBookCover"), coverNote = el("quickBookCoverNote"), duplicate = el("quickBookDuplicate");
    let generation = 0, edits = 0, additional = false, available = false, rows = [], listGeneration = 0, opened = false, completed = false;
    const notice = text => { status.textContent = text; };
    let ledger;
    try { ledger = new PendingWrite(root.localStorage, (kind, payload) => request(kind === "locations" ? "/api/library/books/locations" : "/api/library/book/quick", payload),
      id => request("/api/library/book/quick-status?request_id=" + encodeURIComponent(id)), () => root.crypto.randomUUID()); ledger.pending(); }
    catch (_) { notice("Úložiště pro bezpečné potvrzení není dostupné. Povol ukládání dat této stránky."); }
    const pending = () => { try { return ledger && ledger.pending(); } catch (_) { return true; } };
    function controls() {
      const p = pending(), busy = ledger && ledger.busy;
      [isbn, title, author, year, scan, el("quickBookLookup"), el("quickBookImage"), el("quickBookLocationsOpen"), el("quickBookAdditional")].forEach(x => { x.disabled = !!p || !!busy || !ledger; });
      save.disabled = !!busy || !ledger || completed; save.textContent = p ? "Dokončit původní zápis" : "Uložit do knihovny";
      el("quickBookRecover").hidden = !p; el("quickBookNext").hidden = !!p || !el("quickBookNext").dataset.ready;
      el("quickBookLocationsSave").disabled = !!p || !!busy;
    }
    function setCover(url) {
      image.hidden = true; image.removeAttribute("src"); coverNote.textContent = "Bez obálky";
      if (safeCover(url)) { image.src = url; image.hidden = false; coverNote.textContent = "Náhled z Open Library"; }
    }
    image.addEventListener("error", () => { image.hidden = true; coverNote.textContent = "Bez obálky"; });
    const camera = new Camera(root.navigator.mediaDevices, video, decodeImage, code => { isbn.value = code; changedISBN(); lookup(); },
      () => { video.hidden = true; el("quickBookStop").hidden = true; notice("Kamera není dostupná nebo nemá povolení. Zadej ISBN nebo vyber fotografii kódu."); });
    function stop() { camera.stop(); video.hidden = true; el("quickBookStop").hidden = true; }
    function close() { opened = false; generation++; listGeneration++; stop(); panel.hidden = true; open.setAttribute("aria-expanded", "false"); }
    function changedISBN() { generation++; additional = false; completed = false; duplicate.replaceChildren(); title.value = ""; author.value = ""; year.value = ""; setCover(""); el("quickBookAdditional").hidden = true; controls(); }
    async function lookup() {
      if (pending()) return;
      stop(); let code;
      try { code = normalizeISBN(isbn.value); } catch (e) { notice(e.message); return; }
      isbn.value = code; const token = ++generation, edit = edits;
      notice("Hledám knihu podle ISBN…");
      try {
        const data = await request("/api/library/book/quick-lookup?isbn=" + encodeURIComponent(code));
        if (token !== generation || !opened) return;
        if (!data.ok) { notice(data.message || "Knihu nelze dohledat."); return; }
        if (edits !== edit) { notice("Náhled přišel po tvé úpravě; ruční údaje zůstaly zachované."); return; }
        const b = data.book || {}; title.value = b.title || ""; author.value = b.author || ""; year.value = b.publication_year || ""; setCover(b.cover_url);
        notice(data.found ? "Zkontroluj knihu a ulož ji. Umístění doplníš později na Macu." : data.message); title.focus();
      } catch (_) { if (token === generation && opened) notice("Katalog neodpověděl. Doplň název a knihu ulož ručně."); }
    }
    function complete(data, kind) {
      if (!data.ok || data.state !== "done") return false;
      notice(kind === "locations" ? "Umístění vybraných knih bylo uloženo." : "Kniha je uložená na Macu. Umístění doplníš později.");
      if (kind !== "locations") { completed = true; el("quickBookNext").dataset.ready = "1"; el("quickBookNext").hidden = false; }
      doc.dispatchEvent(new CustomEvent("library-inventory-saved", {detail: data.item || {}}));
      return true;
    }
    async function perform(kind, fields) {
      if (!ledger || ledger.busy) return;
      stop(); generation++;
      let actual = kind;
      try {
        actual = (ledger.pending() || {}).kind || kind;
        const promise = ledger.save(kind, fields); controls(); notice("Ukládám původní požadavek…");
        const data = await promise;
        if (complete(data, actual)) { if (actual === "locations") await loadLocations(); return; }
        if (data.state === "duplicate") {
          duplicate.replaceChildren();
          (data.existing || []).forEach(book => { const b = doc.createElement("button"); b.type = "button"; b.className = "secondary"; b.textContent = "Otevřít: " + book.title;
            b.addEventListener("click", () => doc.dispatchEvent(new CustomEvent("library-inventory-open", {detail: {id: book.id}}))); duplicate.append(b); });
          el("quickBookAdditional").hidden = false;
        }
        notice(data.message || "Výsledek není ověřený. Obnov stav původního zápisu.");
      } catch (_) { notice("Odpověď nepřišla. Původní identita je uchovaná; nejdřív obnov stav zápisu."); }
      finally { controls(); }
    }
    async function recover() {
      if (!ledger || ledger.busy || !pending()) return;
      const p = ledger.pending(); notice("Ověřuji původní zápis…");
      try {
        const data = await ledger.recover();
        if (!complete(data, p.kind)) notice(data.message || "Dokončení ještě není ověřené. Případné dokončení použije pouze původní požadavek.");
        el("quickBookAcknowledgeConflict").hidden = !(data.state === "conflict" && p.kind === "locations");
        el("quickBookAcknowledgeRemoved").hidden = !(data.state === "unavailable" && p.kind === "create");
      }
      catch (_) { notice("Stav zápisu teď nelze ověřit. Původní identita zůstala uchovaná."); }
      controls();
    }
    async function loadLocations() {
      if (pending()) return;
      const token = ++listGeneration;
      el("quickBookLocations").hidden = false; el("quickBookLocationsStatus").textContent = "Načítám knihy bez umístění…";
      try {
        const data = await request("/api/library/books/inventory"); if (token !== listGeneration || !opened) return;
        if (!data.ok) throw Error();
        rows = data.items || []; renderLocations();
      } catch (_) { if (token === listGeneration) { rows = []; el("quickBookLocationList").replaceChildren(); el("quickBookLocationsStatus").textContent = "Přehled nelze ověřit. Obnov jej před přiřazením."; } }
    }
    function renderLocations() {
      const list = el("quickBookLocationList"); list.replaceChildren();
      const shown = rows.filter(b => !el("quickBookMissingOnly").checked || !b.book_location);
      shown.forEach(book => { const label = doc.createElement("label"); label.className = "quick-book-location-row";
        const box = doc.createElement("input"); box.type = "checkbox"; box.value = book.id;
        const text = doc.createElement("span"); text.textContent = book.title + (book.book_location ? " — " + book.book_location : " — umístění k doplnění");
        label.append(box, text); list.append(label); });
      el("quickBookLocationsStatus").textContent = shown.length ? `${shown.length} knih. Vyber nejvýše 100 knih a přiřaď jim umístění.` : "Všechny knihy mají umístění.";
    }
    open.addEventListener("click", () => {
      if (!available) return;
      if (opened) { close(); return; }
      doc.dispatchEvent(new CustomEvent("library-inventory-opening")); opened = true; panel.hidden = false; open.setAttribute("aria-expanded", "true"); controls();
      if (pending()) recover(); else isbn.focus();
    });
    el("quickBookClose").addEventListener("click", close);
    isbn.addEventListener("input", changedISBN);
    [title, author, year].forEach(x => x.addEventListener("input", () => { edits++; }));
    el("quickBookLookup").addEventListener("click", lookup);
    scan.addEventListener("click", async () => {
      if (pending()) return;
      if (!root.isSecureContext || !root.navigator.mediaDevices) { notice("Kamera vyžaduje zabezpečené HTTPS připojení. ISBN můžeš zadat ručně."); return; }
      generation++; const token = generation; notice("Připravuji čtečku…");
      try { await decoder(); if (token !== generation || !opened) return; video.hidden = false; el("quickBookStop").hidden = false; notice("Namiř zadní kameru na knižní čárový kód."); await camera.start(); }
      catch (_) { notice("Čtečku nelze načíst. ISBN můžeš zadat ručně."); }
    });
    el("quickBookStop").addEventListener("click", stop);
    el("quickBookImage").addEventListener("change", async event => {
      stop(); const file = event.target.files[0]; if (!file || pending()) return;
      const token = ++generation;
      if (file.size > 12 * 1024 * 1024 || !file.type.startsWith("image/")) { notice("Vyber fotografii kódu do 12 MB."); return; }
      let bitmap;
      try { bitmap = await root.createImageBitmap(file); const code = await decodeImage(bitmap); if (token !== generation || !opened) return;
        if (!code) { notice("Na fotografii nebylo čitelné knižní ISBN. Zadej je ručně."); return; }
        isbn.value = code; changedISBN(); lookup();
      } catch (_) { if (token === generation) notice("Fotografii nelze přečíst. Zadej ISBN ručně."); }
      finally { if (bitmap) bitmap.close(); event.target.value = ""; }
    });
    save.addEventListener("click", () => {
      if (pending()) { perform("create", {}); return; }
      try { const code = normalizeISBN(isbn.value); if (!title.value.trim()) { notice("Doplň název knihy."); title.focus(); return; }
        perform("create", {isbn: code, title: title.value.trim(), author: author.value.trim(), publication_year: year.value.trim(), additional_copy: additional});
      } catch (e) { notice(e.message); }
    });
    el("quickBookAdditional").addEventListener("click", () => { additional = true; el("quickBookAdditional").hidden = true; notice("Dalším uložením přidáš další fyzický exemplář této knihy."); });
    el("quickBookNext").addEventListener("click", () => { if (pending()) return; isbn.value = ""; changedISBN(); el("quickBookNext").dataset.ready = ""; controls(); isbn.focus(); notice("Naskenuj další knihu nebo zadej ISBN."); });
    el("quickBookRecover").addEventListener("click", recover);
    el("quickBookAcknowledgeConflict").addEventListener("click", async () => {
      const p = pending(); if (!p || p.kind !== "locations" || ledger.busy) return;
      try {
        const current = await ledger.read(p.payload.request_id);
        if (current.state !== "conflict") { notice("Stav se změnil. Znovu ověř původní požadavek."); return; }
        root.localStorage.removeItem(KEY); el("quickBookAcknowledgeConflict").hidden = true;
        controls(); await loadLocations(); notice("Zobrazená jsou aktuální umístění. Případnou novou změnu potvrď novým výběrem.");
      } catch (_) { notice("Konflikt nelze nyní ověřit; původní identita zůstala uchovaná."); }
    });
    el("quickBookAcknowledgeRemoved").addEventListener("click", async () => {
      const p = pending(); if (!p || p.kind !== "create" || ledger.busy) return;
      try {
        const current = await ledger.read(p.payload.request_id);
        if (current.state !== "unavailable") { notice("Stav se změnil. Znovu ověř původní požadavek."); return; }
        root.localStorage.removeItem(KEY); completed = true; el("quickBookNext").dataset.ready = "1";
        el("quickBookAcknowledgeRemoved").hidden = true; controls(); notice("Původní kniha už není v knihovně. Pro nový zápis zvol Další kniha.");
      } catch (_) { notice("Stav nelze ověřit. Původní identita zůstala uchovaná."); }
    });
    el("quickBookLocationsOpen").addEventListener("click", loadLocations);
    el("quickBookLocationsRefresh").addEventListener("click", loadLocations);
    el("quickBookMissingOnly").addEventListener("change", renderLocations);
    el("quickBookLocationsSave").addEventListener("click", () => {
      const selected = [...el("quickBookLocationList").querySelectorAll('input:checked')].map(x => x.value);
      const location = el("quickBookLocationInput").value.trim();
      if (!selected.length || selected.length > 100 || !location) { notice("Vyber nejvýše 100 knih a vyplň umístění."); return; }
      perform("locations", {items: selected.map(id => { const b = rows.find(x => x.id === id); return {id, revision: b.revision}; }), location});
    });
    doc.addEventListener("visibilitychange", () => { if (doc.hidden) { generation++; stop(); } });
    root.addEventListener("pagehide", stop);
    return {close, setAvailable(value) { available = value; open.hidden = !value; open.disabled = !value; if (!value) close(); }};
  }
  const api = {normalizeISBN, safeCover, PendingWrite, Camera, boot};
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else { root.SamanthaBookQuick = api; document.addEventListener("DOMContentLoaded", () => { root.SamanthaBookQuickUI = boot(document); }); }
})(typeof window !== "undefined" ? window : globalThis);
