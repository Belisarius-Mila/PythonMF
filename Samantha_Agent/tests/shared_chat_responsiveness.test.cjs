'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {webcrypto}=require('node:crypto');
const {Client,startPolling,attach}=require('../app/frontend/samantha_chat/app.js');
const settle=async()=>{for(let n=0;n<25;n++)await Promise.resolve();};
function storage(){const m=new Map();return {getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,String(v)),removeItem:k=>m.delete(k)};}
function clock(){
 let now=0,next=0;const jobs=new Map();
 return {jobs,get now(){return now;},setTimeout(fn,delay){const id=++next;jobs.set(id,{fn,due:now+delay,delay});return id;},clearTimeout(id){jobs.delete(id);},
 async advance(ms){const target=now+ms;while(true){const job=[...jobs].filter(([,j])=>j.due<=target).sort((a,b)=>a[1].due-b[1].due)[0];if(!job)break;now=job[1].due;jobs.delete(job[0]);job[1].fn();await settle();}now=target;await settle();}};
}
function state(text='',revision=1,extra={}){return {ok:true,room_id:'synthetic-room',name:'Fixture',client_label:'Phone',messages:[],draft:{text,revision,client_message_id:'synthetic-message-001',can_edit:true,is_writer:true,lease_remaining_ms:120000,...extra}};}
function client(fetch,timer=clock()){
 const c=new Client({fetch,storage:storage(),tabStorage:storage(),crypto:webcrypto,setTimer:timer.setTimeout,clearTimer:timer.clearTimeout});c.token='a'.repeat(64);c.apply(state());return c;
}
const response=data=>({ok:true,json:async()=>data});
function events(){const listeners={};return {listeners,addEventListener(name,fn){(listeners[name]??=[]).push(fn);},fire(name,event={}){for(const fn of listeners[name]||[])fn(event);}};}

test('the save confirmation freezes the visible proposal and disables after an edit',async()=>{
 const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
 const timer=clock(),browser=Object.assign(events(),timer,{localStorage:storage(),sessionStorage:storage(),crypto:webcrypto});
 browser.localStorage.setItem('samantha-shared-chat-client','a'.repeat(64));
 browser.SamanthaLibrary={safeSource:url=>url,create:()=>({render(){}})};
 const proposal={id:'a'.repeat(32),state:'draft',url:'',text:'Původní text',title:'Název',category:'travel_places',visit_state:'want_to_visit'};
 browser.fetch=async()=>response({...state(),library_save:proposal});
 const doc=Object.assign(events(),{hidden:false,activeElement:null});
 function element(){return Object.assign(events(),{children:[],value:'',hidden:false,disabled:false,readOnly:true,textContent:'',scrollHeight:0,scrollTop:0,clientHeight:0,
  focus(){doc.activeElement=this;},appendChild(child){this.children.push(child);},replaceChildren(){this.children=[];}});}
 const elements=new Map();doc.getElementById=id=>{if(!elements.has(id))elements.set(id,element());return elements.get(id);};
 doc.createElement=element;doc.createTextNode=text=>({textContent:text});
 const realm={window:browser,module:{exports:{}},Uint8Array,AbortController,setTimeout,clearTimeout};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../app/frontend/samantha_chat/app.js'),'utf8'),realm);
 const c=realm.module.exports.attach(doc);await settle();
 assert.equal(doc.getElementById('saveConfirm').disabled,false);
 assert.equal(doc.getElementById('saveTextPreview').textContent,'Původní text');
 const input=doc.getElementById('saveText');input.value='Změněný text';input.fire('input');
 assert.equal(doc.getElementById('saveConfirm').disabled,true);
 c.stopPolling();c.disconnect();
});

test('continuous dictation is saved during input rather than waiting for its end',async()=>{
 const timer=clock(),saved=[];
 const c=client(async(_p,o)=>{const p=JSON.parse(o.body);assert.equal(p.action,'draft');saved.push({at:timer.now,text:p.text});return response(state(p.text,p.expected_revision+1));},timer);
 for(let n=0;n<30;n++){c.setText('Dictation '+n);await timer.advance(100);}
 assert.ok(saved.length>=15);assert.equal(saved[0].at,150);assert.ok(saved.some(s=>s.at<1000));
 await timer.advance(150);assert.equal(c.dirty,false);assert.equal(saved.at(-1).text,'Dictation 29');
});

