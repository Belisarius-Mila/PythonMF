/**
 * Scene 3 - Journey to the Lake
 *
 * Standalone MMTX Forest Journey scene.
 * Images: journey_lake_3a.png ... journey_lake_3f.png (1672 x 941).
 */

const sceneImage = document.getElementById("sceneImage");
const overlay = document.getElementById("overlay");
const speechBubble = document.getElementById("speechBubble");
const bubbleEmoji = document.getElementById("bubbleEmoji");
const bubbleText = document.getElementById("bubbleText");
const bubbleTranslation = document.getElementById("bubbleTranslation");
const taskPrompt = document.getElementById("taskPrompt");
const taskEmoji = document.getElementById("taskEmoji");
const taskPromptText = document.getElementById("taskPromptText");
const taskPromptTranslation = document.getElementById("taskPromptTranslation");
const mapFragment = document.getElementById("mapFragment");
const scene = document.getElementById("scene");
const audioGate = document.getElementById("audioGate");
const backButton = document.getElementById("backButton");
const repeatButton = document.getElementById("repeatButton");
const dictionaryButton = document.getElementById("dictionaryButton");
const dictionaryPanel = document.getElementById("dictionaryPanel");
const dictionaryList = document.getElementById("dictionaryList");
const helpButton = document.getElementById("helpButton");
const completeBanner = document.getElementById("completeBanner");

const SCENE_STATES = {
  waitingAudio: "waitingAudio",
  playing: "playing",
  promptingTap: "promptingTap",
  waitingTap: "waitingTap",
  resolvingTap: "resolvingTap",
  complete: "complete",
};

const sharedVoices = {
  benji: "andrew|evan|alex|samantha|ava|fable",
  bunny: "ana|samantha|ava|victoria|karen|echo",
  bruno: "daniel|onyx|aaron|roger|guy",
  fiona: "shimmer|samantha|ava|victoria|karen",
  sunny: "nova|samantha|ava|victoria|karen|junior",
  crow: "onyx|roger|daniel|guy",
  horse: "daniel|roger|guy|alex|aaron",
};

const edgeAudioCharacters = new Set(["benji", "bunny", "bruno", "crow", "fiona", "horse", "sunny", "all"]);
const sceneAssetVersion = "20260701fix8";
const sceneAudioVersion = "20260701voice5";

