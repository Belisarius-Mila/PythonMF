const storyStage = document.getElementById("storyStage");
const sceneImage = document.getElementById("sceneImage");
const magnifierButton = document.getElementById("magnifierButton");
const clickPrompt = document.getElementById("clickPrompt");
const mushroomPortalButton = document.getElementById("mushroomPortalButton");
const mushroomHud = document.getElementById("mushroomHud");
const backToSignpostButton = document.getElementById("backToSignpostButton");
const colorsModeButton = document.getElementById("colorsModeButton");
const numbersModeButton = document.getElementById("numbersModeButton");
const mushroomOverlay = document.getElementById("mushroomOverlay");

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

const state = {
  currentScene: "intro1",
  sequenceId: 0,
  timeouts: [],
  audioContext: null,
  crackleTimerId: null,
  currentVoiceAudio: null,
  audioUnlocked: false,
  mushroomMode: "colors",
  activeHotspotId: "",
  revealedNumbers: {},
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
};

function clearSceneTimers() {
  state.timeouts.forEach((timeoutId) => window.clearTimeout(timeoutId));
  state.timeouts = [];
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
  if (state.currentVoiceAudio) {
    state.currentVoiceAudio.pause();
    state.currentVoiceAudio.currentTime = 0;
    state.currentVoiceAudio = null;
  }
}

function unlockAudio() {
  state.audioUnlocked = true;
  resumeAudioContext();
}
function playAudioElement(audio) {
  return new Promise((resolve) => {
    let resolved = false;
    const finish = () => {
      if (resolved) {
        return;
      }
      resolved = true;
      resolve();
    };

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
  if (!("speechSynthesis" in window) || !state.audioUnlocked) {
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  utterance.rate = 0.86;
  utterance.pitch = 1.0;
  const englishVoice = window.speechSynthesis
    .getVoices()
    .find((voice) => voice.lang && voice.lang.toLowerCase().startsWith("en"));
  if (englishVoice) {
    utterance.voice = englishVoice;
  }
  window.speechSynthesis.speak(utterance);
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
  sceneImage.src = scene.image;
  magnifierButton.classList.toggle("hidden", state.currentScene !== "intro2");
  clickPrompt.classList.toggle("hidden", state.audioUnlocked || state.currentScene === "intro4");
  mushroomPortalButton.classList.toggle("hidden", state.currentScene !== "intro4");
  mushroomHud.classList.toggle("hidden", state.currentScene !== "mushrooms");
  mushroomOverlay.classList.toggle("hidden", state.currentScene !== "mushrooms");
  if (state.currentScene === "mushrooms") {
    renderMushrooms();
  } else {
    mushroomOverlay.innerHTML = "";
  }
}

function cleanupCurrentScene() {
  clearSceneTimers();
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
}

function setMushroomMode(mode) {
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

backToSignpostButton.addEventListener("click", (event) => {
  event.stopPropagation();
  setScene("intro4");
});

colorsModeButton.addEventListener("click", (event) => {
  event.stopPropagation();
  setMushroomMode("colors");
});

numbersModeButton.addEventListener("click", (event) => {
  event.stopPropagation();
  setMushroomMode("numbers");
});

window.addEventListener("pointerdown", () => {
  primeAudio();
}, { once: true });

window.addEventListener("keydown", () => {
  primeAudio();
}, { once: true });

window.speechSynthesis?.addEventListener?.("voiceschanged", () => {});

setScene("intro1");