test('one slow draft request coalesces further edits without a request backlog',async()=>{
 const timer=clock(),requests=[];let release;
 const c=client(async(_p,o)=>{const p=JSON.parse(o.body);requests.push(p);if(requests.length===1)await new Promise(r=>release=r);return response(state(p.text,p.expected_revision+1));},timer);
 c.setText('First');await timer.advance(150);assert.equal(requests.length,1);
 for(let n=0;n<30;n++){c.setText('Newest '+n);await timer.advance(100);}
 assert.equal(requests.length,1);assert.equal(timer.jobs.size,0);
 release();await settle();await timer.advance(150);
 assert.equal(requests.length,2);assert.equal(requests[1].text,'Newest 29');assert.equal(c.dirty,false);
});

test('background refreshes coalesce and stale responses do not overwrite current edits',async()=>{
 let release,gets=0;
 const c=client(async(_p,o)=>{if(!o.body){gets++;await new Promise(r=>release=r);return response(state('Old',1));}const p=JSON.parse(o.body);return response(state(p.text,p.expected_revision+1));});
 const a=c.refresh(),b=c.refresh();assert.equal(gets,1);
 c.setText('Current');await c.flush();release();await Promise.all([a,b]);assert.equal(c.text,'Current');
});

test('expired own lease renews without takeover and foreign ownership is left alone',async()=>{
 const requests=[];const c=client(async(_p,o)=>{const p=JSON.parse(o.body);requests.push(p);return response(state('',p.expected_revision+1));});
 c.focused=true;c.apply(state('',2,{can_edit:false,lease_remaining_ms:0}));
 assert.equal(c.canWriteLocally(),true);await c.keepWriting();assert.equal(requests[0].takeover,false);
 c.apply(state('',4,{can_edit:false,is_writer:false,lease_remaining_ms:100000}));
 await c.keepWriting();assert.equal(requests.length,1);assert.equal(c.canWriteLocally(),false);
});

test('uncertain send keeps new input local and readback never submits a second question',async()=>{
 const timer=clock(),requests=[];let sent=false,release;
 const c=client(async(_p,o)=>{
  if(!o.body)return response(state('',3));
  const p=JSON.parse(o.body);requests.push(p);
  if(p.action==='send'){sent=true;await new Promise(r=>release=r);throw Error('Lost HTTP response');}
  return response(state(p.text,p.expected_revision+1));
 },timer);
 c.setText('Original question');await c.flush();const sending=c.send();await settle();assert.equal(sent,true);
 c.setText('Preserved follow-up');await timer.advance(1000);assert.equal(requests.length,2);
 release();await assert.rejects(sending);assert.ok(c.pending);assert.equal(c.recovery.text,'Preserved follow-up');
 await c.refresh();await timer.advance(1000);
 assert.equal(requests.filter(r=>r.action==='send').length,1);assert.equal(c.text,'Preserved follow-up');
 assert.equal(requests.filter(r=>r.action==='draft').length,1,'unconfirmed send cannot change the original server draft');
});

test('active polling adds at most 400 ms and backs off in the background',async()=>{
 const timer=clock(),browser=Object.assign(events(),timer),doc=Object.assign(events(),{hidden:false});
 let reads=0,renewals=0;const fake={online:true,refresh:async()=>{reads++;},keepWriting:async()=>{renewals++;}};
 const stop=startPolling(fake,doc,browser);await settle();assert.equal(reads,1);
 await timer.advance(399);assert.equal(reads,1);await timer.advance(1);assert.equal(reads,2);
 doc.hidden=true;doc.fire('visibilitychange');await settle();const prior=reads;
 await timer.advance(4999);assert.equal(reads,prior);await timer.advance(1);assert.equal(reads,prior+1);
 doc.hidden=false;doc.fire('visibilitychange');await settle();assert.equal(reads,prior+2);
 browser.fire('pagehide');await timer.advance(5000);assert.equal(reads,prior+2);
 browser.fire('pageshow');await settle();assert.equal(reads,prior+3);assert.ok(renewals>=3);
 stop();assert.equal(timer.jobs.size,0);
});

