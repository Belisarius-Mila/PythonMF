const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const {test} = require('node:test');

class Element {
  constructor(tag = 'div') {
    this.tagName = tag;
    this.children = [];
    this.textContent = '';
    this.value = '';
    this.className = '';
    this.disabled = false;
    this.listeners = {};
    this.classList = {toggle: (name, force) => {
      const classes = new Set(this.className.split(/\s+/).filter(Boolean));
      const added = force === undefined ? !classes.has(name) : force;
      if (added) classes.add(name); else classes.delete(name);
      this.className = [...classes].join(' ');
      return added;
    }};
  }
  set innerHTML(value) {
    assert.equal(value, '', 'Result data must be rendered as text, never HTML');
    this.children = [];
  }
  appendChild(child) { this.children.push(child); }
  addEventListener(name, callback) { this.listeners[name] = callback; }
}

function descendants(node) { return [node, ...node.children.flatMap(descendants)]; }

function setup(fetch) {
  const context = {window: {}, document: {createElement: tag => new Element(tag)}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,
    '../app/frontend/cockpit/document_search.js'), 'utf8'), context);
  const elements = Object.fromEntries(['documentSearchInput', 'documentSearchBtn',
    'documentSearchStatus', 'documentSearchResults', 'documentSearchPagination',
    'documentSearchPreviousBtn', 'documentSearchNextBtn', 'documentSearchRange'].map(key => [key, new Element()]));
  elements.documentSearchInput.value = 'fixture';
  const requests = [], actions = [];
  const handlers = Object.fromEntries(['openDocumentForReading', 'openPurchaseForReading',
    'printDocument', 'moveDocumentLifecycle', 'setDocumentReadingStatus'].map(name =>
    [name, (...args) => actions.push({name, args})]));
  const api = context.window.SamanthaDocumentSearch.create({elements,
    fetch: async (...args) => { requests.push(args); return fetch(...args); },
    readingStatusOptions: [['ok', 'OK'], ['needs_review', 'k revizi'],
      ['unreadable', 'nečitelné'], ['superseded', 'nahrazeno lepší kopií']],
    ...handlers,
  });
  return {api, elements, requests, actions};
}

const response = results => ({json: async () => ({ok: true, message: 'Fixture loaded', results})});
const documentItem = {document_ref: 'docref-fixture', document_id: 'fallback-id',
  title: '<img src=x onerror=alert(1)>', snippet: '<script>unsafe()</script>',
  reading_status: 'unreadable'};

test('short queries clear old results without fetching or invoking actions', async () => {
  const fixture = setup(() => { throw new Error('Unexpected fetch'); });
  for (const query of ['', ' ', ' x ']) {
    fixture.elements.documentSearchResults.appendChild(new Element());
    fixture.elements.documentSearchInput.value = query;
    await fixture.api.searchDocuments();
    assert.equal(fixture.elements.documentSearchResults.children.length, 0);
    assert.match(fixture.elements.documentSearchStatus.textContent, /aspoň dvě/);
  }
  assert.deepEqual(fixture.requests, []);
  assert.deepEqual(fixture.actions, []);
});

test('search encodes a trimmed query, only reads, and restores loading controls', async () => {
  let resolve;
  const fixture = setup(() => new Promise(done => { resolve = done; }));
  fixture.elements.documentSearchInput.value = '  účet & doklad?  ';
  const pending = fixture.api.searchDocuments();
  assert.equal(fixture.elements.documentSearchBtn.disabled, true);
  assert.deepEqual(fixture.requests, [[`/api/documents/search?q=${encodeURIComponent('účet & doklad?')}&limit=8&offset=0`]]);
  resolve(response([]));
  await pending;
  assert.equal(fixture.elements.documentSearchBtn.disabled, false);
  assert.equal(fixture.elements.documentSearchStatus.textContent, 'Fixture loaded');
  assert.deepEqual(fixture.actions, []);
  assert.deepEqual(Object.keys(fixture.api), ['searchDocuments']);
  assert(Object.isFrozen(fixture.api));
});

for (const failure of ['network', 'JSON']) {
  test(`${failure} failure restores the button and reports the error`, async () => {
    const fixture = setup(async () => {
      if (failure === 'network') throw new Error('offline');
      return {json: async () => { throw new SyntaxError('invalid JSON'); }};
    });
    await fixture.api.searchDocuments();
    assert.equal(fixture.elements.documentSearchBtn.disabled, false);
    assert.match(fixture.elements.documentSearchStatus.textContent, /Chyba hledání:/);
    assert.deepEqual(fixture.actions, []);
  });
}