const phases = {
  "3a": {
    image: "journey_lake_3a.png",
    hotspots: {
      benji: { label: "Benji", emoji: "🐶", color: "#5f8bff", rect: { x: 18, y: 38, w: 16, h: 43 }, bubble: { x: 18, y: 27 } },
      bunny: { label: "Bunny", emoji: "🐰", color: "#ff9ec8", rect: { x: 33, y: 39, w: 12, h: 38 }, bubble: { x: 33, y: 28 } },
      bruno: { label: "Bruno", emoji: "🦡", color: "#b8895f", rect: { x: 44, y: 31, w: 14, h: 46 }, bubble: { x: 45, y: 21 } },
      fiona: { label: "Fiona", emoji: "🦊", color: "#d4a574", rect: { x: 58, y: 35, w: 14, h: 45 }, bubble: { x: 58, y: 24 } },
      sunny: { label: "Sunny", emoji: "🐿️", color: "#f4c542", rect: { x: 72, y: 42, w: 16, h: 43 }, bubble: { x: 72, y: 31 } },
    },
  },
  "3b": {
    image: "journey_lake_3b.png",
    hotspots: {
      benji: { label: "Benji", emoji: "🐶", color: "#5f8bff", rect: { x: 5, y: 40, w: 20, h: 45 }, bubble: { x: 7, y: 29 } },
      bunny: { label: "Bunny", emoji: "🐰", color: "#ff9ec8", rect: { x: 28, y: 43, w: 13, h: 38 }, bubble: { x: 29, y: 32 } },
      bruno: { label: "Bruno", emoji: "🦡", color: "#b8895f", rect: { x: 43, y: 34, w: 14, h: 45 }, bubble: { x: 43, y: 24 } },
      fiona: { label: "Fiona", emoji: "🦊", color: "#d4a574", rect: { x: 59, y: 36, w: 17, h: 46 }, bubble: { x: 60, y: 25 } },
      sunny: { label: "Sunny", emoji: "🐿️", color: "#f4c542", rect: { x: 80, y: 43, w: 17, h: 44 }, bubble: { x: 78, y: 31 } },
      crow: { label: "Crow", emoji: "🐦", color: "#444444", rect: { x: 20, y: 6, w: 12, h: 13 }, bubble: { x: 17, y: 15 } },
      leftPath: { label: "Left path", emoji: "⬅️", color: "#ffd86b", rect: { x: 18, y: 24, w: 20, h: 16 }, bubble: { x: 16, y: 28 } },
      rightPath: { label: "Right path", emoji: "➡️", color: "#ffd86b", rect: { x: 72, y: 28, w: 28, h: 48 }, bubble: { x: 72, y: 35 } },
    },
  },
  "3c": {
    image: "journey_lake_3c.png",
    hotspots: {
      benji: { label: "Benji", emoji: "🐶", color: "#5f8bff", rect: { x: 4, y: 41, w: 15, h: 44 }, bubble: { x: 6, y: 30 } },
      bunny: { label: "Bunny", emoji: "🐰", color: "#ff9ec8", rect: { x: 18, y: 44, w: 11, h: 37 }, bubble: { x: 18, y: 33 } },
      bruno: { label: "Bruno", emoji: "🦡", color: "#b8895f", rect: { x: 29, y: 37, w: 13, h: 44 }, bubble: { x: 30, y: 26 } },
      fiona: { label: "Fiona", emoji: "🦊", color: "#d4a574", rect: { x: 41, y: 38, w: 13, h: 43 }, bubble: { x: 40, y: 27 } },
      sunny: { label: "Sunny", emoji: "🐿️", color: "#f4c542", rect: { x: 49, y: 49, w: 12, h: 36 }, bubble: { x: 49, y: 37 } },
      horse: { label: "Horse", emoji: "🐴", color: "#9c6a3d", rect: { x: 66, y: 19, w: 19, h: 57 }, bubble: { x: 62, y: 17 } },
    },
  },
  "3d": {
    image: "journey_lake_3d.png",
    hotspots: {
      bunny: { label: "Bunny", emoji: "🐰", color: "#ff9ec8", rect: { x: 0, y: 41, w: 13, h: 45 }, bubble: { x: 3, y: 31 } },
      bruno: { label: "Bruno", emoji: "🦡", color: "#b8895f", rect: { x: 16, y: 35, w: 15, h: 48 }, bubble: { x: 17, y: 25 } },
      fiona: { label: "Fiona", emoji: "🦊", color: "#d4a574", rect: { x: 30, y: 36, w: 14, h: 46 }, bubble: { x: 30, y: 25 } },
      sunny: { label: "Sunny", emoji: "🐿️", color: "#f4c542", rect: { x: 41, y: 45, w: 13, h: 40 }, bubble: { x: 40, y: 34 } },
      benji: { label: "Benji", emoji: "🐶", color: "#5f8bff", rect: { x: 49, y: 45, w: 14, h: 42 }, bubble: { x: 49, y: 34 } },
      horse: { label: "Horse", emoji: "🐴", color: "#9c6a3d", rect: { x: 70, y: 8, w: 28, h: 82 }, bubble: { x: 66, y: 17 } },
      farmDoor: { label: "Farm door", emoji: "🚪", color: "#ffd86b", rect: { x: 82, y: 13, w: 13, h: 29 }, bubble: { x: 75, y: 22 } },
    },
  },
  "3e": {
    image: "journey_lake_3e.png",
    hotspots: {
      benji: { label: "Benji", emoji: "🐶", color: "#5f8bff", rect: { x: 4, y: 37, w: 16, h: 44 }, bubble: { x: 6, y: 26 } },
      bunny: { label: "Bunny", emoji: "🐰", color: "#ff9ec8", rect: { x: 24, y: 34, w: 12, h: 43 }, bubble: { x: 24, y: 23 } },
      pump: { label: "Pump", emoji: "💧", color: "#78b7df", rect: { x: 38, y: 22, w: 15, h: 45 }, bubble: { x: 37, y: 15 } },
      bruno: { label: "Bruno", emoji: "🦡", color: "#b8895f", rect: { x: 52, y: 30, w: 14, h: 48 }, bubble: { x: 52, y: 19 } },
      fiona: { label: "Fiona", emoji: "🦊", color: "#d4a574", rect: { x: 68, y: 33, w: 16, h: 48 }, bubble: { x: 54, y: 66 } },
      sunny: { label: "Sunny", emoji: "🐿️", color: "#f4c542", rect: { x: 87, y: 39, w: 13, h: 43 }, bubble: { x: 78, y: 28 } },
    },
  },
  "3f": {
    image: "journey_lake_3f.png",
    hotspots: {
      benji: { label: "Benji", emoji: "🐶", color: "#5f8bff", rect: { x: 4, y: 43, w: 16, h: 45 }, bubble: { x: 6, y: 32 } },
      bunny: { label: "Bunny", emoji: "🐰", color: "#ff9ec8", rect: { x: 26, y: 39, w: 13, h: 43 }, bubble: { x: 25, y: 28 } },
      pump: { label: "Pump", emoji: "💧", color: "#78b7df", rect: { x: 39, y: 22, w: 20, h: 55 }, bubble: { x: 39, y: 15 } },
      sunny: { label: "Sunny", emoji: "🐿️", color: "#f4c542", rect: { x: 45, y: 4, w: 19, h: 34 }, bubble: { x: 43, y: 18 } },
      bruno: { label: "Bruno", emoji: "🦡", color: "#b8895f", rect: { x: 55, y: 25, w: 17, h: 56 }, bubble: { x: 56, y: 18 } },
      fiona: { label: "Fiona", emoji: "🦊", color: "#d4a574", rect: { x: 75, y: 37, w: 18, h: 48 }, bubble: { x: 72, y: 26 } },
      all: { label: "All", emoji: "🎉", color: "#7fd49a", rect: { x: 4, y: 4, w: 92, h: 86 }, bubble: { x: 43, y: 8 } },
    },
  },
};

