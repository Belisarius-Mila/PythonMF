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
const taskIcon = document.getElementById("taskIcon");
const scene = document.getElementById("scene");
const logsLayer = document.getElementById("logsLayer");
const logButtons = [...document.querySelectorAll("[data-log]")];
const finalScene = document.getElementById("finalScene");
const benjiAcrossScene = document.getElementById("benjiAcrossScene");
const sunnyAcrossScene = document.getElementById("sunnyAcrossScene");
const fionaAcrossScene = document.getElementById("fionaAcrossScene");
const brunoBunnyCrossingScene = document.getElementById("brunoBunnyCrossingScene");
const lampFallingScene = document.getElementById("lampFallingScene");
const lampRescuedScene = document.getElementById("lampRescuedScene");
const benjiTarget = document.getElementById("benjiTarget");
const sunnyTarget = document.getElementById("sunnyTarget");
const fionaTarget = document.getElementById("fionaTarget");
const brunoTarget = document.getElementById("brunoTarget");
const loganTarget = document.getElementById("loganTarget");
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
  whoFirst: dialogue("logan", "Who wants to go first?", "Kdo chce jít první?"),
  benjiFirst: dialogue("benji", "I will go first.", "Já půjdu první."),
  tapBenji: prompt("benji", "Tap Benji and help him cross.", "Klepni na Benjiho a pomoz mu přejít."),
  benjiSafe: dialogue("benji", "I did it! The bridge is safe.", "Zvládl jsem to! Most je bezpečný."),
  sunnyTurn: dialogue("sunny", "My turn! I can jump.", "Teď já! Umím skákat."),
  tapSunny: prompt("sunny", "Tap Sunny. Help her jump across.", "Klepni na Sunny. Pomoz jí přeskákat."),
  threeJumps: dialogue("sunny", "One, two, three!", "Raz, dva, tři!"),
  bunnyScared: dialogue("bunny", "Oh no... I am scared.", "Ach ne... Já se bojím."),
  bridgeSafeBunny: dialogue("benji", "The bridge is safe, Bunny!", "Most je bezpečný, Bunny!"),
  fionaShows: dialogue("fiona", "Watch me, Bunny.", "Dívej se, Bunny."),
  tapFiona: prompt("fiona", "Tap Fiona and help her cross.", "Klepni na Fionu a pomoz jí přejít."),
  fionaSafe: dialogue("fiona", "I crossed the bridge safely!", "Bezpečně jsem přešla most!"),
  bagHeavy: dialogue("bunny", "My bag is too heavy.", "Můj batoh je příliš těžký."),
  brunoHelps: dialogue("bruno", "I can help you.", "Mohu ti pomoci."),
  giveBag: dialogue("bruno", "Give me your bag.", "Dej mi svůj batoh."),
  bunnyThanks: dialogue("bunny", "Thank you, Bruno.", "Děkuji, Bruno."),
  tapBruno: prompt("bruno", "Tap Bruno. Help Bunny cross.", "Klepni na Bruna. Pomoz Bunnymu přejít."),
  oneStep: dialogue("bruno", "One step at a time, Bunny.", "Krok za krokem, Bunny."),
  lampDropped: dialogue("bruno", "Oh no, my lamp!", "Ach ne, moje lampa!"),
  loganGetsLamp: dialogue("logan", "Do not worry. I can get it.", "Neboj se. Já ji vytáhnu."),
  tapLogan: prompt("logan", "Tap Logan and save the lamp.", "Klepni na Logana a zachraň lampu."),
  lampReturned: dialogue("logan", "Here is your lamp, Bruno.", "Tady je tvoje lampa, Bruno."),
  brunoThanks: dialogue("bruno", "Thank you, Logan!", "Děkuji, Logane!"),
  loganWelcome: dialogue("logan", "You are welcome, friends.", "Není zač, kamarádi."),
  toTheLake: dialogue("benji", "To the lake!", "K jezeru!"),
};

