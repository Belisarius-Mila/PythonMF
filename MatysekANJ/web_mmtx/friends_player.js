/* Shared sentence player for the four Friends chapters. No network TTS. */
(function (global) {
  "use strict";
  class FriendsPlayer {
    constructor(nodes, onChange = () => {}) {
      this.nodes = nodes;
      this.onChange = onChange;
      this.active = false;
      this.mode = 0;
      try { const value = global.localStorage.getItem("mmtx_friends_czech_mode"); if (["0", "1", "2"].includes(value)) this.mode = Number(value); } catch (_) { /* Optional storage. */ }
      this.token = 0;
      this.busy = false;
      this.line = null;
      this.pending = null;
      this.action = null;
      this.manual = false;
      this.blocking = false;
      this.failed = "";
      this.enDone = false;
      nodes.language.addEventListener("click", () => this.changeMode());
      nodes.repeat.addEventListener("click", () => { if (this.active && !this.busy && this.line) this.playEnglish(); });
      nodes.next.addEventListener("click", () => {
        if (!this.active || this.busy || this.failed || !this.manual) return;
        const action = this.action;
        this.action = null;
        this.manual = false;
        this.blocking = false;
        this.resolve(true);
        this.render();
        if (action) action();
      });
      this.render();
    }
    get locked() { return this.busy || this.blocking || Boolean(this.failed); }
    resolve(value) { const done = this.pending; this.pending = null; if (done) done(value); }
    cancelPlayback() {
      this.token += 1;
      if (this.audio) { this.audio.onended = null; this.audio.onerror = null; this.audio.pause(); this.audio = null; }
      if (this.utterance) { this.utterance.onend = null; this.utterance.onerror = null; this.utterance = null; global.speechSynthesis?.cancel(); }
      const cancel = this.transportCancel; this.transportCancel = null; if (cancel) cancel(false);
      this.busy = false;
      this.language = "";
    }
    stop() {
      this.cancelPlayback();
      this.resolve(false);
      this.action = null;
      this.line = null;
      this.failed = "";
      this.manual = false;
      this.blocking = false;
      this.enDone = false;
      this.render();
    }
    setActive(active) { this.active = active; this.render(); }
    present(line, { manual = true, nextLabel = "Next ▶", count = "" } = {}) {
      this.stop();
      if (!this.active) return Promise.resolve(false);
      this.line = line;
      this.manual = manual;
      this.blocking = manual;
      this.nextLabel = nextLabel;
      this.count = count;
      const result = new Promise(resolve => { this.pending = resolve; });
      this.playEnglish();
      return result;
    }
    speak(line) { return this.present(line, { manual: false }); }
    setAction(label, action) {
      if (!this.active || this.busy || this.failed) return;
      this.manual = true;
      this.blocking = false;
      this.action = action;
      this.nextLabel = label;
      this.render();
    }
    async playEnglish() {
      this.cancelPlayback();
      const token = this.token;
      this.failed = "";
      this.enDone = false;
      const ok = await this.clip("en", token);
      if (token !== this.token) return;
      if (!ok) { this.fail("en"); return; }
      this.enDone = true;
      if (this.mode === 2) await this.playCzech(token);
      else this.finish();
    }
    async playCzech(token = this.token) {
      const ok = await this.clip("cs", token);
      if (token !== this.token) return;
      if (!ok) this.fail("cs"); else this.finish();
    }
    clip(language, token) {
      if (!this.active || !this.line || token !== this.token) return Promise.resolve(false);
      this.busy = true;
      this.language = language;
      this.render();
      const line = this.line;
      const path = language === "en" ? line.audioEn : line.audioCz;
      return new Promise(resolve => {
        let settled = false;
        const finish = ok => {
          if (settled) return;
          settled = true;
          if (token === this.token) { this.audio = null; this.utterance = null; this.transportCancel = null; }
          resolve(ok);
        };
        this.transportCancel = finish;
        if (path) {
          try {
            const audio = new global.Audio(path);
            this.audio = audio;
            audio.preload = "auto";
            audio.onended = () => finish(true);
            audio.onerror = () => finish(false);
            const promise = audio.play();
            if (promise?.catch) promise.catch(() => finish(false));
          } catch (_) { finish(false); }
        } else if (global.speechSynthesis && global.SpeechSynthesisUtterance) {
          try {
            const utterance = new global.SpeechSynthesisUtterance(language === "en" ? line.textEn : line.textCz);
            utterance.lang = language === "en" ? "en-US" : "cs-CZ";
            utterance.rate = language === "en" ? 0.86 : 0.9;
            const voices = global.speechSynthesis.getVoices?.() || [];
            const matching = voices.filter(v => v.lang?.toLowerCase().startsWith(language));
            const preferred = (line.preferredVoiceName || "").toLowerCase().split("|");
            const voice = language === "en" ? matching.find(v => preferred.some(n => n && v.name.toLowerCase().includes(n))) || matching[0] : matching[0];
            if (voice) utterance.voice = voice;
            utterance.onend = () => finish(true);
            utterance.onerror = () => finish(false);
            this.utterance = utterance;
            global.speechSynthesis.speak(utterance);
          } catch (_) { finish(false); }
        } else finish(false);
      });
    }
    finish() {
      this.busy = false;
      this.language = "";
      this.failed = "";
      if (!this.manual) this.resolve(true);
      this.render();
    }
    fail(language) { this.busy = false; this.language = ""; this.failed = language; this.render(); }
    changeMode() {
      this.mode = (this.mode + 1) % 3;
      try { global.localStorage.setItem("mmtx_friends_czech_mode", String(this.mode)); } catch (_) { /* Optional storage. */ }
      if (this.mode !== 2 && (this.language === "cs" || this.failed === "cs")) {
        this.cancelPlayback();
        this.finish();
      } else if (this.mode === 2 && this.line && this.enDone && !this.busy && !this.failed) {
        this.cancelPlayback();
        this.playCzech();
      }
      this.render();
    }
    render() {
      const n = this.nodes;
      n.panel.hidden = !this.active;
      n.language.textContent = ["CZ: vypnuto", "CZ: text", "CZ: text + hlas"][this.mode];
      n.language.setAttribute("aria-pressed", String(this.mode > 0));
      n.language.title = ["Zobrazit český překlad", "Zapnout české čtení", "Vypnout češtinu"][this.mode];
      n.language.setAttribute("aria-label", `${n.language.textContent}. ${n.language.title}`);
      n.speaker.textContent = this.line?.speaker || "";
      n.text.textContent = this.line?.textEn || "";
      n.czech.textContent = this.mode > 0 ? this.line?.textCz || "" : "";
      n.czech.hidden = !n.czech.textContent;
      n.count.textContent = this.count || "";
      n.status.textContent = this.failed ? `${this.failed === "cs" ? "Czech" : "English"} audio unavailable. Tap Repeat.` : "";
      n.repeat.disabled = !this.active || !this.line || this.busy;
      n.next.textContent = this.nextLabel || "Next ▶";
      n.next.hidden = !this.manual;
      n.next.disabled = !this.active || this.busy || Boolean(this.failed) || !this.manual;
      this.onChange();
    }
  }
  global.MMTXFriendsPlayer = FriendsPlayer;
})(window);
