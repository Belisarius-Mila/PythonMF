const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const root=path.resolve(__dirname,"../../docs");
const model=require(path.join(root,"vocabulary-en/model.js"));
const vocabulary=JSON.parse(fs.readFileSync(path.join(root,"data/vocabulary-en.json"),"utf8"));
const audio=JSON.parse(fs.readFileSync(path.join(root,"data/vocabulary-en-audio.json"),"utf8"));
const quizCatalog=JSON.parse(fs.readFileSync(path.join(root,"data/vocabulary-en-quiz.json"),"utf8"));
const quiz=require(path.join(root,"vocabulary-en/quiz.js"));
const sentenceAudio={kind:"sentences",items:Object.fromEntries(vocabulary.items.map(i=>[i.uid,{uid:i.uid,sourceEn:i.en,sourceCz:i.cz,sourceSentenceEn:i.sentenceEn,sourceSentenceCz:i.sentenceCz,en:`assets/sentence-en/${i.uid}.mp3`,cz:`assets/sentence-cz/${i.uid}.mp3`}]))};
const html=fs.readFileSync(path.join(root,"vocabulary-en/index.html"),"utf8");
const source=fs.readFileSync(path.join(root,"vocabulary-en/gallery.js"),"utf8");
class Element {
  constructor(tag="div",doc){this.tagName=tag;this.doc=doc;this.children=[];this.dataset={};this.listeners={};this.attributes={};this.className="";this.hidden=false;this.value="";this._text="";
    this.classList={toggle:(name,on)=>{const parts=new Set(this.className.split(/\s+/).filter(Boolean));const add=on===undefined ? !parts.has(name) : on;add ? parts.add(name) : parts.delete(name);this.className=[...parts].join(" ");},add:name=>this.classList.toggle(name,true),remove:name=>this.classList.toggle(name,false),contains:name=>this.className.split(/\s+/).includes(name)};}
  set textContent(value){this._text=String(value);this.children=[];} get textContent(){return this._text+this.children.map(child=>child.textContent).join("");}
  append(...nodes){for(const node of nodes){if(node.tagName==="fragment"){this.append(...node.children);continue;}if(node.parentNode)node.remove();this.children.push(node);node.parentNode=this;}}
  replaceChildren(...nodes){for(const child of this.children)child.parentNode=null;this.children=[];this._text="";this.append(...nodes);}
  remove(){if(this.parentNode)this.parentNode.children=this.parentNode.children.filter(child=>child!==this);this.parentNode=null;}
  addEventListener(name,handler){(this.listeners[name]??=[]).push(handler);} removeEventListener(name,handler){this.listeners[name]=(this.listeners[name]||[]).filter(fn=>fn!==handler);}
  emit(name,extra={}){for(const fn of this.listeners[name]||[])fn({target:this,preventDefault(){},...extra});}
  click(){this.emit("click");} setAttribute(name,value){this.attributes[name]=String(value);}getAttribute(name){return this.attributes[name];}removeAttribute(name){delete this.attributes[name];}
  descendants(){return this.children.flatMap(child=>[child,...child.descendants()]);}
  matches(selector){if(selector.startsWith("."))return this.classList.contains(selector.slice(1));if(selector.startsWith("[data-"))return selector.slice(6,-1).replace(/-([a-z])/g,(_,c)=>c.toUpperCase()) in this.dataset;return this.tagName===selector;}
  querySelectorAll(selector){return this.descendants().filter(node=>node.matches(selector));}querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
  getBoundingClientRect(){return {top:160,width:140,height:180};} focus(){this.doc.activeElement=this;}scrollIntoView(){this.doc.scrolled=this.id;}
}
function storage(map=new Map()){return {map,getItem:key=>map.get(key)||null,setItem:(key,value)=>map.set(key,String(value))};}
async function app({items=vocabulary.items,url="https://example.test/PythonMF/vocabulary-en/",session=storage(),local=storage(),blocked=false,manifest=audio,sentenceManifest=sentenceAudio,failData=false,slowAudio=false,failQuiz=false}={}){
  const doc=new Element("document");doc.doc=doc;doc.title="Vocabulary";
  doc.getElementById=id=>doc.descendants().find(node=>node.id===id)||null;
  doc.createElement=tag=>new Element(tag,doc);doc.createDocumentFragment=()=>new Element("fragment",doc);
  const appRoot=new Element("main",doc);appRoot.dataset={jsonUrl:"../data/vocabulary-en.json",audioUrl:"../data/vocabulary-en-audio.json"};doc.append(appRoot);doc.body=appRoot;
  for(const [,id] of html.matchAll(/\bid="([^"]+)"/g)){const node=new Element("div",doc);node.id=id;appRoot.append(node);}
  for(const [data,values] of [["direction",["czToEn","enToCz"]],["label",["en","cz"]],["practice",["words","sentences"]],["galleryMode",["learn","listen"]]])for(const value of values){const button=new Element("button",doc);button.dataset[data]=value;appRoot.append(button);}
  const listeners={};let scroll=0;const location={href:url};const historyEntries=[{url,state:null}];let historyIndex=0;
  const win={location,innerHeight:844,addEventListener:(name,fn)=>(listeners[name]??=[]).push(fn),scrollTo:value=>{scroll=value.top||0;},get scrollY(){return scroll;},requestAnimationFrame:fn=>fn()};
  let now=0,nextTimer=0;const timers=new Map();
  win.setTimeout=(callback,delay)=>{const id=++nextTimer;timers.set(id,{callback,at:now+delay});return id;};
  win.clearTimeout=id=>timers.delete(id);
  win.crypto=require('node:crypto').webcrypto;win.Blob=Blob;win.URL=URL;win.confirm=()=>true;
  const advance=ms=>{now+=ms;for(const [id,timer] of [...timers])if(timer.at<=now){timers.delete(id);timer.callback();}};
  const emit=(name,extra={})=>{for(const fn of listeners[name]||[])fn(extra);};
  const travel=delta=>{if(!historyEntries[historyIndex+delta])return;historyIndex+=delta;location.href=historyEntries[historyIndex].url;emit("popstate");emit("hashchange");};
  win.history={get state(){return historyEntries[historyIndex].state;},replaceState:(state,unused,url)=>{location.href=new URL(url,location.href).href;historyEntries[historyIndex]={url:location.href,state};},pushState:(state,unused,url)=>{location.href=new URL(url,location.href).href;historyEntries.splice(historyIndex+1);historyEntries.push({url:location.href,state});historyIndex++;},back:()=>travel(-1),forward:()=>travel(1)};
  if(blocked){Object.defineProperty(win,"sessionStorage",{get(){throw Error("blocked")}});Object.defineProperty(win,"localStorage",{get(){throw Error("blocked")}});}else{win.sessionStorage=session;win.localStorage=local;}
  const players=[];class AudioFixture {constructor(url){this.url=url;this.handlers={};this.currentTime=0;this.playCount=0;players.push(this);}addEventListener(name,fn){this.handlers[name]=fn;}removeEventListener(name,fn){if(this.handlers[name]===fn)delete this.handlers[name];}pause(){this.paused=true;}play(){this.played=true;this.playCount++;return Promise.resolve();}}
  const data={...vocabulary,items};
  const ctx=vm.createContext({document:doc,window:win,URL,URLSearchParams,TextEncoder,Audio:AudioFixture,console,fetch:async url=>{if(url.includes("-quiz.json")){if(failQuiz)throw Error("quiz unavailable");return {ok:true,json:async()=>quizCatalog};}if(slowAudio && url.includes("audio"))return new Promise(()=>{});if(failData && !url.includes("audio"))throw Error("offline");const selected=url.includes("sentence-audio")?sentenceManifest:manifest;if(selected===null && url.includes("audio"))throw Error("audio unavailable");return {ok:true,json:async()=>url.includes("audio")?selected:data};}});
  vm.runInContext(fs.readFileSync(path.join(root,"vocabulary-en/model.js"),"utf8"),ctx);
  for(const name of ['learners.js','learner-ui.js','quiz.js'])vm.runInContext(fs.readFileSync(path.join(root,'vocabulary-en',name),'utf8'),ctx);
  vm.runInContext(source.replace('void init();','globalThis.ready=init();')+'\nglobalThis.api={state,context,buildSelection,orderedSelection,openStudy,moveStudy,newRandomRound,returnToGallery,renderGallery,selectionChanged,applyRoute,speakPrompt,speakAnswer,stopAudioPlayback,setPracticeMode};',ctx);
  await ctx.ready;
  return {...ctx.api,doc,win,emit,advance,players,session,local,historyEntries,element:id=>doc.getElementById(id),directions:doc.querySelectorAll("[data-direction]"),labels:doc.querySelectorAll("[data-label]"),practices:doc.querySelectorAll("[data-practice]"),galleryModes:doc.querySelectorAll("[data-gallery-mode]")};
}
const sample=vocabulary.items.slice(0,4);
const quizItems=['ven-0020','ven-0024','ven-0027','ven-0048'].map(uid=>vocabulary.items.find(item=>item.uid===uid));
function quizButtons(view){return view.element('quizChoices').querySelectorAll('button');}
function activePlayer(view){return view.players.find(player=>player.handlers.ended);}
async function loadQuizPictures(view){
  for(const image of view.element('quizChoices').querySelectorAll('img'))image.emit('load');
  await until(()=>activePlayer(view));
}
async function hearQuiz(view){
  await loadQuizPictures(view);activePlayer(view).handlers.ended();
  await until(()=>quizButtons(view).every(button=>!button.disabled));
}
function quizTarget(view){const player=activePlayer(view);assert.ok(player);return vocabulary.items.find(item=>new URL('../'+audio.items[String(item.id)]?.en,view.win.location.href).href===player.url);}
function quizFilter(view,id,value){const field=view.element(id);if(typeof value==='boolean')field.checked=value;else field.value=value;field.emit('change');}
const learners=require('../../docs/vocabulary-en/learners.js');
const retiredUids=['ven-0195','ven-0197','ven-0199','ven-0200','ven-0203','ven-0257','ven-0258','ven-0259','ven-0260','ven-0271'];