const introLines = [lines.bridgeGone, lines.streamWide, lines.getAcross, lines.loganHello, lines.loganHelp, lines.strongLogs, lines.tapLogs];
const countLines = [lines.oneLog, lines.twoLogs, lines.threeLogs];
const benjiLines = [lines.bridgeReady, lines.whoFirst, lines.benjiFirst, lines.tapBenji];
const sunnyLines = [lines.sunnyTurn, lines.tapSunny];
const bunnyLines = [lines.bunnyScared, lines.bridgeSafeBunny, lines.fionaShows, lines.tapFiona];
const helpLines = [lines.bagHeavy, lines.brunoHelps, lines.giveBag, lines.bunnyThanks, lines.tapBruno];
const lampLines = [lines.lampDropped, lines.loganGetsLamp, lines.tapLogan];
const finishLines = [lines.brunoThanks, lines.loganWelcome, lines.toTheLake];

const state = {
  stage: "waiting",
  languageMode: loadLanguageMode(),
  lineIndex: -1,
  crossingIndex: -1,
  placedLogs: 0,
  currentEntry: null,
  isPlaying: false,
  isAnimating: false,
  activeAudio: null,
};

const wait = (milliseconds) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));

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
    taskIcon.textContent = entry === lines.tapLogs ? "🪵" : ({ benji: "🐶", sunny: "🐿️", fiona: "🦊", bruno: "🦡", logan: "🦫" })[entry.speaker] || "👆";
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
  if (state.isPlaying || state.isAnimating) return false;
  if (state.stage === "intro") return state.lineIndex < introLines.length - 1;
  if (state.stage === "bridge-ready") return true;
  if (state.stage === "benji-dialogue") return state.crossingIndex < benjiLines.length - 1;
  if (state.stage === "sunny-dialogue") return state.crossingIndex < sunnyLines.length - 1;
  if (state.stage === "bunny-dialogue") return state.crossingIndex < bunnyLines.length - 1;
  if (state.stage === "help-dialogue") return state.crossingIndex < helpLines.length - 1;
  if (state.stage === "lamp-dialogue") return state.crossingIndex < lampLines.length - 1;
  if (state.stage === "finish-dialogue") return state.crossingIndex < finishLines.length - 1;
  return state.stage === "bunny-ready" || state.stage === "help-ready" || state.stage === "lamp-ready" || state.stage === "finish-ready";
}

