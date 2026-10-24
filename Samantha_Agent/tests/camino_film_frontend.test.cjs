const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("app/frontend/cockpit/app.js", "utf8");
assert(source.includes("window.SamanthaFilmLibrary.create"));
assert(source.includes("caminoFilmLibrary.open()"));
function node(tagName) {
  const classes = new Set(), listeners = {};
  return {tagName, textContent: "", value: "", disabled: false, children: [], closest() { return this; },
    classList: {add: x => classes.add(x), remove: x => classes.delete(x), contains: x => classes.has(x)},
    replaceChildren() { this.children = []; }, appendChild(x) { this.children.push(x); },
    addEventListener(event, fn) { listeners[event] = fn; }, emit(event) { return listeners[event]?.(); }};
}
const pidA = "00000000-0000-0000-0000-000000000001", pidB = "00000000-0000-0000-0000-000000000002";
const tripA = "00000000-0000-0000-0000-000000000501", tripB = "00000000-0000-0000-0000-000000000502";
const otherPid = "00000000-0000-0000-0000-000000000601";
const dayA = "2026-09-25", dayB = "2026-09-26", dayC = "2026-09-27";
const project = (project_id, local_date) => ({project_id, local_date, revision: 2, ready_exports: 1});
const valid = (project_id, local_date, trip_id = tripA) => ({trip_id, ok: true, exists: true, valid: true, project_id, local_date,
  message: "Verified " + local_date, photo_count: 1, video_count: 1, audio_count: 1,
  shots: [{kind: "video", title: "<script>SAFE TEXT</script>", duration_ms: 1500}]});
let catalog = {ok: true, days: [dayC, dayB, dayA].map(local_date => ({local_date})),
  projects: [project(pidB, dayB), project(pidA, dayA)]};
