const appRoot = document.querySelector("[data-json-url]");
const DATA_URL = appRoot?.dataset.jsonUrl || "../data/vocabulary-en.json";

const ui = {
  totalCount: document.getElementById("totalCount"),
  remainingCount: document.getElementById("remainingCount"),
  selectionLabel: document.getElementById("selectionLabel"),
  filterButtons: Array.from(document.querySelectorAll("[data-filter]")),
  directionButtons: Array.from(document.querySelectorAll("[data-direction]")),
  wordSetGroup: document.getElementById("wordSetGroup"),
  wordSetList: document.getElementById("wordSetList"),
  wordSetSummary: document.getElementById("wordSetSummary"),
  clearWordSetsButton: document.getElementById("clearWordSetsButton"),
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
  wordSetOptions: [],
  selectedWordSetKeys: new Set(),
  shownIds: new Set(),
  selectionSignature: "",
};

function normalizeWordSetKey(value) {
  return String(value || "").trim().toLocaleLowerCase();
}

function setChipState(buttons, activeValue, attributeName) {
  buttons.forEach((button) => {
    button.classList.toggle("active", button.dataset[attributeName] === activeValue);
  });
}

function updateControlButtons() {
  setChipState(ui.filterButtons, state.filter, "filter");
  setChipState(ui.directionButtons, state.direction, "direction");
  updateWordSetSummary();
}

function getSelectionLabel() {
  const wordSetCount = state.selectedWordSetKeys.size;
  if (state.filter === "hard") {
    return wordSetCount ? `JEN HT • OKRUHY ${wordSetCount}` : "JEN HT";
  }
  if (state.filter === "selected") {
    return wordSetCount ? `JEN L • OKRUHY ${wordSetCount}` : "JEN L";
  }
  return wordSetCount ? `VSE • OKRUHY ${wordSetCount}` : "VSE";
}

function getAvailableWordSets() {
  const optionsByKey = new Map();
  const candidateLabels = Array.isArray(state.data?.wordSets) ? state.data.wordSets : [];

  candidateLabels.forEach((label) => {
    const trimmed = String(label || "").trim();
    const key = normalizeWordSetKey(trimmed);
    if (trimmed && key && !optionsByKey.has(key)) {
      optionsByKey.set(key, { key, label: trimmed });
    }
  });

  state.items.forEach((item) => {
    const labels = Array.isArray(item.wordSets) ? item.wordSets : [];
    labels.forEach((label) => {
      const trimmed = String(label || "").trim();
      const key = normalizeWordSetKey(trimmed);
      if (trimmed && key && !optionsByKey.has(key)) {
        optionsByKey.set(key, { key, label: trimmed });
      }
    });
  });

  return Array.from(optionsByKey.values()).sort((left, right) =>
    left.label.localeCompare(right.label, "cs", { sensitivity: "base" }),
  );
}

function updateWordSetSummary() {
  if (!ui.wordSetSummary) {
    return;
  }
  const count = state.selectedWordSetKeys.size;
  if (!count) {
    ui.wordSetSummary.textContent = "Vsechny okruhy";
  } else if (count === 1) {
    ui.wordSetSummary.textContent = "1 okruh";
  } else if (count < 5) {
    ui.wordSetSummary.textContent = `${count} okruhy`;
  } else {
    ui.wordSetSummary.textContent = `${count} okruhu`;
  }
  if (ui.clearWordSetsButton) {
    ui.clearWordSetsButton.disabled = count === 0;
  }
}

function renderWordSetControls() {
  if (!ui.wordSetGroup || !ui.wordSetList) {
    return;
  }

  ui.wordSetList.innerHTML = "";
  const availableKeys = new Set(state.wordSetOptions.map((option) => option.key));
  state.selectedWordSetKeys = new Set(
    Array.from(state.selectedWordSetKeys).filter((key) => availableKeys.has(key)),
  );

  if (!state.wordSetOptions.length) {
    ui.wordSetGroup.hidden = true;
    updateWordSetSummary();
    return;
  }

  ui.wordSetGroup.hidden = false;

  state.wordSetOptions.forEach((option) => {
    const label = document.createElement("label");
    label.className = "wordset-option";

    const input = document.createElement("input");
    input.type = "checkbox";
    input.value = option.key;
    input.checked = state.selectedWordSetKeys.has(option.key);

    const text = document.createElement("span");
    text.textContent = option.label;

    label.append(input, text);
    label.classList.toggle("is-active", input.checked);

    input.addEventListener("change", () => {
      if (input.checked) {
        state.selectedWordSetKeys.add(option.key);
      } else {
        state.selectedWordSetKeys.delete(option.key);
      }
      label.classList.toggle("is-active", input.checked);
      updateControlButtons();
      chooseNextItem();
    });

    ui.wordSetList.append(label);
  });

  updateWordSetSummary();
}

function buildSelection() {
  let items = [...state.items];
  if (state.filter === "selected") {
    items = items.filter((item) => item.selected);
  } else if (state.filter === "hard") {
    items = items.filter((item) => item.hardTraining);
  }
  if (state.selectedWordSetKeys.size) {
    items = items.filter((item) => {
      const labels = Array.isArray(item.wordSets) ? item.wordSets : [];
      return labels.some((label) => state.selectedWordSetKeys.has(normalizeWordSetKey(label)));
    });
  }
  return items;
}

function currentSignature(selection) {
  return JSON.stringify({
    filter: state.filter,
    direction: state.direction,
    wordSets: Array.from(state.selectedWordSetKeys).sort(),
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

  if (ui.clearWordSetsButton) {
    ui.clearWordSetsButton.addEventListener("click", () => {
      if (!state.selectedWordSetKeys.size) {
        return;
      }
      state.selectedWordSetKeys.clear();
      renderWordSetControls();
      updateControlButtons();
      chooseNextItem();
    });
  }

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
    state.wordSetOptions = getAvailableWordSets();
    renderWordSetControls();
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
