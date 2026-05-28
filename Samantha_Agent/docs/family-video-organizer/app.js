const STORAGE_KEY = "family-video-organizer:draft:v1";

const state = {
  videos: Array.isArray(window.FAMILY_VIDEO_DATA?.videos) ? window.FAMILY_VIDEO_DATA.videos : [],
  project: window.FAMILY_VIDEO_DATA?.project || "Family video",
  decisions: {},
  activeId: null,
  lockedId: null,
  directoryHandle: null,
  videoFilesByName: new Map(),
};

const elements = {
  projectMeta: document.getElementById("projectMeta"),
  saveState: document.getElementById("saveState"),
  totalCount: document.getElementById("totalCount"),
  shortCount: document.getElementById("shortCount"),
  familyCount: document.getElementById("familyCount"),
  changedCount: document.getElementById("changedCount"),
  searchInput: document.getElementById("searchInput"),
  scopeFilter: document.getElementById("scopeFilter"),
  decisionFilter: document.getElementById("decisionFilter"),
  videoRows: document.getElementById("videoRows"),
  visibleCount: document.getElementById("visibleCount"),
  activeDataset: document.getElementById("activeDataset"),
  previewIndex: document.getElementById("previewIndex"),
  previewTitle: document.getElementById("previewTitle"),
  previewFile: document.getElementById("previewFile"),
  previewImages: document.getElementById("previewImages"),
  playButton: document.getElementById("playButton"),
  selectFolderButton: document.getElementById("selectFolderButton"),
  exportButton: document.getElementById("exportButton"),
  loadDataButton: document.getElementById("loadDataButton"),
  importDraftButton: document.getElementById("importDraftButton"),
  dataFileInput: document.getElementById("dataFileInput"),
  draftFileInput: document.getElementById("draftFileInput"),
  videoFolderInput: document.getElementById("videoFolderInput"),
  videoModal: document.getElementById("videoModal"),
  modalTitle: document.getElementById("modalTitle"),
  videoPlayer: document.getElementById("videoPlayer"),
  videoFallback: document.getElementById("videoFallback"),
  closeModalButton: document.getElementById("closeModalButton"),
};

const decisionLabels = {
  keep: "Ponechat",
  drop: "Vyřadit",
  maybe: "Možná",
  short: "Jen short",
  family: "Jen family",
  both: "Obě verze",
};

function defaultDecision(video) {
  if (video.videoShort && video.videoFamily) return "both";
  if (video.videoShort) return "short";
  if (video.videoFamily) return "family";
  return "drop";
}

function decisionFor(video) {
  return state.decisions[video.id] || {
    decision: defaultDecision(video),
    note: "",
    updatedAt: null,
  };
}

function loadDraft() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const draft = JSON.parse(raw);
    if (draft && typeof draft.decisions === "object") {
      state.decisions = draft.decisions;
      setSaveState("Obnoven lokální draft");
    }
  } catch {
    setSaveState("Draft nešel načíst");
  }
}

let autosaveTimer = null;
function scheduleSave() {
  setSaveState("Ukládám...");
  window.clearTimeout(autosaveTimer);
  autosaveTimer = window.setTimeout(saveDraft, 450);
}

