const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
class Element {
  constructor() { this.children = []; this.textContent = ""; }
  replaceChildren() { this.children = []; }
  append(...elements) { this.children.push(...elements); }
  appendChild(element) { this.children.push(element); }
  set innerHTML(_) { throw new Error("unsafe HTML"); }
}
const status = new Element(), list = new Element();
const doc = {createElement: () => new Element(), getElementById: id => id === "agentSupervisorStatus" ? status : list};
let requests = 0, fail = false;
const ctx = {document: doc, window: {setTimeout, clearTimeout}, AbortController, Date,
  fetch: async (url, options) => {
    requests++; assert.equal(url, "/api/agent-supervisor/status"); assert.equal(options.cache, "no-store");
    if (fail) throw new Error("offline");
    return {ok: true, json: async () => ({ok:true, configured:false, worker_recent:false, rows:[{
      label:"<img onerror=alert(1)>", state:"ok", message:"fixture", last_success_at:"", next_due_at:""
    }]})};
  }};
vm.runInNewContext(fs.readFileSync("app/frontend/cockpit/agent_supervisor.js", "utf8"), ctx);
(async () => {
  const frontend = ctx.window.SamanthaAgentSupervisor;
  await Promise.all([frontend.refresh(), frontend.refresh()]);
  assert.equal(requests,1); assert.equal(list.children.length,1);
  assert.match(list.children[0].children[0].textContent, /<img/);
  assert.match(status.textContent,/vypnutý/);
  fail=true; await frontend.refresh();
  assert.equal(list.children.length,0); assert.match(status.textContent,/nelze ověřit/);
  frontend.render({ok:true, configured:true, worker_recent:true, notifications_enabled:true,
    notifications_paused:true, rows:[{label:'Autosave',state:'paused',message:'Mac se probouzí.'}]},status,list,doc);
  assert.match(list.children[0].children[0].textContent,/Pozastaveno/);
  assert.match(status.textContent,/dočasně pozastavená/);
  console.log("Supervisor frontend PASS");
})().catch(error => { console.error(error); process.exitCode=1; });
