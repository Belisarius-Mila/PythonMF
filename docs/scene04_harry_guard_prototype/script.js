/**
 * MMTX prototype: Harry questions Benji at the sheep gate.
 *
 * Standalone by design. It is not linked from the production journey yet.
 */

const scene = document.getElementById("scene");
const overlay = document.getElementById("overlay");
const speechBubble = document.getElementById("speechBubble");
const speakerName = document.getElementById("speakerName");
const speechEnglish = document.getElementById("speechEnglish");
const speechCzech = document.getElementById("speechCzech");
const taskPrompt = document.getElementById("taskPrompt");
const taskEnglish = document.getElementById("taskEnglish");
const taskCzech = document.getElementById("taskCzech");
const answerPanel = document.getElementById("answerPanel");
const yesButton = document.getElementById("yesButton");
const noButton = document.getElementById("noButton");
const completeBanner = document.getElementById("completeBanner");
const audioGate = document.getElementById("audioGate");
const languageButton = document.getElementById("languageButton");
const repeatButton = document.getElementById("repeatButton");

const LANGUAGE_STORAGE_KEY = "mmtx-language-mode";
const LANGUAGE_MODES = {
  english: "en",
  bilingual: "en-cz",
};

const BENJI_AUDIO_VERSION = "20260813a";
const BENJI_ENGLISH_AUDIO = new Map([
  ["Hello. We are friendly.", `audio/english/scene04_benji_hello_we_are_friendly_en.mp3?v=${BENJI_AUDIO_VERSION}`],
  ["I have a map.", `audio/english/scene04_benji_i_have_a_map_en.mp3?v=${BENJI_AUDIO_VERSION}`],
  ["No. I do not chase sheep.", `audio/english/scene04_benji_no_i_do_not_chase_sheep_en.mp3?v=${BENJI_AUDIO_VERSION}`],
  ["I help little animals.", `audio/english/scene04_benji_i_help_little_animals_en.mp3?v=${BENJI_AUDIO_VERSION}`],
]);

// Keep Benji on a male voice even when the browser exposes voices in a
// different order. Andrew matches the approved Scene 3 voice when available.
const BENJI_ENGLISH_VOICE_ORDER = [
  "andrew",
  "evan",
  "alex",
  "aaron",
  "daniel",
  "reed",
  "eddy",
  "fred",
];

const STAGES = {
  waitingStart: "waitingStart",
  intro: "intro",
  chooseBenji: "chooseBenji",
  benjiAnswer: "benjiAnswer",
  chooseYesNo: "chooseYesNo",
  wrongYes: "wrongYes",
  finishing: "finishing",
  complete: "complete",
};

const characters = {
  bunny: { label: "Bunny", rect: { x: 0, y: 36, w: 13, h: 42 } },
  bruno: { label: "Bruno", rect: { x: 12, y: 34, w: 14, h: 43 } },
  fiona: { label: "Fiona", rect: { x: 24, y: 35, w: 14, h: 43 } },
  sunny: { label: "Sunny", rect: { x: 32, y: 46, w: 12, h: 35 } },
  benji: { label: "Benji", rect: { x: 39, y: 38, w: 16, h: 47 } },
  harry: { label: "Harry", rect: { x: 58, y: 29, w: 34, h: 56 } },
};

function dialogue(characterId, textEn, textCz) {
  return { kind: "dialogue", characterId, textEn, textCz };
}

function prompt(textEn, textCz) {
  return { kind: "prompt", characterId: "harry", textEn, textCz };
}

const lines = {
  stop: dialogue("harry", "Stop! Do not come closer!", "Stůjte! Nepřibližujte se!"),
  friendly: dialogue("benji", "Hello. We are friendly.", "Ahoj. Jsme přátelé."),
  strangers: dialogue("harry", "Friendly? I do not know you.", "Přátelé? Já vás neznám."),
  mapQuestion: prompt("Who has the map?", "Kdo má mapu?"),
  notMe: dialogue("bunny", "Not me.", "Já ne."),
  mapAnswer: dialogue("benji", "I have a map.", "Mám mapu."),
  sheepQuestion: prompt("Do you want to chase my sheep?", "Chceš honit moje ovce?"),
  listenAgain: dialogue("harry", "Listen again.", "Poslechni si otázku znovu."),
  noChase: dialogue("benji", "No. I do not chase sheep.", "Ne. Nehoním ovce."),
  helper: dialogue("benji", "I help little animals.", "Pomáhám malým zvířátkům."),
  trust: dialogue("harry", "Hmm. Maybe I can trust you.", "Hmm. Možná ti můžu věřit."),
};

