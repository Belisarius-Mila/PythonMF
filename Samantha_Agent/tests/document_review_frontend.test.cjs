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
    this.disabled = false;
    this.listeners = {};
  }
  set innerHTML(value) {
    assert.equal(value, '', 'Only clearing the container may use HTML');
    this.children = [];
  }
  appendChild(child) { this.children.push(child); }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  scrollIntoView(options) { this.scrolled = options; }
}

function setup(fetch) {
  const context = {window: {}, document: {createElement: tag => new Element(tag)}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,
    '../app/frontend/cockpit/document_review.js'), 'utf8'), context);
  const elements = Object.fromEntries(['documentsPanel', 'reviewReportBtn',
    'reviewReportStatus', 'reviewReportList', 'reviewReportCount'].map(key => [key, new Element()]));
  const requests = [], errors = [], messages = [], opened = [];
  const api = context.window.SamanthaDocumentReview.create({
    elements,
    fetch: async (...args) => { requests.push(args); return fetch(...args); },
    recordFrontendError: error => errors.push(error),
    showMessage: message => messages.push(message),
    openScanDocuReview: (...args) => opened.push(args),
  });
  return {api, elements, requests, errors, messages, opened};
}

function descendants(node) {
  return [node, ...node.children.flatMap(descendants)];
}

test('opening the review panel reads only the report and restores the button', async () => {
  let resolve;
  const fixture = setup(() => new Promise(done => { resolve = done; }));
  const pending = fixture.api.openDocumentReviewPanel();
  assert.equal(fixture.elements.documentsPanel.open, true);
  assert.equal(fixture.elements.reviewReportBtn.disabled, true);
  assert.deepEqual(fixture.requests, [['/api/documents/review-report']]);
  resolve({json: async () => ({summary: {candidate_count: 0}, groups: []})});
  await pending;
  assert.equal(fixture.elements.reviewReportBtn.disabled, false);
  assert.equal(fixture.elements.reviewReportCount.textContent, '0');
  assert.match(fixture.elements.reviewReportList.children[0].textContent, /Žádný dokument/);
  assert.equal(fixture.elements.reviewReportList.scrolled.block, 'start');
  assert.match(fixture.messages.at(-1), /Vyber dokument/);
  assert.deepEqual(fixture.opened, []);
});

test('a network failure restores controls without a success message or action', async () => {
  const fixture = setup(async () => { throw new Error('offline'); });
  await fixture.api.openDocumentReviewPanel();
  assert.equal(fixture.elements.reviewReportBtn.disabled, false);
  assert.match(fixture.elements.reviewReportStatus.textContent, /Chyba reportu:.*offline/);
  assert.equal(fixture.errors.length, 1);
  assert.equal(fixture.messages.length, 1);
  assert.deepEqual(fixture.opened, []);
});

test('an invalid JSON response is reported and cannot leave the button disabled', async () => {
  const fixture = setup(async () => ({json: async () => { throw new SyntaxError('invalid JSON'); }}));
  assert.equal(await fixture.api.loadDocumentReviewReport(), false);
  assert.equal(fixture.elements.reviewReportBtn.disabled, false);
  assert.match(fixture.elements.reviewReportStatus.textContent, /invalid JSON/);
  assert.equal(fixture.errors.length, 1);
});

test('group rendering preserves safe text, truncation and exact-item click delegation', () => {
  const fixture = setup(() => { throw new Error('Rendering must not fetch'); });
  const item = {document_ref: 'fixture-document', document_id: 'demo',
    title: '<img src=x onerror=alert(1)>', reasons: [{label: 'Ukázkový důvod'}],
    metadata_suggestion: {can_accept: true, summary: 'Ukázkový návrh'}};
  fixture.api.renderDocumentReviewReport({summary: {candidate_count: 2}, truncated: true,
    groups: [{id: 'review', count: 2, items: [item], truncated: true},
      {id: 'empty', items: [], empty_label: 'Ukázková prázdná skupina'}]});
  const nodes = descendants(fixture.elements.reviewReportList);
  assert.equal(fixture.elements.reviewReportCount.textContent, '2');
  assert(nodes.some(node => node.textContent === item.title));
  assert(nodes.some(node => node.textContent === 'Návrh: Ukázkový návrh'));
  assert(nodes.some(node => node.textContent === 'Ukázková prázdná skupina'));
  assert.equal(nodes.filter(node => /zkrácen/.test(node.textContent)).length, 2);
  const buttons = nodes.filter(node => node.tagName === 'button');
  assert.equal(buttons.length, 1);
  assert.equal(buttons[0].textContent, 'Vyřešit ve ScanDocu');
  assert.deepEqual(fixture.opened, []);
  buttons[0].listeners.click();
  assert.equal(fixture.opened[0][0], item);
  assert.equal(fixture.opened[0][1], buttons[0]);
  assert.deepEqual(fixture.requests, []);
});

test('refresh replaces previous items rather than duplicating the list', () => {
  const fixture = setup(() => { throw new Error('Unexpected fetch'); });
  fixture.api.renderDocumentReviewReport({groups: [{items: [{title: 'Old fixture'}]}]});
  fixture.api.renderDocumentReviewReport({groups: []});
  assert.equal(fixture.elements.reviewReportList.children.length, 1);
  assert(!descendants(fixture.elements.reviewReportList).some(node => node.textContent === 'Old fixture'));
});
