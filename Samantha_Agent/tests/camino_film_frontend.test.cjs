const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("app/frontend/cockpit/app.js", "utf8");
assert(source.includes("window.SamanthaFilmLibrary.create"));
assert(source.includes("caminoFilmLibrary.open()"));
function node() {
  const classes = new Set(), listeners = {};
  return {textContent: "", value: "", disabled: false, children: [],
    classList: {add: x => classes.add(x), remove: x => classes.delete(x), contains: x => classes.has(x)},
    replaceChildren() { this.children = []; }, appendChild(x) { this.children.push(x); },
    addEventListener(event, fn) { listeners[event] = fn; }, emit(event) { return listeners[event]?.(); }};
}
const pidA = "00000000-0000-0000-0000-000000000001", pidB = "00000000-0000-0000-0000-000000000002";
const dayA = "2026-09-25", dayB = "2026-09-26", dayC = "2026-09-27";
const project = (project_id, local_date) => ({project_id, local_date, revision: 2, ready_exports: 1});
const valid = (project_id, local_date) => ({ok: true, exists: true, valid: true, project_id, local_date,
  message: "Verified " + local_date, photo_count: 1, video_count: 1, audio_count: 1,
  shots: [{kind: "video", title: "<script>SAFE TEXT</script>", duration_ms: 1500}]});
let catalog = {ok: true, days: [dayC, dayB, dayA].map(local_date => ({local_date})),
  projects: [project(pidB, dayB), project(pidA, dayA)]};
const context = {window: {}, URLSearchParams, console}; vm.createContext(context);
vm.runInContext(fs.readFileSync("app/frontend/cockpit/film_library.js", "utf8"), context);
function fixture() {
  const nodes = {}, docListeners = {};
  const root = {querySelector(selector) { return nodes[selector.slice(1)] ||= node(); }};
  const doc = {hidden: false, createElement: node, addEventListener(event, fn) { docListeners[event] = fn; }};
  const storage = new Map(), opened = [], calls = [], confirmation = [];
  let mayClose = true, consent = false, fetcher, suspended = 0;
  const editor = {open(id) { opened.push(id); }, close() {}, canClose: () => mayClose, suspend() { ++suspended; }};
  const response = data => ({json: async () => data});
  fetcher = async (url, options = {}) => {
    calls.push({url, options});
    if (url === "/api/camino/film/catalog") return response(catalog);
    if (url === "/api/camino/film/close-mac-day") {
      const body = JSON.parse(options.body);
      assert.equal(body.confirmed_final_mac_data, true); assert.equal(body.local_date, dayC);
      const created = "00000000-0000-0000-0000-000000000003";
      catalog = {...catalog, projects: [project(created, dayC), ...catalog.projects]};
      return response(valid(created, dayC));
    }
    const params = new URL(url, "http://localhost").searchParams;
    const local_date = params.get("local_date"), id = params.get("project_id");
    return response(id ? valid(id, local_date) : {ok: true, valid: false, exists: false, local_date});
  };
  const library = context.window.SamanthaFilmLibrary.create(root, {document: doc, editor,
    fetch: (...args) => fetcher(...args), confirm: message => { confirmation.push(message); return consent; },
    setInterval: () => 1, clearInterval() {},
    storage: {getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value)}});
  return {library, nodes, opened, calls, doc, docListeners, response, confirmation,
    set fetch(fn) { fetcher = fn; }, set mayClose(value) { mayClose = value; }, set consent(value) { consent = value; },
    get suspended() { return suspended; }};
}
async function main() {
  const a = fixture(); await a.library.open();
  assert.equal(a.opened.at(-1), pidB);
  assert.equal(a.nodes.caminoFilmProjects.children.length, 2);
  assert(a.nodes.caminoFilmShots.children[0].textContent.includes("<script>"));
  assert.equal(a.nodes.caminoFilmShots.children[0].innerHTML, undefined);
  const b = fixture(); await b.library.open();
  await a.library.choose({local_date: dayA, project_id: pidA});
  assert.equal(a.opened.at(-1), pidA); assert.equal(b.opened.at(-1), pidB, "tabs keep their own selection");
  a.mayClose = false;
  assert.equal(await a.library.choose({local_date: dayB, project_id: pidB}), false);
  assert.equal(a.nodes.caminoFilmDay.value, dayA); assert.equal(a.opened.at(-1), pidA);
  a.mayClose = true;
  let resolveA;
  a.fetch = url => {
    const date = new URL(url, "http://localhost").searchParams.get("local_date");
    return date === dayA ? new Promise(resolve => { resolveA = resolve; }) : Promise.resolve(a.response(valid(pidB, dayB)));
  };
  const late = a.library.check();
  await a.library.choose({local_date: dayB, project_id: pidB});
  resolveA(a.response(valid(pidA, dayA))); await late;
  assert.equal(a.opened.at(-1), pidB, "late response cannot switch the selected day");
  a.fetch = async () => a.response(valid(pidA, dayA));
  await a.library.check();
  assert.equal(a.nodes.caminoFilmShots.children.length, 0, "wrong project response hides stale content");
  assert.equal(a.nodes.caminoFilmProjects.children.length, 0, "unverified project counts must disappear too");
  a.fetch = async () => { throw new Error("offline"); };
  await a.library.refresh();
  assert.equal(a.nodes.caminoFilmSummary.textContent, ""); assert(a.suspended > 0);
  let release;
  a.fetch = () => new Promise(resolve => { release = resolve; });
  const closing = a.library.check(); a.library.close();
  release(a.response(valid(pidB, dayB))); await closing;
  assert.equal(a.nodes.caminoFilmShots.children.length, 0);
  const c = fixture(); await c.library.open();
  await c.library.choose({local_date: dayC, project_id: null});
  const before = c.calls.length; await c.library.createProject();
  assert.equal(c.calls.length, before, "declined owner confirmation never writes");
  c.consent = true; await c.library.createProject();
  assert(c.confirmation.at(-1).includes("27. 9. 2026"));
  assert.equal(c.calls.filter(call => call.options.method === "POST").length, 1);
  assert.equal(c.opened.at(-1), "00000000-0000-0000-0000-000000000003");
  const d = fixture(); await d.library.open(); d.mayClose = false;
  catalog = {...catalog, projects: [project(pidA, dayA)]};
  await d.library.refresh();
  assert.equal(d.opened.at(-1), "00000000-0000-0000-0000-000000000003", "catalog refresh cannot discard a pending edit");
  assert(d.suspended > 0); assert.equal(d.nodes.caminoFilmShots.children.length, 0);
  const e = fixture(); await e.library.open();
  e.doc.hidden = true; e.docListeners.visibilitychange();
  assert.equal(e.nodes.caminoFilmProjects.children.length, 0, "backgrounding conceals the old catalog");
  assert.equal(e.nodes.caminoFilmDay.children.length, 0);
  console.log("Camino film library frontend: PASS");
}
main().catch(error => { console.error(error); process.exitCode = 1; });
