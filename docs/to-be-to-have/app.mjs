import { makeDeck, sentenceParts, Playback } from './core.mjs';

const $ = id => document.getElementById(id);
const modeButtons = [...document.querySelectorAll('[data-mode]')];
const lessonButtons = [...document.querySelectorAll('[data-lesson]')];
const names = { be: 'TO BE · BÝT', have: 'TO HAVE · MÍT', go: 'TO GO · JÍT' };
const state = { mode: 'sentences', lesson: 'be', deck: [], pos: 0, question: false, running: false };
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const audio = new Audio();
audio.preload = 'auto';
const player = new Playback(audio, message => { $('status').textContent = message; });
let data;

const current = () => state.deck[state.pos];
const clip = key => data.audio[key].src;
const rate = () => Number($('speed').value);

function stop() {
  player.stop();
  state.running = false;
  $('pause').disabled = true;
  $('pause').textContent = 'Ⅱ Pauza';
  $('word-stage').classList.remove('is-speaking');
  $('status').textContent = '';
}

function resetDeck() {
  const items = (state.mode === 'sentences' ? data.sentences : data.verbs).filter(row => row.lesson === state.lesson);
  state.deck = makeDeck(items, $('shuffle').checked);
  state.pos = 0;
  $('jump').replaceChildren(...state.deck.map((row, i) => {
    const option = document.createElement('option');
    option.value = row.id;
    option.textContent = `${i + 1}. ${row.question && state.mode === 'sentences' ? row.question : row.statement}`;
    return option;
  }));
  render();
}

function renderWords(row, question = false, hidden = false) {
  const nodes = sentenceParts(row, question).map(part => {
    const node = document.createElement('span');
    node.className = `word ${part.key}${hidden ? ' unseen' : ''}`;
    node.dataset.key = part.key;
    node.textContent = part.text;
    return node;
  });
  $('word-stage').replaceChildren(...nodes);
  $('word-stage').setAttribute('aria-label', question ? row.question : row.statement);
}

function render() {
  stop();
  const row = current();
  if (!row) return;
  state.question = false;
  const image = data.images[row.image];
  $('scene-image').src = image.src;
  $('scene-image').alt = image.alt;
  $('scene-image').classList.remove('arrive');
  void $('scene-image').offsetWidth;
  $('scene-image').classList.add('arrive');
  $('age-badge').hidden = !row.age;
  $('age-badge').textContent = row.age || '';
  $('age-badge').lang = 'en';
  $('topic-label').textContent = names[state.lesson];
  $('progress').textContent = `${state.pos + 1} / ${state.deck.length}`;
  $('jump').value = row.id;
  $('previous').disabled = state.pos === 0;
  $('sentence-view').hidden = state.mode !== 'sentences';
  $('builder-view').hidden = state.mode !== 'builder';
  $('exercise-label').textContent = state.mode === 'sentences' ? 'OTÁZKA PRO TEBE' : 'MALÁ DÍLNA ANGLIČTINY';
  for (const button of modeButtons) button.setAttribute('aria-pressed', String(button.dataset.mode === state.mode));
  for (const button of lessonButtons) button.setAttribute('aria-pressed', String(button.dataset.lesson === state.lesson));
  if (state.mode === 'sentences') {
    $('question').textContent = row.question;
    for (const kind of ['positive', 'negative']) {
      $(`${kind}-text`).textContent = 'Odkryj odpověď';
      $(`${kind}-text`).removeAttribute('lang');
      $(kind).setAttribute('aria-expanded', 'false');
      $(kind).classList.remove('revealed');
    }
  } else {
    renderWords(row);
    $('translation-toggle').disabled = false;
    $('grammar-hint').textContent = 'Nejdřív si slož větu. Pak z ní vykouzli otázku.';
    $('transform-note').textContent = '';
    $('translation').textContent = row.translation;
    $('translation').hidden = $('translation-toggle').getAttribute('aria-expanded') !== 'true';
    $('make-question').textContent = '✦ Vytvořit otázku';
  }
}

async function speak(key) {
  stop();
  return player.play(clip(key), player.token, rate());
}