test('latest cards use permanent creation IDs, then intersect learner and topic filters without reordering input',()=>{
  const items=[{...quizItems[0],id:2,order:99},{...quizItems[1],id:8,order:1},{...quizItems[2],id:6,order:2},{...quizItems[3],id:20,active:false}];
  const before=JSON.stringify(items);
  assert.deepEqual([...model.latestIds(items,2)],[items[1].uid,items[2].uid]);
  assert.deepEqual(model.select([items[0]],{recentCount:2},items),[]);
  assert.deepEqual(model.select(items,{recentCount:2}).map(model.key),[items[1].uid,items[2].uid]);
  assert.equal(JSON.stringify(items),before);
  for(const bad of [-1,1.5,5001,Infinity,true,{},[20],'twenty'])assert.equal(model.recentCount(bad),0);
});
test('recent filter keeps its number through study, history, reload and reset',async()=>{
  const view=await app();quizFilter(view,'recentOnly',true);
  assert.equal(view.buildSelection().length,20);assert.ok(view.buildSelection().every(i=>i.id>=503));
  view.openStudy('ven-0521');view.returnToGallery();
  assert.equal(view.state.recentCount,20);
  const after=await app({url:view.win.location.href,session:view.session,local:view.local});
  assert.equal(after.state.recentCount,20);assert.equal(after.element('recentCount').value,'20');
  after.element('resetButton').click();assert.equal(after.state.recentCount,0);assert.equal(after.buildSelection().length,512);
});
test('reviewed quiz sources reject missing audio, altered meanings, retired and changed images',()=>{
  assert.equal(quiz.eligible(quizItems,audio,quizCatalog).length,4);
  for(const change of [{active:false},{cz:'changed'},{en:'changed'},{image:'different.webp'}])assert.equal(quiz.eligible([{...quizItems[0],...change}],audio,quizCatalog).length,0);
  assert.equal(quiz.eligible(quizItems,null,quizCatalog).length,0);
  assert.equal(quiz.eligible(quizItems,audio,null).length,0);
});
test('every reviewed target has four compatible distinct options inside its pool',()=>{
  const pool=quiz.eligible(vocabulary.items,audio,quizCatalog);
  for(const target of pool){
    const q=quiz.question(target,pool,audio,quizCatalog,()=>.37);assert.ok(q,target.uid);
    assert.equal(q.choices.length,4);assert.equal(new Set(q.choices.map(model.key)).size,4);
    assert.equal(q.choices.filter(item=>item.uid===target.uid).length,1);
    for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)assert.ok(quiz.compatible(q.choices[i],q.choices[j],audio,quizCatalog));
  }
  const deer=vocabulary.items.find(i=>i.en==='deer'),stag=vocabulary.items.find(i=>i.en==='stag');
  assert.equal(quiz.compatible(deer,stag,audio,quizCatalog),false);
  const copy={...quizItems[1],image:quizItems[0].image};assert.equal(quiz.compatible(quizItems[0],copy,audio,quizCatalog),false);
  assert.equal(quiz.question(quizItems[0],quizItems.slice(0,3),audio,quizCatalog),null);
  const blue=vocabulary.items.find(i=>i.en==='blue'),two=vocabulary.items.find(i=>i.en==='two');
  assert.equal(quiz.compatible(blue,quizItems[0],audio,quizCatalog),false);
  assert.equal(quiz.compatible(two,quizItems[0],audio,quizCatalog),false);
});
test('color and number questions use four options of the same kind, never an arbitrary colored or counted object',async()=>{
  const pool=quiz.eligible(vocabulary.items,audio,quizCatalog);
  for(const en of ['blue','two']){
    const target=pool.find(item=>item.en===en),q=quiz.question(target,pool,audio,quizCatalog,()=>.4);
    assert.ok(q);assert.ok(q.choices.every(item=>quizCatalog.entries[item.uid].format===quizCatalog.entries[target.uid].format));
  }
  const view=await app();view.element('quizTab').click();quizFilter(view,'quizTopic','topic-10');
  assert.equal(view.element('quizStart').disabled,false);view.element('quizStart').click();
  assert.ok(quizButtons(view).every(button=>quizCatalog.entries[button.dataset.uid].format==='colors'));
});
test('game requires loaded pictures and completed prompt, hides labels, reveals correct choice and ignores double clicks',async()=>{
  const view=await app({items:quizItems}),original=view.local.getItem(learners.KEY);
  view.element('quizTab').click();view.element('quizStart').click();
  assert.equal(view.state.view,'quiz');assert.equal(view.players.length,0);assert.equal(quizButtons(view).length,4);
  for(const button of quizButtons(view)){assert.ok(button.disabled);assert.equal(button.querySelector('.quiz-caption').textContent.trim(),'');assert.match(button.getAttribute('aria-label'),/^Vybrat obrázek [1-4]$/);}
  await loadQuizPictures(view);const target=quizTarget(view),button=quizButtons(view).find(b=>b.dataset.uid===target.uid);
  button.click();assert.equal(view.element('quizNext').disabled,true);
  activePlayer(view).handlers.ended();await until(()=>!button.disabled);button.click();button.click();
  assert.equal(quizButtons(view).filter(b=>b.classList.contains('is-correct')).length,1);
  assert.equal(button.querySelector('.quiz-caption').textContent,target.en);assert.equal(view.element('quizNext').disabled,false);
  assert.equal(view.local.getItem(learners.KEY),original);assert.ok(activePlayer(view));
  view.element('quizNext').click();assert.equal(view.element('quizPosition').textContent,'Slovíčko 2 z 4');
});
test('wrong answer is marked, only correct label is revealed and prompt is replayed',async()=>{
  const view=await app({items:quizItems});view.element('quizTab').click();view.element('quizStart').click();
  await loadQuizPictures(view);const target=quizTarget(view);activePlayer(view).handlers.ended();
  await until(()=>quizButtons(view).every(b=>!b.disabled));
  const wrong=quizButtons(view).find(b=>b.dataset.uid!==target.uid);wrong.click();
  assert.ok(wrong.classList.contains('is-wrong'));assert.equal(wrong.querySelector('.quiz-mark').textContent,'×');
  assert.equal(wrong.querySelector('.quiz-caption').textContent.trim(),'');
  const correct=quizButtons(view).find(b=>b.classList.contains('is-correct'));assert.equal(correct.dataset.uid,target.uid);
  assert.equal(correct.querySelector('.quiz-caption').textContent,target.en);
  assert.match(view.element('quizMessage').textContent,/Správný je označený/);assert.ok(activePlayer(view));
});
test('a finite quiz round asks each target once, scores once and only restarts explicitly',async()=>{
  const view=await app({items:quizItems}),seen=new Set();view.element('quizTab').click();view.element('quizStart').click();
  for(let i=0;i<4;i++){
    await loadQuizPictures(view);const target=quizTarget(view);assert.ok(!seen.has(target.uid));seen.add(target.uid);
    activePlayer(view).handlers.ended();await until(()=>quizButtons(view).every(b=>!b.disabled));
    const correct=quizButtons(view).find(b=>b.dataset.uid===target.uid);correct.click();correct.click();
    view.element('quizNext').click();
  }
  assert.equal(view.element('quizEnd').hidden,false);assert.equal(view.element('quizRound').hidden,true);
  assert.equal(view.element('quizResult').textContent,'Správně na první pokus: 4 z 4.');assert.equal(activePlayer(view),undefined);
  view.element('quizAgain').click();assert.equal(view.element('quizPosition').textContent,'Slovíčko 1 z 4');
});
test('all hard mode uses shared hard flags and pending or failed word audio prevents guessing',async()=>{
  const items=quizItems.map((item,index)=>({...item,hardTraining:index<3})),view=await app({items});
  view.element('quizTab').click();quizFilter(view,'quizHard',true);assert.ok(view.element('quizStart').disabled);
  const slow=await app({items:quizItems,slowAudio:true});slow.element('quizTab').click();assert.ok(slow.element('quizStart').disabled);
  const failed=await app({items:quizItems,manifest:null});failed.element('quizTab').click();assert.ok(failed.element('quizStart').disabled);assert.match(failed.element('quizPoolNotice').textContent,/Zvuk.*nepodařilo/);
});
test('changed personal membership during a question cancels the round instead of broadening its pool',async()=>{
  const local=storage(),value=learners.empty();value.profiles.C.selected=quizItems.map(model.key);local.setItem(learners.KEY,JSON.stringify(value));
  const view=await app({local});view.element('quizTab').click();quizFilter(view,'quizLearner','C');view.element('quizStart').click();await loadQuizPictures(view);
  const playing=activePlayer(view);value.profiles.C.selected=quizItems.slice(0,3).map(model.key);local.setItem(learners.KEY,JSON.stringify(value));view.emit('storage',{key:learners.KEY});
  assert.ok(playing.paused);assert.equal(view.element('quizSetup').hidden,false);assert.ok(view.element('quizStart').disabled);assert.match(view.element('quizPoolNotice').textContent,/Výběr se změnil/);
});
test('quiz combines personal difficult words and one topic and never borrows options outside the filter',async()=>{
  const local=storage(),value=learners.empty();value.profiles.D.selected=quizItems.map(model.key);value.profiles.D.hard=quizItems.slice(0,3).map(model.key);
  local.setItem(learners.KEY,JSON.stringify(value));const saved=local.getItem(learners.KEY),view=await app({local});
  view.element('quizTab').click();quizFilter(view,'quizLearner','D');quizFilter(view,'quizTopic','topic-06');quizFilter(view,'quizHard',true);
  assert.ok(view.element('quizStart').disabled);assert.match(view.element('quizPoolNotice').textContent,/čtyři/);
  quizFilter(view,'quizHard',false);assert.equal(view.element('quizStart').disabled,false);view.element('quizStart').click();
  assert.deepEqual(new Set(quizButtons(view).map(b=>b.dataset.uid)),new Set(quizItems.map(model.key)));
  assert.equal(local.getItem(learners.KEY),saved);
});
test('latest quiz selection is global before the learner intersection and preserves editable count',async()=>{
  const local=storage(),value=learners.empty();value.profiles.A.selected=quizItems.map(model.key);local.setItem(learners.KEY,JSON.stringify(value));
  const view=await app({local});view.element('quizTab').click();quizFilter(view,'quizLearner','A');quizFilter(view,'quizRecentOnly',true);
  assert.ok(view.element('quizStart').disabled);assert.match(view.element('quizPoolNotice').textContent,/0 slovíček/);
  quizFilter(view,'quizRecentCount','5000');assert.equal(view.element('quizStart').disabled,false);
  quizFilter(view,'quizRecentCount','2.5');assert.ok(view.element('quizStart').disabled);assert.match(view.element('quizPoolNotice').textContent,/celé číslo/);
});
test('game leaves gallery bookmark, learner data and random study sequence intact through Back and Forward',async()=>{
  const view=await app({items:quizItems});view.openStudy(quizItems[0].uid,'random');
  view.setPracticeMode('sentences');
  const sequence=view.state.sequence.map(model.key),last=view.state.lastUid,stored=view.local.getItem('vocabulary-en.last-card.v1');
  view.element('quizTab').click();view.element('quizStart').click();await loadQuizPictures(view);
  const player=activePlayer(view);assert.ok(!player.url.includes('/sentence-en/'));view.element('quizBack').click();
  assert.equal(view.state.view,'study');assert.ok(player.paused);assert.equal(view.state.lastUid,last);assert.deepEqual(view.state.sequence.map(model.key),sequence);
  assert.equal(view.state.practice,'sentences');
  assert.equal(view.local.getItem('vocabulary-en.last-card.v1'),stored);
  view.win.history.forward();assert.equal(view.state.view,'quiz');assert.equal(view.element('quizSetup').hidden,false);
});
test('game can reopen from its link without storage or automatic speech and failed catalog leaves gallery usable',async()=>{
  const view=await app({items:quizItems,blocked:true,url:'https://example.test/PythonMF/vocabulary-en/#game=listen-pictures'});
  assert.equal(view.state.view,'quiz');assert.equal(view.players.filter(p=>p.played).length,0);assert.equal(view.element('quizStart').disabled,false);
  view.element('quizBack').click();assert.equal(view.state.view,'gallery');
  const failed=await app({failQuiz:true});failed.element('quizTab').click();assert.ok(failed.element('quizStart').disabled);assert.match(failed.element('quizPoolNotice').textContent,/nepodařilo načíst/);
  failed.element('quizBack').click();assert.equal(failed.buildSelection().length,512);
});
test('image failure can be skipped without a score and a late audio error cannot overwrite another screen',async()=>{
  const view=await app({items:quizItems});view.element('quizTab').click();view.element('quizStart').click();
  view.element('quizChoices').querySelector('img').emit('error');assert.equal(view.element('quizNext').disabled,false);
  assert.match(view.element('quizMessage').textContent,/nezapočítá/);view.element('quizNext').click();
  await loadQuizPictures(view);const lateError=activePlayer(view).handlers.error;
  view.element('quizChange').click();lateError();await Promise.resolve();
  assert.equal(view.element('quizSetup').hidden,false);assert.equal(view.element('quizRound').hidden,true);
});
async function until(predicate){for(let n=0;n<200;n++){if(predicate())return;await new Promise(resolve=>setTimeout(resolve,10));}assert.fail('UI did not settle');}
async function unlock(view,pin='1234'){
  view.element('pinInput').value=pin;view.element('pinRepeat').value=pin;view.element('unlockButton').click();
  await until(()=>!view.element('learnerEditor').hidden||/správný|nepodporuje/.test(view.element('settingsNotice').textContent));
}
function chooseWord(view,uid,checked=true){const input=view.element('settingsGroups').querySelectorAll('.learner-word-check').find(input=>input.dataset.uid===uid);assert.ok(input);input.checked=checked;input.emit('change');}
function chooseUser(view,id){view.element('learnerSelect').value=id;view.element('learnerSelect').emit('change');}

