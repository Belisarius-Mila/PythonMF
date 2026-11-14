"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const {coverSources} = require("../app/frontend/cockpit/book_quick_add.js");
const fallback = "https://covers.openlibrary.org/b/isbn/9788024932460-S.jpg?default=false";

class Element {
  constructor(tag = "img") {
    Object.assign(this, {tagName: tag.toUpperCase(), children: [], dataset: {}, handlers: {}, hidden: false});
    const change = (name, on) => {
      const names = new Set((this.className || "").split(" ").filter(Boolean));
      if (on) names.add(name); else names.delete(name); this.className = [...names].join(" ");
    };
    this.classList = {add: name => change(name, true), toggle: change};
  }
  setAttribute(key, value) { this[key] = value; }
  removeAttribute(key) { delete this[key]; }
  appendChild(child) { this.children.push(child); child.parentNode = this; return child; }
  addEventListener(name, fn) { this.handlers[name] = fn; }
  click() { if (this.handlers.click) this.handlers.click(); }
  remove() { this.removed = true; }
}
function fixture() {
  const timers = new Map(); let sequence = 0;
  const context = {module: {exports: {}}, setTimeout(fn, ms) { const id = ++sequence; timers.set(id, {fn, ms}); return id; }, clearTimeout(id) { timers.delete(id); }};
  vm.runInNewContext(fs.readFileSync("app/frontend/cockpit/book_quick_add.js", "utf8"), context);
  return {api: context.module.exports, timers, image: new Element(), link: new Element("a"), note: new Element("small")};
}
function load(image, width = 170, height = 240) {
  image.naturalWidth = width; image.naturalHeight = height; image.onload();
}

const sources = coverSources(fallback), parsed = new URL(sources[0].url);
assert.equal(parsed.origin, "https://cache3.obalkyknih.cz");
assert.deepEqual(JSON.parse(parsed.searchParams.get("multi")), {isbn: "9788024932460"});
assert.equal(parsed.searchParams.get("keywords"), "9788024932460");
assert.equal(sources[0].backlink, "https://www.obalkyknih.cz/view?isbn=9788024932460");
assert.equal(sources[1].url, fallback);
for (const bad of ["", "https://evil.example/cover", fallback.replace("https:", "http:"), fallback + "&redirect=evil", fallback.replace("2460", "2461")]) {
  assert.deepEqual(coverSources(bad), []);
}

// The registered origin is sent only to Obálkyknih; the visible image always has its source link.
{
  const {api, image, link, note, timers} = fixture(); api.bindCover(image, fallback, {link, note});
  assert.equal(image.referrerPolicy, "origin"); assert.equal(image.hidden, true); assert.equal(link.hidden, true);
  load(image); assert.equal(image.hidden, false); assert.equal(link.hidden, false);
  assert.equal(link.href, sources[0].backlink); assert.equal(link.rel, "noopener noreferrer");
  assert.match(note.textContent, /Obálkyknih/); assert.equal(timers.size, 0);
}
// Both a provider error and its documented empty 1×1 image fall back without blocking the book.
for (const failure of ["error", "empty"]) {
  const {api, image, link, note, timers} = fixture(); api.bindCover(image, fallback, {link, note});
  if (failure === "error") image.onerror(); else load(image, 1, 1);
  assert.equal(image.src, fallback); assert.equal(image.referrerPolicy, "no-referrer");
  load(image, 40, 60); assert.match(note.textContent, /Open Library/); assert.match(link.href, /^https:\/\/openlibrary.org\/isbn\//);
  assert.equal(timers.size, 0);
}
// Slow previews advance once; exhausted images remove their obsolete link and credit.
{
  const {api, image, link, note, timers} = fixture(); api.bindCover(image, fallback, {link, note});
  const lateLoad = image.onload;
  [...timers.values()][0].fn(); assert.equal(image.src, fallback);
  lateLoad(); assert.equal(image.hidden, true); assert.equal(image.src, fallback);
  image.onerror(); lateLoad(); assert.equal(image.hidden, true); assert.equal(link.hidden, true);
  assert.equal(link.href, undefined); assert.equal(note.textContent, "Bez obálky"); assert.equal(timers.size, 0);
}
// Changing ISBN cancels the old timeout and callbacks, including after switching to a local photo.
{
  const {api, image, link, note, timers} = fixture(); api.bindCover(image, fallback, {link, note});
  const lateError = image.onerror, lateLoad = image.onload;
  api.bindCover(image, "", {link, note}); image.src = "/api/library/attachment?id=book&attachment_id=photo";
  lateError(); lateLoad(); assert.match(image.src, /^\/api\/library\/attachment/); assert.equal(timers.size, 0);
}
// A required backlink cannot be accidentally omitted; lazy list covers do not expire off screen.
{
  const {api, image, link, timers} = fixture();
  api.bindCover(image, fallback, {timeoutMs: 0}); assert.equal(image.src, fallback); assert.equal(timers.size, 0);
  image.loading = "lazy";
  api.bindCover(image, fallback, {link, timeoutMs: 0}); assert.equal(image.src, sources[0].url); assert.equal(timers.size, 0);
  assert.equal(image.hidden, false); assert.equal(link.hidden, false); assert.equal(link.href, undefined);
  load(image); assert.equal(link.href, sources[0].backlink);
}

// Real list renderer keeps the external source link outside the button that opens our own book.
{
  const doc = {createElement: tag => new Element(tag)}, bindings = [], opened = [];
  const code = fs.readFileSync("app/frontend/cockpit/app.js", "utf8");
  const start = code.indexOf("    function createLibraryItemRow("), end = code.indexOf("    function renderLibraryItems(", start);
  const render = new Function("document", "window", "currentLibrarySelectedId", "libraryItemMeta", "libraryAttachmentUrl", "loadLibraryItem",
    code.slice(start, end) + ";return createLibraryItemRow;")(doc, {SamanthaBookQuick: {safeCover: value => value === fallback, bindCover: (...args) => bindings.push(args)}},
    "", () => "Author", (id, attachment) => "/api/library/attachment?id=" + id + "&attachment_id=" + attachment, id => opened.push(id));
  const item = {id: "book", category: "books", title: "Book", book_cover_url: fallback, attachment_roles: []};
  const row = render(item); assert.equal(row.tagName, "DIV"); assert.equal(row.children[0].tagName, "A");
  assert.equal(row.children[1].tagName, "BUTTON"); assert.equal(bindings[0][2].timeoutMs, 0);
  row.children[0].click(); assert.equal(opened.length, 0); row.children[1].click(); assert.deepEqual(opened, ["book"]);
  const local = render({...item, book_cover_attachment_id: "local"});
  assert.equal(local.tagName, "BUTTON"); assert.match(local.children[0].src, /attachment_id=local/); assert.equal(bindings.length, 1);
  const ownPhoto = render({...item, attachment_roles: ["book_cover"]});
  assert.equal(ownPhoto.children[0].tagName, "DIV"); assert.equal(bindings.length, 1);
}
console.log("Book covers: registered-origin referrer, backlink, error/empty/timeout fallback, stale callbacks, lazy rows and local-photo priority: OK");
