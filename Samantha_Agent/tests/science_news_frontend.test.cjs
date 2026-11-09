const assert = require('node:assert/strict');
const {test} = require('node:test');
const vm = require('node:vm');
const fs = require('node:fs');

class Element {
  constructor(tag='div') {
    this.tagName=tag;this.children=[];this.textContent='';this.listeners={};this.disabled=false;
    this.attributes={};this.classes=new Set();
    this.classList={add:k=>this.classes.add(k),remove:k=>this.classes.delete(k),
      toggle:(k,v)=>v?this.classes.add(k):this.classes.delete(k),contains:k=>this.classes.has(k)};
  }
  appendChild(child){this.children.push(child);return child;}
  replaceChildren(){this.children=[];}
  addEventListener(name,fn){this.listeners[name]=fn;}
  setAttribute(k,v){this.attributes[k]=v;}
  scrollIntoView(){}
  get innerHTML(){throw Error('Never read HTML');}
  set innerHTML(v){throw Error('Never inject HTML');}
  async click(){if(!this.disabled)return await this.listeners.click?.();}
}
function nodes(el){return [el,...el.children.flatMap(nodes)];}
const fixtureItem={id:'sn_fixture',title:'<img onerror=alert(1)>',area:'Genetika',published_at:'2026-11-01T09:00:00Z',
 abstract_cs:'Český abstrakt',significance_cs:'Význam',uncertainty_cs:'Nejistota',source_url:'https://www.nature.com/test'};
const data=(items=[fixtureItem])=>({ok:true,items,pending_count:items.length,follows:[],issues:[],activated:false});
const response=payload=>({ok:true,json:async()=>payload});
function setup(fetch, sharedStorage) {
 const context={window:{},URL};
 vm.runInNewContext(fs.readFileSync('app/frontend/cockpit/science_news.js','utf8'),context);
 const elements=Object.fromEntries(['entry','tab','section','status','list','follows'].map(k=>[k,new Element()]));
 const saved=sharedStorage||new Map();
 const calls=[],opened=[],events=[];
 const storage={getItem:k=>saved.get(k)||null,setItem:(k,v)=>saved.set(k,v),removeItem:k=>saved.delete(k)};
 let ids=0;
 const api=context.window.SamanthaScienceNews.create({document:{createElement:t=>new Element(t)},elements,
   fetch:async(path,options)=>{calls.push({path,payload:options?JSON.parse(options.body):null});events.push('fetch');return fetch(path,options);},
   storage,openWindow:(...args)=>{opened.push(args);events.push('window');},openLibrary:()=>events.push('library'),uuid:()=>`req${++ids}`});
 const button=label=>nodes(elements.list).find(i=>i.tagName==='button'&&i.textContent===label);
 return {api,elements,calls,opened,saved,events,button,storage};
}

test('pending news are Czech text with safe source and green pulse',async()=>{
 const f=setup(async()=>response(data()));await f.api.refresh();
 assert(f.elements.entry.classes.has('science-pending'));
 assert.equal(f.elements.list.children.length,1);
 assert(nodes(f.elements.list).some(i=>i.textContent===fixtureItem.title));
 assert.equal(nodes(f.elements.list).find(i=>i.tagName==='a').rel,'noopener noreferrer');
 assert.match(f.elements.status.textContent,/není aktivovaný/);
});
for(const [label,action] of [['Uložit zprávu','save'],['Sledovat','follow'],['Nezařazovat','dismiss']]){
 test(`${label} waits for server acknowledgement, then clears the list and pulse`,async()=>{
  let pending=true,release;
  const f=setup(async(path)=>{
   if(path.endsWith('/decision'))return await new Promise(resolve=>{release=()=>{pending=false;resolve(response({ok:true}));};});
   return response(data(pending?[fixtureItem]:[]));
  });
  await f.api.refresh();const promise=f.button(label).click();
  assert.equal(f.elements.list.children.length,1);assert(f.elements.entry.classes.has('science-pending'));
  assert.equal(f.calls[1].payload.action,action);release();await promise;
  assert.equal(f.elements.list.children.length,0);assert(f.elements.entry.classes.has('science-empty'));
  assert(!f.elements.entry.classes.has('science-pending'));assert.equal(f.saved.size,0);
 });
}
test('lost response preserves card and durable request across reload; different choice blocked',async()=>{
 const f=setup(async(path)=>{if(path.endsWith('/decision'))throw Error('offline');return response(data());});
 await f.api.refresh();await f.button('Uložit zprávu').click();
 assert.equal(f.elements.list.children.length,1);const request=f.calls[1].payload.request_id;
 const second=setup(async()=>response(data()),f.saved);await second.api.refresh();
 await second.button('Nezařazovat').click();assert.equal(second.calls.length,1);
 await second.button('Uložit zprávu').click();
 assert.equal(second.calls[1].payload.request_id,request);
});
test('unavailable storage prevents mutation before request',async()=>{
 const f=setup(async()=>response(data()));await f.api.refresh();
 f.storage.setItem=()=>{throw Error('storage blocked');};await f.button('Sledovat').click();
 assert.equal(f.calls.length,1);assert.equal(f.elements.list.children.length,1);
});
test('translation opens separate window synchronously and never resolves inbox',async()=>{
 const f=setup(async()=>response(data()));await f.api.refresh();f.events.length=0;
 await f.button('Přeložit celou zprávu').click();
 assert.equal(f.events[0],'window');assert.match(f.opened[0][0],/translation\?id=sn_fixture/);
 assert.equal(f.opened[0][2],'noopener');assert.equal(f.elements.list.children.length,1);
 assert.equal(f.calls[1].path,'/api/science-news/translate');
});
test('refresh failure retains pending state and cards; later success clears unknown',async()=>{
 let failure=false;
 const f=setup(async()=>{if(failure)throw Error('offline');return response(data());});
 await f.api.refresh();failure=true;await f.api.refresh();
 assert(f.elements.entry.classes.has('science-pending'));assert(f.elements.entry.classes.has('science-unknown'));
 assert.equal(f.elements.list.children.length,1);
 failure=false;await f.api.refresh();assert(!f.elements.entry.classes.has('science-unknown'));
});
test('stale refresh cannot resurrect already resolved cards',async()=>{
 let release,count=0;
 const f=setup(async()=>{if(count++===0)return await new Promise(r=>{release=()=>r(response(data()));});return response(data([]));});
 const old=f.api.refresh();await f.api.refresh();release();await old;
 assert.equal(f.elements.list.children.length,0);assert(f.elements.entry.classes.has('science-empty'));
});
test('unsafe source is never rendered as a link',async()=>{
 const f=setup(async()=>response(data([{...fixtureItem,source_url:'javascript:alert(1)'}])));
 await f.api.refresh();assert(!nodes(f.elements.list).some(i=>i.tagName==='a'));
});
