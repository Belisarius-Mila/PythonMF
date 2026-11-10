"use strict";

const startButton = document.getElementById("startButton");
const nextButton = document.getElementById("nextButton");
const repeatButton = document.getElementById("repeatButton");
const restartButton = document.getElementById("restartButton");
const speechBubble = document.getElementById("speechBubble");
const speakerName = document.getElementById("speakerName");
const speechText = document.getElementById("speechText");
const lineNumber = document.getElementById("lineNumber");
const status = document.getElementById("status");
let lines = [];
let index = -1;
let activeAudio = null;
let generation = 0;
let playing = false;
let failed = false;

function updateControls() {
  repeatButton.disabled = index < 0 || playing;
  nextButton.disabled = playing || failed || index >= lines.length - 1;
  nextButton.hidden = index < 0 || index >= lines.length - 1;
  restartButton.hidden = index < 0 || index !== lines.length - 1 || playing || failed;
}

function stopAudio() {
  generation += 1;
  if (activeAudio) {
    activeAudio.onended = null;
    activeAudio.onerror = null;
    activeAudio.pause();
    activeAudio = null;
  }
  playing = false;
}

function playLine(newIndex) {
  if (!Number.isInteger(newIndex) || !lines[newIndex]) return;
  stopAudio();
  index = newIndex;
  const line = lines[index];
  const token = generation;
  speakerName.textContent = line.speaker;
  speechText.textContent = line.text;
  lineNumber.textContent = `${index + 1} / ${lines.length}`;
  speechBubble.hidden = false;
  startButton.hidden = true;
  status.textContent = "";
  status.classList.remove("error");
  failed = false;
  playing = true;
  updateControls();
  const audio = new Audio(line.audio);
  activeAudio = audio;
  const settle = (error) => {
    if (token !== generation || activeAudio !== audio) return;
    audio.onended = null;
    audio.onerror = null;
    audio.pause();
    activeAudio = null;
    playing = false;
    failed = error;
    status.classList.toggle("error", error);
    status.textContent = error ? "Audio unavailable. Tap Repeat." :
      (index === lines.length - 1 ? "The Lake · Picture 1 complete" : "");
    updateControls();
  };
  audio.onended = () => settle(false);
  audio.onerror = () => settle(true);
  try {
    const promise = audio.play();
    if (promise) promise.catch(() => settle(true));
  } catch (_error) { settle(true); }
}

startButton.addEventListener("click", () => { if (index < 0 && lines.length) playLine(0); });
nextButton.addEventListener("click", () => { if (!playing && !failed) playLine(index + 1); });
repeatButton.addEventListener("click", () => { if (!playing) playLine(index); });
restartButton.addEventListener("click", () => { if (!playing) playLine(0); });
window.addEventListener("pagehide", () => { stopAudio(); updateControls(); });
window.addEventListener("pageshow", () => { if (!playing) updateControls(); });

fetch("dialogue.json?v=20261110opening1")
  .then((response) => { if (!response.ok) throw new Error("dialogue"); return response.json(); })
  .then((data) => {
    if (data.schema_version !== 1 || !Array.isArray(data.lines) || data.lines.length !== 7 ||
        !data.lines.every((line) => typeof line.speaker === "string" && typeof line.text === "string" &&
          /^audio\/en\/[0-9]{2}_[a-z]+\.mp3$/.test(line.audio))) throw new Error("dialogue");
    lines = data.lines;
    updateControls();
    status.textContent = "";
    startButton.disabled = false;
  })
  .catch(() => {
    status.textContent = "The scene could not load. Please reload.";
    status.classList.add("error");
  });