function updateControls() {
  languageButton.disabled = state.isPlaying || state.isAnimating;
  repeatButton.disabled = !state.currentEntry || state.isPlaying || state.isAnimating;
  const showNext = shouldShowNext();
  nextButton.classList.toggle("hidden", !showNext);
  nextButton.disabled = !showNext;
  for (const button of logButtons) {
    button.disabled = state.stage !== "logs" || state.isPlaying || state.isAnimating || button.classList.contains("placed");
  }
  benjiTarget.disabled = state.stage !== "wait-benji" || state.isPlaying || state.isAnimating;
  sunnyTarget.disabled = state.stage !== "wait-sunny" || state.isPlaying || state.isAnimating;
  fionaTarget.disabled = state.stage !== "wait-fiona" || state.isPlaying || state.isAnimating;
  brunoTarget.disabled = state.stage !== "wait-bruno" || state.isPlaying || state.isAnimating;
  loganTarget.disabled = state.stage !== "wait-logan" || state.isPlaying || state.isAnimating;
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
    state.stage = "benji-dialogue";
    state.crossingIndex = 0;
    taskPrompt.classList.add("hidden");
    await playEntry(benjiLines[state.crossingIndex]);
    updateControls();
    return;
  }
  if (state.stage === "benji-dialogue") {
    state.crossingIndex += 1;
    const entry = benjiLines[state.crossingIndex];
    await playEntry(entry);
    if (entry === lines.tapBenji) {
      state.stage = "wait-benji";
      benjiTarget.classList.remove("hidden");
      updateControls();
    }
    return;
  }
  if (state.stage === "sunny-dialogue") {
    state.crossingIndex += 1;
    const entry = sunnyLines[state.crossingIndex];
    await playEntry(entry);
    if (entry === lines.tapSunny) {
      state.stage = "wait-sunny";
      sunnyTarget.classList.remove("hidden");
      updateControls();
    }
    return;
  }
  if (state.stage === "bunny-ready") {
    state.stage = "bunny-dialogue";
    state.crossingIndex = 0;
    await playEntry(bunnyLines[state.crossingIndex]);
    updateControls();
    return;
  }
  if (state.stage === "bunny-dialogue") {
    state.crossingIndex += 1;
    const entry = bunnyLines[state.crossingIndex];
    await playEntry(entry);
    if (entry === lines.tapFiona) {
      state.stage = "wait-fiona";
      fionaTarget.classList.remove("hidden");
      updateControls();
    }
    return;
  }
  if (state.stage === "help-ready") {
    state.stage = "help-dialogue";
    state.crossingIndex = 0;
    await playEntry(helpLines[state.crossingIndex]);
    updateControls();
    return;
  }
  if (state.stage === "help-dialogue") {
    state.crossingIndex += 1;
    const entry = helpLines[state.crossingIndex];
    await playEntry(entry);
    if (entry === lines.tapBruno) {
      state.stage = "wait-bruno";
      brunoTarget.classList.remove("hidden");
      updateControls();
    }
    return;
  }
  if (state.stage === "lamp-ready") {
    state.stage = "lamp-dialogue";
    state.crossingIndex = 0;
    await Promise.all([
      revealStoryState(lampFallingScene, "lamp-falling"),
      playEntry(lampLines[state.crossingIndex]),
    ]);
    updateControls();
    return;
  }
  if (state.stage === "lamp-dialogue") {
    state.crossingIndex += 1;
    const entry = lampLines[state.crossingIndex];
    await playEntry(entry);
    if (entry === lines.tapLogan) {
      state.stage = "wait-logan";
      loganTarget.classList.remove("hidden");
      updateControls();
    }
    return;
  }
  if (state.stage === "finish-ready") {
    state.stage = "finish-dialogue";
    state.crossingIndex = 0;
    await playEntry(finishLines[state.crossingIndex]);
    updateControls();
    return;
  }
  if (state.stage === "finish-dialogue") {
    state.crossingIndex += 1;
    const entry = finishLines[state.crossingIndex];
    await playEntry(entry);
    if (entry === lines.toTheLake) {
      state.stage = "complete";
      completeBanner.classList.remove("hidden");
    }
    updateControls();
    return;
  }
}

function flightFrames(button, index) {
  const rect = scene.getBoundingClientRect();
  const restTransform = getComputedStyle(button).getPropertyValue("--rest-transform").trim();
  const startX = rect.width * (0.47 + index * 0.025);
  const startY = rect.height * (0.28 - index * 0.025);
  const arcX = rect.width * (0.2 + index * 0.018);
  const arcY = -rect.height * (0.13 + index * 0.012);
  const startRotation = 25 - index * 7;
  const mirrored = index === 2 ? "scaleX(-1) " : "";
  return [
    { opacity: 1, transform: `translate(${startX}px, ${startY}px) ${mirrored}rotate(${startRotation}deg) scale(0.36)`, offset: 0 },
    { opacity: 1, transform: `translate(${startX * 0.92}px, ${startY * 0.82}px) ${mirrored}rotate(${startRotation - 4}deg) scale(0.44)`, offset: 0.12 },
    { opacity: 1, transform: `translate(${arcX}px, ${arcY}px) ${mirrored}rotate(${7 - index * 3}deg) scale(0.78)`, offset: 0.58 },
    { opacity: 1, transform: `translate(0, -${Math.round(rect.height * 0.018)}px) ${restTransform} scale(1.025)`, offset: 0.9 },
    { opacity: 1, transform: `translate(0, 0) ${restTransform}`, offset: 1 },
  ];
}

