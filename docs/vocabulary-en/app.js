const DATA_URL = "../data/vocabulary-en.json";

const ui = {
  totalCount: document.getElementById("totalCount"),
  remainingCount: document.getElementById("remainingCount"),
  selectionLabel: document.getElementById("selectionLabel"),
  filterButtons: Array.from(document.querySelectorAll("[data-filter]")),
  directionButtons: Array.from(document.querySelectorAll("[data-direction]")),
  wordImage: document.getElementById("wordImage"),
  pictureFallback: document.getElementById("pictureFallback"),
  orderBadge: document.getElementById("orderBadge"),
  imageBadge: document.getElementById("imageBadge"),
  promptLabel: document.getElementById("promptLabel"),
  promptText: document.getElementById("promptText"),
  answerCard: document.getElementById("answerCard"),
  answerEn: document.getElementById("answerEn"),
  answerCz: document.getElementById("answerCz"),
  sentenceBox: document.getElementById("sentenceBox"),
  sentenceEn: document.getElementById("sentenceEn"),
  sentenceCz: document.getElementById("sentenceCz"),
  messageStrip: document.getElementById("messageStrip"),
  newWordButton: document.getElementById("newWordButton"),
  revealButton: document.getElementById("revealButton"),
  speakPromptButton: document.getElementById("speakPromptButton"),
  speakAnswerButton: document.getElementById("speakAnswerButton"),
};

const state = {
  data: null,
  items: [],
  currentItem: null,
  revealed: false,
  filter: "all",
  direction: "czToEn",
  shownIds: new Set(),
  selectionSignature: "",
};

function setChipState(buttons, activeValue, attributeName) {
  buttons.forEach((button) => {
    button.classList.toggle("active", button.dataset[attributeName] === activeValue);
  });
}

function updateControlButtons() {
  setChipState(ui.filterButtons, state.filter, "filter");
  setChipState(ui.directionButtons, state.direction, "direction");
}

function getSelectionLabel() {
  if (state.filter === "hard") {
    return "JEN HT";
  }
  if (state.filter === "selected") {
    return "JEN L";
  }
  return "VSE";
}

function buildSelection() {
  let items = [...state.items];
  if (state.filter === "selected") {
    items = items.filter((item) => item.selected);
  } else if (state.filter === "hard") {
    items = items.filter((item) => item.hardTraining);
  }
  return items;
}

function currentSignature(selection) {
  return JSON.stringify({
    filter: state.filter,
    direction: state.direction,
    ids: selection.map((item) => item.id),
  });
}

function updateCounts(selection) {
  ui.totalCount.textContent = String(selection.length);
  ui.selectionLabel.textContent = getSelectionLabel();

  const seen = selection.filter((item) => state.shownIds.has(item.id)).length;
  const remaining = selection.length === 0 ? 0 : Math.max(1, selection.length - seen + 1);
  ui.remainingCount.textContent = String(remaining);
}

function chooseNextItem() {
  const selection = buildSelection();
  const signature = currentSignature(selection);
  if (signature !== state.selectionSignature) {
    state.selectionSignature = signature;
    state.shownIds.clear();
  }

  updateCounts(selection);
  if (selection.length === 0) {
    state.currentItem = null;
    renderEmptyState("Pro tenhle filtr ted nejsou v CSV zadna slovicka.");
    return;
  }

  let available = selection.filter((item) => !state.shownIds.has(item.id));
  if (available.length === 0) {
    state.shownIds.clear();
    available = [...selection];
    updateCounts(selection);
  }

  const randomIndex = Math.floor(Math.random() * available.length);
  state.currentItem = available[randomIndex];
  state.shownIds.add(state.currentItem.id);
  state.revealed = false;
  updateCounts(selection);
  renderCurrentItem();
}

function renderEmptyState(message) {
  ui.promptLabel.textContent = "Zadna karta";
  ui.promptText.textContent = "Nenalezeno";
  ui.answerCard.classList.add("hidden");
  ui.wordImage.hidden = true;
  ui.wordImage.removeAttribute("src");
  ui.wordImage.alt = "";
  ui.pictureFallback.hidden = false;
  ui.pictureFallback.textContent = "Bez dat";
  ui.orderBadge.textContent = "#0";
  ui.imageBadge.textContent = "image";
  ui.messageStrip.textContent = message;
}

function renderImage(item) {
  if (item.image) {
    ui.wordImage.src = new URL(`../${item.image}`, window.location.href).toString();
    ui.wordImage.alt = item.en || item.cz || "Vocabulary image";
    ui.wordImage.hidden = false;
    ui.pictureFallback.hidden = true;
  } else {
    ui.wordImage.hidden = true;
    ui.wordImage.removeAttribute("src");
    ui.wordImage.alt = "";
    ui.pictureFallback.hidden = false;
    ui.pictureFallback.textContent = "Bez obrazku";
  }
}

