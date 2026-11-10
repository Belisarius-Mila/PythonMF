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
const scene = document.getElementById("scene");
const sceneImage = document.getElementById("sceneImage");
let lines = [];
let index = -1;
let activeAudio = null;
let generation = 0;
let playing = false;
let failed = false;

function updateControls() {
  repeatButton.disabled = index < 0 || playing || Boolean(lines[index]?.silent);
  nextButton.disabled = playing || failed || index >= lines.length - 1;
  nextButton.hidden = index < 0 || index >= lines.length - 1;
  restartButton.hidden = index < 0 || index !== lines.length - 1 || playing || failed;
  const nextPicture = lines[index] && lines[index + 1] &&
    (lines[index].picture.id !== lines[index + 1].picture.id ||
      lines[index].frame.image !== lines[index + 1].frame.image);
  nextButton.textContent = nextPicture ? "Next picture ▶" : "Next ▶";
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
  const picture = line.picture;
  const frame = line.frame;
  scene.dataset.picture = String(picture.id);
  scene.dataset.image = frame.image;
  scene.dataset.layout = picture.layout || "overlay";
  scene.setAttribute("aria-label", `Scene 6 — ${picture.title}`);
  sceneImage.src = frame.image;
  sceneImage.alt = frame.alt;
  sceneImage.width = frame.width;
  sceneImage.height = frame.height;
  startButton.hidden = true;
  status.classList.remove("error");
  failed = false;
  if (line.silent) {
    speakerName.textContent = "";
    speechText.textContent = "";
    lineNumber.textContent = "";
    speechBubble.hidden = true;
    status.textContent = picture.title;
    updateControls();
    return;
  }
  const token = generation;
  speakerName.textContent = line.speaker;
  speechText.textContent = line.text;
  lineNumber.textContent = `${line.pictureLine} / ${picture.line_count}`;
  speechBubble.hidden = false;
  status.textContent = "";
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
      (line.pictureLine === picture.line_count ? `${picture.title} · Picture ${picture.id} complete` : "");
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

function readJson(path) {
  return fetch(path).then((response) => {
    if (!response.ok) throw new Error("scene data");
    return response.json();
  });
}

function validImage(frame) {
  return frame && /^[a-z0-9_]+\.webp$/.test(frame.image) && typeof frame.alt === "string" &&
    Number.isInteger(frame.width) && frame.width > 0 && Number.isInteger(frame.height) && frame.height > 0;
}

readJson("pictures.json?v=20261110complete1")
  .then((catalog) => {
    const lineCounts = [7, 10, 8, 7, 7, 8, 8, 6, 0, 6];
    if (catalog.schema_version !== 1 || !Array.isArray(catalog.pictures) || catalog.pictures.length !== 10 ||
        !catalog.pictures.every((picture, n) => picture.id === n + 1 &&
          picture.dialogue === (n === 0 ? "dialogue.json" : `dialogue_${String(picture.id).padStart(2, "0")}.json`) &&
          picture.line_count === lineCounts[n] && typeof picture.title === "string" && validImage(picture) &&
          (picture.layout === undefined || picture.layout === "below") &&
          (picture.image_changes === undefined || (Array.isArray(picture.image_changes) &&
            picture.image_changes.every((frame, i, frames) => validImage(frame) && Number.isInteger(frame.from_line) &&
              frame.from_line > 1 && frame.from_line <= picture.line_count &&
              (i === 0 || frame.from_line > frames[i - 1].from_line)))))) throw new Error("pictures");
    return Promise.all(catalog.pictures.map((picture) =>
      readJson(`${picture.dialogue}?v=20261110complete1`).then((data) => {
        const audioPattern = picture.id === 1 ? /^audio\/en\/[0-9]{2}_[a-z]+\.mp3$/ :
          new RegExp(`^audio/en/p${String(picture.id).padStart(2, "0")}_[0-9]{2}_[a-z_]+\\.mp3$`);
        if (data.schema_version !== 1 || data.picture !== picture.id || !Array.isArray(data.lines) ||
            (picture.id === 9) !== (data.silent === true) ||
            data.lines.length !== picture.line_count || !data.lines.every((line) =>
              typeof line.speaker === "string" && typeof line.text === "string" && audioPattern.test(line.audio))) {
          throw new Error("dialogue");
        }
        if (data.silent) return [{picture, frame: picture, silent: true, pictureLine: 0}];
        return data.lines.map((line, n) => {
          let frame = picture;
          for (const change of picture.image_changes || []) {
            if (n + 1 < change.from_line) break;
            frame = change;
          }
          return {...line, picture, pictureLine: n + 1, frame};
        });
      })));
  })
  .then((pictures) => {
    lines = pictures.flat();
    updateControls();
    status.textContent = "";
    startButton.disabled = false;
  })
  .catch(() => {
    status.textContent = "The scene could not load. Please reload.";
    status.classList.add("error");
  });
