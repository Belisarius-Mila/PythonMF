const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const nodes={};
class Element {
 constructor(tag){this.tag=tag;this.children=[];this.listeners={};this.dataset={};this.value='';this.disabled=false;this.hidden=false;this.open=false;this.textContent='';}
 set id(v){this._id=v;nodes[v]=this;}get id(){return this._id;}
 append(...children){this.children.push(...children);}replaceChildren(...children){this.children=children;}
 setAttribute(key,value){this[key]=value;}addEventListener(event,fn){this.listeners[event]=fn;}
 showModal(){this.open=true;}close(){this.open=false;}
}
const body=new Element('body'),timers=new Map();let timerId=0,uuid=0,queue=[],requests=[];
const window={};
const scope={window,document:{body,createElement:tag=>new Element(tag)},AbortController,crypto:{randomUUID:()=>`calendar-${++uuid}`},
 setTimeout:(fn,ms)=>{const id=++timerId;timers.set(id,{fn,ms});return id;},clearTimeout:id=>timers.delete(id),
 fetch:async(path,options={})=>{requests.push({path,payload:options.body?JSON.parse(options.body):null});assert(queue.length,'Unexpected request: '+JSON.stringify(requests.at(-1)));let data=queue.shift();if(data instanceof Error)throw data;data=await data;return {ok:data.ok!==false,json:async()=>data};}};
