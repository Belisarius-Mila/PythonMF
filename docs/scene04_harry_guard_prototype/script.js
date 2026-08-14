/**
 * MMTX prototype: Harry questions Benji, Bunny, Sunny and Fiona at the sheep gate.
 *
 * Standalone by design. It is not linked from the production journey yet.
 */

const scene = document.getElementById("scene");
const sceneImage = document.getElementById("sceneImage");
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

const BUNNY_AUDIO_VERSION = "20260813a";
const BUNNY_ENGLISH_AUDIO = new Map([
  ["Not me.", `audio/english/scene04_bunny_not_me_en.mp3?v=${BUNNY_AUDIO_VERSION}`],
  ["I am Bunny.", `audio/english/scene04_bunny_i_am_bunny_en.mp3?v=${BUNNY_AUDIO_VERSION}`],
  ["No. I have my own carrots.", `audio/english/scene04_bunny_no_i_have_my_own_carrots_en.mp3?v=${BUNNY_AUDIO_VERSION}`],
  ["I only want to go to the lake.", `audio/english/scene04_bunny_i_only_want_to_go_to_the_lake_en.mp3?v=${BUNNY_AUDIO_VERSION}`],
]);

const SUNNY_AUDIO_VERSION = "20260814a";
const SUNNY_ENGLISH_AUDIO = new Map([
  ["Hello! I am Sunny.", `audio/english/scene04_sunny_hello_i_am_sunny_en.mp3?v=${SUNNY_AUDIO_VERSION}`],
  ["No. I have my own nuts.", `audio/english/scene04_sunny_no_i_have_my_own_nuts_en.mp3?v=${SUNNY_AUDIO_VERSION}`],
  ["I want to go to the lake with my friends.", `audio/english/scene04_sunny_i_want_to_go_to_the_lake_with_my_friends_en.mp3?v=${SUNNY_AUDIO_VERSION}`],
]);

