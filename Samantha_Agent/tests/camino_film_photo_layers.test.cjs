const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
function node(tag = "div") {
  const events = {}, classes = new Set(); let value = null;
  return {tag, children: [], textContent: "", readyState: 0, currentTime: 0, paused: true,
    get value() { return value ?? (tag === "select" ? this.children[0]?.value || "" : ""); },
    set value(v) { value = v; },
    classList: {add: x => classes.add(x), remove: x => classes.delete(x), contains: x => classes.has(x)},
    addEventListener(k, fn) { events[k] = fn; }, emit(k) { return events[k]?.(); },
    appendChild(n) { this.children.push(n); return n; }, replaceChildren() { this.children = []; },
    pause() { this.paused = true; }, load() {}, play() { this.paused = false; return Promise.resolve(); },
    removeAttribute(k) { delete this[k]; }, getAttribute(k) { return this[k] || null; }, scrollIntoView() { this.scrolled = true; }};
}
const keys = ["status", "shots", "voices", "jobs", "save", "preview", "final", "range", "from", "to", "duck", "player", "reload", "source", "sourcePlayer", "sourceStatus", "sourceTitle", "selection", "start", "end", "playSelection", "texts", "cards", "shotNav", "shotTitle", "overview", "visual", "visualImage", "videoPlaceholder", "openSource", "watch", "watchReason", "outputs"];
const nodes = Object.fromEntries(keys.map(k => [k, node()]));
const root = node(); root.querySelector = s => nodes[s.match(/"(.*?)"/)[1]];
const doc = {hidden: false, createElement: node, addEventListener() {}};
const id = n => `00000000-0000-0000-0000-${String(n).padStart(12, "0")}`;
const long = ("Syntetický text o památce a krajině. ".repeat(100)).slice(0, 3022);
const view = {ok: true, project_id: id(1), revision: 1, duration_ms: 30000, jobs: [], narrations: [],
  texts: [{title: "Syntetický text", text: long, reference: {moment_id: id(7), revision_id: id(8), sha256: "a".repeat(64)}}],
  sources: [{asset_id: id(2), kind: "photo", title: "První"}, {asset_id: id(3), kind: "photo", title: "Druhá"}, {asset_id: id(4), kind: "video", title: "Video", duration_ms: 1000}, {asset_id: id(5), kind: "audio", title: "Hlas", duration_ms: 3000}],
  draft: {shots: [2, 3, 4].map((n, i) => ({asset_id: id(n), title: "", in_ms: 0, out_ms: i === 0 ? 25000 : 1000, included: true, gain: 1})),
    voices: [{asset_id: id(5), in_ms: 0, out_ms: 3000, at_ms: 0, gain: 1, included: false}], duck_gain: .2}};
