const storyStage = document.getElementById("storyStage");
const sceneImage = document.getElementById("sceneImage");
const magnifierButton = document.getElementById("magnifierButton");
const clickPrompt = document.getElementById("clickPrompt");
const mushroomPortalButton = document.getElementById("mushroomPortalButton");
const bunnyPortalButton = document.getElementById("bunnyPortalButton");
const mushroomHud = document.getElementById("mushroomHud");
const backToSignpostButton = document.getElementById("backToSignpostButton");
const mushroomHelpButton = document.getElementById("mushroomHelpButton");
const colorsModeButton = document.getElementById("colorsModeButton");
const numbersModeButton = document.getElementById("numbersModeButton");
const mushroomOverlay = document.getElementById("mushroomOverlay");
const dialogueHud = document.getElementById("dialogueHud");
const backFromDialogueButton = document.getElementById("backFromDialogueButton");
const dialoguePanel = document.getElementById("dialoguePanel");
const dialogueHelpButton = document.getElementById("dialogueHelpButton");
const dialogueDoorButton = document.getElementById("dialogueDoorButton");
const owlGardenHud = document.getElementById("owlGardenHud");
const backFromOwlGardenButton = document.getElementById("backFromOwlGardenButton");
const owlGardenHelpButton = document.getElementById("owlGardenHelpButton");
const owlGardenOverlay = document.getElementById("owlGardenOverlay");
const owlGardenPrompt = document.getElementById("owlGardenPrompt");
const owlGardenThumbButton = document.getElementById("owlGardenThumbButton");
const owlGardenDoneBadge = document.getElementById("owlGardenDoneBadge");

const scenes = {
  intro1: {
    image: "intro1.png?v=20260402b",
  },
  intro2: {
    image: "intro2.png?v=20260402b",
  },
  intro3: {
    image: "intro3.png?v=20260402b",
  },
  intro4: {
    image: "intro4.png?v=20260402b",
  },
  mushrooms: {
    image: "scene.jpg?v=20260402b",
  },
  benjiBunny: {
    image: "BenjiBunnyScene.png?v=20260403b",
  },
  owlGarden: {
    image: "MeetingOul1.PNG?v=20260404b",
  },
  houseBunny: {
    image: "HouseBunny1.PNG?v=20260409a",
  },
};

const numberWords = {
  1: "One",
  2: "Two",
  3: "Three",
  4: "Four",
  5: "Five",
};

const colorHotspots = [
  { id: "red", word: "Red", color: "#ff6464", rect: { x: 2.5, y: 21.5, w: 26.4, h: 26.8 } },
  { id: "blue", word: "Blue", color: "#5f8bff", rect: { x: 26.7, y: 45.6, w: 10.1, h: 18.9 } },
  { id: "green", word: "Green", color: "#6ed76a", rect: { x: 58.0, y: 53.4, w: 18.4, h: 18.5 } },
  { id: "orange", word: "Orange", color: "#ffb14f", rect: { x: 73.6, y: 30.1, w: 21.8, h: 21.2 } },
];

const numberHotspots = [
  { id: "red_1", group: "red", color: "#ff6464", rect: { x: 6.5, y: 29.3, w: 18.2, h: 10.4 }, label: { x: 15.6, y: 38.4 } },
  { id: "red_2", group: "red", color: "#ff6464", rect: { x: 4.7, y: 61.5, w: 8.3, h: 7.8 }, label: { x: 7.2, y: 69.1 } },
  { id: "blue_1", group: "blue", color: "#5f8bff", rect: { x: 28.6, y: 49.1, w: 7.2, h: 9.2 }, label: { x: 32.2, y: 56.0 } },
  { id: "blue_2", group: "blue", color: "#5f8bff", rect: { x: 26.2, y: 73.0, w: 5.2, h: 7.0 }, label: { x: 28.6, y: 80.0 } },
  { id: "blue_3", group: "blue", color: "#5f8bff", rect: { x: 33.2, y: 71.6, w: 4.8, h: 8.2 }, label: { x: 35.0, y: 75.3 } },
  { id: "green_1", group: "green", color: "#6ed76a", rect: { x: 61.7, y: 65.2, w: 7.8, h: 7.8 }, label: { x: 65.6, y: 74.8 } },
  { id: "green_2", group: "green", color: "#6ed76a", rect: { x: 57.7, y: 78.5, w: 5.9, h: 6.9 }, label: { x: 59.9, y: 84.6 } },
  { id: "green_3", group: "green", color: "#6ed76a", rect: { x: 67.3, y: 78.5, w: 5.9, h: 6.7 }, label: { x: 69.9, y: 85.1 } },
  { id: "green_4", group: "green", color: "#6ed76a", rect: { x: 64.2, y: 82.4, w: 6.2, h: 6.0 }, label: { x: 67.0, y: 89.2 } },
  { id: "orange_1", group: "orange", color: "#ffb14f", rect: { x: 75.0, y: 38.3, w: 10.0, h: 4.4 }, label: { x: 79.5, y: 42.3 } },
  { id: "orange_2", group: "orange", color: "#ffb14f", rect: { x: 87.2, y: 46.7, w: 6.4, h: 3.5 }, label: { x: 90.4, y: 49.1 } },
  { id: "orange_3", group: "orange", color: "#ffb14f", rect: { x: 75.2, y: 53.3, w: 10.5, h: 4.4 }, label: { x: 80.5, y: 56.2 } },
  { id: "orange_4", group: "orange", color: "#ffb14f", rect: { x: 88.2, y: 58.6, w: 8.8, h: 3.9 }, label: { x: 91.2, y: 61.4 } },
  { id: "orange_5", group: "orange", color: "#ffb14f", rect: { x: 75.2, y: 65.8, w: 16.4, h: 6.2 }, label: { x: 83.8, y: 67.3 } },
];

