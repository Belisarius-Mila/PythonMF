const sceneTitle = document.getElementById("sceneTitle");
const bottomTitle = document.getElementById("bottomTitle");
const bottomSubtitle = document.getElementById("bottomSubtitle");
const overlay = document.getElementById("overlay");
const speechBubble = document.getElementById("speechBubble");
const repeatButton = document.getElementById("repeatButton");
const colorsModeButton = document.getElementById("colorsMode");
const numbersModeButton = document.getElementById("numbersMode");

const numberWords = {
  1: "One",
  2: "Two",
  3: "Three",
  4: "Four",
  5: "Five",
};

const colorHotspots = [
  { id: "red", word: "Red", color: "#ff6464", rect: { x: 2.5, y: 21.5, w: 26.4, h: 26.8 } },
  { id: "blue", word: "Blue", color: "#5f8bff", rect: { x: 22.7, y: 34.8, w: 12.6, h: 23.6 } },
  { id: "green", word: "Green", color: "#6ed76a", rect: { x: 58.0, y: 53.4, w: 18.4, h: 18.5 } },
  { id: "orange", word: "Orange", color: "#ffb14f", rect: { x: 73.6, y: 30.1, w: 21.8, h: 21.2 } },
];

const numberHotspots = [
  { id: "red_1", group: "red", color: "#ff6464", rect: { x: 6.5, y: 29.3, w: 18.2, h: 10.4 }, label: { x: 15.6, y: 38.4 } },
  { id: "red_2", group: "red", color: "#ff6464", rect: { x: 4.7, y: 61.5, w: 8.3, h: 7.8 }, label: { x: 7.2, y: 69.1 } },
  { id: "blue_1", group: "blue", color: "#5f8bff", rect: { x: 26.4, y: 43.2, w: 8.2, h: 10.3 }, label: { x: 30.7, y: 51.0 } },
  { id: "blue_2", group: "blue", color: "#5f8bff", rect: { x: 29.7, y: 61.0, w: 5.6, h: 8.4 }, label: { x: 32.8, y: 72.2 } },
  { id: "blue_3", group: "blue", color: "#5f8bff", rect: { x: 23.4, y: 71.2, w: 4.6, h: 6.8 }, label: { x: 24.6, y: 76.3 } },
  { id: "green_1", group: "green", color: "#6ed76a", rect: { x: 61.7, y: 65.2, w: 7.8, h: 7.8 }, label: { x: 65.6, y: 74.8 } },
  { id: "green_2", group: "green", color: "#6ed76a", rect: { x: 57.7, y: 78.5, w: 5.9, h: 6.9 }, label: { x: 59.9, y: 84.6 } },
  { id: "green_3", group: "green", color: "#6ed76a", rect: { x: 67.3, y: 78.5, w: 5.9, h: 6.7 }, label: { x: 69.9, y: 85.1 } },
  { id: "green_4", group: "green", color: "#6ed76a", rect: { x: 74.0, y: 85.4, w: 5.7, h: 5.9 }, label: { x: 76.4, y: 90.3 } },
  { id: "orange_1", group: "orange", color: "#ffb14f", rect: { x: 75.0, y: 38.3, w: 10.0, h: 4.4 }, label: { x: 79.5, y: 39.9 } },
  { id: "orange_2", group: "orange", color: "#ffb14f", rect: { x: 86.1, y: 42.7, w: 6.6, h: 3.4 }, label: { x: 89.9, y: 43.6 } },
  { id: "orange_3", group: "orange", color: "#ffb14f", rect: { x: 75.2, y: 49.5, w: 10.2, h: 4.2 }, label: { x: 80.1, y: 50.9 } },
  { id: "orange_4", group: "orange", color: "#ffb14f", rect: { x: 87.3, y: 54.1, w: 8.4, h: 3.6 }, label: { x: 90.4, y: 55.5 } },
  { id: "orange_5", group: "orange", color: "#ffb14f", rect: { x: 75.2, y: 65.8, w: 16.4, h: 6.2 }, label: { x: 83.8, y: 67.3 } },
];

const state = {
  mode: "colors",
  activeId: "",
  bubbleText: "",
  bubbleTimeoutId: null,
  revealedNumbers: {},
  groupCounts: {
    red: 0,
    blue: 0,
    green: 0,
    orange: 0,
  },
};