const state = {
  stage: STAGES.waitingStart,
  languageMode: loadLanguageMode(),
  lastRepeatable: null,
  flowId: 0,
  currentEntry: null,
};

let voices = [];
let speechTimeout = 0;
let speechResolve = null;
let activeAudio = null;
let audioTimeout = 0;
let audioResolve = null;
const fixedAudioCache = new Map();

function loadLanguageMode() {
  try {
    return window.localStorage.getItem(LANGUAGE_STORAGE_KEY) === LANGUAGE_MODES.english
      ? LANGUAGE_MODES.english
      : LANGUAGE_MODES.bilingual;
  } catch (_error) {
    return LANGUAGE_MODES.bilingual;
  }
}

function saveLanguageMode() {
  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, state.languageMode);
  } catch (_error) {
    // The prototype still works when private browsing blocks local storage.
  }
}

function isBilingual() {
  return state.languageMode === LANGUAGE_MODES.bilingual;
}

function updateLanguageUi() {
  languageButton.textContent = isBilingual() ? "EN + CZ" : "EN";
  languageButton.setAttribute(
    "aria-label",
    isBilingual() ? "Používá se angličtina i čeština" : "Používá se pouze angličtina",
  );
  speechCzech.classList.toggle("hidden", !isBilingual() || !speechCzech.textContent);
  taskCzech.classList.toggle("hidden", !isBilingual() || !taskCzech.textContent);
}

function loadVoices() {
  voices = window.speechSynthesis?.getVoices?.() || [];
}

function voiceFor(lang, characterId) {
  const languagePrefix = lang === "cs" ? "cs" : "en";
  const matching = voices.filter((voice) => String(voice.lang || "").toLowerCase().startsWith(languagePrefix));
  if (!matching.length) return null;
  if (lang === "en" && characterId === "benji") {
    for (const preferredName of BENJI_ENGLISH_VOICE_ORDER) {
      const selectedVoice = matching.find((voice) => voice.name.toLowerCase().includes(preferredName));
      if (selectedVoice) return selectedVoice;
    }
    return null;
  }
  if (lang === "en") {
    const preferred = characterId === "harry"
      ? /daniel|roger|guy|alex|aaron/i
      : /samantha|ava|fable/i;
    return matching.find((voice) => preferred.test(voice.name)) || matching[0];
  }
  return matching[0];
}

function cancelSpeech() {
  window.clearTimeout(audioTimeout);
  audioTimeout = 0;
  if (activeAudio) {
    activeAudio.pause();
    activeAudio = null;
  }
  if (audioResolve) {
    const resolve = audioResolve;
    audioResolve = null;
    resolve(false);
  }
  window.clearTimeout(speechTimeout);
  speechTimeout = 0;
  window.speechSynthesis?.cancel?.();
  if (speechResolve) {
    const resolve = speechResolve;
    speechResolve = null;
    resolve();
  }
}

function playFixedAudio(src, textLength) {
  return new Promise((resolve) => {
    let finished = false;
    const audio = fixedAudioCache.get(src) || new Audio(src);
    fixedAudioCache.set(src, audio);
    const finish = (played) => {
      if (finished) return;
      finished = true;
      window.clearTimeout(audioTimeout);
      audioTimeout = 0;
      if (!played) audio.pause();
      audio.onended = null;
      audio.onerror = null;
      if (activeAudio === audio) activeAudio = null;
      if (audioResolve === finish) audioResolve = null;
      resolve(played);
    };
    audio.preload = "auto";
    audio.playsInline = true;
    audio.muted = false;
    audio.volume = 0.9;
    audio.currentTime = 0;
    audio.onended = () => finish(true);
    audio.onerror = () => finish(false);
    activeAudio = audio;
    audioResolve = finish;
    let playback;
    try {
      playback = audio.play();
    } catch (_error) {
      finish(false);
      return;
    }
    if (playback && typeof playback.catch === "function") {
      playback.catch(() => finish(false));
    }
    audioTimeout = window.setTimeout(
      () => finish(false),
      Math.max(3500, textLength * 140),
    );
  });
}