const owlGardenGroups = [
  {
    id: "apples",
    word: "Apples",
    objectWord: "apples",
    colorWord: "purple",
    correctCount: 7,
    color: "#a35cff",
    wordRect: { x: 52.0, y: 24.2, w: 13.6, h: 7.2 },
  },
  {
    id: "sunflowers",
    word: "Sunflowers",
    objectWord: "sunflowers",
    colorWord: "yellow",
    correctCount: 6,
    color: "#f0bf36",
    wordRect: { x: 36.4, y: 33.2, w: 17.4, h: 7.2 },
  },
  {
    id: "pigs",
    word: "Pigs",
    objectWord: "pigs",
    colorWord: "pink",
    correctCount: 8,
    color: "#f48aa8",
    wordRect: { x: 65.8, y: 45.6, w: 14.4, h: 7.2 },
  },
];

const owlGardenNumberWords = {
  1: "one",
  2: "two",
  3: "three",
  4: "four",
  5: "five",
  6: "six",
  7: "seven",
  8: "eight",
};

const owlGardenOutroDialogue = [
  {
    id: 1,
    speaker: "Benji",
    cssClass: "benji",
    preferredVoiceName: "fable",
    textEn: "Bunny, do you remember the colors? Yellow, purple, pink...",
    audioEn: "audio/english/owl_garden_08_benji_do_you_remember_colors_en.mp3?v=20260409a",
    audioCz: "audio/czech/owl_garden_08_benji_do_you_remember_colors_cz.m4a?v=20260409a",
  },
  {
    id: 2,
    speaker: "Bunny",
    cssClass: "bunny",
    preferredVoiceName: "echo",
    textEn: "Yes. But we can train all colors in my house. Let's go.",
    audioEn: "audio/english/owl_garden_09_bunny_we_can_train_all_colors_en.mp3?v=20260409a",
    audioCz: "audio/czech/owl_garden_09_bunny_we_can_train_all_colors_cz.m4a?v=20260409a",
  },
];

const benjiBunnyDebugSkipRect = { x: 0, y: 76, w: 16, h: 24 };
const owlGardenDebugSkipRect = { x: 0, y: 76, w: 16, h: 24 };

const state = {
  currentScene: "intro1",
  sequenceId: 0,
  timeouts: [],
  audioContext: null,
  crackleTimerId: null,
  currentVoiceAudio: null,
  currentSpeechUtterance: null,
  currentSpeechResolve: null,
  audioUnlocked: false,
  mushroomMode: "colors",
  activeHotspotId: "",
  revealedNumbers: {},
  mushroomResetTimeoutId: null,
  visibleDialogueCount: 0,
  dialoguePhase: "intro",
  dialogueClickedIds: new Set(),
  dialogueDoorState: "hidden",
  owlGardenPhase: "intro",
  owlGardenActiveId: "",
  owlGardenCompletedIds: new Set(),
  owlGardenCurrentNumbers: {},
  owlGardenLockedNumbers: {},
  owlGardenHelpPlayed: false,
  owlGardenOutroVisibleCount: 0,
  groupCounts: {
    red: 0,
    blue: 0,
    green: 0,
    orange: 0,
  },
};

const manualAudio = {
  intro2_short: {
    src: "audio/intro2_short.m4a",
    text: "Jestli me uz znas, jdeme objevovat, tak klikni na lupu.",
    lang: "cs-CZ",
  },
  intro2_long_1: {
    src: "audio/intro2_long_1.m4a",
    text: "Ahoj, ja jsem Benzi. Tvuj dedecek je muj pritel a pozadal me, abych ti pomohl objevovat novy svet.",
    lang: "cs-CZ",
  },
  intro2_long_2: {
    src: "audio/intro2_long_2.m4a",
    text: "Svet, kde se mluvi anglicky. To je rec, se kterou se pak domluvis skoro vsude, kam pujdes.",
    lang: "cs-CZ",
  },
  intro2_long_3: {
    src: "audio/intro2_long_3.m4a",
    text: "Pojdme na to.",
    lang: "cs-CZ",
  },
  intro3_line: {
    src: "audio/intro3_line.m4a",
    text: "Zacneme v mem rodnem lese.",
    lang: "cs-CZ",
  },
  mushrooms_colors_intro: {
    src: "audio/mushrooms_colors_intro.m4a",
    text: "Klikej na houby a poslouchej barvy.",
    lang: "cs-CZ",
  },
  mushrooms_numbers_intro: {
    src: "audio/mushrooms_numbers_intro.m4a",
    text: "Klikej na houby a pocitej.",
    lang: "cs-CZ",
  },
};

const benjiBunnyDialogue = [
  { id: 1, speaker: "Benji", cssClass: "benji", textEn: "Hello.", audioEn: "audio/english/benji_bunny_01_benji_hello_en.mp3", audioCz: "audio/czech/benji_bunny_01_benji_hello_cz.m4a" },
  { id: 2, speaker: "Bunny", cssClass: "bunny", textEn: "Hello.", audioEn: "audio/english/benji_bunny_02_bunny_hello_en.mp3", audioCz: "audio/czech/benji_bunny_02_bunny_hello_cz.m4a" },
  { id: 3, speaker: "Benji", cssClass: "benji", textEn: "I am Benji.", audioEn: "audio/english/benji_bunny_03_benji_i_am_benji_en.mp3", audioCz: "audio/czech/benji_bunny_03_benji_i_am_benji_cz.m4a" },
  { id: 4, speaker: "Bunny", cssClass: "bunny", textEn: "I am Bunny.", audioEn: "audio/english/benji_bunny_04_bunny_i_am_bunny_en.mp3", audioCz: "audio/czech/benji_bunny_04_bunny_i_am_bunny_cz.m4a" },
  { id: 5, speaker: "Benji", cssClass: "benji", textEn: "We can be friends.", audioEn: "audio/english/benji_bunny_05_benji_we_can_be_friends_en.mp3", audioCz: "audio/czech/benji_bunny_05_benji_we_can_be_friends_cz.m4a" },
  { id: 6, speaker: "Bunny", cssClass: "bunny", textEn: "Yes, we can.", audioEn: "audio/english/benji_bunny_06_bunny_yes_we_can_en.mp3", audioCz: "audio/czech/benji_bunny_06_bunny_yes_we_can_cz.m4a" },
  { id: 7, speaker: "Benji", cssClass: "benji", textEn: "Where do we go?", audioEn: "audio/english/benji_bunny_07_benji_where_do_we_go_en.mp3", audioCz: "audio/czech/benji_bunny_07_benji_where_do_we_go_cz.m4a" },
  { id: 8, speaker: "Bunny", cssClass: "bunny", textEn: "We go to my house. OK?", audioEn: "audio/english/benji_bunny_08_bunny_we_go_to_my_house_ok_en.mp3", audioCz: "audio/czech/benji_bunny_08_bunny_we_go_to_my_house_ok_cz.m4a" },
  { id: 9, speaker: "Benji", cssClass: "benji", textEn: "OK. Let's go.", audioEn: "audio/english/benji_bunny_09_benji_ok_lets_go_en.mp3", audioCz: "audio/czech/benji_bunny_09_benji_ok_lets_go_cz.m4a" },
];