const FIONA_AUDIO_VERSION = "20260814a";
const FIONA_ENGLISH_AUDIO = new Map([
  ["Hi. I am Fiona.", `audio/english/scene04_fiona_hi_i_am_fiona_en.mp3?v=${FIONA_AUDIO_VERSION}`],
  ["No. I do not catch chickens.", `audio/english/scene04_fiona_no_i_do_not_catch_chickens_en.mp3?v=${FIONA_AUDIO_VERSION}`],
  ["I want to go to the lake with my friends.", `audio/english/scene04_fiona_i_want_to_go_to_the_lake_with_my_friends_en.mp3?v=${FIONA_AUDIO_VERSION}`],
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

const BUNNY_ENGLISH_VOICE_ORDER = [
  "ana",
  "samantha",
  "ava",
  "fable",
];

const SUNNY_ENGLISH_VOICE_ORDER = [
  "michelle",
  "nova",
  "samantha",
  "ava",
  "victoria",
  "karen",
];

const FIONA_ENGLISH_VOICE_ORDER = [
  "jenny",
  "shimmer",
  "samantha",
  "ava",
  "victoria",
  "karen",
];

const STAGES = {
  waitingStart: "waitingStart",
  intro: "intro",
  chooseBenji: "chooseBenji",
  benjiAnswer: "benjiAnswer",
  chooseYesNo: "chooseYesNo",
  wrongYes: "wrongYes",
  chooseBunny: "chooseBunny",
  bunnyAnswer: "bunnyAnswer",
  chooseBunnyYesNo: "chooseBunnyYesNo",
  wrongBunnyYes: "wrongBunnyYes",
  chooseSunny: "chooseSunny",
  sunnyAnswer: "sunnyAnswer",
  chooseSunnyYesNo: "chooseSunnyYesNo",
  wrongSunnyYes: "wrongSunnyYes",
  chooseFiona: "chooseFiona",
  fionaAnswer: "fionaAnswer",
  chooseFionaYesNo: "chooseFionaYesNo",
  wrongFionaYes: "wrongFionaYes",
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

const SCENE_IMAGES = Object.freeze({
  group: {
    src: "harry_benji_prototype_01.png",
    alt: "Benji a jeho přátelé stojí před ovčáckým psem Harrym u zavřené ohrady s pěti ovcemi",
  },
  bunny: {
    src: "harry_interrogation_bunny_01.png",
    alt: "Bunny mluví s ovčáckým psem Harrym u zahrádky a zavřené ohrady s pěti ovcemi",
  },
  sunny: {
    src: "harry_interrogation_sunny_01.png",
    alt: "Sunny mluví s ovčáckým psem Harrym pod ořešákem u zavřené ohrady s pěti ovcemi",
  },
  fiona: {
    src: "harry_interrogation_fiona_01.png",
    alt: "Fiona mluví s ovčáckým psem Harrym u dvora se slepicemi a zavřené ohrady s pěti ovcemi",
  },
});

const SCENE_HOTSPOTS = Object.freeze({
  group: Object.freeze(Object.fromEntries(
    Object.entries(characters).map(([characterId, character]) => [characterId, character.rect]),
  )),
  bunny: Object.freeze({
    bunny: { x: 22, y: 29, w: 20, h: 61 },
    bruno: { x: 1, y: 31, w: 11, h: 25 },
    fiona: { x: 9, y: 32, w: 10, h: 24 },
    sunny: { x: 16, y: 39, w: 10, h: 21 },
    benji: { x: 21, y: 37, w: 11, h: 24 },
    harry: { x: 47, y: 22, w: 45, h: 68 },
  }),
  sunny: Object.freeze({
    bunny: { x: 0, y: 39, w: 10, h: 24 },
    bruno: { x: 10, y: 35, w: 10, h: 27 },
    fiona: { x: 18, y: 35, w: 12, h: 28 },
    sunny: { x: 22, y: 38, w: 24, h: 48 },
    harry: { x: 52, y: 28, w: 40, h: 58 },
  }),
  fiona: Object.freeze({
    bunny: { x: 0, y: 37, w: 10, h: 24 },
    bruno: { x: 9, y: 34, w: 10, h: 27 },
    sunny: { x: 16, y: 38, w: 10, h: 24 },
    benji: { x: 22, y: 36, w: 12, h: 28 },
    fiona: { x: 18, y: 32, w: 23, h: 58 },
    harry: { x: 52, y: 28, w: 40, h: 60 },
  }),
});

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
  rabbitIntro: dialogue("harry", "Wait! What about the rabbit?", "Počkejte! A co ten králík?"),
  rabbitPrompt: prompt("Who is the rabbit?", "Kdo je králík?"),
  bunnyAnswer: dialogue("bunny", "I am Bunny.", "Já jsem Bunny."),
  carrotQuestion: prompt(
    "Do you want to eat the carrots in my garden?",
    "Chceš sníst mrkev z mé zahrádky?",
  ),
  ownCarrots: dialogue("bunny", "No. I have my own carrots.", "Ne. Mám vlastní mrkev."),
  lakeOnly: dialogue("bunny", "I only want to go to the lake.", "Chci jen jít k jezeru."),
  bunnyAccepted: dialogue(
    "harry",
    "Good answer, Bunny. But the gate stays closed.",
    "Dobrá odpověď, Bunny. Ale branka zůstává zavřená.",
  ),
  squirrelIntro: dialogue("harry", "Now, what about the squirrel?", "A teď, co ta veverka?"),
  squirrelPrompt: prompt("Who is the squirrel?", "Kdo je veverka?"),
  sunnyAnswer: dialogue("sunny", "Hello! I am Sunny.", "Ahoj! Já jsem Sunny."),
  nutQuestion: prompt(
    "Do you want to eat the nuts from my tree?",
    "Chceš sníst ořechy z mého stromu?",
  ),
  ownNuts: dialogue("sunny", "No. I have my own nuts.", "Ne. Mám vlastní ořechy."),
  lakeWithFriends: dialogue(
    "sunny",
    "I want to go to the lake with my friends.",
    "Chci jít s kamarády k jezeru.",
  ),
  sunnyAccepted: dialogue(
    "harry",
    "Good answer, Sunny. But I have more questions.",
    "Dobrá odpověď, Sunny. Ale mám další otázky.",
  ),
  foxIntro: dialogue("harry", "And what about the fox?", "A co ta liška?"),
  foxPrompt: prompt("Who is the fox?", "Kdo je liška?"),
  fionaAnswer: dialogue("fiona", "Hi. I am Fiona.", "Ahoj. Já jsem Fiona."),
  chickenQuestion: prompt(
    "Do you want to catch a chicken in my yard?",
    "Chceš chytit slepičku na mém dvorku?",
  ),
  noChickens: dialogue(
    "fiona",
    "No. I do not catch chickens.",
    "Ne. Nechytám slepice.",
  ),
  fionaLakeWithFriends: dialogue(
    "fiona",
    "I want to go to the lake with my friends.",
    "Chci jít s kamarády k jezeru.",
  ),
  fionaAccepted: dialogue(
    "harry",
    "Good answer, Fiona. But I have one more question.",
    "Dobrá odpověď, Fiono. Ale mám ještě jednu otázku.",
  ),
};

const state = {
  stage: STAGES.waitingStart,
  sceneId: "group",
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

function setSceneImage(sceneId) {
  const nextScene = SCENE_IMAGES[sceneId];
  if (!nextScene) return;
  state.sceneId = sceneId;
  if (sceneImage.getAttribute("src") !== nextScene.src) {
    sceneImage.src = nextScene.src;
  }
  sceneImage.alt = nextScene.alt;
  renderHotspots();
}

function primeSceneImages() {
  for (const sceneConfig of Object.values(SCENE_IMAGES)) {
    if (sceneConfig.src === sceneImage.getAttribute("src")) continue;
    const image = new Image();
    image.decoding = "async";
    image.src = sceneConfig.src;
  }
}

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
  if (lang === "en" && characterId === "bunny") {
    for (const preferredName of BUNNY_ENGLISH_VOICE_ORDER) {
      const selectedVoice = matching.find((voice) => voice.name.toLowerCase().includes(preferredName));
      if (selectedVoice) return selectedVoice;
    }
  }
  if (lang === "en" && characterId === "sunny") {
    for (const preferredName of SUNNY_ENGLISH_VOICE_ORDER) {
      const selectedVoice = matching.find((voice) => voice.name.toLowerCase().includes(preferredName));
      if (selectedVoice) return selectedVoice;
    }
  }
  if (lang === "en" && characterId === "fiona") {
    for (const preferredName of FIONA_ENGLISH_VOICE_ORDER) {
      const selectedVoice = matching.find((voice) => voice.name.toLowerCase().includes(preferredName));
      if (selectedVoice) return selectedVoice;
    }
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
      Math.max(4500, textLength * 180),
    );
  });
}

