const COLORS = [
  "red", "blue", "green", "yellow", "orange",
  "white", "black", "purple", "brown", "gray", "pink",
];

const NUMBER_TEXT_COLORS = [
  "red", "blue", "green", "orange", "black", "purple", "brown", "gray", "pink",
];

const TRAINING_COLORS = [
  ["white", "white"],
  ["black", "black"],
  ["purple", "purple"],
  ["gray", "gray"],
  ["yellow", "yellow"],
  ["red", "red"],
  ["blue", "blue"],
  ["green", "green"],
  ["brown", "brown"],
  ["pink", "pink"],
];

const NUMBER_WORDS = {
  0: "zero",
  1: "one",
  2: "two",
  3: "three",
  4: "four",
  5: "five",
  6: "six",
  7: "seven",
  8: "eight",
  9: "nine",
  10: "ten",
  11: "eleven",
  12: "twelve",
};

const ICON_FILES = [
  "01_red-apple_1F34E.png",
  "02_tangerine_1F34A.png",
  "03_banana_1F34C.png",
  "04_strawberry_1F353.png",
  "05_grapes_1F347.png",
  "06_cherries_1F352.png",
  "10_carrot_1F955.png",
  "14_bread_1F35E.png",
  "16_pizza_1F355.png",
  "21_doughnut_1F369.png",
  "33_closed-book_1F4D5.png",
  "36_books_1F4DA.png",
  "39_pencil_270F.png",
  "41_scissors_2702.png",
  "45_briefcase_1F4BC.png",
  "46_school-satchel_1F392.png",
  "48_magnifying-glass_1F50D.png",
  "49_key_1F511.png",
];

const ui = {
  screens: Array.from(document.querySelectorAll("[data-screen]")),
  navButtons: Array.from(document.querySelectorAll("[data-screen-target]")),
  mainBoard: document.getElementById("mainBoard"),
  numberStatus: document.getElementById("numberStatus"),
  colorStatus: document.getElementById("colorStatus"),
  newExampleButton: document.getElementById("newExampleButton"),
  numbersBoard: document.getElementById("numbersBoard"),
  numbersNewButton: document.getElementById("numbersNewButton"),
  numbersResultButton: document.getElementById("numbersResultButton"),
  owlOverlay: document.getElementById("owlOverlay"),
  owlCloseButton: document.getElementById("owlCloseButton"),
  owlImage: document.getElementById("owlImage"),
  turboWord: document.getElementById("turboWord"),
  turboNumber: document.getElementById("turboNumber"),
  turboIcons: document.getElementById("turboIcons"),
  turboHint: document.getElementById("turboHint"),
  turboGoButton: document.getElementById("turboGoButton"),
  turboEndButton: document.getElementById("turboEndButton"),
  colorShape: document.getElementById("colorShape"),
  colorsWord: document.getElementById("colorsWord"),
  colorsHint: document.getElementById("colorsHint"),
  colorsGoButton: document.getElementById("colorsGoButton"),
  colorsStopButton: document.getElementById("colorsStopButton"),
};

const appState = {
  screen: "main",
  main: {
    leftCount: 0,
    rightCount: 0,
    leftColors: [],
    rightColors: [],
    resultShown: false,
  },
  numbers: {
    token: 0,
    timers: [],
    first: null,
    second: null,
    result: null,
    op: "+",
    firstColor: "black",
    secondColor: "black",
    resultColor: "black",
    slotIcons: { first: null, second: null, result: null },
    resultPressCount: 0,
    owlShown: false,
    owlHideTimer: null,
    visible: {
      firstNum: false,
      firstWord: false,
      op: false,
      secondNum: false,
      secondWord: false,
      equal: false,
      result: false,
    },
  },
  turbo: {
    running: false,
    pending: null,
    timers: [],
    currentNumber: null,
    currentWord: "",
    currentIcons: [],
  },
  colors: {
    running: false,
    pending: null,
    timers: [],
    currentWord: "",
    currentColor: "",
    currentShape: "circle",
    cyclePool: [],
  },
};

