const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class Element {
  constructor(tag = 'div') {
    this.tag = tag; this.tagName = tag.toUpperCase(); this.children = []; this.listeners = {};
    this.attributes = {}; this.dataset = {}; this.style = {}; this._text = ''; this.value = '';
    this.disabled = false; this.hidden = false; this.open = false; this.isConnected = true;
    this.classList = {add() {}, remove() {}, toggle() {}};
  }
  set textContent(v) { this._text = String(v); this.children = []; }
  get textContent() { return this._text + this.children.map(x => x.textContent || '').join(''); }
  set innerHTML(_) { throw new Error('Render email-derived text with textContent'); }
  append(...items) { for (let x of items) { if (typeof x === 'string') x = {textContent:x}; x.parentNode = this; this.children.push(x); } }
  appendChild(x) { this.append(x); return x; }
  replaceChildren(...items) { this.children = []; this._text = ''; this.append(...items); }
  addEventListener(name, callback) { (this.listeners[name] ||= []).push(callback); }
  setAttribute(k,v) { this.attributes[k] = String(v); }
  getAttribute(k) { return this.attributes[k] ?? null; }
  removeAttribute(k) { delete this.attributes[k]; }
  querySelectorAll(selector) {
    const match = el => selector.split(',').some(part => {
      const token=part.trim().split(/\s+/).pop();
      if(token.startsWith('#')) return el.id===token.slice(1);
      return el.tag===token || (token==='[disabled]' && el.disabled);
    });
    const result=[];
    const walk=el=>{for(const child of el.children||[]){if(match(child))result.push(child);walk(child);}};
    walk(this);return result;
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0]||null; }
  contains(other) { return this===other || this.children.some(x=>x.contains?.(other)); }
  showModal() { this.open = true; }
  close() { this.open = false; }
  focus() {}
  scrollIntoView() {}
  reset() {}
  remove() { if (this.parentNode) this.parentNode.children = this.parentNode.children.filter(x => x !== this); this.isConnected = false; }
  async fire(name, extra={}) { for (const callback of this.listeners[name] || []) await callback({target:this,currentTarget:this,preventDefault(){},...extra}); }
  async click() { if (!this.disabled) await this.fire('click'); }
}
const idsList = ['followupsStatus','followupsActive','followupsCompleted','followupEditor','followupForm',
  'followupTitle','followupGoal','followupNextStep','followupWaitingOn','followupCheckAt',
  'followupSave','followupCancel','followupError','followupVerify'];
