const SPEAKER_VOICE_HINTS = {
  Kate: ["en-US", "female"],
  Lucy: ["en-US", "female"],
  Woman: ["en-US", "female"],
  Tom: ["en-US", "male"],
  Peter: ["en-US", "male"],
  Waiter: ["en-US", "male"],
};

const SCENE_CAPTIONS = {
  1: "Asking for directions",
  2: "Arriving at the restaurant",
  3: "Ordering drinks",
  4: "Ordering food",
  5: "During the meal",
  6: "Dessert",
  7: "Paying and leaving",
};

const PORTRAIT_FILES = {
  Kate: "Kate.png",
  Lucy: "Lucy.png",
  Tom: "Tom.jpg",
  Peter: "Peter.jpg",
  Waiter: "waiter.png",
  Woman: "woman.png",
};

const ui = {
  sectionTitle: document.getElementById("sectionTitle"),
  sectionNav: document.getElementById("sectionNav"),
  currentSpeaker: document.getElementById("currentSpeaker"),
  lineCounter: document.getElementById("lineCounter"),
  focusLine: document.getElementById("focusLine"),
  focusEnglish: document.getElementById("focusEnglish"),
  focusCzech: document.getElementById("focusCzech"),
  transcript: document.getElementById("transcript"),
  speakerPortrait: document.getElementById("speakerPortrait"),
  portraitPlaceholder: document.getElementById("portraitPlaceholder"),
  portraitName: document.getElementById("portraitName"),
  sceneImage: document.getElementById("sceneImage"),
  sceneCaption: document.getElementById("sceneCaption"),
  restartButton: document.getElementById("restartButton"),
  readButton: document.getElementById("readButton"),
  nextButton: document.getElementById("nextButton"),
  directionsButton: document.getElementById("directionsButton"),
  directionsOverlay: document.getElementById("directionsOverlay"),
  directionsArrow: document.getElementById("directionsArrow"),
  directionsText: document.getElementById("directionsText"),
};

const state = {
  sections: [],
  currentSectionId: 1,
  currentIndex: 0,
  readingTimerId: null,
  directionsTimerIds: [],
  directionsActive: false,
  voices: [],
};

function normalizeText(raw) {
  return raw
    .replace(/\r/g, "\n")
    .replace(/\u00a0/g, " ")
    .replace(/[“”]/g, "\"")
    .replace(/[’]/g, "'")
    .replace(/[–—]/g, "-")
    .replace(/…/g, "...");
}

function parseSections(rawText) {
  const normalized = normalizeText(rawText);
  const lines = normalized
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const sections = [];
  let currentSection = null;

  lines.forEach((line) => {
    const sectionMatch = line.match(/^\/?(\d)\)\s*(.+)$/);
    if (sectionMatch) {
      currentSection = {
        id: Number(sectionMatch[1]),
        title: sectionMatch[2].trim(),
        lines: [],
      };
      sections.push(currentSection);
      return;
    }

    if (!currentSection) {
      return;
    }

    const [englishPart, czechPart = ""] = line.split("/", 2);
    const dialogueMatch = englishPart.trim().match(/^([A-Za-z]+):\s*(.+)$/);

    if (dialogueMatch) {
      currentSection.lines.push({
        type: "dialogue",
        speaker: dialogueMatch[1],
        english: dialogueMatch[2].trim(),
        czech: czechPart.trim(),
      });
      return;
    }

    currentSection.lines.push({
      type: "stage",
      speaker: null,
      english: englishPart.trim(),
      czech: czechPart.trim(),
    });
  });

  return sections.sort((left, right) => left.id - right.id);
}

function getCurrentSection() {
  return state.sections.find((section) => section.id === state.currentSectionId) || null;
}

function getCurrentLine() {
  const section = getCurrentSection();
  if (!section || section.lines.length === 0) {
    return null;
  }
  return section.lines[state.currentIndex] || null;
}

function cancelSpeech() {
  window.speechSynthesis?.cancel();
}

function clearReadingTimer() {
  if (state.readingTimerId !== null) {
    window.clearTimeout(state.readingTimerId);
    state.readingTimerId = null;
  }
  ui.focusLine.classList.remove("is-reading");
}