test('retired cards keep their identities but cannot enter selection, random practice or restored sequences',async()=>{
  assert.equal(vocabulary.items.length,522);
  assert.deepEqual(vocabulary.items.filter(item=>item.active===false).map(model.key),retiredUids);
  const selected=model.ordered(vocabulary.items,{},vocabulary.catalog);
  assert.equal(selected.length,512);assert.ok(selected.every(item=>!retiredUids.includes(item.uid)));
  assert.deepEqual(model.restoreSequence([...retiredUids,'ven-0020'],vocabulary.items).map(model.key),['ven-0020']);
  const view=await app({url:'https://example.test/PythonMF/vocabulary-en/#card=ven-0257'});
  assert.equal(view.state.view,'gallery');assert.equal(view.state.currentItem,null);
  assert.match(view.element('galleryNotice').textContent,/vyřazena/);
  assert.ok(retiredUids.every(uid=>!view.element(`tile-${uid}`)));
});

test('teaching type intersects topics and learner selection and survives study, return and reload',async()=>{
  const local=storage(),value=learners.empty();value.profiles.A.selected=['ven-0057','ven-0020',...retiredUids];
  local.setItem(learners.KEY,JSON.stringify(value));const view=await app({local});chooseUser(view,'A');
  view.element('teachingTypeSelect').value='interaction';view.element('teachingTypeSelect').emit('change');
  assert.deepEqual(Array.from(view.orderedSelection(),model.key),['ven-0057']);
  view.element('tile-ven-0057').click();view.returnToGallery();
  assert.equal(view.state.teachingType,'interaction');assert.equal(view.doc.activeElement.id,'tile-ven-0057');
  const after=await app({url:view.win.location.href,local,session:view.session});
  assert.equal(after.state.teachingType,'interaction');assert.equal(after.element('teachingTypeSelect').value,'interaction');
  assert.deepEqual(Array.from(after.orderedSelection(),model.key),['ven-0057']);
  after.state.topics=['topic-06'];after.selectionChanged();assert.equal(after.orderedSelection().length,0);
  after.element('resetButton').click();assert.equal(after.state.teachingType,'all');assert.equal(after.orderedSelection().length,512);
});

