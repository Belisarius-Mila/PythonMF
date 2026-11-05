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
    'closeEditor','status','notice','cards','hours','archived','replyConfirmation','replyQuestion','replySender',
    'reallySendReply','backToReply','prepareReplySend','saveReplyDraft','importancePreferences',
    'pushcutForm','pushcutCockpitUrl','pushcutWebhook','pushcutEnabled','savePushcut','testPushcut',
    'pushcutStatus','pushcutTestStatus'].map(id => [id, new Element(id)]));
  const metadata = {title: 'Podklady', domain: 'work', document_type: 'email', counterparty: 'Firma', tags: ['schůzka']};
  const data = {schedule: {}, sources: [], assessment_errors: 0, archived: [], importance_preferences: [],
    cards: [{id: 'important', header: {subject: '<img src=x onerror=alert(1)>', sender: 'Firma', date: '4. 11.'},
      created_at: '2026-11-04', status: 'awaiting_confirmation', proposal_digest: 'original-digest',
      message: {body_text: 'CELÉ TĚLO A KONEC'}, proposal: {summary: 'Schůzka', reason: 'Je třeba odpověď',
        metadata, reply_subject: 'Re: Schůzka', reply_draft: 'Potvrzuji účast.'}}],
    hours: [{text: '18:00: Firma — Reklama', ids: ['low-1','low-2'], messages: [
      {id: 'low-1', text: 'Firma — Reklama'}, {id: 'low-2', text: '<script> — Jiné novinky'}]}]};
  const calls = [], intervals = [];
  let confirmChoice = true;
  let preparationCount = 0;
  let preparationHold = null;
  let pushcutHold = null;
  const context = {document: {getElementById: id => ids[id], createElement: tag => new Element(tag)},
    window: {setInterval: fn => intervals.push(fn), confirm: () => confirmChoice},
    fetch: async (url, options) => {
      const payload = options?.body ? JSON.parse(options.body) : null;
      calls.push({url, payload});
      if (url.endsWith('/pushcut/configure')) data.pushcut = {
        enabled: payload.enabled, configured: true, cockpit_url: payload.cockpit_url, counts: {}
      };
      if (url.endsWith('/pushcut/test')) {
        if (pushcutHold) await pushcutHold;
        return {ok: true, json: async () => ({ok: true, status: 'accepted'})};
      }
      if (url.endsWith('/edit')) { data.cards[0].proposal = payload.proposal; data.cards[0].proposal_digest = 'new-digest'; }
      if (url.endsWith('/prepare-reply')) {
        if (preparationHold) await preparationHold;
        preparationCount += 1;
        return {ok: true, json: async () => ({ok: true, prepared: {
          recipient_name: 'Firma', recipient: 'reply@example.test', sender: 'owner@example.test',
          subject: data.cards[0].proposal.reply_subject, body: data.cards[0].proposal.reply_draft,
          confirmation_token: `token-${preparationCount}`, confirmation_digest: `digest-${preparationCount}`
        }})};
      }
      if (url.endsWith('/send-reply')) data.cards[0].reply = {status: 'smtp_sent'};
      if (url.endsWith('/remember-importance')) data.importance_preferences = [{id: 'pref-1',
        sender: 'sender@example.test', subject: data.cards[0].header.subject}];
      if (url.endsWith('/forget-importance')) data.importance_preferences = [];
      if (url.endsWith('/dismiss')) data.hours = [];
      if (url.endsWith('/archive')) { data.archived.push(data.cards.pop()); }
      const result = url.endsWith('/overview') ? {ok: true, ...data} : url.endsWith('/edit')
        ? {ok: true, proposal_digest: 'new-digest'} : url.endsWith('/send-reply')
        ? {ok: true, receipt: {status: 'smtp_sent', sent_copy_status: 'saved'}} : {ok: true};
      return {ok: true, json: async () => JSON.parse(JSON.stringify(result))};
    }, Date, Error, JSON};
  const source = fs.readFileSync(path.join(__dirname, '../app/frontend/email_agent/app.js'), 'utf8');
  vm.runInNewContext(source, context);
  const flush = () => new Promise(resolve => setImmediate(resolve));
  await flush();
  assert.match(ids.cards.textContent, /CELÉ TĚLO A KONEC/);
  assert.match(ids.cards.textContent, /<img src=x onerror=alert\(1\)>/);
  await find(ids.cards, 'Příště nedůležité').click();
  assert.equal(data.cards.length, 1, 'Preference must not dismiss the current card');
  assert.equal(calls.some(call => /dismiss|archive|send-reply/.test(call.url)), false);
  assert.deepEqual(calls.find(call => call.url.endsWith('/remember-importance')).payload, {id: 'important'});
  assert.match(ids.importancePreferences.textContent, /sender@example.test/);
  assert.match(ids.importancePreferences.textContent, /<img src=x onerror=alert\(1\)>/);
  await find(ids.importancePreferences, 'Zrušit preferenci').click();
  assert.deepEqual(calls.find(call => call.url.endsWith('/forget-importance')).payload, {id: 'pref-1'});
  assert.equal(data.cards.length, 1);
  assert.equal(data.importance_preferences.length, 0);
  const hourBefore = JSON.stringify(data.hours);
  assert.match(ids.hours.textContent, /Příště nedůležité…/);
  assert.match(ids.hours.textContent, /<script> — Jiné novinky/);
  await find(ids.hours, 'Příště nedůležité').click();
  assert.deepEqual(calls.filter(call => call.url.endsWith('/remember-importance')).at(-1).payload, {id: 'low-1'});
  assert.equal(JSON.stringify(data.hours), hourBefore, 'Preference preserves the complete hourly row');
  assert.equal(calls.some(call => /dismiss|archive|send-reply/.test(call.url)), false);
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
  await find(ids.cards, 'Upravit odpověď').click();
  ids.replyBody.value = 'Text ke skutečnému druhému potvrzení';
  let releasePreparation;
  preparationHold = new Promise(resolve => { releasePreparation = resolve; });
  const preparing = ids.prepareReplySend.click();
  await flush();
  assert.equal(ids.closeEditor.disabled, true);
  let preventedCancel = false;
  ids.replyEditor.listeners.cancel({preventDefault() { preventedCancel = true; }});
  assert.equal(preventedCancel, true);
  await ids.closeEditor.click();
  assert.equal(ids.replyEditor.open, true);
  releasePreparation(); await preparing; preparationHold = null;
  assert.equal(calls.filter(call => call.url.endsWith('/send-reply')).length, 0);
  assert.equal(ids.replyConfirmation.hidden, false);
  assert.match(ids.replyQuestion.textContent, /reply@example.test/);
  assert.match(ids.replySender.textContent, /owner@example.test/);
  assert.equal(ids.replyBody.readOnly, true);
  await ids.backToReply.click();
  assert.equal(ids.replyBody.readOnly, false);
  ids.replyBody.value = 'Ještě upravený konečný text';
  await ids.prepareReplySend.click();
  await ids.reallySendReply.click();
  await ids.reallySendReply.click();
  const sent = calls.filter(call => call.url.endsWith('/send-reply'));
  assert.equal(sent.length, 1);
  assert.equal(sent[0].payload.confirmed, true);
  assert.equal(sent[0].payload.confirmation_token, 'token-2');
  assert.equal(sent[0].payload.confirmation_digest, 'digest-2');
  assert.equal(data.cards[0].proposal.reply_draft, 'Ještě upravený konečný text');
  assert.equal(ids.replyEditor.open, false);
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
  assert.equal(calls.some(call => /purge|trash/.test(call.url)), false);
  ids.pushcutWebhook.value = 'https://api.pushcut.io/browser-test-secret/notifications/SamanthaEmail';
  ids.pushcutCockpitUrl.value = 'https://synthetic.example.test/emails-to-resolve/';
  ids.pushcutEnabled.checked = true;
  ids.pushcutWebhook.listeners.input({});
  await intervals[0]();
  assert.equal(ids.pushcutEnabled.checked, true, 'Polling preserves unsaved notification choices');
  assert.match(ids.pushcutWebhook.value, /browser-test-secret/);
  await ids.testPushcut.click();
  assert.equal(calls.filter(call => call.url.endsWith('/pushcut/test')).length, 0, 'Save changes before testing');
  await ids.pushcutForm.listeners.submit({preventDefault() {}});
  const configuration = calls.find(call => call.url.endsWith('/pushcut/configure'));
  assert.equal(configuration.payload.enabled, true);
  assert.equal(ids.pushcutWebhook.value, '', 'Saved webhook is never returned to the field');
  let releasePushcut;
  pushcutHold = new Promise(resolve => { releasePushcut = resolve; });
  const testing = ids.testPushcut.click();
  await flush(); await ids.testPushcut.click();
  assert.equal(calls.filter(call => call.url.endsWith('/pushcut/test')).length, 1, 'Double click sends one test');
  releasePushcut(); await testing;
  const testCall = calls.find(call => call.url.endsWith('/pushcut/test'));
  assert.equal(testCall.payload.confirmed, true);
  assert.match(testCall.payload.request_id, /^[a-z0-9_]{8,100}$/);
  assert.match(ids.pushcutTestStatus.textContent, /Pushcut test přijal/);
  console.log('Email agent frontend: editor, polling, two-step reply, dismissal and archive OK');
})().catch(error => { console.error(error); process.exitCode = 1; });