function chooseVoiceForSpeaker(speaker) {
  if (!("speechSynthesis" in window)) {
    return null;
  }

  const availableVoices = window.speechSynthesis.getVoices();
  state.voices = availableVoices;
  if (!speaker || availableVoices.length === 0) {
    return null;
  }

  const [, genderHint] = SPEAKER_VOICE_HINTS[speaker] || ["en-US", null];
  const englishVoices = availableVoices.filter((voice) => voice.lang && voice.lang.toLowerCase().startsWith("en"));
  const searchPool = englishVoices.length > 0 ? englishVoices : availableVoices;

  const nameMatchers = genderHint === "female"
    ? ["samantha", "karen", "moira", "tessa", "zira", "victoria", "ava"]
    : ["daniel", "reed", "alex", "fred", "ralph", "eddy", "tom"];

  for (const matcher of nameMatchers) {
    const match = searchPool.find((voice) => voice.name.toLowerCase().includes(matcher));
    if (match) {
      return match;
    }
  }

  return searchPool[0] || null;
}

function speakLine(line) {
  if (!line || line.type !== "dialogue" || !line.english || !("speechSynthesis" in window)) {
    return;
  }

  cancelSpeech();
  const utterance = new SpeechSynthesisUtterance(line.english);
  utterance.lang = "en-US";
  utterance.rate = 0.9;
  utterance.pitch = 1;
  const chosenVoice = chooseVoiceForSpeaker(line.speaker);
  if (chosenVoice) {
    utterance.voice = chosenVoice;
  }
  window.speechSynthesis.speak(utterance);
}

function updatePortrait(line) {
  const speaker = line?.type === "dialogue" ? line.speaker : null;
  const fileName = speaker ? PORTRAIT_FILES[speaker] : null;

  if (!speaker || !fileName) {
    ui.speakerPortrait.hidden = true;
    ui.speakerPortrait.removeAttribute("src");
    ui.speakerPortrait.alt = "";
    ui.portraitPlaceholder.hidden = false;
    ui.portraitName.textContent = "No portrait";
    return;
  }

  ui.speakerPortrait.src = `assets/${fileName}`;
  ui.speakerPortrait.alt = speaker;
  ui.speakerPortrait.hidden = false;
  ui.portraitPlaceholder.hidden = true;
  ui.portraitName.textContent = speaker;
}

function renderTranscript() {
  const section = getCurrentSection();
  ui.transcript.innerHTML = "";

  if (!section) {
    return;
  }

  section.lines.slice(0, state.currentIndex + 1).forEach((line, index) => {
    const article = document.createElement("article");
    article.className = `transcript-line${index === state.currentIndex ? " active" : ""}${line.type === "stage" ? " stage-note" : ""}`;

    const head = document.createElement("div");
    head.className = "transcript-head";

    const speaker = document.createElement("span");
    speaker.className = "speaker-tag";
    speaker.textContent = line.type === "dialogue" ? line.speaker : "Note";

    const lineIndex = document.createElement("span");
    lineIndex.className = "line-index";
    lineIndex.textContent = `${index + 1}`;

    head.appendChild(speaker);
    head.appendChild(lineIndex);

    const english = document.createElement("p");
    english.className = "line-english";
    english.textContent = line.english;

    article.appendChild(head);
    article.appendChild(english);

    if (line.czech) {
      const czech = document.createElement("p");
      czech.className = "line-czech";
      czech.textContent = line.czech;
      article.appendChild(czech);
    }

    ui.transcript.appendChild(article);
  });

  ui.transcript.scrollTop = ui.transcript.scrollHeight;
}

function renderCurrentLine() {
  const section = getCurrentSection();
  const line = getCurrentLine();

  if (!section || !line) {
    ui.sectionTitle.textContent = "No section data";
    ui.currentSpeaker.textContent = "No line";
    ui.lineCounter.textContent = "0 / 0";
    ui.focusEnglish.textContent = "No data loaded.";
    ui.focusCzech.textContent = "";
    ui.sceneCaption.textContent = "";
    return;
  }

  ui.sectionTitle.textContent = `${section.id}. ${section.title}`;
  ui.currentSpeaker.textContent = line.type === "dialogue" ? line.speaker : "Stage note";
  ui.lineCounter.textContent = `${state.currentIndex + 1} / ${section.lines.length}`;
  ui.focusEnglish.textContent = line.english || "";
  ui.focusCzech.textContent = line.czech || "";
  ui.sceneCaption.textContent = SCENE_CAPTIONS[section.id] || section.title;
  ui.sceneImage.src = `assets/RestKPTL${section.id}.jpg`;
  ui.sceneImage.alt = section.title;

  updatePortrait(line);
  renderTranscript();
  updateButtons();
}