test('all four learner profiles preserve retired selected and difficult IDs through visible bulk edits, save and backup',async()=>{
  const local=storage(),value=learners.empty(),pin=await learners.makePin('1234',require('node:crypto').webcrypto);
  for(const id of learners.IDS)value.profiles[id]={selected:['ven-0020',...retiredUids],hard:['ven-0020',...retiredUids],pin};
  local.setItem(learners.KEY,JSON.stringify(value));const original=local.getItem(learners.KEY),view=await app({local});
  assert.equal(local.getItem(learners.KEY),original);
  for(const id of learners.IDS){
    chooseUser(view,id);view.element('editLearnerHard').click();await unlock(view);
    const inputs=view.element('settingsGroups').querySelectorAll('.learner-word-check');
    assert.deepEqual(inputs.map(input=>input.dataset.uid),['ven-0020']);
    chooseWord(view,'ven-0020',false);view.element('saveLearner').click();
    const saved=JSON.parse(local.getItem(learners.KEY));assert.deepEqual(saved.profiles[id].selected,value.profiles[id].selected);
    assert.deepEqual(saved.profiles[id].hard,retiredUids);assert.deepEqual(saved.profiles[id].pin,pin);
    const restored=learners.parseBackup(JSON.stringify(learners.backup(saved)));
    assert.deepEqual(restored.profiles[id].selected,value.profiles[id].selected);assert.deepEqual(restored.profiles[id].hard,retiredUids);
  }
  // A visible topic bulk change must leave every hidden membership intact too.
  view.element('settingsTab').click();await unlock(view);
  view.element('settingsSearch').value='cat';view.element('settingsSearch').emit('input');
  const group=view.element('settingsGroups').querySelector('.learner-group-check');group.checked=false;group.emit('change');
  view.element('saveLearner').click();const saved=JSON.parse(local.getItem(learners.KEY));
  assert.deepEqual(saved.profiles.D.selected,retiredUids);assert.deepEqual(saved.profiles.D.hard,retiredUids);
});

test('importing a backup with retired cards preserves them and explains their hidden state',async()=>{
  const view=await app();view.element('settingsTab').click();await unlock(view);
  const incoming=learners.backup(learners.empty());incoming.profiles.A.selected=['ven-0020',...retiredUids];incoming.profiles.A.hard=[retiredUids[0]];
  view.element('learnerFile').files=[{size:1000,text:async()=>JSON.stringify(incoming)}];view.element('learnerFile').emit('change');
  await until(()=>/Načtený návrh/.test(view.element('settingsNotice').textContent));
  assert.match(view.element('settingsNotice').textContent,/10 vyřazených karet/);view.element('saveLearner').click();
  const saved=JSON.parse(view.local.getItem(learners.KEY));assert.deepEqual(saved.profiles.A.selected,incoming.profiles.A.selected);
  assert.deepEqual(saved.profiles.A.hard,incoming.profiles.A.hard);
});