function renderCurrentItem() {
  const item = state.currentItem;
  if (!item) {
    renderEmptyState("Nejdriv nacti data.");
    return;
  }

  renderImage(item);
  ui.orderBadge.textContent = `#${item.order}`;
  ui.imageBadge.textContent = item.imageSource || "image";

  if (state.direction === "czToEn") {
    ui.promptLabel.textContent = "Rekni anglicky";
    ui.promptText.textContent = item.cz || "-";
  } else {
    ui.promptLabel.textContent = "Rekni cesky";
    ui.promptText.textContent = item.en || "-";
  }

  ui.answerEn.textContent = item.en || "-";
  ui.answerCz.textContent = item.cz || "-";
  ui.sentenceEn.textContent = item.sentenceEn || "-";
  ui.sentenceCz.textContent = item.sentenceCz || "-";
  ui.sentenceBox.classList.toggle("hidden", !(item.sentenceEn || item.sentenceCz));
  ui.answerCard.classList.toggle("hidden", !state.revealed);

  ui.messageStrip.textContent = state.revealed
    ? "Odpoved je odhalena. Muzes prehrat odpoved nebo jit na dalsi kartu."
    : "Nejdriv si odpoved rekni nahlas. Pak klikni na 'Ukaz odpoved'.";
}

function revealCurrentItem() {
  if (!state.currentItem) {
    return;
  }
  state.revealed = true;
  renderCurrentItem();
}

function pickVoice(langPrefix) {
  if (!("speechSynthesis" in window)) {
    return null;
  }
  const voices = window.speechSynthesis.getVoices();
  return voices.find((voice) => voice.lang && voice.lang.toLowerCase().startsWith(langPrefix)) || null;
}

function speak(text, langPrefix) {
  const value = (text || "").trim();
  if (!value || !("speechSynthesis" in window)) {
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(value);
  utterance.rate = 0.86;
  utterance.pitch = 1;
  utterance.lang = langPrefix === "cs" ? "cs-CZ" : "en-US";
  const voice = pickVoice(langPrefix);
  if (voice) {
    utterance.voice = voice;
  }
  window.speechSynthesis.speak(utterance);
}

function speakSequence(sequence) {
  const parts = sequence.filter((part) => part && String(part.text || "").trim());
  if (!parts.length || !("speechSynthesis" in window)) {
    return;
  }

  window.speechSynthesis.cancel();

  let index = 0;
  const playNext = () => {
    const part = parts[index];
    if (!part) {
      return;
    }
    const utterance = new SpeechSynthesisUtterance(part.text.trim());
    utterance.rate = 0.86;
    utterance.pitch = 1;
    utterance.lang = part.langPrefix === "cs" ? "cs-CZ" : "en-US";
    const voice = pickVoice(part.langPrefix);
    if (voice) {
      utterance.voice = voice;
    }
    utterance.onend = () => {
      index += 1;
      playNext();
    };
    window.speechSynthesis.speak(utterance);
  };

  playNext();
}

function speakPrompt() {
  if (!state.currentItem) {
    return;
  }
  if (state.direction === "czToEn") {
    speak(state.currentItem.cz, "cs");
  } else {
    speak(state.currentItem.en, "en");
  }
}

function speakAnswer() {
  if (!state.currentItem) {
    return;
  }
  const item = state.currentItem;
  speakSequence([
    { text: item.en, langPrefix: "en" },
    { text: item.cz, langPrefix: "cs" },
  ]);
}

function bindEvents() {
  ui.filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.filter = button.dataset.filter;
      updateControlButtons();
      chooseNextItem();
    });
  });

  ui.directionButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.direction = button.dataset.direction;
      updateControlButtons();
      renderCurrentItem();
    });
  });

  ui.newWordButton.addEventListener("click", chooseNextItem);
  ui.revealButton.addEventListener("click", revealCurrentItem);
  ui.speakPromptButton.addEventListener("click", speakPrompt);
  ui.speakAnswerButton.addEventListener("click", speakAnswer);
  ui.wordImage.addEventListener("click", speakPrompt);
}

async function loadData() {
  const response = await fetch(DATA_URL, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Failed to load ${DATA_URL}: ${response.status}`);
  }
  return response.json();
}

async function init() {
  bindEvents();
  updateControlButtons();

  try {
    state.data = await loadData();
    state.items = Array.isArray(state.data.items) ? state.data.items : [];
    chooseNextItem();
  } catch (error) {
    renderEmptyState("Nepodarilo se nacist vocabulary-en.json.");
    ui.messageStrip.textContent = `Chyba nacitani dat: ${error.message}`;
  }
}

if ("speechSynthesis" in window) {
  window.speechSynthesis.onvoiceschanged = () => {
    window.speechSynthesis.getVoices();
  };
}

init();