function setMode(mode) {
  state.mode = mode;
  state.activeId = "";
  state.bubbleText = "";
  state.revealedNumbers = {};
  state.groupCounts = { red: 0, blue: 0, green: 0, orange: 0 };
  render();
  speakInstruction();
}

function currentHotspots() {
  return state.mode === "colors" ? colorHotspots : numberHotspots;
}

function speak(text) {
  if (!("speechSynthesis" in window)) {
    showBubble(text);
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  utterance.rate = 0.86;
  utterance.pitch = 1.0;
  const englishVoice = window.speechSynthesis
    .getVoices()
    .find((voice) => voice.lang.toLowerCase().startsWith("en"));
  if (englishVoice) {
    utterance.voice = englishVoice;
  }
  window.speechSynthesis.speak(utterance);
}

function speakInstruction() {
  if (state.mode === "colors") {
    speak("Click a mushroom");
  } else {
    speak("Click mushrooms and count");
  }
}

function showBubble(text) {
  state.bubbleText = text;
  speechBubble.textContent = text;
  speechBubble.classList.remove("hidden");
  if (state.bubbleTimeoutId) {
    window.clearTimeout(state.bubbleTimeoutId);
  }
  state.bubbleTimeoutId = window.setTimeout(() => {
    state.bubbleText = "";
    speechBubble.classList.add("hidden");
  }, 1600);
}

function createHotspotButton(hotspot) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "hotspot";
  if (state.activeId === hotspot.id) {
    button.classList.add("active");
  }

  button.style.left = `${hotspot.rect.x}%`;
  button.style.top = `${hotspot.rect.y}%`;
  button.style.width = `${hotspot.rect.w}%`;
  button.style.height = `${hotspot.rect.h}%`;
  button.style.setProperty("--hotspot-glow", hotspot.color);
  button.setAttribute("aria-label", hotspot.id);
  button.addEventListener("click", () => activateHotspot(hotspot));
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

function activateHotspot(hotspot) {
  state.activeId = hotspot.id;

  if (state.mode === "colors") {
    showBubble(hotspot.word);
    speak(hotspot.word);
    render();
    return;
  }

  let numberValue = state.revealedNumbers[hotspot.id];
  if (!numberValue) {
    state.groupCounts[hotspot.group] += 1;
    numberValue = state.groupCounts[hotspot.group];
    state.revealedNumbers[hotspot.id] = numberValue;
  }

  const word = numberWords[numberValue] ?? String(numberValue);
  showBubble(word);
  speak(word);
  render();
}

function updateTexts() {
  const isColors = state.mode === "colors";
  sceneTitle.textContent = isColors ? "MMTX - Barevne houby" : "MMTX - Pocitani hub";
  bottomTitle.textContent = isColors
    ? "Klikni na houbu a ozve se barva."
    : "Klikni na jednotlive houby a uslysis cislo.";
  bottomSubtitle.textContent = isColors
    ? "Cil: Red, Blue, Green, Orange"
    : "Prvni klik v barve da one, druhy two, treti three.";

  colorsModeButton.classList.toggle("active", isColors);
  numbersModeButton.classList.toggle("active", !isColors);
}

function render() {
  updateTexts();
  overlay.innerHTML = "";

  currentHotspots().forEach((hotspot) => {
    overlay.appendChild(createHotspotButton(hotspot));
  });

  if (state.mode === "numbers") {
    numberHotspots.forEach((hotspot) => {
      const numberValue = state.revealedNumbers[hotspot.id];
      if (numberValue) {
        overlay.appendChild(createNumberTag(hotspot, numberValue));
      }
    });
  }

  if (state.bubbleText) {
    speechBubble.textContent = state.bubbleText;
    speechBubble.classList.remove("hidden");
  } else {
    speechBubble.classList.add("hidden");
  }
}

repeatButton.addEventListener("click", () => {
  speakInstruction();
});

colorsModeButton.addEventListener("click", () => {
  setMode("colors");
});

numbersModeButton.addEventListener("click", () => {
  setMode("numbers");
});

window.speechSynthesis?.addEventListener?.("voiceschanged", () => {});

render();
window.setTimeout(speakInstruction, 350);
