// Execute the actual UI module against a minimal DOM/audio test double.
// These are interaction tests; they do not certify browser rendering or sound.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

class Element {
  constructor(tag = 'div') {
    this.tag = tag; this.attributes = {}; this.dataset = {}; this.children = [];
    this.listeners = {}; this.hidden = false; this.checked = false; this.disabled = false;
    this.value = ''; this.textContent = ''; this.offsetWidth = 400;
    this.classes = new Set(); this.style = { setProperty() {} };
    this.classList = {
      add: (...names) => names.forEach(n => this.classes.add(n)),
      remove: (...names) => names.forEach(n => this.classes.delete(n)),
      contains: name => this.classes.has(name),
    };
  }
  set className(value) { this.classes = new Set(value.split(' ')); }
  get className() { return [...this.classes].join(' '); }
  setAttribute(key, value) { this.attributes[key] = String(value); }
  getAttribute(key) { return this.attributes[key] ?? null; }
  removeAttribute(key) { delete this.attributes[key]; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  async dispatch(type) { return Promise.all((this.listeners[type] || []).map(fn => fn({ target: this }))); }
  replaceChildren(...children) { this.children = children; }
  append(child) { this.children.push(child); }
  remove() {}
  querySelectorAll(selector) { return this.children.filter(child => child.classList.contains(selector.slice(1))); }
  getBoundingClientRect() { return { left: 0, top: 0, width: 100, height: 60 }; }
  animate() { return { finished: Promise.resolve(), cancel() {}, pause() {}, play() {} }; }
}
const html = await readFile(new URL('../web/index.html', import.meta.url), 'utf8');
const nodes = new Map();
for (const match of html.matchAll(/<([a-z0-9]+)\b([^>]*\bid="([^"]+)"[^>]*)>/g)) {
  const node = new Element(match[1]);
  for (const attr of match[2].matchAll(/([\w-]+)="([^"]*)"/g)) node.setAttribute(attr[1], attr[2]);
  node.hidden = /\bhidden\b/.test(match[2]); node.disabled = /\bdisabled\b/.test(match[2]);
  nodes.set(match[3], node);
}
const modes = ['sentences', 'builder'].map(mode => { const el = new Element('button'); el.dataset.mode = mode; return el; });
const lessons = ['be', 'have', 'go'].map(lesson => { const el = new Element('button'); el.dataset.lesson = lesson; return el; });
globalThis.document = {
  getElementById: id => nodes.get(id), createElement: tag => new Element(tag),
  querySelectorAll: selector => selector === '[data-mode]' ? modes : lessons,
  addEventListener() {}, hidden: false,
};
globalThis.window = { addEventListener() {} };
globalThis.matchMedia = () => ({ matches: true });
const audioInstances = [];
globalThis.Audio = class {
  constructor() { this.volume = 1; this.currentTime = 0; audioInstances.push(this); }
  pause() {}
  play() { const end = this.onended; if (end) setTimeout(end, 5); return Promise.resolve(); }
};
const data = JSON.parse(await readFile(new URL('../web/data.json', import.meta.url)));
globalThis.fetch = async () => ({ ok: true, json: async () => data });
nodes.get('speed').value = '1';
await import('../web/app.mjs');
const $ = id => nodes.get(id);
const stage = () => $('word-stage').children.filter(n => n.classList.contains('word')).map(n => n.textContent).join(' ').replace(/ ([.?])$/, '$1');

test('UI loads the first sentence and reveals both exact answers with MP3', async () => {
  assert.equal($('app').getAttribute('aria-busy'), 'false');
  assert.equal($('question').textContent, 'Is he happy?');
  assert.equal($('progress').textContent, '1 / 91');
  await $('positive').dispatch('click');
  assert.equal($('positive-text').textContent, 'Yes, he is.');
  assert.equal($('positive').getAttribute('aria-expanded'), 'true');
  assert.match(audioInstances[0].src, /\.mp3$/);
  await $('negative').dispatch('click');
  assert.equal($('negative-text').textContent, "No, he isn't.");
});

test('next hides answers; lesson and sentence selection update data and contextual image', async () => {
  await $('next').dispatch('click');
  assert.equal($('question').textContent, 'Am I eight years old?');
  assert.equal($('positive').getAttribute('aria-expanded'), 'false');
  assert.equal($('age-badge').textContent, 'eight years old');
  await lessons[1].dispatch('click');
  assert.equal($('question').textContent, 'Do I have a dog?');
  assert.match($('scene-image').src, /black-dog\.webp$/);
  $('jump').value = 'have-003'; await $('jump').dispatch('change');
  assert.equal($('question').textContent, 'Does he have a bike?');
  await $('begin').dispatch('click'); assert.equal($('progress').textContent, '1 / 8');
});

test('builder makes an actual does/has question and hides the statement translation', async () => {
  await modes[1].dispatch('click');
  assert.equal($('sentence-view').hidden, true); assert.equal(stage(), 'I have a dog.');
  $('jump').value = 'verb-011'; await $('jump').dispatch('change');
  assert.equal(stage(), 'He has two sisters.');
  await $('translation-toggle').dispatch('click'); assert.equal($('translation').hidden, false);
  await $('make-question').dispatch('click');
  assert.equal(stage(), 'Does he have two sisters?');
  assert.equal($('translation').hidden, true); assert.equal($('translation-toggle').disabled, true);
  assert.match($('transform-note').textContent, /has → have/);
  const row = data.verbs.find(r => r.id === 'verb-011');
  assert.equal(audioInstances[0].src, data.audio[row.audio.question].src);
  await $('repeat-builder').dispatch('click');
  assert.equal(audioInstances[0].src, data.audio[row.audio.question].src);
});

test('builder swaps be in front of the subject and retains the English capital I', async () => {
  await lessons[0].dispatch('click');
  await $('make-question').dispatch('click');
  assert.equal(stage(), 'Am I old?');
  assert.match($('transform-note').textContent, /Am stojí první/);
});

test('switching lesson during an animated sequence cancels all stale UI updates', async () => {
  const old = $('build-play').dispatch('click');
  await new Promise(resolve => setTimeout(resolve, 40));
  await lessons[2].dispatch('click');
  await old;
  assert.equal(stage(), 'I go home.');
  assert.equal($('pause').disabled, true);
  assert.equal($('translation-toggle').disabled, false);
  await modes[0].dispatch('click');
  assert.equal($('question').textContent, 'Do I go to school?');
});