function next(autoplay = false) {
  if (state.pos + 1 >= state.deck.length) {
    const previousLast = current().id;
    const items = (state.mode === 'sentences' ? data.sentences : data.verbs).filter(row => row.lesson === state.lesson);
    state.deck = makeDeck(items, $('shuffle').checked, Math.random, previousLast);
    state.pos = 0;
    $('jump').replaceChildren(...state.deck.map((row, i) => {
      const option = document.createElement('option');
      option.value = row.id;
      option.textContent = `${i + 1}. ${state.mode === 'sentences' ? row.question : row.statement}`;
      return option;
    }));
  } else state.pos++;
  render();
  if (autoplay && state.mode === 'sentences') speak(current().audio.question);
}

function beginRunning() {
  stop();
  state.running = true;
  $('pause').disabled = false;
  return player.token;
}

function finishRunning(token) {
  if (!player.active(token)) return;
  state.running = false;
  $('pause').disabled = true;
  $('pause').textContent = 'Ⅱ Pauza';
  $('word-stage').classList.remove('is-speaking');
}

async function speakBuilder(key, token) {
  if (!player.active(token)) return false;
  $('word-stage').classList.add('is-speaking');
  const ok = await player.play(clip(key), token, rate());
  if (player.active(token)) $('word-stage').classList.remove('is-speaking');
  return ok;
}

async function buildCycle(token) {
  const row = current();
  state.question = false;
  $('translation-toggle').disabled = false;
  $('translation').hidden = $('translation-toggle').getAttribute('aria-expanded') !== 'true';
  $('make-question').textContent = '✦ Vytvořit otázku';
  $('transform-note').textContent = '';
  renderWords(row, false, true);
  for (const node of $('word-stage').querySelectorAll('.word')) {
    if (!await player.wait(node.dataset.key === 'punctuation' ? 150 : 650, token)) return;
    node.classList.remove('unseen');
    if (!reducedMotion.matches) player.animate(node, [
      { opacity: 0, transform: 'translateY(24px) rotate(-8deg) scale(.75)' },
      { opacity: 1, transform: 'translateY(-5px) rotate(3deg) scale(1.08)', offset: .75 },
      { opacity: 1, transform: 'none' },
    ], { duration: 420, easing: 'ease-out' });
  }
  if (!await player.wait(500, token)) return;
  const ok = await speakBuilder(row.audio.statement, token);
  if (!player.active(token)) return;
  if (ok && $('auto-next').checked) {
    if (!await player.wait(2000, token) || !$('auto-next').checked) return finishRunning(token);
    next();
    const nextToken = beginRunning();
    return buildCycle(nextToken);
  }
  finishRunning(token);
}

async function startBuild() {
  const token = beginRunning();
  await player.prime(clip(current().audio.statement));
  if (player.active(token)) await buildCycle(token);
}

function celebrate() {
  if (reducedMotion.matches) return;
  for (let i = 0; i < 14; i++) {
    const spark = document.createElement('i');
    spark.className = 'spark';
    spark.setAttribute('aria-hidden', 'true');
    spark.style.setProperty('--dx', `${Math.cos(i * 2.4) * (80 + i * 5)}px`);
    spark.style.setProperty('--dy', `${Math.sin(i * 2.4) * 65 - 30}px`);
    spark.style.setProperty('--turn', `${i * 75}deg`);
    spark.addEventListener('animationend', () => spark.remove(), { once: true });
    $('word-stage').append(spark);
  }
}