function updateButtons() {
  const section = getCurrentSection();
  const hasNext = Boolean(section) && state.currentIndex < section.lines.length - 1;

  ui.nextButton.disabled = state.directionsActive || !hasNext;
  ui.readButton.disabled = state.directionsActive || !getCurrentLine();
  ui.restartButton.disabled = state.directionsActive || !section;
  ui.directionsButton.disabled = state.directionsActive || state.currentSectionId !== 1;

  Array.from(ui.sectionNav.querySelectorAll(".section-button")).forEach((button) => {
    button.disabled = state.directionsActive;
    button.classList.toggle("active", Number(button.dataset.sectionId) === state.currentSectionId);
  });
}

function setSection(sectionId) {
  clearReadingTimer();
  cancelSpeech();
  state.currentSectionId = sectionId;
  state.currentIndex = 0;
  renderCurrentLine();
}

function nextLine() {
  const section = getCurrentSection();
  if (!section || state.currentIndex >= section.lines.length - 1) {
    return;
  }

  clearReadingTimer();
  cancelSpeech();
  state.currentIndex += 1;
  renderCurrentLine();
}

function restartSection() {
  clearReadingTimer();
  cancelSpeech();
  state.currentIndex = 0;
  renderCurrentLine();
}

function readCurrentLine() {
  const line = getCurrentLine();
  if (!line) {
    return;
  }

  clearReadingTimer();
  ui.focusLine.classList.add("is-reading");
  speakLine(line);
  state.readingTimerId = window.setTimeout(() => {
    ui.focusLine.classList.remove("is-reading");
    state.readingTimerId = null;
  }, 9000);
}

function clearDirectionsTimers() {
  state.directionsTimerIds.forEach((timerId) => window.clearTimeout(timerId));
  state.directionsTimerIds.length = 0;
}

function finishDirectionsDemo() {
  clearDirectionsTimers();
  state.directionsActive = false;
  ui.directionsOverlay.classList.add("hidden");
  ui.directionsArrow.textContent = "";
  ui.directionsText.textContent = "";
  renderCurrentLine();
}

function scheduleDirection(delayMs, callback) {
  const timerId = window.setTimeout(() => {
    state.directionsTimerIds = state.directionsTimerIds.filter((item) => item !== timerId);
    callback();
  }, delayMs);
  state.directionsTimerIds.push(timerId);
}

function playDirectionsDemo() {
  if (state.currentSectionId !== 1 || state.directionsActive) {
    return;
  }

  clearReadingTimer();
  cancelSpeech();
  state.directionsActive = true;
  updateButtons();
  ui.directionsOverlay.classList.remove("hidden");

  const steps = [
    ["↑", "go straight"],
    ["←", "turn left"],
    ["→", "turn right"],
    ["↑", "go straight"],
    ["←", "turn left"],
    ["→", "turn right"],
  ];

  const showStep = (index) => {
    if (index >= steps.length) {
      finishDirectionsDemo();
      return;
    }

    const [arrow, text] = steps[index];
    ui.directionsArrow.textContent = arrow;
    ui.directionsText.textContent = text;
    speakLine({ type: "dialogue", speaker: "Kate", english: text });

    scheduleDirection(1700, () => {
      ui.directionsArrow.textContent = "";
      ui.directionsText.textContent = "";
      scheduleDirection(450, () => showStep(index + 1));
    });
  };

  showStep(0);
}

function renderSectionButtons() {
  ui.sectionNav.innerHTML = "";

  state.sections.forEach((section) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "section-button";
    button.dataset.sectionId = String(section.id);
    button.textContent = String(section.id);
    button.addEventListener("click", () => setSection(section.id));
    ui.sectionNav.appendChild(button);
  });
}

async function loadApp() {
  const response = await fetch("assets/NavstevaRestaurace.txt");
  if (!response.ok) {
    throw new Error(`Failed to load text data: ${response.status}`);
  }

  const rawText = await response.text();
  state.sections = parseSections(rawText);
  renderSectionButtons();
  setSection(1);
}

ui.restartButton.addEventListener("click", restartSection);
ui.readButton.addEventListener("click", readCurrentLine);
ui.nextButton.addEventListener("click", nextLine);
ui.directionsButton.addEventListener("click", playDirectionsDemo);

window.speechSynthesis?.addEventListener?.("voiceschanged", () => {
  state.voices = window.speechSynthesis.getVoices();
});

loadApp().catch((error) => {
  ui.sectionTitle.textContent = "Load error";
  ui.currentSpeaker.textContent = "Could not load lesson";
  ui.focusEnglish.textContent = error.message;
  ui.focusCzech.textContent = "";
});
