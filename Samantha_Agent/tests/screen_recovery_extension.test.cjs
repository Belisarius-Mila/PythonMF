const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {createHandler, parseRequest} = require('../tools/vscode-screen-recovery/extension.cjs');

const uri = {scheme: 'vscode', authority: 'samantha-local.screen-recovery', path: '/attach', query: `port=8770&ticket=${'a'.repeat(64)}`};
function fixture() {
  const created = [], errors = [], requests = [];
  const vscode = {workspace: {isTrusted: true}, window: {
    terminals: [], showErrorMessage: text => errors.push(text),
    createTerminal: options => {
      const terminal = {show: () => {terminal.shown = true;}, options};
      created.push(terminal); vscode.window.terminals.push(terminal); return terminal;
    }
  }};
  const fetcher = async (url, options) => {
    requests.push({url, options});
    return {ok: true, json: async () => ({ok: true, socket: '42.test'})};
  };
  return {vscode, fetcher, created, errors, requests};
}

test('only a bounded local claim URI is accepted', () => {
  assert.equal(parseRequest(uri).port, 8770);
  for (const bad of [{scheme: 'https'}, {authority: 'evil'}, {path: '/exec'}, {fragment: 'x'},
    {query: uri.query + '&command=bad'}, {query: uri.query.replace('8770', '99999')}]) {
    assert.throws(() => parseRequest({...uri, ...bad}));
  }
});

test('claims locally and creates screen directly without shell text or process revive', async () => {
  const f = fixture();
  const handler = createHandler(f.vscode, f.fetcher, 'darwin');
  await handler.handleUri(uri);
  assert.equal(f.requests[0].url, 'http://127.0.0.1:8770/api/screen/sessions/claim');
  assert.equal(f.requests[0].options.redirect, 'error');
  assert.equal(f.created[0].options.shellPath, '/usr/bin/screen');
  assert.deepEqual(f.created[0].options.shellArgs, ['-d', '-r', '42.test']);
  assert.equal(f.created[0].options.isTransient, true);
  assert.equal(f.created[0].shown, true);
  await handler.handleUri(uri);
  assert.equal(f.created.length, 1);
});

test('untrusted windows and non-Mac hosts never redeem or start terminals', async () => {
  for (const platform of ['darwin', 'linux']) {
    const f = fixture();
    f.vscode.workspace.isTrusted = platform !== 'darwin';
    await createHandler(f.vscode, f.fetcher, platform).handleUri(uri);
    assert.equal(f.requests.length, 0); assert.equal(f.created.length, 0);
  }
});

test('failed claim, injection-shaped socket and network failure never start a terminal', async () => {
  for (const value of [{ok: false}, {ok: true, socket: '42.test; echo bad'}, {ok: true, socket: '-R'}]) {
    const f = fixture();
    await createHandler(f.vscode, async () => ({ok: true, json: async () => value}), 'darwin').handleUri(uri);
    assert.equal(f.created.length, 0); assert.equal(f.errors.length, 1);
  }
  const f = fixture(); let calls = 0;
  await createHandler(f.vscode, async () => {calls++; throw Error('private detail');}, 'darwin').handleUri(uri);
  assert.equal(calls, 1); assert.equal(f.created.length, 0);
  assert.ok(!f.errors.join('').includes('private detail'));
});

test('Cockpit cancel sends nothing; takeover posts only the selected recovery identity', async () => {
  class Element {
    constructor() {this.children = []; this.events = {}; this.textContent = ''; this.disabled = false;}
    append(...items) {this.children.push(...items);}
    replaceChildren() {this.children = [];}
    addEventListener(name, callback) {this.events[name] = callback;}
    querySelectorAll() {return [];}
  }
  const ids = Object.fromEntries(['codexSessionsPanel', 'codexSessionsList', 'codexSessionsStatus',
    'codexSessionsRefreshBtn', 'screenSessionsList', 'screenSessionsStatus', 'dashboardSessionsBtn']
    .map(id => [id, new Element()]));
  const posts = []; let confirmed = false; const prompts = [];
  const session = {pid: 42, socket: '42.test', state: 'Attached', can_attach: true,
    attach_identity: 'recovery-only', identity: 'stop-only', can_stop: false};
  const fetcher = async (path, options) => {
    if (options.method === 'POST') {posts.push({path, body: JSON.parse(options.body)}); return {ok: true, json: async () => ({ok: true, message: 'Předáno VS Code'})};}
    return {ok: true, json: async () => ({ok: true, sessions: path.includes('/screen/') ? [session] : [], generated_at: new Date().toISOString()})};
  };
  vm.runInNewContext(fs.readFileSync('app/frontend/cockpit/codex_sessions.js', 'utf8'), {
    document: {getElementById: id => ids[id], createElement: () => new Element()},
    window: {setInterval() {}, confirm: text => {prompts.push(text); return confirmed;}}, fetch: fetcher
  });
  await ids.codexSessionsRefreshBtn.events.click();
  const button = ids.screenSessionsList.children[0].children.find(x => x.textContent === 'Obnovit ve VS Code na Macu');
  assert.ok(button);
  await button.events.click();
  assert.equal(posts.length, 0);
  confirmed = true;
  await button.events.click();
  assert.deepEqual(posts, [{path: '/api/screen/sessions/attach', body: {pid: 42, identity: 'recovery-only', confirmed: true, takeover: true}}]);
  assert.ok(prompts[0].includes('Původní terminál se odpojí'));
  assert.equal(ids.screenSessionsStatus.textContent, 'Předáno VS Code');
});