test('word type includes multiword names, interactions are separate and empty idiom filter is usable',async()=>{
  assert.equal(model.select(vocabulary.items,{teachingType:'word'}).length,492);
  assert.equal(model.select(vocabulary.items,{teachingType:'interaction'}).length,20);
  assert.equal(model.select(vocabulary.items,{teachingType:'idiom'}).length,0);
  for(const uid of ['ven-0004','ven-0017','ven-0131','ven-0145'])assert.ok(model.select(vocabulary.items,{teachingType:'word'}).some(i=>i.uid===uid));
  const view=await app({url:'https://example.test/PythonMF/vocabulary-en/#teachingType=idiom'});
  assert.equal(view.orderedSelection().length,0);assert.equal(view.element('emptyState').hidden,false);
  view.element('emptyResetButton').click();assert.equal(view.orderedSelection().length,512);
  const future={...sample[0],uid:'ven-future-idiom',teachingType:'idiom'};
  assert.deepEqual(model.select([...sample,future],{teachingType:'idiom'}).map(model.key),['ven-future-idiom']);
  const legacy=sample.map(({teachingType,active,...item})=>item);
  assert.equal(model.select(legacy,{teachingType:'word'}).length,4);
});
test('settings saves only A, keeps eighteen topic definitions, and a fresh browser has independent empty profiles',async()=>{
  const view=await app({items:sample});view.element('settingsTab').click();await unlock(view);
  chooseWord(view,sample[0].uid);chooseWord(view,sample[1].uid);assert.equal(view.local.getItem(learners.KEY),null);
  view.element('saveLearner').click();chooseUser(view,'A');assert.equal(view.state.view,'gallery');assert.equal(view.buildSelection().length,2);assert.equal(view.state.data.catalog.groups.length,18);
  const saved=JSON.parse(view.local.getItem(learners.KEY));assert.equal(saved.profiles.B.selected.length,0);assert.ok(saved.profiles.A.pin.hash);assert.ok(!view.local.getItem(learners.KEY).includes('1234'));
  const reload=await app({items:sample,local:view.local,session:view.session});assert.equal(reload.state.learner,'A');assert.equal(reload.buildSelection().length,2);
  const other=await app({items:sample});chooseUser(other,'A');assert.equal(other.buildSelection().length,0);assert.equal(view.buildSelection().length,2);
});
test('personal hard editing requires the PIN and stays within the selected vocabulary for learning and listening',async()=>{
  const view=await app({items:sample});view.element('settingsTab').click();await unlock(view);chooseWord(view,sample[0].uid);chooseWord(view,sample[1].uid);view.element('saveLearner').click();chooseUser(view,'A');
  view.element('editLearnerHard').click();await unlock(view,'4321');assert.equal(view.element('learnerEditor').hidden,true);
  await unlock(view);assert.equal(view.element('settingsGroups').querySelectorAll('.learner-word-check').length,2);chooseWord(view,sample[1].uid);view.element('saveLearner').click();
  view.element('learnerHardFilter').click();assert.deepEqual(view.buildSelection().map(i=>i.uid),[sample[1].uid]);
  view.element('tile-'+sample[1].uid).click();assert.equal(view.state.view,'study');assert.equal(view.state.sequence.length,1);view.returnToGallery();
  chooseUser(view,'B');assert.equal(view.buildSelection().length,0);chooseUser(view,'all');assert.equal(view.buildSelection().length,4);
});
test('backup import previews one user, requires Save, preserves the local PIN and other users, and rejects malformed files',async()=>{
  const view=await app({items:sample});view.element('settingsTab').click();await unlock(view);chooseWord(view,sample[0].uid);view.element('saveLearner').click();
  const before=view.local.getItem(learners.KEY),pin=JSON.parse(before).profiles.A.pin;
  view.element('settingsTab').click();await unlock(view);const file=view.element('learnerFile');file.files=[{size:1,text:async()=>'{'}];file.emit('change');await until(()=>view.element('settingsNotice').textContent.includes('platný JSON'));assert.equal(view.local.getItem(learners.KEY),before);
  const backup=learners.backup(learners.empty());backup.profiles.A.selected=[sample[2].uid];backup.profiles.A.hard=[sample[2].uid];backup.profiles.B.selected=[sample[3].uid];
  file.files=[{size:200,text:async()=>JSON.stringify(backup)}];file.emit('change');await until(()=>view.element('settingsNotice').textContent.includes('Načtený návrh'));assert.equal(view.local.getItem(learners.KEY),before);
  view.element('saveLearner').click();const saved=JSON.parse(view.local.getItem(learners.KEY));assert.deepEqual(saved.profiles.A.selected,[sample[2].uid]);assert.deepEqual(saved.profiles.A.pin,pin);assert.deepEqual(saved.profiles.B.selected,[]);
});
test('failed persistence keeps the editor open and corrupt storage does not block the shared gallery',async()=>{
  const local=storage();local.setItem=()=>{throw Error('quota');};const view=await app({items:sample,local});view.element('settingsTab').click();await unlock(view);chooseWord(view,sample[0].uid);view.element('saveLearner').click();
  assert.equal(view.state.view,'settings');assert.match(view.element('settingsNotice').textContent,/nepodařilo uložit/);assert.equal(view.local.getItem(learners.KEY),null);
  const broken=storage();broken.setItem(learners.KEY,'broken');const normal=await app({items:sample,local:broken,url:'https://example.test/#learner=A'});
  assert.equal(normal.state.learner,'all');assert.equal(normal.buildSelection().length,4);assert.equal(normal.element('learnerSelect').disabled,true);assert.equal(broken.getItem(learners.KEY),'broken');
});
test('other-tab changes and direct links cannot continue learning removed personal words',async()=>{
  const local=storage(),value=learners.empty();value.profiles.A.selected=[sample[0].uid,sample[1].uid];local.setItem(learners.KEY,JSON.stringify(value));
  const view=await app({items:sample,local,url:'https://example.test/#learner=A'});view.element('tile-'+sample[0].uid).click();assert.equal(view.state.view,'study');
  value.profiles.A.selected=[sample[1].uid];local.setItem(learners.KEY,JSON.stringify(value));view.emit('storage',{key:learners.KEY});
  assert.equal(view.state.view,'gallery');assert.equal(view.buildSelection().length,1);assert.match(view.element('galleryNotice').textContent,/není v aktuálním výběru/);
  const linked=await app({items:sample,local,url:'https://example.test/#learner=A&card='+sample[0].uid});assert.equal(linked.state.view,'gallery');assert.equal(linked.state.currentItem,null);
});
test('a late import cannot replace newer manual edits or the next user draft',async()=>{
  const view=await app({items:sample});view.element('settingsTab').click();await unlock(view);
  const backup=learners.backup(learners.empty());backup.profiles.A.selected=[sample[2].uid];let finish;
  const file=view.element('learnerFile');file.files=[{size:200,text:()=>new Promise(resolve=>{finish=resolve;})}];file.emit('change');
  chooseWord(view,sample[0].uid);finish(JSON.stringify(backup));await new Promise(resolve=>setImmediate(resolve));view.element('saveLearner').click();
  assert.deepEqual(JSON.parse(view.local.getItem(learners.KEY)).profiles.A.selected,[sample[0].uid]);
  view.element('settingsTab').click();await unlock(view);let next;file.files=[{size:200,text:()=>new Promise(resolve=>{next=resolve;})}];file.emit('change');
  view.element('settingsUser').value='B';view.element('settingsUser').emit('change');await unlock(view);chooseWord(view,sample[1].uid);
  next(JSON.stringify(backup));await new Promise(resolve=>setImmediate(resolve));view.element('saveLearner').click();
  assert.deepEqual(JSON.parse(view.local.getItem(learners.KEY)).profiles.B.selected,[sample[1].uid]);
});
test("gallery listening plays the English WORD with Czech labels and sentence practice without opening or changing navigation",async()=>{
  const view=await app();view.labels[1].click();view.state.practice='sentences';view.win.scrollTo({top:1250});
  const before={url:view.win.location.href,history:view.historyEntries.length,last:view.state.lastUid,local:[...view.local.map],session:[...view.session.map]};
  view.galleryModes[1].click();const tile=view.element('tile-ven-0020');tile.click();
  assert.equal(view.state.view,'gallery');assert.equal(view.state.currentItem,null);assert.equal(view.win.scrollY,1250);
  assert.equal(view.win.location.href,before.url);assert.equal(view.historyEntries.length,before.history);assert.equal(view.state.lastUid,before.last);
  assert.deepEqual([...view.local.map],before.local);assert.deepEqual([...view.session.map],before.session);
  assert.equal(tile.getAttribute('aria-label'),'Přehrát anglicky: cat');assert.equal(view.element('galleryModeHint').textContent,'Anglicky: cat');
  assert.equal(view.players.filter(p=>p.played).length,1);assert.ok(view.players.find(p=>p.played).url.endsWith(audio.items['20'].en));
  view.advance(1000);assert.equal(tile.querySelector('.tile-label').textContent,'kočka');
});
test("listening shows Czech for exactly one second then restores the English caption without changing navigation",async()=>{
  for(const direction of ['czToEn','enToCz']){
    const view=await app({url:`https://example.test/PythonMF/vocabulary-en/#direction=${direction}`});view.galleryModes[1].click();const tile=view.element('tile-ven-0020'),caption=tile.querySelector('.tile-label');
    const before={url:view.win.location.href,history:view.historyEntries.length,session:[...view.session.map],local:[...view.local.map]};
    tile.click();assert.equal(caption.textContent,'kočka');assert.equal(caption.lang,'cs');
    view.advance(999);assert.equal(caption.textContent,'kočka');view.advance(1);assert.equal(caption.textContent,'cat');assert.equal(caption.lang,'en');
    assert.equal(view.state.view,'gallery');assert.equal(view.win.location.href,before.url);assert.equal(view.historyEntries.length,before.history);
    assert.deepEqual([...view.session.map],before.session);assert.deepEqual([...view.local.map],before.local);
  }
});
test("repeated clicks renew the translation second and switching tiles restores the previous caption immediately",async()=>{
  const view=await app();view.galleryModes[1].click();const cat=view.element('tile-ven-0020'),cow=view.element('tile-ven-0024');
  cat.click();view.advance(600);cat.click();view.advance(400);assert.equal(cat.querySelector('.tile-label').textContent,'kočka');
  view.advance(599);assert.equal(cat.querySelector('.tile-label').textContent,'kočka');view.advance(1);assert.equal(cat.querySelector('.tile-label').textContent,'cat');
  cat.click();view.advance(500);cow.click();assert.equal(cat.querySelector('.tile-label').textContent,'cat');assert.equal(cow.querySelector('.tile-label').textContent,'kráva');
  view.advance(500);assert.equal(cow.querySelector('.tile-label').textContent,'kráva');view.advance(500);assert.equal(cow.querySelector('.tile-label').textContent,'cow');
});
test("changing mode, labels, filters or leaving the page cancels the temporary translation",async()=>{
  const view=await app();view.galleryModes[1].click();const cat=view.element('tile-ven-0020');cat.click();view.galleryModes[0].click();
  assert.equal(cat.querySelector('.tile-label').textContent,'cat');view.advance(1000);assert.equal(cat.querySelector('.tile-label').textContent,'cat');
  view.galleryModes[1].click();cat.click();view.labels[1].click();view.advance(1000);assert.equal(view.element('tile-ven-0020').querySelector('.tile-label').textContent,'kočka');
  view.labels[0].click();const old=view.element('tile-ven-0020');old.click();view.state.query='cow';view.selectionChanged();
  assert.equal(old.querySelector('.tile-label').textContent,'cat');const cow=view.element('tile-ven-0024');cow.click();view.emit('pagehide');view.advance(1000);
  assert.equal(cow.querySelector('.tile-label').textContent,'cow');
});
test("repeating a tile restarts its audio, and another tile stops the previous word",async()=>{
  const view=await app();view.galleryModes[1].click();view.element('tile-ven-0020').click();const cat=view.players.find(p=>p.played);cat.currentTime=1;
  view.element('tile-ven-0020').click();assert.equal(cat.playCount,2);assert.equal(cat.currentTime,0);
  view.element('tile-ven-0024').click();assert.equal(cat.paused,true);assert.ok(view.players.some(p=>p.played && p.url.endsWith(audio.items['24'].en)));
});
test("mode switch keeps the same tiles, scroll and filters, stops sound and restores learning click",async()=>{
  const view=await app();view.state.topics=['topic-06'];view.selectionChanged();view.galleryModes[1].click();const cat=view.element('tile-ven-0020');view.win.scrollTo({top:650});cat.click();
  view.galleryModes[0].click();assert.equal(view.element('tile-ven-0020'),cat);assert.equal(view.win.scrollY,650);assert.deepEqual([...view.state.topics],['topic-06']);
  assert.ok(view.players.filter(p=>p.played).every(p=>p.paused));assert.equal(cat.getAttribute('aria-label'),'Učit se: cat');
  assert.equal(view.galleryModes[0].getAttribute('aria-pressed'),'true');assert.equal(view.galleryModes[1].getAttribute('aria-pressed'),'false');
  cat.click();assert.equal(view.state.view,'study');assert.equal(view.state.currentItem.uid,'ven-0020');
});
test("missing or mismatched word audio leaves gallery accessible and reports the problem in its visible mode bar",async()=>{
  for(const manifest of [null,{items:{20:{sourceEn:'cat',sourceCz:'wrong',en:'wrong.mp3'}}}]){
    const view=await app({manifest});view.galleryModes[1].click();view.element('tile-ven-0020').click();
    assert.equal(view.state.view,'gallery');assert.ok(view.players.every(p=>!p.played));assert.match(view.element('galleryModeHint').textContent,/Zvuk zatím není/);
    view.galleryModes[0].click();view.element('tile-ven-0020').click();assert.equal(view.state.view,'study');
  }
});
test("filtering, explicit study and leaving the page stop gallery speech; the last studied card stays unchanged",async()=>{
  const view=await app();view.openStudy('ven-0118');view.returnToGallery();const last=view.state.lastUid;view.galleryModes[1].click();view.element('tile-ven-0020').click();
  view.state.query='cow';view.selectionChanged();assert.ok(view.players.filter(p=>p.played).every(p=>p.paused));assert.equal(view.state.galleryMode,'listen');assert.equal(view.state.lastUid,last);
  view.element('tile-ven-0024').click();view.element('shuffleButton').click();assert.equal(view.state.view,'study');assert.ok(view.players.filter(p=>p.played).every(p=>p.paused));
  view.returnToGallery();view.element('tile-ven-0024').click();view.emit('pagehide');assert.ok(view.players.filter(p=>p.played).every(p=>p.paused));
});
test("a late gallery playback failure cannot overwrite the next mode hint",async()=>{
  const view=await app();view.galleryModes[1].click();view.element('tile-ven-0020').click();const player=view.players.find(p=>p.played);const error=player.handlers.error;
  error();view.galleryModes[0].click();await Promise.resolve();await Promise.resolve();
  assert.equal(view.element('galleryModeHint').textContent,'Kliknutí otevře kartu.');
});
test("listening mode lasts only for the open page and does not change stored study context",async()=>{
  const before=await app();before.galleryModes[1].click();before.element('tile-ven-0020').click();
  const after=await app({url:before.win.location.href,session:before.session,local:before.local});
  assert.equal(after.state.galleryMode,'learn');assert.equal('galleryMode' in after.context(),false);
  after.element('tile-ven-0020').click();assert.equal(after.state.view,'study');
});
test("switching translation direction preserves current card and the ordered selection",async()=>{
  const view=await app({items:sample});view.openStudy(sample[0].uid);const first=view.state.currentItem.uid;const sequence=[...view.state.sequence];view.directions[1].click();assert.equal(view.state.currentItem.uid,first);assert.deepEqual([...view.state.sequence],sequence);view.moveStudy(1);assert.notEqual(view.state.currentItem.uid,first);assert.equal(view.state.revealed,false);
});
test("explicit random practice shows every card once in each of three rounds despite direction changes",async()=>{
  const view=await app();view.element("shuffleButton").click();
  for(let round=0;round<3;round++){
    const seen=new Set();for(let i=0;i<512;i++){view.directions[i%2].click();assert.ok(!seen.has(view.state.currentItem.uid));seen.add(view.state.currentItem.uid);if(i<511)view.element("nextButton").click();}
    assert.equal(seen.size,512);assert.equal(view.element("nextButton").hidden,true);assert.match(view.element("roundStatus").textContent,/konec/);if(round<2)view.element("newRoundButton").click();
  }
});
test("a new random round never immediately repeats the last card",async()=>{
  const view=await app({items:sample});view.openStudy("","random");for(let i=0;i<3;i++)view.moveStudy(1);const last=view.state.currentItem.uid;view.newRandomRound();assert.notEqual(view.state.currentItem.uid,last);assert.equal(view.state.index,0);
});
test("empty, singleton, and changed filter selections work",async()=>{
  const empty=await app({items:[]});empty.openStudy("","random");assert.equal(empty.state.view,"gallery");assert.equal(empty.element("shuffleButton").disabled,true);
  const single=await app({items:sample.slice(0,1)});single.openStudy("","random");single.newRandomRound();assert.equal(single.state.currentItem.uid,sample[0].uid);assert.equal(single.element("nextButton").hidden,true);
  const view=await app();view.state.filter="selected";view.selectionChanged();assert.equal(view.element("totalCount").textContent,"107");view.openStudy("","random");assert.equal(view.state.sequence.length,107);
});
test("topics combine by union while source, part, difficulty and selection narrow by intersection",()=>{
  const animals=model.select(vocabulary.items,{topics:["topic-06"]});const benjiAnimals=model.select(vocabulary.items,{topics:["topic-06"],sources:["benji"]});assert.equal(animals.length,42);assert.equal(benjiAnimals.length,4);
  const union=model.select(vocabulary.items,{topics:["topic-06","topic-05"],sources:["benji"],parts:["noun"]});assert.ok(union.every(i=>i.sourceIds.includes("benji") && i.partOfSpeech.includes("noun") && i.topicIds.some(t=>["topic-06","topic-05"].includes(t))));assert.ok(union.length>6);
  assert.equal(model.select(vocabulary.items,{query:"orisky"})[0].en,"nuts");assert.equal(model.select(vocabulary.items,{query:"orange"}).length,2);
});
test("gallery is the default; all 512 active tiles occur once and language never changes order",async()=>{
  const view=await app();assert.equal(view.state.view,"gallery");assert.equal(view.element("studyView").hidden,true);const tiles=view.element("galleryGroups").querySelectorAll(".vocab-tile");assert.equal(tiles.length,512);assert.equal(new Set(tiles.map(t=>t.dataset.uid)).size,512);
  const order=tiles.map(t=>t.dataset.uid);view.labels[1].click();assert.deepEqual(view.element("galleryGroups").querySelectorAll(".vocab-tile").map(t=>t.dataset.uid),order);assert.match(view.element("tile-ven-0020").textContent,/kočka/);
});
test("next follows the gallery across group boundaries and return anchors the LAST studied tile",async()=>{
  const view=await app();view.state.topics=["topic-06"];view.selectionChanged();const sequence=view.orderedSelection();const clicked=view.element(`tile-${sequence[2].uid}`);clicked.click();view.element("nextButton").click();view.element("nextButton").click();const last=view.state.currentItem.uid;assert.equal(last,sequence[4].uid);assert.notEqual(last,sequence[2].uid);
  view.element("backButton").click();assert.equal(view.state.view,"gallery");assert.equal(view.doc.activeElement.id,`tile-${last}`);assert.equal(view.element(`tile-${last}`).classList.contains("is-last"),true);assert.deepEqual([...view.state.topics],["topic-06"]);assert.equal(view.historyEntries.length,2);
});
test("browser back and forward restore the same card without a history entry per next",async()=>{
  const view=await app();const sequence=view.orderedSelection();view.openStudy(sequence[5].uid);for(let i=0;i<20;i++)view.moveStudy(1);const last=view.state.currentItem.uid;assert.equal(view.historyEntries.length,2);view.win.history.back();assert.equal(view.state.view,"gallery");view.win.history.forward();assert.equal(view.state.view,"study");assert.equal(view.state.currentItem.uid,last);
});
test("reload retains frozen order, filters, language and the last card",async()=>{
  const before=await app();before.state.sources=["benji"];before.state.sort="cz";before.state.labelLanguage="cz";before.selectionChanged();before.openStudy("","random");before.moveStudy(1);const uid=before.state.currentItem.uid,order=Array.from(before.state.sequence,i=>i.uid);
  const after=await app({url:before.win.location.href,session:before.session,local:before.local});assert.equal(after.state.currentItem.uid,uid);assert.deepEqual(Array.from(after.state.sequence,i=>i.uid),order);assert.equal(after.state.labelLanguage,"cz");assert.deepEqual([...after.state.sources],["benji"]);
});
test("direct card links return to an in-app gallery, even with blocked storage",async()=>{
  const view=await app({url:"https://example.test/PythonMF/vocabulary-en/#card=ven-0020",blocked:true});assert.equal(view.state.currentItem.en,"cat");view.returnToGallery();assert.equal(view.state.view,"gallery");assert.equal(view.historyEntries.length,1);assert.equal(view.doc.activeElement.id,"tile-ven-0020");
});
test("invalid links, invalid saved JSON, and updated data cannot select a different meaning by position",async()=>{
  const session=storage(new Map([["vocabulary-en.navigation.v1","{invalid"]]));const view=await app({url:"https://example.test/PythonMF/vocabulary-en/#card=ven-removed",session});assert.equal(view.state.view,"gallery");assert.match(view.element("galleryNotice").textContent,/už/);
  const reversed=[...vocabulary.items].reverse();const orange=await app({items:reversed,url:"https://example.test/PythonMF/vocabulary-en/#card=ven-0170"});assert.equal(orange.state.currentItem.cz,"oranžový");
});
test("study navigation stops audio, resets revealed answer, and preserves focus semantics",async()=>{
  const view=await app();view.openStudy("ven-0020");view.element("revealButton").click();assert.equal(view.state.revealed,true);view.speakPrompt();assert.ok(view.players.some(p=>p.played));view.moveStudy(1);assert.equal(view.state.revealed,false);assert.ok(view.players.filter(p=>p.played).every(p=>p.paused));view.doc.emit("keydown",{key:"Escape"});assert.equal(view.state.view,"gallery");
});
test("audio identity must match BOTH texts; missing audio does not block the gallery",async()=>{
  const cat=vocabulary.items.find(i=>i.en==="cat");const wrong={items:{[cat.id]:{sourceEn:"cat",sourceCz:"špatně",en:"wrong.mp3"}}};assert.equal(model.audioRecord(cat,wrong),null);const view=await app({manifest:null});assert.equal(view.element("galleryGroups").querySelectorAll(".vocab-tile").length,512);view.openStudy(cat.uid);view.speakPrompt();assert.match(view.element("messageStrip").textContent,/neni pripraveny/);
});
test("revealing and changing a card keeps both sentences attached to the studied meaning",async()=>{
  const view=await app();view.openStudy("ven-0118");
  assert.equal(view.element("answerCard").classList.contains("hidden"),true);
  view.element("revealButton").click();
  assert.equal(view.element("answerCard").classList.contains("hidden"),false);
  for(const uid of ["ven-0118","ven-0170"]){
    view.openStudy(uid);view.element("revealButton").click();
    const item=vocabulary.items.find(item=>item.uid===uid);
    assert.equal(view.element("sentenceBox").hidden,false);
    assert.equal(view.element("sentenceEn").textContent,item.sentenceEn);
    assert.equal(view.element("sentenceCz").textContent,item.sentenceCz);
    view.directions[1].click();
    assert.equal(view.element("sentenceEn").textContent,item.sentenceEn);
  }
  view.moveStudy(1);
  assert.equal(view.element("answerCard").classList.contains("hidden"),true);
  assert.equal(view.element("sentenceEn").textContent,view.state.currentItem.sentenceEn);
});
test("ordinal numbers and related meanings stay distinct; natural cardinal order precedes other quantities",()=>{
  const numbers=model.ordered(vocabulary.items,{topics:["topic-11"],sort:"recommended"},vocabulary.catalog);assert.deepEqual(numbers.slice(0,12).map(i=>i.en),["one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve"]);assert.deepEqual(numbers.filter(i=>i.en==="second").map(model.key),["ven-0440"]);assert.ok(!numbers.some(i=>i.uid==="ven-0385"));assert.equal(new Set(vocabulary.items.map(model.key)).size,522);
});
test("a broken vocabulary request has an explicit error and does not claim an empty loaded dictionary",async()=>{
  const view=await app({failData:true});assert.equal(view.element("totalCount").textContent,"—");assert.match(view.element("galleryNotice").textContent,/nepodařilo/);assert.equal(view.element("shuffleButton").disabled,true);
});