const benjiBunnyHelpAudio = {
  intro: "audio/czech/benji_bunny_scene_help_cz1.m4a",
};

function clearSceneTimers() {
  state.timeouts.forEach((timeoutId) => window.clearTimeout(timeoutId));
  state.timeouts = [];
}

function pauseMs(delayMs) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, delayMs);
  });
}

function clearMushroomResetTimeout() {
  if (state.mushroomResetTimeoutId) {
    window.clearTimeout(state.mushroomResetTimeoutId);
    state.mushroomResetTimeoutId = null;
  }
}

function schedule(callback, delayMs) {
  const timeoutId = window.setTimeout(callback, delayMs);
  state.timeouts.push(timeoutId);
  return timeoutId;
}

function isSceneActive(sceneName, sequenceId) {
  return state.currentScene === sceneName && state.sequenceId === sequenceId;
}

function cancelSpeech() {
  if ("speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
  if (state.currentSpeechResolve) {
    const resolve = state.currentSpeechResolve;
    state.currentSpeechResolve = null;
    state.currentSpeechUtterance = null;
    resolve();
  }
  if (state.currentVoiceAudio) {
    const activeAudio = state.currentVoiceAudio;
    state.currentVoiceAudio = null;
    if (typeof activeAudio._finishPlayback === "function") {
      activeAudio._finishPlayback();
      activeAudio._finishPlayback = null;
    }
    activeAudio.pause();
    activeAudio.currentTime = 0;
  }
}

function unlockAudio() {
  state.audioUnlocked = true;
  resumeAudioContext();
}
function playAudioElement(audio) {
  return new Promise((resolve) => {
    cancelSpeech();
    let resolved = false;
    const finish = () => {
      if (resolved) {
        return;
      }
      resolved = true;
      audio._finishPlayback = null;
      resolve();
    };

    audio._finishPlayback = finish;
    audio.onended = finish;
    audio.onerror = () => {
      state.currentVoiceAudio = null;
      finish();
    };

    state.currentVoiceAudio = audio;
    audio.currentTime = 0;
    const playPromise = audio.play();
    if (playPromise && typeof playPromise.then === "function") {
      playPromise.catch((error) => {
        state.currentVoiceAudio = null;
        finish();
      });
    }
  });
}

async function playAudioFile(src) {
  if (!state.audioUnlocked || !src) {
    return;
  }
  const audio = new Audio(src);
  audio.preload = "auto";
  await playAudioElement(audio);
}

async function playAudioFileIfAvailable(src) {
  if (!state.audioUnlocked || !src) {
    return false;
  }
  try {
    const response = await fetch(src, { method: "HEAD", cache: "no-store" });
    if (!response.ok) {
      return false;
    }
  } catch (error) {
    return false;
  }
  const audio = new Audio(src);
  audio.preload = "auto";
  await playAudioElement(audio);
  return true;
}

async function speakCue(cueKey) {
  const cue = manualAudio[cueKey];
  if (!cue) {
    return;
  }
  if (!state.audioUnlocked) {
    return;
  }
  const audio = new Audio(cue.src);
  audio.preload = "auto";
  await playAudioElement(audio);
}

function speakEnglish(text) {
  void speakEnglishLine(text);
}

function pickEnglishVoice(preferredNameFragment = "") {
  const voices = window.speechSynthesis?.getVoices?.() ?? [];
  const englishVoices = voices.filter((voice) => voice.lang && voice.lang.toLowerCase().startsWith("en"));
  if (preferredNameFragment) {
    const preferredNames = preferredNameFragment
      .split("|")
      .map((item) => item.trim().toLowerCase())
      .filter(Boolean);
    for (const preferredName of preferredNames) {
      const preferred = englishVoices.find((voice) => voice.name.toLowerCase().includes(preferredName));
      if (preferred) {
        return preferred;
      }
    }
  }
  return englishVoices[0] ?? null;
}

function speakEnglishLine(text, options = {}) {
  if (!("speechSynthesis" in window) || !state.audioUnlocked) {
    return Promise.resolve();
  }

  window.speechSynthesis.cancel();
  return new Promise((resolve) => {
    state.currentSpeechResolve = resolve;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = options.rate ?? 0.86;
    utterance.pitch = options.pitch ?? 1.0;

    const englishVoice = pickEnglishVoice(options.preferredVoiceName ?? "");
    if (englishVoice) {
      utterance.voice = englishVoice;
    }

    const finish = () => {
      if (state.currentSpeechResolve !== resolve) {
        return;
      }
      state.currentSpeechResolve = null;
      state.currentSpeechUtterance = null;
      resolve();
    };

    utterance.onend = finish;
    utterance.onerror = finish;
    state.currentSpeechUtterance = utterance;
    window.speechSynthesis.speak(utterance);
  });
}

function ensureAudioContext() {
  if (!window.AudioContext && !window.webkitAudioContext) {
    return null;
  }
  if (!state.audioContext) {
    const Context = window.AudioContext || window.webkitAudioContext;
    state.audioContext = new Context();
  }
  return state.audioContext;
}

async function resumeAudioContext() {
  const audioContext = ensureAudioContext();
  if (!audioContext) {
    return null;
  }
  if (audioContext.state !== "running") {
    try {
      await audioContext.resume();
    } catch (error) {
      return audioContext;
    }
  }
  return audioContext;
}

function playCrackleBurst(audioContext) {
  const duration = 0.045 + Math.random() * 0.08;
  const sampleCount = Math.max(1, Math.floor(audioContext.sampleRate * duration));
  const buffer = audioContext.createBuffer(1, sampleCount, audioContext.sampleRate);
  const channel = buffer.getChannelData(0);

  for (let index = 0; index < sampleCount; index += 1) {
    const fade = 1 - index / sampleCount;
    channel[index] = (Math.random() * 2 - 1) * fade * (0.45 + Math.random() * 0.65);
  }

  const source = audioContext.createBufferSource();
  source.buffer = buffer;

  const filter = audioContext.createBiquadFilter();
  filter.type = "bandpass";
  filter.frequency.value = 1100 + Math.random() * 1500;
  filter.Q.value = 0.7;

  const gain = audioContext.createGain();
  gain.gain.setValueAtTime(0.0001, audioContext.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.018 + Math.random() * 0.03, audioContext.currentTime + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + duration);

  source.connect(filter);
  filter.connect(gain);
  gain.connect(audioContext.destination);
  source.start();
  source.stop(audioContext.currentTime + duration);
}

async function startCrackle() {
  const audioContext = await resumeAudioContext();
  if (!audioContext || audioContext.state !== "running") {
    return;
  }
  stopCrackle();
  state.crackleTimerId = window.setInterval(() => {
    if (Math.random() < 0.5) {
      playCrackleBurst(audioContext);
    }
  }, 180);
}

function stopCrackle() {
  if (state.crackleTimerId) {
    window.clearInterval(state.crackleTimerId);
    state.crackleTimerId = null;
  }
}

function renderScene() {
  const scene = scenes[state.currentScene];
  const owlGardenOutro = state.currentScene === "owlGarden" && state.owlGardenPhase === "outro";
  sceneImage.src = owlGardenOutro ? "MeetingOul2.PNG?v=20260409b" : scene.image;
  magnifierButton.classList.toggle("hidden", state.currentScene !== "intro2");
  clickPrompt.classList.toggle("hidden", state.audioUnlocked || state.currentScene === "intro4" || state.currentScene === "benjiBunny" || state.currentScene === "owlGarden" || state.currentScene === "houseBunny");
  mushroomPortalButton.classList.toggle("hidden", state.currentScene !== "intro4");
  bunnyPortalButton.classList.toggle("hidden", state.currentScene !== "intro4");
  mushroomHud.classList.toggle("hidden", state.currentScene !== "mushrooms");
  mushroomOverlay.classList.toggle("hidden", state.currentScene !== "mushrooms");
  dialogueHud.classList.toggle("hidden", state.currentScene !== "benjiBunny");
  dialoguePanel.classList.toggle("hidden", state.currentScene !== "benjiBunny");
  owlGardenHud.classList.toggle("hidden", state.currentScene !== "owlGarden");
  owlGardenHelpButton.classList.toggle("hidden", state.currentScene !== "owlGarden" || state.owlGardenPhase !== "play");
  owlGardenHelpButton.classList.toggle("pulse-soft", state.currentScene === "owlGarden" && state.owlGardenPhase === "play");
  owlGardenOverlay.classList.toggle("hidden", state.currentScene !== "owlGarden");
  owlGardenPrompt.classList.toggle("hidden", state.currentScene !== "owlGarden" || state.owlGardenPhase === "outro");
  owlGardenThumbButton.classList.toggle("hidden", state.currentScene !== "owlGarden" || state.owlGardenPhase !== "play" || (!state.owlGardenHelpPlayed && !state.owlGardenActiveId));
  owlGardenThumbButton.classList.toggle("pulse-soft", state.currentScene === "owlGarden" && state.owlGardenPhase === "play" && !!state.owlGardenActiveId);
  owlGardenDoneBadge.classList.toggle("hidden", true);
  dialogueDoorButton.classList.toggle("hidden", state.currentScene !== "benjiBunny" || state.dialogueDoorState === "hidden");
  dialogueDoorButton.classList.toggle("ready-final", state.currentScene === "benjiBunny" && state.dialogueDoorState === "green");
  dialogueDoorButton.classList.toggle("pulse-soft", state.currentScene === "benjiBunny" && state.dialogueDoorState !== "hidden");
  dialogueHelpButton.classList.toggle("hidden", state.currentScene !== "benjiBunny" || state.dialoguePhase === "intro" || state.dialogueDoorState !== "hidden");
  dialogueHelpButton.classList.toggle("pulse-soft", state.currentScene === "benjiBunny" && state.dialoguePhase !== "intro");
  if (state.currentScene === "mushrooms") {
    renderMushrooms();
  } else {
    mushroomOverlay.innerHTML = "";
  }
  if (state.currentScene === "benjiBunny") {
    renderBenjiBunnyDialogue();
  } else {
    dialoguePanel.innerHTML = "";
  }
  if (state.currentScene === "owlGarden") {
    renderOwlGarden();
  } else {
    owlGardenOverlay.innerHTML = "";
  }
}

function cleanupCurrentScene() {
  clearSceneTimers();
  clearMushroomResetTimeout();
  cancelSpeech();
  stopCrackle();
}

function setScene(sceneName) {
  cleanupCurrentScene();
  state.currentScene = sceneName;
  state.sequenceId += 1;
  renderScene();
  const sequenceId = state.sequenceId;

  if (sceneName === "intro1") {
    runIntro1(sequenceId);
  } else if (sceneName === "intro2") {
    runIntro2(sequenceId);
  } else if (sceneName === "intro3") {
    runIntro3(sequenceId);
  } else if (sceneName === "intro4") {
    runIntro4(sequenceId);
  } else if (sceneName === "mushrooms") {
    runMushrooms(sequenceId);
  } else if (sceneName === "benjiBunny") {
    runBenjiBunny(sequenceId);
  } else if (sceneName === "owlGarden") {
    runOwlGarden(sequenceId);
  }
}

async function runIntro1(sequenceId) {
  startCrackle();
}

async function runIntro2(sequenceId) {
  await speakCue("intro2_short");
  if (!isSceneActive("intro2", sequenceId)) {
    return;
  }

  schedule(async () => {
    if (!isSceneActive("intro2", sequenceId)) {
      return;
    }
    await speakCue("intro2_long_1");
    if (!isSceneActive("intro2", sequenceId)) {
      return;
    }
    await speakCue("intro2_long_2");
    if (!isSceneActive("intro2", sequenceId)) {
      return;
    }
    await speakCue("intro2_long_3");
    if (!isSceneActive("intro2", sequenceId)) {
      return;
    }
    setScene("intro3");
  }, 3000);
}

async function runIntro3(sequenceId) {
  await speakCue("intro3_line");
  if (!isSceneActive("intro3", sequenceId)) {
    return;
  }
  schedule(() => {
    if (isSceneActive("intro3", sequenceId)) {
      setScene("intro4");
    }
  }, 2000);
}

function runIntro4(sequenceId) {
  if (!isSceneActive("intro4", sequenceId)) {
    return;
  }
}

function resetMushrooms() {
  clearMushroomResetTimeout();
  state.mushroomMode = "colors";
  state.activeHotspotId = "";
  state.revealedNumbers = {};
  state.groupCounts = { red: 0, blue: 0, green: 0, orange: 0 };
}

function currentMushroomHotspots() {
  return state.mushroomMode === "colors" ? colorHotspots : numberHotspots;
}

function renderMushrooms() {
  mushroomOverlay.innerHTML = "";

  colorsModeButton.classList.toggle("active", state.mushroomMode === "colors");
  numbersModeButton.classList.toggle("active", state.mushroomMode === "numbers");

  currentMushroomHotspots().forEach((hotspot) => {
    mushroomOverlay.appendChild(createHotspotButton(hotspot));
  });

  if (state.mushroomMode === "numbers") {
    numberHotspots.forEach((hotspot) => {
      const numberValue = state.revealedNumbers[hotspot.id];
      if (numberValue) {
        mushroomOverlay.appendChild(createNumberTag(hotspot, numberValue));
      }
    });
  }
}

function createHotspotButton(hotspot) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "hotspot";
  if (state.activeHotspotId === hotspot.id) {
    button.classList.add("active");
  }
  button.style.left = `${hotspot.rect.x}%`;
  button.style.top = `${hotspot.rect.y}%`;
  button.style.width = `${hotspot.rect.w}%`;
  button.style.height = `${hotspot.rect.h}%`;
  button.style.setProperty("--hotspot-glow", hotspot.color);
  button.setAttribute("aria-label", hotspot.id);
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    activateMushroomHotspot(hotspot);
  });
  return button;
}