function saveDraft() {
  const payload = {
    project: state.project,
    savedAt: new Date().toISOString(),
    decisions: state.decisions,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  setSaveState("Uloženo " + new Date().toLocaleTimeString("cs-CZ", { hour: "2-digit", minute: "2-digit" }));
  updateSummary();
}

function setSaveState(value) {
  elements.saveState.textContent = value;
}

function normalize(value) {
  return String(value || "").toLocaleLowerCase("cs-CZ");
}

function filteredVideos() {
  const query = normalize(elements.searchInput.value);
  const scope = elements.scopeFilter.value;
  const decision = elements.decisionFilter.value;

  return state.videos.filter((video) => {
    const current = decisionFor(video);
    const haystack = normalize([video.id, video.date, video.title, video.originalName, video.description].join(" "));
    if (query && !haystack.includes(query)) return false;
    if (scope === "short" && !video.videoShort) return false;
    if (scope === "family" && !video.videoFamily) return false;
    if (scope === "outside" && (video.videoShort || video.videoFamily)) return false;
    if (scope === "changed" && !state.decisions[video.id]) return false;
    if (scope === "notes" && !current.note.trim()) return false;
    if (decision !== "all" && current.decision !== decision) return false;
    return true;
  });
}

function updateSummary() {
  elements.totalCount.textContent = state.videos.length;
  elements.shortCount.textContent = state.videos.filter((video) => video.videoShort).length;
  elements.familyCount.textContent = state.videos.filter((video) => video.videoFamily).length;
  elements.changedCount.textContent = Object.keys(state.decisions).length;
}

function renderRows() {
  const rows = filteredVideos();
  elements.videoRows.innerHTML = "";
  elements.visibleCount.textContent = `${rows.length} záznamů`;

  for (const video of rows) {
    const current = decisionFor(video);
    const tr = document.createElement("tr");
    tr.dataset.id = video.id;
    if (state.activeId === video.id) tr.classList.add("is-active");
    if (state.lockedId === video.id) tr.classList.add("is-locked");
    tr.innerHTML = `
      <td class="muted-cell">${escapeHtml(video.id)}</td>
      <td>${escapeHtml(video.date)}</td>
      <td>${escapeHtml(video.duration)}</td>
      <td>${video.videoShort ? '<span class="pill">ano</span>' : ""}</td>
      <td>${video.videoFamily ? '<span class="pill">ano</span>' : ""}</td>
      <td>${escapeHtml(video.title)}</td>
      <td class="muted-cell">${escapeHtml(video.originalName)}</td>
      <td>${decisionSelect(video.id, current.decision)}</td>
      <td><textarea class="note-input" data-note-for="${escapeHtml(video.id)}" rows="1">${escapeHtml(current.note)}</textarea></td>
      <td><button class="play-row-button" data-play-for="${escapeHtml(video.id)}" type="button">Play</button></td>
    `;
    tr.addEventListener("mouseenter", () => {
      if (!state.lockedId) activateVideo(video.id);
    });
    tr.addEventListener("click", (event) => {
      if (event.target instanceof HTMLSelectElement || event.target instanceof HTMLTextAreaElement || event.target instanceof HTMLButtonElement) {
        return;
      }
      activateVideo(video.id, { lock: true });
    });
    elements.videoRows.appendChild(tr);
  }
}

function decisionSelect(id, selected) {
  const className = selected === "keep" || selected === "drop" || selected === "maybe" ? selected : "";
  const options = Object.entries(decisionLabels)
    .map(([value, label]) => `<option value="${value}" ${value === selected ? "selected" : ""}>${label}</option>`)
    .join("");
  return `<select class="decision-select ${className}" data-decision-for="${escapeHtml(id)}">${options}</select>`;
}

function activateVideo(id, options = {}) {
  const video = state.videos.find((item) => item.id === id);
  if (!video) return;

  state.activeId = id;
  if (options.lock) state.lockedId = id;

  document.querySelectorAll("tbody tr").forEach((row) => {
    row.classList.toggle("is-active", row.dataset.id === id);
    row.classList.toggle("is-locked", row.dataset.id === state.lockedId);
  });
  elements.previewIndex.textContent = `#${video.id}`;
  elements.previewTitle.textContent = video.title;
  elements.previewFile.textContent = video.originalName;
  elements.previewImages.innerHTML = "";

  const thumbs = Array.isArray(video.thumbs) ? video.thumbs : [];
  if (!thumbs.length) {
    const placeholder = document.createElement("div");
    placeholder.className = "image-placeholder";
    placeholder.textContent = "Náhled není v ukázkových datech";
    elements.previewImages.appendChild(placeholder);
    return;
  }

  for (const src of thumbs) {
    const img = document.createElement("img");
    img.className = "preview-image";
    img.src = src;
    img.alt = `Náhled ${video.id}`;
    img.onerror = () => {
      img.replaceWith(Object.assign(document.createElement("div"), {
        className: "image-placeholder",
        textContent: "Náhled není dostupný",
      }));
    };
    elements.previewImages.appendChild(img);
  }
}

function updateDecision(id, patch) {
  const video = state.videos.find((item) => item.id === id);
  if (!video) return;
  state.decisions[id] = {
    ...decisionFor(video),
    ...patch,
    updatedAt: new Date().toISOString(),
  };
  scheduleSave();
}

function exportDecisions() {
  const payload = {
    app: "FamilyVideoOrganizer",
    project: state.project,
    exportedAt: new Date().toISOString(),
    decisions: state.videos.map((video) => ({
      id: video.id,
      date: video.date,
      title: video.title,
      originalName: video.originalName,
      currentVideoShort: Boolean(video.videoShort),
      currentVideoFamily: Boolean(video.videoFamily),
      ...decisionFor(video),
    })),
  };
  downloadJson(`family-video-decisions-${dateStamp()}.json`, payload);
}

function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function dateStamp() {
  return new Date().toISOString().slice(0, 10);
}

async function playActiveVideo() {
  if (!state.activeId) return;
  const video = state.videos.find((item) => item.id === state.activeId);
  if (!video) return;
  await openVideo(video);
}

async function openVideo(video) {
  elements.modalTitle.textContent = video.originalName;
  elements.videoFallback.textContent = "";
  elements.videoPlayer.removeAttribute("src");

  if (state.directoryHandle && "getFileHandle" in state.directoryHandle) {
    try {
      const fileHandle = await state.directoryHandle.getFileHandle(video.originalName);
      const file = await fileHandle.getFile();
      elements.videoPlayer.src = URL.createObjectURL(file);
      elements.videoModal.hidden = false;
      return;
    } catch {
      elements.videoFallback.textContent = `Video nebylo nalezeno ve vybrané složce: ${video.originalName}`;
    }
  }

  const selectedFile = state.videoFilesByName.get(video.originalName);
  if (selectedFile) {
    elements.videoPlayer.src = URL.createObjectURL(selectedFile);
    elements.videoModal.hidden = false;
    return;
  }

  elements.videoPlayer.src = video.videoPath || video.originalName;
  elements.videoModal.hidden = false;
  elements.videoFallback.textContent = "Pokud se video nespustí, použij tlačítko Složka s videi a vyber složku nebo všechny MP4 soubory.";
}

async function selectVideoFolder() {
  if (!("showDirectoryPicker" in window)) {
    elements.videoFolderInput.click();
    return;
  }
  state.directoryHandle = await window.showDirectoryPicker({ mode: "read" });
  state.videoFilesByName = new Map();
  setSaveState("Složka s videi připojena");
}

function selectVideoFiles(files) {
  const videoFiles = Array.from(files || []).filter((file) => {
    const name = normalize(file.name);
    return name.endsWith(".mp4") || file.type === "video/mp4";
  });
  state.videoFilesByName = new Map(videoFiles.map((file) => [file.name, file]));
  state.directoryHandle = null;
  setSaveState(`Video soubory připojeny: ${state.videoFilesByName.size}`);
}

function importDraft(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const draft = JSON.parse(String(reader.result || "{}"));
      const decisions = {};
      for (const item of draft.decisions || []) {
        decisions[item.id] = {
          decision: item.decision || "maybe",
          note: item.note || "",
          updatedAt: item.updatedAt || new Date().toISOString(),
        };
      }
      state.decisions = decisions;
      saveDraft();
      renderRows();
    } catch {
      setSaveState("Import draftu selhal");
    }
  };
  reader.readAsText(file);
}