test("a pending audio request never delays the gallery or prevents a bottom-bar return",async()=>{
  const view=await app({slowAudio:true});assert.equal(view.element("galleryGroups").querySelectorAll(".vocab-tile").length,512);view.openStudy("ven-0020");assert.equal(view.element("backBottomButton").hidden,false);view.element("backBottomButton").click();assert.equal(view.state.view,"gallery");assert.equal(view.doc.activeElement.id,"tile-ven-0020");
});
test("reloading the gallery preserves the frozen random order for browser Forward",async()=>{
  const before=await app();before.state.sources=["benji"];before.selectionChanged();before.openStudy("","random");before.moveStudy(1);
  const uid=before.state.currentItem.uid,order=Array.from(before.state.sequence,i=>i.uid),studyUrl=before.win.location.href;
  before.returnToGallery();
  const after=await app({url:before.win.location.href,session:before.session,local:before.local});
  after.win.history.pushState({vocabularyEN:1,kind:"study",fromGallery:true},"",studyUrl);after.applyRoute();
  assert.equal(after.state.currentItem.uid,uid);assert.deepEqual(Array.from(after.state.sequence,i=>i.uid),order);assert.deepEqual([...after.state.sources],["benji"]);assert.equal(after.state.mode,"random");
});

test("sentence prompts use complete paired texts in the selected direction",()=>{
  const cat=vocabulary.items.find(item=>item.uid==="ven-0020");
  assert.equal(model.studyPrompt(cat,{practice:"sentences",direction:"czToEn"}).text,cat.sentenceCz);
  assert.equal(model.studyPrompt(cat,{practice:"sentences",direction:"enToCz"}).text,cat.sentenceEn);
  assert.equal(model.studyPrompt(cat,{practice:"words",direction:"czToEn"}).text,cat.cz);
  assert.equal(model.studyPrompt({...cat,sentenceEn:" "},{practice:"sentences"}).available,false);
});
test("switching practice keeps the card and order, stops audio, and hides the previous answer",async()=>{
  const view=await app();view.openStudy("ven-0020");const order=Array.from(view.state.sequence,model.key),cat=view.state.currentItem;
  assert.equal(view.state.practice,"words");view.element("revealButton").click();view.speakPrompt();
  view.practices[1].click();
  assert.equal(view.state.practice,"sentences");assert.equal(view.state.currentItem.uid,cat.uid);assert.deepEqual(Array.from(view.state.sequence,model.key),order);
  assert.equal(view.element("promptText").textContent,cat.sentenceCz);assert.equal(view.element("promptText").lang,"cs");
  assert.equal(view.element("answerCard").classList.contains("hidden"),true);assert.equal(view.state.revealed,false);
  assert.ok(view.players.filter(player=>player.played).every(player=>player.paused));
  assert.equal(view.practices[1].getAttribute("aria-pressed"),"true");assert.equal(view.practices[0].getAttribute("aria-pressed"),"false");
  view.directions[1].click();assert.equal(view.element("promptText").textContent,cat.sentenceEn);assert.equal(view.element("promptText").lang,"en");
  assert.match(view.element("promptLabel").textContent,/větu česky/);
  view.element("revealButton").click();assert.equal(view.element("answerCard").classList.contains("hidden"),false);
  assert.equal(view.element("sentenceCz").textContent,cat.sentenceCz);
  view.practices[0].click();assert.equal(view.element("promptText").textContent,cat.en);assert.equal(view.element("speakAnswerButton").hidden,false);
  assert.equal(view.element("speakPromptButton").textContent,"♪ Přehrát zadání");
});
test("sentence practice plays the complete prompt and only the revealed target translation in both directions",async()=>{
  const view=await app();view.openStudy("ven-0020");view.practices[1].click();
  assert.match(view.element("speakPromptButton").textContent,/Přehrát větu/);
  view.speakAnswer();assert.ok(view.players.every(player=>!player.played));
  view.speakPrompt();assert.ok(view.players.some(player=>player.played && player.url.endsWith(sentenceAudio.items['ven-0020'].cz)));
  view.element("revealButton").click();view.speakAnswer();assert.ok(view.players.some(player=>player.played && player.url.endsWith(sentenceAudio.items['ven-0020'].en)));
  view.directions[1].click();
  const en=view.players.find(p=>p.url.endsWith(sentenceAudio.items['ven-0020'].en)),cz=view.players.find(p=>p.url.endsWith(sentenceAudio.items['ven-0020'].cz));
  const enBefore=en.playCount,czBefore=cz.playCount;
  view.speakPrompt();assert.equal(en.playCount,enBefore+1);assert.equal(cz.playCount,czBefore);
  view.speakAnswer();assert.equal(cz.playCount,czBefore+1);assert.equal(en.playCount,enBefore+1);
  assert.ok(view.players.filter(player=>player.played).every(player=>player.url.includes('/sentence-')));
});