const scene03Config = {
  placeholderImage: "scene_placeholder.svg",
  audioVolume: 0.78,
  phase: "3a",
  mainHelp: "Poslouchej anglické věty. Když se objeví žlutá nápověda, klepni na havrana, cestu nebo postavu.",
  vocabulary: [
    { en: "look", cz: "podívej, dívat se", emoji: "👀" },
    { en: "left", cz: "vlevo", emoji: "⬅️" },
    { en: "right", cz: "vpravo", emoji: "➡️" },
    { en: "way", cz: "cesta", emoji: "🛤️" },
    { en: "path", cz: "cesta", emoji: "🛤️" },
    { en: "crow", cz: "havran", emoji: "🐦" },
    { en: "bad", cz: "špatný", emoji: "👎" },
    { en: "deep", cz: "hluboký", emoji: "🏞️" },
    { en: "valley", cz: "údolí", emoji: "🏞️" },
    { en: "maybe", cz: "možná", emoji: "🤔" },
    { en: "bears", cz: "medvědi", emoji: "🐻" },
    { en: "but", cz: "ale", emoji: "↔️" },
    { en: "horse", cz: "kůň", emoji: "🐴" },
    { en: "scared", cz: "vystrašený", emoji: "😧" },
    { en: "me too", cz: "já také", emoji: "🙋" },
    { en: "friendly", cz: "přátelský", emoji: "🙂" },
    { en: "careful", cz: "opatrný, opatrně", emoji: "⚠️" },
    { en: "dog", cz: "pes", emoji: "🐕" },
    { en: "live", cz: "žít, bydlet", emoji: "🏠" },
    { en: "warning", cz: "varování", emoji: "⚠️" },
    { en: "farm", cz: "farma", emoji: "🚜" },
    { en: "door", cz: "dveře", emoji: "🚪" },
    { en: "stranger", cz: "cizinec", emoji: "🧍" },
    { en: "come", cz: "jít, přijít", emoji: "👣" },
    { en: "drink", cz: "pít", emoji: "🥤" },
    { en: "water", cz: "voda", emoji: "💧" },
    { en: "pump", cz: "pumpa", emoji: "💧" },
    { en: "get", cz: "dostat", emoji: "🤲" },
    { en: "bucket", cz: "vědro, kbelík", emoji: "🪣" },
    { en: "empty", cz: "prázdný", emoji: "⭕" },
    { en: "I don't know", cz: "nevím", emoji: "🤷" },
    { en: "forest", cz: "les", emoji: "🌲" },
    { en: "handle", cz: "páka", emoji: "↕️" },
    { en: "jump", cz: "skočit", emoji: "⬆️" },
    { en: "push", cz: "tlačit", emoji: "🤲" },
  ],
  steps: [
    { type: "phase", phase: "3a" },
    line("benji", "Look! Two paths.", "Podívej! Dvě cesty.", "🛤️"),
    line("bunny", "This way!", "Tudy!", "⬅️"),
    line("bruno", "No! This way!", "Ne! Tudy!", "➡️"),
    line("fiona", "Wait, wait...", "Počkejte, počkejte...", "✋"),
    { type: "phase", phase: "3b" },
    tap({
      targetId: "crow",
      promptEmoji: "🐦",
      promptEn: "Tap the crow.",
      promptCz: "Klepni na havrana.",
      wrongHintEn: "Try the crow.",
      response: lineData("crow", "Caw! Go left!", "Krá krá! Jděte vlevo!", "🐦"),
    }),
    line("crow", "Left is good. Right is bad.", "Vlevo je to dobré. Vpravo je to špatné.", "⬅️"),
    line("sunny", "Why is it bad?", "Proč je to špatné?", "❓"),
    line("crow", "It is a deep valley.", "Je tam hluboké údolí.", "🏞️"),
    line("crow", "Maybe... bears!", "Možná... medvědi!", "🐻"),
    line("bunny", "Bears?! No, thank you!", "Medvědi?! Ne, děkuji!", "😧"),
    line("fiona", "Okay. Left it is.", "Dobře. Tak vlevo.", "✅"),
    line("benji", "Thank you, crow!", "Děkujeme, havrane!", "🙏"),
    line("crow", "Caw! Bye bye!", "Krá krá! Pá pá!", "👋"),
    line("all", "Let's go left!", "Pojďme vlevo!", "⬅️"),
    tap({
      targetId: "leftPath",
      acceptIds: ["leftPath"],
      promptEmoji: "⬅️",
      promptEn: "Tap the left path.",
      promptCz: "Klepni na levou cestu.",
      wrongResponses: {
        rightPath: lineData("crow", "Caw! No, no. Go left!", "Krá krá! Ne, ne. Jděte vlevo!", "⬅️"),
      },
      wrongHintEn: "Try left.",
    }),
    { type: "phase", phase: "3c" },
    line("sunny", "A horse! A big horse!", "Kůň! Velký kůň!", "🐴"),
    line("bunny", "I am scared.", "Bojím se.", "😧"),
    line("fiona", "Me too!", "Já taky!", "😧"),
    tap({
      targetId: "benji",
      promptEmoji: "🐶",
      promptEn: "Tap Benji.",
      promptCz: "Klepni na Benjiho.",
      wrongHintEn: "Benji is brave.",
      response: lineData("benji", "I am not scared. I will go.", "Já se nebojím. Já půjdu.", "🐶"),
    }),
    { type: "phase", phase: "3d" },
    line("horse", "Hello! Don't be scared.", "Ahoj! Nebojte se.", "🐴"),
    line("horse", "I am friendly.", "Jsem přátelský.", "🙂"),
    line("benji", "Hello! I am Benji.", "Ahoj! Já jsem Benji.", "🐶"),
    line("horse", "Careful! A dog lives there.", "Opatrně! Bydlí tam pes.", "⚠️"),
    line("horse", "He is not friendly with strangers.", "Není přátelský k cizím.", "🐕"),
    line("benji", "Thank you for the warning.", "Děkuji za varování.", "🙏"),
    line("horse", "Come! Drink some water.", "Pojďte! Napijte se vody.", "💧"),
    tap({
      targetId: "farmDoor",
      promptEmoji: "🚪",
      promptEn: "Tap the farm door.",
      promptCz: "Klepni na dveře statku.",
      wrongHintEn: "Try the door.",
    }),
    { type: "phase", phase: "3e" },
    line("fiona", "Look, a pump! But the bucket is empty.", "Podívej, pumpa! Ale vědro je prázdné.", "💧"),
    line("bunny", "How do we get water?", "Jak dostaneme vodu?", "❓"),
    tap({
      targetId: "fiona",
      promptEmoji: "❓",
      promptEn: "Who knows how to get water?",
      promptCz: "Klikni na některého kamaráda, aby řekl, zda ví, jak dostat vodu.",
      hideTargetHighlight: true,
      wrongResponses: {
        bunny: lineData("bunny", "I don't know.", "Nevím.", "🤷"),
        benji: lineData("benji", "I don't know.", "Nevím.", "🤷"),
        bruno: lineData("bruno", "Let us drink in the forest.", "Napijme se v lese.", "🌲"),
        sunny: lineData("sunny", "I have nuts, not water!", "Mám oříšky, ne vodu!", "🥜"),
        pump: lineData("fiona", "The pump needs help.", "Pumpa potřebuje pomoc.", "💧"),
      },
      wrongHintEn: "Try someone else.",
      hintAfterMistakesEn: "Try Fiona!",
      response: lineData("fiona", "I know! Sunny, jump on the handle!", "Já vím! Sunny, skoč na páku!", "💡"),
      afterResponse: lineData("fiona", "Bruno, push it up!", "Bruno, tlač ji nahoru!", "🤲"),
    }),
    { type: "phase", phase: "3f" },
    line("sunny", "Okay, I am jumping!", "Dobře, skáču!", "⬆️"),
    line("bruno", "I am pushing!", "Tlačím!", "🤲"),
    line("bunny", "Water! We have water!", "Voda! Máme vodu!", "💧"),
    line("all", "Thank you, Fiona!", "Děkujeme, Fiono!", "🎉", { revealMap: true }),
  ],
};