test('document cards use safe text and expand without triggering document actions', async () => {
  const fixture = setup(() => response([documentItem]));
  await fixture.api.searchDocuments();
  const nodes = descendants(fixture.elements.documentSearchResults);
  assert(nodes.some(node => node.textContent === documentItem.title));
  assert(nodes.some(node => node.textContent === documentItem.snippet));
  assert.equal(nodes.find(node => node.tagName === 'option' && node.selected).value, 'unreadable');
  const toggle = nodes.find(node => node.textContent === 'Rozbalit');
  const detail = nodes.find(node => node.className === 'search-detail hidden');
  toggle.listeners.click();
  assert.equal(detail.className, 'search-detail');
  assert.equal(toggle.textContent, 'Sbalit');
  toggle.listeners.click();
  assert.equal(detail.className, 'search-detail hidden');
  assert.deepEqual(fixture.actions, []);
});

test('each document action delegates the exact reference only after user interaction', async () => {
  const fixture = setup(() => response([documentItem]));
  await fixture.api.searchDocuments();
  const nodes = descendants(fixture.elements.documentSearchResults);
  assert.deepEqual(fixture.actions, []);
  for (const label of ['Otevřít / číst', 'Otevřít / číst PDF', 'Tisknout', 'Archivovat', 'Do koše']) {
    nodes.find(node => node.tagName === 'button' && node.textContent === label).listeners.click();
  }
  const select = nodes.find(node => node.tagName === 'select');
  select.value = 'superseded';
  select.listeners.change();
  assert.deepEqual(fixture.actions.map(action => [action.name, action.args[0]]), [
    ['openDocumentForReading', 'docref-fixture'], ['openDocumentForReading', 'docref-fixture'],
    ['printDocument', 'docref-fixture'], ['moveDocumentLifecycle', 'docref-fixture'],
    ['moveDocumentLifecycle', 'docref-fixture'], ['setDocumentReadingStatus', 'docref-fixture'],
  ]);
  assert.equal(fixture.actions[0].args[1].textContent, 'Otevřít / číst');
  assert.equal(fixture.actions[1].args[1].textContent, 'Otevřít / číst PDF');
  assert.equal(fixture.actions[3].args[1], 'archive');
  assert.equal(fixture.actions[4].args[1], 'trash');
  assert.equal(fixture.actions[5].args[1], 'superseded');
  assert.equal(fixture.requests.length, 1, 'Delegated actions must not add module requests');
});

test('purchase cards only offer purchase opening with their own reference', async () => {
  const fixture = setup(() => response([{source_type: 'purchase',
    document_ref: 'purref-fixture', document_id: 'purchase-fallback', title: 'Fixture purchase'}]));
  await fixture.api.searchDocuments();
  const nodes = descendants(fixture.elements.documentSearchResults);
  assert(!nodes.some(node => node.tagName === 'select'));
  assert.deepEqual(nodes.filter(node => node.tagName === 'button').map(node => node.textContent),
    ['Otevřít PDF', 'Rozbalit', 'Otevřít nákupní PDF']);
  assert.deepEqual(fixture.actions, []);
  for (const button of nodes.filter(node => node.tagName === 'button' && node.textContent !== 'Rozbalit')) {
    button.listeners.click();
  }
  assert.deepEqual(fixture.actions.map(action => [action.name, action.args[0]]),
    [['openPurchaseForReading', 'purref-fixture'], ['openPurchaseForReading', 'purref-fixture']]);
});

test('legacy document IDs still open and subsequent searches replace previous cards', async () => {
  let items = [{document_id: 'legacy-fixture', title: 'Old fixture'}];
  const fixture = setup(() => response(items));
  await fixture.api.searchDocuments();
  descendants(fixture.elements.documentSearchResults).find(node => node.textContent === 'Otevřít / číst').listeners.click();
  assert.equal(fixture.actions[0].args[0], 'legacy-fixture');
  items = [{document_ref: 'fresh-fixture', title: 'Fresh fixture'}];
  await fixture.api.searchDocuments();
  assert.equal(fixture.elements.documentSearchResults.children.length, 1);
  assert(!descendants(fixture.elements.documentSearchResults).some(node => node.textContent === 'Old fixture'));
  items = [];
  await fixture.api.searchDocuments();
  assert.equal(fixture.elements.documentSearchResults.children.length, 0);
});