let saves = [], renders = [], generations = [], uploads = [], serial = 50, waitGeneration = null, failSave = false, delayedRead = null, delayedSave = null;
const feedback = [];
function recordTake(p, imported = false) {
  const layer = view.draft.shots.find(r => r.asset_id === p.asset_id).photo_text;
  const n = {id: p.request_id, duration_ms: imported ? 2400 : 45000, sha256: "b".repeat(64), included: false};
  view.narrations.push({...n, asset_id: p.asset_id, text: layer.text, original_text: layer.original_text || "", text_source: layer.text_source, deleted: false, label: imported ? "Import MP3" : "Místní čtení"});
  return {ok: true, narration: n, narrations: JSON.parse(JSON.stringify(view.narrations))};
}
const fetch = async (url, options = {}) => {
  if (url.includes("/editor")) return delayedRead || {json: async () => JSON.parse(JSON.stringify(view))};
  if (url.endsWith("/narration-import")) {
    uploads.push(options); const p = {asset_id: options.headers["X-Camino-Asset-Id"], request_id: options.headers["X-Camino-Request-Id"]};
    return {json: async () => recordTake(p, true)};
  }
  const p = JSON.parse(options.body);
  if (url.endsWith("/narration-trash")) {
    view.narrations.find(t => t.id === p.narration_id).deleted = p.deleted;
    assert(!p.deleted || !view.draft.shots.some(r => r.photo_text?.narration?.id === p.narration_id), "detach and save before moving an attached take to trash");
    return {json: async () => ({ok: true, narrations: JSON.parse(JSON.stringify(view.narrations))})};
  }
  if (url.endsWith("/save")) {
    saves.push(p); if (delayedSave) return delayedSave; if (failSave) return {json: async () => ({ok: false, message: "Viditelná chyba u fotografie"})};
    view.draft = p.draft; view.revision++;
    return {json: async () => ({ok: true, revision: view.revision})};
  }
  if (url.endsWith("/narration")) {
    generations.push(p); if (waitGeneration) return waitGeneration;
    return {json: async () => recordTake(p)};
  }
  assert(url.endsWith("/render")); renders.push(p); return {json: async () => ({ok: true})};
};
const context = {window: {}, console}; vm.createContext(context);
vm.runInContext(fs.readFileSync("app/frontend/cockpit/film_editor.js", "utf8"), context);
const editor = context.window.SamanthaFilmEditor.create(root, {document: doc, fetch, feedback: event => feedback.push(event), uuid: () => id(++serial), setTimeout() {}, clearTimeout() {}, confirm: () => true});
const flush = () => new Promise(resolve => setImmediate(resolve));
function all(n) { return [n, ...n.children.flatMap(all)]; }
function find(n, text) { const result = all(n).find(x => x.textContent === text); assert(result, `Missing: ${text}`); return result; }
function photo(index = 0) { return nodes.shots.children[index].children.find(n => n.tag === "details"); }
function area(index = 0) { return all(photo(index)).find(n => n.tag === "textarea"); }
function mode(index = 0) { return all(photo(index)).find(n => n.tag === "select"); }
async function main() {
  editor.open(); await flush();
  const materials = nodes.texts.children[1];
  const target = all(materials).find(n => n.tag === "select");
  assert.equal(target.children.length, 2, "only photographs are offered");
  find(materials, "Přidat samostatnou textovou kartu za fotografii").emit("click");
  assert(all(materials).some(n => n.textContent.includes("nejvýše 1000")), "card rejection is beside its button");
  find(materials, "Předat celý text na fotografii").emit("click");
  assert.equal(area().value, long); assert.equal(photo().open, true); assert.equal(photo().scrolled, true);
  const writesBeforeSelection = saves.length;
  nodes.shotNav.children[1].children[0].emit("click");
  assert(nodes.shots.children[0].classList.contains("hidden"));
  nodes.shotNav.children[0].children[0].emit("click");
  assert.equal(area().value, long, "switching the inspector preserves the unsaved working script");
  assert.equal(saves.length, writesBeforeSelection, "selection does not create a revision");
  await editor.save(); assert.equal(saves.at(-1).draft.shots[0].photo_text.text.length, 3022);
  assert.equal(saves.at(-1).draft.shots[0].out_ms, 25000, "transfer does not silently change photo duration");
  const staleView = JSON.parse(JSON.stringify(view)); let releaseRead;
  delayedRead = new Promise(resolve => { releaseRead = resolve; });
  const oldRead = editor.check(); delayedRead = null;
  area().value += "\nVlastní závěr."; area().emit("input"); await editor.save();
  releaseRead({json: async () => staleView}); await oldRead;
  assert(area().value.endsWith("Vlastní závěr."), "a delayed poll must not replace a newly saved script");
  area().value += "\nDruhý dodatek."; area().emit("input");
  let releaseSave; delayedSave = new Promise(resolve => { releaseSave = resolve; });
  const savingNow = editor.save(); await flush();
  const beforeAcknowledgment = JSON.parse(JSON.stringify(view));
  delayedRead = new Promise(resolve => { releaseRead = resolve; });
  const readDuringSave = editor.check(); delayedRead = null;
  view.draft = saves.at(-1).draft; view.revision++;
  releaseSave({json: async () => ({ok: true, revision: view.revision})}); delayedSave = null; await savingNow;
  releaseRead({json: async () => beforeAcknowledgment}); await readDuringSave;
  assert(area().value.endsWith("Druhý dodatek."), "a poll begun during save must not roll back the acknowledged revision");
  nodes.reload.emit("click"); await flush();
  assert(area().value.endsWith("Druhý dodatek."), "edited text survives a real editor reload");
  mode().value = "scroll"; mode().emit("change");
  find(photo(), "Prodloužit pro celý text / čtení").emit("click"); await editor.save();
  assert(saves.at(-1).draft.shots[0].out_ms > 25000);
  await find(photo(), "Náhled fotografie s textem a zvukem").emit("click");
  assert.equal(renders.at(-1).range.start_ms, 0);
  assert.equal(renders.at(-1).range.end_ms, saves.at(-1).draft.shots[0].out_ms);
  mode().value = "narration"; mode().emit("change");
  await find(photo(), "Vytvořit místní čtení").emit("click");
  assert.equal(generations.length, 1); assert.equal(saves.at(-1).draft.shots[0].photo_text.narration.included, false);
  assert(all(photo()).some(n => n.tag === "audio" && n.src.includes("/narration/")), "saved listening copy has a protected URL");
  const lengthField = nodes.shots.children[0].children.find(n => n.className === "camino-film-fields").children[1].children[0];
  lengthField.value = 25; lengthField.emit("change"); await editor.save();
  find(photo(), "Použít čtení ve filmu").emit("click");
  assert(all(photo()).some(n => n.textContent.includes("Nejprve prodluž")));
  assert(feedback.some(e => e.kind === "warning" && e.message.includes("Fotografie 1") && e.message.includes("Nejprve prodluž")), "the prerequisite is also visible outside the long photo panel");
  find(photo(), "Prodloužit pro celý text / čtení").emit("click");
  find(photo(), "Použít čtení ve filmu").emit("click"); await editor.save();
  assert.equal(saves.at(-1).draft.shots[0].out_ms, 45000);
  assert.equal(saves.at(-1).draft.shots[0].photo_text.narration.included, true);
  find(photo(), "Vyřadit čtení z filmu").emit("click"); await editor.save();
  assert.equal(saves.at(-1).draft.shots[0].photo_text.mode, "none", "explicit removal also clears the narration mode");
  assert.equal(saves.at(-1).draft.shots[0].photo_text.narration.included, false);
  find(photo(), "Použít čtení ve filmu").emit("click"); await editor.save();
  find(nodes.shots.children[0], "↓ Později").emit("click"); await editor.save();
  assert.equal(saves.at(-1).draft.shots[1].asset_id, id(2));
  assert(nodes.shotNav.children[1].children[0].classList.contains("is-selected"), "reordering retains the selected asset identity");
  assert.equal(saves.at(-1).draft.shots[1].photo_text.narration.duration_ms, 45000);
  // A new recording attaches to the second photo, with an identity rather than a fragile absolute time.
  find(photo(0), "Prodloužit fotografii pro nahrávku").emit("click");
  find(photo(0), "Připojit vybranou nahrávku k fotografii").emit("click"); await editor.save();
  assert.equal(saves.at(-1).draft.voices[0].photo_asset_id, id(3));
  // Editing a narrated text invalidates its old synthetic voice immediately.
  area(1).value = "Nový text."; area(1).emit("input"); await editor.save();
  assert.equal(saves.at(-1).draft.shots[1].photo_text.narration, null);
  let release; waitGeneration = new Promise(resolve => { release = resolve; });
  const generating = find(photo(1), "Vytvořit místní čtení").emit("click"); await flush();
  assert(feedback.some(e => e.kind === "busy" && e.channel === "photo"), "in-flight narration reaches the shared status panel");
  assert.equal(editor.canClose(), false, "project switching waits for in-flight synthesis");
  area(1).value = "Změněno během čtení."; area(1).emit("input"); await editor.save();
  release({json: async () => ({ok: true, narration: {id: id(90), duration_ms: 1000, sha256: "c".repeat(64), included: false}})});
  await generating; waitGeneration = null;
  assert.equal(saves.at(-1).draft.shots[1].photo_text.narration, null, "stale generated audio is never attached to new text");
  assert.equal(generations.length, 2, "generation has no automatic retries");
  area(1).value += " Další úprava."; area(1).emit("input"); failSave = true;
  assert.equal(await editor.save(), false);
  assert(all(photo(1)).some(n => n.textContent === "Viditelná chyba u fotografie"));
  failSave = false; assert.equal(await editor.save(), true);
  assert.equal(all(photo(1)).find(n => n.name === "film-original-text").readOnly, true);
  assert.equal(all(photo(1)).find(n => n.name === "film-original-text").value, long, "iPhone original survives every manual edit");
  assert.equal(area(1).readOnly, false, "working script is visibly editable");
  await find(photo(1), "Vytvořit místní čtení").emit("click");
  assert.equal(view.narrations.length, 2, "a new reading keeps the previous take");
  function takeItem(index) { return all(photo(1)).filter(n => n.className === "camino-film-take").find(n => n.children[0].textContent.startsWith(`Pokus ${index} ·`)); }
  const workingBeforeTrash = area(1).value;
  await find(takeItem(2), "Smazat pokus do koše").emit("click");
  assert.equal(view.narrations[1].deleted, true);
  assert.equal(area(1).value, workingBeforeTrash, "deleting a take preserves the working script");
  assert.equal(view.draft.shots[1].photo_text.narration, null);
  assert(all(photo(1)).some(n => n.textContent === "Koš pokusů (1)"));
  await find(takeItem(2), "Obnovit pokus").emit("click");
  assert.equal(view.narrations[1].deleted, false);
  find(takeItem(1), "Upravit text tohoto pokusu").emit("click"); await editor.save();
  assert.equal(area(1).value, long + "\nVlastní závěr.\nDruhý dodatek.", "previous takes retain their exact scripts");
  assert.equal(view.draft.shots[1].photo_text.original_text, long);
  find(photo(1), "Obnovit pracovní text z originálu").emit("click"); await editor.save();
  assert.equal(area(1).value, long);
  const input = all(photo(1)).find(n => n.type === "file");
  const file = {size: 1500, name: "recording.mp3"}; input.files = [file];
  await find(photo(1), "Importovat MP3/WAV k fotografii").emit("click");
  assert.equal(uploads.length, 1); assert.equal(uploads[0].body, file);
  assert.equal(view.narrations.length, 3); assert.equal(view.draft.shots[1].photo_text.narration.included, false);
  find(takeItem(3), "Použít tento pokus ve filmu").emit("click"); await editor.save();
  assert.equal(view.draft.shots[1].photo_text.narration.included, true);
  await find(takeItem(3), "Smazat pokus do koše").emit("click");
  assert.equal(view.draft.shots[1].photo_text.mode, "none");
  assert.equal(view.narrations[2].deleted, true);
  assert.equal(view.draft.shots[1].photo_text.original_text, long);
  console.log("Camino photo text and narration interactions: PASS");
}
main().catch(error => { console.error(error); process.exitCode = 1; });
