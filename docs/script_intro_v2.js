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
  forestSchool: {
    image: "ForestSchool1.PNG?v=20260526a",
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

const houseBunnyWheelRect = { x: 29.7, y: 1.2, w: 43.5, h: 79.4 };
const houseBunnyWheelColors = [
  { id: "yellow", word: "yellow", index: 0 },
  { id: "red", word: "red", index: 1 },
  { id: "white", word: "white", index: 2 },
  { id: "blue", word: "blue", index: 3 },
  { id: "grey", word: "grey", index: 4 },
  { id: "purple", word: "purple", index: 5 },
  { id: "brown", word: "brown", index: 6 },
  { id: "orange", word: "orange", index: 7 },
  { id: "pink", word: "pink", index: 8 },
  { id: "green", word: "green", index: 9 },
];
const houseBunnyCenterColor = { id: "black", word: "black" };
const houseBunnyWinCount = 5;
const forestSchoolWinCount = 5;
const forestSchoolObjects = [
  { id: "ball", word: "ball" },
  { id: "book", word: "book" },
  { id: "apple", word: "apple" },
  { id: "car", word: "car" },
  { id: "house", word: "house" },
];
const forestSchoolQuestionWords = ["ball", "book", "apple", "car", "house"];
const forestSchoolHelpDisplayText = "Je to správně? Pokud ano klikni jes, pokud ne klikni no.";
const forestSchoolHelpSpokenText = "Je to správně? Pokud ano, klikňi na jes. Pokud ne, klikňi na nou.";
const forestSchoolHelpAudio = "audio/czech/forest_school_help_cz.mp3?v=20260526j";
const forestSchoolDemoAudio = {
  bunnyYes: "audio/english/forest_school_bunny_yes_it_is.mp3?v=20260526l",
  benjiNo: "audio/english/forest_school_benji_no_it_isnt.mp3?v=20260526l",
};

const benjiBunnyDebugSkipRect = { x: 0, y: 76, w: 16, h: 24 };
const owlGardenDebugSkipRect = { x: 0, y: 76, w: 16, h: 24 };
const forestSchoolDebugRect = { x: 0, y: 0, w: 14, h: 20 };

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
  owlGardenRemainingNumbers: [],
  owlGardenHelpPlayed: false,
  owlGardenOutroVisibleCount: 0,
  houseBunnyPhase: "idle",
  houseBunnyImageStep: 1,
  houseBunnyTargetId: "",
  houseBunnyRemainingIds: [],
  houseBunnyDartColorId: "",
  houseBunnyScore: 0,
  forestSchoolPhase: "intro",
  forestSchoolScore: 0,
  forestSchoolCurrentObjectId: "",
  forestSchoolQuestionWord: "",
  forestSchoolAnswerYes: true,
  forestSchoolRemainingIds: [],
  forestSchoolHelpVisible: false,
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
  { id: 1, speaker: "Benji", cssClass: "benji", textEn: "Hello.", audioEn: "audio/english/benji_bunny_01_benji_hello_en.mp3", audioCz: "audio/czech/benji_bunny_01_benji_hello_cz.m4a?v=20260410a" },
  { id: 2, speaker: "Bunny", cssClass: "bunny", textEn: "Hello.", audioEn: "audio/english/benji_bunny_02_bunny_hello_en.mp3", audioCz: "audio/czech/benji_bunny_02_bunny_hello_cz.m4a?v=20260410a" },
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

const houseBunnyIntroAudio = [
  "audio/czech/house_bunny_01_intro_train_basic_colours_cz.m4a?v=20260410a",
  "audio/czech/house_bunny_02_intro_excellent_try_again_cz.m4a?v=20260410a",
];

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

function pickCzechVoice(preferredNameFragment = "") {
  const voices = window.speechSynthesis?.getVoices?.() ?? [];
  const czechVoices = voices.filter((voice) => voice.lang && voice.lang.toLowerCase().startsWith("cs"));
  if (preferredNameFragment) {
    const preferredNames = preferredNameFragment
      .split("|")
      .map((item) => item.trim().toLowerCase())
      .filter(Boolean);
    for (const preferredName of preferredNames) {
      const preferred = czechVoices.find((voice) => voice.name.toLowerCase().includes(preferredName));
      if (preferred) {
        return preferred;
      }
    }
  }
  return czechVoices[0] ?? null;
}

function speakCzechLine(text, options = {}) {
  if (!("speechSynthesis" in window) || !state.audioUnlocked) {
    return Promise.resolve();
  }

  window.speechSynthesis.cancel();
  return new Promise((resolve) => {
    state.currentSpeechResolve = resolve;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "cs-CZ";
    utterance.rate = options.rate ?? 0.9;
    utterance.pitch = options.pitch ?? 1.0;

    const czechVoice = pickCzechVoice(options.preferredVoiceName ?? "");
    if (czechVoice) {
      utterance.voice = czechVoice;
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
  const houseBunnyScene = state.currentScene === "houseBunny";
  const forestSchoolScene = state.currentScene === "forestSchool";
  let imageSrc = scene.image;
  if (owlGardenOutro) {
    imageSrc = "MeetingOul2.PNG?v=20260409b";
  } else if (houseBunnyScene) {
    imageSrc = `HouseBunny${state.houseBunnyImageStep}.PNG?v=20260410a`;
  }
  sceneImage.src = imageSrc;
  magnifierButton.classList.toggle("hidden", state.currentScene !== "intro2");
  clickPrompt.classList.toggle("hidden", state.audioUnlocked || state.currentScene === "intro4" || state.currentScene === "benjiBunny" || state.currentScene === "owlGarden" || houseBunnyScene);
  mushroomPortalButton.classList.toggle("hidden", state.currentScene !== "intro4");
  bunnyPortalButton.classList.toggle("hidden", state.currentScene !== "intro4");
  mushroomHud.classList.toggle("hidden", state.currentScene !== "mushrooms");
  mushroomOverlay.classList.toggle("hidden", state.currentScene !== "mushrooms");
  dialogueHud.classList.toggle("hidden", state.currentScene !== "benjiBunny");
  dialoguePanel.classList.toggle("hidden", state.currentScene !== "benjiBunny");
  owlGardenHud.classList.toggle("hidden", state.currentScene !== "owlGarden" && !houseBunnyScene && !forestSchoolScene);
  owlGardenHelpButton.classList.toggle("hidden", (!houseBunnyScene && !forestSchoolScene && state.currentScene !== "owlGarden") || (state.currentScene === "owlGarden" && state.owlGardenPhase !== "play") || (houseBunnyScene && state.houseBunnyPhase !== "waiting"));
  owlGardenHelpButton.classList.toggle("pulse-soft", (state.currentScene === "owlGarden" && state.owlGardenPhase === "play") || (houseBunnyScene && state.houseBunnyPhase === "waiting") || forestSchoolScene);
  owlGardenOverlay.classList.toggle("hidden", state.currentScene !== "owlGarden" && !houseBunnyScene && !forestSchoolScene);
  owlGardenPrompt.classList.toggle("hidden", (state.currentScene !== "owlGarden" && !houseBunnyScene && !forestSchoolScene) || (state.currentScene === "owlGarden" && state.owlGardenPhase === "outro") || (forestSchoolScene && (state.forestSchoolPhase === "intro" || state.forestSchoolPhase === "conjure")));
  owlGardenPrompt.classList.toggle("forest-school-prompt", forestSchoolScene);
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
  } else if (houseBunnyScene) {
    renderHouseBunny();
  } else if (forestSchoolScene) {
    renderForestSchool();
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
  } else if (sceneName === "houseBunny") {
    runHouseBunny(sequenceId);
  } else if (sceneName === "forestSchool") {
    if (!state.audioUnlocked) {
      resetForestSchool();
      renderScene();
      return;
    }
    runForestSchool(sequenceId);
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
  state.owlGardenRemainingNumbers = shuffledOwlGardenNumbers();
  state.owlGardenHelpPlayed = false;
  state.owlGardenOutroVisibleCount = 0;
}

function resetHouseBunny() {
  state.houseBunnyPhase = "idle";
  state.houseBunnyImageStep = 1;
  state.houseBunnyTargetId = "";
  state.houseBunnyRemainingIds = [];
  state.houseBunnyDartColorId = "";
  state.houseBunnyScore = 0;
}

function resetForestSchool() {
  state.forestSchoolPhase = "intro";
  state.forestSchoolScore = 0;
  state.forestSchoolCurrentObjectId = "";
  state.forestSchoolQuestionWord = "";
  state.forestSchoolAnswerYes = true;
  state.forestSchoolRemainingIds = shuffledForestSchoolObjectIds();
  state.forestSchoolHelpVisible = false;
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

function shuffledHouseBunnyColorIds() {
  const ids = [...houseBunnyWheelColors.map((item) => item.id), houseBunnyCenterColor.id];
  for (let index = ids.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [ids[index], ids[swapIndex]] = [ids[swapIndex], ids[index]];
  }
  return ids;
}

function shuffledOwlGardenNumbers() {
  const numbers = [1, 2, 3, 4, 5, 6, 7, 8];
  for (let index = numbers.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [numbers[index], numbers[swapIndex]] = [numbers[swapIndex], numbers[index]];
  }
  return numbers;
}

function currentHouseBunnyColor() {
  return houseBunnyWheelColors.find((item) => item.id === state.houseBunnyTargetId) ?? (state.houseBunnyTargetId === houseBunnyCenterColor.id ? houseBunnyCenterColor : null);
}

function nextHouseBunnyColorId() {
  if (!state.houseBunnyRemainingIds.length) {
    state.houseBunnyRemainingIds = shuffledHouseBunnyColorIds();
  }
  state.houseBunnyTargetId = state.houseBunnyRemainingIds.pop() ?? "";
  return state.houseBunnyTargetId;
}

async function speakHouseBunnyLine(text) {
  await speakEnglishLine(text, { preferredVoiceName: "samantha|ava|victoria|karen", rate: 0.9, pitch: 1.02 });
}

async function playHouseBunnyCurrentColor() {
  if (state.currentScene !== "houseBunny" || state.houseBunnyPhase !== "waiting") {
    return;
  }
  const activeColor = currentHouseBunnyColor();
  if (!activeColor) {
    return;
  }
  await speakHouseBunnyLine(activeColor.word);
}

async function queueNextHouseBunnyColor(sequenceId, delayMs = 500) {
  state.houseBunnyPhase = "idle";
  state.houseBunnyImageStep = 1;
  state.houseBunnyDartColorId = "";
  state.houseBunnyTargetId = "";
  renderScene();

  await pauseMs(delayMs);
  if (!isSceneActive("houseBunny", sequenceId)) {
    return;
  }

  nextHouseBunnyColorId();
  state.houseBunnyPhase = "waiting";
  state.houseBunnyImageStep = 1;
  renderScene();
  await playHouseBunnyCurrentColor();
}

async function runHouseBunny(sequenceId) {
  if (!isSceneActive("houseBunny", sequenceId)) {
    return;
  }
  resetHouseBunny();
  renderScene();
  for (const audioSrc of houseBunnyIntroAudio) {
    await playAudioFile(audioSrc);
    if (!isSceneActive("houseBunny", sequenceId)) {
      return;
    }
  }
  await queueNextHouseBunnyColor(sequenceId, 420);
}

async function speakForestSchoolOwlLine(text) {
  await speakEnglishLine(text, { preferredVoiceName: "ash", rate: 0.84, pitch: 0.94 });
}

async function speakForestSchoolBunnyLine(text) {
  const played = text === "Yes, it is." ? await playAudioFileIfAvailable(forestSchoolDemoAudio.bunnyYes) : false;
  if (!played) {
    await speakEnglishLine(text, { preferredVoiceName: "samantha|ava|karen|victoria", rate: 0.9, pitch: 1.12 });
  }
}

async function speakForestSchoolBenjiLine(text) {
  const played = text === "No, it isn't." ? await playAudioFileIfAvailable(forestSchoolDemoAudio.benjiNo) : false;
  if (!played) {
    await speakEnglishLine(text, { preferredVoiceName: "daniel|fred|fable", rate: 0.88, pitch: 0.96 });
  }
}

function currentForestSchoolObject() {
  return forestSchoolObjects.find((item) => item.id === state.forestSchoolCurrentObjectId) ?? forestSchoolObjects[0];
}

function forestSchoolObjectById(objectId) {
  return forestSchoolObjects.find((item) => item.id === objectId) ?? forestSchoolObjects[0];
}

function shuffledForestSchoolObjectIds() {
  const ids = forestSchoolObjects.map((item) => item.id);
  for (let index = ids.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [ids[index], ids[swapIndex]] = [ids[swapIndex], ids[index]];
  }
  return ids;
}

function nextForestSchoolObject() {
  if (!state.forestSchoolRemainingIds.length) {
    state.forestSchoolRemainingIds = shuffledForestSchoolObjectIds();
  }
  return forestSchoolObjectById(state.forestSchoolRemainingIds.pop());
}

function wrongForestSchoolQuestionWord(objectWord) {
  const wrongWords = forestSchoolQuestionWords.filter((word) => word !== objectWord);
  return wrongWords[Math.floor(Math.random() * wrongWords.length)] ?? objectWord;
}

function setForestSchoolQuestion(object, questionWord) {
  state.forestSchoolCurrentObjectId = object.id;
  state.forestSchoolQuestionWord = questionWord;
  state.forestSchoolAnswerYes = questionWord === object.word;
}

function pickForestSchoolQuestion() {
  const object = nextForestSchoolObject();
  const shouldBeCorrect = Math.random() >= 0.38;
  const questionWord = shouldBeCorrect ? object.word : wrongForestSchoolQuestionWord(object.word);
  setForestSchoolQuestion(object, questionWord);
}

async function queueNextForestSchoolQuestion(sequenceId, delayMs = 650) {
  state.forestSchoolPhase = "conjure";
  renderScene();
  await pauseMs(delayMs);
  if (!isSceneActive("forestSchool", sequenceId)) {
    return;
  }
  pickForestSchoolQuestion();
  state.forestSchoolPhase = "question";
  renderScene();
  await speakForestSchoolOwlLine(`Is this a ${state.forestSchoolQuestionWord}?`);
}

async function runForestSchoolDemo(sequenceId) {
  const demoIds = shuffledForestSchoolObjectIds();
  const bunnyObject = forestSchoolObjectById(demoIds.pop());
  const benjiObject = forestSchoolObjectById(demoIds.pop());

  state.forestSchoolPhase = "conjure";
  renderScene();
  await pauseMs(650);
  if (!isSceneActive("forestSchool", sequenceId)) {
    return false;
  }

  setForestSchoolQuestion(bunnyObject, wrongForestSchoolQuestionWord(bunnyObject.word));
  state.forestSchoolPhase = "demoBunny";
  renderScene();
  await speakForestSchoolOwlLine(`Is this a ${state.forestSchoolQuestionWord}?`);
  if (!isSceneActive("forestSchool", sequenceId)) {
    return false;
  }
  await speakForestSchoolBunnyLine("Yes, it is.");
  if (!isSceneActive("forestSchool", sequenceId)) {
    return false;
  }
  await pauseMs(650);

  state.forestSchoolPhase = "conjure";
  renderScene();
  await pauseMs(650);
  if (!isSceneActive("forestSchool", sequenceId)) {
    return false;
  }

  setForestSchoolQuestion(benjiObject, wrongForestSchoolQuestionWord(benjiObject.word));
  state.forestSchoolPhase = "demoBenji";
  renderScene();
  await speakForestSchoolOwlLine(`Is this a ${state.forestSchoolQuestionWord}?`);
  if (!isSceneActive("forestSchool", sequenceId)) {
    return false;
  }
  await speakForestSchoolBenjiLine("No, it isn't.");
  if (!isSceneActive("forestSchool", sequenceId)) {
    return false;
  }
  await pauseMs(650);

  state.forestSchoolCurrentObjectId = "";
  state.forestSchoolQuestionWord = "";
  state.forestSchoolAnswerYes = true;
  state.forestSchoolPhase = "demoReady";
  renderScene();
  await speakForestSchoolOwlLine("Will you try?");
  return isSceneActive("forestSchool", sequenceId);
}

async function runForestSchool(sequenceId) {
  if (!isSceneActive("forestSchool", sequenceId)) {
    return;
  }
  resetForestSchool();
  renderScene();
  await pauseMs(900);
  if (!isSceneActive("forestSchool", sequenceId)) {
    return;
  }
  await speakForestSchoolOwlLine("Welcome to forest school.");
  if (!isSceneActive("forestSchool", sequenceId)) {
    return;
  }
  await playForestSchoolHelp();
  if (!isSceneActive("forestSchool", sequenceId)) {
    return;
  }
  const demoFinished = await runForestSchoolDemo(sequenceId);
  if (!demoFinished || !isSceneActive("forestSchool", sequenceId)) {
    return;
  }
  state.forestSchoolRemainingIds = shuffledForestSchoolObjectIds();
  await queueNextForestSchoolQuestion(sequenceId, 700);
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

async function playForestSchoolHelp() {
  if (state.currentScene !== "forestSchool") {
    return;
  }
  state.forestSchoolHelpVisible = true;
  renderScene();
  const playedHelpAudio = await playAudioFileIfAvailable(forestSchoolHelpAudio);
  if (!playedHelpAudio) {
    await speakCzechLine(forestSchoolHelpSpokenText, { rate: 0.86 });
  }
}

function detectHouseBunnyColor(localX, localY, width, height) {
  const side = Math.min(width, height);
  const centerX = width / 2;
  const centerY = height / 2;
  const dx = localX - centerX;
  const dy = localY - centerY;
  const radius = Math.sqrt(dx * dx + dy * dy);
  const outerRadius = side * 0.49;
  const innerRadius = side * 0.12;
  if (radius < innerRadius) {
    return houseBunnyCenterColor;
  }
  if (radius > outerRadius) {
    return null;
  }

  const angle = (Math.atan2(dy, dx) * 180 / Math.PI + 450) % 360;
  const sectorIndex = Math.floor(angle / 36) % houseBunnyWheelColors.length;
  return houseBunnyWheelColors[sectorIndex] ?? null;
}

function houseBunnyDartStyle(color) {
  if (color.id === houseBunnyCenterColor.id) {
    return {
      targetXPercent: houseBunnyWheelRect.x + houseBunnyWheelRect.w / 2,
      targetYPercent: houseBunnyWheelRect.y + houseBunnyWheelRect.h / 2,
      rotateDeg: 180,
    };
  }
  const centerX = houseBunnyWheelRect.x + houseBunnyWheelRect.w / 2;
  const centerY = houseBunnyWheelRect.y + houseBunnyWheelRect.h / 2;
  const angleOverrides = {
    yellow: 6,
    red: 33,
    pink: 318,
  };
  const angleDeg = angleOverrides[color.id] ?? (color.index * 36 + 18);
  const angle = angleDeg * Math.PI / 180;
  const radiusPercent = houseBunnyWheelRect.w * 0.31;
  const tipX = centerX + Math.sin(angle) * radiusPercent;
  const tipY = centerY - Math.cos(angle) * radiusPercent;
  const rotateDeg = ((Math.atan2(centerY - tipY, centerX - tipX) * 180) / Math.PI) - 180;
  return {
    targetXPercent: tipX,
    targetYPercent: tipY,
    rotateDeg,
  };
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
    return;
  }
  if (state.currentScene === "forestSchool" && (wasLocked || state.forestSchoolPhase === "intro")) {
    setScene("forestSchool");
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
  } else if (state.currentScene === "houseBunny") {
    await playHouseBunnyCurrentColor();
  } else if (state.currentScene === "forestSchool") {
    await playForestSchoolHelp();
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

function renderHouseBunny() {
  owlGardenOverlay.innerHTML = "";
  owlGardenPrompt.textContent = state.houseBunnyPhase === "waiting"
    ? "Listen and click the colour."
    : state.houseBunnyPhase === "result"
      ? "Excellent."
      : state.houseBunnyPhase === "retry"
        ? "Try again."
        : "Get ready.";

  const wheel = document.createElement("button");
  wheel.type = "button";
  wheel.className = "house-bunny-wheel";
  wheel.style.left = `${houseBunnyWheelRect.x}%`;
  wheel.style.top = `${houseBunnyWheelRect.y}%`;
  wheel.style.width = `${houseBunnyWheelRect.w}%`;
  wheel.style.height = `${houseBunnyWheelRect.h}%`;
  wheel.setAttribute("aria-label", "Colour target");
  wheel.addEventListener("click", async (event) => {
    event.stopPropagation();
    if (state.currentScene !== "houseBunny" || state.houseBunnyPhase !== "waiting") {
      return;
    }
    const rect = wheel.getBoundingClientRect();
    const localX = event.clientX - rect.left;
    const localY = event.clientY - rect.top;
    const selectedColor = detectHouseBunnyColor(localX, localY, rect.width, rect.height);
    if (!selectedColor) {
      return;
    }
    await primeAudio();
    await handleHouseBunnySelection(selectedColor.id);
  });
  owlGardenOverlay.appendChild(wheel);
  owlGardenOverlay.appendChild(createForestSchoolDebugButton());

  if (state.houseBunnyImageStep === 3 && state.houseBunnyDartColorId) {
    const color = houseBunnyWheelColors.find((item) => item.id === state.houseBunnyDartColorId) ?? (state.houseBunnyDartColorId === houseBunnyCenterColor.id ? houseBunnyCenterColor : null);
    if (color) {
      const dart = document.createElement("img");
      dart.className = "house-bunny-dart";
      dart.src = "assets/red_dart.png?v=20260410a";
      dart.alt = "";
      const style = houseBunnyDartStyle(color);
      const overlayWidth = owlGardenOverlay.clientWidth || storyStage.clientWidth || 0;
      const overlayHeight = owlGardenOverlay.clientHeight || storyStage.clientHeight || 0;
      const dartWidth = Math.min(176, Math.max(118, overlayWidth * 0.11));
      const dartHeight = dartWidth * (1024 / 1536);
      const tipOffsetX = dartWidth * 0.44;
      const tipOffsetY = dartHeight * 0.586;
      dart.style.width = `${dartWidth}px`;
      dart.style.left = `${(overlayWidth * style.targetXPercent / 100) - tipOffsetX}px`;
      dart.style.top = `${(overlayHeight * style.targetYPercent / 100) - tipOffsetY}px`;
      dart.style.transform = `rotate(${style.rotateDeg}deg)`;
      owlGardenOverlay.appendChild(dart);
    }
  }
}

function renderForestSchool() {
  owlGardenOverlay.innerHTML = "";
  owlGardenPrompt.textContent = state.forestSchoolPhase === "intro"
    ? "Owl is speaking..."
    : state.forestSchoolPhase === "conjure"
      ? "Magic..."
    : state.forestSchoolPhase === "done"
      ? "Excellent."
    : state.forestSchoolPhase === "finished"
        ? "Forest school complete."
      : state.forestSchoolPhase === "demoReady"
        ? "Will you try?"
      : state.forestSchoolPhase === "checking"
        ? "Listening..."
      : state.forestSchoolPhase === "retry"
        ? "Try again."
        : `Is this a ${state.forestSchoolQuestionWord}?`;

  const rewards = document.createElement("div");
  rewards.className = "forest-school-rewards";
  for (let index = 0; index < 5; index += 1) {
    const reward = document.createElement("span");
    reward.className = "forest-school-reward";
    reward.textContent = "🍄";
    if (index < state.forestSchoolScore) {
      reward.classList.add("active");
    }
    rewards.appendChild(reward);
  }
  owlGardenOverlay.appendChild(rewards);

  if (state.forestSchoolPhase === "conjure") {
    const beam = document.createElement("div");
    beam.className = "forest-school-wand-beam";
    owlGardenOverlay.appendChild(beam);

    const magic = document.createElement("div");
    magic.className = "forest-school-magic";
    for (let index = 0; index < 8; index += 1) {
      const spark = document.createElement("span");
      spark.className = "forest-school-spark";
      spark.style.setProperty("--spark-angle", `${index * 45}deg`);
      magic.appendChild(spark);
    }
    owlGardenOverlay.appendChild(magic);
  }

  if (state.forestSchoolPhase === "demoBunny" || state.forestSchoolPhase === "demoBenji" || state.forestSchoolPhase === "question" || state.forestSchoolPhase === "checking" || state.forestSchoolPhase === "done" || state.forestSchoolPhase === "retry" || state.forestSchoolPhase === "finished") {
    const currentObject = currentForestSchoolObject();
    const item = document.createElement("div");
    item.className = `forest-school-item forest-school-item-${currentObject.id}`;
    item.setAttribute("aria-label", currentObject.word);
    item.appendChild(createForestSchoolObjectDrawing(currentObject.id));
    owlGardenOverlay.appendChild(item);
  }

  const showForestSchoolHelp = state.forestSchoolHelpVisible
    || state.forestSchoolPhase === "question"
    || state.forestSchoolPhase === "checking"
    || state.forestSchoolPhase === "done"
    || state.forestSchoolPhase === "retry";
  if (showForestSchoolHelp) {
    const help = document.createElement("div");
    help.className = "forest-school-help";
    help.textContent = forestSchoolHelpDisplayText;
    owlGardenOverlay.appendChild(help);
  }

  const controls = document.createElement("div");
  controls.className = "forest-school-answer-row";
  controls.appendChild(createForestSchoolAnswerButton(true));
  controls.appendChild(createForestSchoolAnswerButton(false));
  owlGardenOverlay.appendChild(controls);
}

function createForestSchoolObjectDrawing(objectId) {
  const drawing = document.createElement("span");
  drawing.className = "forest-school-object-drawing";
  if (forestSchoolQuestionWords.includes(objectId)) {
    const image = document.createElement("img");
    image.className = "forest-school-object-image";
    image.src = `assets/forest_school_${objectId}.png?v=20260526b`;
    image.alt = objectId;
    drawing.appendChild(image);
    return drawing;
  }

  const drawings = {
    ball: `
      <svg viewBox="0 0 120 120" role="img" aria-label="ball">
        <circle class="svg-shadow" cx="60" cy="64" r="46"></circle>
        <circle class="svg-outline" cx="60" cy="58" r="45"></circle>
        <path class="svg-ball-red" d="M21 48c9-25 34-39 59-31 13 4 23 13 30 24-25-2-46 5-65 21-8-6-16-10-24-14Z"></path>
        <path class="svg-ball-blue" d="M34 85c13 15 36 21 56 10 18-10 28-29 24-49-27-1-50 8-68 27-5 5-9 9-12 12Z"></path>
        <path class="svg-ball-band" d="M24 52c14 6 24 13 31 22 8 10 13 22 15 34"></path>
        <path class="svg-shine" d="M43 31c7-5 16-7 24-5"></path>
      </svg>
    `,
    book: `
      <svg viewBox="0 0 120 120" role="img" aria-label="book">
        <path class="svg-shadow" d="M17 88c19 12 36 14 52 7 13 7 27 6 43-2V36c-16 9-30 10-43 3-15 7-32 6-52-4v53Z"></path>
        <path class="svg-outline" d="M14 82c18 12 36 14 53 6 13 8 28 7 45-2V30c-17 10-32 11-45 3-15 8-33 7-53-4v53Z"></path>
        <path class="svg-book-left" d="M20 39c16 7 30 8 43 2v39c-13 5-27 4-43-4V39Z"></path>
        <path class="svg-book-right" d="M72 41c11 5 22 4 34-2v39c-13 7-24 8-34 2V41Z"></path>
        <path class="svg-book-fold" d="M67 34v55"></path>
        <path class="svg-book-line" d="M30 53h21M30 64h18M83 52h14M83 63h17"></path>
      </svg>
    `,
    star: `
      <svg viewBox="0 0 120 120" role="img" aria-label="star">
        <path class="svg-shadow" d="M61 13l13 29 32 3-24 22 7 31-28-16-28 16 7-31-24-22 32-3 13-29Z"></path>
        <path class="svg-outline" d="M60 9l14 31 34 4-25 23 7 34-30-17-30 17 7-34-25-23 34-4 14-31Z"></path>
        <path class="svg-star-fill" d="M60 18l11 27 29 3-22 19 6 28-24-15-24 15 6-28-22-19 29-3 11-27Z"></path>
        <path class="svg-shine" d="M50 39c5-8 11-12 18-13"></path>
      </svg>
    `,
    apple: `
      <svg viewBox="0 0 120 120" role="img" aria-label="apple">
        <path class="svg-shadow" d="M61 31c9-10 27-11 38 4 13 19 3 58-25 68-5 2-9-1-14-1s-10 3-15 1C17 93 7 54 20 35c11-15 29-14 38-4h3Z"></path>
        <path class="svg-stem" d="M60 28c1-12 7-20 18-24"></path>
        <path class="svg-leaf" d="M70 18c13-8 26-5 32 8-14 7-25 5-32-8Z"></path>
        <path class="svg-outline" d="M60 31c9-11 28-12 39 4 13 20 2 58-25 68-6 2-10-2-14-2s-9 4-15 2C18 93 7 55 21 35c11-16 30-15 39-4Z"></path>
        <path class="svg-apple-fill" d="M60 39c8-9 23-10 31 3 10 16 1 44-20 52-5 2-8-2-11-2s-7 4-12 2c-21-8-30-36-20-52 8-13 24-12 32-3Z"></path>
        <path class="svg-shine" d="M41 48c5-7 12-9 20-8"></path>
      </svg>
    `,
    box: `
      <svg viewBox="0 0 120 120" role="img" aria-label="box">
        <path class="svg-shadow" d="M22 40l38-18 39 18v49l-39 20-38-20V40Z"></path>
        <path class="svg-outline" d="M18 36l42-20 43 20v51l-43 22-42-22V36Z"></path>
        <path class="svg-box-top" d="M18 36l42 19 43-19-43-20-42 20Z"></path>
        <path class="svg-box-left" d="M18 36l42 19v54L18 87V36Z"></path>
        <path class="svg-box-right" d="M60 55l43-19v51l-43 22V55Z"></path>
        <path class="svg-box-line" d="M60 55v54M36 45l42-20"></path>
      </svg>
    `,
  };
  drawing.innerHTML = drawings[objectId] ?? drawings.ball;
  return drawing;
}

function createForestSchoolAnswerButton(answerYes) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `forest-school-answer ${answerYes ? "yes" : "no"}`;
  button.disabled = state.forestSchoolPhase !== "question";
  button.setAttribute("aria-label", answerYes ? "Yes" : "No");

  const icon = document.createElement("span");
  icon.className = "forest-school-answer-icon";
  icon.textContent = answerYes ? "OK" : "X";

  const label = document.createElement("span");
  label.className = "forest-school-answer-label";
  label.textContent = answerYes ? "YES" : "NO";

  button.appendChild(icon);
  button.appendChild(label);
  button.addEventListener("click", async (event) => {
    event.stopPropagation();
    await primeAudio();
    await handleForestSchoolAnswer(answerYes);
  });
  return button;
}

function createForestSchoolDebugButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "owl-garden-debug-skip";
  button.style.left = `${forestSchoolDebugRect.x}%`;
  button.style.top = `${forestSchoolDebugRect.y}%`;
  button.style.width = `${forestSchoolDebugRect.w}%`;
  button.style.height = `${forestSchoolDebugRect.h}%`;
  button.setAttribute("aria-label", "Debug forest school");
  button.addEventListener("click", async (event) => {
    event.stopPropagation();
    await primeAudio();
    setScene("forestSchool");
  });
  return button;
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
  if (!state.owlGardenRemainingNumbers.length) {
    state.owlGardenRemainingNumbers = shuffledOwlGardenNumbers();
  }
  const numberValue = state.owlGardenRemainingNumbers.pop();
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

async function handleHouseBunnySelection(colorId) {
  if (state.currentScene !== "houseBunny" || state.houseBunnyPhase !== "waiting") {
    return;
  }

  if (colorId !== state.houseBunnyTargetId) {
    state.houseBunnyPhase = "retry";
    renderScene();
    await speakHouseBunnyLine("Try again.");
    if (state.currentScene === "houseBunny") {
      state.houseBunnyPhase = "waiting";
      renderScene();
    }
    return;
  }

  const sequenceId = state.sequenceId;
  state.houseBunnyPhase = "result";
  state.houseBunnyScore += 1;
  renderScene();
  await speakHouseBunnyLine("Excellent.");
  if (!isSceneActive("houseBunny", sequenceId)) {
    return;
  }

  state.houseBunnyImageStep = 2;
  renderScene();
  await pauseMs(360);
  if (!isSceneActive("houseBunny", sequenceId)) {
    return;
  }

  state.houseBunnyImageStep = 3;
  state.houseBunnyDartColorId = colorId;
  renderScene();
  await pauseMs(2000);
  if (!isSceneActive("houseBunny", sequenceId)) {
    return;
  }

  if (state.houseBunnyScore >= houseBunnyWinCount) {
    await speakHouseBunnyLine("Great job. Let's go to forest school.");
    if (isSceneActive("houseBunny", sequenceId)) {
      setScene("forestSchool");
    }
    return;
  }

  await queueNextHouseBunnyColor(sequenceId, 420);
}

async function handleForestSchoolAnswer(answerYes) {
  if (state.currentScene !== "forestSchool" || state.forestSchoolPhase !== "question") {
    return;
  }

  const sequenceId = state.sequenceId;
  state.forestSchoolPhase = "checking";
  renderScene();
  await speakEnglishLine(answerYes ? "yes" : "no", { preferredVoiceName: "samantha|ava|victoria|karen", rate: 0.9, pitch: 1.02 });
  if (!isSceneActive("forestSchool", sequenceId)) {
    return;
  }

  if (answerYes !== state.forestSchoolAnswerYes) {
    state.forestSchoolPhase = "retry";
    renderScene();
    await speakForestSchoolOwlLine("Try again.");
    if (isSceneActive("forestSchool", sequenceId)) {
      state.forestSchoolPhase = "question";
      renderScene();
      await speakForestSchoolOwlLine(`Is this a ${state.forestSchoolQuestionWord}?`);
    }
    return;
  }

  state.forestSchoolScore += 1;
  state.forestSchoolPhase = "done";
  renderScene();
  await speakForestSchoolOwlLine("Excellent.");
  if (!isSceneActive("forestSchool", sequenceId)) {
    return;
  }

  if (state.forestSchoolScore >= forestSchoolWinCount) {
    state.forestSchoolPhase = "finished";
    renderScene();
    await speakForestSchoolOwlLine("Great job. Forest school is finished.");
    return;
  }

  await queueNextForestSchoolQuestion(sequenceId, 650);
}

function debugSkipOwlGarden() {
  if (state.currentScene !== "owlGarden") {
    return;
  }

  if (state.owlGardenPhase === "outro") {
    setScene("houseBunny");
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

const requestedScene = new URLSearchParams(window.location.search).get("scene");
setScene(requestedScene === "forestSchool" ? "forestSchool" : "intro1");
