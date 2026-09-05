const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(path.resolve(__dirname, "../../docs/vocabulary-en/app.js"), "utf8");
const vocabulary = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../../docs/data/vocabulary-en.json"), "utf8"));

function element(dataset = {}) {
  return {
    dataset, textContent: "", classList: { toggle() {}, add() {} }, listeners: {},
    addEventListener(name, handler) { this.listeners[name] = handler; },
    removeAttribute() {}, append() {},
    click() { this.listeners.click(); },
  };
}

function app(items, random = () => 0) {
  const elements = new Map();
  const directions = ["czToEn", "enToCz"].map((direction) => element({ direction }));
  const filters = ["all", "selected", "hard"].map((filter) => element({ filter }));
  const context = vm.createContext({
    document: {
      querySelector() { return null; },
      querySelectorAll(selector) { return selector === "[data-filter]" ? filters : directions; },
      getElementById(id) {
        if (!elements.has(id)) elements.set(id, element());
        return elements.get(id);
      },
      createElement: () => element(),
    },
    fetch: () => new Promise(() => {}),
    Math: Object.assign(Object.create(Math), { random }),
    URL, window: { location: { href: "http://localhost/vocabulary-en/" } },
  });
  vm.runInContext(source + "\nglobalThis.api = { state, chooseNextItem };", context);
  context.api.state.items = items;
  return { ...context.api, elements, directions, filters };
}

const sample = Array.from({ length: 4 }, (_, index) => ({
  id: index + 1, en: `word${index}`, cz: `slovo${index}`, selected: index < 2,
}));

test("switching translation direction preserves progress and the current card", () => {
  const view = app(sample);
  view.chooseNextItem();
  const first = view.state.currentItem.id;
  view.directions[1].click();
  assert.equal(view.state.currentItem.id, first);
  view.elements.get("newWordButton").click();
  assert.notEqual(view.state.currentItem.id, first);
  assert.equal(view.state.shownIds.size, 2);
});

test("every card is shown once before a round ends, including with direction changes", () => {
  let seed = 17;
  const random = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
  const view = app(vocabulary.items, random);
  for (let round = 0; round < 3; round++) {
    const seen = new Set();
    for (let index = 0; index < vocabulary.items.length; index++) {
      view.directions[index % 2].click();
      view.chooseNextItem();
      assert.ok(!seen.has(view.state.currentItem.id), `Repeated card ${view.state.currentItem.id}`);
      seen.add(view.state.currentItem.id);
      assert.equal(view.elements.get("remainingCount").textContent, String(vocabulary.items.length - index - 1));
    }
    assert.equal(seen.size, vocabulary.items.length);
    assert.match(view.elements.get("messageStrip").textContent, /Sada je hotov/);
  }
});

test("a new round does not immediately repeat the previous card", () => {
  let random = 0;
  const view = app(sample, () => random);
  sample.forEach(() => view.chooseNextItem());
  const last = view.state.currentItem.id;
  random = 0.999;
  view.chooseNextItem();
  assert.notEqual(view.state.currentItem.id, last);
  assert.equal(view.state.shownIds.size, 1);
});

test("empty and one-card selections work and an actual filter change starts a new selection", () => {
  const empty = app([]);
  empty.chooseNextItem();
  assert.equal(empty.state.currentItem, null);
  assert.equal(empty.elements.get("remainingCount").textContent, "0");
  const single = app(sample.slice(0, 1));
  single.chooseNextItem();
  single.chooseNextItem();
  assert.equal(single.state.currentItem.id, 1);
  assert.equal(single.elements.get("remainingCount").textContent, "0");
  const filtered = app(sample);
  filtered.chooseNextItem();
  filtered.filters[1].click();
  assert.equal(filtered.elements.get("totalCount").textContent, "2");
  assert.equal(filtered.state.shownIds.size, 1);
  filtered.chooseNextItem();
  assert.equal(filtered.state.shownIds.size, 2);
});
