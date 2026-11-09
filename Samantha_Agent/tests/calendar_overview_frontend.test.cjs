const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class Element {
 constructor(tag='div'){this.tagName=tag;this.children=[];this.listeners={};this.dataset={};this.value='';this.checked=false;this.hidden=false;this.disabled=false;this.textContent='';}
 append(...nodes){this.children.push(...nodes);}
 replaceChildren(...nodes){this.children=nodes;}
 get firstChild(){return this.children[0];}
 addEventListener(name,fn){this.listeners[name]=fn;}
 querySelectorAll(selector){let all=this.children.flatMap(node=>[node,...node.querySelectorAll('*')]);return all.filter(node=>selector==='*'||selector==='input,select'&&['input','select'].includes(node.tagName)||selector==='input:checked'&&node.tagName==='input'&&node.checked);}
}
const ids=Object.fromEntries(['refresh','authorize','save','notice','permission','loaded','count','events','calendars','target','selection','settings','draft'].map(id=>[id,new Element()]));
ids.settings.append(ids.calendars,ids.target);
const now='2026-11-07T12:00:00Z';
const state={ok:true,revision:0,read_calendar_ids:[],target_calendar_id:'',calendars:[],events:[],ready:false,status:'selection_required',can_select:false,last_loaded_at:null};
let queue=[state],calls=[];
const scope={window:{addEventListener:()=>{}},document:{getElementById:id=>ids[id],createElement:tag=>new Element(tag)},Intl,Date,Map,Array,String,setTimeout,clearTimeout,setInterval:()=>0,
 AbortController,fetch:async(path,options)=>{calls.push({path,options,body:options.body?JSON.parse(options.body):null});const value=queue.shift();assert(value,'unexpected fetch');return{ok:value.ok,json:async()=>value};}};
vm.runInNewContext(fs.readFileSync('app/frontend/calendar_overview/app.js','utf8'),scope);
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 await tick();assert.equal(calls.length,1);assert.equal(calls[0].options.method,'GET');assert.equal(ids.save.disabled,true);
 const inventory={...state,can_select:true,calendars:[{id:'a',title:'<script>unsafe</script>',source_title:'iCloud',writable:true},{id:'b',title:'Readonly',source_title:'Other',writable:false}]};
 queue.push(inventory);ids.refresh.listeners.click();await tick();
 assert.equal(calls[1].body.action,'refresh');assert.equal(ids.calendars.children[0].children[1].textContent,'<script>unsafe</script>');assert.equal(ids.target.children.length,2);
 ids.calendars.children[0].children[0].checked=true;ids.target.value='a';ids.settings.listeners.change();
 // Refresh must preserve an unsaved user selection.
 queue.push(inventory);ids.refresh.listeners.click();await tick();assert.equal(ids.calendars.children[0].children[0].checked,true);
 const ready={...inventory,revision:1,read_calendar_ids:['a'],target_calendar_id:'a',ready:true,status:'ready',last_loaded_at:now,
 events:[{calendar_id:'a',title:'<img src=x onerror=alert(1)>',start:'2026-10-24T22:00:00Z',end:'2026-10-26T23:00:00Z',start_day:'2026-10-25',end_day:'2026-10-27',all_day:true,timezone:'Europe/Prague'}]};
 queue.push({...ready,ready:false},ready);ids.settings.listeners.submit({preventDefault(){}});await tick();await tick();
 const save=calls.find(row=>row.body?.action==='save_selection');assert.deepEqual(save.body.read_calendar_ids,['a']);assert.equal(save.body.expected_revision,0);
 assert.equal(ids.events.children[0].children[1].textContent,'<img src=x onerror=alert(1)>');
 assert.match(ids.events.children[0].children[0].textContent,/25.*26/);assert.doesNotMatch(ids.events.children[0].children[0].textContent,/27/);
 assert.equal(ids.notice.dataset.ready,'true');
 queue.push({...ready,ready:false,status:'missing_calendars',events:[]});ids.refresh.listeners.click();await tick();
 assert.match(ids.notice.textContent,/neúplný/);assert.match(ids.events.children[0].textContent,/nepotvrzuje volný čas/);
 queue.push({...state,status:'authorization_required'});ids.refresh.listeners.click();await tick();assert.equal(ids.permission.hidden,false);
 queue.push({...state,authorization_status:'pending'});ids.authorize.listeners.click();await tick();assert.match(ids.notice.textContent,/povolení na Macu/);
 queue.push({ok:false,message:'Stale selection'});ids.refresh.listeners.click();await tick();assert.equal(ids.notice.dataset.ready,'false');assert.equal(ids.refresh.disabled,false);
 const savedPanel=new Element('section');
 scope.document.getElementById=id=>id==='saved-event' ? savedPanel : ids[id];
 scope.location={search:'?email='+'a'.repeat(64)};scope.URLSearchParams=URLSearchParams;scope.URL=URL;
 queue.push(state,{ok:true,write:{state:'verified',checked_at:now,verified_event:{title:'<script>literal saved title</script>',start:now,end:'2026-11-07T13:00:00Z',location:'Praha',reminders:[1440,60],join_url:'https://meet.example.test/room'}}});
 vm.runInNewContext(fs.readFileSync('app/frontend/calendar_overview/app.js','utf8'),scope);
 await tick();await tick();
 assert.equal(savedPanel.hidden,false);assert.equal(savedPanel.children[0].textContent,'<script>literal saved title</script>');
 assert(savedPanel.children.some(n=>n.textContent.includes('Zápis ověřen')));
 assert.equal(savedPanel.children.at(-1).href,'https://meet.example.test/room');
 assert(calls.at(-1).path.startsWith('/api/email-agent/calendar-draft?id='));
 console.log('Calendar overview browser contract PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
