const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

class Element {
  constructor(tag) { this.tag = tag; this.children = []; this.listeners = {}; this.dataset = {}; this.value = ''; this.disabled = false; this._text = ''; this._html = ''; this.classList = {toggle(){},add(){},remove(){}}; }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(''); }
  set innerHTML(value) { this._html = value; this.children = []; this._text = ''; this.deleteButtons = null; }
  get innerHTML() { return this._html; }
  append(...nodes) { this.children.push(...nodes); }
  appendChild(node) { this.children.push(node); }
  replaceChildren(...nodes) { this.children = nodes; this._text = ''; }
  addEventListener(name, handler) { this.listeners[name] = handler; }
  setAttribute(name, value) { this[name] = value; }
  querySelector(selector) { return selector === 'button' ? (this.button ||= new Element('button')) : null; }
  querySelectorAll(selector) {
    if (selector === '[data-delete-source]' || selector === 'input,button') {
      this.deleteButtons ||= [...this._html.matchAll(/data-delete-source="([^"]+)"/g)].map(match => {
        const button = new Element('button'); button.dataset.deleteSource = match[1]; return button;
      });
      return [...this.deleteButtons, ...(selector === 'input,button' ? this.children.filter(c=>c.tag==='button') : [])];
    }
    return [];
  }
  showModal() { this.open = true; }
  close() { this.open = false; }
  async click() { if (!this.disabled) await this.listeners.click?.({preventDefault(){}}); }
}

