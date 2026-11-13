"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
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
function cameraFixture() {
  const doc = dom(), scripts = [], timers = new Map();
  let permit, deny, mediaCalls = 0, stopped = 0, timerID = 0;
  const video = doc.getElementById("quickBookVideo"); video.play = async () => {};
  doc.head = {append: script => scripts.push(script)};
  doc.createElement = () => ({remove() { this.removed = true; }});
  const context = {module: {exports: {}}, document: doc, localStorage: store(),
    navigator: {mediaDevices: {getUserMedia: constraints => {
      mediaCalls++; assert.equal(constraints.audio, false);
      return new Promise((resolve, reject) => { permit = resolve; deny = reject; });
    }}}, isSecureContext: true, crypto: {randomUUID: () => "camera_test_request"},
    addEventListener() {}, CustomEvent: class {},
    setTimeout(fn, ms) { const id = ++timerID; timers.set(id, {fn, ms}); return id; },
    clearTimeout(id) { timers.delete(id); }};
  vm.runInNewContext(fs.readFileSync("app/frontend/cockpit/book_quick_add.js", "utf8"), context);
  const ui = context.module.exports.boot(doc); ui.setAvailable(true);
  const el = id => doc.getElementById(id); el("quickBookOpen").dispatch("click");
  return {doc, scripts, timers, context, el, ui,
    get mediaCalls() { return mediaCalls; }, get stopped() { return stopped; },
    permit() { permit({getTracks: () => [{stop() { stopped++; }}]}); },
    deny(name) { deny(Object.assign(new Error("permission"), {name})); }};
}
async function cameraClickRegressions() {
  const denied = cameraFixture(), deniedStart = denied.el("quickBookScan").dispatch("click");
  assert.equal(denied.mediaCalls, 1, "a click requests camera before downloading the decoder");
  assert.equal(denied.scripts.length, 0);
  assert.equal(denied.el("quickBookScan").disabled, true);
  assert.match(denied.el("quickBookStatus").textContent, /Otevírám zadní kameru/);
  denied.deny("NotAllowedError"); await deniedStart;
  assert.match(denied.el("quickBookStatus").textContent, /nemá povolení/);
  assert.equal(denied.el("quickBookScan").disabled, false);
  assert.equal(denied.el("quickBookStop").hidden, true);

  const stalled = cameraFixture(), stalledStart = stalled.el("quickBookScan").dispatch("click");
  stalled.permit(); await tick();
  assert.equal(stalled.scripts.length, 1);
  assert.equal(stalled.el("quickBookVideo").srcObject !== null, true);
  assert.match(stalled.el("quickBookStatus").textContent, /Kamera je zapnutá/);
  const timeout = [...stalled.timers.values()].find(t => t.ms === 15000);
  assert.ok(timeout); timeout.fn(); await stalledStart;
  assert.equal(stalled.stopped, 1); assert.equal(stalled.scripts[0].removed, true);
  assert.match(stalled.el("quickBookStatus").textContent, /Čtečku se nepodařilo připravit/);
  assert.equal(stalled.timers.size, 0);

  for (const invalid of [true, false]) {
    const broken = cameraFixture(), start = broken.el("quickBookScan").dispatch("click");
    broken.permit(); await tick();
    if (!invalid) broken.context.ZXingWASM = {prepareZXingModule: async () => { throw Error("WASM unavailable"); }};
    await broken.scripts[0].onload(); await start;
    assert.equal(broken.stopped, 1);
    assert.match(broken.el("quickBookStatus").textContent, /Čtečku se nepodařilo připravit/);
    assert.equal(broken.timers.size, 0);
  }

  const closed = cameraFixture(), closedStart = closed.el("quickBookScan").dispatch("click");
  closed.permit(); await tick(); closed.el("quickBookClose").dispatch("click");
  const notice = closed.el("quickBookStatus").textContent;
  closed.context.ZXingWASM = {prepareZXingModule: async () => {}};
  await closed.scripts[0].onload(); await closedStart;
  assert.equal(closed.stopped, 1); assert.equal(closed.el("quickBookVideo").srcObject, null);
  assert.equal(closed.el("quickBookStatus").textContent, notice, "late decoder cannot reopen or update a closed scanner");
  assert.equal(closed.timers.size, 0);

  const restarted = cameraFixture(), oldStart = restarted.el("quickBookScan").dispatch("click");
  restarted.permit(); await tick(); restarted.el("quickBookStop").dispatch("click");
  const newStart = restarted.el("quickBookScan").dispatch("click");
  assert.equal(restarted.mediaCalls, 2); restarted.permit(); await tick();
  restarted.context.ZXingWASM = {prepareZXingModule: async () => {}};
  await restarted.scripts[0].onload(); await Promise.all([oldStart, newStart]);
  assert.equal(restarted.stopped, 1, "late completion from an old scan must not stop the replacement camera");
  assert.ok(restarted.el("quickBookVideo").srcObject);
  assert.match(restarted.el("quickBookStatus").textContent, /Namiř zadní kameru/);
  restarted.el("quickBookStop").dispatch("click"); assert.equal(restarted.stopped, 2);
  assert.equal(restarted.timers.size, 0);

  const markup = fs.readFileSync("app/frontend/cockpit/page.html", "utf8");
  assert.ok(markup.indexOf('id="quickBookScan"') < markup.indexOf('id="quickBookStatus"'));
  assert.ok(markup.indexOf('id="quickBookStatus"') < markup.indexOf('id="quickBookVideo"'), "camera feedback is next to the button, before the form");
}
async function run() {
  await cameraClickRegressions();
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

  const loading3 = e("quickBookLookup").dispatch("click");
  e("quickBookCategories").value = "Moje kategorie"; e("quickBookCategories").dispatch("input");
  answer({ok: true, found: true, book: {title: "Late", categories: ["román"]}}); await loading3;
  assert.equal(e("quickBookCategories").value, "Moje kategorie", "late catalog never overwrites a category edit");
  const loading4 = e("quickBookLookup").dispatch("click");
  answer({ok: true, found: true, book: {title: "Book", categories: ["české příběhy", "humoristické příběhy"]}}); await loading4;
  assert.equal(e("quickBookCategories").value, "české příběhy, humoristické příběhy");
  let savedPayload;
  global.fetch = async (_url, options) => {
    savedPayload = JSON.parse(options.body);
    return {ok: true, json: async () => ({ok: true, state: "done", item: {id: "one", book_cover_attachment_id: "catalog-cover"}})};
  };
  e("quickBookTitle").value = "Saved book"; e("quickBookSave").dispatch("click"); await tick(); await tick();
  assert.deepEqual(savedPayload.categories, ["české příběhy", "humoristické příběhy"]);
  assert.equal(savedPayload.store_cover, true);
  assert.match(e("quickBookCover").src, /^\/api\/library\/attachment\?id=one&attachment_id=catalog-cover&variant=thumb$/);
  assert.equal(e("quickBookCoverNote").textContent, "Miniatura uložená na Macu");
  assert.equal(e("quickBookSave").disabled, true, "successful write cannot be repeated as another copy");
  assert.equal(e("quickBookNext").hidden, false);
  e("quickBookNext").dispatch("click"); assert.equal(e("quickBookSave").disabled, false);
  assert.equal(e("quickBookTitle").value, "");
  assert.equal(e("quickBookCategories").value, "");
  assert.equal(e("quickBookCover").hidden, true);
  // A catalog genre outside the shared defaults remains selected in the full editor.
  const source = fs.readFileSync("app/frontend/cockpit/app.js", "utf8");
  const start = source.indexOf("    function renderLibraryBookCategoryChoices(");
  const end = source.indexOf("    function renderLibraryBookLocationOptions(", start);
  const render = new Function("document", source.slice(start, end) + ";return renderLibraryBookCategoryChoices;")(doc);
  const choices = new Element(); render(choices, ["román"], ["humoristické příběhy"]);
  assert.equal(choices.children.find(x => x.children[0].value === "humoristické příběhy").children[0].checked, true);
  ui.setAvailable(false); assert.equal(e("quickBookPanel").hidden, true); assert.equal(e("quickBookOpen").hidden, true);
  global.fetch = originalFetch;
  console.log("Quick book frontend: ISBN, durable writes/reload, double click, unavailable storage, camera cancellation, stale lookup and explicit next: OK");
}
run().catch(error => { console.error(error); process.exitCode = 1; });
