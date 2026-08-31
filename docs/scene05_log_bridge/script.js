"use strict";

const languageButton = document.getElementById("languageButton");
const repeatButton = document.getElementById("repeatButton");
const nextButton = document.getElementById("nextButton");
const audioGate = document.getElementById("audioGate");
const speechBubble = document.getElementById("speechBubble");
const speakerName = document.getElementById("speakerName");
const speechEnglish = document.getElementById("speechEnglish");
const speechCzech = document.getElementById("speechCzech");
const taskPrompt = document.getElementById("taskPrompt");
const taskEnglish = document.getElementById("taskEnglish");
const taskCzech = document.getElementById("taskCzech");
const logsLayer = document.getElementById("logsLayer");
const logButtons = [...document.querySelectorAll("[data-log]")];
const completeBanner = document.getElementById("completeBanner");

const LANGUAGE_MODES = Object.freeze({ english: "en", bilingual: "en-cz" });
const LANGUAGE_STORAGE_KEY = "mmtx-language-mode";

function dialogue(speaker, en, cz) { return Object.freeze({ kind: "dialogue", speaker, en, cz }); }
function prompt(speaker, en, cz) { return Object.freeze({ kind: "prompt", speaker, en, cz }); }

const lines = {
  bridgeGone: dialogue("benji", "Oh no! The old bridge is gone.", "Ach ne! Starý most je pryč."),
  streamWide: dialogue("bunny", "The stream is too wide.", "Potok je příliš široký."),
  getAcross: dialogue("fiona", "How can we get across?", "Jak se dostaneme na druhou stranu?"),
  loganHello: dialogue("logan", "Hello, friends! My name is Logan.", "Ahoj, kamarádi! Jmenuji se Logan."),
  loganHelp: dialogue("logan", "I can help you.", "Mohu vám pomoci."),
  strongLogs: dialogue("logan", "I have three strong logs.", "Mám tři pevné klády."),
  tapLogs: prompt("logan", "Help Logan. Tap the three logs.", "Pomoz Loganovi. Klepni na tři klády."),
  oneLog: dialogue("logan", "One log.", "Jedna kláda."),
  twoLogs: dialogue("logan", "Two logs.", "Dvě klády."),
  threeLogs: dialogue("logan", "Three logs!", "Tři klády!"),
  bridgeReady: dialogue("logan", "Great! The bridge is ready.", "Skvěle! Most je hotový."),
};

const introLines = [lines.bridgeGone, lines.streamWide, lines.getAcross, lines.loganHello, lines.loganHelp, lines.strongLogs, lines.tapLogs];
const countLines = [lines.oneLog, lines.twoLogs, lines.threeLogs];

const state = {
  stage: "waiting",
  languageMode: loadLanguageMode(),
  lineIndex: -1,
  placedLogs: 0,
  currentEntry: null,
  isPlaying: false,
  activeAudio: null,
};

function loadLanguageMode() {
  try {
    return localStorage.getItem(LANGUAGE_STORAGE_KEY) === LANGUAGE_MODES.english ? LANGUAGE_MODES.english : LANGUAGE_MODES.bilingual;
  } catch (_error) {
    return LANGUAGE_MODES.bilingual;
  }
}

function isBilingual() { return state.languageMode === LANGUAGE_MODES.bilingual; }
function saveLanguageMode() {
  try { localStorage.setItem(LANGUAGE_STORAGE_KEY, state.languageMode); } catch (_error) { /* Storage is optional. */ }
}

function updateLanguageUi() {
  languageButton.textContent = isBilingual() ? "EN + CZ" : "EN";
  languageButton.setAttribute("aria-pressed", String(isBilingual()));
  speechCzech.classList.toggle("hidden", !isBilingual());
  taskCzech.classList.toggle("hidden", !isBilingual());
}

function audioPath(entry, language) {
  const manifest = window.SCENE05_AUDIO_MANIFEST;
  if (!manifest || !manifest.dialogue || !manifest.dialogue[language]) return "";
  const text = language === "en" ? entry.en : entry.cz;
  return manifest.dialogue[language][`${entry.speaker}::${text}`] || "";
}