const state = {
  sceneState: SCENE_STATES.waitingAudio,
  stepIndex: 0,
  phase: scene03Config.phase,
  activeTargetId: "",
  sequenceId: 0,
  audioUnlocked: false,
  audioCache: new Map(),
  currentAudio: null,
  currentUtterance: null,
  speechQueue: Promise.resolve(),
  wrongTapCount: 0,
  htmlAudioPrimed: false,
};

function line(characterId, textEn, textCz, emoji, options = {}) {
  return { type: "dialogue", line: lineData(characterId, textEn, textCz, emoji, options) };
}

function lineData(characterId, textEn, textCz, emoji, options = {}) {
  return {
    characterId,
    textEn,
    textCz,
    emoji,
    audio: audioForLine(characterId, textEn),
    ...options,
  };
}

function tap(config) {
  return { type: "tap", ...config };
}

function currentPhase() {
  return phases[state.phase] || phases["3a"];
}

function currentStep() {
  return scene03Config.steps[state.stepIndex];
}

function targetById(id) {
  return currentPhase().hotspots[id] || null;
}

function isWaitingForTap() {
  return state.sceneState === SCENE_STATES.waitingTap;
}

function isTapStep(step = currentStep()) {
  return step?.type === "tap";
}

function acceptedIds(step = currentStep()) {
  if (!isTapStep(step)) {
    return [];
  }
  return step.acceptIds || [step.targetId];
}

function currentPhaseStartIndex() {
  const startAt = Math.min(state.stepIndex, scene03Config.steps.length - 1);
  for (let index = startAt; index >= 0; index -= 1) {
    const step = scene03Config.steps[index];
    if (step?.type === "phase" && step.phase === state.phase) {
      return index;
    }
  }
  return 0;
}

function setupSceneImage() {
  sceneImage.src = `${currentPhase().image}?v=${sceneAssetVersion}`;
  sceneImage.addEventListener("error", () => {
    if (!sceneImage.src.endsWith(scene03Config.placeholderImage)) {
      sceneImage.src = scene03Config.placeholderImage;
    }
  }, { once: true });
}