test("stale or absent sentence audio never plays another sentence or falls back to word audio",async()=>{
  const cat=vocabulary.items.find(i=>i.uid==='ven-0020');
  for(const field of ['uid','sourceEn','sourceCz','sourceSentenceEn','sourceSentenceCz']){
    const wrong={kind:'sentences',items:{[cat.uid]:{...sentenceAudio.items[cat.uid],[field]:'wrong'}}};
    assert.equal(model.sentenceAudioRecord(cat,wrong),null);
    const view=await app({sentenceManifest:wrong});view.openStudy(cat.uid);view.practices[1].click();view.speakPrompt();
    assert.ok(view.players.every(p=>!p.played));assert.match(view.element('messageStrip').textContent,/větu zatím není/);
  }
  const view=await app({sentenceManifest:null});view.openStudy(cat.uid);view.practices[1].click();view.speakPrompt();
  assert.ok(view.players.every(p=>!p.played));view.practices[0].click();view.speakPrompt();assert.ok(view.players.some(p=>p.played));
});

test("leaving or changing sentence practice cancels the playing sentence and resets the revealed answer",async()=>{
  const view=await app();view.openStudy('ven-0020');view.practices[1].click();view.speakPrompt();
  view.element('revealButton').click();view.moveStudy(1);assert.equal(view.state.revealed,false);
  assert.ok(view.players.filter(p=>p.played).every(p=>p.paused));view.speakAnswer();
  view.speakPrompt();view.returnToGallery();assert.ok(view.players.filter(p=>p.played).every(p=>p.paused));
});
test("sentence practice survives next, previous, gallery return and continuation at the last tile",async()=>{
  const view=await app();view.state.topics=["topic-06"];view.selectionChanged();const order=view.orderedSelection();view.openStudy(order[2].uid);view.practices[1].click();
  view.element("revealButton").click();view.moveStudy(1);const last=view.state.currentItem;
  assert.equal(last.uid,order[3].uid);assert.equal(view.state.practice,"sentences");assert.equal(view.element("promptText").textContent,last.sentenceCz);assert.equal(view.state.revealed,false);
  view.moveStudy(-1);assert.equal(view.state.currentItem.uid,order[2].uid);view.moveStudy(1);view.returnToGallery();
  assert.equal(view.doc.activeElement.id,`tile-${last.uid}`);assert.equal(view.state.view,"gallery");assert.equal(view.state.practice,"sentences");
  view.element("continueButton").click();assert.equal(view.state.currentItem.uid,last.uid);assert.equal(view.element("promptText").textContent,last.sentenceCz);
});
test("sentence practice restores from reload and browser Forward without changing a random sequence",async()=>{
  const before=await app();before.openStudy("","random");before.practices[1].click();before.directions[1].click();before.moveStudy(1);
  const uid=before.state.currentItem.uid,order=Array.from(before.state.sequence,model.key);
  const after=await app({url:before.win.location.href,session:before.session,local:before.local});
  assert.equal(after.state.practice,"sentences");assert.equal(after.state.currentItem.uid,uid);assert.deepEqual(Array.from(after.state.sequence,model.key),order);
  assert.equal(after.element("promptText").textContent,after.state.currentItem.sentenceEn);
  after.win.history.back(); // A reload has no earlier entry; explicit return still preserves the mode.
  after.returnToGallery();assert.equal(after.state.view,"gallery");
  const studyUrl=before.win.location.href;after.win.history.pushState({vocabularyEN:1,kind:"study",fromGallery:true},"",studyUrl);after.applyRoute();
  assert.equal(after.state.practice,"sentences");assert.equal(after.state.currentItem.uid,uid);assert.deepEqual(Array.from(after.state.sequence,model.key),order);
});
test("missing sentence pairs are explicit and never reveal a fabricated or stale answer",async()=>{
  const cat=vocabulary.items.find(item=>item.uid==="ven-0020"),missing={...cat,sentenceEn:"",sentenceCz:""};
  const view=await app({items:[missing]});view.openStudy(cat.uid);view.practices[1].click();
  assert.equal(view.element("revealButton").disabled,true);assert.match(view.element("messageStrip").textContent,/chybí/);
  view.element("revealButton").click();assert.equal(view.state.revealed,false);assert.equal(view.element("answerCard").classList.contains("hidden"),true);
  view.practices[0].click();assert.equal(view.element("promptText").textContent,cat.cz);assert.equal(view.element("revealButton").disabled,false);
});
test("old or invalid practice state stays compatible and sentence links work with blocked storage",async()=>{
  const invalid=await app({url:"https://example.test/PythonMF/vocabulary-en/#card=ven-0020&practice=invalid"});assert.equal(invalid.state.practice,"words");
  const old=await app({url:"https://example.test/PythonMF/vocabulary-en/#card=ven-0020"});assert.equal(old.state.practice,"words");
  const linked=await app({url:"https://example.test/PythonMF/vocabulary-en/#card=ven-0020&practice=sentences",blocked:true});
  assert.equal(linked.state.practice,"sentences");assert.equal(linked.element("promptText").textContent,linked.state.currentItem.sentenceCz);
  linked.returnToGallery();assert.equal(linked.doc.activeElement.id,"tile-ven-0020");
});

