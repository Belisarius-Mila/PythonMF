"use strict";

const startButton = document.getElementById("startButton");
const nextButton = document.getElementById("nextButton");
const repeatButton = document.getElementById("repeatButton");
const restartButton = document.getElementById("restartButton");
const speechBubble = document.getElementById("speechBubble");
const speakerName = document.getElementById("speakerName");
const speechText = document.getElementById("speechText");
const czechText = document.getElementById("czechText");
const languageButton = document.getElementById("languageButton");
const dictionaryButton = document.getElementById("dictionaryButton");
const dictionaryPanel = document.getElementById("dictionaryPanel");
const dictionaryList = document.getElementById("dictionaryList");
const dictionaryClose = document.getElementById("dictionaryClose");
const dictionaryStatus = document.getElementById("dictionaryStatus");
const lineNumber = document.getElementById("lineNumber");
const status = document.getElementById("status");
const scene = document.getElementById("scene");
const sceneImage = document.getElementById("sceneImage");
let lines = [];
let index = -1;
let activeAudio = null;
let generation = 0;
let playing = false;
let failed = false;
let openingIndex = 0;
let audioLanguage = "";
let failedLanguage = "";
const LANGUAGE_KEY = "mmtx_scene06_czech_mode";
let languageMode = loadLanguageMode();
let dictionaryItems = [];
let activeVocabulary = null;
let vocabularyFailedLanguage = "";
let finalCompleted = false;

function dictionaryAvailable() { return finalCompleted && index === lines.length - 1 && !failed; }

function loadLanguageMode() {
  try {
    const value = window.localStorage.getItem(LANGUAGE_KEY);
    return ["0", "1", "2"].includes(value) ? Number(value) : 0;
  } catch (_error) { return 0; }
}

function updateLanguageUi() {
  const labels = ["CZ: vypnuto", "CZ: text", "CZ: text + hlas"];
  const actions = ["Zobrazit český překlad", "Zapnout české čtení", "Vypnout češtinu"];
  languageButton.textContent = labels[languageMode];
  languageButton.setAttribute("aria-pressed", String(languageMode > 0));
  languageButton.setAttribute("aria-label", `${labels[languageMode]}. ${actions[languageMode]}`);
  languageButton.title = actions[languageMode];
  const line = lines[index];
  czechText.textContent = languageMode > 0 && line && !line.silent ? line.translation.text : "";
  czechText.hidden = !czechText.textContent;
  dictionaryItems.forEach(({item, button, translation}) => {
    translation.hidden = languageMode === 0;
    button.setAttribute("aria-label", languageMode > 0 ? `${item.en} — ${item.cz}` : item.en);
  });
  if (lines.length) showFrame(lines[index >= 0 ? index : openingIndex]);
}

function updateControls() {
  repeatButton.disabled = index < 0 || playing || Boolean(lines[index]?.silent) || !dictionaryPanel.hidden;
  nextButton.disabled = playing || failed || index >= lines.length - 1;
  nextButton.hidden = index < 0 || index >= lines.length - 1;
  restartButton.hidden = index < 0 || index !== lines.length - 1 || playing || failed || !dictionaryPanel.hidden;
  dictionaryButton.hidden = !dictionaryAvailable();
  dictionaryButton.disabled = !dictionaryAvailable() || (playing && !activeVocabulary);
  dictionaryItems.forEach(({item, button}) => {
    button.disabled = playing || !dictionaryAvailable();
    button.setAttribute("aria-current", String(activeVocabulary === item));
  });
  const nextPicture = lines[index] && lines[index + 1] &&
    (lines[index].picture.id !== lines[index + 1].picture.id ||
      lines[index].frame.image !== lines[index + 1].frame.image);
  nextButton.textContent = nextPicture ? "Next picture ▶" : "Next ▶";
}

function stopAudio() {
  generation += 1;
  if (activeAudio) {
    activeAudio.onended = null;
    activeAudio.onerror = null;
    activeAudio.pause();
    activeAudio = null;
  }
  playing = false;
  audioLanguage = "";
}

