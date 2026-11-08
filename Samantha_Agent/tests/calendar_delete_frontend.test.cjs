const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class Element {
 constructor(tag='div'){this.tag=tag;this.children=[];this.listeners={};this.textContent='';this.disabled=false;this.className='';}
 append(...nodes){this.children.push(...nodes);} setAttribute(name,value){this[name]=value;}
 addEventListener(name,fn){this.listeners[name]=fn;}
 querySelectorAll(selector){return this.children.flatMap(n=>[n,...n.querySelectorAll(selector)]).filter(n=>selector==='button.calendar-delete-button'&&n.tag==='button'&&n.className.includes('calendar-delete-button'));}
}
const document=new Element();document.createElement=tag=>new Element(tag);
const event={calendar_id:'private',title:'Káva <script>bad</script>',start:'2026-11-11T09:00:00Z',end:'2026-11-11T10:00:00Z',all_day:false};
let queue=[],calls=[],confirmations=[],consent=true,refreshes=0;
const window={confirm:text=>{confirmations.push(text);return consent;}};
const scope={window,document,Intl,Date,AbortController,setTimeout,clearTimeout,
 fetch:async(path,options)=>{const payload=JSON.parse(options.body);calls.push({path,payload});assert(queue.length,'Unexpected call');const next=queue.shift();if(next instanceof Error)throw next;return {ok:true,json:async()=>next};}};
vm.runInNewContext(fs.readFileSync('app/frontend/shared/calendar_delete.js','utf8'),scope);
function widget(options={}){
 const host=new Element();document.append(host);window.SamanthaCalendarDelete.attach(host,event,{onDeleted:()=>{refreshes++;},...options});
 return {host,button:host.children[0].children[0],notice:host.children[0].children[1]};
}
const prepared={ok:true,state:'prepared',request_id:'a'.repeat(32),calendar_title:'Osobní',event,recurring:true};
(async()=>{
 const a=widget();consent=false;queue.push(prepared);await a.button.listeners.click();
 assert.equal(calls.length,1);assert.equal(calls[0].payload.action,'prepare');assert(a.notice.textContent.includes('Zrušeno'));
 assert(confirmations[0].includes('pouze tento výskyt'));assert(confirmations[0].includes(event.title));
 consent=true;queue.push(prepared,new Error('timeout'));await a.button.listeners.click();
 assert.equal(calls.at(-1).payload.action,'delete');assert.equal(calls.at(-1).payload.request_id,prepared.request_id);
 assert.equal(a.button.textContent,'Ověřit původní smazání');assert(!a.button.disabled);
 queue.push({ok:true,state:'unknown',message:'Zatím neověřeno'});await a.button.listeners.click();
 assert.equal(calls.at(-1).payload.action,'recover');assert.equal(calls.filter(c=>c.payload.action==='delete').length,1);
 queue.push({ok:true,state:'deleted',message:'Smazáno z kalendáře.'});await a.button.listeners.click();
 assert.equal(calls.at(-1).payload.request_id,prepared.request_id);assert.equal(refreshes,1);assert(a.button.disabled);
 const count=calls.length;await a.button.listeners.click();assert.equal(calls.length,count);
 const b=widget();queue.push({ok:true,state:'setup_required',message:'Povol mazání na Macu'});await b.button.listeners.click();
 assert.equal(b.button.textContent,'Povolit mazání na Macu');assert.equal(calls.at(-1).payload.action,'prepare');
 consent=false;await b.button.listeners.click();assert.equal(calls.at(-1).payload.action,'prepare');
 consent=true;queue.push({ok:true,state:'setup',message:'Dokonči na Macu'});await b.button.listeners.click();
 assert.equal(calls.at(-1).payload.action,'authorize');assert.equal(calls.at(-1).payload.confirmed,true);
 const c=widget({disabled:()=>true});await c.button.listeners.click();assert(c.button.disabled);
 const d=widget({onDeleted:()=>{throw new Error('refresh failed');}});queue.push(prepared,{ok:true,state:'deleted',message:'Smazáno.'});await d.button.listeners.click();
 assert(d.button.disabled);assert.equal(d.notice.textContent,'Smazáno.');
 // Double click while prepare is in flight cannot produce another request.
 const e=widget();let resolve;const old=scope.fetch;scope.fetch=()=>new Promise(r=>{resolve=r;});
 const running=e.button.listeners.click();await e.button.listeners.click();
 consent=false;resolve({ok:true,json:async()=>prepared});await running;scope.fetch=old;
 assert.equal(queue.length,0);console.log('Calendar delete UI: PASS');
})().catch(e=>{console.error(e);process.exitCode=1;});