vm.runInNewContext(fs.readFileSync('app/frontend/email_agent/calendar_draft.js','utf8'),scope);
const api=window.SamanthaCalendarDraft,all=root=>[root,...root.children.flatMap(all)],button=text=>all(body).find(n=>n.tag==='button'&&n.textContent===text);
const item={id:'a'.repeat(64),content_digest:'b'.repeat(64),header:{subject:'<img src=x onerror=alert(1)>'}};
const fields={kind:'meeting',title:'Schůzka',date:'2026-11-11',start_time:'10:00',end_date:'2026-11-11',end_time:'12:30',duration_minutes:'150',time_zone:'Europe/Prague',location:'Praha',join_url:'',all_day:false};
const initial={ok:true,job:null,draft:null,write:null,review:null,writer_built:true};
const complete={...initial,job:{status:'completed'},draft:{revision:0,fields,reminders:[1440,60],issues:[]}};
const reviewed={...complete,review:{fingerprint:'fingerprint-1',valid:true,conflicts:[],target:{title:'Osobní'}}};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
async function timer(ms){const pair=[...timers].find(([,t])=>t.ms===ms);assert(pair,'Missing timer '+ms);timers.delete(pair[0]);await pair[1].fn();}
function input(key,value){const n=nodes['calendarDraft_'+key];n.value=value;n.listeners.input({target:n});}
(async()=>{
 // One source click prepares automatically; polling is GET-only, and no repeated model attempt.
 queue.push(initial,{...initial,job:{status:'queued'}});await api.open(item);
 assert(api.isOpen());assert.equal(requests.length,2);assert.equal(requests[1].payload.action,'prepare');assert.equal(requests[1].payload.expected_content_digest,item.content_digest);
 assert.equal(all(body).filter(n=>n.tag==='input'||n.tag==='select').length,4);
 assert(!all(body).some(n=>n.tag==='blockquote'||n.tag==='img'||n.tag==='script'||n.type==='checkbox'));
 for(const old of ['Připravit návrh modelem','Uložit návrh','Potvrdit návrh'])assert(!button(old));
 queue.push(complete,reviewed);await timer(1000);
 assert.equal(nodes.calendarDraft_start.value,'2026-11-11T10:00');assert.equal(nodes.calendarDraft_title.value,'Schůzka');
 assert(all(body).some(n=>n.textContent.includes('Konec 12:30')));assert(!button('Zapsat do kalendáře').disabled);
 // Autosave sends exactly four editable values and the loaded revision, followed by automatic collision check.
 input('title','Moje schůzka');input('location','');
 const edited={...complete,draft:{...complete.draft,revision:1,fields:{...fields,title:'Moje schůzka',location:''}}};
 const editedReview={...edited,review:{...reviewed.review,fingerprint:'fingerprint-2'}};
 queue.push(edited,editedReview);await timer(600);
 const save=requests.find(r=>r.payload?.action==='save_simple').payload;
 assert.deepEqual(Object.keys(save.values).sort(),['kind','location','start','title']);assert.equal(save.expected_revision,0);assert.equal(save.values.location,'');
 assert.equal(requests.at(-1).payload.action,'review');
 // No extra checkbox/confirmation; the primary button creates the exact reviewed event once.
 let resolveWrite;queue.push(new Promise(resolve=>resolveWrite=resolve));const writing=button('Zapsat do kalendáře').listeners.click();await tick();
 assert(button('Zrušit').disabled);button('Zrušit').listeners.click();assert(api.isOpen());assert(nodes.calendarDraft_title.disabled);
 const written={...editedReview,write:{state:'verified',message:'Zapsáno.',event:{operation_id:'synthetic'}}};resolveWrite(written);await writing;
 assert.equal(requests.at(-1).payload.action,'write');assert.equal(requests.at(-1).payload.review_fingerprint,'fingerprint-2');
 const link=all(body).find(n=>n.tag==='a');assert(!link.hidden);assert.equal(link.href,'/calendar/?email='+item.id);assert(button('Zapsat do kalendáře').hidden);
 button('Zavřít').listeners.click();
 // Reopening a saved event never calls model or writes again.
 const oldCount=requests.filter(r=>r.payload?.action==='prepare').length;
 queue.push(written);await api.open(item);assert.equal(requests.filter(r=>r.payload?.action==='prepare').length,oldCount);button('Zavřít').listeners.click();
 // Conflicts have a short inline notice and explicit primary-button wording.
 const collision={...reviewed,review:{...reviewed.review,conflicts:[{title:'Jiná schůzka'}]}};
 queue.push(complete,collision);await api.open(item);assert(button('Zapsat i přes kolizi'));assert(all(body).some(n=>n.textContent==='Kolize: Jiná schůzka.'));
 queue.push(written);await button('Zapsat i přes kolizi').listeners.click();button('Zavřít').listeners.click();
 // A failed model POST cannot be retried by status refresh or reopen.
 queue.push(initial,new Error('Lost model response'));await api.open(item);
 const prepares=requests.filter(r=>r.payload?.action==='prepare').length;
 const unknownModel={...initial,job:{status:'delivery_unknown'}};queue.push(unknownModel);await button('Obnovit stav').listeners.click();
 assert.equal(requests.filter(r=>r.payload?.action==='prepare').length,prepares);button('Zrušit').listeners.click();
 queue.push(unknownModel);await api.open(item);assert.equal(requests.filter(r=>r.payload?.action==='prepare').length,prepares);button('Zrušit').listeners.click();
 // Unknown writes allow only the original write recovery; GET does not initiate any action.
 const uncertain={...reviewed,write:{state:'unknown',message:'Ověř původní zápis'}};
 queue.push(uncertain);await api.open(item);assert(button('Ověřit původní zápis'));assert(nodes.calendarDraft_title.disabled);
 queue.push(written);await button('Ověřit původní zápis').listeners.click();assert.equal(requests.at(-1).payload.action,'write');button('Zavřít').listeners.click();
 // CAS failure preserves edits, and closing cancels any pending autosave.
 queue.push(complete,reviewed);await api.open(item);input('title','Neztratit');queue.push({ok:false,message:'Revision conflict'});await timer(600);
 assert.equal(nodes.calendarDraft_title.value,'Neztratit');assert(all(body).some(n=>n.textContent==='Revision conflict'));
 input('location','Pending');button('Zrušit').listeners.click();assert(!api.isOpen());assert(![...timers.values()].some(t=>t.ms===600||t.ms===1000));
 assert.equal(queue.length,0);console.log('Simple calendar frontend: PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
