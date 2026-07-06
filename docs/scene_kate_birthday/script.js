const scene = document.getElementById("scene");
const startButton = document.getElementById("startButton");
const replayButton = document.getElementById("replayButton");
const backButton = document.getElementById("backButton");
const nextButton = document.getElementById("nextButton");
const speechBubble = document.getElementById("speechBubble");
const speakerName = document.getElementById("speakerName");
const lineText = document.getElementById("lineText");
const lineTranslation = document.getElementById("lineTranslation");
const startGate = document.getElementById("startGate");
const completeBanner = document.getElementById("completeBanner");
const characterGlow = document.getElementById("characterGlow");

const assetVersion = "20260706c";

const characterPositions = {
  All: { x: 50, y: 67 },
  Benji: { x: 19, y: 70 },
  Bunny: { x: 34, y: 68 },
  Bruno: { x: 50, y: 66 },
  Fiona: { x: 66, y: 68 },
  Sunny: { x: 81, y: 71 },
};

const dialogue = [
  {
    speaker: "Benji",
    en: "Hello, I am Benji.",
    cz: "Ahoj, já jsem Benji.",
    audioEn: `audio/english/kate_birthday_01_benji_hello_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/kate_birthday_01_benji_hello_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Benji",
    en: "Kate, you have a birthday today. I wish you good health.",
    cz: "Katko, dnes máš narozeniny. Přeji ti hodně zdraví.",
    audioEn: `audio/english/kate_birthday_02_benji_wish_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/kate_birthday_02_benji_wish_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Bunny",
    en: "Hello, I am Bunny.",
    cz: "Ahoj, já jsem Bunny.",
    audioEn: `audio/english/kate_birthday_03_bunny_hello_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/kate_birthday_03_bunny_hello_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Bunny",
    en: "I wish you happiness.",
    cz: "Přeji ti štěstí.",
    audioEn: `audio/english/kate_birthday_04_bunny_wish_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/kate_birthday_04_bunny_wish_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Bruno",
    en: "Hello, I am Bruno.",
    cz: "Ahoj, já jsem Bruno.",
    audioEn: `audio/english/kate_birthday_05_bruno_hello_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/kate_birthday_05_bruno_hello_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Bruno",
    en: "I wish you good friends.",
    cz: "Přeji ti dobré kamarády.",
    audioEn: `audio/english/kate_birthday_06_bruno_wish_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/kate_birthday_06_bruno_wish_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Fiona",
    en: "Hello, I am Fiona.",
    cz: "Ahoj, já jsem Fiona.",
    audioEn: `audio/english/kate_birthday_07_fiona_hello_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/kate_birthday_07_fiona_hello_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Fiona",
    en: "I wish you a nice party today.",
    cz: "Přeji ti dnes hezkou oslavu.",
    audioEn: `audio/english/kate_birthday_08_fiona_wish_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/kate_birthday_08_fiona_wish_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Sunny",
    en: "Hello, I am Sunny.",
    cz: "Ahoj, já jsem Sunny.",
    audioEn: `audio/english/kate_birthday_09_sunny_hello_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/kate_birthday_09_sunny_hello_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Sunny",
    en: "I wish you that all your dreams come true.",
    cz: "Přeji ti, aby se ti splnily všechny sny.",
    audioEn: `audio/english/kate_birthday_10_sunny_wish_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/kate_birthday_10_sunny_wish_cz.mp3?v=${assetVersion}`,
  },
];

const birthdaySong = {
  speaker: "All friends",
  en: "Kate, it is your special day.\nSmile and laugh and dance and play.\nWe wish you joy in all you do.\nYour forest friends are cheering for you.",
  cz: "Katko, dnes je tvůj výjimečný den.\nUsmívej se, směj se, tancuj a hraj si.\nPřejeme ti radost ve všem, co děláš.\nTvoji lesní kamarádi ti fandí.",
  audioEn: `audio/english/kate_birthday_11_song_en.mp3?v=${assetVersion}`,
};

const sleep = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

let currentAudio = null;
let currentMusicContext = null;
let runToken = 0;

function stopAudio() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
  if (currentMusicContext) {
    currentMusicContext.close().catch(() => {});
    currentMusicContext = null;
  }
}

function showSpeaker(speaker) {
  const position = characterPositions[speaker] || { x: 50, y: 70 };
  characterGlow.style.left = `${position.x}%`;
  characterGlow.style.top = `${position.y}%`;
  characterGlow.classList.add("visible");
}

function setLine(entry, translationVisible) {
  speakerName.textContent = entry.speaker;
  lineText.textContent = entry.en;
  lineTranslation.textContent = translationVisible ? entry.cz : "";
  speechBubble.classList.remove("hidden");
  showSpeaker(entry.speaker);
}

function playAudio(src) {
  return new Promise((resolve) => {
    stopAudio();
    const audio = new Audio(src);
    currentAudio = audio;
    audio.addEventListener("ended", resolve, { once: true });
    audio.addEventListener("error", resolve, { once: true });
    audio.play().catch(resolve);
  });
}

function playBirthdayTune(token) {
  const AudioContext = window.AudioContext || window.webkitAudioContext;
  if (!AudioContext) return sleep(0);

  const context = new AudioContext();
  currentMusicContext = context;
  const masterGain = context.createGain();
  masterGain.gain.value = 0.045;
  masterGain.connect(context.destination);

  const notes = [
    [523.25, 0.25], [587.33, 0.25], [659.25, 0.38], [783.99, 0.38],
    [659.25, 0.3], [587.33, 0.3], [523.25, 0.48],
    [659.25, 0.25], [698.46, 0.25], [783.99, 0.42], [880.0, 0.42],
    [783.99, 0.3], [659.25, 0.3], [587.33, 0.56],
    [523.25, 0.26], [659.25, 0.26], [783.99, 0.5], [1046.5, 0.68],
  ];

  let time = context.currentTime + 0.08;
  for (const [frequency, duration] of notes) {
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.type = "triangle";
    oscillator.frequency.value = frequency;
    gain.gain.setValueAtTime(0, time);
    gain.gain.linearRampToValueAtTime(0.9, time + 0.025);
    gain.gain.exponentialRampToValueAtTime(0.001, time + duration);
    oscillator.connect(gain).connect(masterGain);
    oscillator.start(time);
    oscillator.stop(time + duration + 0.04);
    time += duration + 0.055;
  }

  const totalMs = Math.max(0, (time - context.currentTime) * 1000);
  return sleep(totalMs).then(() => {
    if (token === runToken && currentMusicContext === context) {
      currentMusicContext = null;
      return context.close().catch(() => {});
    }
    return undefined;
  });
}

async function playEntry(entry, token) {
  setLine(entry, false);
  await playAudio(entry.audioEn);
  if (token !== runToken) return;
  await sleep(220);
  setLine(entry, true);
  await playAudio(entry.audioCz);
  if (token !== runToken) return;
  await sleep(360);
}

async function playSong(token) {
  speakerName.textContent = birthdaySong.speaker;
  lineText.textContent = birthdaySong.en;
  lineTranslation.textContent = birthdaySong.cz;
  speechBubble.classList.remove("hidden");
  showSpeaker("All");

  const audioPromise = playAudio(birthdaySong.audioEn);
  await sleep(160);
  const tunePromise = playBirthdayTune(token);
  await audioPromise;
  if (token !== runToken) return;
  await tunePromise;
  if (token !== runToken) return;
  await sleep(500);
}

async function startScene() {
  runToken += 1;
  const token = runToken;
  startButton.disabled = true;
  replayButton.disabled = true;
  startGate.classList.add("hidden");
  completeBanner.classList.add("hidden");

  for (const entry of dialogue) {
    if (token !== runToken) return;
    await playEntry(entry, token);
  }

  if (token !== runToken) return;
  await playSong(token);

  if (token !== runToken) return;
  stopAudio();
  characterGlow.classList.remove("visible");
  speechBubble.classList.add("hidden");
  completeBanner.classList.remove("hidden");
  startButton.disabled = false;
  replayButton.disabled = false;
}

function resetScene() {
  runToken += 1;
  stopAudio();
  speechBubble.classList.add("hidden");
  characterGlow.classList.remove("visible");
  completeBanner.classList.add("hidden");
  startGate.classList.remove("hidden");
  startButton.disabled = false;
  replayButton.disabled = false;
}

startButton.addEventListener("click", (event) => {
  event.stopPropagation();
  startScene();
});

replayButton.addEventListener("click", (event) => {
  event.stopPropagation();
  resetScene();
  startScene();
});

scene.addEventListener("click", () => {
  if (!startGate.classList.contains("hidden")) {
    startScene();
  }
});

backButton.addEventListener("click", (event) => {
  event.stopPropagation();
  window.location.href = "../index.html?scene=intro4";
});

nextButton.addEventListener("click", (event) => {
  event.stopPropagation();
  window.location.href = "../scene02_sunnys_lost_nuts/index.html";
});