function setPhase(phaseId) {
  state.phase = phaseId;
  sceneImage.src = `${currentPhase().image}?v=${sceneAssetVersion}`;
  hideBubble();
}

function loadVoices() {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.getVoices();
  }
}

function cancelSpeech() {
  if (state.currentAudio) {
    state.currentAudio.pause();
    state.currentAudio = null;
  }
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
  state.currentUtterance = null;
}

function firstDialogueAudio() {
  const firstDialogue = scene03Config.steps.find((step) => step.type === "dialogue" && step.line?.audio);
  return firstDialogue?.line.audio || "";
}

function primeHtmlAudio() {
  if (state.htmlAudioPrimed) {
    return;
  }
  const src = firstDialogueAudio();
  if (!src) {
    return;
  }

  state.htmlAudioPrimed = true;
  const audio = new Audio(src);
  audio.muted = true;
  audio.volume = 0;
  audio.preload = "auto";
  audio.playsInline = true;

  const playPromise = audio.play();
  if (playPromise && typeof playPromise.then === "function") {
    playPromise
      .then(() => {
        audio.pause();
        audio.currentTime = 0;
      })
      .catch(() => {
        audio.load();
      });
  } else {
    audio.load();
  }
}

function preloadOpeningAudio() {
  scene03Config.steps
    .filter((step) => step.type === "dialogue" && step.line?.audio)
    .slice(0, 4)
    .forEach((step) => {
      const audio = new Audio(step.line.audio);
      audio.preload = "auto";
      audio.load();
    });
}

function audioSlug(text) {
  return String(text || "")
    .toLowerCase()
    .replaceAll("'", "")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 64);
}

function audioForLine(characterId, textEn) {
  if (!edgeAudioCharacters.has(characterId)) {
    return "";
  }
  return `audio/english/scene03_${characterId}_${audioSlug(textEn)}_en.mp3?v=${sceneAudioVersion}`;
}

function audioForEnglishText(characterId, textEn) {
  if (!textEn) {
    return "";
  }
  const characterAudio = audioForLine(characterId, textEn);
  if (characterAudio) {
    return characterAudio;
  }
  return `audio/english/scene03_ui_${audioSlug(textEn)}_en.mp3?v=${sceneAudioVersion}`;
}

async function audioFileExists(src) {
  if (!src) {
    return false;
  }
  if (state.audioCache.has(src)) {
    return state.audioCache.get(src);
  }

  let exists = false;
  try {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 2000);
    const response = await fetch(src, {
      method: "GET",
      cache: "no-store",
      signal: controller.signal,
      headers: { Range: "bytes=0-0" },
    });
    window.clearTimeout(timeoutId);
    exists = response.ok;
  } catch (error) {
    exists = false;
  }

  state.audioCache.set(src, exists);
  return exists;
}

function playAudioElement(audio) {
  return new Promise((resolve) => {
    let settled = false;
    let played = false;
    const timeoutId = window.setTimeout(finish, 15000);

    function finish(result = played) {
      if (settled) {
        return;
      }
      settled = true;
      window.clearTimeout(timeoutId);
      if (state.currentAudio === audio) {
        state.currentAudio = null;
      }
      resolve(result);
    }

    audio.addEventListener("playing", () => {
      played = true;
    }, { once: true });
    audio.addEventListener("ended", () => finish(true), { once: true });
    audio.addEventListener("error", () => finish(false), { once: true });
    state.currentAudio = audio;

    const playPromise = audio.play();
    if (playPromise && typeof playPromise.then === "function") {
      playPromise
        .then(() => {
          played = true;
        })
        .catch(() => finish(false));
    }
  });
}

async function playAudioIfExists(src) {
  if (!state.audioUnlocked || !src) {
    return false;
  }
  if (!(await audioFileExists(src))) {
    return false;
  }

  const audio = new Audio(src);
  audio.preload = "auto";
  audio.volume = scene03Config.audioVolume;
  return playAudioElement(audio);
}

async function playVoice({ src, text, characterId, rate }) {
  const played = await playAudioIfExists(src);
  if (played) {
    return;
  }
  await speakEnglish(text, characterId, { rate });
}

function pickVoice(preferredPattern, langPrefix) {
  if (!("speechSynthesis" in window)) {
    return null;
  }

  const voices = window.speechSynthesis.getVoices();
  const patterns = String(preferredPattern || "")
    .split("|")
    .map((part) => part.trim().toLowerCase())
    .filter(Boolean);

  for (const pattern of patterns) {
    const match = voices.find((voice) => voice.name.toLowerCase().includes(pattern));
    if (match) {
      return match;
    }
  }

  return voices.find((voice) => voice.lang.toLowerCase().startsWith(langPrefix)) || null;
}

function estimateSpeechMs(text) {
  return Math.min(9000, Math.max(1200, String(text || "").length * 70));
}

function normalizeCzechSpeech(text) {
  return String(text || "")
    .replaceAll("Benjiho", "Benžiho")
    .replaceAll("Benji", "Benži")
    .replaceAll("Bunnyho", "Bannyho")
    .replaceAll("Bunny", "Banny")
    .replaceAll("Fiono", "Fijono")
    .replaceAll("Fiona", "Fijona");
}

