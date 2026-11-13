"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const {normalizeISBN, safeCover, PendingWrite, Camera, boot} = require("../app/frontend/cockpit/book_quick_add.js");
const tick = () => new Promise(resolve => setImmediate(resolve));
function store() { const values = new Map(); return {getItem: k => values.get(k) || null, setItem: (k, v) => values.set(k, v), removeItem: k => values.delete(k)}; }
class Element {
  constructor() { this.value = ""; this.hidden = false; this.disabled = false; this.dataset = {}; this.handlers = {}; this.children = []; this.checked = false; this.files = []; this.textContent = ""; }
  addEventListener(k, fn) { this.handlers[k] = fn; }
  dispatch(k, event = {}) { return this.handlers[k] && this.handlers[k]({target: this, ...event}); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = children; }
  removeAttribute(k) { delete this[k]; }
  setAttribute(k, v) { this[k] = v; }
  focus() { this.focused = true; }
  querySelectorAll() { return this.children.flatMap(x => x.children || []).filter(x => x.type === "checkbox" && x.checked); }
}
function dom() {
  const markup = fs.readFileSync("app/frontend/cockpit/page.html", "utf8");
  const elements = new Map([...markup.matchAll(/id="(quickBook[^" ]+)"/g)].map(m => [m[1], new Element()]));
  const handlers = {};
  return {elements, getElementById: id => elements.get(id), createElement: () => new Element(),
    addEventListener: (k, fn) => { handlers[k] = fn; }, dispatchEvent: () => {}, handlers};
}
async function run() {
  assert.equal(normalizeISBN("ISBN 0-385-47257-9"), "9780385472579");
  assert.equal(normalizeISBN("ISBN-13: 978-0-385-47257-9"), "9780385472579");
  for (const input of ["4006381333931", "9780385472570", "123", ""]) assert.throws(() => normalizeISBN(input));
  assert.equal(safeCover("https://evil.example/b/isbn/9780385472579-S.jpg?default=false"), false);
  assert.equal(safeCover("https://covers.openlibrary.org/b/isbn/9780385472579-S.jpg?default=false"), true);

  const storage = store(); let sends = 0, sent, reads = 0;
  const ledger = new PendingWrite(storage, async (kind, payload) => { sends++; sent = payload; throw Error("lost response"); }, async () => { reads++; return {ok: true, state: "done"}; }, () => "test_request_12345");
  await assert.rejects(() => ledger.save("create", {title: "A"}));
  assert.equal(sends, 1); assert.equal(ledger.pending().payload.request_id, "test_request_12345");
  const reloaded = new PendingWrite(storage, () => { throw Error("recovery must not send"); }, ledger.read, () => { throw Error("must preserve identity"); });
  await reloaded.recover(); assert.equal(reads, 1); assert.equal(reloaded.pending(), null); assert.equal(sends, 1);

  let release;
  const double = new PendingWrite(store(), async (_, p) => { sends++; return new Promise(r => { release = r; }); }, async () => ({}), () => "double_request_12345");
  const first = double.save("create", {title: "A"}); const second = await double.save("create", {title: "B"});
  assert.equal(second.state, "busy"); release({ok: true, state: "done"}); await first;
  assert.equal(sends, 2);

  const pendingStorage = store(); let replayed;
  const uncertain = new PendingWrite(pendingStorage, async (_, p) => { replayed = p; throw Error(); }, async () => ({ok: true, state: "not_found"}), () => "same_request_123456");
  await assert.rejects(() => uncertain.save("create", {title: "Original"}));
  await uncertain.recover(); assert.equal(uncertain.pending().payload.title, "Original");
  await assert.rejects(() => uncertain.save("create", {title: "Different"}));
  assert.equal(replayed.title, "Original"); assert.equal(replayed.request_id, "same_request_123456");
  const failedStorage = {getItem: () => null, setItem: () => { throw Error("quota"); }};
  const blocked = new PendingWrite(failedStorage, () => { throw Error("network must not run"); }, () => {}, () => "no_storage_request");
  await assert.rejects(() => blocked.save("create", {}), /quota/);

  let permission, stopped = 0, played = 0;
  const cam = new Camera({getUserMedia: () => new Promise(r => { permission = r; })}, {play: async () => { played++; }}, async () => "", () => { throw Error("closed camera found a book"); }, () => {});
  const opening = cam.start(); cam.stop(); permission({getTracks: () => [{stop: () => stopped++}]}); await opening;
  assert.equal(stopped, 1); assert.equal(played, 0);
  let decode, found = 0;
  const active = new Camera({getUserMedia: async () => ({getTracks: () => [{stop: () => stopped++}]})}, {play: async () => {}}, () => new Promise(r => { decode = r; }), () => found++, () => {});
  await active.start(); active.stop(); decode("9780385472579"); await tick(); assert.equal(found, 0);

  global.localStorage = store();
  global.CustomEvent = class { constructor(type, options) { this.type = type; this.detail = options && options.detail; } };
  Object.defineProperty(global, "navigator", {configurable: true, value: {mediaDevices: {}}});
  global.addEventListener = () => {};
  const originalFetch = global.fetch;
  let answer;
  global.fetch = async () => new Promise(resolve => { answer = data => resolve({ok: true, json: async () => data}); });
  const doc = dom(); const ui = boot(doc); ui.setAvailable(true);
  const e = id => doc.getElementById(id);
  e("quickBookOpen").dispatch("click");
  e("quickBookISBN").value = "0385472579";
  const loading = e("quickBookLookup").dispatch("click");
  e("quickBookTitle").value = "My correction"; e("quickBookTitle").dispatch("input");
  answer({ok: true, found: true, book: {title: "Late catalog", author: "Author"}}); await loading;
  assert.equal(e("quickBookTitle").value, "My correction");
  const loading2 = e("quickBookLookup").dispatch("click");
  e("quickBookISBN").value = "9788025229033"; e("quickBookISBN").dispatch("input");
  answer({ok: true, found: true, book: {title: "Old ISBN"}}); await loading2;
  assert.equal(e("quickBookTitle").value, "");

  global.fetch = async () => ({ok: true, json: async () => ({ok: true, state: "done", item: {id: "one"}})});
  e("quickBookTitle").value = "Saved book"; e("quickBookSave").dispatch("click"); await tick(); await tick();
  assert.equal(e("quickBookSave").disabled, true, "successful write cannot be repeated as another copy");
  assert.equal(e("quickBookNext").hidden, false);
  e("quickBookNext").dispatch("click"); assert.equal(e("quickBookSave").disabled, false);
  assert.equal(e("quickBookTitle").value, "");
  ui.setAvailable(false); assert.equal(e("quickBookPanel").hidden, true); assert.equal(e("quickBookOpen").hidden, true);
  global.fetch = originalFetch;
  console.log("Quick book frontend: ISBN, durable writes/reload, double click, unavailable storage, camera cancellation, stale lookup and explicit next: OK");
}
run().catch(error => { console.error(error); process.exitCode = 1; });
