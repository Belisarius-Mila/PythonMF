const assert = require("node:assert/strict");
const {test} = require("node:test");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
class Element {
  constructor(tag = "div") {this.tag = tag; this.children = []; this.value = ""; this.files = [];}
  append(...nodes) {this.children.push(...nodes);}
  replaceChildren(...nodes) {this.children = nodes;}
  removeAttribute(name) {delete this[name];}
  scrollIntoView() {}
  focus() {this.focused = true;}
  click() {this.clicked = true;}
  showModal() {this.open = true;}
  close() {this.open = false; if (this.onclose) this.onclose();}
}
function fixture() {
  const elements = new Map();
  const doc = {getElementById(id) {
    if (!elements.has(id)) elements.set(id, new Element());
    return elements.get(id);
  }, createElement(tag) {
    const el = new Element(tag);
    if (tag === "canvas") {
      el.getContext = () => ({drawImage() {}});
      el.toDataURL = () => "data:image/jpeg;base64,YQ==";
    }
    return el;
  }};
  const sent = [], opened = [], api = {fail: false};
  const fetcher = async (url, options) => {
    sent.push({url, options});
    if (api.fail) throw new Error("Spojení přerušeno");
    return {ok: true, json: async () => options
      ? {ok: true, scan: {scan_id: "a".repeat(32), pages: 2}}
      : {ok: true, items: [{scan_id: "a".repeat(32), title: "<img onerror=bad>", pages: 2}]}};
  };
  const context = {Blob, atob, URLSearchParams, crypto: require("node:crypto").webcrypto,
    URL: {createObjectURL: () => "blob:preview", revokeObjectURL() {}},
    fetch: async () => {throw new Error("Photo preview must stay in browser memory");},
    Image: class {
      constructor() {this.naturalWidth = 2000; this.naturalHeight = 3000;}
      set src(value) {queueMicrotask(() => this.onload());}
    }};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname, "../app/frontend/cockpit/document_scan.js"), "utf8"), context);
  const scanner = context.createDocumentScanner(doc, fetcher, (...args) => opened.push(args));
  return {api, scanner, sent, opened, el: id => doc.getElementById(id)};
}
test("capture several pages, reorder and save only after confirmation", async () => {
  const f = fixture();
  assert.equal(f.sent.length, 0);
  await f.el("scanFilesInput").onchange({target: {files: [{}, {}], value: ""}});
  assert.equal(f.sent.length, 0);
  assert.equal(f.scanner.state.pages.length, 2);
  f.el("scanPages").children[1].children[2].onclick();
  f.el("scanTitle").value = "Smlouva";
  await f.el("scanSave").onclick();
  const request = f.sent.find(s => s.options);
  assert.equal(request.url, "/api/documents/scans");
  const data = JSON.parse(request.options.body);
  assert.equal(data.pages.length, 2);
  assert.equal(data.confirmed, true);
  assert.equal(f.scanner.state.committed, true);
  assert.equal(f.el("scanSave").disabled, true);
});
test("an uncertain transfer retains pages and the same retry ID", async () => {
  const f = fixture();
  await f.el("scanCameraInput").onchange({target: {files: [{}], value: ""}});
  f.el("scanTitle").value = "Účtenka";
  const id = f.scanner.state.id;
  f.api.fail = true;
  await f.el("scanSave").onclick();
  assert.equal(f.scanner.state.id, id);
  assert.equal(f.scanner.state.pages.length, 1);
  assert.equal(f.scanner.state.committed, false);
  f.api.fail = false;
  await f.el("scanSave").onclick();
  const attempts = f.sent.filter(s => s.options).map(s => JSON.parse(s.options.body));
  assert.equal(attempts[0].scan_id, attempts[1].scan_id);
});
test("PDF selection previews locally, preserves the title and sends one confirmed PDF", async () => {
  const f = fixture();
  const file = new Blob(["%PDF-fixture"], {type: "application/pdf"});
  file.name = "Pojištění.pdf";
  f.el("scanPdfInput").onchange({target: {files: [file], value: ""}});
  assert.equal(f.sent.length, 0);
  assert.equal(f.el("scanTitle").value, "Pojištění");
  assert.equal(f.el("scanPdfPreview").hidden, false);
  await f.el("scanSave").onclick();
  const request = f.sent.find(s => s.options);
  assert.ok(request.url.startsWith("/api/documents/scans/pdf?"));
  assert.equal(request.options.body, file);
  assert.equal(request.options.headers["X-Confirm-Save"], "yes");
});
test("saved documents use text labels and open the selected opaque reference", async () => {
  const f = fixture();
  await f.scanner.saved();
  const row = f.el("scanSaved").children[0];
  assert.equal(row.children[0].textContent, "<img onerror=bad> · 2 stran");
  row.children[2].onclick();
  assert.equal(f.opened[0][0], "a".repeat(32));
});