const itemID = 'a'.repeat(64), caseID = 'b'.repeat(32);
const clone = x => JSON.parse(JSON.stringify(x));
function find(root, label) {
  if (root.tag === 'button' && root.textContent === label) return root;
  for (const child of root.children || []) { const v = find(child,label); if(v) return v; }
  return null;
}
function stored(fields={}) {
  return {id:caseID, source:{item_id:itemID,thread_binding:'pending'}, title:'Nabídka koupelny',
    goal:'Získat nabídku',next_step:'Čekáme na dodavatele',waiting_on:'other',
    check_at:'2099-01-15T08:00:00+00:00',state:'active',revision:1,generation:1,
    created_at:'2026-11-11T00:00:00+00:00',updated_at:'2026-11-11T00:00:00+00:00',
    completed_at:'',history:[],monitoring:'not_connected',...fields};
}
function server(initial=null) {
  const s={value:initial?clone(initial):null,calls:[],mode:'ok',hold:null,ledger:new Map(),getHold:null};
  s.fetch=async(url,options={}) => {
    assert.ok(url.startsWith('/api/email-agent/followups'), 'UI must not call archive, mail, model or calendar actions');
    const payload=options.body?JSON.parse(options.body):null;
    s.calls.push({url,payload:payload?clone(payload):null});
    const response=(status,value)=>({ok:status===200,status,json:async()=>clone(value)});
    if (!payload) {
      const snapshot={ok:true,version:1,capabilities:{manual_lifecycle:true,automatic_monitoring:!!s.running,monitor_version:s.monitorVersion??1},
        monitor:{configured:!!s.configured},
        active:s.value?.state==='active'?[clone(s.value)]:[],completed:s.value?.state==='completed'?[clone(s.value)]:[]};
      if(s.getHold) await s.getHold;
      if(s.mode==='unavailable') return response(503,{ok:false,error:'unavailable',message:'Zdroj není dostupný.'});
      if(url.includes('?id=')) return s.value?response(200,{ok:true,followup:s.value,
        source_message:s.sourceMissing?null:{header:{sender:'Firma',subject:'<script>Zdroj</script>',date:''},body_text:'<img src=x> Původní zpráva'}}):response(404,{ok:false,error:'not_found'});
      return response(200,snapshot);
    }
    assert.match(payload.operation_id,/^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$/);
    assert.equal(options.method,'POST');
    if(s.hold) await s.hold;
    if(s.mode==='unknown_uncommitted') throw new Error('network interrupted');
    if(s.mode==='unavailable') return response(503,{ok:false,error:'unavailable'});
    if(s.mode==='invalid') return response(400,{ok:false,error:'invalid',message:'Neplatný čas kontroly.'});
    if(s.mode==='conflict') return response(409,{ok:false,error:'conflict',message:'Záležitost se mezitím změnila.'});
    if(s.ledger.has(payload.operation_id)) return response(200,{ok:true,followup:s.value,idempotent_replay:true});
    if(payload.action==='create') {
      assert.deepEqual(Object.keys(payload).sort(),['action','fields','operation_id','source_item_id']);
      assert.equal(payload.source_item_id,itemID);
      assert.deepEqual(Object.keys(payload.fields).sort(),['check_at','goal','next_step','title','waiting_on']);
      assert.ok(!s.value, 'Must open an existing case rather than create a second one');
      s.value=stored(payload.fields);
    } else {
      assert.equal(payload.id,caseID);
      assert.equal(payload.expected_revision,s.value.revision);
      if(payload.action==='update') {
        assert.deepEqual(Object.keys(payload).sort(),['action','expected_revision','fields','id','operation_id']);
        Object.assign(s.value,payload.fields);
      } else if(payload.action==='verify_source') {
        assert.equal(payload.confirmed,true);
        s.value.source.thread_binding='verified_headers';
      } else if(payload.action==='resolve_binding') {
        assert.equal(payload.confirmed,true);
        const event=s.value.observations.reviews[payload.item_id];
        assert.equal(payload.source_digest,event.content_digest);
        event.resolution={decision:payload.decision};
        if(payload.decision==='accept') s.value.observations.items[payload.item_id]={...clone(event),decision:'human_linked'};
        s.value.assessment={status:'manual_review'};
      } else if(['accept_suggestion','reject_suggestion'].includes(payload.action)) {
        assert.equal(payload.confirmed,true);assert.equal(payload.suggestion_id,s.value.suggestion.attempt_id);
        if(payload.action==='accept_suggestion') {
          s.value.next_step=s.value.suggestion.candidate.next_step;
          s.value.waiting_on=s.value.suggestion.candidate.waiting_on;
        }
        s.value.suggestion.status=payload.action==='accept_suggestion'?'accepted':'rejected';
      } else {
        assert.equal(payload.action,'set_state');
        s.value.state=payload.state;s.value.generation++;
        s.value.completed_at=payload.state==='completed'?'2026-11-12T12:00:00Z':'';
        if(payload.check_at) s.value.check_at=payload.check_at;
      }
      s.value.revision++;
    }
    s.value.history.push({operation_id:payload.operation_id,revision:s.value.revision});
    s.ledger.set(payload.operation_id,clone(payload));
    if(s.mode==='unknown_committed') {s.mode='ok';throw new Error('lost response after commit');}
    return response(200,{ok:true,followup:s.value,changed:true,idempotent_replay:false});
  };
  return s;
}
async function boot(s=server(),storage=new Map()) {
  const ids=Object.fromEntries(idsList.map(id=>{
    const tag=id==='followupEditor'?'dialog':id==='followupForm'?'form':
      ['followupSave','followupCancel','followupVerify'].includes(id)?'button':
      id==='followupWaitingOn'?'select':id==='followupCheckAt'||id==='followupTitle'?'input':
      ['followupGoal','followupNextStep'].includes(id)?'textarea':'div';
    const el=new Element(tag);el.id=id;return [id,el];
  }));
  const body=new Element('body');
  body.append(ids.followupsStatus,ids.followupsActive,ids.followupsCompleted,ids.followupEditor);
  ids.followupEditor.append(ids.followupForm);
  ids.followupForm.append(...idsList.slice(5).map(id=>ids[id]));
  const c={document:{getElementById:id=>ids[id]||null,createElement:tag=>new Element(tag),
      createTextNode:text=>({textContent:String(text)}),body,contains:el=>el.isConnected},
    fetch:s.fetch,Date,Intl,Error,JSON,Map,Set,URL,URLSearchParams,Promise,Uint8Array,
    crypto:{getRandomValues:a=>{for(let i=0;i<a.length;i++) a[i]=(++boot.nonce)%256;return a;}},
    sessionStorage:{getItem:k=>storage.get(k)??null,setItem:(k,v)=>storage.set(k,String(v)),removeItem:k=>storage.delete(k)},
    setTimeout,clearTimeout,setInterval:()=>{throw new Error('Use the existing page refresh; no second timer');}};
  c.window=c;c.globalThis=c;
  for(const name of ['followup_time.js','followups.js']) vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../app/frontend/email_agent',name),'utf8'),c);
  assert.ok(c.SamanthaEmailFollowups && typeof c.SamanthaEmailFollowups.refresh==='function','Provide the follow-up UI controller');
  const api=c.SamanthaEmailFollowups;
  await api.refresh();
  const card=new Element('article');body.append(card);
  api.attach(card,{id:itemID,status:'awaiting_confirmation',header:{subject:'<img src=x onerror=alert(1)>',sender:'Firma'},
    proposal:{metadata:{title:'Nabídka koupelny'},summary:'Získat nabídku',reason:'Dodavatel připraví podklady.'}});
  return {ids,api,card,storage,c,s};
}
boot.nonce=0;
const flush=()=>new Promise(resolve=>setImmediate(resolve));
const posts=s=>s.calls.filter(x=>x.payload);
async function open(b) {
  const button=find(b.card,'Hlídat tuto záležitost');assert.ok(button);await button.click();
  assert.equal(b.ids.followupEditor.open,true);assert.equal(b.api.isOpen(),true);
}
function edit(b,values={}) {
  const fields={followupTitle:'Nabídka koupelny',followupGoal:'Nabídka včetně montáže',
    followupNextStep:'Čekáme na dodavatele',followupWaitingOn:'other',followupCheckAt:'2099-01-15T09:00',...values};
  for(const [id,value] of Object.entries(fields)) b.ids[id].value=value;
}
async function submit(b) {await b.ids.followupForm.fire('submit',{submitter:b.ids.followupSave});await flush();}

