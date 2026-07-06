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

const assetVersion = "20260706a";

const characterPositions = {
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

const sleep = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

let currentAudio = null;
let runToken = 0;

function stopAudio() {
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
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
