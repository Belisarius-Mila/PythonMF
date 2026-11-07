const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
class Element {
 constructor(tag='div'){this.tag=tag;this.children=[];this.listeners={};this.dataset={};this.textContent='';this.className='';this.disabled=false;this.open=false;this.value='';}
 append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=nodes;}
 addEventListener(name,fn){this.listeners[name]=fn;}setAttribute(name,value){this[name]=value;}
 querySelectorAll(selector){return this.children.flatMap(n=>[n,...n.querySelectorAll('*')]).filter(n=>selector==='*'||n.tag===selector||selector==='details.calendar-agenda-more'&&n.tag==='details'&&n.className==='calendar-agenda-more');}
 querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
}
const ids=Object.fromEntries(['calendarAgenda','calendarAgendaStatus','calendarAgendaRefresh','calendarAgendaDeadlines','calendarAgendaMeetings','calendarAgendaDeadlineCount','calendarAgendaMeetingCount'].map(id=>[id,new Element()]));
ids.calendarAgenda.append(...Object.entries(ids).filter(([id])=>id!=='calendarAgenda').map(([,n])=>n));
const document={hidden:false,getElementById:id=>ids[id],createElement:tag=>new Element(tag),listeners:{},addEventListener(name,fn){this.listeners[name]=fn;}};
const window={listeners:{},addEventListener(name,fn){this.listeners[name]=fn;}};
let queue=[],calls=[],timers=new Map(),intervals=[],tid=0,wall=Date.now();
class ClockDate extends Date {static now(){return wall;}}
const scope={window,document,Intl,Date:ClockDate,AbortController,setTimeout:(fn,ms)=>{const id=++tid;timers.set(id,{fn,ms});return id;},clearTimeout:id=>timers.delete(id),setInterval:(fn,ms)=>intervals.push({fn,ms}),
 fetch:async(path,options)=>{const payload=options.body?JSON.parse(options.body):null;calls.push({path,payload,options});assert(queue.length,'Unexpected request '+JSON.stringify(payload));let value=queue.shift();if(value instanceof Error)throw value;value=await value;return {ok:value.ok!==false,json:async()=>value};}};
const event=(n,extra={})=>({key:String(n).padStart(64,'0'),calendar_id:'a',title:n===1?'<img src=x onerror=alert(1)>':'Událost '+n,
 start:'2026-11-09T14:00:00Z',end:'2026-11-09T15:00:00Z',start_day:'2026-11-09',end_day:'2026-11-09',all_day:false,kind:'event',display_kind:'auto',can_classify:true,...extra});
