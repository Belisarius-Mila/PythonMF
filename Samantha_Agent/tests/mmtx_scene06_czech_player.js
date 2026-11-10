const fs = require("fs"), vm = require("vm"), path = require("path"), assert = require("assert");
const folder = process.argv[2];
const read = name => JSON.parse(fs.readFileSync(path.join(folder, name), "utf8"));
const catalog = read("pictures.json").pictures, translations = read("translations_cs.json").lines;
const source = fs.readFileSync(path.join(folder, "script.js"), "utf8");

async function harness(mode = "0", hash = "", blocked = false, badTranslation = false) {
  const nodes = new Map(), audios = [], events = {}, saved = [];
  function node(id) {
    if (!nodes.has(id)) nodes.set(id, {hidden: false, disabled: id !== "restartButton", textContent: "", dataset: {}, listeners: {},
      setAttribute(k, v) { this[k] = v; }, classList: {remove() {}, add() {}, toggle() {}},
      addEventListener(k, f) { this.listeners[k] = f; }, click() { if (!this.disabled) this.listeners.click?.(); }});
    return nodes.get(id);
  }
  class Audio {
    constructor(src) { this.src = src; audios.push(this); }
    play() { return Promise.resolve(); }
    pause() { this.paused = true; }
  }
  const context = vm.createContext({document: {getElementById: node}, Audio,
    window: {location: {hash}, addEventListener(k, f) { events[k] = f; }, localStorage: {
      getItem() { if (blocked) throw Error("blocked"); return mode; },
      setItem(k, v) { if (blocked) throw Error("blocked"); saved.push([k, v]); }
    }}, fetch: async url => ({ok: true, json: async () => {
      const data = read(url.split("?")[0]);
      if (badTranslation && url.startsWith("translations_cs")) data.lines[0].english = "wrong binding";
      return data;
    }})});
  vm.runInContext(source, context);
  await new Promise(resolve => setImmediate(resolve));
  return {node, audios, events, saved, click: id => node(id).click(), end: () => audios.at(-1).onended()};
}

(async () => {
  // All 67 bilingual lines, the silent step, the final Repeat and Again.
  const h = await harness("2");
  assert.equal(h.audios.length, 0); assert.equal(h.node("languageButton").textContent, "CZ: text + hlas");
  h.click("startButton");
  let spoken = 0;
  for (const picture of catalog) {
    const rows = read(picture.dialogue).lines;
    if (!rows.length) {
      const before = h.audios.length; h.click("nextButton");
      assert.equal(h.node("sceneImage").src, "silence.webp");
      assert.equal(h.node("speechBubble").hidden, true); assert.equal(h.node("czechText").hidden, true);
      for (let n = 0; n < 3; n++) h.click("languageButton");
      h.events.pagehide(); h.events.pageshow(); h.click("repeatButton");
      assert.equal(h.audios.length, before); assert.equal(h.node("nextButton").disabled, false);
      continue;
    }
    for (const row of rows) {
      if (spoken > 0) h.click("nextButton");
      const cs = translations[spoken];
      assert.equal(h.audios.at(-1).src, row.audio); assert.equal(h.node("speechText").textContent, row.text);
      assert.equal(h.node("czechText").textContent, cs.text); assert.equal(h.node("czechText").hidden, false);
      assert.equal(h.node("scene").dataset.layout, "below");
      assert.equal(h.node("nextButton").disabled, true);
      const englishEnded = h.audios.at(-1).onended; h.end();
      assert.equal(h.audios.at(-1).src, cs.audio); assert.equal(h.node("nextButton").disabled, true);
      const count = h.audios.length; englishEnded(); assert.equal(h.audios.length, count);
      h.end(); spoken++;
    }
  }
  assert.equal(spoken, 67); assert.equal(h.audios.length, 134);
  assert.equal(h.node("restartButton").hidden, false);
  h.click("repeatButton"); assert.equal(h.audios.at(-1).src, translations.at(-1).audio_en);
  h.end(); assert.equal(h.audios.at(-1).src, translations.at(-1).audio); h.end();
  h.click("restartButton"); assert.equal(h.audios.at(-1).src, translations[0].audio_en);
  h.end(); assert.equal(h.audios.at(-1).src, translations[0].audio); h.end();

  // Live switching: text-only does not play Czech; reading an idle line does.
  const a = await harness(); a.click("startButton"); a.click("languageButton");
  assert.equal(a.node("languageButton").textContent, "CZ: text");
  assert.equal(a.node("czechText").textContent, translations[0].text);
  a.end(); assert.equal(a.audios.length, 1); assert.equal(a.node("nextButton").disabled, false);
  a.click("languageButton"); assert.equal(a.audios.at(-1).src, translations[0].audio);
  a.audios.at(-1).onerror(); assert.equal(a.node("nextButton").disabled, true);
  a.click("languageButton"); assert.equal(a.node("nextButton").disabled, false);
  assert.equal(a.node("czechText").hidden, true);
  a.click("languageButton"); a.click("languageButton");
  const staleCzech = a.audios.at(-1).onended, beforeStop = a.audios.length;
  a.click("languageButton"); assert.equal(a.audios.at(-1).paused, true);
  staleCzech(); assert.equal(a.audios.length, beforeStop); assert.equal(a.node("nextButton").disabled, false);

  // Turning reading off during English prevents the follow-up Czech clip.
  a.click("languageButton"); a.click("languageButton"); a.end();
  a.click("nextButton"); const beforeEnglishEnd = a.audios.length;
  a.click("languageButton"); a.end(); assert.equal(a.audios.length, beforeEnglishEnd);
  assert.equal(a.node("czechText").hidden, true);

  // Enabling Czech cannot skip an English error. Repeat replays both tracks.
  a.click("nextButton"); a.audios.at(-1).onerror();
  const failedCount = a.audios.length;
  a.click("languageButton"); a.click("languageButton");
  assert.equal(a.audios.length, failedCount); assert.equal(a.node("nextButton").disabled, true);
  a.click("repeatButton"); a.end(); assert.ok(a.audios.at(-1).src.startsWith("audio/cs/")); a.end();

  // History restoration never restarts speech and ignores a paused Czech callback.
  a.click("nextButton"); a.end(); const pausedEnded = a.audios.at(-1).onended;
  const historyCount = a.audios.length; a.events.pagehide(); pausedEnded(); a.events.pageshow();
  assert.equal(a.audios.length, historyCount); a.click("repeatButton");
  assert.ok(a.audios.at(-1).src.startsWith("audio/en/")); a.end(); a.end();
  assert.ok(a.saved.some(([, value]) => value === "2"));

  for (const [value, blocked] of [["garbage", false], ["2", true]]) {
    const fallback = await harness(value, "#picture=4", blocked);
    assert.equal(fallback.node("languageButton").textContent, "CZ: vypnuto");
    fallback.click("languageButton"); assert.equal(fallback.node("languageButton").textContent, "CZ: text");
    assert.equal(fallback.audios.length, 0);
  }
  const invalid = await harness("0", "", false, true);
  assert.equal(invalid.node("startButton").disabled, true); assert.equal(invalid.audios.length, 0);
  assert.ok(invalid.node("status").textContent.includes("could not load"));
  console.log("67 EN+CZ pairs, silent step, switching, errors, stale callbacks, storage and history: PASS");
})().catch(error => { console.error(error); process.exitCode = 1; });