function showFrame(line) {
  const picture = line.picture;
  const frame = line.frame;
  scene.dataset.picture = String(picture.id);
  scene.dataset.image = frame.image;
  scene.dataset.layout = languageMode > 0 ? "below" : (picture.layout || "overlay");
  scene.setAttribute("aria-label", `Scene 6 — ${picture.title}`);
  sceneImage.src = frame.image;
  sceneImage.alt = frame.alt;
  sceneImage.width = frame.width;
  sceneImage.height = frame.height;
}

function playLine(newIndex) {
  if (!Number.isInteger(newIndex) || !lines[newIndex]) return;
  stopAudio();
  closeDictionary(false);
  index = newIndex;
  if (index !== lines.length - 1) finalCompleted = false;
  const line = lines[index];
  const picture = line.picture;
  showFrame(line);
  startButton.hidden = true;
  status.classList.remove("error");
  failed = false;
  failedLanguage = "";
  updateLanguageUi();
  if (line.silent) {
    speakerName.textContent = "";
    speechText.textContent = "";
    lineNumber.textContent = "";
    speechBubble.hidden = true;
    status.textContent = picture.title;
    updateControls();
    return;
  }
  speakerName.textContent = line.speaker;
  speechText.textContent = line.text;
  lineNumber.textContent = `${line.pictureLine} / ${picture.line_count}`;
  speechBubble.hidden = false;
  status.textContent = "";
  playClip(line.audio, "en", () => {
    if (languageMode === 2) playCzech();
    else finishLine(false);
  });
}

function finishLine(error, language = "") {
  playing = false;
  failed = error;
  failedLanguage = error ? language : "";
  if (!error && index === lines.length - 1) finalCompleted = true;
  status.classList.toggle("error", error);
  const line = lines[index];
  status.textContent = error ? `${language === "cs" ? "Czech audio" : "Audio"} unavailable. Tap Repeat.` :
    (line.pictureLine === line.picture.line_count ? `${line.picture.title} · Picture ${line.picture.id} complete` : "");
  updateControls();
}

function playClip(path, language, onDone) {
  const token = generation;
  playing = true;
  audioLanguage = language;
  updateControls();
  const audio = new Audio(path);
  activeAudio = audio;
  const settle = (error) => {
    if (token !== generation || activeAudio !== audio) return;
    audio.onended = null;
    audio.onerror = null;
    audio.pause();
    activeAudio = null;
    playing = false;
    audioLanguage = "";
    if (error) finishPlayback(true, language);
    else onDone();
  };
  audio.onended = () => settle(false);
  audio.onerror = () => settle(true);
  try {
    const promise = audio.play();
    if (promise) promise.catch(() => settle(true));
  } catch (_error) { settle(true); }
}

function playCzech() {
  if (activeVocabulary) {
    dictionaryStatus.textContent = "";
    vocabularyFailedLanguage = "";
    playClip(`audio/vocabulary/cs/${activeVocabulary.id}.mp3`, "cs", () => finishPlayback(false));
    return;
  }
  status.textContent = "";
  status.classList.remove("error");
  failed = false;
  failedLanguage = "";
  playClip(lines[index].translation.audio, "cs", () => finishLine(false));
}

languageButton.addEventListener("click", () => {
  const stopCzech = audioLanguage === "cs" || (failed && failedLanguage === "cs") || vocabularyFailedLanguage === "cs";
  languageMode = (languageMode + 1) % 3;
  try { window.localStorage.setItem(LANGUAGE_KEY, String(languageMode)); } catch (_error) { /* Optional storage. */ }
  updateLanguageUi();
  if (languageMode !== 2 && stopCzech) {
    stopAudio();
    finishPlayback(false);
  } else if (languageMode === 2 && index >= 0 && !lines[index].silent && !playing && !failed &&
      !vocabularyFailedLanguage && (dictionaryPanel.hidden || activeVocabulary)) {
    playCzech();
  }
});

