const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
function node() {
  const classes = new Set(), events = {};
  return {dataset: {}, textContent: "", attrs: {},
    classList: {add: k => classes.add(k), contains: k => classes.has(k), toggle(k, on) { if (on) classes.add(k); else classes.delete(k); }},
    setAttribute(k, v) { this.attrs[k] = v; },
    addEventListener(k, fn) { events[k] = fn; }, emit(k) { events[k]?.(); }};
}
const message = node(), label = node(), dismiss = node(), root = node();
let visibility, focusReturned = false;
const doc = {hidden: false, addEventListener(event, fn) { assert.equal(event, "visibilitychange"); visibility = fn; }};
root.ownerDocument = doc;
root.querySelector = selector => selector === "button" ? dismiss : selector.includes("label") ? label : message;
root.closest = () => ({querySelector: () => ({focus: () => { focusReturned = true; }})});
const context = {window: {}}; vm.createContext(context);
vm.runInContext(fs.readFileSync("app/frontend/cockpit/film_feedback.js", "utf8"), context);
const feedback = context.window.SamanthaFilmFeedback.create(root);
feedback.report({message: "Fotografie 12: nejprve prodluž obraz.", kind: "warning", channel: "photo"});
assert.equal(root.classList.contains("hidden"), false);
assert.equal(label.textContent, "Vyžaduje zásah");
feedback.report({message: "Uloženo.", kind: "success", channel: "save"});
assert(message.textContent.includes("Fotografie 12"), "autosave cannot replace a photo prerequisite");
feedback.report({message: "Spojení se ztratilo.", kind: "error", channel: "save"});
feedback.report({message: "Uložená revize 3.", channel: "save"});
assert.equal(message.textContent, "Spojení se ztratilo.", "routine status cannot erase an error");
assert.equal(message.attrs.role, "alert");
feedback.report({message: "Uloženo po opakování.", kind: "success", channel: "save"});
assert(message.textContent.includes("Fotografie 12"), "confirmed save resolves its own error only");
dismiss.emit("click"); assert.equal(message.textContent, "Uloženo po opakování.");
feedback.report({message: "Náhled 720p: Vytváří se · 42 %", kind: "busy", channel: "render"});
assert.equal(dismiss.disabled, true);
dismiss.emit("click"); assert(message.textContent.includes("42 %"));
doc.hidden = true; visibility();
assert.equal(root.classList.contains("hidden"), true); assert.equal(message.textContent, "");
doc.hidden = false; visibility(); assert(message.textContent.includes("42 %"));
feedback.report({message: "Náhled je hotový.", kind: "success", channel: "render"});
assert.equal(dismiss.disabled, false);
dismiss.emit("click"); dismiss.emit("click");
assert(root.classList.contains("hidden")); assert(focusReturned);
feedback.clear(); assert(root.classList.contains("hidden"));
console.log("Camino visible feedback priorities, privacy and recovery: PASS");