(async()=>{
  const html=fs.readFileSync(path.join(__dirname,'../app/frontend/email_agent/page.html'),'utf8');
  for(const id of idsList) assert.match(html,new RegExp(`id=["']${id}["']`),`Missing accessible UI element ${id}`);
  assert.match(html,/Hlídané záležitosti/);
  let b=await boot();
  assert.match(b.ids.followupsStatus.textContent,/automatick|ruční/i);
  assert.doesNotMatch(b.ids.followupsStatus.textContent,/právě sleduji|kontroly běží/i);
  const time=b.c.SamanthaFollowupTime;
  assert.equal(time.fromInput('2027-01-15T09:00'),'2027-01-15T08:00:00.000Z');
  assert.equal(time.fromInput('2027-07-15T09:00'),'2027-07-15T07:00:00.000Z');
  assert.throws(()=>time.fromInput('2027-03-28T02:30'));
  assert.throws(()=>time.fromInput('2027-10-31T02:30'));
  await open(b);edit(b);
  await b.ids.followupCancel.click();assert.equal(b.ids.followupEditor.open,false);assert.equal(posts(b.s).length,0);
  await open(b);edit(b,{followupGoal:'Nezahodit rozepsaný cíl'});
  await b.api.refresh();assert.equal(b.ids.followupGoal.value,'Nezahodit rozepsaný cíl');
  await submit(b);
  assert.equal(posts(b.s).length,1);assert.equal(posts(b.s)[0].payload.fields.check_at,'2099-01-15T08:00:00.000Z');
  assert.match(b.ids.followupsActive.textContent,/Nezahodit rozepsaný cíl/);
  assert.equal(b.ids.followupEditor.open,false);
  assert.equal(find(b.card,'Hlídat tuto záležitost'),null);
  assert.ok(find(b.card,'Hlídání'));assert.ok(find(b.card,'Vyřízeno'));
  await find(b.ids.followupsActive,'Vyřízeno').click();await flush();
  assert.equal(b.s.value.state,'completed');assert.match(b.ids.followupsCompleted.textContent,/Nezahodit/);
  assert.equal(b.ids.followupsActive.textContent.includes('Nezahodit'),false);
  await find(b.ids.followupsCompleted,'Hlídání').click();await flush();
  assert.equal(b.ids.followupEditor.open,true,'Reopening must allow a fresh check time');
  b.ids.followupCheckAt.value='2099-01-20T09:00';await submit(b);
  assert.equal(b.s.value.id,caseID);assert.equal(b.s.value.state,'active');
  assert.equal(posts(b.s).filter(x=>x.payload.action==='create').length,1);
  b=await boot(b.s,b.storage);assert.match(b.ids.followupsActive.textContent,/Nezahodit/);
  assert.equal(posts(b.s).filter(x=>x.payload.action==='create').length,1,'Reload never POSTs automatically');

  b=await boot();await open(b);edit(b);
  let release;b.s.hold=new Promise(resolve=>{release=resolve;});
  const saving=submit(b);await flush();await submit(b);
  assert.equal(posts(b.s).length,1,'Double submit has one intent and one POST');
  release();await saving;b.s.hold=null;
  await find(b.ids.followupsActive,'Upravit hlídání').click();edit(b,{followupGoal:'Můj neuložený cíl'});
  b.s.mode='conflict';await submit(b);
  assert.equal(b.ids.followupEditor.open,true);assert.equal(b.ids.followupGoal.value,'Můj neuložený cíl');
  assert.match(b.ids.followupError.textContent,/změnil|reviz|konflikt/i);
  assert.equal(posts(b.s).length,2,'Conflict must not silently retry against a new revision');
  await submit(b);assert.equal(posts(b.s).length,2,'Conflict keeps the old form locked until consciously reopened');
  assert.equal(b.ids.followupSave.disabled,true);

  b=await boot();await open(b);edit(b);b.s.mode='unknown_committed';await submit(b);
  assert.equal(posts(b.s).length,1);assert.ok(b.storage.size,'Persist only the unresolved intent for reload recovery');
  const saved=posts(b.s)[0].payload;
  b=await boot(b.s,b.storage);await flush();
  assert.equal(posts(b.s).length,1,'Recovery reads the existing operation; never repeats the POST');
  assert.equal(b.s.value.history[0].operation_id,saved.operation_id);
  assert.equal(b.storage.size,0,'Confirmed intent is removed from tab storage');
  assert.match(b.ids.followupsActive.textContent,/Nabídka/);

  b=await boot();await open(b);edit(b);b.s.mode='unknown_uncommitted';await submit(b);
  await submit(b);assert.equal(posts(b.s).length,1,'Unknown result cannot become a new intent');
  assert.ok(!b.ids.followupVerify.hidden,'Offer read-only verification');
  await b.ids.followupVerify.click();assert.equal(posts(b.s).length,1,'Verification never writes');

  b=await boot(server(stored({title:'<script>alert(1)</script>'})));
  assert.match(b.ids.followupsActive.textContent,/<script>alert\(1\)<\/script>/);
  await find(b.ids.followupsActive,'Zobrazit zdrojový e-mail').click();
  assert.match(b.ids.followupsActive.textContent,/<img src=x> Původní zpráva/);
  assert.equal(posts(b.s).length,0,'Opening a cached source is read-only');
  b.s.sourceMissing=true;await find(b.ids.followupsActive,'Zobrazit zdrojový e-mail').click();
  assert.match(b.ids.followupsActive.textContent,/není dostupný/);
  assert.doesNotMatch(b.ids.followupsActive.textContent,/Původní zpráva/,'Unavailable source must not display a stale replacement');
  b.s.mode='unavailable';await b.api.refresh();
  assert.match(b.ids.followupsStatus.textContent,/nedostup|nepodař|ověř|chyba|nelze/i);
  assert.match(b.ids.followupsActive.textContent,/<script>/,'Unavailable refresh retains the last known list');

  b=await boot();await open(b);edit(b,{followupCheckAt:''});await submit(b);
  assert.equal(posts(b.s).length,0,'A missing time cannot silently acquire a default');
  edit(b,{followupCheckAt:'2020-01-15T09:00'});await submit(b);
  assert.equal(posts(b.s).length,0,'Creating an already expired control is rejected before POST');
  edit(b);b.s.mode='invalid';await submit(b);
  assert.equal(b.ids.followupEditor.open,true);assert.equal(b.storage.size,0);
  assert.equal(b.ids.followupGoal.value,'Nabídka včetně montáže');
  b.s.mode='ok';await submit(b);assert.equal(b.s.value.state,'active','A definite rejection allows a corrected explicit save');

  b=await boot();await open(b);edit(b);b.s.mode='unavailable';await submit(b);
  const unresolved=JSON.parse([...b.storage.values()][0]);
  assert.deepEqual(Object.keys(unresolved).sort(),['operation_id','source_item_id']);
  assert.doesNotMatch(JSON.stringify(unresolved),/Nabídka|montáže|2099/,'Tab storage contains no email content or form text');
  b.s.mode='ok';await b.ids.followupVerify.click();await submit(b);
  assert.equal(posts(b.s).length,1,'A 503 after submission remains uncertain, never a new write');

  b=await boot();await open(b);edit(b);
  b.c.sessionStorage.setItem=()=>{throw new Error('storage disabled');};await submit(b);
  assert.equal(posts(b.s).length,0,'Failure to durably record intent prevents POST');

  b=await boot(server(stored()));
  let resolveRead;b.s.getHold=new Promise(resolve=>{resolveRead=resolve;});
  const staleRead=b.api.refresh();await flush();
  await find(b.ids.followupsActive,'Vyřízeno').click();assert.equal(b.s.value.state,'completed');
  resolveRead();await staleRead;b.s.getHold=null;
  assert.equal(find(b.ids.followupsActive,'Vyřízeno'),null,'A read begun before mutation cannot resurrect the active case');
  assert.match(b.ids.followupsCompleted.textContent,/Nabídka/);

  b=await boot(server(stored()));
  await find(b.ids.followupsActive,'Upravit hlídání').click();await submit(b);
  assert.equal(posts(b.s).length,0,'Unchanged edits need no write or uncertain no-op receipt');
  assert.equal(b.ids.followupEditor.open,false);

  const corrupted=new Map([['samantha.email.followup.intent.v1','not json']]);
  b=await boot(server(),corrupted);await find(b.card,'Hlídat tuto záležitost').click();
  assert.equal(b.ids.followupEditor.open,false);assert.equal(posts(b.s).length,0,'Malformed recovery state is not discarded to allow a second intent');
  b=await boot(server(stored({tracking:{status:'source_unverified',last_checked_at:'2026-11-12T09:00:00Z',
    last_verified_at:'2026-11-12T08:00:00Z',next_check_slot:'2026-11-12T10:00:00Z'}})));
  assert.match(b.ids.followupsActive.textContent,/nelze dokončit/);
  b.s.running=true;b.s.configured=true;await b.api.refresh();
  assert.match(b.ids.followupsStatus.textContent,/Hodinová kontrola běží/);
  assert.match(b.ids.followupsActive.textContent,/Poslední ověření zdroje/);
  const verify=find(b.ids.followupsActive,'Ověřit původní e-mail pro párování');assert.ok(verify);
  b.s.mode='unknown_committed';await verify.click();
  assert.equal(posts(b.s).length,1);assert.equal(posts(b.s)[0].payload.action,'verify_source');
  assert.equal(b.ids.followupEditor.open,true);await b.ids.followupVerify.click();
  assert.equal(posts(b.s).length,1,'Recovery reads the original verification receipt without a second source operation');
  assert.equal(b.ids.followupEditor.open,false);assert.equal(b.storage.size,0);

  const relatedID='c'.repeat(64);
  b=await boot(server(stored({source:{item_id:itemID,thread_binding:'verified_headers'},
    observations:{items:{[relatedID]:{observed_at:'2026-11-12T09:00:00Z'}},reviews:{}}})));
  const relatedCard=new Element('article');b.c.document.body.append(relatedCard);
  b.api.attach(relatedCard,{id:relatedID,status:'awaiting_confirmation'});
  assert.equal(find(relatedCard,'Hlídat tuto záležitost'),null,'Bound reply opens the existing matter');
  assert.match(relatedCard.textContent,/Záležitost/);
  const sourceButton=b.ids.followupsActive.querySelectorAll('button').find(x=>x.textContent.startsWith('Související zpráva'));
  await sourceButton.click();assert.ok(b.s.calls.at(-1).url.includes('&item_id='+relatedID));
  assert.match(b.ids.followupsActive.textContent,/<img src=x>/);

  b.s.running=true;b.s.monitorVersion=99;await b.api.refresh();
  assert.match(b.ids.followupsStatus.textContent,/nelze ověřit/);
  assert.equal(find(b.ids.followupsActive,'Vyřízeno').disabled,true,'Unknown running protocol cannot authorize writes');

  const suggestion={attempt_id:'d'.repeat(64),status:'pending',source_item_id:relatedID,generation:1,
    candidate:{kind:'review_completion',next_step:'Posoudit nabídku a případné vyřízení.',waiting_on:'review',
      reason:'<script>Reason</script>',evidence:[{source:'body',quote:'<img src=x> Doložený podklad'}],uncertainties:['Ověřit přílohu.']}};
  const proposed=stored({suggestion,observations:{items:{[relatedID]:{observed_at:'2026-11-12T09:00:00Z'}},reviews:{}}});
  b=await boot(server(proposed));const originalGoal=b.s.value.goal, originalCheck=b.s.value.check_at;
  assert.match(b.ids.followupsActive.textContent,/Návrh posoudit vyřízení/);
  assert.match(b.ids.followupsActive.textContent,/<script>Reason<\/script>/);
  assert.equal(posts(b.s).length,0,'Rendering a model suggestion performs no action');
  await find(b.ids.followupsActive,'Převzít další krok').click();
  assert.equal(b.s.value.state,'active','Accepting the next step cannot complete a matter');
  assert.equal(b.s.value.goal,originalGoal);assert.equal(b.s.value.check_at,originalCheck);
  assert.equal(b.s.value.next_step,suggestion.candidate.next_step);
  assert.equal(posts(b.s)[0].payload.action,'accept_suggestion');

  b=await boot(server(proposed));await find(b.ids.followupsActive,'Upravit navržený krok').click();
  assert.equal(b.ids.followupNextStep.value,suggestion.candidate.next_step);
  b.ids.followupNextStep.value='Můj ručně upřesněný krok';await submit(b);
  assert.equal(posts(b.s)[0].payload.action,'update');assert.equal(b.s.value.next_step,'Můj ručně upřesněný krok');

  b=await boot(server(proposed));b.s.mode='unknown_committed';await find(b.ids.followupsActive,'Odmítnout návrh').click();
  await b.ids.followupVerify.click();assert.equal(posts(b.s).length,1,'Lost suggestion decision is only read back');
  assert.equal(b.s.value.suggestion.status,'rejected');assert.equal(b.s.value.next_step,proposed.next_step);

  const event={generation:1,content_digest:'e'.repeat(64),observed_at:'2026-11-12T09:00:00Z'};
  const review=stored({observations:{items:{},reviews:{[relatedID]:event}}});
  b=await boot(server(review));await find(b.ids.followupsActive,'Patří k této záležitosti').click();
  assert.equal(posts(b.s)[0].payload.action,'resolve_binding');assert.equal(posts(b.s)[0].payload.decision,'accept');
  assert.equal(b.s.value.goal,review.goal);assert.equal(b.s.value.state,'active');
  assert.equal(find(b.ids.followupsActive,'Patří k této záležitosti'),null);
  b=await boot(server(review));b.s.mode='unknown_committed';await find(b.ids.followupsActive,'Nesouvisí').click();
  await b.ids.followupVerify.click();assert.equal(posts(b.s).length,1);
  assert.equal(b.s.value.observations.reviews[relatedID].resolution.decision,'reject');

  b=await boot(server({...proposed,suggestion:{...suggestion,status:'stale'}}));
  assert.equal(find(b.ids.followupsActive,'Převzít další krok'),null);
  assert.match(b.ids.followupsActive.textContent,/starších podkladů/);
  console.log('Follow-up UI: lifecycle/recovery, source binding, related read, truthful worker state and no second timer OK');
})().catch(error=>{console.error(error);process.exitCode=1;});