async function flyLog(button, index) {
  button.classList.add("placing");
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reducedMotion || typeof button.animate !== "function") {
    button.classList.remove("placing");
    button.classList.add("placed");
    return;
  }
  const animation = button.animate(flightFrames(button, index), {
    duration: 1180,
    easing: "cubic-bezier(0.2, 0.78, 0.22, 1)",
    fill: "forwards",
  });
  try {
    await animation.finished;
  } catch (_error) {
    // A cancelled animation still lands safely in its final state.
  }
  button.classList.remove("placing");
  button.classList.add("placed");
  button.style.transform = getComputedStyle(button).getPropertyValue("--rest-transform").trim();
  animation.cancel();
}

async function revealFinalScene() {
  await wait(260);
  finalScene.classList.add("visible");
  scene.dataset.sceneState = "bridge-complete";
}

async function revealStoryState(element, sceneState) {
  element.classList.add("visible");
  scene.dataset.sceneState = sceneState;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  await wait(reducedMotion ? 1 : 540);
}

async function placeLog(button) {
  if (state.stage !== "logs" || state.isPlaying || state.isAnimating || button.classList.contains("placed")) return;
  state.isAnimating = true;
  updateControls();
  const logIndex = state.placedLogs;
  state.placedLogs += 1;
  await Promise.all([flyLog(button, logIndex), playEntry(countLines[logIndex])]);
  if (state.placedLogs === logButtons.length) {
    await revealFinalScene();
    state.stage = "bridge-ready";
  }
  state.isAnimating = false;
  updateControls();
}

async function crossWithBenji() {
  if (state.stage !== "wait-benji" || state.isPlaying || state.isAnimating) return;
  state.isAnimating = true;
  benjiTarget.classList.add("hidden");
  taskPrompt.classList.add("hidden");
  updateControls();
  await revealStoryState(benjiAcrossScene, "benji-across");
  await playEntry(lines.benjiSafe);
  state.stage = "sunny-dialogue";
  state.crossingIndex = -1;
  state.isAnimating = false;
  updateControls();
}

async function crossWithSunny() {
  if (state.stage !== "wait-sunny" || state.isPlaying || state.isAnimating) return;
  state.isAnimating = true;
  sunnyTarget.classList.add("hidden");
  taskPrompt.classList.add("hidden");
  updateControls();
  await Promise.all([
    revealStoryState(sunnyAcrossScene, "benji-sunny-across"),
    playEntry(lines.threeJumps),
  ]);
  state.stage = "bunny-ready";
  state.isAnimating = false;
  updateControls();
}

async function crossWithFiona() {
  if (state.stage !== "wait-fiona" || state.isPlaying || state.isAnimating) return;
  state.isAnimating = true;
  fionaTarget.classList.add("hidden");
  taskPrompt.classList.add("hidden");
  updateControls();
  await revealStoryState(fionaAcrossScene, "fiona-across");
  await playEntry(lines.fionaSafe);
  state.stage = "help-ready";
  state.isAnimating = false;
  updateControls();
}

async function crossWithBruno() {
  if (state.stage !== "wait-bruno" || state.isPlaying || state.isAnimating) return;
  state.isAnimating = true;
  brunoTarget.classList.add("hidden");
  taskPrompt.classList.add("hidden");
  updateControls();
  await revealStoryState(brunoBunnyCrossingScene, "bruno-bunny-crossing");
  await playEntry(lines.oneStep);
  state.stage = "lamp-ready";
  state.isAnimating = false;
  updateControls();
}

async function rescueLampWithLogan() {
  if (state.stage !== "wait-logan" || state.isPlaying || state.isAnimating) return;
  state.isAnimating = true;
  loganTarget.classList.add("hidden");
  taskPrompt.classList.add("hidden");
  updateControls();
  await revealStoryState(lampRescuedScene, "lamp-rescued");
  await playEntry(lines.lampReturned);
  state.stage = "finish-ready";
  state.isAnimating = false;
  updateControls();
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
benjiTarget.addEventListener("click", crossWithBenji);
sunnyTarget.addEventListener("click", crossWithSunny);
fionaTarget.addEventListener("click", crossWithFiona);
brunoTarget.addEventListener("click", crossWithBruno);
loganTarget.addEventListener("click", rescueLampWithLogan);
updateLanguageUi();
updateControls();