const owlAudio = new Audio("oul170426.m4a");
owlAudio.preload = "auto";

function randomChoice(items) {
  return items[Math.floor(Math.random() * items.length)];
}

function shuffle(items) {
  const clone = [...items];
  for (let index = clone.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [clone[index], clone[swapIndex]] = [clone[swapIndex], clone[index]];
  }
  return clone;
}

function cancelSpeech() {
  window.speechSynthesis?.cancel();
}

function speakEnglish(text) {
  if (!text || !("speechSynthesis" in window)) {
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "en-US";
  utterance.rate = 0.88;
  utterance.pitch = 1.0;
  const englishVoice = window.speechSynthesis
    .getVoices()
    .find((voice) => voice.lang && voice.lang.toLowerCase().startsWith("en"));
  if (englishVoice) {
    utterance.voice = englishVoice;
  }
  window.speechSynthesis.speak(utterance);
}

function clearTimers(bucket) {
  bucket.forEach((timerId) => window.clearTimeout(timerId));
  bucket.length = 0;
}

function createBallButton(color) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "ball-button";
  button.style.background = color;
  button.style.borderColor = color === "white" ? "#202020" : color;
  button.style.borderWidth = color === "white" ? "3px" : "2px";
  button.setAttribute("aria-label", color);
  button.addEventListener("click", () => {
    ui.colorStatus.textContent = color.toUpperCase();
    ui.colorStatus.style.color = color === "white" ? "#4b5968" : color;
    speakEnglish(color);
  });
  return button;
}

function createWordBadge(number) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "word-badge";
  button.textContent = NUMBER_WORDS[number].toUpperCase();
  button.addEventListener("click", () => {
    ui.numberStatus.textContent = NUMBER_WORDS[number].toUpperCase();
    speakEnglish(NUMBER_WORDS[number]);
  });
  return button;
}

function createNumberBadge(number) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "number-badge";
  button.textContent = String(number);
  button.addEventListener("click", () => {
    ui.numberStatus.textContent = NUMBER_WORDS[number].toUpperCase();
    speakEnglish(NUMBER_WORDS[number]);
  });
  return button;
}

function renderOperandColumn(count, colors, label) {
  const column = document.createElement("article");
  column.className = "operand-column";

  const balls = document.createElement("div");
  balls.className = "operand-balls";
  colors.forEach((color) => balls.appendChild(createBallButton(color)));

  const meta = document.createElement("div");
  meta.className = "operand-meta";
  meta.appendChild(createNumberBadge(count));
  meta.appendChild(createWordBadge(count));

  const slotLabel = document.createElement("div");
  slotLabel.className = "slot-label";
  slotLabel.textContent = label;
  meta.appendChild(slotLabel);

  column.appendChild(balls);
  column.appendChild(meta);
  return column;
}

function renderMainBoard() {
  ui.mainBoard.innerHTML = "";
  const { leftCount, rightCount, leftColors, rightColors, resultShown } = appState.main;

  ui.mainBoard.appendChild(renderOperandColumn(leftCount, leftColors, "Left"));

  const plus = document.createElement("div");
  plus.className = "math-sign";
  plus.textContent = "+";
  ui.mainBoard.appendChild(plus);

  ui.mainBoard.appendChild(renderOperandColumn(rightCount, rightColors, "Right"));

  const equal = document.createElement("button");
  equal.type = "button";
  equal.className = "equal-trigger";
  equal.textContent = "=";
  equal.addEventListener("click", revealMainResult);
  ui.mainBoard.appendChild(equal);

  const resultColumn = document.createElement("article");
  resultColumn.className = "result-column";

  if (!resultShown) {
    const placeholder = document.createElement("div");
    placeholder.className = "result-placeholder";
    placeholder.textContent = "Click = to reveal the result.";
    resultColumn.appendChild(placeholder);
  } else {
    const total = leftCount + rightCount;
    const resultBalls = document.createElement("div");
    resultBalls.className = "result-balls";
    [...leftColors, ...rightColors].forEach((color) => resultBalls.appendChild(createBallButton(color)));
    resultColumn.appendChild(resultBalls);

    const meta = document.createElement("div");
    meta.className = "result-meta";
    meta.appendChild(createNumberBadge(total));
    meta.appendChild(createWordBadge(total));
    const label = document.createElement("div");
    label.className = "slot-label";
    label.textContent = "Result";
    meta.appendChild(label);
    resultColumn.appendChild(meta);
  }

  ui.mainBoard.appendChild(resultColumn);
}

