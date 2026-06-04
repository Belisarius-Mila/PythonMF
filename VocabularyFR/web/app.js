const FIELDNAMES = ["FR", "CZ", "Order", "Sentence", "SentenceT", "L", "HT", "gender_fr"];
const STORAGE_KEY = "vocabularyfr-web-state-v1";
const FEMALE_PRONOUNS = new Set(["ona", "elle"]);
const MALE_PRONOUNS = new Set(["on", "il", "lui"]);
const AMBIGUOUS_PRONOUNS = new Set(["ja", "je", "moi", "vy", "vous"]);
const CONJUNCTION_WORDS = new Set(["a", "ale", "nebo", "et", "ou", "mais"]);
const PREPOSITION_WORDS = new Set(["na", "v", "ve", "do", "z", "u", "k", "sur", "dans", "de", "en"]);
const ADJ_ADV_WORDS = new Set(["prislovce", "pridavnejmeno", "adverbe", "adjective", "adjectif"]);

const state = {
  rows: [],
  selectedIndex: -1,
  visibleIndexes: [],
  showBack: false,
  fileName: "",
  fileHandle: null,
  dirty: false,
  voices: [],
  selectedVoiceURI: "",
  autoSpeak: false,
  pictureMap: new Map(),
  pictureFiles: new Map(),
  pictureAssetsReady: false,
  loopRunning: false,
  loopTimer: 0,
  loopMode: "random",
  loopSpeechMode: "word",
  loopIntervalSeconds: 5,
};

const els = {
  fileStatus: document.getElementById("fileStatus"),
  openDirectBtn: document.getElementById("openDirectBtn"),
  fileInput: document.getElementById("fileInput"),
  saveDirectBtn: document.getElementById("saveDirectBtn"),
  exportBtn: document.getElementById("exportBtn"),
  searchInput: document.getElementById("searchInput"),
  filterSelect: document.getElementById("filterSelect"),
  sortSelect: document.getElementById("sortSelect"),
  totalCount: document.getElementById("totalCount"),
  visibleCount: document.getElementById("visibleCount"),
  learnedCount: document.getElementById("learnedCount"),
  hardCount: document.getElementById("hardCount"),
  rowsBody: document.getElementById("rowsBody"),
  prevBtn: document.getElementById("prevBtn"),
  randomBtn: document.getElementById("randomBtn"),
  nextBtn: document.getElementById("nextBtn"),
  flipBtn: document.getElementById("flipBtn"),
  pictureImg: document.getElementById("pictureImg"),
  genderPictureImg: document.getElementById("genderPictureImg"),
  pictureFallback: document.getElementById("pictureFallback"),
  pictureMeta: document.getElementById("pictureMeta"),
  wordSub: document.getElementById("wordSub"),
  sentenceLine: document.getElementById("sentenceLine"),
  sentenceTLine: document.getElementById("sentenceTLine"),
  speakWordBtn: document.getElementById("speakWordBtn"),
  speakSentenceBtn: document.getElementById("speakSentenceBtn"),
  autoSpeakField: document.getElementById("autoSpeakField"),
  voiceSelect: document.getElementById("voiceSelect"),
  loopToggleBtn: document.getElementById("loopToggleBtn"),
  loopModeSelect: document.getElementById("loopModeSelect"),
  loopSpeechSelect: document.getElementById("loopSpeechSelect"),
  loopIntervalField: document.getElementById("loopIntervalField"),
  loopStatus: document.getElementById("loopStatus"),
  editForm: document.getElementById("editForm"),
  editorTitle: document.getElementById("editorTitle"),
  newBtn: document.getElementById("newBtn"),
  frField: document.getElementById("frField"),
  czField: document.getElementById("czField"),
  sentenceField: document.getElementById("sentenceField"),
  sentenceTField: document.getElementById("sentenceTField"),
  genderField: document.getElementById("genderField"),
  learnedField: document.getElementById("learnedField"),
  hardField: document.getElementById("hardField"),
  applyBtn: document.getElementById("applyBtn"),
  insertAfterBtn: document.getElementById("insertAfterBtn"),
  deleteBtn: document.getElementById("deleteBtn"),
  toast: document.getElementById("toast"),
};