function finishPlayback(error, language = "") {
  if (!activeVocabulary) { finishLine(error, language); return; }
  playing = false;
  vocabularyFailedLanguage = error ? language : "";
  dictionaryStatus.textContent = error ? "Zvuk není dostupný. Klepni na slovíčko znovu." : "";
  updateControls();
}

function closeDictionary(restoreFocus = true) {
  const wasOpen = !dictionaryPanel.hidden;
  if (activeVocabulary && playing) stopAudio();
  activeVocabulary = null;
  vocabularyFailedLanguage = "";
  dictionaryStatus.textContent = "";
  dictionaryPanel.hidden = true;
  dictionaryButton.setAttribute("aria-expanded", "false");
  if (wasOpen && restoreFocus) dictionaryButton.focus?.();
  updateControls();
}

function playVocabulary(item) {
  if (!dictionaryAvailable() || dictionaryPanel.hidden || playing) return;
  stopAudio();
  activeVocabulary = item;
  vocabularyFailedLanguage = "";
  dictionaryStatus.textContent = "";
  playClip(`audio/vocabulary/en/${item.id}.mp3`, "en", () => {
    if (languageMode === 2) playCzech();
    else finishPlayback(false);
  });
}

function renderDictionary(items) {
  dictionaryList.replaceChildren();
  dictionaryItems = items.map((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "dictionary-item";
    button.setAttribute("aria-label", item.en);
    const emoji = document.createElement("span");
    emoji.className = "dictionary-emoji"; emoji.textContent = item.emoji; emoji.setAttribute("aria-hidden", "true");
    const word = document.createElement("span"); word.className = "dictionary-word"; word.textContent = item.en;
    const translation = document.createElement("span"); translation.className = "dictionary-translation";
    translation.lang = "cs"; translation.textContent = item.cz;
    button.append(emoji, word, translation);
    button.addEventListener("click", () => playVocabulary(item));
    dictionaryList.append(button);
    return {item, button, translation};
  });
}

dictionaryButton.addEventListener("click", () => {
  if (!dictionaryPanel.hidden) { closeDictionary(); return; }
  if (!dictionaryAvailable() || playing) return;
  dictionaryPanel.hidden = false;
  dictionaryButton.setAttribute("aria-expanded", "true");
  updateControls();
  dictionaryClose.focus?.();
});
dictionaryClose.addEventListener("click", () => closeDictionary());
window.addEventListener("keydown", (event) => { if (event.key === "Escape" && !dictionaryPanel.hidden) closeDictionary(); });

startButton.addEventListener("click", () => { if (index < 0 && lines.length) playLine(openingIndex); });
nextButton.addEventListener("click", () => { if (!playing && !failed) playLine(index + 1); });
repeatButton.addEventListener("click", () => { if (!playing) playLine(index); });
restartButton.addEventListener("click", () => { if (!playing) playLine(0); });
window.addEventListener("pagehide", () => { stopAudio(); updateControls(); });
window.addEventListener("pageshow", () => { if (!playing) updateControls(); });

function readJson(path) {
  return fetch(path).then((response) => {
    if (!response.ok) throw new Error("scene data");
    return response.json();
  });
}

function validImage(frame) {
  return frame && /^[a-z0-9_]+\.webp$/.test(frame.image) && typeof frame.alt === "string" &&
    Number.isInteger(frame.width) && frame.width > 0 && Number.isInteger(frame.height) && frame.height > 0;
}