function newMainExample() {
  let first = 0;
  let second = 0;
  while (first + second < 2 || first + second > 10) {
    first = 1 + Math.floor(Math.random() * 10);
    second = 1 + Math.floor(Math.random() * 10);
  }

  appState.main.leftCount = first;
  appState.main.rightCount = second;
  appState.main.leftColors = Array.from({ length: first }, () => randomChoice(COLORS));
  appState.main.rightColors = Array.from({ length: second }, () => randomChoice(COLORS));
  appState.main.resultShown = false;

  ui.numberStatus.textContent = "NUMBER";
  ui.colorStatus.textContent = "COLOR";
  ui.colorStatus.style.color = "";
  renderMainBoard();
}

function revealMainResult() {
  if (appState.main.resultShown) {
    return;
  }
  appState.main.resultShown = true;
  renderMainBoard();
}

function numbersPickSlotIcons() {
  const shuffled = shuffle(ICON_FILES);
  appState.numbers.slotIcons = {
    first: shuffled[0],
    second: shuffled[1],
    result: shuffled[2],
  };
}

function createNumbersSlot(title, number, color, iconFile, wordVisible, resultVisible) {
  const slot = document.createElement("article");
  slot.className = "numbers-slot";

  const value = document.createElement("div");
  value.className = "numbers-value";

  const num = document.createElement("div");
  num.className = "number-big";
  num.textContent = number === null || number === undefined || number === "" ? "" : String(number);
  num.style.color = color;

  const word = document.createElement("div");
  word.className = "word-small";
  word.textContent = wordVisible && resultVisible && number !== null ? NUMBER_WORDS[number].toUpperCase() : "";
  word.style.color = color;

  value.appendChild(num);
  value.appendChild(word);

  const grid = document.createElement("div");
  grid.className = "icon-grid";
  const safeCount = typeof number === "number" ? Math.min(12, Math.max(0, number)) : 0;
  for (let index = 0; index < safeCount; index += 1) {
    const img = document.createElement("img");
    img.src = `assets/openmoji_numbers/${iconFile}`;
    img.alt = title;
    grid.appendChild(img);
  }

  const label = document.createElement("div");
  label.className = "slot-label";
  label.textContent = title;

  slot.appendChild(value);
  slot.appendChild(grid);
  slot.appendChild(label);
  return slot;
}

function renderNumbersBoard() {
  ui.numbersBoard.innerHTML = "";
  const state = appState.numbers;
  const firstNumber = state.visible.firstNum ? state.first : null;
  const secondNumber = state.visible.secondNum ? state.second : null;
  const resultNumber = state.visible.result ? state.result : null;

  ui.numbersBoard.appendChild(
    createNumbersSlot("First", firstNumber, state.firstColor, state.slotIcons.first, state.visible.firstWord, state.visible.firstNum),
  );

  const op = document.createElement("div");
  op.className = "math-sign";
  op.textContent = state.visible.op ? state.op : "";
  ui.numbersBoard.appendChild(op);

  ui.numbersBoard.appendChild(
    createNumbersSlot("Second", secondNumber, state.secondColor, state.slotIcons.second, state.visible.secondWord, state.visible.secondNum),
  );

  const eq = document.createElement("div");
  eq.className = "math-sign";
  eq.textContent = state.visible.equal ? "=" : "";
  ui.numbersBoard.appendChild(eq);

  ui.numbersBoard.appendChild(
    createNumbersSlot("Result", resultNumber, state.resultColor, state.slotIcons.result, state.visible.result, state.visible.result),
  );
}