function parseCsv(text) {
  const rows = [];
  let row = [];
  let value = "";
  let quoted = false;

  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];

    if (quoted) {
      if (ch === '"' && next === '"') {
        value += '"';
        i += 1;
      } else if (ch === '"') {
        quoted = false;
      } else {
        value += ch;
      }
      continue;
    }

    if (ch === '"') {
      quoted = true;
    } else if (ch === ",") {
      row.push(value);
      value = "";
    } else if (ch === "\n") {
      row.push(value);
      rows.push(row);
      row = [];
      value = "";
    } else if (ch !== "\r") {
      value += ch;
    }
  }

  if (value || row.length) {
    row.push(value);
    rows.push(row);
  }

  if (!rows.length) return [];
  rows[0][0] = rows[0][0].replace(/^\uFEFF/, "");
  const headers = rows.shift().map((item) => item.trim());
  return repairRows(rows.map((items) => {
    const out = {};
    headers.forEach((header, index) => {
      out[header] = items[index] || "";
    });
    return out;
  }));
}

function repairRows(rows) {
  const repaired = rows
    .map((row) => {
      const learned = cleanAnoNe(row.L);
      let hard = cleanAnoNe(row.HT);
      const fixedLearned = learned === "ano" && hard === "ano" ? "ne" : learned;
      if (fixedLearned === "ano") hard = "ne";
      const gender = String(row.gender_fr || "").trim().toLowerCase();
      return {
        FR: String(row.FR || "").trim(),
        CZ: String(row.CZ || "").trim(),
        Order: "",
        Sentence: String(row.Sentence || "").trim(),
        SentenceT: String(row.SentenceT || "").trim(),
        L: fixedLearned,
        HT: hard,
        gender_fr: gender === "m" || gender === "f" ? gender : "",
      };
    })
    .filter((row) => row.FR || row.CZ || row.Sentence);

  renumber(repaired);
  return repaired;
}

function cleanAnoNe(value) {
  return String(value || "ne").trim().toLowerCase() === "ano" ? "ano" : "ne";
}

function renumber(rows = state.rows) {
  rows.forEach((row, index) => {
    row.Order = String(index + 1);
  });
}