function speakLine({ text, lang = "en", characterId = "", rate, pitch, volume }) {
  return new Promise((resolve) => {
    if (!text) {
      resolve();
      return;
    }

    const estimatedMs = estimateSpeechMs(text);
    let settled = false;
    let timeoutId = null;

    const finish = () => {
      if (settled) {
        return;
      }
      settled = true;
      if (timeoutId) {
        window.clearTimeout(timeoutId);
      }
      state.currentUtterance = null;
      resolve();
    };

    if (!state.audioUnlocked || !("speechSynthesis" in window)) {
      window.setTimeout(finish, estimatedMs);
      return;
    }

    window.speechSynthesis.cancel();

    window.setTimeout(() => {
      if (settled) {
        return;
      }

      const isCzech = lang === "cs";
      const utterance = new SpeechSynthesisUtterance(isCzech ? normalizeCzechSpeech(text) : text);
      utterance.lang = isCzech ? "cs-CZ" : "en-US";
      utterance.rate = rate ?? (isCzech ? 0.9 : 0.86);
      utterance.pitch = pitch ?? (characterId === "sunny" ? 1.14 : characterId === "bruno" ? 0.9 : 1.0);
      utterance.volume = volume ?? (isCzech ? 0.62 : 1.0);

      const voice = pickVoice(
        isCzech ? "zuzana|iveta|jana|cs" : sharedVoices[characterId],
        isCzech ? "cs" : "en",
      );
      if (voice) {
        utterance.voice = voice;
      }

      state.currentUtterance = utterance;
      utterance.onend = finish;
      utterance.onerror = finish;
      window.speechSynthesis.resume();
      window.speechSynthesis.speak(utterance);
      timeoutId = window.setTimeout(finish, estimatedMs + 1200);
    }, 60);
  });
}

async function speakEnglish(text, characterId = "", options = {}) {
  const played = await playAudioIfExists(options.audio || audioForEnglishText(characterId, text));
  if (played) {
    return;
  }
  await speakLine({ text, lang: "en", characterId, rate: options.rate });
}

async function speakCzech(text) {
  await speakLine({ text, lang: "cs", rate: 0.9, volume: 0.62 });
}

function queueSpeech(job) {
  state.speechQueue = state.speechQueue.then(job).catch(() => {});
  return state.speechQueue;
}

function showBubble(target, { emoji, textEn = "", textCz = "" } = {}) {
  if (!target) {
    speechBubble.classList.add("hidden");
    return;
  }

  bubbleEmoji.textContent = emoji || target.emoji || "";
  bubbleText.textContent = textEn || "";
  bubbleTranslation.textContent = textCz || "";
  bubbleText.classList.toggle("hidden", !textEn);
  bubbleTranslation.classList.toggle("hidden", !textCz);
  speechBubble.style.left = `${target.bubble.x}%`;
  speechBubble.style.top = `${target.bubble.y}%`;
  speechBubble.classList.remove("hidden");
}

function hideBubble() {
  speechBubble.classList.add("hidden");
}

function hideDictionary() {
  dictionaryPanel.classList.add("hidden");
  dictionaryButton.classList.remove("active-panel");
}

function showTaskPrompt(step) {
  if (!isTapStep(step) || state.sceneState !== SCENE_STATES.waitingTap) {
    taskPrompt.classList.add("hidden");
    return;
  }

  taskEmoji.textContent = step.promptEmoji || "👆";
  taskPromptText.textContent = step.promptEn;
  taskPromptTranslation.textContent = step.promptCz || "";
  taskPromptTranslation.classList.toggle("hidden", !step.promptCz);
  taskPrompt.classList.remove("hidden");
  taskPrompt.classList.add("pulse");
}

function renderDictionary() {
  dictionaryList.innerHTML = "";
  scene03Config.vocabulary.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "dictionary-item";
    button.innerHTML = `
      <span class="dictionary-emoji" aria-hidden="true">${item.emoji}</span>
      <span class="dictionary-word">${item.en}</span>
      <span class="dictionary-translation">${item.cz}</span>
    `;
    button.addEventListener("click", () => {
      queueSpeech(async () => {
        await speakEnglish(item.en, "", { rate: 0.82 });
        await speakCzech(item.cz);
      });
    });
    dictionaryList.appendChild(button);
  });
}

function createHotspot(targetId, target) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "hotspot";
  button.dataset.targetId = targetId;
  button.style.left = `${target.rect.x}%`;
  button.style.top = `${target.rect.y}%`;
  button.style.width = `${target.rect.w}%`;
  button.style.height = `${target.rect.h}%`;
  button.style.setProperty("--hotspot-glow", target.color);
  button.setAttribute("aria-label", target.label);

  const step = currentStep();
  const isActive = state.activeTargetId === targetId;
  const isTarget = isWaitingForTap() && !step?.hideTargetHighlight && acceptedIds(step).includes(targetId);
  const isClickableWrong = isWaitingForTap() && isTapStep(step);

  if (isActive) {
    button.classList.add("active");
  }
  if (isTarget) {
    button.classList.add("task-ready", "target-pulse", "active");
  } else if (!isClickableWrong) {
    button.classList.add("locked");
  }

  button.addEventListener("click", () => handleTap(targetId));
  return button;
}

function createQuickSkipButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "scene-quick-skip";
  button.setAttribute(
    "aria-label",
    isDirectScene04Shortcut()
      ? "Pokračovat k Harrymu"
      : "Rychlý posun scény",
  );
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    quickAdvanceScene();
  });
  return button;
}

function renderHotspots() {
  overlay.innerHTML = "";
  overlay.appendChild(createQuickSkipButton());
  Object.entries(currentPhase().hotspots).forEach(([targetId, target]) => {
    if (targetId === "all" && !isWaitingForTap() && state.activeTargetId !== "all") {
      return;
    }
    overlay.appendChild(createHotspot(targetId, target));
  });
}

function renderHud() {
  audioGate?.classList.toggle("hidden", state.sceneState !== SCENE_STATES.waitingAudio);

  const busy = state.sceneState === SCENE_STATES.playing
    || state.sceneState === SCENE_STATES.promptingTap
    || state.sceneState === SCENE_STATES.resolvingTap;

  repeatButton.disabled = state.sceneState === SCENE_STATES.waitingAudio;
  dictionaryButton.disabled = state.sceneState === SCENE_STATES.waitingAudio || busy;
  helpButton.disabled = state.sceneState === SCENE_STATES.waitingAudio
    || state.sceneState === SCENE_STATES.promptingTap
    || state.sceneState === SCENE_STATES.resolvingTap;

  if (state.sceneState === SCENE_STATES.complete) {
    completeBanner.classList.remove("hidden");
    completeBanner.querySelector(".complete-text").textContent = "Scene 3 complete";
  } else {
    completeBanner.classList.add("hidden");
  }

  showTaskPrompt(currentStep());
  renderHotspots();
}

async function primeAudio() {
  if (state.audioUnlocked) {
    return;
  }
  state.audioUnlocked = true;
  primeHtmlAudio();
  preloadOpeningAudio();
  loadVoices();

  if (!("speechSynthesis" in window)) {
    return;
  }

  await new Promise((resolve) => {
    if (window.speechSynthesis.getVoices().length > 0) {
      resolve();
      return;
    }
    window.speechSynthesis.addEventListener("voiceschanged", resolve, { once: true });
    window.setTimeout(resolve, 300);
  });
}

async function playLine(line, runId) {
  if (!line || runId !== state.sequenceId) {
    return;
  }

  const target = targetById(line.characterId) || targetById("all");
  state.activeTargetId = line.characterId;
  renderHud();
  showBubble(target, { emoji: line.emoji, textEn: line.textEn, textCz: line.textCz });

  await playVoice({
    src: line.audio,
    text: line.textEn,
    characterId: line.characterId,
  });
  await speakCzech(line.textCz);

  if (line.revealMap) {
    mapFragment.classList.remove("hidden");
    mapFragment.classList.add("reveal");
  }

  if (runId !== state.sequenceId) {
    return;
  }

  await new Promise((resolve) => window.setTimeout(resolve, 240));
  state.activeTargetId = "";
  hideBubble();
}

async function beginTapStep(step, runId) {
  if (runId !== state.sequenceId) {
    return;
  }
  state.sceneState = SCENE_STATES.promptingTap;
  state.activeTargetId = "";
  state.wrongTapCount = 0;
  hideBubble();
  renderHud();

  await speakEnglish(step.promptEn, "", { rate: 0.84 });
  await speakCzech(step.promptCz);

  if (runId !== state.sequenceId || currentStep() !== step) {
    return;
  }
  state.sceneState = SCENE_STATES.waitingTap;
  renderHud();
}

async function advanceScene(runId = state.sequenceId) {
  while (state.stepIndex < scene03Config.steps.length) {
    if (runId !== state.sequenceId) {
      return;
    }

    const step = currentStep();
    if (!step) {
      break;
    }

    if (step.type === "phase") {
      setPhase(step.phase);
      state.stepIndex += 1;
      renderHud();
      await new Promise((resolve) => window.setTimeout(resolve, 240));
      continue;
    }

    if (step.type === "dialogue") {
      state.sceneState = SCENE_STATES.playing;
      renderHud();
      await playLine(step.line, runId);
      state.stepIndex += 1;
      continue;
    }

    if (step.type === "tap") {
      await beginTapStep(step, runId);
      return;
    }
  }

  finishScene();
}

async function runScene() {
  const runId = state.sequenceId;
  state.sceneState = SCENE_STATES.playing;
  state.stepIndex = 0;
  state.phase = scene03Config.phase;
  state.activeTargetId = "";
  state.wrongTapCount = 0;
  mapFragment.classList.remove("reveal");
  mapFragment.classList.add("hidden");
  completeBanner.classList.add("hidden");
  hideBubble();
  hideDictionary();
  setupSceneImage();
  renderHud();
  await advanceScene(runId);
}

