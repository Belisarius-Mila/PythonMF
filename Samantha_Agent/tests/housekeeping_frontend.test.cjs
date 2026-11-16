const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
class Element {
  constructor() { this.children = []; this.textContent = ""; this.open = true; this.disabled = false; this.handlers = {}; }
  replaceChildren() { this.children = []; }
  append(...elements) { this.children.push(...elements); }
  appendChild(element) { this.children.push(element); }
  addEventListener(name, callback) { this.handlers[name] = callback; }
  set innerHTML(_) { throw new Error("unsafe HTML"); }
}
const elements = Object.fromEntries(["housekeepingStatus", "housekeepingMetrics", "housekeepingList", "housekeepingRefreshBtn", "servicePanel", "serviceOperationsPanel"].map(id => [id, new Element()]));
const doc = {hidden:false, handlers:{}, createElement: () => new Element(), getElementById: id => elements[id], addEventListener(name, callback) { this.handlers[name] = callback; }};
const fixture = {ok:true,enabled:true,scheduler:{loaded:true,last_exit_code:0},audit:{checked_at:10000,stale:false,pending:false},
  last_run:{at:10000,recent:true,state:"completed",free_change_bytes:2**29,autosave_removed:48,worktrees_removed:0},
  counts:{pending:0,blocked:1,unclosed:0},rows:[{name:"<img onerror=alert(1)>",state:"blocked",reason:"Lokální data."}]};
let requests = [], fail = false, resolveFetch, intervalCallback;
const ctx = {document:doc,window:{setTimeout,clearTimeout,setInterval:callback=>{intervalCallback=callback;}},AbortController,Date,
  fetch: (url, options) => {
    requests.push(url); assert.equal(options.cache,"no-store"); assert.equal(options.method,undefined);
    if (fail) return Promise.reject(new Error("offline"));
    return new Promise(resolve => {resolveFetch = () => resolve({ok:true,json:async()=>fixture});});
  }};
vm.runInNewContext(fs.readFileSync("app/frontend/cockpit/housekeeping.js","utf8"),ctx);
(async () => {
  const frontend=ctx.window.SamanthaWorkspaceHousekeeping;
  const {housekeepingStatus:status,housekeepingMetrics:metrics,housekeepingList:list}=elements;
  const first=frontend.refresh(true); const duplicate=frontend.refresh(true); resolveFetch(); await Promise.all([first,duplicate]);
  assert.deepEqual(requests,["/api/workspace-housekeeping?refresh=1"]);
  assert.match(status.textContent,/každou hodinu/);
  assert.match(metrics.children[1].children[1].textContent,/\+0\.50 GiB/);
  assert.match(list.children[0].children[0].textContent,/<img/);
  fail=true; await frontend.refresh();
  assert.equal(list.children.length,0); assert.equal(metrics.children.length,0); assert.match(status.textContent,/nelze ověřit/);
  frontend.render({...fixture,audit:{pending:true,checked_at:null},counts:{pending:null,blocked:null,unclosed:null},rows:[]},status,metrics,list,doc);
  assert.match(status.textContent,/Ověřuji/); assert.equal(metrics.children[3].children[1].textContent,"zatím neověřeno");
  frontend.render({...fixture,audit:{checked_at:10000,stale:true,failed:true},last_run:{at:10000,recent:false,state:"attention",free_change_bytes:-(2**29)}},status,metrics,list,doc);
  assert.match(status.textContent,/poslední známý stav/); assert.match(status.textContent,/čerstvě doložený/);
  assert.match(metrics.children[1].children[1].textContent,/-0\.50 GiB/);
  const before=requests.length; elements.servicePanel.open=false; await frontend.refresh(true); assert.equal(requests.length,before);
  fail=false;elements.servicePanel.open=true;
  const late=frontend.refresh(); elements.servicePanel.open=false; resolveFetch(); await late;
  assert.match(status.textContent,/poslední známý stav/); // a hidden panel cannot receive a late green result
  const closedCount=requests.length;frontend.init();frontend.init();assert.equal(requests.length,closedCount);
  fail=true;elements.servicePanel.open=true;elements.servicePanel.handlers.toggle();
  await new Promise(resolve=>setImmediate(resolve));assert.equal(requests.length,closedCount+1);
  elements.housekeepingRefreshBtn.handlers.click();await new Promise(resolve=>setImmediate(resolve));
  assert.equal(requests.at(-1),"/api/workspace-housekeeping?refresh=1");
  elements.servicePanel.open=false;elements.servicePanel.handlers.toggle();
  const hiddenCount=requests.length;intervalCallback();assert.equal(requests.length,hiddenCount);
  console.log("Housekeeping frontend PASS");
})().catch(error=>{console.error(error);process.exitCode=1;});