function csvEscape(value) {
  const text = String(value || "");
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function toCsv(rows) {
  const lines = [FIELDNAMES.join(",")];
  rows.forEach((row) => {
    lines.push(FIELDNAMES.map((field) => csvEscape(row[field])).join(","));
  });
  return `${lines.join("\r\n")}\r\n`;
}

async function loadFromFile(file) {
  stopLoop();
  const text = await file.text();
  state.rows = parseCsv(text);
  state.fileName = file.name || "VocabularyFR.csv";
  state.fileHandle = null;
  state.selectedIndex = state.rows.length ? 0 : -1;
  state.showBack = false;
  state.dirty = false;
  persistLocal();
  render();
  toast(`Načteno ${state.rows.length} řádků`);
}

async function openDirectFile() {
  stopLoop();
  if (!window.showOpenFilePicker) {
    els.fileInput.click();
    toast("Přímé ukládání není v tomto prohlížeči dostupné");
    return;
  }
  const [handle] = await window.showOpenFilePicker({
    multiple: false,
    types: [{ description: "CSV", accept: { "text/csv": [".csv"] } }],
  });
  const file = await handle.getFile();
  const text = await file.text();
  state.rows = parseCsv(text);
  state.fileName = file.name || "VocabularyFR.csv";
  state.fileHandle = handle;
  state.selectedIndex = state.rows.length ? 0 : -1;
  state.showBack = false;
  state.dirty = false;
  persistLocal();
  render();
  toast(`Načteno ${state.rows.length} řádků`);
}

async function saveDirect() {
  if (!state.fileHandle) {
    exportCsv();
    return;
  }
  const writable = await state.fileHandle.createWritable();
  await writable.write(toCsv(state.rows));
  await writable.close();
  state.dirty = false;
  persistLocal();
  renderStatus();
  toast("CSV uloženo");
}

function exportCsv() {
  const blob = new Blob([toCsv(state.rows)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const baseName = state.fileName || "VocabularyFR.csv";
  link.href = url;
  link.download = baseName.replace(/\.csv$/i, "") + ".csv";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  state.dirty = false;
  persistLocal();
  renderStatus();
}

function filteredIndexes() {
  const query = normalize(els.searchInput.value);
  const filter = els.filterSelect.value;
  let indexes = state.rows
    .map((row, index) => ({ row, index }))
    .filter(({ row }) => {
      const haystack = normalize([row.FR, row.CZ, row.Sentence, row.SentenceT].join(" "));
      if (query && !haystack.includes(query)) return false;
      if (filter === "unknown") return row.L !== "ano";
      if (filter === "hard") return row.HT === "ano";
      if (filter === "learned") return row.L === "ano";
      if (filter === "with-sentence") return Boolean(row.Sentence || row.SentenceT);
      return true;
    });

  const sort = els.sortSelect.value;
  if (sort === "fr") indexes.sort((a, b) => a.row.FR.localeCompare(b.row.FR, "fr"));
  if (sort === "cz") indexes.sort((a, b) => a.row.CZ.localeCompare(b.row.CZ, "cs"));
  return indexes.map((item) => item.index);
}

function normalize(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

function normalizeWord(value) {
  return String(value || "")
    .trim()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "");
}

function tokenizeWords(value) {
  const raw = String(value || "").toLowerCase().match(/[A-Za-zÀ-ÖØ-öø-ÿ'-]+/g) || [];
  return raw.map(normalizeWord).filter(Boolean);
}

async function loadPictureAssets() {
  try {
    const response = await fetch("pict/manifest.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const manifest = await response.json();
    state.pictureMap = new Map();
    Object.entries(manifest.mapping || {}).forEach(([key, value]) => {
      const normalizedKey = normalizeWord(key);
      const normalizedValue = normalizeWord(value);
      if (normalizedKey && normalizedValue) state.pictureMap.set(normalizedKey, normalizedValue);
    });
    state.pictureFiles = new Map();
    (manifest.images || []).forEach((name) => {
      const stem = String(name).replace(/\.[^.]+$/, "");
      const normalizedStem = normalizeWord(stem);
      if (normalizedStem && !state.pictureFiles.has(normalizedStem)) state.pictureFiles.set(normalizedStem, name);
    });
    state.pictureAssetsReady = true;
  } catch {
    state.pictureAssetsReady = false;
  }
  renderCard();
}

function probableVerb(frWord) {
  const word = normalizeWord(frWord);
  return Boolean(word) && /(?:er|ir|re|oir|at|it|et|yt)$/.test(word);
}

function probableAdjOrAdv(frWord, czWord) {
  const cz = normalizeWord(czWord);
  const fr = normalizeWord(frWord);
  return /(?:e|ne|ove|ova|ovy|ych|ich|y|a|i)$/.test(cz)
    || /(?:ment|if|ive|eux|euse|al|ale|el|elle|ant|ente)$/.test(fr);
}

function pickGenderFallback(frWord, czWord) {
  const key = `${normalizeWord(frWord)}|${normalizeWord(czWord)}`;
  let score = 0;
  for (const ch of key) score += ch.charCodeAt(0);
  return score % 2 ? "woman" : "man";
}

function choosePictureStem(row) {
  if (!row) return "others";
  const fr = row.FR || "";
  const cz = row.CZ || "";
  const frNorm = normalizeWord(fr);
  const czNorm = normalizeWord(cz);
  const tokens = [...tokenizeWords(fr), ...tokenizeWords(cz)];
  const keys = [frNorm, czNorm, ...tokens].filter(Boolean);

  for (const key of keys) {
    if (state.pictureFiles.has(key)) return key;
  }
  for (const key of keys) {
    const mapped = state.pictureMap.get(key);
    if (mapped && state.pictureFiles.has(mapped)) return mapped;
  }

  const tokenSet = new Set(tokens);
  if ([...FEMALE_PRONOUNS].some((token) => tokenSet.has(token))) return "woman";
  if ([...MALE_PRONOUNS].some((token) => tokenSet.has(token))) return "man";
  if ([...AMBIGUOUS_PRONOUNS].some((token) => tokenSet.has(token))) return pickGenderFallback(fr, cz);
  if ([...CONJUNCTION_WORDS].some((token) => tokenSet.has(token))) return "conjuction";
  if ([...PREPOSITION_WORDS].some((token) => tokenSet.has(token))) return "preposition";
  if ([...ADJ_ADV_WORDS].some((token) => tokenSet.has(token))) return "proverbs";
  if (probableVerb(fr)) return "verb";
  if (probableAdjOrAdv(fr, cz)) return "proverbs";
  return "others";
}

function imageUrlForStem(stem) {
  const file = state.pictureFiles.get(normalizeWord(stem));
  return file ? `pict/images/${encodeURIComponent(file)}` : "";
}

function updatePicture(row) {
  if (!els.pictureImg) return;
  if (!row || !state.pictureAssetsReady) {
    els.pictureImg.hidden = true;
    els.genderPictureImg.hidden = true;
    els.pictureFallback.hidden = false;
    els.pictureFallback.textContent = state.pictureAssetsReady ? "Bez obrázku" : "Obrázky nejsou načtené";
    els.pictureMeta.textContent = "";
    return;
  }

  const stem = choosePictureStem(row);
  const url = imageUrlForStem(stem) || imageUrlForStem("others");
  if (url) {
    els.pictureImg.src = url;
    els.pictureImg.hidden = false;
    els.pictureFallback.hidden = true;
    els.pictureMeta.textContent = stem ? `obrázek: ${stem}` : "";
  } else {
    els.pictureImg.hidden = true;
    els.pictureFallback.hidden = false;
    els.pictureFallback.textContent = "Bez obrázku";
    els.pictureMeta.textContent = "";
  }

  const gender = String(row.gender_fr || "").trim().toLowerCase();
  const genderStem = gender === "m" ? "malefox" : gender === "f" ? "femalefox" : "";
  const genderUrl = imageUrlForStem(genderStem);
  if (genderUrl) {
    els.genderPictureImg.src = genderUrl;
    els.genderPictureImg.hidden = false;
  } else {
    els.genderPictureImg.hidden = true;
  }
}

function render() {
  state.visibleIndexes = filteredIndexes();
  if (state.selectedIndex >= state.rows.length) state.selectedIndex = state.rows.length - 1;
  if (state.selectedIndex < 0 && state.rows.length) state.selectedIndex = state.visibleIndexes[0] ?? 0;
  renderStatus();
  renderStats();
  renderTable();
  renderCard();
  renderEditor();
}

function renderStatus() {
  const mode = state.fileHandle ? "přímé ukládání" : "export";
  const marker = state.dirty ? " • neuloženo" : "";
  els.fileStatus.textContent = state.fileName
    ? `${state.fileName} • ${state.rows.length} řádků • ${mode}${marker}`
    : "CSV není načtené";
  const hasRows = state.rows.length > 0;
  els.exportBtn.disabled = !hasRows;
  els.saveDirectBtn.disabled = !hasRows || !state.fileHandle;
  els.loopToggleBtn.disabled = !hasRows;
  els.loopToggleBtn.textContent = state.loopRunning ? "Stop smyčky" : "Start smyčky";
  els.loopStatus.textContent = state.loopRunning
    ? `Smyčka běží: ${state.loopMode === "random" ? "náhodně" : "postupně"}, ${state.loopIntervalSeconds}s`
    : "Smyčka vypnutá";
  els.loopStatus.classList.toggle("running", state.loopRunning);
}

function renderStats() {
  els.totalCount.textContent = String(state.rows.length);
  els.visibleCount.textContent = String(state.visibleIndexes.length);
  els.learnedCount.textContent = String(state.rows.filter((row) => row.L === "ano").length);
  els.hardCount.textContent = String(state.rows.filter((row) => row.HT === "ano").length);
}

function renderTable() {
  els.rowsBody.innerHTML = "";
  state.visibleIndexes.forEach((index) => {
    const row = state.rows[index];
    const tr = document.createElement("tr");
    if (index === state.selectedIndex) tr.classList.add("selected");
    tr.dataset.index = String(index);
    [row.Order, row.gender_fr, row.FR, row.CZ, mark(row.L), mark(row.HT)].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value;
      tr.appendChild(td);
    });
    tr.addEventListener("click", () => selectIndex(index));
    els.rowsBody.appendChild(tr);
  });
}

function mark(value) {
  return value === "ano" ? "✓" : "";
}

function renderCard() {
  const row = state.rows[state.selectedIndex];
  const hasRows = Boolean(row);
  els.prevBtn.disabled = !hasRows;
  els.randomBtn.disabled = !hasRows;
  els.nextBtn.disabled = !hasRows;
  els.flipBtn.disabled = !hasRows;
  els.speakWordBtn.disabled = !hasRows || !row.FR;
  els.speakSentenceBtn.disabled = !hasRows || !row.Sentence;

  if (!row) {
    els.flipBtn.textContent = "Načti CSV";
    els.wordSub.textContent = "";
    els.sentenceLine.textContent = "";
    els.sentenceTLine.textContent = "";
    updatePicture(null);
    return;
  }

  els.flipBtn.textContent = state.showBack ? row.CZ || "CZ" : row.FR || "FR";
  els.wordSub.textContent = state.showBack ? row.FR : row.CZ;
  els.sentenceLine.textContent = row.Sentence || "";
  els.sentenceTLine.textContent = row.SentenceT || "";
  updatePicture(row);
}

function loadVoices() {
  if (!("speechSynthesis" in window)) {
    els.voiceSelect.innerHTML = '<option value="">Hlas není dostupný</option>';
    els.speakWordBtn.disabled = true;
    els.speakSentenceBtn.disabled = true;
    els.autoSpeakField.disabled = true;
    return;
  }
  const allVoices = window.speechSynthesis.getVoices();
  const frenchVoices = allVoices.filter((voice) => voice.lang.toLowerCase().startsWith("fr"));
  state.voices = frenchVoices.length ? frenchVoices : allVoices;
  const previous = state.selectedVoiceURI;
  els.voiceSelect.innerHTML = "";

  if (!state.voices.length) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "Výchozí francouzský hlas";
    els.voiceSelect.appendChild(option);
    return;
  }

  state.voices.forEach((voice) => {
    const option = document.createElement("option");
    option.value = voice.voiceURI;
    option.textContent = `${voice.name} (${voice.lang})`;
    els.voiceSelect.appendChild(option);
  });

  const preferred = state.voices.find((voice) => voice.voiceURI === previous)
    || state.voices.find((voice) => voice.lang.toLowerCase() === "fr-fr")
    || state.voices[0];
  state.selectedVoiceURI = preferred ? preferred.voiceURI : "";
  els.voiceSelect.value = state.selectedVoiceURI;
}

function currentVoice() {
  return state.voices.find((voice) => voice.voiceURI === state.selectedVoiceURI) || null;
}

function speak(text) {
  const clean = String(text || "").trim();
  if (!clean) return;
  if (!("speechSynthesis" in window) || typeof SpeechSynthesisUtterance === "undefined") {
    toast("Hlas není v tomto prohlížeči dostupný");
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.lang = "fr-FR";
  utterance.rate = 0.9;
  utterance.pitch = 1;
  const voice = currentVoice();
  if (voice) {
    utterance.voice = voice;
    utterance.lang = voice.lang || "fr-FR";
  }
  window.speechSynthesis.speak(utterance);
}

function audioSlug(text) {
  return String(text || "")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 90) || "audio";
}

function playAudio(kind, text) {
  const clean = String(text || "").trim();
  if (!clean) return;
  const audio = new Audio(`audio/${kind}/${audioSlug(clean)}.m4a`);
  audio.addEventListener("error", () => speak(clean), { once: true });
  audio.play().catch(() => speak(clean));
}

function speakCurrentWord() {
  const row = state.rows[state.selectedIndex];
  if (!row) return;
  playAudio("fr_words", row.FR);
}

function speakCurrentSentence() {
  const row = state.rows[state.selectedIndex];
  if (!row) return;
  playAudio("fr_sentences", row.Sentence || row.FR);
}

function speakLoopCurrent() {
  const row = state.rows[state.selectedIndex];
  if (!row) return;
  speakCurrentWord();
  if (state.loopSpeechMode === "word-sentence" && row.Sentence) {
    window.setTimeout(() => speakCurrentSentence(), 1400);
  }
}

function autoSpeakCurrent() {
  if (!state.autoSpeak) return;
  window.setTimeout(() => speakCurrentWord(), 80);
}

function loopIntervalMs() {
  const raw = Number(els.loopIntervalField.value || state.loopIntervalSeconds || 5);
  const seconds = Math.max(2, Math.min(30, Number.isFinite(raw) ? raw : 5));
  state.loopIntervalSeconds = seconds;
  els.loopIntervalField.value = String(seconds);
  return seconds * 1000;
}

function nextLoopIndex() {
  if (!state.visibleIndexes.length) return -1;
  if (state.loopMode === "random") {
    if (state.visibleIndexes.length === 1) return state.visibleIndexes[0];
    let next = state.selectedIndex;
    for (let attempt = 0; attempt < 8 && next === state.selectedIndex; attempt += 1) {
      next = state.visibleIndexes[Math.floor(Math.random() * state.visibleIndexes.length)];
    }
    return next;
  }
  const currentPosition = Math.max(0, state.visibleIndexes.indexOf(state.selectedIndex));
  return state.visibleIndexes[(currentPosition + 1) % state.visibleIndexes.length];
}

function scheduleLoopTick() {
  window.clearTimeout(state.loopTimer);
  if (!state.loopRunning) return;
  state.loopTimer = window.setTimeout(runLoopTick, loopIntervalMs());
}

function runLoopTick() {
  if (!state.loopRunning) return;
  const next = nextLoopIndex();
  if (next < 0) {
    stopLoop();
    return;
  }
  state.selectedIndex = next;
  state.showBack = false;
  render();
  speakLoopCurrent();
  scheduleLoopTick();
}

function startLoop() {
  if (!state.rows.length || !state.visibleIndexes.length) {
    toast("Nejsou vybraná žádná slovíčka");
    return;
  }
  state.loopMode = els.loopModeSelect.value === "sequence" ? "sequence" : "random";
  state.loopSpeechMode = els.loopSpeechSelect.value === "word-sentence" ? "word-sentence" : "word";
  loopIntervalMs();
  state.loopRunning = true;
  renderStatus();
  speakLoopCurrent();
  scheduleLoopTick();
}

function stopLoop() {
  window.clearTimeout(state.loopTimer);
  state.loopTimer = 0;
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  state.loopRunning = false;
  if (els.loopToggleBtn) renderStatus();
}

function toggleLoop() {
  if (state.loopRunning) {
    stopLoop();
  } else {
    startLoop();
  }
}

function renderEditor() {
  const row = state.rows[state.selectedIndex];
  els.editorTitle.textContent = row ? `Řádek ${row.Order}` : "Nové slovíčko";
  els.frField.value = row?.FR || "";
  els.czField.value = row?.CZ || "";
  els.sentenceField.value = row?.Sentence || "";
  els.sentenceTField.value = row?.SentenceT || "";
  els.genderField.value = row?.gender_fr || "";
  els.learnedField.checked = row?.L === "ano";
  els.hardField.checked = row?.HT === "ano";
  els.applyBtn.disabled = false;
  els.insertAfterBtn.disabled = state.selectedIndex < 0;
  els.deleteBtn.disabled = state.selectedIndex < 0;
}

function selectIndex(index) {
  state.selectedIndex = index;
  state.showBack = false;
  render();
  autoSpeakCurrent();
}

function moveSelection(delta) {
  if (!state.visibleIndexes.length) return;
  const currentPosition = Math.max(0, state.visibleIndexes.indexOf(state.selectedIndex));
  const nextPosition = (currentPosition + delta + state.visibleIndexes.length) % state.visibleIndexes.length;
  selectIndex(state.visibleIndexes[nextPosition]);
}

function selectRandom() {
  if (!state.visibleIndexes.length) return;
  const index = state.visibleIndexes[Math.floor(Math.random() * state.visibleIndexes.length)];
  selectIndex(index);
}

function readEditorRow() {
  let learned = els.learnedField.checked ? "ano" : "ne";
  let hard = els.hardField.checked ? "ano" : "ne";
  if (learned === "ano") hard = "ne";
  if (hard === "ano") learned = "ne";
  const gender = els.genderField.value === "m" || els.genderField.value === "f" ? els.genderField.value : "";
  return {
    FR: els.frField.value.trim(),
    CZ: els.czField.value.trim(),
    Order: "",
    Sentence: els.sentenceField.value.trim(),
    SentenceT: els.sentenceTField.value.trim(),
    L: learned,
    HT: hard,
    gender_fr: gender,
  };
}

function applyEditor(event) {
  event.preventDefault();
  const row = readEditorRow();
  if (!row.FR || !row.CZ) {
    toast("Zadej FR i CZ");
    return;
  }
  if (state.selectedIndex >= 0) {
    row.Order = state.rows[state.selectedIndex].Order;
    state.rows[state.selectedIndex] = row;
  } else {
    state.rows.push(row);
    state.selectedIndex = state.rows.length - 1;
  }
  renumber();
  markDirty();
}

function newRow() {
  state.selectedIndex = -1;
  state.showBack = false;
  renderEditor();
  els.frField.focus();
}

function insertAfterSelected() {
  if (state.selectedIndex < 0) return;
  const row = readEditorRow();
  if (!row.FR || !row.CZ) {
    toast("Zadej FR i CZ");
    return;
  }
  state.rows.splice(state.selectedIndex + 1, 0, row);
  state.selectedIndex += 1;
  renumber();
  markDirty();
}

function deleteSelected() {
  if (state.selectedIndex < 0) return;
  const row = state.rows[state.selectedIndex];
  if (!window.confirm(`Smazat řádek ${row.Order}: ${row.FR}?`)) return;
  state.rows.splice(state.selectedIndex, 1);
  renumber();
  state.selectedIndex = Math.min(state.selectedIndex, state.rows.length - 1);
  markDirty();
}

function markDirty() {
  state.dirty = true;
  persistLocal();
  render();
}

function persistLocal() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      rows: state.rows,
      fileName: state.fileName,
      dirty: state.dirty,
      autoSpeak: state.autoSpeak,
      selectedVoiceURI: state.selectedVoiceURI,
      loopMode: state.loopMode,
      loopSpeechMode: state.loopSpeechMode,
      loopIntervalSeconds: state.loopIntervalSeconds,
    }));
  } catch {
    // Export remains the reliable fallback.
  }
}