function scheduleNumbers(delayMs, callback) {
  const token = appState.numbers.token;
  const timerId = window.setTimeout(() => {
    appState.numbers.timers = appState.numbers.timers.filter((item) => item !== timerId);
    if (token !== appState.numbers.token) {
      return;
    }
    callback();
  }, delayMs);
  appState.numbers.timers.push(timerId);
}

function clearNumbersSequence() {
  appState.numbers.token += 1;
  clearTimers(appState.numbers.timers);
}

function hideOwlOverlay() {
  if (appState.numbers.owlHideTimer) {
    window.clearTimeout(appState.numbers.owlHideTimer);
    appState.numbers.owlHideTimer = null;
  }
  owlAudio.pause();
  try {
    owlAudio.currentTime = 0;
  } catch (error) {
    // ignore currentTime reset errors
  }
  ui.owlOverlay.classList.add("hidden");
  ui.owlOverlay.setAttribute("aria-hidden", "true");
}

function showOwlOverlay() {
  if (appState.numbers.owlShown) {
    return;
  }
  appState.numbers.owlShown = true;
  cancelSpeech();
  ui.owlOverlay.classList.remove("hidden");
  ui.owlOverlay.setAttribute("aria-hidden", "false");
  try {
    owlAudio.currentTime = 0;
  } catch (error) {
    // ignore currentTime reset errors
  }
  owlAudio.play().catch(() => {});
  appState.numbers.owlHideTimer = window.setTimeout(hideOwlOverlay, 40000);
}

function newNumbersSequence() {
  clearNumbersSequence();
  const visible = {
    firstNum: false,
    firstWord: false,
    op: false,
    secondNum: false,
    secondWord: false,
    equal: false,
    result: false,
  };

  let first = 1;
  let second = 1;
  let result = 0;
  const op = Math.random() < 0.5 ? "+" : "-";
  if (op === "+") {
    first = 1 + Math.floor(Math.random() * 11);
    second = 1 + Math.floor(Math.random() * Math.min(11, 12 - first));
    result = first + second;
  } else {
    first = 1 + Math.floor(Math.random() * 11);
    second = 1 + Math.floor(Math.random() * first);
    result = first - second;
  }

  appState.numbers.first = first;
  appState.numbers.second = second;
  appState.numbers.result = result;
  appState.numbers.op = op;
  appState.numbers.firstColor = randomChoice(NUMBER_TEXT_COLORS);
  appState.numbers.secondColor = randomChoice(NUMBER_TEXT_COLORS);
  appState.numbers.resultColor = randomChoice(NUMBER_TEXT_COLORS);
  appState.numbers.visible = visible;
  numbersPickSlotIcons();
  renderNumbersBoard();

  appState.numbers.visible.firstNum = true;
  renderNumbersBoard();

  scheduleNumbers(500, () => {
    appState.numbers.visible.firstWord = true;
    renderNumbersBoard();
    speakEnglish(NUMBER_WORDS[appState.numbers.first]);
  });

  scheduleNumbers(2700, () => {
    appState.numbers.visible.op = true;
    renderNumbersBoard();
    speakEnglish(appState.numbers.op === "+" ? "plus" : "minus");
  });

  scheduleNumbers(3600, () => {
    appState.numbers.visible.secondNum = true;
    renderNumbersBoard();
  });

  scheduleNumbers(4100, () => {
    appState.numbers.visible.secondWord = true;
    renderNumbersBoard();
    speakEnglish(NUMBER_WORDS[appState.numbers.second]);
  });

  scheduleNumbers(6300, () => {
    appState.numbers.visible.equal = true;
    renderNumbersBoard();
    speakEnglish("is");
  });
}