readJson("pictures.json?v=20261110dictionary1")
  .then((catalog) => {
    const lineCounts = [7, 10, 8, 7, 7, 8, 8, 6, 0, 6];
    if (catalog.schema_version !== 1 || !Array.isArray(catalog.pictures) || catalog.pictures.length !== 10 ||
        !catalog.pictures.every((picture, n) => picture.id === n + 1 &&
          picture.dialogue === (n === 0 ? "dialogue.json" : `dialogue_${String(picture.id).padStart(2, "0")}.json`) &&
          picture.line_count === lineCounts[n] && typeof picture.title === "string" && validImage(picture) &&
          (picture.layout === undefined || picture.layout === "below") &&
          (picture.image_changes === undefined || (Array.isArray(picture.image_changes) &&
            picture.image_changes.every((frame, i, frames) => validImage(frame) && Number.isInteger(frame.from_line) &&
              frame.from_line > 1 && frame.from_line <= picture.line_count &&
              (i === 0 || frame.from_line > frames[i - 1].from_line)))))) throw new Error("pictures");
    return Promise.all(catalog.pictures.map((picture) =>
      readJson(`${picture.dialogue}?v=20261110dictionary1`).then((data) => {
        const audioPattern = picture.id === 1 ? /^audio\/en\/[0-9]{2}_[a-z]+\.mp3$/ :
          new RegExp(`^audio/en/p${String(picture.id).padStart(2, "0")}_[0-9]{2}_[a-z_]+\\.mp3$`);
        if (data.schema_version !== 1 || data.picture !== picture.id || !Array.isArray(data.lines) ||
            (picture.id === 9) !== (data.silent === true) ||
            data.lines.length !== picture.line_count || !data.lines.every((line) =>
              typeof line.speaker === "string" && typeof line.text === "string" && audioPattern.test(line.audio))) {
          throw new Error("dialogue");
        }
        if (data.silent) return [{picture, frame: picture, silent: true, pictureLine: 0}];
        return data.lines.map((line, n) => {
          let frame = picture;
          for (const change of picture.image_changes || []) {
            if (n + 1 < change.from_line) break;
            frame = change;
          }
          return {...line, picture, pictureLine: n + 1, frame};
        });
      })));
  })
  .then((pictures) => {
    lines = pictures.flat();
    return readJson("translations_cs.json?v=20261110dictionary1").then((data) => {
      const spoken = lines.filter((line) => !line.silent);
      if (data.schema_version !== 1 || data.language !== "cs" || !Array.isArray(data.lines) ||
          data.lines.length !== spoken.length) throw new Error("translations");
      spoken.forEach((line, n) => {
        const row = data.lines[n];
        const prefix = `p${String(line.picture.id).padStart(2, "0")}_${String(line.pictureLine).padStart(2, "0")}`;
        if (row.audio_en !== line.audio || row.english !== line.text || row.speaker !== line.speaker ||
            row.picture !== line.picture.id || row.number !== line.pictureLine ||
            typeof row.text !== "string" || !row.text.trim() || row.voice !== "cs-CZ-VlastaNeural" ||
            row.audio !== `audio/cs/${prefix}_${line.speaker.toLowerCase().replace(/ /g, "_")}.mp3`) throw new Error("translation");
        line.translation = row;
      });
    });
  })
  .then(() => {
    return readJson("vocabulary.json?v=20261110dictionary1").then((data) => {
      if (data.schema_version !== 1 || !Array.isArray(data.entries) || data.entries.length === 0 ||
          !data.entries.every((item, n) => item.id === `v${String(n + 1).padStart(2, "0")}` &&
            typeof item.en === "string" && item.en.trim() && typeof item.cz === "string" && item.cz.trim() &&
            typeof item.emoji === "string")) throw new Error("vocabulary");
      renderDictionary(data.entries);
    });
  })
  .then(() => {
    const requested = Number(window.location?.hash?.match(/^#picture=(\d+)$/)?.[1] || 1);
    const requestedIndex = lines.findIndex((line) => line.picture.id === requested);
    openingIndex = requestedIndex >= 0 ? requestedIndex : 0;
    updateLanguageUi();
    languageButton.disabled = false;
    updateControls();
    status.textContent = "";
    startButton.disabled = false;
  })
  .catch(() => {
    status.textContent = "The scene could not load. Please reload.";
    status.classList.add("error");
  });
