/**
 * Scene 2 — Sunny's Lost Nuts (standalone prototype)
 *
 * Image: scene_02_sunnys_lost_nuts_before.png (1672 x 941)
 *
 * Future MMTX integration:
 *   scene id: sunnysLostNuts
 *   query: ?scene=sunnysLostNuts
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
const nutsReveal = document.getElementById("nutsReveal");
const nutsRevealImage = document.getElementById("nutsRevealImage");
const nutsRevealFallback = document.getElementById("nutsRevealFallback");
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
  idle: "idle",
  waitingAudio: "waitingAudio",
  playing: "playing",
  promptingTap: "promptingTap",
  waitingTap: "waitingTap",
  resolvingTap: "resolvingTap",
  complete: "complete",
};

const scene02Config = {
  sceneId: "sunnysLostNuts",
  image: "scene_02_sunnys_lost_nuts_before.png",
  placeholderImage: "scene_placeholder.svg",
  aspect: { w: 1672, h: 941 },
  characters: [
    {
      id: "benji",
      label: "Benji",
      rect: { x: 3.0, y: 40.0, w: 23.0, h: 40.0 },
      bubble: { x: 10.0, y: 32.0 },
      color: "#5f8bff",
      emoji: "🐶",
      preferredVoice: "fable|brian|andrew|roger|guy|daniel|alex|aaron|evan|junior",
      pitch: 1.0,
      rate: 0.86,
    },
    {
      id: "bunny",
      label: "Bunny",
      rect: { x: 25.0, y: 17.0, w: 13.0, h: 37.0 },
      bubble: { x: 31.0, y: 18.0 },
      color: "#ff9ec8",
      emoji: "🐰",
      preferredVoice: "echo|junior|samantha|ava|victoria|karen",
      pitch: 1.12,
      rate: 0.9,
    },
    {
      id: "bruno",
      label: "Bruno",
      rect: { x: 44.0, y: 28.0, w: 14.0, h: 47.0 },
      bubble: { x: 49.0, y: 18.0 },
      color: "#b8895f",
      emoji: "🦡",
      preferredVoice: "onyx|aaron|roger|daniel|guy",
      pitch: 0.88,
      rate: 0.84,
    },
    {
      id: "fiona",
      label: "Fiona",
      rect: { x: 62.0, y: 29.0, w: 17.0, h: 48.0 },
      bubble: { x: 68.0, y: 18.0 },
      color: "#d4a574",
      emoji: "🦊",
      preferredVoice: "shimmer|samantha|ava|victoria|karen",
      pitch: 1.08,
      rate: 0.9,
    },
    {
      id: "sunny",
      label: "Sunny",
      rect: { x: 81.0, y: 47.0, w: 15.0, h: 41.0 },
      bubble: { x: 86.0, y: 36.0 },
      color: "#f4c542",
      emoji: "🐿️",
      preferredVoice: "nova|samantha|ava|victoria|karen|junior",
      pitch: 1.18,
      rate: 0.95,
    },
  ],
  mainHelp: {
    textCz: "Poslouchej anglické věty. Když se objeví žlutá nápověda, klepni na správnou postavu nebo na brašnu.",
  },
  props: [
    {
      id: "bag",
      label: "Bruno's bag",
      rect: { x: 50.5, y: 44.0, w: 10.5, h: 22.0 },
      bubble: { x: 53.0, y: 36.0 },
      color: "#c9954a",
      emoji: "🎒",
    },
    {
      id: "bag-zone",
      label: "Bruno's bag area",
      rect: { x: 46.0, y: 38.0, w: 20.0, h: 32.0 },
      bubble: { x: 53.0, y: 36.0 },
      color: "#c9954a",
      emoji: "🎒",
      hiddenHotspot: true,
    },
  ],
  nutsReveal: {
    position: { x: 53.0, y: 52.0 },
    imageAsset: "nuts_reveal.png",
    fallbackEmoji: ["🥜", "🥜", "🥜"],
  },
  vocabulary: [
    { en: "nuts", cz: "oříšky", emoji: "🥜", audio: "audio/english/scene02_vocab_nuts_en.mp3" },
    { en: "map", cz: "mapa", emoji: "🗺️", audio: "audio/english/scene02_vocab_map_en.mp3" },
    { en: "carrot", cz: "mrkev", emoji: "🥕", audio: "audio/english/scene02_vocab_carrot_en.mp3" },
    { en: "bag", cz: "brašna", emoji: "🎒", audio: "audio/english/scene02_vocab_bag_en.mp3" },
    { en: "I have", cz: "mám", emoji: "✅", audio: "audio/english/scene02_vocab_i_have_en.mp3" },
    { en: "I don't have", cz: "nemám", emoji: "❌", audio: "audio/english/scene02_vocab_i_dont_have_en.mp3" },
    { en: "Do you have?", cz: "máš?", emoji: "❓", audio: "audio/english/scene02_vocab_do_you_have_en.mp3" },
    { en: "Does he have?", cz: "má on?", emoji: "❓", audio: "audio/english/scene02_vocab_does_he_have_en.mp3" },
    { en: "Look inside", cz: "podívej se dovnitř", emoji: "👀", audio: "audio/english/scene02_vocab_look_inside_en.mp3" },
    { en: "ready", cz: "připravený", emoji: "✅", audio: "audio/english/scene02_vocab_ready_en.mp3" },
    { en: "wait", cz: "počkat", emoji: "✋", audio: "audio/english/scene02_vocab_wait_en.mp3" },
    { en: "happy", cz: "šťastný", emoji: "😊", audio: "audio/english/scene02_vocab_happy_en.mp3" },
  ],
  steps: [
    {
      type: "dialogue",
      line: {
        characterId: "sunny",
        textEn: "Oh no! I don't have my nuts!",
        textCz: "Ach ne! Nemám svoje oříšky!",
        emoji: "😢",
        audio: "audio/english/scene02_01_sunny_no_nuts_en.mp3",
      },
    },
    {
      type: "dialogue",
      line: {
        characterId: "fiona",
        textEn: "Benji, do you have nuts?",
        textCz: "Benji, máš oříšky?",
        emoji: "❓",
        audio: "audio/english/scene02_02_fiona_benji_nuts_en.mp3",
      },
    },
    {
      type: "tap",
      targetId: "benji",
      promptEmoji: "🐶",
      promptEn: "Tap Benji. Does he have nuts?",
      promptCz: "Klepni na Benjiho. Má oříšky?",
      promptAudio: "audio/english/scene02_prompt_tap_benji_en.mp3",
      helpCz: "Klepni na Benjiho. Má oříšky?",
      helpAudioCz: "audio/czech/scene02_help_tap_benji_cz.mp3",
      helpEn: "Tap Benji. Does he have nuts?",
      wrongHintEn: "Not yet. Tap Benji.",
      wrongHintAudio: "audio/english/scene02_not_yet_tap_benji_en.mp3",
      response: {
        characterId: "benji",
        textEn: "No. I have a map.",
        textCz: "Ne. Mám mapu.",
        emoji: "🗺️",
        audio: "audio/english/scene02_03_benji_map_en.mp3",
      },
    },
    {
      type: "dialogue",
      line: {
        characterId: "fiona",
        textEn: "Bunny, do you have nuts?",
        textCz: "Bunny, máš oříšky?",
        emoji: "❓",
        audio: "audio/english/scene02_04_fiona_bunny_nuts_en.mp3",
      },
    },
    {
      type: "tap",
      targetId: "bunny",
      promptEmoji: "🐰",
      promptEn: "Tap Bunny. Does he have nuts?",
      promptCz: "Klepni na Bunnyho. Má oříšky?",
      promptAudio: "audio/english/scene02_prompt_tap_bunny_en.mp3",
      helpCz: "Klepni na Bunny. Má oříšky?",
      helpAudioCz: "audio/czech/scene02_help_tap_bunny_cz.mp3",
      helpEn: "Tap Bunny. Does he have nuts?",
      wrongHintEn: "Not yet. Tap Bunny.",
      wrongHintAudio: "audio/english/scene02_not_yet_tap_bunny_en.mp3",
      response: {
        characterId: "bunny",
        textEn: "No. I have a carrot.",
        textCz: "Ne. Mám mrkev.",
        emoji: "🥕",
        audio: "audio/english/scene02_05_bunny_carrot_en.mp3",
      },
    },
    {
      type: "dialogue",
      line: {
        characterId: "bruno",
        textEn: "Wait a second. I have a bag.",
        textCz: "Počkejte chvilku. Mám brašnu.",
        emoji: "🎒",
        audio: "audio/english/scene02_06_bruno_bag_wait_second_en_fix1.mp3",
      },
    },
    {
      type: "dialogue",
      line: {
        characterId: "bruno",
        textEn: "It is big. Look inside, friends!",
        textCz: "Je velká. Podívejte se dovnitř, kamarádi!",
        emoji: "👀",
        audio: "audio/english/scene02_07_bruno_look_inside_friends_en_fix3_balanced.mp3",
      },
    },
    {
      type: "tap",
      targetId: "bag",
      acceptIds: ["bag", "bag-zone"],
      promptEmoji: "🎒",
      promptEn: "Tap the bag.",
      promptCz: "Klepni na brašnu.",
      promptAudio: "audio/english/scene02_prompt_tap_bag_en.mp3",
      helpCz: "Klepni na brašnu.",
      helpAudioCz: "audio/czech/scene02_help_tap_bag_cz.mp3",
      helpEn: "Tap the bag.",
      wrongHintEn: "Look at the bag.",
      wrongHintAudio: "audio/english/scene02_look_at_bag_en.mp3",
      revealNuts: true,
    },
    {
      type: "dialogue",
      line: {
        characterId: "sunny",
        textEn: "My nuts! I am so happy!",
        textCz: "Moje oříšky! Mám takovou radost!",
        emoji: "🎉",
        audio: "audio/english/scene02_08_sunny_my_nuts_en_fix1_balanced.mp3",
        bounceSunny: true,
      },
    },
    {
      type: "dialogue",
      line: {
        characterId: "fiona",
        textEn: "Good. Now we are ready.",
        textCz: "Dobře. Teď jsme připraveni.",
        emoji: "✅",
        audio: "audio/english/scene02_09_fiona_ready_en.mp3",
        revealMap: true,
      },
    },
  ],
  audio: {
    volume: 0.78,
    tryAgain: "audio/english/scene02_try_again_en.mp3",
    lookAtBag: "audio/english/scene02_look_at_bag_en.mp3",
    dictionaryHelpCz: "audio/czech/scene02_dictionary_help_cz.mp3",
  },
};

const state = {
  sceneState: SCENE_STATES.idle,
  stepIndex: 0,
  activeCharacterId: "",
  activeLine: null,
  sequenceId: 0,
  audioUnlocked: false,
  currentAudio: null,
  currentUtterance: null,
  speechQueue: Promise.resolve(),
  audioCache: new Map(),
  nutsRevealed: false,
  nutsImageReady: null,
};

function characterById(id) {
  return scene02Config.characters.find((item) => item.id === id);
}

function propById(id) {
  return scene02Config.props.find((item) => item.id === id);
}

function currentStep() {
  return scene02Config.steps[state.stepIndex];
}

function isTapStep(step = currentStep()) {
  return step?.type === "tap";
}

function isWaitingForTap() {
  return state.sceneState === SCENE_STATES.waitingTap;
}

function isTapPromptVisible() {
  return isTapStep() && (
    state.sceneState === SCENE_STATES.promptingTap
    || state.sceneState === SCENE_STATES.waitingTap
  );
}

function stepAcceptIds(step = currentStep()) {
  if (!step || step.type !== "tap") {
    return [];
  }
  return step.acceptIds || [step.targetId];
}

function isBagStepActive() {
  const step = currentStep();
  return isWaitingForTap() && step?.type === "tap" && step.targetId === "bag";
}

function setupSceneImage() {
  sceneImage.src = scene02Config.image;
  sceneImage.addEventListener("error", () => {
    if (!sceneImage.src.endsWith(scene02Config.placeholderImage)) {
      sceneImage.src = scene02Config.placeholderImage;
    }
  }, { once: true });
}

function setupNutsReveal() {
  const config = scene02Config.nutsReveal;
  nutsReveal.style.left = `${config.position.x}%`;
  nutsReveal.style.top = `${config.position.y}%`;

  nutsRevealFallback.innerHTML = "";
  config.fallbackEmoji.forEach((emoji) => {
    const span = document.createElement("span");
    span.textContent = emoji;
    nutsRevealFallback.appendChild(span);
  });

  if (config.imageAsset) {
    const probe = new Image();
    probe.onload = () => {
      state.nutsImageReady = config.imageAsset;
      nutsRevealImage.src = config.imageAsset;
      nutsRevealImage.alt = "Found nuts";
    };
    probe.onerror = () => {
      state.nutsImageReady = null;
    };
    probe.src = config.imageAsset;
  }
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

function goBackToForestSignpost() {
  window.location.href = "../index.html?scene=intro4";
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
    const finish = () => {
      if (settled) {
        return;
      }
      settled = true;
      window.clearTimeout(timeoutId);
      if (state.currentAudio === audio) {
        state.currentAudio = null;
      }
      resolve();
    };

    const timeoutId = window.setTimeout(finish, 15000);
    audio.addEventListener("ended", finish, { once: true });
    audio.addEventListener("error", finish, { once: true });
    state.currentAudio = audio;

    const playPromise = audio.play();
    if (playPromise && typeof playPromise.then === "function") {
      playPromise.catch(finish);
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
  audio.volume = scene02Config.audio.volume;
  await playAudioElement(audio);
  return true;
}

function estimateSpeechMs(text) {
  return Math.min(9000, Math.max(1400, text.length * 72));
}

function normalizeCzechSpeech(text) {
  return String(text || "")
    .replaceAll("Benjiho", "Benžiho")
    .replaceAll("Benji", "Benži")
    .replaceAll("Bunnyho", "Bannyho")
    .replaceAll("Bunny", "Banny");
}

function speakLine({ text, lang, character, rate, pitch, volume }) {
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

      const utterance = new SpeechSynthesisUtterance(text);
      const isCzech = lang === "cs";
      utterance.lang = isCzech ? "cs-CZ" : "en-US";
      utterance.rate = rate ?? (isCzech ? 0.92 : character?.rate ?? 0.88);
      utterance.pitch = pitch ?? character?.pitch ?? 1.0;
      utterance.volume = volume ?? (isCzech ? 0.62 : 1.0);

      const voice = pickVoice(
        isCzech ? "zuzana|iveta|jana|cs" : character?.preferredVoice,
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

async function playVoice({ src, text, lang = "en", character, rate, pitch }) {
  const played = await playAudioIfExists(src);
  if (played) {
    return;
  }
  await speakLine({ text, lang, character, rate, pitch });
}

async function speakCzechTranslation(text) {
  if (!text) {
    return;
  }
  await speakLine({ text: normalizeCzechSpeech(text), lang: "cs", rate: 0.9, volume: 0.62 });
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

  bubbleEmoji.textContent = emoji || target.emoji;
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

function setBottomHint(text, parentOnly = false) {
  void text;
  void parentOnly;
}

function updateTaskPrompt(step) {
  if (!step || step.type !== "tap" || !isTapPromptVisible()) {
    taskPrompt.classList.add("hidden");
    return;
  }

  taskEmoji.textContent = step.promptEmoji;
  taskPromptText.textContent = step.promptEn;
  taskPromptTranslation.textContent = step.promptCz || step.helpCz || "";
  taskPromptTranslation.classList.toggle("hidden", !(step.promptCz || step.helpCz));
  taskPrompt.classList.remove("hidden");
}

function revealNutsEffect() {
  state.nutsRevealed = true;
  nutsReveal.classList.remove("hidden");

  if (state.nutsImageReady) {
    nutsRevealImage.classList.remove("hidden");
    nutsRevealImage.hidden = false;
    nutsRevealFallback.classList.add("hidden");
  } else {
    nutsRevealImage.classList.add("hidden");
    nutsRevealImage.hidden = true;
    nutsRevealFallback.classList.remove("hidden");
  }
}

function hideNutsEffect() {
  state.nutsRevealed = false;
  nutsReveal.classList.add("hidden");
}

function revealMapEffect() {
  mapFragment.classList.remove("hidden");
  mapFragment.classList.add("reveal");
}

function renderDictionary() {
  dictionaryList.innerHTML = "";
  scene02Config.vocabulary.forEach((item) => {
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
        await playVoice({
          src: item.audio,
          text: item.en,
          lang: "en",
          rate: 0.82,
        });
        await speakLine({
          text: item.cz,
          lang: "cs",
          rate: 0.9,
        });
      });
    });
    dictionaryList.appendChild(button);
  });
}

function createCharacterHotspot(character) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "hotspot";
  button.dataset.targetId = character.id;
  button.style.left = `${character.rect.x}%`;
  button.style.top = `${character.rect.y}%`;
  button.style.width = `${character.rect.w}%`;
  button.style.height = `${character.rect.h}%`;
  button.style.setProperty("--hotspot-glow", character.color);
  button.setAttribute("aria-label", character.label);

  const step = currentStep();
  const isIntroSpeaker = state.sceneState === SCENE_STATES.playing
    && state.activeCharacterId === character.id;
  const isTapTarget = isWaitingForTap()
    && isTapStep(step)
    && stepAcceptIds(step).includes(character.id);

  if (state.activeCharacterId === character.id) {
    button.classList.add("active");
  }
  if (isIntroSpeaker) {
    button.classList.add("intro-target");
  }
  if (isWaitingForTap()) {
    if (isTapTarget) {
      button.classList.add("task-ready", "target-pulse");
    } else if (!isBagStepActive() || character.id !== "bruno") {
      button.classList.remove("locked");
    } else {
      button.classList.add("locked");
    }
  } else {
    button.classList.add("locked");
  }

  button.addEventListener("click", () => handleTap(character.id));
  return button;
}

function createBagHotspot(prop) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "hotspot bag-hotspot";
  if (prop.hiddenHotspot) {
    button.classList.add("bag-zone-hotspot");
  }
  button.dataset.targetId = prop.id;
  button.style.left = `${prop.rect.x}%`;
  button.style.top = `${prop.rect.y}%`;
  button.style.width = `${prop.rect.w}%`;
  button.style.height = `${prop.rect.h}%`;
  button.style.setProperty("--hotspot-glow", prop.color);
  button.setAttribute("aria-label", prop.label);

  const step = currentStep();
  const isTapTarget = isWaitingForTap()
    && isTapStep(step)
    && stepAcceptIds(step).includes(prop.id);

  if (isWaitingForTap() && isTapTarget) {
    button.classList.add("task-ready", "target-pulse", "active");
  } else {
    button.classList.add("locked");
  }

  button.addEventListener("click", () => handleTap(prop.id));
  return button;
}

function renderHotspots() {
  overlay.innerHTML = "";
  scene02Config.characters.forEach((character) => {
    overlay.appendChild(createCharacterHotspot(character));
  });

  const bagStepActive = isBagStepActive();

  if (bagStepActive) {
    const orderedProps = [propById("bag-zone"), propById("bag")].filter(Boolean);
    orderedProps.forEach((prop) => {
      overlay.appendChild(createBagHotspot(prop));
    });
  }
}

function renderHud() {
  audioGate?.classList.toggle("hidden", state.sceneState !== SCENE_STATES.waitingAudio);

  const busy = state.sceneState === SCENE_STATES.playing
    || state.sceneState === SCENE_STATES.promptingTap
    || state.sceneState === SCENE_STATES.resolvingTap;

  repeatButton.disabled = state.sceneState === SCENE_STATES.idle
    || state.sceneState === SCENE_STATES.waitingAudio
    || busy;
  dictionaryButton.disabled = state.sceneState === SCENE_STATES.idle
    || state.sceneState === SCENE_STATES.waitingAudio
    || busy;
  helpButton.disabled = state.sceneState === SCENE_STATES.idle
    || state.sceneState === SCENE_STATES.waitingAudio
    || state.sceneState === SCENE_STATES.promptingTap
    || state.sceneState === SCENE_STATES.resolvingTap;

  taskPrompt.classList.toggle("pulse", isWaitingForTap());
  completeBanner.classList.add("hidden");
  nutsReveal.classList.toggle("hidden", !state.nutsRevealed);
  mapFragment.classList.toggle("hidden", !mapFragment.classList.contains("reveal"));

  updateTaskPrompt(currentStep());
  renderHotspots();
}

async function primeAudio() {
  if (state.audioUnlocked) {
    return;
  }
  state.audioUnlocked = true;
  loadVoices();

  if ("speechSynthesis" in window && window.speechSynthesis.getVoices().length === 0) {
    window.speechSynthesis.addEventListener("voiceschanged", loadVoices, { once: true });
    window.setTimeout(loadVoices, 300);
  }
}

async function playDialogueLine(line, runId) {
  if (!line || runId !== state.sequenceId) {
    return;
  }

  const character = characterById(line.characterId);
  state.activeCharacterId = line.characterId;
  state.activeLine = line;
  renderHud();
  showBubble(character, { emoji: line.emoji, textEn: line.textEn, textCz: line.textCz });

  if (line.bounceSunny) {
    const sunnyButton = overlay.querySelector('[data-target-id="sunny"]');
    sunnyButton?.classList.add("intro-target");
  }

  await playVoice({
    src: line.audio,
    text: line.textEn,
    lang: "en",
    character,
  });
  await speakCzechTranslation(line.textCz);

  if (line.revealMap) {
    revealMapEffect();
  }

  if (runId !== state.sequenceId) {
    return;
  }

  await new Promise((resolve) => window.setTimeout(resolve, 280));
  state.activeCharacterId = "";
  state.activeLine = null;
  hideBubble();
}

function maybeFinishScene() {
  if (
    state.stepIndex >= scene02Config.steps.length
    && state.sceneState !== SCENE_STATES.promptingTap
    && state.sceneState !== SCENE_STATES.waitingTap
    && state.sceneState !== SCENE_STATES.resolvingTap
  ) {
    finishScene();
  }
}

async function beginTapStep(step, runId) {
  if (runId !== state.sequenceId) {
    return;
  }

  state.sceneState = SCENE_STATES.promptingTap;
  state.activeCharacterId = "";
  state.activeLine = null;
  hideBubble();
  setBottomHint("Nejdřív poslouchej nápovědu. Potom klepni.", true);
  renderHud();
  await playVoice({
    src: step.promptAudio,
    text: step.promptEn,
    lang: "en",
    rate: 0.84,
  });
  await speakCzechTranslation(step.promptCz || step.helpCz);

  if (runId !== state.sequenceId || currentStep() !== step) {
    return;
  }

  state.sceneState = SCENE_STATES.waitingTap;
  setBottomHint("Teď klepni na správnou postavu nebo brašnu.", true);
  renderHud();
}

async function advanceScene(runId = state.sequenceId) {
  while (state.stepIndex < scene02Config.steps.length) {
    if (runId !== state.sequenceId) {
      return;
    }

    const step = currentStep();
    if (!step) {
      break;
    }

    if (step.type === "dialogue") {
      state.sceneState = SCENE_STATES.playing;
      setBottomHint("Poslouchej příběh o ztracených oříšcích.", true);
      renderHud();
      await playDialogueLine(step.line, runId);
      if (runId !== state.sequenceId) {
        return;
      }
      state.stepIndex += 1;
      continue;
    }

    if (step.type === "tap") {
      await beginTapStep(step, runId);
      return;
    }
  }

  maybeFinishScene();
}

async function runScene() {
  const runId = state.sequenceId;
  state.sceneState = SCENE_STATES.playing;
  state.stepIndex = 0;
  state.activeCharacterId = "";
  state.activeLine = null;
  state.nutsRevealed = false;
  hideBubble();
  completeBanner.classList.add("hidden");
  mapFragment.classList.remove("reveal");
  mapFragment.classList.add("hidden");
  hideNutsEffect();
  hideDictionary();
  setBottomHint("Sunny ztratila oříšky. Pomoz jí je najít.", true);
  renderHud();
  await advanceScene(runId);
}

function isCorrectTap(step, targetId) {
  return stepAcceptIds(step).includes(targetId);
}

async function handleTap(targetId) {
  if (!isWaitingForTap()) {
    return;
  }

  const step = currentStep();
  if (!step || step.type !== "tap") {
    return;
  }

  if (!isCorrectTap(step, targetId)) {
    const runId = state.sequenceId;
    state.sceneState = SCENE_STATES.resolvingTap;
    renderHud();
    await handleWrongTap(step);
    if (runId === state.sequenceId && currentStep() === step) {
      state.sceneState = SCENE_STATES.waitingTap;
      renderHud();
    }
    return;
  }

  state.sceneState = SCENE_STATES.resolvingTap;
  renderHud();

  if (step.revealNuts) {
    revealNutsEffect();
    const bag = propById("bag");
    showBubble(bag, { emoji: "🥜", textEn: "" });
    await new Promise((resolve) => window.setTimeout(resolve, 900));
  } else if (step.response) {
    const character = characterById(step.response.characterId);
    showBubble(character, { emoji: step.response.emoji, textEn: step.response.textEn, textCz: step.response.textCz });
    await playVoice({
      src: step.response.audio,
      text: step.response.textEn,
      lang: "en",
      character,
    });
    await speakCzechTranslation(step.response.textCz);
  }

  hideBubble();
  state.stepIndex += 1;
  state.sceneState = SCENE_STATES.playing;
  await advanceScene(state.sequenceId);
}

async function handleWrongTap(step) {
  hideBubble();

  await playVoice({
    src: step.wrongHintAudio || scene02Config.audio.tryAgain,
    text: step.wrongHintEn || "Try again.",
    lang: "en",
    rate: 0.86,
  });

  renderHud();
}

function finishScene() {
  state.sceneState = SCENE_STATES.complete;
  state.activeCharacterId = "";
  hideBubble();
  revealMapEffect();
  renderHud();
  setBottomHint("Hotovo! Zatím se vrať šipkou ↩ na lesní rozcestí.", true);
}

function playHelp() {
  const step = currentStep();

  return queueSpeech(async () => {
    if (!step || step.type !== "tap") {
      await speakCzechTranslation(scene02Config.mainHelp.textCz);
      return;
    }
    const playedCz = await playAudioIfExists(step.helpAudioCz);
    if (!playedCz && step.helpCz) {
      await speakCzechTranslation(step.helpCz);
    }
    await playVoice({
      src: step.promptAudio,
      text: step.helpEn || step.promptEn,
      lang: "en",
      rate: 0.84,
    });
  });
}

async function startGame() {
  primeAudio();

  if (
    state.sceneState === SCENE_STATES.idle
    || state.sceneState === SCENE_STATES.waitingAudio
    || state.sceneState === SCENE_STATES.complete
  ) {
    restartScene();
  }
}

function restartScene() {
  state.sequenceId += 1;
  cancelSpeech();
  state.speechQueue = Promise.resolve();
  state.stepIndex = 0;
  state.activeCharacterId = "";
  state.activeLine = null;
  state.nutsRevealed = false;
  completeBanner.classList.add("hidden");
  mapFragment.classList.remove("reveal");
  mapFragment.classList.add("hidden");
  hideNutsEffect();
  hideDictionary();
  runScene();
}

function handleRepeat() {
  if (isWaitingForTap()) {
    const step = currentStep();
    if (step?.type === "tap") {
      queueSpeech(async () => {
        await playVoice({
          src: step.promptAudio,
          text: step.promptEn,
          lang: "en",
          rate: 0.84,
        });
        await speakCzechTranslation(step.promptCz || step.helpCz);
      });
    }
    return;
  }

  if (state.sceneState === SCENE_STATES.complete) {
    restartScene();
  }
}

backButton.addEventListener("click", goBackToForestSignpost);
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
      const played = await playAudioIfExists(scene02Config.audio.dictionaryHelpCz);
      if (!played) {
        await speakLine({
          text: "Slovníček. Klepni na slovo a uslyšíš ho anglicky.",
          lang: "cs",
          rate: 0.88,
        });
      }
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

window.speechSynthesis?.addEventListener?.("voiceschanged", loadVoices);

setupSceneImage();
setupNutsReveal();
renderDictionary();
loadVoices();
state.sceneState = SCENE_STATES.waitingAudio;
setBottomHint("Klepni do scény a poslouchej.", true);
renderHud();