function primeFixedAudio() {
  const sources = [...BENJI_ENGLISH_AUDIO.values()];
  sources.forEach((src) => {
    const audio = fixedAudioCache.get(src) || new Audio(src);
    fixedAudioCache.set(src, audio);
    audio.preload = "auto";
    audio.playsInline = true;
    audio.load();
  });
  const firstAudio = fixedAudioCache.get(sources[0]);
  if (!firstAudio) return;
  firstAudio.muted = true;
  firstAudio.volume = 0;
  let playback;
  try {
    playback = firstAudio.play();
  } catch (_error) {
    firstAudio.muted = false;
    firstAudio.volume = 0.9;
    return;
  }
  if (playback && typeof playback.then === "function") {
    playback.then(() => {
      firstAudio.pause();
      firstAudio.currentTime = 0;
      firstAudio.muted = false;
      firstAudio.volume = 0.9;
    }).catch(() => {
      firstAudio.muted = false;
      firstAudio.volume = 0.9;
    });
  }
}

async function speakText(text, lang, characterId) {
  if (lang === "en" && characterId === "benji") {
    const fixedAudio = BENJI_ENGLISH_AUDIO.get(text);
    if (fixedAudio && await playFixedAudio(fixedAudio, text.length)) return;
  }
  if (!text || !("speechSynthesis" in window)) return Promise.resolve();
  return new Promise((resolve) => {
    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      window.clearTimeout(speechTimeout);
      speechTimeout = 0;
      if (speechResolve === finish) speechResolve = null;
      resolve();
    };
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang === "cs" ? "cs-CZ" : "en-US";
    utterance.rate = lang === "cs" ? 0.9 : 0.94;
    utterance.volume = lang === "cs" ? 0.68 : 0.9;
    const voice = voiceFor(lang, characterId);
    if (lang === "en" && characterId === "benji" && !voice) {
      finish();
      return;
    }
    if (voice) utterance.voice = voice;
    utterance.onend = finish;
    utterance.onerror = finish;
    speechResolve = finish;
    window.speechSynthesis.speak(utterance);
    speechTimeout = window.setTimeout(finish, Math.max(1800, text.length * 95));
  });
}

function showSpeech(entry) {
  state.currentEntry = entry;
  speakerName.textContent = characters[entry.characterId]?.label || "Harry";
  speechEnglish.textContent = entry.textEn;
  speechCzech.textContent = entry.textCz;
  speechBubble.className = `speech-bubble ${entry.characterId}`;
  updateLanguageUi();
}

function hideSpeech() {
  speechBubble.classList.add("hidden");
  state.currentEntry = null;
}

async function playEntry(entry, flowId, { remember = true } = {}) {
  if (flowId !== state.flowId) return false;
  if (remember) {
    state.lastRepeatable = entry;
  }
  showSpeech(entry);
  await speakText(entry.textEn, "en", entry.characterId);
  if (flowId !== state.flowId) return false;
  if (isBilingual()) await speakText(entry.textCz, "cs", entry.characterId);
  return flowId === state.flowId;
}

function showTask(entry) {
  taskEnglish.textContent = entry.textEn;
  taskCzech.textContent = entry.textCz;
  taskPrompt.classList.remove("hidden");
  updateLanguageUi();
}

function hideTask() {
  taskPrompt.classList.add("hidden");
}

function updateRepeatAvailability() {
  const repeatableStages = new Set([
    STAGES.chooseBenji,
    STAGES.chooseYesNo,
    STAGES.complete,
  ]);
  repeatButton.disabled = !state.lastRepeatable || !repeatableStages.has(state.stage);
}

function setStage(stage) {
  state.stage = stage;
  renderHotspots();
  updateRepeatAvailability();
}

function renderHotspots() {
  overlay.replaceChildren();
  const canChooseCharacter = state.stage === STAGES.chooseBenji;
  for (const [characterId, character] of Object.entries(characters)) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "hotspot";
    button.style.left = `${character.rect.x}%`;
    button.style.top = `${character.rect.y}%`;
    button.style.width = `${character.rect.w}%`;
    button.style.height = `${character.rect.h}%`;
    button.setAttribute("aria-label", character.label);
    button.disabled = !canChooseCharacter;
    if (canChooseCharacter) {
      button.classList.add("enabled");
      if (characterId === "benji") button.classList.add("target");
      button.addEventListener("click", () => chooseCharacter(characterId));
    }
    overlay.appendChild(button);
  }
}

