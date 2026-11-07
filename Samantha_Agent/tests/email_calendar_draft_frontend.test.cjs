const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const nodes={};
class Element {
 constructor(tag){this.tag=tag;this.children=[];this.listeners={};this.dataset={};this.value='';this.checked=false;this.disabled=false;this.hidden=false;this.open=false;this.textContent='';}
 set id(value){this._id=value;nodes[value]=this;}get id(){return this._id;}
 append(...children){this.children.push(...children);}replaceChildren(...children){this.children=children;}
 setAttribute(key,value){this[key]=value;}addEventListener(event,fn){this.listeners[event]=fn;}
 showModal(){this.open=true;}close(){this.open=false;this.listeners.close?.({});}
}
const body=new Element('body'),timers=new Map();let timerId=0,uuid=0,queue=[],requests=[];
const window={confirm:()=>true};
const response=data=>({ok:data.ok!==false,json:async()=>data});
const scope={window,document:{body,createElement:tag=>new Element(tag)},AbortController,crypto:{randomUUID:()=>`client-calendar-${++uuid}`},
 setTimeout:(fn,ms)=>{const id=++timerId;timers.set(id,{fn,ms});return id;},clearTimeout:id=>timers.delete(id),
 fetch:async(path,options={})=>{requests.push({path,options,payload:options.body?JSON.parse(options.body):null});assert(queue.length,'Unexpected request');const data=queue.shift();if(data instanceof Error)throw data;return response(await data);}};
vm.runInNewContext(fs.readFileSync('app/frontend/email_agent/calendar_draft.js','utf8'),scope);
const api=window.SamanthaCalendarDraft;
const all=root=>[root,...root.children.flatMap(all)];
const button=text=>all(body).find(node=>node.tag==='button'&&node.textContent===text);
const title=()=>nodes.calendarDraft_title;
const fields={kind:'meeting',title:'Schůzka',date:'2026-11-11',start_time:'10:00',end_date:'',end_time:'11:00',duration_minutes:'',time_zone:'Europe/Prague',location:'Praha',join_url:'',all_day:false};
const initial={ok:true,source:{id:'a'.repeat(64),subject:'<img src=x onerror=alert(1)>',date:'7.11.2026'},model:'synthetic',job:null,draft:null};
const draft={revision:0,fields,evidence:{title:{source:'subject',quote:'<script>literal</script>',origin:'email_quote'}},issues:[],normalized:{start:'x',end:'y'}};
const complete={...initial,job:{status:'completed'},draft};
const item={id:'a'.repeat(64),content_digest:'b'.repeat(64),header:{subject:'Selected email'}};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
const poll=async()=>{const pair=[...timers].find(([,timer])=>timer.ms===1000);assert(pair,'Missing polling timer');timers.delete(pair[0]);await pair[1].fn();};
(async()=>{
 queue.push(initial);await api.open(item);assert(api.isOpen());assert.equal(requests.length,1);assert(!requests[0].payload);assert(title().disabled);assert(!button('Připravit návrh modelem').disabled);
 queue.push({...initial,job:{status:'queued'}});await button('Připravit návrh modelem').listeners.click();
 assert.equal(requests.at(-1).payload.action,'prepare');assert.equal(requests.at(-1).payload.expected_content_digest,item.content_digest);assert(button('Připravit návrh modelem').hidden);
 queue.push(complete);await poll();assert.equal(title().value,'Schůzka');assert(!title().disabled);
 assert(all(body).some(node=>node.tag==='blockquote'&&node.textContent==='<script>literal</script>'));assert(!all(body).some(node=>node.tag==='script'||node.tag==='img'));
 title().value='My edit';title().listeners.input();queue.push({...complete,draft:{...draft,revision:1,fields:{...fields,title:'Changed elsewhere'}}});await button('Obnovit stav').listeners.click();assert.equal(title().value,'My edit');
 queue.push({ok:false,message:'Revision conflict'});await button('Uložit návrh').listeners.click();assert.equal(title().value,'My edit');assert.equal(requests.at(-1).payload.expected_revision,0);
 button('Zavřít').listeners.click();queue.push({...complete,draft:{...draft,revision:1}});await api.open(item);
 let resolveOld;queue.push(new Promise(resolve=>resolveOld=resolve));const oldRead=button('Obnovit stav').listeners.click();await tick();
 title().value='Saved new';title().listeners.input();queue.push({...complete,draft:{...draft,revision:2,fields:{...fields,title:'Saved new'}}});await button('Uložit návrh').listeners.click();
 resolveOld({...complete,draft:{...draft,revision:1,fields:{...fields,title:'Late old data'}}});await oldRead;assert.equal(title().value,'Saved new');
 button('Zavřít').listeners.click();queue.push(initial);await api.open(item);queue.push(new Error('Lost response'));await button('Připravit návrh modelem').listeners.click();
 const count=requests.length;await button('Připravit návrh modelem').listeners.click();assert.equal(requests.length,count);assert(button('Připravit návrh modelem').disabled);
 queue.push({...initial,job:{status:'delivery_unknown',message:'Vyžaduje ověření'}});await button('Obnovit stav').listeners.click();assert(button('Připravit návrh modelem').hidden);assert(all(body).some(node=>node.textContent==='Vyžaduje ověření'));
 button('Zavřít').listeners.click();queue.push({...initial,job:{status:'running'}});await api.open(item);button('Zavřít').listeners.click();assert(!api.isOpen());assert(![...timers.values()].some(timer=>timer.ms===1000));
 queue.push(initial);await api.open(item);let resolvePost;queue.push(new Promise(resolve=>resolvePost=resolve));const inProgress=button('Připravit návrh modelem').listeners.click();await tick();
 assert(button('Zavřít').disabled);nodes.calendarDraftEditor.listeners.cancel({preventDefault(){}});assert(api.isOpen());
 resolvePost(complete);await inProgress;button('Zavřít').listeners.click();assert(!api.isOpen());
 assert.equal(requests.filter(r=>r.payload?.action==='prepare').length,3);
 console.log('Email calendar draft browser contract PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
