/**
 * MMTX prototype: Harry questions Benji, Bunny, Sunny, Fiona and Bruno at the sheep gate.
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
const nextButton = document.getElementById("nextButton");
const completeBanner = document.getElementById("completeBanner");
const audioGate = document.getElementById("audioGate");
const languageButton = document.getElementById("languageButton");
const repeatButton = document.getElementById("repeatButton");
const dictionaryButton = document.getElementById("dictionaryButton");
const dictionaryPanel = document.getElementById("dictionaryPanel");
const dictionaryList = document.getElementById("dictionaryList");

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

const BRUNO_AUDIO_VERSION = "20260814a";
const BRUNO_ENGLISH_AUDIO = new Map([
  ["Hello. I am Bruno.", `audio/english/scene04_bruno_hello_i_am_bruno_en.mp3?v=${BRUNO_AUDIO_VERSION}`],
  ["No. I do not dig under fences.", `audio/english/scene04_bruno_no_i_do_not_dig_under_fences_en.mp3?v=${BRUNO_AUDIO_VERSION}`],
  ["I want to go to the lake with my friends.", `audio/english/scene04_bruno_i_want_to_go_to_the_lake_with_my_friends_en.mp3?v=${BRUNO_AUDIO_VERSION}`],
]);

const DICTIONARY_AUDIO_VERSION = "20260815a";
const VOCABULARY = Object.freeze([
  { en: "come closer", cz: "přijít blíž", emoji: "👣", file: "come_closer" },
  { en: "chase", cz: "honit", emoji: "🐾", file: "chase" },
  { en: "sheep", cz: "ovce", emoji: "🐑", file: "sheep" },
  { en: "little animals", cz: "malá zvířátka", emoji: "🐾", file: "little_animals" },
  { en: "trust", cz: "důvěřovat", emoji: "🤝", file: "trust" },
  { en: "rabbit", cz: "králík", emoji: "🐇", file: "rabbit" },
  { en: "eat", cz: "jíst", emoji: "🍽️", file: "eat" },
  { en: "own", cz: "vlastní", emoji: "🎒", file: "own" },
  { en: "gate", cz: "branka", emoji: "🚪", file: "gate" },
  { en: "closed", cz: "zavřený", emoji: "🔒", file: "closed" },
  { en: "squirrel", cz: "veverka", emoji: "🐿️", file: "squirrel" },
  { en: "question", cz: "otázka", emoji: "❓", file: "question" },
  { en: "answer", cz: "odpověď", emoji: "💬", file: "answer" },
  { en: "fox", cz: "liška", emoji: "🦊", file: "fox" },
  { en: "catch", cz: "chytit", emoji: "🙌", file: "catch" },
  { en: "chicken", cz: "slepice", emoji: "🐔", file: "chicken" },
  { en: "yard", cz: "dvorek", emoji: "🏡", file: "yard" },
  { en: "badger", cz: "jezevec", emoji: "🦡", file: "badger" },
  { en: "dig", cz: "hrabat", emoji: "🕳️", file: "dig" },
  { en: "under", cz: "pod", emoji: "⬇️", file: "under" },
  { en: "fence", cz: "plot", emoji: "🪵", file: "fence" },
  { en: "believe", cz: "věřit", emoji: "💚", file: "believe" },
].map((item) => Object.freeze({
  ...item,
  audio: `audio/english/scene04_vocab_${item.file}_en.mp3?v=${DICTIONARY_AUDIO_VERSION}`,
})));

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

const BRUNO_ENGLISH_VOICE_ORDER = [
  "daniel",
  "onyx",
  "aaron",
  "roger",
  "guy",
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
  chooseBruno: "chooseBruno",
  brunoAnswer: "brunoAnswer",
  chooseBrunoYesNo: "chooseBrunoYesNo",
  wrongBrunoYes: "wrongBrunoYes",
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
  bruno: {
    src: "harry_interrogation_bruno_02.png",
    alt: "Bruno mluví s ovčáckým psem Harrym u zavřené ohrady s pěti ovcemi a Benji stojí mezi přáteli",
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
  bruno: Object.freeze({
    bunny: { x: 0, y: 39, w: 10, h: 25 },
    fiona: { x: 9, y: 37, w: 10, h: 28 },
    sunny: { x: 17, y: 43, w: 9, h: 23 },
    benji: { x: 22, y: 38, w: 10, h: 31 },
    bruno: { x: 27, y: 28, w: 20, h: 55 },
    harry: { x: 59, y: 28, w: 33, h: 58 },
  }),
});

function dialogue(characterId, textEn, textCz) {
  return { kind: "dialogue", characterId, textEn, textCz };
}

function prompt(textEn, textCz) {
  return { kind: "prompt", characterId: "harry", textEn, textCz };
}

const lines = {
  introduction: dialogue(
    "harry",
    "My name is Harry, and I guard this gate!",
    "Jmenuji se Harry a hlídám tuto branku!",
  ),
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
  badgerIntro: dialogue("harry", "One more! What about the badger?", "Ještě jeden! A co ten jezevec?"),
  badgerPrompt: prompt("Who is the badger?", "Kdo je jezevec?"),
  brunoAnswer: dialogue("bruno", "Hello. I am Bruno.", "Ahoj. Já jsem Bruno."),
  fenceQuestion: prompt(
    "Do you want to dig under my fence?",
    "Chceš se podhrabat pod mým plotem?",
  ),
  noDigging: dialogue(
    "bruno",
    "No. I do not dig under fences.",
    "Ne. Nepodhrabávám se pod ploty.",
  ),
  brunoLakeWithFriends: dialogue(
    "bruno",
    "I want to go to the lake with my friends.",
    "Chci jít s kamarády k jezeru.",
  ),
  brunoAccepted: dialogue(
    "harry",
    "Good answer, Bruno. I believe you.",
    "Dobrá odpověď, Bruno. Věřím ti.",
  ),
  gateOpened: dialogue(
    "harry",
    "OK, now you can continue. The gate is open for you, friends!",
    "Dobře, teď můžete pokračovat. Branka je pro vás otevřená, kamarádi!",
  ),
};

const state = {
  stage: STAGES.waitingStart,
  sceneId: "group",
  languageMode: loadLanguageMode(),
  lastRepeatable: null,
  flowId: 0,
  currentEntry: null,
  entryPlaybackId: 0,
  isSpeakingEntry: false,
  isRepeating: false,
};

let voices = [];
let speechTimeout = 0;
let speechResolve = null;
let activeAudio = null;
let audioTimeout = 0;
let audioResolve = null;
let nextResolve = null;
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
  if (lang === "en" && characterId === "dictionary") {
    for (const preferredName of FIONA_ENGLISH_VOICE_ORDER) {
      const selectedVoice = matching.find((voice) => voice.name.toLowerCase().includes(preferredName));
      if (selectedVoice) return selectedVoice;
    }
  }
  if (lang === "en" && characterId === "bruno") {
    for (const preferredName of BRUNO_ENGLISH_VOICE_ORDER) {
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
    ...BRUNO_ENGLISH_AUDIO.values(),
    ...VOCABULARY.map((item) => item.audio),
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
  if (lang === "en" && ["benji", "bunny", "sunny", "fiona", "bruno"].includes(characterId)) {
    const fixedAudio = characterId === "benji"
      ? BENJI_ENGLISH_AUDIO.get(text)
      : characterId === "bunny"
        ? BUNNY_ENGLISH_AUDIO.get(text)
        : characterId === "sunny"
          ? SUNNY_ENGLISH_AUDIO.get(text)
          : characterId === "fiona"
            ? FIONA_ENGLISH_AUDIO.get(text)
            : BRUNO_ENGLISH_AUDIO.get(text);
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
  updateRepeatAvailability();
}

async function playEntry(entry, flowId, { remember = true } = {}) {
  if (flowId !== state.flowId) return false;
  if (remember) {
    state.lastRepeatable = entry;
  }
  const playbackId = ++state.entryPlaybackId;
  state.isSpeakingEntry = true;
  showSpeech(entry);
  updateRepeatAvailability();
  try {
    await speakText(entry.textEn, "en", entry.characterId);
    if (flowId !== state.flowId) return false;
    if (isBilingual()) await speakText(entry.textCz, "cs", entry.characterId);
    return flowId === state.flowId;
  } finally {
    if (playbackId === state.entryPlaybackId) {
      state.isSpeakingEntry = false;
      updateRepeatAvailability();
    }
  }
}

function waitForNext(flowId) {
  if (flowId !== state.flowId) return Promise.resolve(false);
  nextButton.disabled = false;
  nextButton.classList.remove("hidden");
  return new Promise((resolve) => {
    nextResolve = () => {
      nextResolve = null;
      nextButton.disabled = true;
      nextButton.classList.add("hidden");
      resolve(flowId === state.flowId);
    };
  });
}

function advanceDialogue() {
  if (!nextResolve || nextButton.disabled) return;
  const resolve = nextResolve;
  resolve();
}

async function playSequence(entries, flowId) {
  for (let index = 0; index < entries.length; index += 1) {
    if (!(await playEntry(entries[index], flowId))) return false;
    const hasAnotherEntry = index < entries.length - 1;
    if (hasAnotherEntry && !(await waitForNext(flowId))) return false;
  }
  return true;
}

async function advanceToScene(sceneId, entries, flowId) {
  if (!(await waitForNext(flowId))) return false;
  setSceneImage(sceneId);
  return playSequence(entries, flowId);
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
    STAGES.chooseBruno,
    STAGES.chooseBrunoYesNo,
    STAGES.complete,
  ]);
  const visibleEntry = state.currentEntry;
  const fallbackEntry = repeatableStages.has(state.stage) ? state.lastRepeatable : null;
  repeatButton.disabled = (
    state.isSpeakingEntry
    || state.isRepeating
    || !(visibleEntry || fallbackEntry)
  );
}

function closeDictionary() {
  dictionaryPanel.classList.add("hidden");
  dictionaryButton.classList.remove("active-panel");
  dictionaryButton.setAttribute("aria-expanded", "false");
}

function updateDictionaryAvailability() {
  const isComplete = state.stage === STAGES.complete;
  dictionaryButton.disabled = !isComplete;
  dictionaryButton.classList.toggle("hidden", !isComplete);
  if (!isComplete) closeDictionary();
}

function updateDictionaryLanguageUi() {
  dictionaryList.querySelectorAll(".dictionary-translation").forEach((translation) => {
    translation.classList.toggle("hidden", !isBilingual());
  });
}

function renderDictionary() {
  dictionaryList.replaceChildren();
  VOCABULARY.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "dictionary-item";
    button.setAttribute("aria-label", `${item.en} — ${item.cz}`);

    const emoji = document.createElement("span");
    emoji.className = "dictionary-emoji";
    emoji.setAttribute("aria-hidden", "true");
    emoji.textContent = item.emoji;

    const word = document.createElement("span");
    word.className = "dictionary-word";
    word.textContent = item.en;

    const translation = document.createElement("span");
    translation.className = "dictionary-translation";
    translation.textContent = item.cz;

    button.append(emoji, word, translation);
    button.addEventListener("click", () => playVocabularyItem(item));
    dictionaryList.appendChild(button);
  });
  updateDictionaryLanguageUi();
}

async function playVocabularyItem(item) {
  if (state.stage !== STAGES.complete) return;
  const flowId = ++state.flowId;
  cancelSpeech();
  const played = await playFixedAudio(item.audio, item.en.length);
  if (flowId !== state.flowId) return;
  if (!played) await speakText(item.en, "en", "dictionary");
  if (flowId !== state.flowId) return;
  if (isBilingual()) await speakText(item.cz, "cs", "dictionary");
}

function toggleDictionary() {
  if (state.stage !== STAGES.complete || dictionaryButton.disabled) return;
  const willOpen = dictionaryPanel.classList.contains("hidden");
  dictionaryPanel.classList.toggle("hidden", !willOpen);
  dictionaryButton.classList.toggle("active-panel", willOpen);
  dictionaryButton.setAttribute("aria-expanded", willOpen ? "true" : "false");
}

function setStage(stage) {
  state.stage = stage;
  renderHotspots();
  updateRepeatAvailability();
  updateDictionaryAvailability();
}

function renderHotspots() {
  overlay.replaceChildren();
  const canChooseCharacter = [
    STAGES.chooseBenji,
    STAGES.chooseBunny,
    STAGES.chooseSunny,
    STAGES.chooseFiona,
    STAGES.chooseBruno,
  ].includes(state.stage);
  const targetCharacterId = state.stage === STAGES.chooseBunny
    ? "bunny"
    : state.stage === STAGES.chooseSunny
      ? "sunny"
      : state.stage === STAGES.chooseFiona
        ? "fiona"
        : state.stage === STAGES.chooseBruno
          ? "bruno"
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
  if (!(await playSequence([
    lines.introduction,
    lines.stop,
    lines.friendly,
    lines.strangers,
    lines.mapQuestion,
  ], flowId))) return;
  hideSpeech();
  showTask(lines.mapQuestion);
  setStage(STAGES.chooseBenji);
}

async function chooseCharacter(characterId) {
  if (![STAGES.chooseBenji, STAGES.chooseBunny, STAGES.chooseSunny, STAGES.chooseFiona, STAGES.chooseBruno].includes(state.stage)) return;
  const choosingBunny = state.stage === STAGES.chooseBunny;
  const choosingSunny = state.stage === STAGES.chooseSunny;
  const choosingFiona = state.stage === STAGES.chooseFiona;
  const choosingBruno = state.stage === STAGES.chooseBruno;
  const targetCharacterId = choosingBunny ? "bunny" : choosingSunny ? "sunny" : choosingFiona ? "fiona" : choosingBruno ? "bruno" : "benji";
  const question = choosingBunny ? lines.rabbitPrompt : choosingSunny ? lines.squirrelPrompt : choosingFiona ? lines.foxPrompt : choosingBruno ? lines.badgerPrompt : lines.mapQuestion;
  const answerStage = choosingBunny ? STAGES.bunnyAnswer : choosingSunny ? STAGES.sunnyAnswer : choosingFiona ? STAGES.fionaAnswer : choosingBruno ? STAGES.brunoAnswer : STAGES.benjiAnswer;
  const chooseStage = choosingBunny ? STAGES.chooseBunny : choosingSunny ? STAGES.chooseSunny : choosingFiona ? STAGES.chooseFiona : choosingBruno ? STAGES.chooseBruno : STAGES.chooseBenji;
  if (characterId !== targetCharacterId) {
    const flowId = ++state.flowId;
    cancelSpeech();
    setStage(answerStage);
    const wrongLine = { ...lines.notMe, characterId };
    if (!(await playSequence([wrongLine, question], flowId))) return;
    hideSpeech();
    showTask(question);
    setStage(chooseStage);
    return;
  }

  const flowId = ++state.flowId;
  cancelSpeech();
  hideTask();
  setStage(answerStage);
  const answer = choosingBunny ? lines.bunnyAnswer : choosingSunny ? lines.sunnyAnswer : choosingFiona ? lines.fionaAnswer : choosingBruno ? lines.brunoAnswer : lines.mapAnswer;
  const yesNoQuestion = choosingBunny ? lines.carrotQuestion : choosingSunny ? lines.nutQuestion : choosingFiona ? lines.chickenQuestion : choosingBruno ? lines.fenceQuestion : lines.sheepQuestion;
  if (!(await playSequence([answer, yesNoQuestion], flowId))) return;
  hideSpeech();
  showTask(yesNoQuestion);
  answerPanel.classList.remove("hidden");
  setStage(choosingBunny ? STAGES.chooseBunnyYesNo : choosingSunny ? STAGES.chooseSunnyYesNo : choosingFiona ? STAGES.chooseFionaYesNo : choosingBruno ? STAGES.chooseBrunoYesNo : STAGES.chooseYesNo);
}

async function chooseYes() {
  if (![STAGES.chooseYesNo, STAGES.chooseBunnyYesNo, STAGES.chooseSunnyYesNo, STAGES.chooseFionaYesNo, STAGES.chooseBrunoYesNo].includes(state.stage)) return;
  const questioningBunny = state.stage === STAGES.chooseBunnyYesNo;
  const questioningSunny = state.stage === STAGES.chooseSunnyYesNo;
  const questioningFiona = state.stage === STAGES.chooseFionaYesNo;
  const questioningBruno = state.stage === STAGES.chooseBrunoYesNo;
  const question = questioningBunny ? lines.carrotQuestion : questioningSunny ? lines.nutQuestion : questioningFiona ? lines.chickenQuestion : questioningBruno ? lines.fenceQuestion : lines.sheepQuestion;
  const flowId = ++state.flowId;
  cancelSpeech();
  answerPanel.classList.add("hidden");
  hideTask();
  setStage(questioningBunny ? STAGES.wrongBunnyYes : questioningSunny ? STAGES.wrongSunnyYes : questioningFiona ? STAGES.wrongFionaYes : questioningBruno ? STAGES.wrongBrunoYes : STAGES.wrongYes);
  if (!(await playSequence([lines.listenAgain, question], flowId))) return;
  hideSpeech();
  showTask(question);
  answerPanel.classList.remove("hidden");
  setStage(questioningBunny ? STAGES.chooseBunnyYesNo : questioningSunny ? STAGES.chooseSunnyYesNo : questioningFiona ? STAGES.chooseFionaYesNo : questioningBruno ? STAGES.chooseBrunoYesNo : STAGES.chooseYesNo);
}

async function chooseNo() {
  if (![STAGES.chooseYesNo, STAGES.chooseBunnyYesNo, STAGES.chooseSunnyYesNo, STAGES.chooseFionaYesNo, STAGES.chooseBrunoYesNo].includes(state.stage)) return;
  const questioningBunny = state.stage === STAGES.chooseBunnyYesNo;
  const questioningSunny = state.stage === STAGES.chooseSunnyYesNo;
  const questioningFiona = state.stage === STAGES.chooseFionaYesNo;
  const questioningBruno = state.stage === STAGES.chooseBrunoYesNo;
  const flowId = ++state.flowId;
  cancelSpeech();
  answerPanel.classList.add("hidden");
  hideTask();
  setStage(STAGES.finishing);
  if (questioningBruno) {
    if (!(await playSequence([
      lines.noDigging,
      lines.brunoLakeWithFriends,
      lines.brunoAccepted,
      lines.gateOpened,
    ], flowId))) return;
    hideSpeech();
    completeBanner.classList.remove("hidden");
    setStage(STAGES.complete);
    return;
  }

  if (questioningFiona) {
    if (!(await playSequence([
      lines.noChickens,
      lines.fionaLakeWithFriends,
      lines.fionaAccepted,
    ], flowId))) return;
    if (!(await advanceToScene("bruno", [lines.badgerIntro, lines.badgerPrompt], flowId))) return;
    hideSpeech();
    showTask(lines.badgerPrompt);
    setStage(STAGES.chooseBruno);
    return;
  }

  if (questioningSunny) {
    if (!(await playSequence([
      lines.ownNuts,
      lines.lakeWithFriends,
      lines.sunnyAccepted,
    ], flowId))) return;
    if (!(await advanceToScene("fiona", [lines.foxIntro, lines.foxPrompt], flowId))) return;
    hideSpeech();
    showTask(lines.foxPrompt);
    setStage(STAGES.chooseFiona);
    return;
  }

  if (questioningBunny) {
    if (!(await playSequence([
      lines.ownCarrots,
      lines.lakeOnly,
      lines.bunnyAccepted,
    ], flowId))) return;
    if (!(await advanceToScene("sunny", [lines.squirrelIntro, lines.squirrelPrompt], flowId))) return;
    hideSpeech();
    showTask(lines.squirrelPrompt);
    setStage(STAGES.chooseSunny);
    return;
  }

  if (!(await playSequence([lines.noChase, lines.helper, lines.trust], flowId))) return;
  if (!(await advanceToScene("bunny", [lines.rabbitIntro, lines.rabbitPrompt], flowId))) return;
  hideSpeech();
  showTask(lines.rabbitPrompt);
  setStage(STAGES.chooseBunny);
}

async function repeatLast() {
  const entry = state.currentEntry || state.lastRepeatable;
  if (!entry || repeatButton.disabled || state.isSpeakingEntry || state.isRepeating) return;
  const resumeStage = state.stage;
  const resumeEntry = state.currentEntry;
  const flowId = state.flowId;
  const nextWasAvailable = Boolean(nextResolve && !nextButton.disabled);
  cancelSpeech();
  closeDictionary();
  state.isRepeating = true;
  if (nextWasAvailable) nextButton.disabled = true;
  updateRepeatAvailability();
  try {
    await playEntry(entry, flowId, { remember: false });
    if (flowId !== state.flowId) return;
    if (!resumeEntry) {
      hideSpeech();
      if (resumeStage === STAGES.chooseBenji) showTask(lines.mapQuestion);
      if (resumeStage === STAGES.chooseYesNo) showTask(lines.sheepQuestion);
      if (resumeStage === STAGES.chooseBunny) showTask(lines.rabbitPrompt);
      if (resumeStage === STAGES.chooseBunnyYesNo) showTask(lines.carrotQuestion);
      if (resumeStage === STAGES.chooseSunny) showTask(lines.squirrelPrompt);
      if (resumeStage === STAGES.chooseSunnyYesNo) showTask(lines.nutQuestion);
      if (resumeStage === STAGES.chooseFiona) showTask(lines.foxPrompt);
      if (resumeStage === STAGES.chooseFionaYesNo) showTask(lines.chickenQuestion);
      if (resumeStage === STAGES.chooseBruno) showTask(lines.badgerPrompt);
      if (resumeStage === STAGES.chooseBrunoYesNo) showTask(lines.fenceQuestion);
    }
  } finally {
    state.isRepeating = false;
    if (nextWasAvailable && nextResolve && flowId === state.flowId) {
      nextButton.disabled = false;
    }
    updateRepeatAvailability();
  }
}

function toggleLanguage() {
  state.languageMode = isBilingual() ? LANGUAGE_MODES.english : LANGUAGE_MODES.bilingual;
  saveLanguageMode();
  updateLanguageUi();
  updateDictionaryLanguageUi();
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
nextButton.addEventListener("click", advanceDialogue);
dictionaryButton.addEventListener("click", toggleDictionary);
yesButton.addEventListener("click", chooseYes);
noButton.addEventListener("click", chooseNo);
window.speechSynthesis?.addEventListener?.("voiceschanged", loadVoices);

updateLanguageUi();
renderDictionary();
updateDictionaryAvailability();
renderHotspots();
