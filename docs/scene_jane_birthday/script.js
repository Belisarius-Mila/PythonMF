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
const friendsLayer = document.getElementById("friendsLayer");
const musicButton = document.getElementById("musicButton");

const assetVersion = "20260825a";

const characterPositions = {
  All: { x: 50, y: 67 },
  Benji: { x: 19, y: 70 },
  Bunny: { x: 34, y: 68 },
  Bruno: { x: 50, y: 66 },
  Fiona: { x: 66, y: 68 },
  Sunny: { x: 81, y: 71 },
};

const friendOrder = ["Benji", "Bunny", "Bruno", "Fiona", "Sunny"];

const dialogue = [
  {
    speaker: "Benji",
    en: "Hello, I am Benji.",
    cz: "Ahoj, já jsem Benji.",
    audioEn: `audio/english/jane_birthday_01_benji_hello_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/jane_birthday_01_benji_hello_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Benji",
    en: "Jane, today is your birthday. I wish you good health and lots of energy.",
    cz: "Jane, dnes máš narozeniny. Přeji ti hodně zdraví a energie.",
    audioEn: `audio/english/jane_birthday_02_benji_wish_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/jane_birthday_02_benji_wish_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Bunny",
    en: "Hello, I am Bunny.",
    cz: "Ahoj, já jsem Bunny.",
    audioEn: `audio/english/jane_birthday_03_bunny_hello_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/jane_birthday_03_bunny_hello_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Bunny",
    en: "I wish you happiness and many reasons to smile.",
    cz: "Přeji ti štěstí a mnoho důvodů k úsměvu.",
    audioEn: `audio/english/jane_birthday_04_bunny_wish_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/jane_birthday_04_bunny_wish_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Bruno",
    en: "Hello, I am Bruno.",
    cz: "Ahoj, já jsem Bruno.",
    audioEn: `audio/english/jane_birthday_05_bruno_hello_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/jane_birthday_05_bruno_hello_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Bruno",
    en: "I wish you good friends and many happy adventures.",
    cz: "Přeji ti dobré kamarády a mnoho veselých dobrodružství.",
    audioEn: `audio/english/jane_birthday_06_bruno_wish_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/jane_birthday_06_bruno_wish_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Fiona",
    en: "Hello, I am Fiona.",
    cz: "Ahoj, já jsem Fiona.",
    audioEn: `audio/english/jane_birthday_07_fiona_hello_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/jane_birthday_07_fiona_hello_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Fiona",
    en: "I wish you a lovely party full of laughter.",
    cz: "Přeji ti krásnou oslavu plnou smíchu.",
    audioEn: `audio/english/jane_birthday_08_fiona_wish_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/jane_birthday_08_fiona_wish_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Sunny",
    en: "Hello, I am Sunny.",
    cz: "Ahoj, já jsem Sunny.",
    audioEn: `audio/english/jane_birthday_09_sunny_hello_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/jane_birthday_09_sunny_hello_cz.mp3?v=${assetVersion}`,
  },
  {
    speaker: "Sunny",
    en: "I wish you beautiful dreams that come true.",
    cz: "Přeji ti krásné sny, které se splní.",
    audioEn: `audio/english/jane_birthday_10_sunny_wish_en.mp3?v=${assetVersion}`,
    audioCz: `audio/czech/jane_birthday_10_sunny_wish_cz.mp3?v=${assetVersion}`,
  },
];

const birthdaySong = {
  speaker: "All friends",
  en: "Jane, today is your special day.\nSmile and laugh and dance and play.\nWe wish you joy the whole year through.\nYour forest friends are here for you.",
  cz: "Jane, dnes je tvůj výjimečný den.\nUsmívej se, směj se, tancuj a hraj si.\nPřejeme ti radost po celý rok.\nTvoji lesní kamarádi jsou tu pro tebe.",
  audioEn: `audio/english/jane_birthday_11_song_en.mp3?v=${assetVersion}`,
};

const sleep = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

let currentAudio = null;
let currentMusicContext = null;
let runToken = 0;
let sceneActive = false;
let isBusy = false;
let activeSpeaker = "";
let completedSpeakers = new Set();
const hotspotButtons = new Map();