// A homograph is a set of distinct meanings, never an identity based on spelling.
test("same English spellings preserve independent meanings, audio records, POS and navigation",async()=>{
  const ids=["ven-0385","ven-0440"],items=ids.map(uid=>vocabulary.items.find(i=>i.uid===uid));
  assert.deepEqual(items.map(i=>i.cz),["sekunda","druhý"]);
  assert.deepEqual(model.select(items,{parts:["noun"]}).map(model.key),[ids[0]]);
  assert.deepEqual(model.select(items,{parts:["number"]}).map(model.key),[ids[1]]);
  const records=items.map(i=>model.audioRecord(i,audio));assert.ok(records.every(Boolean));
  assert.equal(records[0].en,records[1].en);assert.notEqual(records[0].cz,records[1].cz);
  const view=await app({items}),order=Array.from(view.orderedSelection(),model.key);view.openStudy(order[0]);view.moveStudy(1);
  assert.equal(view.state.currentItem.uid,order[1]);view.openStudy(ids[1]);assert.equal(view.state.currentItem.sentenceEn,"The rabbit in blue is second.");
  view.returnToGallery();assert.equal(view.doc.activeElement.id,"tile-"+ids[1]);
});
test("a stored personal selection of the original meaning never silently acquires its new siblings",async()=>{
  const local=storage(),value=learners.empty();value.profiles.A.selected=["ven-0385"];value.profiles.A.hard=["ven-0385"];
  local.setItem(learners.KEY,JSON.stringify(value));const before=local.getItem(learners.KEY),view=await app({local});
  chooseUser(view,"A");assert.deepEqual(Array.from(view.orderedSelection(),model.key),["ven-0385"]);
  assert.equal(local.getItem(learners.KEY),before);view.element("settingsTab").click();await unlock(view);
  chooseWord(view,"ven-0440");view.element("saveLearner").click();
  const saved=JSON.parse(local.getItem(learners.KEY));assert.deepEqual(saved.profiles.A.selected,["ven-0385","ven-0440"]);
  assert.deepEqual(saved.profiles.A.hard,["ven-0385"]);
});

test("body batch stays within the original theme and navigates distinct new nouns",async()=>{
  const view=await app();view.state.topics=["topic-02"];view.selectionChanged();
  assert.equal(view.orderedSelection().length,16);assert.equal(view.state.data.catalog.groups.length,18);
  view.openStudy("ven-0443");assert.equal(view.state.currentItem.en,"head");view.moveStudy(1);
  assert.equal(view.state.currentItem.uid,"ven-0444");assert.equal(view.state.currentItem.sentenceEn,"I wash my face.");
  view.returnToGallery();assert.equal(view.doc.activeElement.id,"tile-ven-0444");
});