function stopAudio() {
  if (!state.activeAudio) return;
  state.activeAudio.pause();
  state.activeAudio.currentTime = 0;
  state.activeAudio = null;
}

function playFixedAudio(path) {
  return new Promise((resolve) => {
    if (!path) { resolve(); return; }
    const audio = new Audio(path);
    state.activeAudio = audio;
    const finish = () => {
      if (state.activeAudio === audio) state.activeAudio = null;
      resolve();
    };
    audio.addEventListener("ended", finish, { once: true });
    audio.addEventListener("error", finish, { once: true });
    audio.play().catch(finish);
  });
}

function showEntry(entry) {
  if (entry.kind === "prompt") {
    speechBubble.classList.add("hidden");
    taskEnglish.textContent = entry.en;
    taskCzech.textContent = entry.cz;
    taskPrompt.classList.remove("hidden");
    return;
  }
  speakerName.textContent = entry.speaker;
  speechEnglish.textContent = entry.en;
  speechCzech.textContent = entry.cz;
  speechBubble.classList.remove("hidden");
  if (state.stage !== "logs") taskPrompt.classList.add("hidden");
}

function shouldShowNext() {
  if (state.isPlaying) return false;
  if (state.stage === "intro") return state.lineIndex < introLines.length - 1;
  return state.stage === "bridge-ready";
}

function updateControls() {
  languageButton.disabled = state.isPlaying;
  repeatButton.disabled = !state.currentEntry || state.isPlaying;
  const showNext = shouldShowNext();
  nextButton.classList.toggle("hidden", !showNext);
  nextButton.disabled = !showNext;
  for (const button of logButtons) {
    button.disabled = state.stage !== "logs" || state.isPlaying || button.classList.contains("placed");
  }
}

async function playEntry(entry, { remember = true } = {}) {
  stopAudio();
  if (remember) state.currentEntry = entry;
  state.isPlaying = true;
  showEntry(entry);
  updateLanguageUi();
  updateControls();
  await playFixedAudio(audioPath(entry, "en"));
  if (isBilingual()) await playFixedAudio(audioPath(entry, "cs"));
  state.isPlaying = false;
  updateControls();
}

async function startScene() {
  if (state.stage !== "waiting") return;
  audioGate.classList.add("hidden");
  state.stage = "intro";
  state.lineIndex = 0;
  await playEntry(introLines[state.lineIndex]);
}

async function advanceDialogue() {
  if (state.isPlaying || nextButton.disabled) return;
  if (state.stage === "intro") {
    state.lineIndex += 1;
    const entry = introLines[state.lineIndex];
    await playEntry(entry);
    if (entry === lines.tapLogs) {
      state.stage = "logs";
      logsLayer.classList.remove("hidden");
      updateControls();
    }
    return;
  }
  if (state.stage === "bridge-ready") {
    state.stage = "complete";
    taskPrompt.classList.add("hidden");
    await playEntry(lines.bridgeReady);
    completeBanner.classList.remove("hidden");
    updateControls();
  }
}

async function placeLog(button) {
  if (state.stage !== "logs" || state.isPlaying || button.classList.contains("placed")) return;
  button.classList.add("placed");
  state.placedLogs += 1;
  await playEntry(countLines[state.placedLogs - 1]);
  if (state.placedLogs === logButtons.length) {
    state.stage = "bridge-ready";
    updateControls();
  }
}

async function repeatCurrent() {
  if (!state.currentEntry || state.isPlaying || repeatButton.disabled) return;
  await playEntry(state.currentEntry, { remember: false });
}

function toggleLanguage() {
  if (state.isPlaying) return;
  state.languageMode = isBilingual() ? LANGUAGE_MODES.english : LANGUAGE_MODES.bilingual;
  saveLanguageMode();
  updateLanguageUi();
}

audioGate.addEventListener("click", startScene);
nextButton.addEventListener("click", advanceDialogue);
repeatButton.addEventListener("click", repeatCurrent);
languageButton.addEventListener("click", toggleLanguage);
for (const button of logButtons) button.addEventListener("click", () => placeLog(button));
updateLanguageUi();
updateControls();
