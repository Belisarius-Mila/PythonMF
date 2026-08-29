"use strict";

const STORAGE_KEY = "vocabulary-en-audio-casting-v1";
const statusNode = document.querySelector("#status");
const castingNode = document.querySelector("#casting");
const summaryNode = document.querySelector("#selection-summary");
const notesNode = document.querySelector("#notes");

let manifest = null;
let currentAudio = null;
let sequenceToken = 0;
let preferences = loadPreferences();

function loadPreferences() {
  try {
    return { en: "", cz: "", notes: "", ...JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") };
  } catch (_) {
    return { en: "", cz: "", notes: "" };
  }
}

function savePreferences() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
  updateSelection();
}

function stopPlayback() {
  sequenceToken += 1;
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
  document.querySelectorAll(".playing").forEach((node) => node.classList.remove("playing"));
}

function playFile(path, button, token = null) {
  return new Promise((resolve, reject) => {
    if (token === null) stopPlayback();
    currentAudio = new Audio(path);
    button.classList.add("playing");
    currentAudio.addEventListener("ended", () => {
      button.classList.remove("playing");
      currentAudio = null;
      resolve();
    }, { once: true });
    currentAudio.addEventListener("error", () => {
      button.classList.remove("playing");
      currentAudio = null;
      reject(new Error(`Nelze přehrát ${path}`));
    }, { once: true });
    currentAudio.play().catch(reject);
  });
}

async function playSequence(voice, button) {
  stopPlayback();
  const token = sequenceToken;
  button.classList.add("playing");
  button.textContent = "■ Zastavit sérii";
  try {
    for (const item of manifest.items) {
      if (token !== sequenceToken) break;
      await playFile(manifest.audio[voice.id][item.id], button, token);
      if (token !== sequenceToken) break;
      await new Promise((resolve) => setTimeout(resolve, 220));
    }
  } catch (error) {
    statusNode.textContent = error.message;
    statusNode.classList.add("error");
  } finally {
    button.classList.remove("playing");
    button.textContent = "▶ Přehrát celou sérii";
  }
}

function updateSelection() {
  if (!manifest) return;
  const selected = {};
  for (const language of ["en", "cz"]) {
    selected[language] = manifest.voices.find((voice) => voice.id === preferences[language]);
  }
  summaryNode.textContent = `Angličtina: ${selected.en?.label || "nevybráno"} · Čeština: ${selected.cz?.label || "nevybráno"}`;
  document.querySelectorAll(".voice-card").forEach((card) => {
    const language = card.dataset.language;
    card.classList.toggle("selected", card.dataset.voice === preferences[language]);
  });
}

function voiceCard(voice) {
  const card = document.createElement("article");
  card.className = "voice-card";
  card.dataset.voice = voice.id;
  card.dataset.language = voice.language;

  const heading = document.createElement("div");
  heading.className = "voice-heading";
  heading.innerHTML = `<div><h3>${voice.label}</h3><p>${voice.description}</p></div>`;
  const choose = document.createElement("label");
  choose.className = "choose";
  const radio = document.createElement("input");
  radio.type = "radio";
  radio.name = `voice-${voice.language}`;
  radio.checked = preferences[voice.language] === voice.id;
  radio.addEventListener("change", () => {
    preferences[voice.language] = voice.id;
    savePreferences();
  });
  choose.append(radio, " Vybrat");
  heading.append(choose);
  card.append(heading);

  const playAll = document.createElement("button");
  playAll.type = "button";
  playAll.className = "play-all";
  playAll.textContent = "▶ Přehrát celou sérii";
  playAll.addEventListener("click", () => {
    if (playAll.classList.contains("playing")) stopPlayback();
    else playSequence(voice, playAll);
  });
  card.append(playAll);

  const list = document.createElement("ol");
  list.className = "sample-list";
  for (const item of manifest.items) {
    const row = document.createElement("li");
    const words = document.createElement("div");
    words.className = "words";
    words.innerHTML = `<strong>${item.displayEn}</strong><span>${item.displayCz}</span>`;
    const play = document.createElement("button");
    play.type = "button";
    play.className = "play-item";
    play.textContent = "▶ Poslech";
    play.setAttribute("aria-label", `Přehrát ${item.displayEn} hlasem ${voice.label}`);
    play.addEventListener("click", () => {
      if (play.classList.contains("playing")) stopPlayback();
      else playFile(manifest.audio[voice.id][item.id], play).catch((error) => {
        statusNode.textContent = error.message;
        statusNode.classList.add("error");
      });
    });
    row.append(words, play);
    list.append(row);
  }
  card.append(list);
  return card;
}

function render() {
  const labels = { en: "Anglické hlasy", cz: "České hlasy" };
  for (const language of ["en", "cz"]) {
    const section = document.createElement("section");
    section.className = "language-section";
    section.innerHTML = `<h2>${labels[language]}</h2>`;
    const grid = document.createElement("div");
    grid.className = "voice-grid";
    manifest.voices.filter((voice) => voice.language === language).forEach((voice) => grid.append(voiceCard(voice)));
    section.append(grid);
    castingNode.append(section);
  }
  notesNode.value = preferences.notes;
  notesNode.addEventListener("input", () => {
    preferences.notes = notesNode.value;
    savePreferences();
  });
  castingNode.hidden = false;
  statusNode.textContent = `Připraveno ${manifest.items.length} stejných zkoušek pro každý hlas.`;
  updateSelection();
}

fetch("casting.json", { cache: "no-store" })
  .then((response) => {
    if (!response.ok) throw new Error(`Casting nelze načíst (${response.status}).`);
    return response.json();
  })
  .then((data) => {
    manifest = data;
    render();
  })
  .catch((error) => {
    statusNode.textContent = `${error.message} Spusť stránku přes místní HTTP server.`;
    statusNode.classList.add("error");
  });
