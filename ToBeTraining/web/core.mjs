export function makeDeck(items, random = false, rng = Math.random, previousLast = null) {
  const deck = [...items];
  if (random) {
    for (let i = deck.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      [deck[i], deck[j]] = [deck[j], deck[i]];
    }
    if (deck.length > 1 && deck[0].id === previousLast) [deck[0], deck[1]] = [deck[1], deck[0]];
  }
  return deck;
}

export function sentenceParts(row, question = false) {
  const cap = text => text.charAt(0).toUpperCase() + text.slice(1);
  const parts = [
    { key: 'pronoun', text: question ? row.pronoun : cap(row.pronoun) },
    { key: 'verb', text: question ? row.base : row.verb },
    { key: 'rest', text: row.rest },
  ];
  if (question && row.aux) parts.unshift({ key: 'aux', text: row.aux });
  if (question && !row.aux) {
    [parts[0], parts[1]] = [parts[1], parts[0]];
    parts[0].text = cap(parts[0].text);
  }
  parts.push({ key: 'punctuation', text: question ? '?' : '.' });
  return parts;
}

// A single owner for audio, timers and animations. Changing lessons invalidates
// every old callback; pause also freezes the teaching delays and word motion.
export class Playback {
  constructor(audio, notify = () => {}) {
    this.audio = audio;
    this.notify = notify;
    this.token = 0;
    this.paused = false;
    this.animations = new Set();
    this.finishAudio = null;
  }
  stop() {
    this.token++;
    this.paused = false;
    this.audio.pause();
    this.audio.currentTime = 0;
    if (this.finishAudio) this.finishAudio(false);
    for (const animation of this.animations) animation.cancel();
    this.animations.clear();
    return this.token;
  }
  active(token) { return token === this.token; }
  async wait(ms, token) {
    let elapsed = 0;
    let previous = performance.now();
    while (elapsed < ms && this.active(token)) {
      await new Promise(resolve => setTimeout(resolve, 30));
      const now = performance.now();
      if (!this.paused) elapsed += now - previous;
      previous = now;
    }
    return this.active(token);
  }
  async prime(src) {
    // Unlock this same audio element inside the initial touch/click, before
    // any asynchronous animation. Audible playback is always a real MP3.
    const token = this.token;
    this.audio.src = src;
    this.audio.volume = 0;
    try { await this.audio.play(); } catch { /* Actual playback reports errors. */ }
    if (this.active(token)) {
      this.audio.pause();
      this.audio.currentTime = 0;
      this.audio.volume = 1;
    }
  }
  play(src, token, speed = 1) {
    if (!this.active(token)) return Promise.resolve(false);
    if (this.finishAudio) this.finishAudio(false);
    return new Promise(resolve => {
      let elapsed = 0;
      let settled = false;
      const finish = ok => {
        if (settled) return;
        settled = true;
        clearInterval(watchdog);
        this.audio.onended = null;
        this.audio.onerror = null;
        if (this.finishAudio === finish) this.finishAudio = null;
        resolve(ok && this.active(token));
      };
      const fail = () => {
        if (settled) return;
        if (this.active(token)) this.notify('Zvuk se nepodařilo přehrát. Zkus Poslechnout znovu.');
        this.audio.pause();
        finish(false);
      };
      const watchdog = setInterval(() => {
        if (!this.paused) elapsed += 250;
        if (elapsed > 30000) fail();
      }, 250);
      this.finishAudio = finish;
      this.audio.src = src;
      this.audio.volume = 1;
      this.audio.playbackRate = speed;
      this.audio.onended = () => finish(true);
      this.audio.onerror = fail;
      if (!this.paused) this.audio.play().catch(fail);
    });
  }
  togglePause() {
    this.paused = !this.paused;
    for (const animation of this.animations) this.paused ? animation.pause() : animation.play();
    if (this.paused) this.audio.pause();
    else if (this.finishAudio) this.audio.play().catch(() => {
      this.notify('Zvuk se nepodařilo obnovit. Zkus Poslechnout znovu.');
      if (this.finishAudio) this.finishAudio(false);
    });
    return this.paused;
  }
  animate(element, frames, options) {
    const animation = element.animate(frames, options);
    this.animations.add(animation);
    if (this.paused) animation.pause();
    animation.finished.catch(() => {}).finally(() => this.animations.delete(animation));
    return animation;
  }
}
