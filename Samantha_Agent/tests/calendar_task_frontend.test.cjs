const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class Element {
 constructor(){this.children=[];this.value='';this.disabled=false;this.hidden=false;this.listeners={};this.dataset={};this.textContent='';}
 append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=nodes;}
 addEventListener(name,fn){this.listeners[name]=fn;}setAttribute(name,value){this[name]=value;}
 reportValidity(){return true;}
}
const source=fs.readFileSync('app/frontend/calendar_task/app.js','utf8');
const key='samantha.calendarTask.pending.v1';
const context={ok:true,ready:true,target:{id:'a',title:'Soukromý'},selection_revision:2,today:'2026-11-08',default_time:'09:00',time_zone:'Europe/Prague',reminders:[1440,60]};
const id='a'.repeat(32), second='b'.repeat(32);
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function app({stored=null,initial=context,storageFails=false,cryptoMode='https',storageWriteFailures=0,readbackFailure=false}={}) {
 const ids=Object.fromEntries(['taskForm','taskFields','taskTitle','taskDay','taskMonth','taskYear','taskTime','taskNotice','taskRecover','taskSummary','taskTarget','taskSubmit'].map(k=>[k,new Element()]));
 let queue=[initial],calls=[],timers=new Map(),counter=0,serial=0,failNextRead=false,storage=new Map(stored?[[key,JSON.stringify(stored)]]:[]);
 const document={hidden:false,getElementById:id=>ids[id],createElement:()=>new Element(),createTextNode:text=>({textContent:text}),listeners:{},addEventListener(name,fn){this.listeners[name]=fn;}};
 const crypto={getRandomValues:bytes=>{bytes.fill(++serial===1?0xaa:0xbb);return bytes;}};
 if(cryptoMode==='https')crypto.randomUUID=()=>++serial===1?'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa':'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb';
 if(cryptoMode==='none')delete crypto.getRandomValues;
 const window={listeners:{},addEventListener(name,fn){this.listeners[name]=fn;},crypto,
  localStorage:{getItem:k=>{if(storageFails)throw new Error('Storage unavailable');if(failNextRead){failNextRead=false;throw new Error('Read-back unavailable');}return storage.get(k)||null;},setItem:(k,v)=>{if(storageFails||storageWriteFailures-->0)throw new Error('Storage unavailable');storage.set(k,v);if(readbackFailure){readbackFailure=false;failNextRead=true;}},removeItem:k=>storage.delete(k)}};
 const scope={window,document,Date,Intl,AbortController,setTimeout:(fn,ms)=>{const id=++counter;timers.set(id,{fn,ms});return id;},clearTimeout:id=>timers.delete(id),
  fetch:async(path,options)=>{const payload=options.body?JSON.parse(options.body):null;calls.push({path,payload,options});assert(queue.length,'Unexpected request '+JSON.stringify(payload));let next=queue.shift();if(next instanceof Error)throw next;next=await next;return {ok:next.ok!==false,json:async()=>next};}};
 vm.runInNewContext(source,scope);
 const send=()=>ids.taskForm.listeners.submit({preventDefault(){}});
 const result=(state,extra={})=>({ok:true,request_id:calls.find(c=>c.payload?.action==='create')?.payload.request_id||stored?.id||id,state,message:state,...extra});
 const poll=async()=>{const pair=[...timers].find(([,v])=>v.ms===1500);assert(pair,'Missing status timer');timers.delete(pair[0]);await pair[1].fn();};
 return {ids,queue,calls,storage,window,document,send,result,poll};
}
(async()=>{
 // HTTP/private-LAN browsers expose getRandomValues but not randomUUID.
 let http=app({cryptoMode:'http'});await tick();http.ids.taskTitle.value='Úkol z HTTP';
 http.queue.push(http.result('verified',{task:{title:'Úkol z HTTP',date:'2026-11-08',time:'09:00'}}));await http.send();
 assert.equal(http.calls.filter(c=>c.payload?.action==='create').length,1,'HTTP must work without randomUUID');
 assert.match(http.calls.at(-1).payload.request_id,/^[a-f0-9]{32}$/);assert.equal(http.ids.taskNotice.dataset.state,'verified');
 // Date/time defaults come from Prague on the server; day changes usually suffice.
 let a=app();await tick();assert.equal(a.ids.taskTime.value,'09:00');assert.equal(a.ids.taskDay.value,'8');assert.equal(a.ids.taskMonth.value,'11');
 assert.equal(a.ids.taskFields.disabled,false);a.ids.taskMonth.value='2';a.ids.taskYear.value='2028';a.ids.taskDay.value='31';a.ids.taskMonth.listeners.change();
 assert.equal(a.ids.taskDay.value,'29');assert.equal(a.ids.taskDay.children.length,29);
 // One submit includes the user-edited hour and exact selection; no AI/preview request.
 a.ids.taskTitle.value='<img src=x onerror=alert(1)> u pošty';a.ids.taskTime.value='16:20';
 let resolve; a.queue.push(new Promise(r=>resolve=r));const first=a.send();await tick();
 assert.equal(a.ids.taskFields.disabled,true);assert(a.storage.has(key));await a.send();assert.equal(a.calls.filter(c=>c.payload?.action==='create').length,1);
 const sent=a.calls.at(-1).payload;assert.equal(sent.time,'16:20');assert.equal(sent.date,'2028-02-29');assert.equal(sent.confirmed,true);assert.equal(sent.expected_selection_revision,2);
 resolve(a.result('verified',{task:{title:sent.title,date:sent.date,time:sent.time}}));await first;
 assert.equal(a.ids.taskTitle.value,'');assert.equal(a.ids.taskFields.disabled,false);assert(!a.storage.has(key));
 assert(a.ids.taskNotice.textContent.includes('<img src=x onerror=alert(1)>'));assert.equal(a.ids.taskNotice.dataset.state,'verified');
 // A network failure never clears input or sends a second create; only status is automatic.
 a=app();await tick();a.ids.taskTitle.value='Původní text';a.queue.push(new Error('Lost response'));await a.send();
 assert.equal(a.ids.taskTitle.value,'Původní text');assert(a.ids.taskFields.disabled);const pending=JSON.parse(a.storage.get(key));
 a.queue.push(a.result('unknown'));await a.poll();assert.equal(a.calls.at(-1).payload.action,'status');
 a.queue.push(a.result('verified',{task:{title:'Původní text',date:'2026-11-08',time:'09:00'}}));await a.ids.taskRecover.listeners.click();
 assert.equal(a.calls.at(-1).payload.action,'recover');assert.equal(a.calls.filter(c=>c.payload?.action==='create').length,1);
 // A restarted page only reads the saved request. It never replays create automatically.
 a=app({stored:pending});a.queue.push({ok:true,request_id:pending.id,state:'unknown',message:'Ověř zápis'});await tick();await tick();
 assert.equal(a.calls.length,2);assert.equal(a.calls[1].payload.action,'status');assert.equal(a.ids.taskTitle.value,'Původní text');assert(a.ids.taskFields.disabled);
 // If the original did not reach the server, explicit retry keeps exactly the same ID/payload.
 a.queue.push({ok:true,request_id:pending.id,state:'not_found',message:'Nenalezeno'});await a.ids.taskRecover.listeners.click();
 assert.equal(a.calls.at(-1).payload.action,'recover');assert.equal(a.ids.taskRecover.textContent,'Zapsat stejné zadání');
 a.queue.push({ok:true,request_id:pending.id,state:'verified',task:{title:'Původní text',date:'2026-11-08',time:'09:00'}});await a.ids.taskRecover.listeners.click();
 assert.deepEqual(a.calls.at(-1).payload,pending.payload);assert(!a.storage.has(key));
 // Known rejection unlocks unchanged input and reloads target metadata, without another write.
 a=app();await tick();a.ids.taskTitle.value='Pozdější hodina';a.queue.push(a.result('blocked',{message:'Čas už uplynul'}),context);await a.send();await tick();
 assert.equal(a.ids.taskTitle.value,'Pozdější hodina');assert.equal(a.ids.taskFields.disabled,false);assert.equal(a.ids.taskNotice.dataset.state,'blocked');
 assert.equal(a.calls.filter(c=>c.payload?.action==='create').length,1);
 // Unavailable browser storage or an unconfigured target prevents any outgoing action.
 a=app({storageFails:true});await tick();a.ids.taskTitle.value='Neodeslat';await a.send();assert.equal(a.calls.length,1);assert(a.ids.taskSubmit.disabled);assert(!a.ids.taskFields.disabled);
 assert(a.ids.taskNotice.textContent.includes('Uložené zadání'));assert(!a.ids.taskNotice.textContent.includes('Storage unavailable'));
 a=app({initial:{...context,ready:false,target:null}});await tick();assert(a.ids.taskFields.disabled);assert.equal(a.calls.length,1);
 a=app();await tick();a.ids.taskTitle.value='   ';await a.send();assert.equal(a.calls.length,1);assert(!a.storage.has(key));assert(!a.ids.taskFields.disabled);
 // A failed pre-send write preserves editable text and permits a later explicit retry.
 a=app({storageWriteFailures:1});await tick();a.ids.taskTitle.value='Uchovat text';await a.send();
 assert.equal(a.calls.length,1);assert.equal(a.ids.taskTitle.value,'Uchovat text');assert(!a.ids.taskFields.disabled);assert(!a.ids.taskSubmit.disabled);assert(!a.storage.has(key));
 a.queue.push({ok:true,request_id:second,state:'verified',task:{title:'Uchovat text',date:'2026-11-08',time:'09:00'}});await a.send();
 assert.equal(a.calls.filter(c=>c.payload?.action==='create').length,1);assert.equal(a.ids.taskNotice.dataset.state,'verified');
 // If the write persisted but read-back failed, only status and the same identity may continue.
 a=app({readbackFailure:true});await tick();a.ids.taskTitle.value='Částečně uložené zadání';
 a.queue.push({ok:true,request_id:id,state:'not_found',message:'Nenalezeno'});await a.send();await tick();
 assert.equal(a.calls.filter(c=>c.payload?.action==='create').length,0);assert.equal(a.calls.at(-1).payload.action,'status');
 assert(a.ids.taskFields.disabled);assert.equal(a.ids.taskRecover.textContent,'Zapsat stejné zadání');
 const partial=JSON.parse(a.storage.get(key));a.queue.push({ok:true,request_id:id,state:'verified',task:{title:'Částečně uložené zadání',date:'2026-11-08',time:'09:00'}});await a.ids.taskRecover.listeners.click();
 assert.deepEqual(a.calls.at(-1).payload,partial.payload);assert.equal(a.calls.filter(c=>c.payload?.action==='create').length,1);
 // No weak fallback when the browser lacks a strong random generator.
 a=app({cryptoMode:'none'});await tick();a.ids.taskTitle.value='Zachovat';await a.send();
 assert.equal(a.calls.length,1);assert.equal(a.ids.taskTitle.value,'Zachovat');assert(!a.ids.taskFields.disabled);assert(!a.storage.has(key));
 console.log('Calendar task frontend: PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