function restoreLocal() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    if (!Array.isArray(data.rows) || !data.rows.length) return;
    state.rows = repairRows(data.rows);
    state.fileName = data.fileName || "VocabularyFR.csv";
    state.selectedIndex = 0;
    state.dirty = Boolean(data.dirty);
    state.autoSpeak = Boolean(data.autoSpeak);
    state.selectedVoiceURI = data.selectedVoiceURI || "";
    state.loopMode = data.loopMode === "sequence" ? "sequence" : "random";
    state.loopSpeechMode = data.loopSpeechMode === "word-sentence" ? "word-sentence" : "word";
    state.loopIntervalSeconds = Math.max(2, Math.min(30, Number(data.loopIntervalSeconds || 5)));
    els.autoSpeakField.checked = state.autoSpeak;
    els.loopModeSelect.value = state.loopMode;
    els.loopSpeechSelect.value = state.loopSpeechMode;
    els.loopIntervalField.value = String(state.loopIntervalSeconds);
    render();
  } catch {
    // Ignore broken browser cache.
  }
}

let toastTimer = 0;
function toast(message) {
  window.clearTimeout(toastTimer);
  els.toast.textContent = message;
  els.toast.classList.add("visible");
  toastTimer = window.setTimeout(() => els.toast.classList.remove("visible"), 2200);
}