test('a network request in progress never grows a polling backlog on repeated wakeups',async()=>{
 const timer=clock(),browser=Object.assign(events(),timer),doc=Object.assign(events(),{hidden:false});let release,reads=0;
 const stop=startPolling({online:true,refresh:async()=>{reads++;await new Promise(r=>release=r);},keepWriting:async()=>{}},doc,browser);
 for(let i=0;i<10;i++)doc.fire('visibilitychange');assert.equal(reads,1);
 release();await settle();await timer.advance(0);assert.equal(reads,2);stop();release();await settle();assert.equal(timer.jobs.size,0);
});

test('tapping the input starts ownership inside the gesture and preserves keyboard focus',async()=>{
 const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
 const timer=clock(),browser=Object.assign(events(),timer,{localStorage:storage(),sessionStorage:storage(),crypto:webcrypto});
 browser.localStorage.setItem('samantha-shared-chat-client','a'.repeat(64));
 let release,claimCalls=0;browser.fetch=async(_p,o)=>{
  if(!o.body)return response(state('',1,{can_edit:false,is_writer:false}));
  const p=JSON.parse(o.body);
  if(p.action==='claim'){claimCalls++;await new Promise(r=>release=r);return response(state('',2));}
  assert.equal(p.action,'draft');return response(state(p.text,p.expected_revision+1));
 };
 const doc=Object.assign(events(),{hidden:false,activeElement:null});let inGesture=false,focusedInGesture=false;
 function element(){return Object.assign(events(),{value:'',hidden:false,disabled:false,readOnly:true,textContent:'',scrollHeight:0,scrollTop:0,clientHeight:0,
  focus(){if(doc.activeElement===this)return;assert.equal(this.readOnly,false);focusedInGesture=inGesture;doc.activeElement=this;this.fire('focus');},
  appendChild(){},replaceChildren(){}});}
 const elements=new Map();doc.getElementById=id=>{if(!elements.has(id))elements.set(id,element());return elements.get(id);};doc.createElement=element;doc.createTextNode=text=>({textContent:text});
 const realm={window:browser,module:{exports:{}},Uint8Array,AbortController,setTimeout,clearTimeout};
 vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../app/frontend/samantha_chat/app.js'),'utf8'),realm);
 const c=realm.module.exports.attach(doc);await settle();const input=doc.getElementById('input');assert.equal(input.readOnly,true);
 inGesture=true;input.fire('pointerdown');inGesture=false;
 assert.equal(focusedInGesture,true);assert.equal(c.claiming,true);assert.equal(input.readOnly,false);
 input.fire('input',{target:{value:'Typed before claim reply'}});assert.equal(c.text,'Typed before claim reply');
 await timer.advance(150);assert.equal(claimCalls,1);assert.equal(input.readOnly,false);
 release();await settle();await c.chain;assert.equal(input.value,'Typed before claim reply');assert.equal(c.dirty,false);
 let prevented=false;doc.getElementById('send').fire('pointerdown',{preventDefault(){prevented=true;}});
 assert.equal(prevented,true);assert.equal(doc.activeElement,input);
 c.stopPolling();c.disconnect();assert.equal(timer.jobs.size,0);
});

test('input after an expired own lease renews with CAS before saving text',async()=>{
 const requests=[];const c=client(async(_p,o)=>{const p=JSON.parse(o.body);requests.push(p);return response(state(p.text||'',p.expected_revision+1));});
 c.focused=true;c.apply(state('',4,{can_edit:false,lease_remaining_ms:0}));
 c.setText('After idle');await c.flush();
 assert.deepEqual(requests.map(p=>p.action),['claim','draft']);assert.equal(requests[0].takeover,false);
 assert.equal(requests[1].expected_revision,5);assert.equal(c.text,'After idle');assert.equal(c.dirty,false);
});