const pagedResponse = (offset, total = 23) => ({ok: true, json: async () => ({
  ok: true, offset, total_count: total, has_more: offset + 8 < total,
  next_offset: offset + 8 < total ? offset + 8 : null,
  results: Array.from({length: Math.max(0, Math.min(8, total - offset))}, (_, i) => ({document_ref: `ref-${offset + i}`, title: `Result ${offset + i}`})),
})});

test('three pages expose all 23 distinct references and return to the preceding page', async () => {
  const fixture = setup(url => pagedResponse(Number(new URL(url, 'http://fixture.test').searchParams.get('offset'))));
  await fixture.api.searchDocuments();
  const ranges = [], refs = [];
  for (let page = 0; page < 3; page++) {
    if (page) await fixture.elements.documentSearchNextBtn.listeners.click();
    ranges.push(fixture.elements.documentSearchRange.textContent);
    for (const node of descendants(fixture.elements.documentSearchResults).filter(node => node.textContent === 'Otevřít / číst')) node.listeners.click();
  }
  refs.push(...fixture.actions.map(action => action.args[0]));
  assert.equal(new Set(refs).size, 23);
  assert.deepEqual(ranges, ['1–8 z 23', '9–16 z 23', '17–23 z 23']);
  assert.equal(fixture.elements.documentSearchNextBtn.disabled, true);
  await fixture.elements.documentSearchPreviousBtn.listeners.click();
  assert.equal(fixture.elements.documentSearchRange.textContent, '9–16 z 23');
});

test('typing a different query clears pages and ignores an older response', async () => {
  const pending = [];
  const fixture = setup(() => new Promise(resolve => pending.push(resolve)));
  const old = fixture.api.searchDocuments();
  fixture.elements.documentSearchInput.value = 'changed';
  fixture.elements.documentSearchInput.listeners.input();
  assert.equal(fixture.elements.documentSearchNextBtn.disabled, true);
  const fresh = fixture.api.searchDocuments();
  pending[1](pagedResponse(0, 1));await fresh;
  pending[0](pagedResponse(0, 23));await old;
  assert.equal(fixture.elements.documentSearchRange.textContent, '1–1 z 1');
  assert.equal(fixture.elements.documentSearchResults.children.length, 1);
  assert.match(fixture.requests[1][0], /q=changed&limit=8&offset=0$/);
});

for (const failure of ['HTTP', 'provider', 'network']) {
  test(`${failure} on the next page preserves results and allows retry`, async () => {
    let fail = true;
    const fixture = setup(url => {
      const offset = Number(new URL(url, 'http://fixture.test').searchParams.get('offset'));
      if (offset && fail) {
        if (failure === 'network') throw new Error('offline');
        return {ok: failure !== 'HTTP', json: async () => ({ok: failure !== 'provider', message: 'Fixture failed'})};
      }
      return pagedResponse(offset, 9);
    });
    await fixture.api.searchDocuments();
    await fixture.elements.documentSearchNextBtn.listeners.click();
    assert.equal(fixture.elements.documentSearchRange.textContent, '1–8 z 9');
    assert.equal(fixture.elements.documentSearchResults.children.length, 8);
    assert.equal(fixture.elements.documentSearchNextBtn.disabled, false);
    assert.match(fixture.elements.documentSearchStatus.textContent, /Chyba/);
    fail = false;await fixture.elements.documentSearchNextBtn.listeners.click();
    assert.equal(fixture.elements.documentSearchRange.textContent, '9–9 z 9');
  });
}

test('repeated submit while the same page loads makes only one request', async () => {
  let resolve;
  const fixture = setup(() => new Promise(done => {resolve = done;}));
  const first = fixture.api.searchDocuments();
  await fixture.api.searchDocuments();
  assert.equal(fixture.requests.length, 1);
  resolve(pagedResponse(0));await first;
});

test('a shrinking index has a reachable previous page and an explicit empty-page message', async () => {
  const fixture = setup(url => pagedResponse(Number(new URL(url, 'http://fixture.test').searchParams.get('offset')), url.endsWith('offset=0') ? 9 : 0));
  await fixture.api.searchDocuments();await fixture.elements.documentSearchNextBtn.listeners.click();
  assert.equal(fixture.elements.documentSearchResults.children.length, 0);
  assert.equal(fixture.elements.documentSearchPreviousBtn.disabled, false);
  assert.equal(fixture.elements.documentSearchNextBtn.disabled, true);
  assert.match(fixture.elements.documentSearchStatus.textContent, /předchozí/);
});