function importData(file) {
  const reader = new FileReader();
  reader.onload = () => {
    try {
      let payload;
      const text = String(reader.result || "");
      if (file.name.endsWith(".js")) {
        const marker = "window.FAMILY_VIDEO_DATA";
        const start = text.indexOf("{", text.indexOf(marker));
        const end = text.lastIndexOf("}");
        payload = JSON.parse(text.slice(start, end + 1));
      } else {
        payload = JSON.parse(text);
      }
      state.project = payload.project || "Family video";
      state.videos = Array.isArray(payload.videos) ? payload.videos : [];
      state.activeId = state.videos[0]?.id || null;
      state.lockedId = null;
      elements.projectMeta.textContent = state.project;
      elements.activeDataset.textContent = file.name;
      updateSummary();
      renderRows();
      if (state.activeId) activateVideo(state.activeId);
      setSaveState("Data načtena");
    } catch {
      setSaveState("Data nešla načíst");
    }
  };
  reader.readAsText(file);
}

function closeModal() {
  elements.videoPlayer.pause();
  elements.videoPlayer.removeAttribute("src");
  elements.videoPlayer.load();
  elements.videoModal.hidden = true;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function wireEvents() {
  elements.searchInput.addEventListener("input", renderRows);
  elements.scopeFilter.addEventListener("change", renderRows);
  elements.decisionFilter.addEventListener("change", renderRows);
  elements.exportButton.addEventListener("click", exportDecisions);
  elements.playButton.addEventListener("click", playActiveVideo);
  elements.closeModalButton.addEventListener("click", closeModal);
  elements.videoModal.addEventListener("click", (event) => {
    if (event.target === elements.videoModal) {
      closeModal();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !elements.videoModal.hidden) {
      closeModal();
    }
  });
  elements.selectFolderButton.addEventListener("click", selectVideoFolder);
  elements.loadDataButton.addEventListener("click", () => elements.dataFileInput.click());
  elements.importDraftButton.addEventListener("click", () => elements.draftFileInput.click());
  elements.dataFileInput.addEventListener("change", () => {
    const file = elements.dataFileInput.files?.[0];
    if (file) importData(file);
  });
  elements.videoFolderInput.addEventListener("change", () => {
    selectVideoFiles(elements.videoFolderInput.files);
  });
  elements.draftFileInput.addEventListener("change", () => {
    const file = elements.draftFileInput.files?.[0];
    if (file) importDraft(file);
  });
  elements.videoRows.addEventListener("change", (event) => {
    const target = event.target;
    if (target instanceof HTMLSelectElement && target.dataset.decisionFor) {
      updateDecision(target.dataset.decisionFor, { decision: target.value });
      target.className = `decision-select ${["keep", "drop", "maybe"].includes(target.value) ? target.value : ""}`;
    }
  });
  elements.videoRows.addEventListener("input", (event) => {
    const target = event.target;
    if (target instanceof HTMLTextAreaElement && target.dataset.noteFor) {
      updateDecision(target.dataset.noteFor, { note: target.value });
    }
  });
  elements.videoRows.addEventListener("click", (event) => {
    const target = event.target;
    if (target instanceof HTMLButtonElement && target.dataset.playFor) {
      const video = state.videos.find((item) => item.id === target.dataset.playFor);
      if (video) {
        activateVideo(video.id, { lock: true });
        openVideo(video);
      }
    }
  });
}

function init() {
  elements.projectMeta.textContent = state.project;
  if (!("showDirectoryPicker" in window)) {
    elements.selectFolderButton.title = "Vyber složku nebo označ všechny MP4 soubory";
  }
  loadDraft();
  wireEvents();
  updateSummary();
  renderRows();
  if (state.videos[0]) activateVideo(state.videos[0].id);
}

init();