const clone = value => JSON.parse(JSON.stringify(value));
const flush = async () => { for (let i=0;i<10;i++) await new Promise(resolve => setImmediate(resolve)); };
function fixture({variants = {}, initial = null, cachedDraft = null} = {}) {
  const page = fs.readFileSync(path.join(__dirname, '../app/frontend/interior/page.html'),'utf8');
  const ids = Object.fromEntries([...page.matchAll(/id="([^"]+)"/g)].map(m => [m[1], new Element(m[1])]));
  const cache = new Map(), intervals = [], calls = [], paid = new Set();
  if (initial) cache.set('samantha-interior-selection-v1',JSON.stringify(initial));
  if (cachedDraft) cache.set('samantha-interior-draft-v1:project:A:dead',JSON.stringify(cachedDraft));
  const jobs = {A:[],B:[]};
  const draft = {title:'Saved title',prompt:'Keep the room',fixed_elements:'Door',source_ids:['photo'],image_source_id:'photo',annotations:[],revision:2};
  let sequence = 0, holdStart = null, holdStatusA = null, throwStart = false, holdDelete = null, throwDelete = false, deleted = false;
  const deletedRequests = new Set();
  const confirmation = 'Potvrzuji globální brzdu: rozumím riziku a chci pokračovat.';
  function room(id) { return {id,title:'Room '+id,sources:deleted?{}:{photo:{id:'photo',title:'Private photo',kind:'photo'}},variants,notes:[]}; }
  const projects = [{id:'project',title:'Private project',rooms:[{id:'A',title:'A'},{id:'B',title:'B'}]}];
  const context = {document:{getElementById:id=>ids[id],createElement:tag=>new Element(tag)},
    localStorage:{getItem:k=>cache.get(k)??null,setItem:(k,v)=>cache.set(k,v),removeItem:k=>cache.delete(k)},
    crypto:{randomUUID:()=>`synthetic-request-${++sequence}`},URLSearchParams,console,confirm:()=>true,
    setInterval:fn=>intervals.push(fn),
    fetch:async (url, options) => {
      const payload = options?.body ? JSON.parse(options.body) : null;
      calls.push({url,payload});
      let result;
      if (url.startsWith('/api/interior/state')) {
        const selected = new URLSearchParams(url.split('?')[1]).get('room_id');
        result={ok:true,projects,room:selected?room(selected):null,draft:selected?clone(draft):null};
      } else if (url.startsWith('/api/interior/delete-preview?')) {
        result={ok:true,asset_id:'photo',title:'<img src=x onerror=evil()>',bytes:12345,file_count:3,
          shared_file_count:0,variant_count:1,draft_count:1,plan_token:'d'.repeat(64),confirmation_text:confirmation};
      } else if (url.startsWith('/api/interior/ai/status')) {
        const selected=new URLSearchParams(url.split('?')[1]).get('room_id');
        const captured=clone(jobs[selected]);
        if (selected==='A' && holdStatusA) await holdStatusA;
        result={ok:true,enabled:true,image_generation:true,model:'approved-model',jobs:captured,
          brief:{changes:draft.prompt,preserve:draft.fixed_elements,unresolved:[],revision:draft.revision,
            working_image:'Private photo',source_count:1,drawing_count:0,can_generate:true,token:'review-'+draft.revision}};
      } else if (url==='/api/interior/action') {
        if (payload.action==='delete_source') {
          assert.equal(payload.confirmation,confirmation);
          assert.equal(payload.plan_token,'d'.repeat(64));
          if (!deletedRequests.has(payload.request_id)) {
            deletedRequests.add(payload.request_id); deleted=true;
            draft.source_ids=[];draft.image_source_id='';draft.annotations=[];draft.revision++;
            for (const variant of Object.values(variants)) {
              variant.source_ids = (variant.source_ids || []).filter(id => id !== 'photo');
              if (variant.image_source_id === 'photo') { variant.image_source_id = ''; variant.annotations = []; }
            }
          }
          if (holdDelete) await holdDelete;
          if (throwDelete) { throwDelete=false;throw new Error('Network outcome unknown'); }
          result={ok:true,deleted_bytes:12345};
        } else {
          assert.equal(payload.action,'save_draft');
          Object.assign(draft,clone(payload.draft));draft.revision++;
          result={ok:true,revision:draft.revision};
        }
      } else if (url==='/api/interior/ai/start') {
        if (!paid.has(payload.request_id)) {
          paid.add(payload.request_id);
          jobs[payload.room_id].push({id:'job-'+payload.request_id,client_request_id:payload.request_id,
            message:payload.message,status:'queued',answer:'',variant_id:'',created_at:'now'});
        }
        if (holdStart) await holdStart;
        if (throwStart) { throwStart=false; throw new Error('Network outcome unknown'); }
        result={ok:true,request_id:'job-'+payload.request_id};
      } else throw new Error('Unexpected endpoint '+url);
      return {ok:true,json:async()=>clone(result)};
    }};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../app/frontend/interior/app.js'),'utf8'),context);
  return {ids,calls,cache,jobs,intervals,paid,deletedRequests,confirmation,variants,draft,
    setHoldDelete:p=>holdDelete=p,setThrowDelete:()=>throwDelete=true,
    setHoldStart:p=>holdStart=p,setHoldStatusA:p=>holdStatusA=p,setThrowStart:()=>throwStart=true};
}

test('double AI submission produces one request; completed text stays plain and draft polling is preserved',async()=>{
  const f=fixture();await flush();
  assert.equal(f.ids.askArchitect.disabled,false);
  assert.match(f.ids.aiSources.textContent,/1/);
  f.ids.aiText.value='Describe selected photos';
  let release;f.setHoldStart(new Promise(resolve=>release=resolve));
  f.ids.aiForm.listeners.submit({preventDefault(){}});await flush();
  assert.equal(f.ids.projectSelect.disabled,true,'Scope cannot change while preparing the request');
  f.ids.aiForm.listeners.submit({preventDefault(){}});await flush();
  assert.equal(f.calls.filter(c=>c.url.endsWith('/ai/start')).length,1);
  release();await flush();f.setHoldStart(null);
  assert.equal(f.ids.askArchitect.disabled,true,'Queued request blocks another paid send');
  f.ids.draftTitle.value='My newer unfinished draft';f.ids.draftTitle.listeners.input();
  f.jobs.A[0].status='completed';f.jobs.A[0].answer='<img src=x onerror=evil()> Architect answer';
  f.intervals[0]();await flush();
  assert.match(f.ids.aiConversation.textContent,/<img src=x onerror=evil\(\)> Architect answer/);
  assert.equal(f.ids.aiConversation.children[0].children[1].tag,'p');
  assert.equal(f.ids.draftTitle.value,'My newer unfinished draft');
  assert.equal(f.ids.askArchitect.disabled,false);
  assert.equal(f.paid.size,1);
});

test('late AI status from room A cannot enter room B conversation',async()=>{
  const f=fixture();await flush();
  f.jobs.A.push({id:'old',message:'ROOM_A_PRIVATE',answer:'A answer',status:'completed',created_at:'old'});
  let release;f.setHoldStatusA(new Promise(resolve=>release=resolve));
  f.intervals[0]();await flush();
  f.ids.roomSelect.value='B';f.ids.roomSelect.listeners.change();await flush();
  release();await flush();
  assert.doesNotMatch(f.ids.aiConversation.textContent,/ROOM_A_PRIVATE/);
  assert.equal(f.calls.filter(c=>c.url.endsWith('/ai/start')).length,0);
});

test('unknown HTTP outcome is reconciled by status without another model request',async()=>{
  const f=fixture();await flush();
  f.ids.aiText.value='Question with uncertain HTTP';f.setThrowStart();
  f.ids.aiForm.listeners.submit({preventDefault(){}});await flush();
  assert.equal(f.ids.checkAISend.hidden,false);
  assert.equal(f.ids.askArchitect.disabled,true);
  f.intervals[0]();await flush();
  assert.equal(f.ids.checkAISend.hidden,true,'Original durable request was found');
  assert.equal(f.calls.filter(c=>c.url.endsWith('/ai/start')).length,1);
  assert.equal(f.paid.size,1);
});

test('all verified outputs can be opened without another generation request',async()=>{
  const f=fixture();await flush();
  f.jobs.A.push({id:'verified',message:'One image request',status:'completed',answer:'Two verified variants',
    variant_id:'variant-1',variant_ids:['variant-1','variant-2'],output_count:2,created_at:'now'});
  f.intervals[0]();await flush();
  const buttons=f.ids.aiConversation.children[0].children.filter(node=>node.tag==='button');
  assert.deepEqual(buttons.map(node=>node.textContent),['Otevřít AI návrh 1','Otevřít AI návrh 2']);
  await buttons[1].click();await flush();
  assert.ok(f.calls.some(call=>call.url.includes('/api/interior/state?')&&call.url.includes('base_id=variant-2')));
  assert.equal(f.paid.size,0);
});

test('opening and cancelling source deletion is read-only and renders the private title as text',async()=>{
  const f=fixture();await flush();
  await f.ids.sourceList.querySelectorAll('[data-delete-source]')[0].click();await flush();
  assert.equal(f.ids.deleteDialog.open,true);
  assert.equal(f.ids.confirmDelete.disabled,true);
  assert.match(f.ids.deleteTitle.textContent,/<img src=x onerror=evil\(\)>/);
  assert.equal(f.ids.deleteTitle.innerHTML,'');
  await f.ids.cancelDelete.click();
  assert.equal(f.ids.deleteDialog.open,false);
  assert.equal(f.calls.filter(c=>c.payload?.action==='delete_source').length,0);
  assert.equal(f.paid.size,0);
});

test('exact confirmation is required; double submit deletes once and preserves unsaved text',async()=>{
  const f=fixture();await flush();
  f.ids.draftTitle.value='My unfinished text';f.ids.draftTitle.listeners.input();
  await f.ids.sourceList.querySelectorAll('[data-delete-source]')[0].click();await flush();
  await f.ids.deleteForm.listeners.submit({preventDefault(){}});
  assert.equal(f.deletedRequests.size,0);
  f.ids.deleteConfirmation.value=f.confirmation;f.ids.deleteConfirmation.listeners.input();
  assert.equal(f.ids.confirmDelete.disabled,false);
  let release;f.setHoldDelete(new Promise(resolve=>release=resolve));
  f.ids.deleteForm.listeners.submit({preventDefault(){}});await flush();
  f.ids.deleteForm.listeners.submit({preventDefault(){}});await flush();
  assert.equal(f.calls.filter(c=>c.payload?.action==='delete_source').length,1);
  assert.equal(f.ids.cancelDelete.disabled,true);
  release();await flush();
  assert.equal(f.ids.deleteDialog.open,false);
  assert.equal(f.ids.draftTitle.value,'My unfinished text');
  assert.equal(f.ids.sourceList.querySelectorAll('[data-delete-source]').length,0);
  assert.equal(f.paid.size,0);
});

test('uncertain delete response never automatically retries and explicit completion reuses the request ID',async()=>{
  const f=fixture();await flush();
  await f.ids.sourceList.querySelectorAll('[data-delete-source]')[0].click();
  f.ids.deleteConfirmation.value=f.confirmation;f.ids.deleteConfirmation.listeners.input();
  f.setThrowDelete();await f.ids.deleteForm.listeners.submit({preventDefault(){}});await flush();
  assert.equal(f.ids.deleteDialog.open,true);
  assert.match(f.ids.deleteError.textContent,/není potvrzené/);
  assert.equal(f.calls.filter(c=>c.payload?.action==='delete_source').length,1);
  await f.ids.deleteForm.listeners.submit({preventDefault(){}});await flush();
  const deletes=f.calls.filter(c=>c.payload?.action==='delete_source');
  assert.equal(deletes.length,2);
  assert.equal(deletes[0].payload.request_id,deletes[1].payload.request_id);
  assert.equal(f.deletedRequests.size,1);
  assert.equal(f.ids.deleteDialog.open,false);
  assert.equal(f.paid.size,0);
});

const proposal = (id,image,kind='ai_proposal',parent=null) => ({id,title:id,kind,parent_id:parent,
  image_source_id:image,source_ids:image?[image]:[],annotations:[],prompt:'Retained text'});

test('deleted AI thumbnails and conversation links disappear while text-only human proposals and new outputs remain',async()=>{
  const f=fixture({variants:{dead:proposal('dead',''),live:proposal('live','photo'),human:proposal('human','','human_proposal')}});
  await flush();
  assert.doesNotMatch(f.ids.variants.innerHTML,/data-variant="dead"/);
  assert.match(f.ids.variants.innerHTML,/data-variant="live"/);
  assert.match(f.ids.variants.innerHTML,/data-variant="human"/);
  assert.doesNotMatch(f.ids.variants.innerHTML,/class="placeholder"/,'Text-only human proposals have a label without an empty image frame');
  f.jobs.A.push({id:'history',message:'Earlier outputs',status:'completed',answer:'Saved',variant_ids:['dead','live','fresh'],created_at:'now'});
  f.intervals[0]();await flush();
  const buttons=f.ids.aiConversation.children[0].children.filter(c=>c.tag==='button');
  assert.equal(buttons.length,2);
  await buttons[1].click();await flush();
  assert.ok(f.calls.some(c=>c.url.includes('base_id=fresh')),'New outputs absent from an older room snapshot still open');
  assert.equal(f.variants.dead.prompt,'Retained text');
  assert.equal(f.paid.size,0);
});

test('remembered deleted AI selection falls back to the base without removing its cached unfinished text',async()=>{
  const orphanCache={draft:{title:'Unfinished',prompt:'Keep my text',fixed_elements:'',image_source_id:'',source_ids:[],annotations:[]},revision:3,dirty:true};
  const f=fixture({variants:{dead:proposal('dead','')},initial:{project:'project',room:'A',base:'dead'},cachedDraft:orphanCache});
  await flush();
  assert.equal(JSON.parse(f.cache.get('samantha-interior-selection-v1')).base,'base');
  assert.match(f.ids.variantTitle.textContent,/Saved title/);
  assert.doesNotMatch(f.ids.variants.innerHTML,/data-variant="dead"/);
  assert.equal(JSON.parse(f.cache.get('samantha-interior-draft-v1:project:A:dead')).draft.prompt,'Keep my text');
  assert.equal(f.calls.filter(c=>c.payload).length,0);
});

test('deleting the selected AI image immediately removes its thumbnail and selection',async()=>{
  const f=fixture({variants:{live:proposal('live','photo')},initial:{project:'project',room:'A',base:'live'}});
  await flush();
  await f.ids.sourceList.querySelectorAll('[data-delete-source]')[0].click();
  f.ids.deleteConfirmation.value=f.confirmation;f.ids.deleteConfirmation.listeners.input();
  await f.ids.deleteForm.listeners.submit({preventDefault(){}});await flush();
  assert.doesNotMatch(f.ids.variants.innerHTML,/data-variant="live"/);
  assert.equal(JSON.parse(f.cache.get('samantha-interior-selection-v1')).base,'base');
  assert.equal(f.variants.live.prompt,'Retained text');
  assert.equal(f.deletedRequests.size,1);
  assert.equal(f.paid.size,0);
});

test('surviving AI child stays usable but cannot compare against its deleted parent image',async()=>{
  const f=fixture({variants:{dead:proposal('dead',''),child:proposal('child','photo','ai_proposal','dead')},initial:{project:'project',room:'A',base:'child'}});
  await flush();
  assert.equal(f.ids.compare.disabled,true);
  assert.match(f.ids.visual.innerHTML,/<img/);
  assert.doesNotMatch(f.ids.visual.innerHTML,/compare-grid/);
  assert.equal(JSON.parse(f.cache.get('samantha-interior-selection-v1')).base,'child');
});


test('image approval pins displayed brief without saving again and excludes an unsent conversation',async()=>{
  const f=fixture();await flush();
  assert.equal(f.ids.draftPrompt,undefined);assert.equal(f.ids.draftFixed,undefined);
  assert.equal(f.ids.briefChanges.textContent,'Keep the room');
  assert.equal(f.ids.generateProposal.disabled,false);
  f.ids.aiText.value='What if we moved the door?';f.ids.aiText.listeners.input();
  assert.equal(f.ids.generateProposal.disabled,true);
  await f.ids.generateProposal.click();assert.equal(f.paid.size,0);
  f.ids.aiText.value='';f.ids.aiText.listeners.input();
  await f.ids.generateProposal.click();await flush();
  const sends=f.calls.filter(c=>c.url==='/api/interior/ai/start');
  assert.equal(sends.length,1);assert.equal(sends[0].payload.brief_protocol,'interior-brief-v1');
  assert.equal(sends[0].payload.brief_token,'review-2');
  assert.equal(sends[0].payload.expected_revision,2);
  assert.equal(f.calls.filter(c=>c.payload?.action==='save_draft').length,0);
});

test('architect revision refresh preserves an unsent question and does not overwrite dirty local edits',async()=>{
  const f=fixture();await flush();
  f.ids.aiText.value='Unsent question';f.ids.aiText.listeners.input();
  f.draft.prompt='Architect summary';f.draft.revision++;
  f.intervals[0]();await flush();
  assert.equal(f.ids.briefChanges.textContent,'Architect summary');
  assert.equal(f.ids.aiText.value,'Unsent question');
  f.ids.draftTitle.value='Local title';f.ids.draftTitle.listeners.input();
  f.draft.title='Server title';f.draft.revision++;
  f.intervals[0]();await flush();
  assert.equal(f.ids.draftTitle.value,'Local title');
  assert.equal(f.ids.generateProposal.disabled,true);
});
