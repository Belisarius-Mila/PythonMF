const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class Element {
 constructor(tag='div'){this.tag=tag;this.children=[];this.listeners={};this.textContent='';this.value='';this.className='';this.disabled=false;this.hidden=false;this.isConnected=true;}
 append(...nodes){this.children.push(...nodes);nodes.forEach(n=>n.parent=this);}
 replaceChildren(...nodes){this.children=[];this.append(...nodes);}
 setAttribute(k,v){this[k]=v;} addEventListener(k,fn){this.listeners[k]=fn;}
 reportValidity(){return true;}focus(){}showModal(){this.open=true;}close(){this.open=false;}
 remove(){if(this.parent)this.parent.children=this.parent.children.filter(n=>n!==this);this.isConnected=false;}
 querySelectorAll(selector){return this.children.flatMap(n=>[n,...n.querySelectorAll(selector)]).filter(n=>selector==='button.calendar-action-button'&&n.tag==='button'&&n.className.includes('calendar-action-button'));}
}
const document=new Element();document.body=document;document.createElement=tag=>new Element(tag);
let queue=[{ok:true,state:'idle'}],calls=[],consent=true,refreshes=0,storageFail=false;
const store=new Map(),window={confirm:()=>consent,dispatchEvent:()=>{},localStorage:{getItem:k=>store.get(k)||null,setItem:(k,v)=>{if(storageFail)throw Error('storage');store.set(k,v);},removeItem:k=>store.delete(k)}};
const scope={window,document,Intl,Date,Map,Array,String,Event:class{},AbortController,setTimeout,clearTimeout,
 fetch:async(path,options)=>{const body=JSON.parse(options.body);calls.push({path,body});assert(queue.length,'Unexpected fetch');let value=queue.shift();if(value instanceof Error)throw value;return{ok:value.ok,json:async()=>value};}};
vm.runInNewContext(fs.readFileSync('app/frontend/shared/calendar_actions.js','utf8'),scope);
const row={calendar_id:'private',title:'Káva <script>',start:'2026-11-11T09:00:00Z',end:'2026-11-11T10:00:00Z',all_day:false,key:'b'.repeat(64),can_complete:true,can_edit:true};
const prepared={ok:true,state:'prepared',request_id:'a'.repeat(32),calendar_title:'Osobní',event:row,form:{title:row.title,date:'2026-11-11',time:'10:00'},recurring:true};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function widget(options={}) {let host=new Element();document.append(host);window.SamanthaCalendarActions.attach(host,row,{context:()=>({selection_revision:4,labels_revision:7}),onChanged:()=>{refreshes++;},...options});return host.children[0];}
const all=root=>root.children.flatMap(n=>[n,...all(n)]),find=(root,tag)=>all(root).find(n=>n.tag===tag);
const modal=()=>document.children.find(n=>n.tag==='dialog');
(async()=>{
 await tick();assert.equal(calls[0].body.action,'current');
 const first=widget();queue.push({ok:true});await first.children[0].listeners.click();
 assert.equal(calls.at(-1).path,'/api/calendar/agenda');assert.equal(calls.at(-1).body.action,'set_completed');assert.equal(calls.at(-1).body.expected_labels_revision,7);assert.equal(refreshes,1);
 queue.push(prepared);await first.children[1].listeners.click();let dialog=modal();assert(dialog.open);assert.equal(find(dialog,'textarea').value,row.title);assert.equal(find(dialog,'input').value,'10:00');
 const canc=all(dialog).find(n=>n.textContent==='Zrušit');canc.listeners.click();assert(!modal());assert.equal(calls.filter(c=>c.body.action==='update').length,0);
 queue.push(prepared);await first.children[1].listeners.click();dialog=modal();const form=find(dialog,'form');find(dialog,'textarea').value='Upravený text';find(dialog,'input').value='11:30';
 queue.push({...prepared,validation_error:'Čas je dvojznačný'});await form.listeners.submit({preventDefault(){}});
 assert(modal());assert.equal(find(modal(),'fieldset').disabled,false);assert.equal(store.size,0);
 queue.push(new Error('network'));await form.listeners.submit({preventDefault(){}});
 assert.equal(calls.at(-1).body.action,'update');assert.equal(calls.at(-1).body.changes.title,'Upravený text');assert(!modal());
 const recovery=document.children.find(n=>n.className.includes('calendar-edit-recovery'));
 assert(recovery);queue.push({ok:true,state:'unknown',message:'Ověř původní úpravu'});await recovery.children[0].listeners.click();
 assert.equal(calls.at(-1).body.action,'recover');assert.equal(calls.at(-1).body.request_id,prepared.request_id);assert.equal(calls.filter(c=>c.body.action==='update').length,2);
 queue.push({ok:true,state:'verified',message:'Uloženo'});await recovery.children[0].listeners.click();assert(recovery.children[0].disabled);assert.equal(store.size,0);
 const second=widget();queue.push({ok:true,state:'setup_required',message:'Povol úpravy'});await second.children[1].listeners.click();assert(second.children[1].textContent.includes('Povolit'));
 consent=false;let n=calls.length;await second.children[1].listeners.click();assert.equal(calls.length,n);
 consent=true;queue.push({ok:true,state:'setup',message:'Dokonči na Macu'});await second.children[1].listeners.click();assert.equal(calls.at(-1).body.action,'authorize');
 const third=widget();queue.push(prepared);await third.children[1].listeners.click();dialog=modal();storageFail=true;n=calls.length;
 await find(dialog,'form').listeners.submit({preventDefault(){}});assert.equal(calls.length,n);assert(modal());storageFail=false;
 all(dialog).find(n=>n.textContent==='Zrušit').listeners.click();
 const disabled=widget({disabled:()=>true});n=calls.length;await disabled.children[0].listeners.click();await disabled.children[1].listeners.click();assert.equal(calls.length,n);
 assert.equal(queue.length,0);console.log('Calendar completion/edit frontend: PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
