const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("app/frontend/cockpit/app.js", "utf8");
const start = source.indexOf("    let caminoFilmRequest = 0;");
const end = source.indexOf("    function closeJanickaModal()", start);
assert(start >= 0 && end > start);
function node(hidden = false) {
  const classes = new Set(hidden ? ["hidden"] : []);
  return {textContent: "", disabled: false, children: [],
    classList: {add: x => classes.add(x), remove: x => classes.delete(x), contains: x => classes.has(x)},
    replaceChildren() { this.children = []; }, appendChild(x) { this.children.push(x); },
    pause() {}, load() {}, removeAttribute() {}};
}
const context = {console, document: {hidden: false, createElement: () => node()},
  caminoFilmEditor: {invalidate() {}, open() {}, close() {}, canClose: () => true},
  confirm: () => false, fetch: async () => { throw new Error("unexpected fetch"); },
  setInterval: () => 1, clearInterval() {}};
for (const name of ["caminoFilmModal", "caminoFilmSummary", "caminoFilmShots", "caminoFilmCreateBtn",
                    "caminoFilmStatus", "caminoFilmVideo", "caminoFilmTest"]) context[name] = node();
vm.createContext(context);
vm.runInContext(source.slice(start, end), context);
const valid = {ok: true, exists: true, valid: true, message: "Verified", photo_count: 1,
  video_count: 1, audio_count: 1, duration_ms: 4500,
  shots: [{kind: "video", title: "<script>PRIVATE SCRIPT</script>", duration_ms: 1500}]};
async function main() {
  context.renderCaminoFilmProject(valid);
  assert.equal(context.caminoFilmShots.children.length, 1);
  assert(context.caminoFilmShots.children[0].textContent.includes("<script>"));
  assert.equal(context.caminoFilmShots.children[0].innerHTML, undefined);
  context.renderCaminoFilmProject({ok: true, exists: true, valid: false, message: "Changed"});
  assert.equal(context.caminoFilmShots.children.length, 0);
  assert.equal(context.caminoFilmSummary.textContent, "");
  assert(context.caminoFilmSummary.classList.contains("hidden"));
  context.renderCaminoFilmProject(valid);
  context.renderCaminoFilmProject({ok: false, message: "Offline"});
  assert.equal(context.caminoFilmShots.children.length, 0);
  let resolves = [];
  context.fetch = () => new Promise(resolve => resolves.push(resolve));
  const earlier = context.refreshCaminoFilmProject();
  const later = context.refreshCaminoFilmProject();
  resolves[1]({json: async () => ({ok: true, exists: true, valid: false, message: "Latest locked"})});
  await later;
  resolves[0]({json: async () => valid});
  await earlier;
  assert.equal(context.caminoFilmStatus.textContent, "Latest locked");
  assert.equal(context.caminoFilmShots.children.length, 0);
  resolves = [];
  const pending = context.refreshCaminoFilmProject();
  context.closeCaminoFilm();
  resolves[0]({json: async () => valid});
  await pending;
  assert.equal(context.caminoFilmShots.children.length, 0);
  let calls = 0;
  context.fetch = async () => { ++calls; return {json: async () => valid}; };
  await context.createCaminoFilmProject();
  assert.equal(calls, 0, "refused owner confirmation must not write");
  context.caminoFilmModal.classList.remove("hidden");
  context.confirm = () => true;
  context.fetch = async (url, options) => {
    assert.equal(url, "/api/camino/film/close-mac-day");
    assert.equal(options.method, "POST");
    assert.deepEqual(JSON.parse(options.body), {confirmed_final_mac_data: true});
    return {json: async () => valid};
  };
  await context.createCaminoFilmProject();
  assert.equal(context.caminoFilmShots.children.length, 1);
  console.log("Camino film frontend: PASS");
}
main().catch(error => { console.error(error); process.exitCode = 1; });