function showNumbersResult() {
  if (appState.numbers.result === null) {
    return;
  }
  appState.numbers.resultPressCount += 1;
  appState.numbers.visible.result = true;
  renderNumbersBoard();
  speakEnglish(NUMBER_WORDS[appState.numbers.result]);
  if (appState.numbers.resultPressCount === 3 && !appState.numbers.owlShown) {
    showOwlOverlay();
  }
}

function schedulePractice(mode, delayMs, callback) {
  const state = appState[mode];
  const scheduledAt = Date.now();
  const timerId = window.setTimeout(() => {
    state.timers = state.timers.filter((item) => item !== timerId);
    state.pending = null;
    if (!state.running) {
      return;
    }
    callback();
  }, delayMs);
  state.pending = { callback, scheduledAt, delayMs, timerId };
  state.timers.push(timerId);
}

function pausePractice(mode) {
  const state = appState[mode];
  state.running = false;
  if (state.pending) {
    const elapsed = Date.now() - state.pending.scheduledAt;
    state.pending.delayMs = Math.max(0, state.pending.delayMs - elapsed);
  }
  clearTimers(state.timers);
  if (state.pending) {
    state.pending.timerId = null;
  }
}

function resumePractice(mode, fallbackStart) {
  const state = appState[mode];
  if (state.running) {
    return;
  }
  state.running = true;
  if (state.pending) {
    schedulePractice(mode, state.pending.delayMs, state.pending.callback);
    return;
  }
  fallbackStart();
}

function renderTurbo() {
  ui.turboWord.textContent = appState.turbo.currentWord ? appState.turbo.currentWord.toUpperCase() : "";
  ui.turboNumber.textContent = appState.turbo.currentNumber === null ? "" : String(appState.turbo.currentNumber);
  ui.turboIcons.innerHTML = "";
  appState.turbo.currentIcons.forEach((iconFile) => {
    const img = document.createElement("img");
    img.src = `assets/openmoji_numbers/${iconFile}`;
    img.alt = "number object";
    ui.turboIcons.appendChild(img);
  });
}

function turboStartCycle() {
  if (!appState.turbo.running) {
    return;
  }

  const number = Math.floor(Math.random() * 13);
  appState.turbo.currentNumber = number;
  appState.turbo.currentWord = "";
  appState.turbo.currentIcons = Array.from({ length: number }, () => randomChoice(ICON_FILES));
  ui.turboHint.textContent = "";
  renderTurbo();

  schedulePractice("turbo", 3000, turboShowWord);
}

function turboShowWord() {
  if (!appState.turbo.running || appState.turbo.currentNumber === null) {
    return;
  }
  appState.turbo.currentWord = NUMBER_WORDS[appState.turbo.currentNumber];
  renderTurbo();
  schedulePractice("turbo", 3000, turboSpeakWord);
}

function turboSpeakWord() {
  if (!appState.turbo.running || !appState.turbo.currentWord) {
    return;
  }
  speakEnglish(appState.turbo.currentWord);
  schedulePractice("turbo", 2000, turboStartCycle);
}

function resetTurbo() {
  pausePractice("turbo");
  appState.turbo.pending = null;
  appState.turbo.currentNumber = null;
  appState.turbo.currentWord = "";
  appState.turbo.currentIcons = [];
  ui.turboHint.textContent = "Go = start/continue, End = pause, Back = main screen";
  renderTurbo();
}