const dialogueBySpeaker = dialogue.reduce((groups, entry) => {
  if (!groups.has(entry.speaker)) groups.set(entry.speaker, []);
  groups.get(entry.speaker).push(entry);
  return groups;
}, new Map());

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

function buildHotspots() {
  for (const speaker of friendOrder) {
    const position = characterPositions[speaker];
    const button = document.createElement("button");
    const mark = document.createElement("span");
    button.type = "button";
    button.className = "character-hotspot";
    button.style.left = `${position.x}%`;
    button.style.top = `${position.y}%`;
    button.setAttribute("aria-label", `${speaker} birthday wish`);
    mark.className = "hotspot-mark";
    mark.setAttribute("aria-hidden", "true");
    mark.textContent = "♡";
    button.appendChild(mark);
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      playFriendWish(speaker);
    });
    hotspotButtons.set(speaker, button);
    friendsLayer.appendChild(button);
  }
}

function updateHotspots() {
  for (const [speaker, button] of hotspotButtons.entries()) {
    const mark = button.querySelector(".hotspot-mark");
    button.disabled = !sceneActive || isBusy;
    button.classList.toggle("active", speaker === activeSpeaker);
    button.classList.toggle("done", completedSpeakers.has(speaker));
    mark.textContent = completedSpeakers.has(speaker) ? "✓" : "♡";
  }
}

function allWishesDone() {
  return friendOrder.every((speaker) => completedSpeakers.has(speaker));
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

function startScene() {
  runToken += 1;
  stopAudio();
  sceneActive = true;
  isBusy = false;
  activeSpeaker = "";
  completedSpeakers = new Set();
  startButton.disabled = true;
  replayButton.disabled = false;
  startGate.classList.add("hidden");
  completeBanner.classList.add("hidden");
  characterGlow.classList.remove("visible");
  speechBubble.classList.add("hidden");
  musicButton.classList.add("hidden");
  musicButton.disabled = true;
  scene.classList.add("ready");
  updateHotspots();
}

async function playFriendWish(speaker) {
  if (!sceneActive || isBusy) return;

  const entries = dialogueBySpeaker.get(speaker) || [];
  const token = runToken;
  isBusy = true;
  activeSpeaker = speaker;
  musicButton.disabled = true;
  musicButton.classList.add("hidden");
  updateHotspots();

  for (const entry of entries) {
    if (token !== runToken) return;
    await playEntry(entry, token);
  }

  if (token !== runToken) return;
  completedSpeakers.add(speaker);
  activeSpeaker = "";
  isBusy = false;
  updateHotspots();

  if (allWishesDone()) {
    characterGlow.classList.remove("visible");
    speechBubble.classList.add("hidden");
    musicButton.disabled = false;
    musicButton.classList.remove("hidden");
  }
}

async function playFinalSong() {
  if (!sceneActive || isBusy || !allWishesDone()) return;

  const token = runToken;
  isBusy = true;
  musicButton.disabled = true;
  activeSpeaker = "";
  updateHotspots();

  await playSong(token);

  if (token !== runToken) return;
  stopAudio();
  isBusy = false;
  sceneActive = false;
  characterGlow.classList.remove("visible");
  speechBubble.classList.add("hidden");
  musicButton.classList.add("hidden");
  scene.classList.remove("ready");
  updateHotspots();
  completeBanner.classList.remove("hidden");
  startButton.disabled = false;
  replayButton.disabled = false;
}

function resetScene() {
  runToken += 1;
  stopAudio();
  sceneActive = false;
  isBusy = false;
  activeSpeaker = "";
  completedSpeakers = new Set();
  speechBubble.classList.add("hidden");
  characterGlow.classList.remove("visible");
  completeBanner.classList.add("hidden");
  musicButton.classList.add("hidden");
  musicButton.disabled = true;
  scene.classList.remove("ready");
  startGate.classList.remove("hidden");
  startButton.disabled = false;
  replayButton.disabled = false;
  updateHotspots();
}

startButton.addEventListener("click", (event) => {
  event.stopPropagation();
  startScene();
});

replayButton.addEventListener("click", (event) => {
  event.stopPropagation();
  resetScene();
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

musicButton.addEventListener("click", (event) => {
  event.stopPropagation();
  playFinalSong();
});

buildHotspots();
updateHotspots();