let otherCatalog = {ok: true, days: [{local_date:dayA}], projects:[project(otherPid, dayA)]};
const context = {window: {}, URLSearchParams, console, crypto: require("node:crypto")}; vm.createContext(context);
vm.runInContext(fs.readFileSync("app/frontend/cockpit/film_library.js", "utf8"), context);
function fixture(savedStorage = new Map()) {
  const nodes = {}, docListeners = {};
  const root = {querySelector(selector) { return nodes[selector.slice(1)] ||= node(); }};
  const doc = {hidden: false, createElement: node, addEventListener(event, fn) { docListeners[event] = fn; }};
  const storage = savedStorage, opened = [], calls = [], confirmation = [];
  let mayClose = true, consent = false, fetcher, suspended = 0;
  const editor = {open(id) { opened.push(id); }, close() {}, canClose: () => mayClose, suspend() { ++suspended; }};
  const response = data => ({json: async () => data});
  fetcher = async (url, options = {}) => {
    calls.push({url, options});
    if (url === "/api/camino/film/project-trash") return response({ok:true,requests:[]});
    if (url === "/api/camino/film/trips") return response({ok:true, default_trip_id:tripA,
      trips:[{id:tripA,name:"Same holiday",status:"active"},{id:tripB,name:"Same holiday",status:"archived"}]});
    if (url.startsWith("/api/camino/film/catalog?")) {
      const selected = new URL(url,"http://localhost").searchParams.get("trip_id");
      return response({...selected === tripB ? otherCatalog : catalog, trip_id:selected});
    }
    if (url === "/api/camino/film/close-mac-day") {
      const body = JSON.parse(options.body);
      assert.equal(body.confirmed_final_mac_data, true); assert.equal(body.local_date, dayC); assert.equal(body.trip_id, tripA);
      const created = "00000000-0000-0000-0000-000000000003";
      catalog = {...catalog, projects: [project(created, dayC), ...catalog.projects]};
      return response(valid(created, dayC));
    }
    const params = new URL(url, "http://localhost").searchParams;
    const local_date = params.get("local_date"), id = params.get("project_id");
    const trip_id = params.get("trip_id");
    return response(id ? valid(id, local_date, trip_id) : {trip_id, ok: true, valid: false, exists: false, local_date});
  };
  const defaultFetch = fetcher;
  const library = context.window.SamanthaFilmLibrary.create(root, {document: doc, editor,
    fetch: (...args) => fetcher(...args), confirm: message => { confirmation.push(message); return consent; },
    setInterval: () => 1, clearInterval() {},
    storage: {getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value)}});
  return {library, nodes, opened, calls, doc, docListeners, response, confirmation, defaultFetch,
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
  await a.library.choose({trip_id:tripA, local_date: dayA, project_id: pidA});
  assert.equal(a.opened.at(-1), pidA); assert.equal(b.opened.at(-1), pidB, "tabs keep their own selection");
  a.mayClose = false;
  assert.equal(await a.library.choose({trip_id:tripA, local_date: dayB, project_id: pidB}), false);
  assert.equal(a.nodes.caminoFilmDay.value, dayA); assert.equal(a.opened.at(-1), pidA);
  a.mayClose = true;
  let resolveA;
  a.fetch = url => {
    const date = new URL(url, "http://localhost").searchParams.get("local_date");
    return date === dayA ? new Promise(resolve => { resolveA = resolve; }) : Promise.resolve(a.response(valid(pidB, dayB)));
  };
  const late = a.library.check();
  await a.library.choose({trip_id:tripA, local_date: dayB, project_id: pidB});
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
  await c.library.choose({trip_id:tripA, local_date: dayC, project_id: null});
  const before = c.calls.length; await c.library.createProject();
  assert.equal(c.calls.length, before, "declined owner confirmation never writes");
  c.consent = true; await c.library.createProject();
  assert(c.confirmation.at(-1).includes("27. 9. 2026"));
  assert.equal(c.calls.filter(call => call.url === "/api/camino/film/close-mac-day" && call.options.method === "POST").length, 1);
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
  const shared = new Map(), x = fixture(shared), y = fixture();
  await x.library.open(); await y.library.open();
  assert.notEqual(x.nodes.caminoFilmTrip.children[0].textContent, x.nodes.caminoFilmTrip.children[1].textContent,
    "duplicate holiday names have distinguishable labels");
  x.mayClose = false;
  assert.equal(await x.library.chooseTrip(tripB), false, "dirty edit blocks a different holiday too");
  assert.equal(x.nodes.caminoFilmTrip.value, tripA);
  x.mayClose = true; await x.library.chooseTrip(tripB);
  assert.equal(x.opened.at(-1), otherPid); assert.equal(x.nodes.caminoFilmDay.value, dayA);
  assert.equal(y.opened.at(-1), pidA, "another tab keeps the first holiday on the same date");
  const reloaded = fixture(shared); await reloaded.library.open();
  assert.equal(reloaded.nodes.caminoFilmTrip.value, tripB); assert.equal(reloaded.opened.at(-1), otherPid);
  let lateHoliday;
  x.fetch = (url, options) => {
    const params = new URL(url,"http://localhost").searchParams;
    if (url.includes("/day?") && params.get("trip_id") === tripB)
      return new Promise(resolve => {lateHoliday = resolve;});
    return x.defaultFetch(url,options);
  };
  const pendingHoliday = x.library.check(); await x.library.chooseTrip(tripA);
  lateHoliday(x.response(valid(otherPid,dayA,tripB))); await pendingHoliday;
  assert.equal(x.opened.at(-1),pidA,"late response from a different holiday is ignored");
  x.fetch = async () => x.response(valid(pidA,dayA,tripB)); await x.library.check();
  assert.equal(x.nodes.caminoFilmSummary.textContent, "", "same date and film ID with wrong trip are refused");
  const emptyStorage = new Map(); otherCatalog = {ok:true,days:[],projects:[]};
  const empty = fixture(emptyStorage); await empty.library.open(); await empty.library.chooseTrip(tripB);
  assert.equal(empty.nodes.caminoFilmDay.disabled,true); assert.equal(empty.nodes.caminoFilmCreateBtn.disabled,true);
  const emptyReloaded = fixture(emptyStorage); await emptyReloaded.library.open();
  assert.equal(emptyReloaded.nodes.caminoFilmTrip.value,tripB,"empty holiday selection survives reload");
  catalog = {...catalog, projects:[project(pidB,dayB),project(pidA,dayA)]};
  const t = fixture(); t.consent = true;
  const row = {request_id:pidA, target_kind:"trip", target_id:tripA, trip_id:tripA,
    state:"requested", name:"<script>private name</script>", waiting_for_phone:false};
  const controlCalls = [];
  t.fetch = async (url, options) => {
    if (url !== "/api/camino/film/project-trash") return t.defaultFetch(url,options);
    const payload = JSON.parse(options.body); controlCalls.push(payload);
    if (payload.operation === "list") return t.response({ok:true,requests:row.state === "restored" ? [] : [row]});
    if (payload.operation === "preview") return t.response({ok:true,request:{...row,plan_token:"frozen-plan",bytes:1024,
      moment_count:2,asset_count:3,film_count:1,file_count:5}});
    if (payload.operation === "confirm") {
      assert.equal(payload.plan_token,"frozen-plan");
      assert.equal(payload.confirmation,"Potvrzuji globální brzdu: rozumím riziku a chci pokračovat.");
      row.state = "trashed"; row.purge_ms = Date.now() + 604800000;
    } else if (payload.operation === "restore") row.state = "restored";
    else if (payload.operation === "film") {
      assert.equal(payload.project_id,pidB); assert.equal(payload.trip_id,tripA);
      row.target_kind = "film"; row.target_id = pidB; row.state = "requested";
    } else throw new Error("unexpected control");
    return t.response({ok:true,request:row});
  };
  await t.library.open();
  const trash = t.nodes.caminoProjectTrash;
  assert(trash.children[0].children[0].textContent.includes("<script>private name</script>"));
  assert.equal(trash.children[0].children[0].innerHTML,undefined,"names are rendered as text");
  await trash.children[0].children.find(x => x.textContent === "Zkontrolovat rozsah").emit("click");
  const label = trash.children.find(x => x.tagName === "label"), input = label.children[0];
  const submit = trash.children.find(x => x.textContent === "Potvrdit koš na 7 dní");
  assert.equal(submit.disabled,true);
  input.value = "ano"; input.emit("input"); assert.equal(submit.disabled,true);
  input.value = "Potvrzuji globální brzdu: rozumím riziku a chci pokračovat."; input.emit("input");
  assert.equal(submit.disabled,false); await submit.emit("click");
  assert.equal(controlCalls.filter(x => x.operation === "confirm").length,1);
  await trash.children[0].children.find(x => x.textContent === "Obnovit projekt").emit("click");
  assert.equal(row.state,"restored");
  const removeFilm = t.nodes.caminoFilmProjects.children.find(li => li.children[0].textContent.includes("26. 9. 2026"))
    .children.find(x => x.textContent === "Smazat celý film…");
  await removeFilm.emit("click");
  assert.equal(row.target_kind,"film");
  assert(trash.children[0].textContent.startsWith("Pouze film"));
  assert.equal(controlCalls.filter(x => x.operation === "confirm").length,1,"film request alone is not confirmation");
  assert(!controlCalls.some(x => x.operation === "trip"),"whole-trip initiation is absent on Mac");
  console.log("Camino film library frontend: PASS");
}
main().catch(error => { console.error(error); process.exitCode = 1; });
