/**
 * Scene 2 — Sunny's Lost Nuts (production web module)
 *
 * Image: scene_02_sunnys_lost_nuts_before.png (1672 x 941)
 *
 * MMTX integration:
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
const audioManifest = window.SCENE02_AUDIO_MANIFEST;

if (!audioManifest || audioManifest.schemaVersion !== 1) {
  throw new Error("Scene 2 audio manifest is missing or invalid.");
}

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
    },
    {
      id: "bunny",
      label: "Bunny",
      rect: { x: 25.0, y: 17.0, w: 13.0, h: 37.0 },
      bubble: { x: 31.0, y: 18.0 },
      color: "#ff9ec8",
      emoji: "🐰",
    },
    {
      id: "bruno",
      label: "Bruno",
      rect: { x: 44.0, y: 28.0, w: 14.0, h: 47.0 },
      bubble: { x: 49.0, y: 18.0 },
      color: "#b8895f",
      emoji: "🦡",
    },
    {
      id: "fiona",
      label: "Fiona",
      rect: { x: 62.0, y: 29.0, w: 17.0, h: 48.0 },
      bubble: { x: 68.0, y: 18.0 },
      color: "#d4a574",
      emoji: "🦊",
    },
    {
      id: "sunny",
      label: "Sunny",
      rect: { x: 81.0, y: 47.0, w: 15.0, h: 41.0 },
      bubble: { x: 86.0, y: 36.0 },
      color: "#f4c542",
      emoji: "🐿️",
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
    { en: "nuts", cz: "oříšky", emoji: "🥜" },
    { en: "map", cz: "mapa", emoji: "🗺️" },
    { en: "carrot", cz: "mrkev", emoji: "🥕" },
    { en: "bag", cz: "brašna", emoji: "🎒" },
    { en: "I have", cz: "mám", emoji: "✅" },
    { en: "I don't have", cz: "nemám", emoji: "❌" },
    { en: "Do you have?", cz: "máš?", emoji: "❓" },
    { en: "Does he have?", cz: "má on?", emoji: "❓" },
    { en: "Look inside", cz: "podívej se dovnitř", emoji: "👀" },
    { en: "ready", cz: "připravený", emoji: "✅" },
    { en: "wait", cz: "počkat", emoji: "✋" },
    { en: "happy", cz: "šťastný", emoji: "😊" },
  ],
  steps: [
    {
      type: "dialogue",
      line: {
        characterId: "sunny",
        textEn: "Oh no! I don't have my nuts!",
        textCz: "Ach ne! Nemám svoje oříšky!",
        emoji: "😢",
      },
    },
    {
      type: "dialogue",
      line: {
        characterId: "fiona",
        textEn: "Benji, do you have nuts?",
        textCz: "Benji, máš oříšky?",
        emoji: "❓",
      },
    },
    {
      type: "tap",
      targetId: "benji",
      promptEmoji: "🐶",
      promptEn: "Tap Benji. Does he have nuts?",
      promptCz: "Klepni na Benjiho. Má oříšky?",
      helpCz: "Klepni na Benjiho. Má oříšky?",
      helpEn: "Tap Benji. Does he have nuts?",
      wrongHintEn: "Not yet. Tap Benji.",
      response: {
        characterId: "benji",
        textEn: "No. I have a map.",
        textCz: "Ne. Mám mapu.",
        emoji: "🗺️",
      },
    },
    {
      type: "dialogue",
      line: {
        characterId: "fiona",
        textEn: "Bunny, do you have nuts?",
        textCz: "Bunny, máš oříšky?",
        emoji: "❓",
      },
    },
    {
      type: "tap",
      targetId: "bunny",
      promptEmoji: "🐰",
      promptEn: "Tap Bunny. Does he have nuts?",
      promptCz: "Klepni na Bunnyho. Má oříšky?",
      helpCz: "Klepni na Bunny. Má oříšky?",
      helpEn: "Tap Bunny. Does he have nuts?",
      wrongHintEn: "Not yet. Tap Bunny.",
      response: {
        characterId: "bunny",
        textEn: "No. I have a carrot.",
        textCz: "Ne. Mám mrkev.",
        emoji: "🥕",
      },
    },
    {
      type: "dialogue",
      line: {
        characterId: "bruno",
        textEn: "Wait a second. I have a bag.",
        textCz: "Počkejte chvilku. Mám brašnu.",
        emoji: "🎒",
      },
    },
    {
      type: "dialogue",
      line: {
        characterId: "bruno",
        textEn: "It is big. Look inside, friends!",
        textCz: "Je velká. Podívejte se dovnitř, kamarádi!",
        emoji: "👀",
      },
    },
    {
      type: "tap",
      targetId: "bag",
      acceptIds: ["bag", "bag-zone"],
      promptEmoji: "🎒",
      promptEn: "Tap the bag.",
      promptCz: "Klepni na brašnu.",
      helpCz: "Klepni na brašnu.",
      helpEn: "Tap the bag.",
      wrongHintEn: "Look at the bag.",
      revealNuts: true,
    },
    {
      type: "dialogue",
      line: {
        characterId: "sunny",
        textEn: "My nuts! I am so happy!",
        textCz: "Moje oříšky! Mám takovou radost!",
        emoji: "🎉",
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
        revealMap: true,
      },
    },
  ],
  audio: {
    volume: 0.78,
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

function cancelSpeech() {
  if (state.currentAudio) {
    state.currentAudio.pause();
    state.currentAudio = null;
  }
}

function goBackToForestSignpost() {
  window.location.href = "../index.html?scene=intro4";
}

function goToScene03() {
  window.location.href = "../scene03_journey_to_the_lake/index.html";
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

function fixedAudioPath(text, lang, speakerId) {
  const key = `${speakerId}::${text}`;
  const path = audioManifest.dialogue?.[lang]?.[key];
  if (!path) {
    throw new Error(`Missing Scene 2 audio manifest entry: ${lang} ${key}`);
  }
  return `${path}?v=${audioManifest.version}`;
}

async function playVoice({ text, lang = "en", character, speakerId = "ui" }) {
  if (!text) {
    return;
  }
  const resolvedSpeakerId = character?.id || speakerId;
  const src = fixedAudioPath(text, lang, resolvedSpeakerId);
  const played = await playAudioIfExists(src);
  if (!played) {
    console.error(`Scene 2 fixed audio could not be played: ${src}`);
  }
}

async function speakCzechTranslation(text, speakerId = "ui") {
  await playVoice({ text, lang: "cs", speakerId });
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
          text: item.en,
          lang: "en",
          speakerId: "dictionary",
        });
        await playVoice({
          text: item.cz,
          lang: "cs",
          speakerId: "dictionary",
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

function createQuickSkipButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "scene-quick-skip";
  button.setAttribute("aria-label", "Přeskočit na cestu k jezeru");
  const skipToLake = (event) => {
    event.preventDefault();
    event.stopPropagation();
    goToScene03();
  };
  button.addEventListener("pointerdown", skipToLake);
  button.addEventListener("touchstart", skipToLake, { passive: false });
  button.addEventListener("click", skipToLake);
  return button;
}

function renderHotspots() {
  overlay.innerHTML = "";
  overlay.appendChild(createQuickSkipButton());
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
  if (state.sceneState === SCENE_STATES.complete) {
    completeBanner.classList.remove("hidden");
    completeBanner.querySelector(".complete-text").textContent = "Next: Journey to the Lake";
  } else {
    completeBanner.classList.add("hidden");
  }
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
    text: line.textEn,
    lang: "en",
    character,
  });
  await speakCzechTranslation(line.textCz, line.characterId);

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
    text: step.promptEn,
    lang: "en",
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
      text: step.response.textEn,
      lang: "en",
      character,
    });
    await speakCzechTranslation(step.response.textCz, step.response.characterId);
  }

  hideBubble();
  state.stepIndex += 1;
  state.sceneState = SCENE_STATES.playing;
  await advanceScene(state.sequenceId);
}

async function handleWrongTap(step) {
  hideBubble();

  await playVoice({
    text: step.wrongHintEn || "Try again.",
    lang: "en",
  });

  renderHud();
}

function finishScene() {
  state.sceneState = SCENE_STATES.complete;
  state.activeCharacterId = "";
  hideBubble();
  revealMapEffect();
  renderHud();
  setBottomHint("Hotovo! Klepni na spodní bublinu a pokračuj k jezeru.", true);
}

function playHelp() {
  const step = currentStep();

  return queueSpeech(async () => {
    if (!step || step.type !== "tap") {
      await speakCzechTranslation(scene02Config.mainHelp.textCz);
      return;
    }
    await speakCzechTranslation(step.helpCz);
    await playVoice({
      text: step.helpEn || step.promptEn,
      lang: "en",
    });
  });
}

async function startGame() {
  await primeAudio();

  if (
    state.sceneState === SCENE_STATES.idle
    || state.sceneState === SCENE_STATES.waitingAudio
    || state.sceneState === SCENE_STATES.complete
  ) {
    setBottomHint("Nejdřív poslouchej českou nápovědu.", true);
    renderHud();
    await playHelp();
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

function quickAdvanceScene() {
  goToScene03();
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

function handleRepeat() {
  if (isWaitingForTap()) {
    const step = currentStep();
    if (step?.type === "tap") {
      queueSpeech(async () => {
        await playVoice({
          text: step.promptEn,
          lang: "en",
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
completeBanner.addEventListener("click", () => {
  if (state.sceneState === SCENE_STATES.complete) {
    goToScene03();
  }
});
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
      await playVoice({
        text: "Slovníček. Klepni na slovo a uslyšíš ho anglicky.",
        lang: "cs",
      });
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

function handleQuickSkipCorner(event) {
  if (!isQuickSkipCornerClick(event, scene)) {
    return;
  }
  event.preventDefault();
  event.stopImmediatePropagation();
  goToScene03();
}

scene.addEventListener("pointerdown", handleQuickSkipCorner, true);
scene.addEventListener("touchstart", handleQuickSkipCorner, { capture: true, passive: false });
scene.addEventListener("click", handleQuickSkipCorner, true);

setupSceneImage();
setupNutsReveal();
renderDictionary();
state.sceneState = SCENE_STATES.waitingAudio;
setBottomHint("Klepni do scény a poslouchej.", true);
renderHud();
