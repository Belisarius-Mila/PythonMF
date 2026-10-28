const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

function target() {
  const listeners = new Map(), classes = new Set();
  return {
    classList: {contains: name => classes.has(name), toggle(name, value) { value ? classes.add(name) : classes.delete(name); }},
    addEventListener(name, fn) { listeners.set(name, fn); },
    emit(name, event = {}) { listeners.get(name)?.(event); },
    setAttribute(name, value) { this[name] = value; },
  };
}
function fixture(mode = "native") {
  const modal = target(), button = target(), doc = target();
  const state = {requests: 0, exits: 0, layouts: 0};
  modal.ownerDocument = doc; modal.querySelector = () => button;
  modal.contains = node => node === button;
  modal.scrollTop = 231;
  if (mode !== "missing") modal.requestFullscreen = () => {
    state.requests++;
    if (mode === "reject") return Promise.reject(new Error("denied"));
    if (mode === "throw") throw new Error("unavailable");
    return new Promise(resolve => { state.enter = () => {
      doc.fullscreenElement = modal; doc.emit("fullscreenchange"); resolve();
    }; });
  };
  doc.exitFullscreen = () => {
    state.exits++; doc.fullscreenElement = null; doc.emit("fullscreenchange"); return Promise.resolve();
  };
  const context = {window: {}, Promise}; vm.createContext(context);
  vm.runInContext(fs.readFileSync("app/frontend/cockpit/film_editor.js", "utf8"), context);
  const control = context.window.SamanthaFilmEditor.createWindow(modal, {onResize: () => state.layouts++});
  return {modal, button, doc, state, control, expanded: () => modal.classList.contains("is-expanded")};
}
const flush = async () => { for (let i = 0; i < 6; i++) await Promise.resolve(); };
(async () => {
  const f = fixture();
  f.button.emit("click"); assert.equal(f.expanded(), true); assert.equal(f.button["aria-pressed"], "true");
  f.state.enter(); await flush();
  assert.equal(f.doc.fullscreenElement, f.modal);
  f.button.emit("click"); await flush();
  assert.equal(f.expanded(), false); assert.equal(f.state.exits, 1); assert.equal(f.button.textContent, "Celá obrazovka");
  assert.equal(f.modal.scrollTop, 231, "presentation does not replace or reset the editor");
  assert.equal(f.state.layouts, 2, "both size changes remeasure thumbnail navigation");
  f.button.emit("click"); f.state.enter(); await flush();
  f.doc.fullscreenElement = null; f.doc.emit("fullscreenchange");
  assert.equal(f.expanded(), false, "browser Escape synchronizes button and layout");
  for (const mode of ["missing", "reject", "throw"]) {
    const x = fixture(mode); x.button.emit("click"); await flush();
    assert.equal(x.expanded(), true, mode + " keeps a usable full-window fallback");
    let prevented = false, stopped = false;
    x.modal.emit("keydown", {key: "Escape", preventDefault() { prevented = true; }, stopPropagation() { stopped = true; }});
    assert.equal(x.expanded(), false); assert.equal(prevented && stopped, true, "first Escape shrinks without closing the film");
  }
  const late = fixture(); late.button.emit("click"); late.control.reset();
  late.modal.classList.toggle("hidden", true); late.state.enter(); await flush();
  assert.equal(late.doc.fullscreenElement, null, "late fullscreen entry cannot revive a closed editor");
  assert.equal(late.expanded(), false);
  const race = fixture(); race.button.emit("click"); race.control.reset(); race.button.emit("click");
  assert.equal(race.state.requests, 1, "an outstanding request is never retried");
  race.state.enter(); await flush();
  assert.equal(race.doc.fullscreenElement, null); assert.equal(race.expanded(), true, "new opening retains its viewport fallback");
  race.control.reset();
  console.log("Camino window: native, fallback, Escape, close and delayed entry PASS");
})().catch(error => { console.error(error); process.exitCode = 1; });