async function runIntro() {
  const flowId = ++state.flowId;
  setStage(STAGES.intro);
  hideTask();
  answerPanel.classList.add("hidden");
  for (const entry of [lines.stop, lines.friendly, lines.strangers, lines.mapQuestion]) {
    if (!(await playEntry(entry, flowId))) return;
  }
  hideSpeech();
  showTask(lines.mapQuestion);
  setStage(STAGES.chooseBenji);
}

async function chooseCharacter(characterId) {
  if (state.stage !== STAGES.chooseBenji) return;
  if (characterId !== "benji") {
    const flowId = ++state.flowId;
    cancelSpeech();
    setStage(STAGES.benjiAnswer);
    const wrongLine = { ...lines.notMe, characterId };
    if (!(await playEntry(wrongLine, flowId))) return;
    if (!(await playEntry(lines.mapQuestion, flowId))) return;
    hideSpeech();
    showTask(lines.mapQuestion);
    setStage(STAGES.chooseBenji);
    return;
  }

  const flowId = ++state.flowId;
  cancelSpeech();
  hideTask();
  setStage(STAGES.benjiAnswer);
  if (!(await playEntry(lines.mapAnswer, flowId))) return;
  if (!(await playEntry(lines.sheepQuestion, flowId))) return;
  hideSpeech();
  showTask(lines.sheepQuestion);
  answerPanel.classList.remove("hidden");
  setStage(STAGES.chooseYesNo);
}

async function chooseYes() {
  if (state.stage !== STAGES.chooseYesNo) return;
  const flowId = ++state.flowId;
  cancelSpeech();
  answerPanel.classList.add("hidden");
  hideTask();
  setStage(STAGES.wrongYes);
  if (!(await playEntry(lines.listenAgain, flowId))) return;
  if (!(await playEntry(lines.sheepQuestion, flowId))) return;
  hideSpeech();
  showTask(lines.sheepQuestion);
  answerPanel.classList.remove("hidden");
  setStage(STAGES.chooseYesNo);
}

async function chooseNo() {
  if (state.stage !== STAGES.chooseYesNo) return;
  const flowId = ++state.flowId;
  cancelSpeech();
  answerPanel.classList.add("hidden");
  hideTask();
  setStage(STAGES.finishing);
  for (const entry of [lines.noChase, lines.helper, lines.trust]) {
    if (!(await playEntry(entry, flowId))) return;
  }
  hideSpeech();
  completeBanner.classList.remove("hidden");
  setStage(STAGES.complete);
}

async function repeatLast() {
  if (!state.lastRepeatable || repeatButton.disabled) return;
  const resumeStage = state.stage;
  const flowId = ++state.flowId;
  cancelSpeech();
  repeatButton.disabled = true;
  try {
    await playEntry(state.lastRepeatable, flowId, { remember: false });
    if (flowId !== state.flowId) return;
    hideSpeech();
    if (resumeStage === STAGES.chooseBenji) showTask(lines.mapQuestion);
    if (resumeStage === STAGES.chooseYesNo) showTask(lines.sheepQuestion);
  } finally {
    updateRepeatAvailability();
  }
}

function toggleLanguage() {
  state.languageMode = isBilingual() ? LANGUAGE_MODES.english : LANGUAGE_MODES.bilingual;
  saveLanguageMode();
  updateLanguageUi();
}

async function startPrototype() {
  if (state.stage !== STAGES.waitingStart) return;
  audioGate.classList.add("hidden");
  loadVoices();
  primeFixedAudio();
  await runIntro();
}

audioGate.addEventListener("click", startPrototype);
languageButton.addEventListener("click", toggleLanguage);
repeatButton.addEventListener("click", repeatLast);
yesButton.addEventListener("click", chooseYes);
noButton.addEventListener("click", chooseNo);
window.speechSynthesis?.addEventListener?.("voiceschanged", loadVoices);

updateLanguageUi();
renderHotspots();