function createNumberTag(hotspot, numberValue) {
  const tag = document.createElement("div");
  tag.className = "number-tag";
  tag.textContent = String(numberValue);
  tag.style.left = `${hotspot.label.x}%`;
  tag.style.top = `${hotspot.label.y}%`;
  return tag;
}

function activateMushroomHotspot(hotspot) {
  state.activeHotspotId = hotspot.id;

  if (state.mushroomMode === "colors") {
    speakEnglish(hotspot.word);
    renderMushrooms();
    return;
  }

  let numberValue = state.revealedNumbers[hotspot.id];
  if (!numberValue) {
    state.groupCounts[hotspot.group] += 1;
    numberValue = state.groupCounts[hotspot.group];
    state.revealedNumbers[hotspot.id] = numberValue;
  }

  speakEnglish(numberWords[numberValue] ?? String(numberValue));
  renderMushrooms();

  if (Object.keys(state.revealedNumbers).length === numberHotspots.length) {
    clearMushroomResetTimeout();
    state.mushroomResetTimeoutId = window.setTimeout(() => {
      if (state.currentScene !== "mushrooms" || state.mushroomMode !== "numbers") {
        return;
      }
      state.activeHotspotId = "";
      state.revealedNumbers = {};
      state.groupCounts = { red: 0, blue: 0, green: 0, orange: 0 };
      renderMushrooms();
    }, 1500);
  }
}

