const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function target() {
  const listeners = new Map(), styles = new Map(), classes = new Set();
  return {
    children: [], scrollTop: 177,
    style: {getPropertyValue: key => styles.get(key) || "", setProperty: (key, value) => styles.set(key, value), removeProperty: key => styles.delete(key)},
    classList: {add: key => classes.add(key), remove: key => classes.delete(key), contains: key => classes.has(key)},
    addEventListener(name, callback) { if (!listeners.has(name)) listeners.set(name, new Set()); listeners.get(name).add(callback); },
    removeEventListener(name, callback) { listeners.get(name)?.delete(callback); },
    emit(name) { for (const callback of listeners.get(name) || []) callback(); },
    count(name) { return listeners.get(name)?.size || 0; },
    replaceChildren() { this.children = []; }, removeAttribute() {}, pause() {}, load() {},
  };
}

function fixture({observer = true, animationFrame = true} = {}) {
  const keys = ["status", "shots", "voices", "jobs", "save", "preview", "final", "range", "from", "to", "duck", "player", "reload", "source", "sourcePlayer", "sourceStatus", "sourceTitle", "selection", "start", "end", "playSelection", "texts", "cards", "shotNav", "navigator", "shotTitle", "overview", "visual", "visualImage", "videoPlaceholder", "openSource", "watch", "watchReason", "outputs"];
  const nodes = Object.fromEntries(keys.map(key => [key, target()]));
  const host = target(), header = target(), body = target(), root = target(), doc = target(), win = target(), viewport = target();
  const geometry = {hostTop: 20, hostBottom: 880, headerBottom: 140, navTop: 280};
  host.getBoundingClientRect = () => ({top: geometry.hostTop, bottom: geometry.hostBottom, height: geometry.hostBottom - geometry.hostTop});
  header.getBoundingClientRect = () => ({bottom: geometry.headerBottom});
  nodes.navigator.getBoundingClientRect = () => ({top: geometry.navTop});
  root.closest = () => host;
  root.querySelector = selector => nodes[selector.match(/"(.*?)"/)[1]];
  host.querySelector = selector => selector === ".modal-header" ? header : body;
  doc.hidden = false; doc.createElement = target; doc.defaultView = win;
  win.innerWidth = 1440; win.innerHeight = 900;
  viewport.height = 900; viewport.offsetTop = 0; win.visualViewport = viewport;
  let serial = 0; const frames = new Map(), observers = [], requests = [];
  if (animationFrame) {
    win.requestAnimationFrame = callback => { const id = ++serial; frames.set(id, callback); return id; };
    win.cancelAnimationFrame = id => frames.delete(id);
  }
  if (observer) win.ResizeObserver = class {
    constructor(callback) { this.callback = callback; this.targets = []; this.disconnected = false; observers.push(this); }
    observe(element) { this.targets.push(element); }
    disconnect() { this.disconnected = true; }
  };
  const context = {window: {}}; vm.createContext(context);
  vm.runInContext(fs.readFileSync("app/frontend/cockpit/film_editor.js", "utf8"), context);
  const editor = context.window.SamanthaFilmEditor.create(root, {document: doc,
    fetch(url) { requests.push(url); return new Promise(() => {}); }, setTimeout() { return 1; }, clearTimeout() {}});
  return {editor, nodes, host, header, body, doc, win, viewport, geometry, observers, requests, frames,
    flush() { const pending = [...frames.values()]; frames.clear(); for (const callback of pending) callback(); },
    height() { return nodes.navigator.style.getPropertyValue("--film-nav-height"); },
    top() { return nodes.navigator.style.getPropertyValue("--film-nav-top"); }};
}

const f = fixture();
f.editor.open(); f.flush();
assert.equal(f.height(), "588px", "initial list reaches the bottom of the visible dialog");
assert.equal(f.top(), "130px", "sticky position accounts for the actual toolbar");
assert.deepEqual(f.observers[0].targets, [f.host, f.header, f.body]);
const rows = f.nodes.shotNav.children;

f.geometry.navTop = 150;
for (let i = 0; i < 30; ++i) f.host.emit("scroll");
assert.equal(f.frames.size, 1, "scroll events share one layout frame");
f.flush();
assert.equal(f.height(), "718px", "list grows to fill all available space after scrolling");
assert.equal(f.nodes.shotNav.scrollTop, 177, "sizing does not reset the user's place");
assert.equal(f.nodes.shotNav.children, rows, "sizing does not rebuild or reload thumbnails");
assert.equal(f.requests.length, 1, "layout changes never create extra requests or saves");

f.geometry.headerBottom = 220; f.geometry.navTop = 230;
f.observers[0].callback(); f.flush();
assert.equal(f.top(), "210px"); assert.equal(f.height(), "638px", "feedback wrapping leaves the whole list below the header");
f.win.innerHeight = 700; f.viewport.height = 700; f.geometry.hostBottom = 680;
f.win.emit("resize"); f.flush();
assert.equal(f.height(), "438px", "window resizing preserves the visible lower boundary");

f.win.innerWidth = 600; f.win.emit("resize"); f.flush();
assert.equal(f.height(), ""); assert.equal(f.top(), "", "mobile returns to its compact stacked layout");
f.win.innerWidth = 1440; f.win.innerHeight = 900; f.geometry.hostBottom = 880;
f.viewport.height = 550; f.viewport.offsetTop = 20; f.viewport.emit("resize"); f.flush();
assert.equal(f.height(), "328px", "visual viewport changes cannot hide the bottom of the list");

f.doc.hidden = true; f.doc.emit("visibilitychange");
assert(f.observers[0].disconnected); assert.equal(f.host.count("scroll"), 0); assert.equal(f.win.count("resize"), 0);
assert.equal(f.height(), "");
f.doc.hidden = false; f.doc.emit("visibilitychange"); f.flush();
assert.equal(f.host.count("scroll"), 1, "return attaches exactly one scroll listener");
f.host.emit("scroll"); assert.equal(f.frames.size, 1);
f.editor.close(); assert.equal(f.frames.size, 0); assert.equal(f.host.count("scroll"), 0);
f.observers.at(-1).callback(); assert.equal(f.frames.size, 0, "stale layout notifications do nothing after close");
f.editor.open(); f.flush(); assert.equal(f.host.count("scroll"), 1);
f.editor.suspend(); assert.equal(f.host.count("scroll"), 0); assert.equal(f.height(), "");
assert(f.requests.every(url => url.startsWith("/api/camino/film/editor")), "no playback, render, narration or write is triggered");

const fallback = fixture({observer: false, animationFrame: false});
fallback.editor.open(); assert.equal(fallback.height(), "588px");
fallback.geometry.headerBottom = 100; fallback.geometry.navTop = 110; fallback.host.emit("scroll");
assert.equal(fallback.height(), "758px", "resize/scroll fallback works without ResizeObserver or RAF");
fallback.geometry.headerBottom = 1000; fallback.host.emit("scroll");
assert.equal(fallback.height(), "0px", "a very tall toolbar never produces a negative height");
fallback.editor.close();
console.log("Camino navigation viewport, scroll and lifecycle: PASS");
