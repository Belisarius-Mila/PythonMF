const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
function node() {
  const classes = new Set(), listeners = {};
  return {children: [], value: "", textContent: "", disabled: false, paused: false,
    classList: {add: x => classes.add(x), remove: x => classes.delete(x), contains: x => classes.has(x)},
    addEventListener(event, fn) { listeners[event] = fn; },
    emit(event) { return listeners[event]?.(); },
    appendChild(n) { this.children.push(n); }, replaceChildren() { this.children = []; },
    pause() { this.paused = true; }, load() {}, removeAttribute(k) { delete this[k]; }};
}
const doc = {hidden: false, createElement: node, addEventListener() {}};
const nodes = Object.fromEntries(["status", "shots", "voices", "jobs", "save", "preview", "final", "range", "from", "to", "duck", "player", "reload"].map(k => [k, node()]));
const root = node(); root.querySelector = selector => nodes[selector.match(/"(.*?)"/)[1]];
const sid = "00000000-0000-0000-0000-000000000001", pid = "00000000-0000-0000-0000-000000000002";
let view = {ok: true, project_id: pid, revision: 1, duration_ms: 3000,
  sources: [{asset_id: sid, kind: "photo", duration_ms: null, title: "<script>SAFE TEXT</script>"}],
  draft: {shots: [{asset_id: sid, title: "Title", in_ms: 0, out_ms: 3000, gain: 1, included: true}], voices: [], duck_gain: .2}, jobs: []};
let saves = [], renderCalls = [], clock = [], loseReply = false, uuidCount = 10, offline = false, readWait = null;
const fetch = async (url, options) => {
  if (url.endsWith("/editor")) {
    if (offline) throw new Error("offline");
    if (readWait) return readWait;
    return {json: async () => JSON.parse(JSON.stringify(view))};
  }
  const p = JSON.parse(options.body);
  if (url.endsWith("/save")) {
    saves.push(p);
    if (loseReply) { loseReply = false; throw new Error("lost after save"); }
    view.revision = p.expected_revision + 1; view.draft = p.draft;
    return {json: async () => ({ok: true, revision: view.revision})};
  }
  assert(url.endsWith("/render")); renderCalls.push(p);
  return {json: async () => ({ok: true})};
};
const context = {window: {}, console}; vm.createContext(context);
vm.runInContext(fs.readFileSync("app/frontend/cockpit/film_editor.js", "utf8"), context);
const editor = context.window.SamanthaFilmEditor.create(root, {document: doc, fetch,
  uuid: () => `00000000-0000-0000-0000-${String(++uuidCount).padStart(12, "0")}`,
  setTimeout: (fn, delay) => { clock.push({fn, delay}); return clock.length; }, clearTimeout() {}, confirm: () => true});
const flush = () => new Promise(resolve => setImmediate(resolve));
function titleInput() { return nodes.shots.children[0].children.find(n => n.className === "camino-film-fields").children[0].children[0]; }
async function main() {
  editor.open(); await flush();
  assert.equal(nodes.shots.children.length, 1);
  assert(nodes.shots.children[0].children[0].textContent.includes("<script>"));
  assert.equal(nodes.shots.children[0].children[0].innerHTML, undefined);
  titleInput().value = "Manual title"; titleInput().emit("change");
  assert.equal(nodes.preview.disabled, true);
  const auto = clock.find(t => t.delay === 700); await auto.fn(); await flush();
  assert.equal(saves.length, 1); assert.equal(saves[0].draft.shots[0].title, "Manual title");
  assert.equal(nodes.preview.disabled, false);
  titleInput().value = "Another title"; titleInput().emit("change"); loseReply = true;
  assert.equal(await editor.save(), false); const lostId = saves.at(-1).request_id;
  assert.equal(await editor.save(), true); assert.equal(saves.at(-1).request_id, lostId);
  nodes.final.emit("click"); await flush();
  assert.equal(renderCalls.at(-1).revision, view.revision);
  assert.equal(renderCalls.at(-1).profile, "final"); assert.equal(renderCalls.at(-1).range, null);
  view.jobs = [{job_id: pid, revision: 1, profile: "preview", range: null, state: "failed"},
    {job_id: sid, revision: 1, profile: "preview", range: null, state: "ready", url: `/api/camino/film/output/${pid}/${sid}`}];
  await editor.check(); assert(nodes.jobs.children[0].textContent.includes("starší střih"));
  assert(nodes.jobs.children[1].textContent.includes("Starší neúspěšný pokus"));
  assert.equal(nodes.jobs.children[1].children.length, 0, "replaced failed job must not appear as the current export failure");
  nodes.jobs.children[0].children[0].emit("click"); assert(nodes.player.src.startsWith("/api/camino/film/output/"));
  titleInput().value = "Survives temporary offline"; titleInput().emit("change");
  offline = true; await editor.check(); assert.equal(nodes.shots.children.length, 0);
  offline = false; await editor.check(); assert.equal(titleInput().value, "Survives temporary offline");
  assert.equal(await editor.save(), true);
  view = {ok: false, message: "Privacy changed"}; await editor.check();
  assert.equal(nodes.shots.children.length, 0); assert.equal(nodes.jobs.children.length, 0);
  assert.equal(nodes.player.src, undefined); assert(nodes.player.paused); assert(nodes.final.disabled);
  editor.close(); assert(root.classList.contains("hidden"));
  let resolve; readWait = new Promise(r => { resolve = r; }); editor.open();
  editor.close(); resolve({json: async () => ({ok: true, project_id: pid, revision: 99})});
  await flush(); assert.equal(nodes.shots.children.length, 0); assert.equal(nodes.jobs.children.length, 0);
  console.log("Camino film editor frontend: PASS");
}
main().catch(error => { console.error(error); process.exitCode = 1; });