function setMushroomMode(mode) {
  clearMushroomResetTimeout();
  state.mushroomMode = mode;
  state.activeHotspotId = "";
  state.revealedNumbers = {};
  state.groupCounts = { red: 0, blue: 0, green: 0, orange: 0 };
  if (state.currentScene === "mushrooms") {
    renderMushrooms();
  }
}

function runMushrooms(sequenceId) {
  if (!isSceneActive("mushrooms", sequenceId)) {
    return;
  }
  renderMushrooms();
}

function resetBenjiBunnyDialogue() {
  state.visibleDialogueCount = 0;
  state.dialoguePhase = "intro";
  state.dialogueClickedIds = new Set();
  state.dialogueDoorState = "hidden";
}

function resetOwlGarden() {
  state.owlGardenPhase = "intro";
  state.owlGardenActiveId = "";
  state.owlGardenCompletedIds = new Set();
  state.owlGardenCurrentNumbers = {};
  state.owlGardenLockedNumbers = {};
  state.owlGardenHelpPlayed = false;
  state.owlGardenOutroVisibleCount = 0;
}

function renderBenjiBunnyDialogue() {
  dialoguePanel.innerHTML = "";
  dialoguePanel.appendChild(createBenjiBunnyDebugSkipButton());
  let benjiIndex = 0;
  let bunnyIndex = 0;
  benjiBunnyDialogue.slice(0, state.visibleDialogueCount).forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `dialogue-card ${item.cssClass}`;
    if (state.dialogueClickedIds.has(item.id)) {
      button.classList.add("done");
    }

    if (item.speaker === "Benji") {
      button.style.left = "22px";
      button.style.top = `${104 + benjiIndex * 58}px`;
      benjiIndex += 1;
    } else {
      button.style.right = "22px";
      button.style.top = `${104 + bunnyIndex * 58}px`;
      bunnyIndex += 1;
    }

    const speaker = document.createElement("span");
    speaker.className = "dialogue-speaker";
    speaker.textContent = `${item.speaker}:`;

    const line = document.createElement("span");
    line.className = "dialogue-line";
    const indexBadge = document.createElement("span");
    indexBadge.className = "dialogue-index";
    indexBadge.textContent = String(item.id);

    const text = document.createElement("span");
    text.className = "dialogue-text";
    text.textContent = item.textEn;

    line.appendChild(indexBadge);
    line.appendChild(text);

    button.appendChild(speaker);
    button.appendChild(line);
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (state.dialoguePhase === "intro") {
        return;
      }
      await primeAudio();
      if (state.currentScene !== "benjiBunny") {
        return;
      }
      state.dialogueClickedIds.add(item.id);
      renderScene();
      await playAudioFile(item.audioEn);
      if (state.currentScene !== "benjiBunny") {
        return;
      }
      await playAudioFile(item.audioCz);
      if (state.currentScene !== "benjiBunny") {
        return;
      }
      if (state.dialogueClickedIds.size === benjiBunnyDialogue.length) {
        state.dialogueDoorState = "green";
        renderScene();
      }
    });
    dialoguePanel.appendChild(button);
  });
}

function createBenjiBunnyDebugSkipButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "owl-garden-debug-skip";
  button.style.left = `${benjiBunnyDebugSkipRect.x}%`;
  button.style.top = `${benjiBunnyDebugSkipRect.y}%`;
  button.style.width = `${benjiBunnyDebugSkipRect.w}%`;
  button.style.height = `${benjiBunnyDebugSkipRect.h}%`;
  button.setAttribute("aria-label", "Debug skip to owl garden");
  button.addEventListener("click", async (event) => {
    event.stopPropagation();
    await primeAudio();
    if (state.currentScene === "benjiBunny") {
      setScene("owlGarden");
    }
  });
  return button;
}

async function runBenjiBunny(sequenceId) {
  if (!isSceneActive("benjiBunny", sequenceId)) {
    return;
  }
  state.visibleDialogueCount = 0;
  state.dialoguePhase = "intro";
  state.dialogueDoorState = "hidden";
  renderScene();

  for (let index = 0; index < benjiBunnyDialogue.length; index += 1) {
    if (!isSceneActive("benjiBunny", sequenceId)) {
      return;
    }
    state.visibleDialogueCount = index + 1;
    renderScene();
    await playAudioFile(benjiBunnyDialogue[index].audioEn);
    if (!isSceneActive("benjiBunny", sequenceId)) {
      return;
    }
    await playAudioFile(benjiBunnyDialogue[index].audioCz);
    if (!isSceneActive("benjiBunny", sequenceId)) {
      return;
    }
    await pauseMs(220);
  }

  if (!isSceneActive("benjiBunny", sequenceId)) {
    return;
  }
  state.dialoguePhase = "practice";
  renderScene();
}

async function runOwlGarden(sequenceId) {
  if (!isSceneActive("owlGarden", sequenceId)) {
    return;
  }
  resetOwlGarden();
  renderScene();

  await pauseMs(420);
  if (!isSceneActive("owlGarden", sequenceId)) {
    return;
  }

  await speakEnglishLine("Hello Benji and Bunny.", { preferredVoiceName: "ash", rate: 0.84, pitch: 0.92 });
  if (!isSceneActive("owlGarden", sequenceId)) {
    return;
  }
  await playAudioFile("audio/czech/owl_garden_01_owl_hello_benji_bunny_cz.m4a");
  if (!isSceneActive("owlGarden", sequenceId)) {
    return;
  }

  await speakEnglishLine("I have presents for you.", { preferredVoiceName: "ash", rate: 0.84, pitch: 0.92 });
  if (!isSceneActive("owlGarden", sequenceId)) {
    return;
  }
  await playAudioFile("audio/czech/owl_garden_02_owl_i_have_presents_cz.m4a");
  if (!isSceneActive("owlGarden", sequenceId)) {
    return;
  }

  await speakEnglishLine("Count purple apples, yellow sunflowers and pink pigs in my garden.", { preferredVoiceName: "ash", rate: 0.84, pitch: 0.92 });
  if (!isSceneActive("owlGarden", sequenceId)) {
    return;
  }
  await playAudioFile("audio/czech/owl_garden_03_owl_count_apples_sunflowers_pigs_cz.m4a?v=20260409a");
  if (!isSceneActive("owlGarden", sequenceId)) {
    return;
  }

  state.owlGardenPhase = "play";
  renderScene();
}

async function playOwlGardenOutro(sequenceId) {
  if (!isSceneActive("owlGarden", sequenceId)) {
    return;
  }

  state.owlGardenPhase = "outro";
  state.owlGardenActiveId = "";
  state.owlGardenOutroVisibleCount = 0;
  renderScene();

  await pauseMs(420);
  if (!isSceneActive("owlGarden", sequenceId)) {
    return;
  }

  for (const item of owlGardenOutroDialogue) {
    state.owlGardenOutroVisibleCount = item.id;
    renderScene();
    const playedEnglish = await playAudioFileIfAvailable(item.audioEn);
    if (!playedEnglish) {
      await speakEnglishLine(item.textEn, { preferredVoiceName: item.preferredVoiceName, rate: 0.84, pitch: 0.94 });
    }
    if (!isSceneActive("owlGarden", sequenceId)) {
      return;
    }
    await playAudioFile(item.audioCz);
    if (!isSceneActive("owlGarden", sequenceId)) {
      return;
    }
    await pauseMs(220);
    if (!isSceneActive("owlGarden", sequenceId)) {
      return;
    }
  }

  await pauseMs(380);
  if (!isSceneActive("owlGarden", sequenceId)) {
    return;
  }
  setScene("houseBunny");
}

async function playBenjiBunnyHelp() {
  await playAudioFile(benjiBunnyHelpAudio.intro);
}

async function playOwlGardenHelp() {
  if (state.currentScene !== "owlGarden" || state.owlGardenPhase !== "play") {
    return;
  }

  state.owlGardenHelpPlayed = true;
  renderScene();
  await playAudioFile("audio/czech/owl_garden_04_help_click_words_cz.m4a?v=20260409a");
  if (state.currentScene !== "owlGarden") {
    return;
  }
  await playAudioFile("audio/czech/owl_garden_05_help_thumbs_up_cz.m4a");
  if (state.currentScene !== "owlGarden") {
    return;
  }
  await playAudioFile("audio/czech/owl_garden_06_help_green_light_cz.m4a");
  if (state.currentScene !== "owlGarden") {
    return;
  }
  await playAudioFile("audio/czech/owl_garden_07_help_all_done_cz.m4a");
  if (state.currentScene !== "owlGarden") {
    return;
  }
  await speakEnglishLine("Listen to the colours: yellow, purple and pink.", { preferredVoiceName: "ash", rate: 0.84, pitch: 0.94 });
}