async function transformQuestion() {
  const token = beginRunning();
  const row = current();
  await player.prime(clip(row.audio.question));
  if (!player.active(token)) return;
  state.question = false;
  renderWords(row);
  $('transform-note').textContent = row.aux ? `${row.aux} přichází na začátek…` : 'Sloveso přeskočí před zájmeno…';
  if (!await player.wait(400, token)) return;
  const before = new Map([...$('word-stage').querySelectorAll('.word')].map(node => [node.dataset.key, node.getBoundingClientRect()]));
  renderWords(row, true);
  state.question = true;
  $('translation').hidden = true;
  $('translation-toggle').disabled = true;
  for (const node of $('word-stage').querySelectorAll('.word')) {
    if (reducedMotion.matches) continue;
    const from = before.get(node.dataset.key);
    const to = node.getBoundingClientRect();
    const dx = from ? from.left - to.left : -90;
    const dy = from ? from.top - to.top : -35;
    player.animate(node, [
      { transform: `translate(${dx}px,${dy}px) rotate(${from ? 0 : -15}deg) scale(${from ? 1 : .4})`, opacity: from ? 1 : 0 },
      { transform: `translate(${dx * .45}px,${dy * .45 - 32}px) rotate(-4deg) scale(1.09)`, opacity: 1, offset: .5 },
      { transform: 'none', opacity: 1 },
    ], { duration: 950, easing: 'cubic-bezier(.25,.7,.2,1)' });
  }
  if (!await player.wait(reducedMotion.matches ? 150 : 1050, token)) return;
  state.question = true;
  $('make-question').textContent = '✦ Znovu vytvořit otázku';
  $('transform-note').textContent = row.aux
    ? row.verb !== row.base ? `${row.aux} + ${row.pronoun} · ${row.verb} → ${row.base}. A otázka je na světě!` : `${row.aux} stojí první. A otázka je na světě!`
    : `${row.base[0].toUpperCase() + row.base.slice(1)} stojí první. A otázka je na světě!`;
  celebrate();
  if (!await player.wait(250, token)) return;
  await speakBuilder(row.audio.question, token);
  finishRunning(token);
}

for (const button of modeButtons) button.addEventListener('click', () => {
  state.mode = button.dataset.mode;
  resetDeck();
});
for (const button of lessonButtons) button.addEventListener('click', () => {
  state.lesson = button.dataset.lesson;
  resetDeck();
});
$('shuffle').addEventListener('change', resetDeck);
$('listen-question').addEventListener('click', () => speak(current().audio.question));
for (const kind of ['positive', 'negative']) $(kind).addEventListener('click', () => {
  const row = current();
  $(`${kind}-text`).textContent = row[kind];
  $(`${kind}-text`).lang = 'en';
  $(kind).setAttribute('aria-expanded', 'true');
  $(kind).classList.remove('revealed');
  void $(kind).offsetWidth;
  $(kind).classList.add('revealed');
  speak(row.audio[kind]);
});
$('next').addEventListener('click', () => next(true));
$('previous').addEventListener('click', () => { if (state.pos > 0) state.pos--; render(); });
$('begin').addEventListener('click', () => { state.pos = 0; render(); });
$('jump').addEventListener('change', () => { state.pos = state.deck.findIndex(row => row.id === $('jump').value); render(); });
$('build-play').addEventListener('click', startBuild);
$('make-question').addEventListener('click', transformQuestion);
$('pause').addEventListener('click', () => {
  if (!state.running) return;
  const paused = player.togglePause();
  $('pause').textContent = paused ? '▶ Pokračovat' : 'Ⅱ Pauza';
});
$('repeat-builder').addEventListener('click', async () => {
  const token = beginRunning();
  await speakBuilder(current().audio[state.question ? 'question' : 'statement'], token);
  finishRunning(token);
});
$('translation-toggle').addEventListener('click', () => {
  const shown = $('translation-toggle').getAttribute('aria-expanded') !== 'true';
  $('translation-toggle').setAttribute('aria-expanded', String(shown));
  $('translation').hidden = !shown;
});
$('speed').addEventListener('change', () => { audio.playbackRate = rate(); });
$('scene-image').addEventListener('error', () => { $('status').textContent = 'Obrázek se nepodařilo načíst.'; });
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) return;
  if (state.running && !player.paused) {
    player.togglePause();
    $('pause').textContent = '▶ Pokračovat';
  } else if (!state.running) stop();
});
window.addEventListener('pagehide', stop);

try {
  const response = await fetch('./data.json');
  if (!response.ok) throw new Error('Missing data');
  data = await response.json();
  resetDeck();
  $('app').setAttribute('aria-busy', 'false');
} catch {
  $('question').textContent = 'Věty se nepodařilo načíst.';
  $('status').textContent = 'Obnov stránku. Pro lokální náhled otevři aplikaci přes její HTTP adresu.';
}