function renderColors() {
  const shape = ui.colorShape;
  const color = appState.colors.currentColor || "transparent";
  const shapeName = appState.colors.currentShape;

  shape.className = `shape-object ${shapeName}`;
  shape.style.background = "";
  shape.style.borderBottomColor = "";
  shape.style.borderLeftColor = "";
  shape.style.borderRightColor = "";
  shape.style.borderBottomStyle = "";

  if (shapeName === "triangle") {
    shape.style.borderBottomColor = color;
    shape.style.borderBottomStyle = "solid";
  } else {
    shape.style.background = color;
    shape.style.border = color === "white" ? "4px solid #2f3a43" : "3px solid transparent";
  }

  ui.colorsWord.textContent = appState.colors.currentWord ? appState.colors.currentWord.toUpperCase() : "";
}

function nextTrainingColor() {
  if (appState.colors.cyclePool.length === 0) {
    appState.colors.cyclePool = shuffle(TRAINING_COLORS);
  }
  return appState.colors.cyclePool.pop();
}

function colorsStartCycle() {
  if (!appState.colors.running) {
    return;
  }

  const [word, color] = nextTrainingColor();
  appState.colors.currentWord = "";
  appState.colors.currentColor = color;
  appState.colors.currentShape = randomChoice(["circle", "square", "triangle"]);
  ui.colorsHint.textContent = "";
  renderColors();

  schedulePractice("colors", 2000, colorsShowWord.bind(null, word));
}

function colorsShowWord(word) {
  if (!appState.colors.running) {
    return;
  }
  appState.colors.currentWord = word;
  renderColors();
  schedulePractice("colors", 2000, colorsSpeakWord.bind(null, word));
}

function colorsSpeakWord(word) {
  if (!appState.colors.running) {
    return;
  }
  speakEnglish(word);
  schedulePractice("colors", 2000, colorsStartCycle);
}

function resetColors() {
  pausePractice("colors");
  appState.colors.pending = null;
  appState.colors.currentWord = "";
  appState.colors.currentColor = "";
  appState.colors.currentShape = "circle";
  appState.colors.cyclePool = [];
  ui.colorsHint.textContent = "Go = start, Stop = pause, Back = main screen";
  renderColors();
}

function showScreen(screenName) {
  appState.screen = screenName;
  cancelSpeech();

  if (screenName !== "numbers") {
    clearNumbersSequence();
    hideOwlOverlay();
  }
  if (screenName !== "turbo") {
    resetTurbo();
  }
  if (screenName !== "colors") {
    resetColors();
  }

  ui.screens.forEach((screen) => {
    screen.classList.toggle("active", screen.dataset.screen === screenName);
  });
  ui.navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.screenTarget === screenName);
  });

  if (screenName === "main") {
    renderMainBoard();
  } else if (screenName === "numbers") {
    newNumbersSequence();
  } else if (screenName === "turbo") {
    resetTurbo();
  } else if (screenName === "colors") {
    resetColors();
  }
}

ui.newExampleButton.addEventListener("click", newMainExample);
ui.numbersNewButton.addEventListener("click", newNumbersSequence);
ui.numbersResultButton.addEventListener("click", showNumbersResult);
ui.owlCloseButton.addEventListener("click", hideOwlOverlay);
ui.owlOverlay.addEventListener("click", (event) => {
  if (event.target === ui.owlOverlay) {
    hideOwlOverlay();
  }
});
owlAudio.addEventListener("ended", hideOwlOverlay);
ui.turboGoButton.addEventListener("click", () => resumePractice("turbo", turboStartCycle));
ui.turboEndButton.addEventListener("click", () => pausePractice("turbo"));
ui.colorsGoButton.addEventListener("click", () => resumePractice("colors", colorsStartCycle));
ui.colorsStopButton.addEventListener("click", () => pausePractice("colors"));

ui.navButtons.forEach((button) => {
  button.addEventListener("click", () => {
    showScreen(button.dataset.screenTarget);
  });
});

window.speechSynthesis?.addEventListener?.("voiceschanged", () => {});

newMainExample();
renderNumbersBoard();
renderTurbo();
renderColors();