async function handleTap(targetId) {
  if (!isWaitingForTap()) {
    return;
  }

  const step = currentStep();
  if (!isTapStep(step)) {
    return;
  }

  state.sceneState = SCENE_STATES.resolvingTap;
  state.activeTargetId = targetId;
  renderHud();

  if (!acceptedIds(step).includes(targetId)) {
    state.wrongTapCount += 1;
    await handleWrongTap(step, targetId);
    if (currentStep() === step) {
      state.activeTargetId = "";
      state.sceneState = SCENE_STATES.waitingTap;
      if (step.hintAfterMistakesEn && state.wrongTapCount >= 2) {
        taskPromptText.textContent = step.hintAfterMistakesEn;
      }
      renderHud();
    }
    return;
  }

  if (step.response) {
    await playLine(step.response, state.sequenceId);
  }
  if (step.afterResponse) {
    await playLine(step.afterResponse, state.sequenceId);
  }

  state.stepIndex += 1;
  state.sceneState = SCENE_STATES.playing;
  state.activeTargetId = "";
  await advanceScene(state.sequenceId);
}

async function handleWrongTap(step, targetId) {
  const response = step.wrongResponses?.[targetId];
  if (response) {
    await playLine(response, state.sequenceId);
    return;
  }
  hideBubble();
  await speakEnglish(step.wrongHintEn || "Try again.", "", { rate: 0.86 });
}

function finishScene() {
  state.sceneState = SCENE_STATES.complete;
  state.activeTargetId = "";
  hideBubble();
  mapFragment.classList.remove("hidden");
  mapFragment.classList.add("reveal");
  renderHud();
}

function restartScene() {
  state.sequenceId += 1;
  cancelSpeech();
  state.speechQueue = Promise.resolve();
  runScene();
}

function replayCurrentImage() {
  if (state.sceneState === SCENE_STATES.waitingAudio) {
    return;
  }
  state.sequenceId += 1;
  cancelSpeech();
  state.speechQueue = Promise.resolve();
  state.stepIndex = currentPhaseStartIndex();
  state.sceneState = SCENE_STATES.playing;
  state.activeTargetId = "";
  state.wrongTapCount = 0;
  hideBubble();
  hideDictionary();
  advanceScene(state.sequenceId);
}

function quickAdvanceScene() {
  if (isDirectScene04Shortcut()) {
    goToNextScene();
    return;
  }
  if (state.sceneState === SCENE_STATES.waitingAudio) {
    startGame();
    return;
  }

  state.sequenceId += 1;
  cancelSpeech();
  state.speechQueue = Promise.resolve();
  hideBubble();
  state.activeTargetId = "";
  state.wrongTapCount = 0;
  state.stepIndex = Math.min(state.stepIndex + 1, scene03Config.steps.length);
  state.sceneState = SCENE_STATES.playing;
  advanceScene(state.sequenceId);
}

function isQuickSkipCornerClick(event, container) {
  const rect = container.getBoundingClientRect();
  if (!rect.width || !rect.height) {
    return false;
  }
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  return x >= 0 && y >= 0 && x <= rect.width * 0.16 && y >= rect.height * 0.76;
}

function playHelp() {
  return queueSpeech(async () => {
    const step = currentStep();
    if (isTapStep(step)) {
      await speakCzech(step.promptCz);
      await speakEnglish(step.promptEn, "", { rate: 0.84 });
      return;
    }
    await speakCzech(scene03Config.mainHelp);
  });
}

async function startGame() {
  await primeAudio();
  await speakCzech(scene03Config.mainHelp);
  restartScene();
}

function goBack() {
  window.location.href = "../scene02_sunnys_lost_nuts/index.html";
}

function goToNextScene() {
  window.location.href = "../scene04_harry_guard_prototype/index.html";
}

function isDirectScene04Shortcut() {
  return state.phase === "3a" || state.sceneState === SCENE_STATES.complete;
}

function handleRepeat() {
  replayCurrentImage();
}

backButton.addEventListener("click", goBack);
repeatButton.addEventListener("click", handleRepeat);
dictionaryButton.addEventListener("click", () => {
  if (dictionaryButton.disabled) {
    return;
  }
  const willShow = dictionaryPanel.classList.contains("hidden");
  dictionaryPanel.classList.toggle("hidden", !willShow);
  dictionaryButton.classList.toggle("active-panel", willShow);
  if (willShow) {
    queueSpeech(async () => {
      await speakCzech("Slovníček. Klepni na slovo a uslyšíš ho anglicky.");
    });
  }
});
helpButton.addEventListener("click", () => {
  if (!helpButton.disabled) {
    playHelp();
  }
});
scene.addEventListener("click", (event) => {
  if (event.target.closest(".ui-button")) {
    return;
  }
  if (state.sceneState === SCENE_STATES.waitingAudio) {
    startGame();
  }
});

scene.addEventListener("click", (event) => {
  if (!isQuickSkipCornerClick(event, scene)) {
    return;
  }
  event.preventDefault();
  event.stopImmediatePropagation();
  quickAdvanceScene();
}, true);

window.speechSynthesis?.addEventListener?.("voiceschanged", loadVoices);

setupSceneImage();
renderDictionary();
loadVoices();
renderHud();