function playMushroomHelp() {
  if (state.mushroomMode === "colors") {
    speakCue("mushrooms_colors_intro");
  } else {
    speakCue("mushrooms_numbers_intro");
  }
}

async function primeAudio() {
  unlockAudio();
  await resumeAudioContext();
}

storyStage.addEventListener("click", async (event) => {
  const wasLocked = !state.audioUnlocked;
  await primeAudio();
  if (state.currentScene === "intro1") {
    setScene("intro2");
    return;
  }
  if (state.currentScene === "intro2" && event.target === magnifierButton) {
    setScene("intro4");
    return;
  }
  if (state.currentScene === "intro4" && event.target === mushroomPortalButton) {
    resetMushrooms();
    setScene("mushrooms");
    return;
  }
  if (state.currentScene === "intro4" && event.target === bunnyPortalButton) {
    resetBenjiBunnyDialogue();
    setScene("benjiBunny");
    return;
  }
  if (wasLocked && (state.currentScene === "intro2" || state.currentScene === "intro3")) {
    setScene(state.currentScene);
  }
});

magnifierButton.addEventListener("click", async (event) => {
  event.stopPropagation();
  await primeAudio();
  if (state.currentScene === "intro2") {
    setScene("intro4");
  }
});

mushroomPortalButton.addEventListener("click", async (event) => {
  event.stopPropagation();
  await primeAudio();
  if (state.currentScene === "intro4") {
    resetMushrooms();
    setScene("mushrooms");
  }
});

bunnyPortalButton.addEventListener("click", async (event) => {
  event.stopPropagation();
  await primeAudio();
  if (state.currentScene === "intro4") {
    resetBenjiBunnyDialogue();
    setScene("benjiBunny");
  }
});

backToSignpostButton.addEventListener("click", (event) => {
  event.stopPropagation();
  setScene("intro4");
});

backFromDialogueButton.addEventListener("click", (event) => {
  event.stopPropagation();
  setScene("intro4");
});

backFromOwlGardenButton.addEventListener("click", (event) => {
  event.stopPropagation();
  setScene("intro4");
});

dialogueHelpButton.addEventListener("click", async (event) => {
  event.stopPropagation();
  await primeAudio();
  if (state.currentScene === "benjiBunny") {
    await playBenjiBunnyHelp();
  }
});

dialogueDoorButton.addEventListener("click", async (event) => {
  event.stopPropagation();
  await primeAudio();
  if (state.currentScene !== "benjiBunny" || state.dialogueDoorState === "hidden") {
    return;
  }
  if (state.dialogueDoorState === "green") {
    setScene("owlGarden");
  }
});

owlGardenHelpButton.addEventListener("click", async (event) => {
  event.stopPropagation();
  await primeAudio();
  if (state.currentScene === "owlGarden") {
    await playOwlGardenHelp();
  }
});

owlGardenThumbButton.addEventListener("click", async (event) => {
  event.stopPropagation();
  await primeAudio();
  await confirmOwlGardenCurrentGroup();
});

mushroomHelpButton.addEventListener("click", async (event) => {
  event.stopPropagation();
  await primeAudio();
  if (state.currentScene === "mushrooms") {
    playMushroomHelp();
  }
});

colorsModeButton.addEventListener("click", (event) => {
  event.stopPropagation();
  setMushroomMode("colors");
});

numbersModeButton.addEventListener("click", (event) => {
  event.stopPropagation();
  setMushroomMode("numbers");
});

function renderOwlGarden() {
  owlGardenOverlay.innerHTML = "";
  owlGardenOverlay.appendChild(createOwlGardenDebugSkipButton());
  if (state.owlGardenPhase === "intro") {
    owlGardenPrompt.textContent = "🦉 Owl is speaking...";
    return;
  }

  if (state.owlGardenPhase === "outro") {
    owlGardenOutroDialogue.slice(0, state.owlGardenOutroVisibleCount).forEach((item, index) => {
      owlGardenOverlay.appendChild(createOwlGardenOutroBubble(item, index));
    });
    return;
  }

  const activeGroup = owlGardenGroups.find((group) => group.id === state.owlGardenActiveId);
  if (activeGroup) {
    owlGardenPrompt.textContent = `${activeGroup.colorWord} ${activeGroup.objectWord}: ${state.owlGardenCompletedIds.size}/${owlGardenGroups.length}`;
  } else {
    owlGardenPrompt.textContent = `Choose apples, sunflowers or pigs. Listen for yellow, purple and pink.`;
  }

  owlGardenGroups.forEach((group) => {
    owlGardenOverlay.appendChild(createOwlGardenDots(group));
    owlGardenOverlay.appendChild(createOwlGardenWordButton(group));
  });
}

function createOwlGardenOutroBubble(item, index) {
  const bubble = document.createElement("div");
  bubble.className = `owl-garden-outro-bubble ${item.cssClass}`;
  if (item.cssClass === "benji") {
    bubble.style.left = "4.2%";
    bubble.style.bottom = `${17.2 - index * 1.2}%`;
  } else {
    bubble.style.right = "4.4%";
    bubble.style.bottom = `${18.6 - index * 1.2}%`;
  }

  const speaker = document.createElement("span");
  speaker.className = "owl-garden-outro-speaker";
  speaker.textContent = `${item.speaker}:`;

  const line = document.createElement("span");
  line.className = "owl-garden-outro-text";
  line.textContent = item.textEn;

  bubble.appendChild(speaker);
  bubble.appendChild(line);
  return bubble;
}

function createOwlGardenDebugSkipButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "owl-garden-debug-skip";
  button.style.left = `${owlGardenDebugSkipRect.x}%`;
  button.style.top = `${owlGardenDebugSkipRect.y}%`;
  button.style.width = `${owlGardenDebugSkipRect.w}%`;
  button.style.height = `${owlGardenDebugSkipRect.h}%`;
  button.setAttribute("aria-label", "Debug skip");
  button.addEventListener("click", async (event) => {
    event.stopPropagation();
    await primeAudio();
    debugSkipOwlGarden();
  });
  return button;
}

