const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.listeners = {}; this._text = ''; this.open = false; this.value = ''; this.disabled = false; }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(''); }
  set innerHTML(_) { throw new Error('Untrusted email content must remain text'); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = [...children]; this._text = ''; }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  showModal() { this.open = true; }
  close() { this.open = false; }
  async click() { if (!this.disabled) await this.listeners.click?.({target: this}); }
}

function find(element, label) {
  if (element.tag === 'button' && element.textContent === label) return element;
  for (const child of element.children) { const result = find(child, label); if (result) return result; }
  return null;
}

(async () => {
  const ids = Object.fromEntries(['replyEditor','replyRecipient','replySubject','replyBody','replyStatus','replyForm',
    'closeEditor','status','notice','cards','hours','archived'].map(id => [id, new Element(id)]));
  const metadata = {title: 'Podklady', domain: 'work', document_type: 'email', counterparty: 'Firma', tags: ['schůzka']};
  const data = {schedule: {}, sources: [], assessment_errors: 0, archived: [],
    cards: [{id: 'important', header: {subject: '<img src=x onerror=alert(1)>', sender: 'Firma', date: '4. 11.'},
      created_at: '2026-11-04', status: 'awaiting_confirmation', proposal_digest: 'original-digest',
      message: {body_text: 'CELÉ TĚLO A KONEC'}, proposal: {summary: 'Schůzka', reason: 'Je třeba odpověď',
        metadata, reply_subject: 'Re: Schůzka', reply_draft: 'Potvrzuji účast.'}}],
    hours: [{text: '18:00: Firma — Reklama', ids: ['low-1','low-2']}]};
  const calls = [], intervals = [];
  let confirmChoice = true;
  const context = {document: {getElementById: id => ids[id], createElement: tag => new Element(tag)},
    window: {setInterval: fn => intervals.push(fn), confirm: () => confirmChoice},
    fetch: async (url, options) => {
      const payload = options?.body ? JSON.parse(options.body) : null;
      calls.push({url, payload});
      if (url.endsWith('/edit')) { data.cards[0].proposal = payload.proposal; data.cards[0].proposal_digest = 'new-digest'; }
      if (url.endsWith('/dismiss')) data.hours = [];
      if (url.endsWith('/archive')) { data.archived.push(data.cards.pop()); }
      return {ok: true, json: async () => JSON.parse(JSON.stringify(url.endsWith('/overview') ? {ok: true, ...data} : {ok: true}))};
    }, Date, Error, JSON};
  const source = fs.readFileSync(path.join(__dirname, '../app/frontend/email_agent/app.js'), 'utf8');
  vm.runInNewContext(source, context);
  const flush = () => new Promise(resolve => setImmediate(resolve));
  await flush();
  assert.match(ids.cards.textContent, /CELÉ TĚLO A KONEC/);
  assert.match(ids.cards.textContent, /<img src=x onerror=alert\(1\)>/);
  await find(ids.cards, 'Upravit odpověď').click();
  assert.equal(ids.replyEditor.open, true);
  ids.replySubject.value = 'Můj předmět'; ids.replyBody.value = 'Moje upravená odpověď';
  const count = calls.length;
  await intervals[0]();
  assert.equal(calls.length, count, 'Polling must not overwrite an open editor');
  const submitter = new Element('button');
  await ids.replyForm.listeners.submit({preventDefault() {}, submitter});
  const edit = calls.find(call => call.url.endsWith('/edit'));
  assert.equal(edit.payload.proposal.reply_subject, 'Můj předmět');
  assert.equal(edit.payload.proposal.reply_draft, 'Moje upravená odpověď');
  assert.equal(edit.payload.expected_digest, 'original-digest');
  assert.equal(ids.replyEditor.open, false);
  assert.equal(submitter.disabled, false);
  await find(ids.hours, 'Smazat z Cockpitu').click();
  assert.deepEqual(calls.find(call => call.url.endsWith('/dismiss')).payload.ids, ['low-1','low-2']);
  assert.equal(data.hours.length, 0);
  confirmChoice = false;
  await find(ids.cards, 'Uložit').click();
  assert.equal(calls.filter(call => call.url.endsWith('/archive')).length, 0);
  confirmChoice = true;
  await find(ids.cards, 'Uložit').click();
  assert.equal(calls.filter(call => call.url.endsWith('/archive')).length, 1);
  assert.equal(calls.find(call => call.url.endsWith('/archive')).payload.proposal_digest, 'new-digest');
  assert.equal(data.cards.length, 0);
  assert.equal(calls.some(call => /send|purge|trash/.test(call.url)), false);
  console.log('Email agent frontend: editor, polling, local dismissal and confirmed archive OK');
})().catch(error => { console.error(error); process.exitCode = 1; });