els.fileInput.addEventListener("change", (event) => {
  const file = event.target.files?.[0];
  if (file) loadFromFile(file).catch((err) => toast(String(err)));
  event.target.value = "";
});

els.openDirectBtn.addEventListener("click", () => {
  openDirectFile().catch((err) => toast(String(err)));
});
els.saveDirectBtn.addEventListener("click", () => saveDirect().catch((err) => toast(String(err))));
els.exportBtn.addEventListener("click", exportCsv);
els.searchInput.addEventListener("input", render);
els.filterSelect.addEventListener("change", () => {
  stopLoop();
  render();
});
els.sortSelect.addEventListener("change", () => {
  stopLoop();
  render();
});
els.prevBtn.addEventListener("click", () => moveSelection(-1));
els.nextBtn.addEventListener("click", () => moveSelection(1));
els.randomBtn.addEventListener("click", selectRandom);
els.speakWordBtn.addEventListener("click", speakCurrentWord);
els.speakSentenceBtn.addEventListener("click", speakCurrentSentence);
els.autoSpeakField.addEventListener("change", () => {
  state.autoSpeak = els.autoSpeakField.checked;
  persistLocal();
  if (state.autoSpeak) speakCurrentWord();
});
els.voiceSelect.addEventListener("change", () => {
  state.selectedVoiceURI = els.voiceSelect.value;
  persistLocal();
  speakCurrentWord();
});
els.loopToggleBtn.addEventListener("click", toggleLoop);
els.loopModeSelect.addEventListener("change", () => {
  state.loopMode = els.loopModeSelect.value === "sequence" ? "sequence" : "random";
  persistLocal();
  if (state.loopRunning) scheduleLoopTick();
  renderStatus();
});
els.loopSpeechSelect.addEventListener("change", () => {
  state.loopSpeechMode = els.loopSpeechSelect.value === "word-sentence" ? "word-sentence" : "word";
  persistLocal();
});
els.loopIntervalField.addEventListener("change", () => {
  loopIntervalMs();
  persistLocal();
  if (state.loopRunning) scheduleLoopTick();
  renderStatus();
});
els.flipBtn.addEventListener("click", () => {
  state.showBack = !state.showBack;
  renderCard();
});
els.editForm.addEventListener("submit", applyEditor);
els.newBtn.addEventListener("click", newRow);
els.insertAfterBtn.addEventListener("click", insertAfterSelected);
els.deleteBtn.addEventListener("click", deleteSelected);
els.learnedField.addEventListener("change", () => {
  if (els.learnedField.checked) els.hardField.checked = false;
});
els.hardField.addEventListener("change", () => {
  if (els.hardField.checked) els.learnedField.checked = false;
});
window.addEventListener("beforeunload", (event) => {
  if (!state.dirty) return;
  event.preventDefault();
  event.returnValue = "";
});

if (!window.showOpenFilePicker) {
  els.openDirectBtn.textContent = "Vybrat CSV";
}
els.loopModeSelect.value = state.loopMode;
els.loopSpeechSelect.value = state.loopSpeechMode;
els.loopIntervalField.value = String(state.loopIntervalSeconds);
loadVoices();
loadPictureAssets();
if ("speechSynthesis" in window) {
  window.speechSynthesis.onvoiceschanged = loadVoices;
}
restoreLocal();
render();