function createOwlGardenDots(group) {
  const dots = document.createElement("div");
  const shownNumber = state.owlGardenLockedNumbers[group.id] ?? state.owlGardenCurrentNumbers[group.id] ?? 0;
  dots.className = "owl-garden-dots";
  dots.style.left = `${group.wordRect.x}%`;
  dots.style.top = `${group.wordRect.y - 4.6}%`;
  dots.style.width = `${group.wordRect.w}%`;
  dots.style.height = "3.2%";

  for (let index = 0; index < shownNumber; index += 1) {
    const dot = document.createElement("span");
    dot.className = "owl-garden-dot";
    dot.style.background = group.color;
    dots.appendChild(dot);
  }

  return dots;
}

function owlGardenPhrase(group, numberValue) {
  const numberText = owlGardenNumberWords[numberValue] ?? String(numberValue);
  return `${numberText} ${group.colorWord} ${group.objectWord}`;
}

function createOwlGardenWordButton(group) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "owl-garden-word";
  if (state.owlGardenActiveId === group.id) {
    button.classList.add("active");
  }
  if (state.owlGardenCompletedIds.has(group.id)) {
    button.classList.add("done");
  }
  button.style.left = `${group.wordRect.x}%`;
  button.style.top = `${group.wordRect.y}%`;
  button.style.width = `${group.wordRect.w}%`;
  button.style.height = `${group.wordRect.h}%`;

  const numberBadge = document.createElement("span");
  numberBadge.className = "owl-garden-word-badge";
  const shownNumber = state.owlGardenLockedNumbers[group.id] ?? state.owlGardenCurrentNumbers[group.id];
  if (state.owlGardenLockedNumbers[group.id]) {
    numberBadge.classList.add("locked");
  }
  numberBadge.textContent = shownNumber ? String(shownNumber) : "?";

  const label = document.createElement("span");
  label.className = "owl-garden-word-label";
  label.textContent = group.word.toLowerCase();

  const light = document.createElement("span");
  light.className = "owl-garden-word-light";
  if (state.owlGardenCompletedIds.has(group.id)) {
    light.classList.add("on");
  }

  button.appendChild(numberBadge);
  button.appendChild(label);
  button.appendChild(light);
  button.setAttribute("aria-label", group.word);
  button.addEventListener("click", async (event) => {
    event.stopPropagation();
    await primeAudio();
    await selectOwlGardenGroup(group);
  });
  return button;
}

function nextOwlGardenNumber(groupId) {
  const numberValue = 1 + Math.floor(Math.random() * 8);
  state.owlGardenCurrentNumbers[groupId] = numberValue;
  return numberValue;
}

async function selectOwlGardenGroup(group) {
  if (state.currentScene !== "owlGarden" || state.owlGardenPhase !== "play") {
    return;
  }

  if (!state.owlGardenHelpPlayed) {
    state.owlGardenHelpPlayed = true;
  }

  if (state.owlGardenCompletedIds.has(group.id)) {
    state.owlGardenActiveId = "";
    renderScene();
    await speakEnglishLine(owlGardenPhrase(group, group.correctCount), { preferredVoiceName: "ash", rate: 0.86, pitch: 0.94 });
    return;
  }

  state.owlGardenActiveId = group.id;
  const numberValue = nextOwlGardenNumber(group.id);
  renderScene();

  await speakEnglishLine(owlGardenPhrase(group, numberValue), { preferredVoiceName: "ash", rate: 0.86, pitch: 0.94 });
}

async function confirmOwlGardenCurrentGroup() {
  if (state.currentScene !== "owlGarden" || state.owlGardenPhase !== "play" || !state.owlGardenActiveId) {
    return;
  }

  const group = owlGardenGroups.find((item) => item.id === state.owlGardenActiveId);
  if (!group) {
    return;
  }

  const shownNumber = state.owlGardenCurrentNumbers[group.id];
  if (shownNumber === group.correctCount) {
    state.owlGardenCompletedIds.add(group.id);
    state.owlGardenLockedNumbers[group.id] = shownNumber;
    renderScene();
    await speakEnglishLine(owlGardenPhrase(group, shownNumber), { preferredVoiceName: "ash", rate: 0.86, pitch: 0.94 });
    if (state.currentScene !== "owlGarden" || state.owlGardenPhase !== "play") {
      return;
    }

    if (state.owlGardenCompletedIds.size === owlGardenGroups.length) {
      await playAudioFile("audio/effects/owl_garden_fanfare.mp3");
      if (state.currentScene === "owlGarden" && state.owlGardenPhase === "play") {
        await playOwlGardenOutro(state.sequenceId);
      }
      return;
    }

    state.owlGardenActiveId = "";
    renderScene();
    return;
  }

  const nextNumber = nextOwlGardenNumber(group.id);
  renderScene();
  await pauseMs(260);
  if (state.currentScene !== "owlGarden" || state.owlGardenPhase !== "play" || state.owlGardenActiveId !== group.id) {
    return;
  }
  await speakEnglishLine(owlGardenPhrase(group, nextNumber), { preferredVoiceName: "ash", rate: 0.86, pitch: 0.94 });
}

function debugSkipOwlGarden() {
  if (state.currentScene !== "owlGarden") {
    return;
  }

  cleanupCurrentScene();
  state.sequenceId += 1;
  state.owlGardenCompletedIds = new Set(owlGardenGroups.map((group) => group.id));
  state.owlGardenLockedNumbers = Object.fromEntries(
    owlGardenGroups.map((group) => [group.id, group.correctCount]),
  );
  state.owlGardenCurrentNumbers = { ...state.owlGardenLockedNumbers };
  state.owlGardenActiveId = "";
  state.owlGardenHelpPlayed = true;
  state.owlGardenPhase = "outro";
  state.owlGardenOutroVisibleCount = owlGardenOutroDialogue.length;
  renderScene();
}

window.addEventListener("pointerdown", () => {
  primeAudio();
}, { once: true });

window.addEventListener("keydown", () => {
  primeAudio();
}, { once: true });

window.speechSynthesis?.addEventListener?.("voiceschanged", () => {});

setScene("intro1");
