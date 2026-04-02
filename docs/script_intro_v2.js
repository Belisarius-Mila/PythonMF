const storyStage = document.getElementById("storyStage");
const sceneImage = document.getElementById("sceneImage");
const magnifierButton = document.getElementById("magnifierButton");
const clickPrompt = document.getElementById("clickPrompt");

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
};

const state = {
  currentScene: "intro1",
  sequenceId: 0,
  timeouts: [],
  audioContext: null,
  crackleTimerId: null,
  currentVoiceAudio: null,
  audioUnlocked: false,
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

window.addEventListener("pointerdown", () => {
  primeAudio();
}, { once: true });

window.addEventListener("keydown", () => {
  primeAudio();
}, { once: true });

setScene("intro1");