const fresh={ok:true,status:'ready',fresh:true,refreshing:false,selected_count:1,loaded_at:'2026-11-07T13:00:00Z',selection_revision:2,labels_revision:0,classification_partial:false,deadlines:[],meetings:Array.from({length:8},(_,i)=>event(i+1))};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const timer=async()=>{const pair=[...timers].find(([,v])=>v.ms===1500);assert(pair,'Missing poll');timers.delete(pair[0]);return pair[1].fn();};
(async()=>{
 // Cached rows are usable while the asynchronous refresh request is still in flight.
 let resolveRefresh;queue.push(fresh,new Promise(resolve=>resolveRefresh=resolve));
 vm.runInNewContext(fs.readFileSync('app/frontend/cockpit/calendar_agenda.js','utf8'),scope);await tick();
 assert.equal(calls.length,2);assert.equal(calls[0].payload,null);assert.deepEqual(calls[1].payload,{action:'refresh'});
 assert.equal(ids.calendarAgendaMeetingCount.textContent,'8');assert(ids.calendarAgendaMeetings.querySelector('details.calendar-agenda-more'));
 assert(ids.calendarAgendaMeetings.querySelectorAll('strong').some(n=>n.textContent==='<img src=x onerror=alert(1)>'));
 assert(!ids.calendarAgenda.querySelectorAll('img').length);assert(ids.calendarAgendaMeetings.querySelectorAll('span').some(n=>n.textContent.includes('15:00')));
 resolveRefresh({...fresh,refreshing:true});await tick();assert.equal(ids.calendarAgenda['aria-busy'],'true');
 queue.push(fresh);await timer();assert.equal(calls.at(-1).payload,null);assert.equal(ids.calendarAgenda['aria-busy'],'false');
 // Collapsed rest stays open across updates; ambiguous native duplicates remain uneditable.
 const more=ids.calendarAgendaMeetings.querySelector('details.calendar-agenda-more');more.open=true;
 const ambiguous={...fresh,meetings:[event(1,{can_classify:false}),...fresh.meetings.slice(1)]};
 queue.push(ambiguous,ambiguous);await ids.calendarAgendaRefresh.listeners.click();
 assert(ids.calendarAgendaMeetings.querySelector('details.calendar-agenda-more').open);assert(ids.calendarAgenda.querySelectorAll('select')[0].disabled);
 // User classification sends the exact key and both revisions, with no native write action.
 const selects=ids.calendarAgenda.querySelectorAll('select');const chosen=selects[1];chosen.value='task_deadline';
 const labeled={...fresh,labels_revision:1,deadlines:[event(2,{kind:'task_deadline',display_kind:'task_deadline'})],meetings:fresh.meetings.filter(e=>e.key!==event(2).key)};
 queue.push(labeled);await chosen.listeners.change();assert.equal(calls.at(-1).payload.action,'set_kind');assert.equal(calls.at(-1).payload.confirmed,true);
 assert.equal(calls.at(-1).payload.expected_selection_revision,2);assert.equal(calls.at(-1).payload.expected_labels_revision,0);assert.equal(ids.calendarAgendaDeadlineCount.textContent,'1');
 // A slow old poll may not overwrite the result of a later label save.
 queue.push(labeled,{...labeled,refreshing:true});await ids.calendarAgendaRefresh.listeners.click();
 let resolveOld;queue.push(new Promise(resolve=>resolveOld=resolve));const oldPoll=timer();await tick();
 const next=ids.calendarAgenda.querySelectorAll('select')[0];next.value='meeting';queue.push({...fresh,labels_revision:2});await next.listeners.change();
 resolveOld(labeled);await oldPoll;assert.equal(ids.calendarAgendaDeadlineCount.textContent,'0');
 // Failed refresh retains rows but removes freshness and disables type changes.
 queue.push(new Error('Kalendář nedostupný'));await ids.calendarAgendaRefresh.listeners.click();
 assert.equal(ids.calendarAgendaStatus.dataset.fresh,'false');assert.equal(ids.calendarAgendaMeetingCount.textContent,'8');assert(ids.calendarAgenda.querySelectorAll('select').every(n=>n.disabled));
 // A failed background poll must also disable previously enabled controls immediately.
 queue.push(fresh,{...fresh,refreshing:true});await ids.calendarAgendaRefresh.listeners.click();
 assert(ids.calendarAgenda.querySelectorAll('select').some(n=>!n.disabled));
 queue.push(new Error('Poll nedostupný'));await timer();
 assert.equal(ids.calendarAgendaStatus.dataset.fresh,'false');assert(ids.calendarAgenda.querySelectorAll('select').every(n=>n.disabled));
 // No background requests while hidden; returning to the page starts a bounded refresh.
 document.hidden=true;const count=calls.length;wall+=120001;intervals[0].fn();window.listeners.focus();assert.equal(calls.length,count);
 document.hidden=false;queue.push(fresh,fresh);document.listeners.visibilitychange();await tick();await tick();assert.equal(calls.length,count+2);
 // A meeting crossing midnight includes the end date instead of an ambiguous time range.
 const overnight={...fresh,meetings:[event(1,{start:'2026-11-09T22:30:00Z',end:'2026-11-10T00:30:00Z'})]};
 queue.push(overnight,overnight);await ids.calendarAgendaRefresh.listeners.click();
 assert(ids.calendarAgendaMeetings.querySelectorAll('span').some(n=>n.textContent.includes('10. 11.')&&n.textContent.includes('01:30')));
 // Unavailable type metadata must not be presented as a confirmed empty deadline list.
 const partial={...fresh,classification_partial:true};queue.push(partial,partial);await ids.calendarAgendaRefresh.listeners.click();
 assert(ids.calendarAgendaDeadlines.children[0].textContent.includes('není úplné'));
 // With no selected calendars, startup/refresh never requests a native read and does not claim an empty success.
 queue.push({...fresh,fresh:false,status:'selection_required',selected_count:0,deadlines:[],meetings:[]});await ids.calendarAgendaRefresh.listeners.click();
 assert.equal(calls.at(-1).payload,null);assert(ids.calendarAgendaStatus.textContent.includes('Vyber kalendáře'));
 assert.equal(queue.length,0);console.log('Calendar agenda frontend: PASS');
})().catch(err=>{console.error(err);process.exitCode=1;});