test("saved PDF and draft preview stay inside Cockpit and return without losing pages", async () => {
  const f = fixture();
  await f.el("scanCameraInput").onchange({target: {files: [{}], value: ""}});
  const id = f.scanner.state.id;
  await f.scanner.saved();
  const link = f.el("scanSaved").children[0].children[1];
  let prevented = false;
  link.onclick({preventDefault() {prevented = true;}});
  assert.ok(prevented);
  assert.equal(link.target, undefined);
  assert.equal(f.el("scanPreviewDialog").open, true);
  assert.ok(f.el("scanPreviewFrame").src.startsWith("/api/documents/scans/pdf?scan_id="));
  f.el("scanPreviewBack").onclick();
  assert.equal(f.el("scanPreviewDialog").open, false);
  assert.equal(f.el("scanPreviewFrame").src, undefined);
  assert.equal(f.scanner.state.pages.length, 1);
  assert.equal(f.scanner.state.id, id);
  f.scanner.reset();
  const file = new Blob(["%PDF-test"], {type: "application/pdf"});
  file.name = "Preview.pdf";
  f.el("scanPdfInput").onchange({target: {files: [file], value: ""}});
  f.el("scanPdfFullPreview").onclick({preventDefault() {}});
  assert.equal(f.el("scanPreviewFrame").src, "blob:preview");
  f.el("scanPreviewBack").onclick();
  assert.equal(f.scanner.state.pdf, file);
});

test("consecutive camera captures retain all pages in the same document", async () => {
  const f = fixture(), id = f.scanner.state.id;
  for (let count = 1; count <= 3; count++) {
    await f.el("scanCameraInput").onchange({target: {files: [{}], value: ""}});
    assert.equal(f.scanner.state.pages.length, count);
    assert.equal(f.scanner.state.id, id);
  }
});

test("trash cancellation has no write; uncertain retry preserves exact operation", async () => {
  let confirmed = false, fail = true;
  const posts = [];
  const context = {URLSearchParams, crypto: require("node:crypto").webcrypto,
    window: {confirm: () => confirmed}, fetch: async (url, options) => {
      if (options && options.method === "POST") {
        posts.push(JSON.parse(options.body));
        if (fail) throw new Error("lost response");
        return {ok: true, json: async () => ({ok: true})};
      }
      return {ok: true, json: async () => ({ok: true, title: "Synthetic", revision: "revision"})};
    }};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname, "../app/frontend/shared/document_lifecycle.js"), "utf8"), context);
  const button = {disabled: false};
  const apply = () => context.SamanthaDocumentLifecycle.apply("document", "docref-test", "trash", button);
  assert.equal(await apply(), false);
  assert.equal(posts.length, 0);
  confirmed = true;
  await assert.rejects(apply(), /lost response/);
  assert.equal(button.disabled, false);
  fail = false;
  assert.equal(await apply(), true);
  assert.deepEqual(posts[0], posts[1]);
});