function primeFixedAudio() {
  const sources = [
    ...BENJI_ENGLISH_AUDIO.values(),
    ...BUNNY_ENGLISH_AUDIO.values(),
    ...SUNNY_ENGLISH_AUDIO.values(),
    ...FIONA_ENGLISH_AUDIO.values(),
  ];
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
  if (lang === "en" && ["benji", "bunny", "sunny", "fiona"].includes(characterId)) {
    const fixedAudio = characterId === "benji"
      ? BENJI_ENGLISH_AUDIO.get(text)
      : characterId === "bunny"
        ? BUNNY_ENGLISH_AUDIO.get(text)
        : characterId === "sunny"
          ? SUNNY_ENGLISH_AUDIO.get(text)
          : FIONA_ENGLISH_AUDIO.get(text);
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
    STAGES.chooseBunny,
    STAGES.chooseBunnyYesNo,
    STAGES.chooseSunny,
    STAGES.chooseSunnyYesNo,
    STAGES.chooseFiona,
    STAGES.chooseFionaYesNo,
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
  const canChooseCharacter = [
    STAGES.chooseBenji,
    STAGES.chooseBunny,
    STAGES.chooseSunny,
    STAGES.chooseFiona,
  ].includes(state.stage);
  const targetCharacterId = state.stage === STAGES.chooseBunny
    ? "bunny"
    : state.stage === STAGES.chooseSunny
      ? "sunny"
      : state.stage === STAGES.chooseFiona
        ? "fiona"
        : "benji";
  const sceneHotspots = SCENE_HOTSPOTS[state.sceneId] || SCENE_HOTSPOTS.group;
  for (const [characterId, character] of Object.entries(characters)) {
    const rect = sceneHotspots[characterId];
    if (!rect) continue;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "hotspot";
    button.style.left = `${rect.x}%`;
    button.style.top = `${rect.y}%`;
    button.style.width = `${rect.w}%`;
    button.style.height = `${rect.h}%`;
    button.setAttribute("aria-label", character.label);
    button.disabled = !canChooseCharacter;
    if (canChooseCharacter) {
      button.classList.add("enabled");
      if (characterId === targetCharacterId) button.classList.add("target");
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
  if (![STAGES.chooseBenji, STAGES.chooseBunny, STAGES.chooseSunny, STAGES.chooseFiona].includes(state.stage)) return;
  const choosingBunny = state.stage === STAGES.chooseBunny;
  const choosingSunny = state.stage === STAGES.chooseSunny;
  const choosingFiona = state.stage === STAGES.chooseFiona;
  const targetCharacterId = choosingBunny ? "bunny" : choosingSunny ? "sunny" : choosingFiona ? "fiona" : "benji";
  const question = choosingBunny ? lines.rabbitPrompt : choosingSunny ? lines.squirrelPrompt : choosingFiona ? lines.foxPrompt : lines.mapQuestion;
  const answerStage = choosingBunny ? STAGES.bunnyAnswer : choosingSunny ? STAGES.sunnyAnswer : choosingFiona ? STAGES.fionaAnswer : STAGES.benjiAnswer;
  const chooseStage = choosingBunny ? STAGES.chooseBunny : choosingSunny ? STAGES.chooseSunny : choosingFiona ? STAGES.chooseFiona : STAGES.chooseBenji;
  if (characterId !== targetCharacterId) {
    const flowId = ++state.flowId;
    cancelSpeech();
    setStage(answerStage);
    const wrongLine = { ...lines.notMe, characterId };
    if (!(await playEntry(wrongLine, flowId))) return;
    if (!(await playEntry(question, flowId))) return;
    hideSpeech();
    showTask(question);
    setStage(chooseStage);
    return;
  }

  const flowId = ++state.flowId;
  cancelSpeech();
  hideTask();
  setStage(answerStage);
  const answer = choosingBunny ? lines.bunnyAnswer : choosingSunny ? lines.sunnyAnswer : choosingFiona ? lines.fionaAnswer : lines.mapAnswer;
  const yesNoQuestion = choosingBunny ? lines.carrotQuestion : choosingSunny ? lines.nutQuestion : choosingFiona ? lines.chickenQuestion : lines.sheepQuestion;
  if (!(await playEntry(answer, flowId))) return;
  if (!(await playEntry(yesNoQuestion, flowId))) return;
  hideSpeech();
  showTask(yesNoQuestion);
  answerPanel.classList.remove("hidden");
  setStage(choosingBunny ? STAGES.chooseBunnyYesNo : choosingSunny ? STAGES.chooseSunnyYesNo : choosingFiona ? STAGES.chooseFionaYesNo : STAGES.chooseYesNo);
}

async function chooseYes() {
  if (![STAGES.chooseYesNo, STAGES.chooseBunnyYesNo, STAGES.chooseSunnyYesNo, STAGES.chooseFionaYesNo].includes(state.stage)) return;
  const questioningBunny = state.stage === STAGES.chooseBunnyYesNo;
  const questioningSunny = state.stage === STAGES.chooseSunnyYesNo;
  const questioningFiona = state.stage === STAGES.chooseFionaYesNo;
  const question = questioningBunny ? lines.carrotQuestion : questioningSunny ? lines.nutQuestion : questioningFiona ? lines.chickenQuestion : lines.sheepQuestion;
  const flowId = ++state.flowId;
  cancelSpeech();
  answerPanel.classList.add("hidden");
  hideTask();
  setStage(questioningBunny ? STAGES.wrongBunnyYes : questioningSunny ? STAGES.wrongSunnyYes : questioningFiona ? STAGES.wrongFionaYes : STAGES.wrongYes);
  if (!(await playEntry(lines.listenAgain, flowId))) return;
  if (!(await playEntry(question, flowId))) return;
  hideSpeech();
  showTask(question);
  answerPanel.classList.remove("hidden");
  setStage(questioningBunny ? STAGES.chooseBunnyYesNo : questioningSunny ? STAGES.chooseSunnyYesNo : questioningFiona ? STAGES.chooseFionaYesNo : STAGES.chooseYesNo);
}

async function chooseNo() {
  if (![STAGES.chooseYesNo, STAGES.chooseBunnyYesNo, STAGES.chooseSunnyYesNo, STAGES.chooseFionaYesNo].includes(state.stage)) return;
  const questioningBunny = state.stage === STAGES.chooseBunnyYesNo;
  const questioningSunny = state.stage === STAGES.chooseSunnyYesNo;
  const questioningFiona = state.stage === STAGES.chooseFionaYesNo;
  const flowId = ++state.flowId;
  cancelSpeech();
  answerPanel.classList.add("hidden");
  hideTask();
  setStage(STAGES.finishing);
  if (questioningFiona) {
    for (const entry of [lines.noChickens, lines.fionaLakeWithFriends, lines.fionaAccepted]) {
      if (!(await playEntry(entry, flowId))) return;
    }
    hideSpeech();
    completeBanner.classList.remove("hidden");
    setStage(STAGES.complete);
    return;
  }

  if (questioningSunny) {
    for (const entry of [lines.ownNuts, lines.lakeWithFriends, lines.sunnyAccepted]) {
      if (!(await playEntry(entry, flowId))) return;
    }
    setSceneImage("fiona");
    for (const entry of [lines.foxIntro, lines.foxPrompt]) {
      if (!(await playEntry(entry, flowId))) return;
    }
    hideSpeech();
    showTask(lines.foxPrompt);
    setStage(STAGES.chooseFiona);
    return;
  }

  if (questioningBunny) {
    for (const entry of [lines.ownCarrots, lines.lakeOnly, lines.bunnyAccepted]) {
      if (!(await playEntry(entry, flowId))) return;
    }
    setSceneImage("sunny");
    for (const entry of [lines.squirrelIntro, lines.squirrelPrompt]) {
      if (!(await playEntry(entry, flowId))) return;
    }
    hideSpeech();
    showTask(lines.squirrelPrompt);
    setStage(STAGES.chooseSunny);
    return;
  }

  for (const entry of [lines.noChase, lines.helper, lines.trust]) {
    if (!(await playEntry(entry, flowId))) return;
  }
  setSceneImage("bunny");
  for (const entry of [lines.rabbitIntro, lines.rabbitPrompt]) {
    if (!(await playEntry(entry, flowId))) return;
  }
  hideSpeech();
  showTask(lines.rabbitPrompt);
  setStage(STAGES.chooseBunny);
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
    if (resumeStage === STAGES.chooseBunny) showTask(lines.rabbitPrompt);
    if (resumeStage === STAGES.chooseBunnyYesNo) showTask(lines.carrotQuestion);
    if (resumeStage === STAGES.chooseSunny) showTask(lines.squirrelPrompt);
    if (resumeStage === STAGES.chooseSunnyYesNo) showTask(lines.nutQuestion);
    if (resumeStage === STAGES.chooseFiona) showTask(lines.foxPrompt);
    if (resumeStage === STAGES.chooseFionaYesNo) showTask(lines.chickenQuestion);
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
  primeSceneImages();
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
