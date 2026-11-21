const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');const vm=require('node:vm');const test=require('node:test');
const root=path.resolve(__dirname,'../../docs');
const model=require(path.join(root,'vocabulary-it/model.js'));
const learners=require(path.join(root,'vocabulary-it/learners.js'));
const vocabulary=JSON.parse(fs.readFileSync(path.join(root,'data/vocabulary-it-v2.json'),'utf8'));
const html=fs.readFileSync(path.join(root,'vocabulary-it/index.html'),'utf8');
const source=fs.readFileSync(path.join(root,'vocabulary-it/gallery.js'),'utf8');
const audio={language:'it',kind:'words',items:Object.fromEntries(vocabulary.items.map(i=>[i.uid,{uid:i.uid,sourceIt:i.it,sourceCz:i.cz,it:`assets/vocabulary-it-audio/fixture/${i.uid}-it.mp3`,cz:`assets/vocabulary-it-audio/fixture/${i.uid}-cz.mp3`}]))};
const sentenceAudio={language:'it',kind:'sentences',items:Object.fromEntries(vocabulary.items.map(i=>[i.uid,{uid:i.uid,sourceIt:i.it,sourceCz:i.cz,sourceSentenceIt:i.sentenceIt,sourceSentenceCz:i.sentenceCz,it:`assets/vocabulary-it-sentences/fixture/${i.uid}-it.mp3`,cz:`assets/vocabulary-it-sentences/fixture/${i.uid}-cz.mp3`}]))};
const quizCatalog=JSON.parse(fs.readFileSync(path.join(root,"data/vocabulary-it-quiz.json"),"utf8"));
const pictures=JSON.parse(fs.readFileSync(path.join(root,'data/vocabulary-it-sentence-pictures.json'),'utf8'));
const practice=require(path.join(root,"vocabulary-it/practice.js"));
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
  showModal(){this.open=true;}close(){this.open=false;}
  descendants(){return this.children.flatMap(child=>[child,...child.descendants()]);}
  matches(selector){if(selector.startsWith("."))return this.classList.contains(selector.slice(1));if(selector.startsWith("[data-"))return selector.slice(6,-1).replace(/-([a-z])/g,(_,c)=>c.toUpperCase()) in this.dataset;return this.tagName===selector;}
  querySelectorAll(selector){return this.descendants().filter(node=>node.matches(selector));}querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
  getBoundingClientRect(){return {top:160,width:140,height:180};} focus(){this.doc.activeElement=this;}scrollIntoView(){this.doc.scrolled=this.id;}
}
function storage(map=new Map()){return {map,getItem:key=>map.get(key)||null,setItem:(key,value)=>map.set(key,String(value))};}
async function app({items=vocabulary.items,url="https://example.test/PythonMF/vocabulary-it/",session=storage(),local=storage(),blocked=false,manifest=audio,sentenceManifest=sentenceAudio,failData=false,slowAudio=false,audioReject=false,reducedMotion=false,failQuiz=false,delayedSeek=false,dataOverride={},pictureManifest=pictures,pictureDeferred=null}={}){
  const doc=new Element("document");doc.doc=doc;doc.title="Vocabulary";
  doc.getElementById=id=>doc.descendants().find(node=>node.id===id)||null;
  doc.createElement=tag=>new Element(tag,doc);doc.createDocumentFragment=()=>new Element("fragment",doc);
  const appRoot=new Element("main",doc);appRoot.dataset={jsonUrl:"../data/vocabulary-it-v2.json",audioUrl:"../data/vocabulary-it-audio.json"};doc.append(appRoot);doc.body=appRoot;
  for(const [,id] of html.matchAll(/\bid="([^"]+)"/g)){const node=new Element("div",doc);node.id=id;appRoot.append(node);}
  for(const [data,values] of [["direction",["czToIt","itToCz"]],["label",["it","cz"]],["practice",["words","sentences"]],["galleryMode",["learn","listen"]]])for(const value of values){const button=new Element("button",doc);button.dataset[data]=value;appRoot.append(button);}
  const listeners={};let scroll=0;const location={href:url};const historyEntries=[{url,state:null}];let historyIndex=0;
  const win={location,innerHeight:844,addEventListener:(name,fn)=>(listeners[name]??=[]).push(fn),scrollTo:value=>{scroll=value.top||0;},get scrollY(){return scroll;},requestAnimationFrame:fn=>fn()};
  let now=0,nextTimer=0;const timers=new Map();
  win.setTimeout=(callback,delay)=>{const id=++nextTimer;timers.set(id,{callback,at:now+delay});return id;};
  win.clearTimeout=id=>timers.delete(id);
  win.matchMedia=()=>({matches:reducedMotion});
  win.crypto=require('node:crypto').webcrypto;win.Blob=Blob;win.URL=URL;win.confirm=()=>true;
  const advance=ms=>{now+=ms;for(const [id,timer] of [...timers])if(timer.at<=now){timers.delete(id);timer.callback();}};
  const emit=(name,extra={})=>{for(const fn of listeners[name]||[])fn(extra);};
  const travel=delta=>{if(!historyEntries[historyIndex+delta])return;historyIndex+=delta;location.href=historyEntries[historyIndex].url;emit("popstate");emit("hashchange");};
  win.history={get state(){return historyEntries[historyIndex].state;},replaceState:(state,unused,url)=>{location.href=new URL(url,location.href).href;historyEntries[historyIndex]={url:location.href,state};},pushState:(state,unused,url)=>{location.href=new URL(url,location.href).href;historyEntries.splice(historyIndex+1);historyEntries.push({url:location.href,state});historyIndex++;},back:()=>travel(-1),forward:()=>travel(1)};
  if(blocked){Object.defineProperty(win,"sessionStorage",{get(){throw Error("blocked")}});Object.defineProperty(win,"localStorage",{get(){throw Error("blocked")}});}else{win.sessionStorage=session;win.localStorage=local;}
  let rejectPlayback=audioReject;const players=[];class AudioFixture {
    constructor(url){this.url=url;this.handlers={};this.position=0;this.playCount=0;this.starts=[];this.paused=true;this.ended=false;this.loadCount=0;players.push(this);}
    set src(value){this.url=value;}get src(){return this.url;}
    load(){this.position=0;this.ended=false;this.seekPending=false;this.loadCount++;}
    get currentTime(){return this.position;}set currentTime(value){if(delayedSeek&&value===0&&this.position>0)this.seekPending=true;else this.position=value;}
    addEventListener(name,fn){this.handlers[name]=fn;}removeEventListener(name,fn){if(this.handlers[name]===fn)delete this.handlers[name];}
    pause(){this.paused=true;}play(){this.played=true;this.paused=false;this.ended=false;this.playCount++;this.starts.push(this.position);return rejectPlayback?Promise.reject(Error("blocked")):Promise.resolve();}
  }
  const data={...vocabulary,items,...dataOverride};
  const ctx=vm.createContext({document:doc,window:win,URL,URLSearchParams,TextEncoder,Audio:AudioFixture,console,fetch:async url=>{if(url.includes("sentence-pictures.json")){if(pictureManifest===null)throw Error("optional unavailable");return {ok:true,json:async()=>pictureDeferred?await pictureDeferred:pictureManifest};}if(url.includes("-quiz.json")){if(failQuiz)throw Error("quiz unavailable");return {ok:true,json:async()=>quizCatalog};}if(slowAudio && url.includes("audio"))return new Promise(()=>{});if(failData && !url.includes("audio"))throw Error("offline");const selected=url.includes("sentence-audio")?sentenceManifest:manifest;if(selected===null && url.includes("audio"))throw Error("audio unavailable");return {ok:true,json:async()=>url.includes("audio")?selected:data};}});
  vm.runInContext(fs.readFileSync(path.join(root,"vocabulary-it/model.js"),"utf8"),ctx);
  for(const name of ['learners.js','learner-ui.js','practice.js','memory.js'])vm.runInContext(fs.readFileSync(path.join(root,'vocabulary-it',name),'utf8'),ctx);
  vm.runInContext(source.replace('void init();','globalThis.ready=init();')+'\nglobalThis.api={state,context,buildSelection,orderedSelection,openStudy,moveStudy,newRandomRound,returnToGallery,renderGallery,selectionChanged,applyRoute,speakPrompt,speakAnswer,stopAudioPlayback,setPracticeMode};',ctx);
  await ctx.ready;
  return {...ctx.api,doc,win,emit,advance,players,setAudioReject:value=>{rejectPlayback=value;},session,local,historyEntries,element:id=>doc.getElementById(id),directions:doc.querySelectorAll("[data-direction]"),labels:doc.querySelectorAll("[data-label]"),practices:doc.querySelectorAll("[data-practice]"),galleryModes:doc.querySelectorAll("[data-gallery-mode]")};
}
const catalog={groups:vocabulary.groups,parents:vocabulary.parents};
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(check){for(let i=0;i<300;i++){if(check())return;await sleep(10);}throw Error('Timed out');}
function change(view,id,value){const node=view.element(id);if(typeof value==='boolean')node.checked=value;else node.value=value;node.emit('change');}

test('1116 Italian meanings and18 topics; new20 intersect filters without source order mutation',()=>{
 assert.equal(vocabulary.items.length,1116);assert.equal(vocabulary.groups.length,18);
 assert.equal(vocabulary.imageReviewComplete,true);assert.ok(vocabulary.items.every(i=>i.imageReviewed));
 const before=JSON.stringify(vocabulary);
 const latest=model.select(vocabulary.items,{recentCount:20});
 assert.equal(latest.length,20);assert.ok(latest.every(i=>i.id>=1097));
 assert.equal(model.select(vocabulary.items,{query:'eclair'})[0].it,'éclair');
 assert.equal(model.select(vocabulary.items,{query:'němčina'})[0].uid,'vit-0473');
 assert.equal(model.select(vocabulary.items,{topics:['topic-09'],recentCount:20}).every(i=>i.topicIds.includes('topic-09')),true);
 const ordered=model.ordered(vocabulary.items,{groupBy:'topic'},catalog);
 assert.equal(new Set(ordered.map(i=>i.uid)).size,1116);
 assert.equal(JSON.stringify(vocabulary),before);
});
test('Italian and Czech prompts preserve complete sentences and correct lang',()=>{
 const i=vocabulary.items.find(i=>i.uid==='vit-0108');
 assert.equal(model.studyPrompt(i,{direction:'itToCz'}).text,'éclair');
 assert.equal(model.studyPrompt(i,{direction:'itToCz',practice:'sentences'}).language,'it');
 assert.equal(model.studyPrompt(i,{direction:'itToCz',practice:'sentences'}).text,'Dopo il pasto prendo un éclair al cioccolato.');
 assert.equal(model.studyPrompt(i,{direction:'czToIt',practice:'sentences'}).text,i.sentenceCz);
 assert.equal(model.studyPrompt({...i,sentenceIt:''},{practice:'sentences'}).available,false);
});
test('audio must match Italian UID, language, texts and own asset namespace',()=>{
 const i=vocabulary.items[0],valid=audio.items[i.uid];
 assert.ok(model.audioRecord(i,audio));assert.ok(model.sentenceAudioRecord(i,sentenceAudio));
 for(const change of [{uid:'vit-9999'},{sourceIt:'wrong'},{sourceCz:'wrong'},{it:'assets/vocabulary-en-audio/voice/x.mp3'},{it:'https://outside.test/x.mp3'},{cz:'assets/vocabulary-it-audio/../x.mp3'}]){
  assert.equal(model.audioRecord(i,{...audio,items:{[i.uid]:{...valid,...change}}}),null);
 }
 assert.equal(model.audioRecord(i,{...audio,language:'en'}),null);
 assert.equal(model.sentenceAudioRecord(i,{...sentenceAudio,items:{[i.uid]:{...sentenceAudio.items[i.uid],sourceSentenceIt:'changed'}}}),null);
 assert.equal(model.audioRecord(i,{language:'it',kind:'words',items:{}}),null);
});
test('actual gallery opens, shows1116 thumbnails, ordered next and returns to the current tile',async()=>{
 const view=await app();assert.equal(view.state.view,'gallery');assert.equal(view.buildSelection().length,1116);
 assert.equal(view.element('galleryGroups').querySelectorAll('.vocab-tile').length,1116);
 assert.equal(view.element('galleryGroups').querySelectorAll('img').every(i=>i.width===240),true);
 const target=view.orderedSelection()[3];view.openStudy(target.uid);
 assert.equal(view.state.currentItem.uid,target.uid);assert.equal(view.state.mode,'ordered');
 view.moveStudy(1);const last=view.state.currentItem.uid;view.returnToGallery();
 assert.equal(view.state.view,'gallery');assert.equal(view.state.lastUid,last);
 assert.equal(view.doc.activeElement.id,'tile-'+last);assert.ok(view.win.scrollY>0);
 assert.ok(view.doc.getElementById('tile-'+last).classList.contains('is-last'));
});
test('last20, language switch, sentence mode, refresh and back/forward keep selection',async()=>{
 const view=await app();change(view,'recentOnly',true);assert.equal(view.buildSelection().length,20);
 const target=view.orderedSelection()[2];view.openStudy(target.uid);view.setPracticeMode('sentences');
 view.directions.find(b=>b.dataset.direction==='itToCz').click();view.element('revealButton').click();
 assert.equal(view.element('promptText').textContent,target.sentenceIt);assert.equal(view.element('promptText').lang,'it');
 assert.equal(view.state.recentCount,20);
 const refreshed=await app({url:view.win.location.href,session:view.session,local:view.local});
 assert.equal(refreshed.state.currentItem.uid,target.uid);assert.equal(refreshed.state.practice,'sentences');
 assert.equal(refreshed.state.direction,'itToCz');assert.equal(refreshed.state.recentCount,20);
 view.returnToGallery();assert.equal(view.state.view,'gallery');view.win.history.forward();assert.equal(view.state.view,'study');
});
test('random ordering is explicit; missing and foreign deep links return to gallery',async()=>{
 const view=await app();view.openStudy('','random');assert.equal(view.state.mode,'random');
 const bad=await app({url:'https://example.test/vocabulary-it/#card=ven-0001'});assert.equal(bad.state.view,'gallery');
 assert.match(bad.element('galleryNotice').textContent,/není/);
 const foreign=await app({dataOverride:{language:'en'}});assert.equal(foreign.state.data,null);assert.match(foreign.element('galleryNotice').textContent,/nepodařilo načíst/);
});
test('gender is shown for nouns, not old noun metadata on reactions',async()=>{
 const view=await app();view.openStudy('vit-0001');assert.equal(view.element('wordGender').hidden,false);
 assert.match(view.element('wordGender').textContent,/rod/);view.returnToGallery();view.openStudy('vit-0461');assert.equal(view.element('wordGender').hidden,true);
});
test('missing audio never blocks gallery, never constructs a player, and keeps listening recent filter',async()=>{
 const view=await app({manifest:{language:'it',kind:'words',status:'not-generated',items:{}},sentenceManifest:null});
 assert.equal(view.buildSelection().length,1116);change(view,'recentOnly',true);
 view.galleryModes.find(b=>b.dataset.galleryMode==='listen').click();
 const tile=view.element('galleryGroups').querySelectorAll('.vocab-tile')[0];const caption=tile.querySelector('.tile-label').textContent;
 tile.click();await sleep(0);assert.equal(view.state.view,'gallery');assert.equal(view.players.length,0);
 assert.match(view.doc.getElementById('galleryModeHint').textContent,/není připravený/);
 assert.equal(tile.querySelector('.tile-label').textContent,caption);
 view.galleryModes.find(b=>b.dataset.galleryMode==='learn').click();tile.click();view.speakPrompt();
 assert.match(view.element('messageStrip').textContent,/neni pripraveny|není připravený/);assert.equal(view.players.length,0);
});
test('Italian listening flashes Czech for1s and restores after rapid click/mode change',async()=>{
 const view=await app();view.galleryModes.find(b=>b.dataset.galleryMode==='listen').click();
 const tiles=view.element('galleryGroups').querySelectorAll('.vocab-tile').slice(0,2);
 const words=tiles.map(tile=>tile.querySelector('.tile-label').textContent);
 tiles[0].click();await sleep(0);assert.equal(tiles[0].querySelector('.tile-label').lang,'cs');
 tiles[1].click();await sleep(0);assert.equal(tiles[0].querySelector('.tile-label').textContent,words[0]);
 view.advance(1000);assert.equal(tiles[1].querySelector('.tile-label').textContent,words[1]);
 tiles[0].click();view.galleryModes.find(b=>b.dataset.galleryMode==='learn').click();assert.equal(tiles[0].querySelector('.tile-label').textContent,words[0]);
});
test('complete real libraries resolve all1116 meanings and drive both word and sentence players',async()=>{
 const words=JSON.parse(fs.readFileSync(path.join(root,'data/vocabulary-it-audio.json'),'utf8'));
 const sentences=JSON.parse(fs.readFileSync(path.join(root,'data/vocabulary-it-sentence-audio.json'),'utf8'));
 assert.equal(words.status,'complete');assert.equal(sentences.status,'complete');
 for(const item of vocabulary.items){assert.ok(model.audioRecord(item,words));assert.ok(model.sentenceAudioRecord(item,sentences));}
 const view=await app({manifest:words,sentenceManifest:sentences});
 view.galleryModes.find(b=>b.dataset.galleryMode==='listen').click();
 const tile=view.element('galleryGroups').querySelectorAll('.vocab-tile')[0];tile.click();await sleep(0);
 assert.equal(view.players.find(p=>p.played).url,new URL('../'+words.items[tile.dataset.uid].it,view.win.location.href).href);
 view.galleryModes.find(b=>b.dataset.galleryMode==='learn').click();view.openStudy('vit-0108');
 view.setPracticeMode('sentences');view.directions.find(b=>b.dataset.direction==='itToCz').click();
 view.speakPrompt();await sleep(0);assert.ok(view.players.some(p=>p.played && p.url===new URL('../'+sentences.items['vit-0108'].it,view.win.location.href).href));
 view.element('revealButton').click();view.speakAnswer();await sleep(0);
 assert.ok(view.players.some(p=>p.played && p.url===new URL('../'+sentences.items['vit-0108'].cz,view.win.location.href).href));
});
test('blocked storage leaves common Italian gallery usable and settings honest',async()=>{
 const view=await app({blocked:true});assert.equal(view.buildSelection().length,1116);
 assert.equal(view.element('learnerSelect').disabled,true);assert.match(view.element('learnerNotice').textContent,/nelze načíst/);
});
test('IT profiles begin empty; EN backup and IDs are rejected; EN storage is untouched',()=>{
 const map=new Map([['vocabulary-en.learners.v1','EN PRIVATE DATA']]);const s=storage(map);const repo=learners.store(()=>s);const initial=repo.read();
 assert.ok(learners.IDS.every(id=>initial.value.profiles[id].selected.length===0));
 assert.equal(learners.KEY,'vocabulary-it.learners.v1');
 const next=initial.value;next.profiles.A.selected=['vit-0001'];next.profiles.A.hard=['vit-0001'];repo.write(next,initial.raw);
 assert.equal(map.get('vocabulary-en.learners.v1'),'EN PRIVATE DATA');
 const backup=learners.backup(next);assert.equal(backup.kind,'vocabulary-it.learner-backup');assert.equal('pin' in backup.profiles.A,false);
 assert.throws(()=>learners.parseBackup(JSON.stringify({...backup,kind:'vocabulary-en.learner-backup'})));
 const invalid=structuredClone(backup);invalid.profiles.A.selected=['ven-0001'];invalid.profiles.A.hard=[];assert.throws(()=>learners.parseBackup(JSON.stringify(invalid)));
});
test('learner storage protects concurrent writes and hard words must be selected',()=>{
 const s=storage();const repo=learners.store(()=>s),first=repo.read();const next=structuredClone(first.value);next.profiles.A.selected=['vit-0001'];
 repo.write(next,first.raw);assert.throws(()=>repo.write(first.value,first.raw),/mezitím/);
 const bad=repo.read().value;bad.profiles.B.hard=['vit-0002'];assert.throws(()=>repo.write(bad,repo.read().raw),/patřit/);
});
test('PIN uses a salted digest and confirms valid/invalid input',async()=>{
 const crypto=require('node:crypto').webcrypto;const a=await learners.makePin('4826',crypto),b=await learners.makePin('4826',crypto);
 assert.notEqual(a.salt,b.salt);assert.notEqual(a.hash,b.hash);assert.equal(await learners.verifyPin('4826',a,crypto),true);assert.equal(await learners.verifyPin('1111',a,crypto),false);
 assert.equal(Object.hasOwn(a,'pin'),false);await assert.rejects(()=>learners.makePin('no',crypto));
});
test('settings save A, hard selection and restoring into another device remain language isolated',async()=>{
 const view=await app();view.element('settingsTab').click();view.element('pinInput').value='4826';view.element('pinRepeat').value='4826';view.element('unlockButton').click();
 await until(()=>!view.element('learnerEditor').hidden);
 const box=view.element('settingsGroups').querySelectorAll('.learner-word-check')[0];box.checked=true;box.emit('change');view.element('saveLearner').click();
 assert.equal(view.state.learner,'A');assert.equal(view.buildSelection().length,1);
 view.element('editLearnerHard').click();view.element('pinInput').value='4826';view.element('unlockButton').click();await until(()=>!view.element('learnerEditor').hidden);
 const hard=view.element('settingsGroups').querySelectorAll('.learner-word-check')[0];hard.checked=true;hard.emit('change');view.element('saveLearner').click();view.element('learnerHardFilter').click();assert.equal(view.buildSelection().length,1);
 const saved=learners.store(()=>view.local).read().value;const backup=learners.parseBackup(JSON.stringify(learners.backup(saved)));
 assert.deepEqual(backup.profiles.A.selected,[box.dataset.uid]);assert.deepEqual(backup.profiles.A.hard,[box.dataset.uid]);assert.equal('pin' in backup.profiles.A,false);
 const other=learners.empty();other.profiles.B.selected=['vit-0002'];other.profiles.A={...other.profiles.A,...backup.profiles.A};assert.deepEqual(other.profiles.B.selected,['vit-0002']);assert.equal(learners.selection(vocabulary.items,other,'A').length,1);
});
test('actual backup import updates only unlocked A and preserves its PIN and B',async()=>{
 const saved=learners.empty();saved.profiles.A.pin=await learners.makePin('4826',require('node:crypto').webcrypto);saved.profiles.A.selected=['vit-0001'];saved.profiles.B.selected=['vit-0002'];
 const local=storage(new Map([[learners.KEY,JSON.stringify(saved)]]));const view=await app({local});view.element('settingsTab').click();view.element('pinInput').value='4826';view.element('unlockButton').click();await until(()=>!view.element('learnerEditor').hidden);
 const imported=learners.backup(learners.empty());imported.profiles.A.selected=['vit-0003','vit-9999'];imported.profiles.A.hard=['vit-0003'];imported.profiles.B.selected=['vit-0004'];const raw=JSON.stringify(imported);
 view.element('learnerFile').files=[{size:raw.length,text:async()=>raw}];view.element('learnerFile').emit('change');await until(()=>view.element('settingsNotice').textContent.includes('Načtený návrh'));view.element('saveLearner').click();
 const after=learners.store(()=>local).read().value;assert.deepEqual(after.profiles.A.selected,['vit-0003','vit-9999']);assert.deepEqual(after.profiles.A.hard,['vit-0003']);assert.deepEqual(after.profiles.A.pin,saved.profiles.A.pin);assert.deepEqual(after.profiles.B,saved.profiles.B);
});

const fourIds=['vit-0001','vit-0093','vit-0106','vit-0320'];
const fourItems=vocabulary.items.filter(i=>fourIds.includes(i.uid));
function choices(view){return view.element('quizChoices').querySelectorAll('.practice-choice');}
function completeImages(view){for(const image of view.element('quizChoices').querySelectorAll('img'))image.emit('load');}
async function animateWord(view){for(let n=0;n<35;n++){view.advance(100);await sleep(0);}}
function endSound(view){const player=[...view.players].reverse().find(p=>p.handlers.ended);assert.ok(player,'a real player must have started');player.position=1.25;player.handlers.ended();}
function correctChoice(view){const word=view.element('practiceWord').textContent;return choices(view).find(b=>vocabulary.items.find(i=>i.uid===b.dataset.uid).it===word);}
async function readyQuestion(view){completeImages(view);await animateWord(view);endSound(view);await sleep(0);}
async function practiceView(options={}){const view=await app({items:fourItems,...options});view.element('quizTab').click();view.element('quizStart').click();return view;}

test('reviewed practice metadata covers1116 cards; all can form a valid four-picture question in the full selection',()=>{
 const pool=practice.eligible(vocabulary.items,audio,quizCatalog);assert.equal(pool.length,1116);
 const latest=practice.eligible(model.select(vocabulary.items,{recentCount:20}),audio,quizCatalog);assert.equal(latest.length,20);assert.ok(latest.every(i=>practice.question(i,latest,quizCatalog,()=>.5)));
 for(const item of pool){const q=practice.question(item,pool,quizCatalog,()=>.5);assert.equal(q.choices.length,4);assert.ok(q.choices.some(i=>i.uid===item.uid));assert.equal(new Set(q.choices.map(i=>i.image)).size,4);for(let a=0;a<4;a++)for(let b=a+1;b<4;b++)assert.ok(practice.compatible(q.choices[a],q.choices[b],quizCatalog));}
 assert.equal(practice.question(pool[0],pool.slice(0,3),quizCatalog),null);
 assert.equal(practice.question({...pool[0],active:false},pool,quizCatalog),null);
});
test('practice refuses changed spellings, source meanings, image bindings and foreign namespaces',()=>{
 const item=vocabulary.items.find(i=>i.uid==='vit-0320'),entry=quizCatalog.entries[item.uid];assert.deepEqual(entry.pieces,['la','var','si']);
 for(const change of [{it:'lavare'},{cz:'jiný význam'},{image:'other.webp'},{thumbnail:'other.webp'},{pieces:['la','var','si!']},{reviewed:false},{displayMode:'unknown'}])assert.equal(practice.record(item,{...quizCatalog,entries:{[item.uid]:{...entry,...change}}}),null);
 assert.equal(practice.record(item,{...quizCatalog,language:'en'}),null);
 assert.equal(practice.compatible(vocabulary.items.find(i=>i.uid==='vit-0353'),vocabulary.items.find(i=>i.uid==='vit-0491'),quizCatalog),false);
 assert.equal(practice.compatible(vocabulary.items.find(i=>i.uid==='vit-0298'),vocabulary.items.find(i=>i.uid==='vit-0403'),quizCatalog),false);
});
test('four tiles wait for images, show syllables, join spelling and enable answers only after Italian audio ends',async()=>{
 const view=await practiceView();assert.equal(view.state.view,'quiz');assert.equal(choices(view).length,4);assert.ok(choices(view).every(b=>b.disabled));assert.ok(view.players.every(p=>!p.played));
 const images=view.element('quizChoices').querySelectorAll('img');for(const image of images.slice(0,3))image.emit('load');await animateWord(view);assert.ok(view.players.every(p=>!p.played));
 images[3].emit('load');assert.ok(view.element('practiceWord').children.some(s=>s.classList.contains('is-pending')));
 await animateWord(view);assert.ok(view.element('practiceWord').classList.contains('is-joined'));assert.ok(choices(view).every(b=>b.disabled));assert.ok(view.players.some(p=>p.played));
 endSound(view);await sleep(0);assert.ok(choices(view).every(b=>!b.disabled));assert.equal(view.element('quizNext').disabled,true);
 assert.ok(!view.element('practiceStrip').hidden);assert.ok(view.element('practiceHero').hidden);
});
test('a wrong picture becomes crossed out, remaining attempts stay active, and correct answer grows one card until Next',async()=>{
 const view=await practiceView();await readyQuestion(view);const correct=correctChoice(view),wrong=choices(view).find(b=>b!==correct);const word=view.element('practiceWord').textContent;
 wrong.click();wrong.click();assert.ok(wrong.disabled);assert.ok(wrong.classList.contains('is-wrong'));assert.equal(wrong.querySelector('.quiz-mark').textContent,'×');assert.ok(!correct.disabled);assert.equal(view.element('practiceWord').textContent,word);assert.equal(view.element('quizChoices').hidden,false);
 correct.click();correct.click();assert.equal(view.element('quizChoices').hidden,true);assert.equal(view.element('practiceStrip').hidden,true);assert.equal(view.element('practiceHero').hidden,false);assert.equal(view.element('practiceHeroWord').textContent,word);assert.ok(view.element('practiceHeroCz').textContent);assert.equal(view.element('quizNext').disabled,true);await endFeedback(view);assert.equal(view.element('quizNext').disabled,false);
 view.advance(10000);await sleep(0);assert.equal(view.element('practiceHero').hidden,false);assert.equal(view.element('practiceHeroWord').textContent,word);assert.match(view.element('quizMessage').textContent,/zopakuješ/);
});
test('one initial error is requeued once after the original words; score counts first tries and remedial drill is available',async()=>{
 const view=await practiceView();let mistaken;
 for(let n=0;n<4;n++){await readyQuestion(view);const right=correctChoice(view);if(n===0){mistaken=right.dataset.uid;choices(view).find(b=>b!==right).click();}right.click();await endFeedback(view);view.element('quizNext').click();}
 assert.match(view.element('quizPosition').textContent,/Opakování/);await readyQuestion(view);assert.equal(correctChoice(view).dataset.uid,mistaken);choices(view).find(b=>b!==correctChoice(view)).click();correctChoice(view).click();await endFeedback(view);view.element('quizNext').click();
 assert.equal(view.element('quizEnd').hidden,false);assert.match(view.element('quizResult').textContent,/Na první pokus 3 z 4\. Opakování 1/);assert.equal(view.element('quizErrors').disabled,false);
 view.element('quizErrors').click();await readyQuestion(view);assert.equal(correctChoice(view).dataset.uid,mistaken);
});
test('game inherits personal A, hard and latest20 filters; it never borrows distractors or writes learner storage',async()=>{
 const local=storage(),repo=learners.store(()=>local),initial=repo.read(),next=initial.value;
 const recent=model.select(vocabulary.items,{recentCount:20});const sample=practice.question(recent[0],recent,quizCatalog,()=>0.41);assert.ok(sample);const ids=sample.choices.map(i=>i.uid);next.profiles.A.selected=[...ids,'vit-0001'];next.profiles.A.hard=ids;repo.write(next,initial.raw);const saved=local.getItem(learners.KEY);
 const view=await app({local});change(view,'learnerSelect','A');view.element('learnerHardFilter').click();change(view,'recentOnly',true);view.element('quizTab').click();
 assert.match(view.element('quizSelection').textContent,/Uživatel A.*obtížná.*Posledních 20/);assert.match(view.element('quizPoolNotice').textContent,/4 slovíčka/);view.element('quizStart').click();assert.ok(choices(view).every(b=>ids.includes(b.dataset.uid)));
 await readyQuestion(view);correctChoice(view).click();view.element('quizBack').click();assert.equal(view.state.view,'gallery');assert.equal(view.state.learner,'A');assert.equal(view.state.onlyLearnerHard,true);assert.equal(view.state.recentCount,20);assert.equal(local.getItem(learners.KEY),saved);
});
test('narrow filters and unavailable data explain the blocker; the common gallery remains usable',async()=>{
 for(const options of [{items:fourItems.slice(0,3)},{items:[]},{failQuiz:true},{manifest:null}]){
  const view=await app(options);view.element('quizTab').click();assert.equal(view.element('quizStart').disabled,true);assert.ok(view.element('quizPoolNotice').textContent);view.element('quizBack').click();assert.equal(view.state.view,'gallery');
 }
});
test('an image error or timeout permits an explicit unscored skip without revealing a wrong answer',async()=>{
 for(const timeout of [false,true]){const view=await practiceView();if(timeout)view.advance(15000);else view.element('quizChoices').querySelector('img').emit('error');assert.equal(view.element('quizNext').disabled,false);assert.match(view.element('quizMessage').textContent,/obrázek.*nepodařilo/);assert.ok(view.element('practiceHero').hidden);view.element('quizNext').click();assert.match(view.element('quizPosition').textContent,/Slovíčko 2/);}
});
test('blocked playback has an explicit gesture retry that preserves the current four images and word',async()=>{
 const view=await practiceView({audioReject:true});completeImages(view);await animateWord(view);await sleep(0);assert.match(view.element('quizMessage').textContent,/Zvuk se nepodařilo/);const ids=choices(view).map(b=>b.dataset.uid);assert.ok(choices(view).every(b=>b.disabled));
 view.setAudioReject(false);view.element('quizReplay').click();await sleep(0);endSound(view);await sleep(0);assert.deepEqual(choices(view).map(b=>b.dataset.uid),ids);assert.ok(choices(view).every(b=>!b.disabled));
});
test('leaving during animation or audio cancels late callbacks; history and bfcache restore usable setup',async()=>{
 const view=await practiceView();completeImages(view);view.win.history.back();const before=view.players.length;await animateWord(view);assert.equal(view.state.view,'gallery');assert.equal(view.players.length,before);
 view.win.history.forward();assert.equal(view.state.view,'quiz');assert.equal(view.element('quizSetup').hidden,false);view.element('quizStart').click();completeImages(view);await animateWord(view);assert.ok(view.players.some(p=>p.played));
 view.emit('pagehide');view.emit('pageshow',{persisted:true});assert.equal(view.element('quizSetup').hidden,false);view.element('quizStart').click();await readyQuestion(view);assert.ok(!correctChoice(view).disabled);
});
test('reduced motion keeps spelling readable immediately, and keyboard answers obey the same correct-answer rules',async()=>{
 const view=await practiceView({reducedMotion:true});completeImages(view);assert.ok(view.element('practiceWord').classList.contains('is-joined'));endSound(view);await sleep(0);
 const correct=correctChoice(view),n=choices(view).indexOf(correct)+1;view.doc.emit('keydown',{key:String(n)});assert.equal(view.element('practiceHero').hidden,false);
});
test('a stalled MP3 times out into an explicit retry or skip instead of leaving all controls locked',async()=>{
 const view=await practiceView();completeImages(view);await animateWord(view);assert.ok(choices(view).every(b=>b.disabled));view.advance(20000);await sleep(0);
 assert.match(view.element('quizMessage').textContent,/Přehrávání se nedokončilo/);assert.equal(view.element('quizNext').disabled,false);assert.ok(view.players.filter(p=>p.played).every(p=>p.paused));
 view.element('quizReplay').click();await sleep(0);endSound(view);await sleep(0);assert.ok(choices(view).every(b=>!b.disabled));
});
test('explicit overview and change-filter buttons return to gallery even when practice was opened from a study card',async()=>{
 for(const id of ['quizBack','quizSetupChange']){const view=await app({items:fourItems});view.openStudy('vit-0001');view.element('quizTab').click();view.element(id).click();assert.equal(view.state.view,'gallery');assert.ok(!view.win.location.href.includes('card='));assert.equal(view.state.lastUid,'vit-0001');}
});

async function writingView(options={}){const view=await app({items:fourItems,...options});view.element('quizTab').click();view.element('practiceWritingToggle').click();view.element('quizStart').click();await readyQuestion(view);correctChoice(view).click();return view;}
async function endFeedback(view){endSound(view);await sleep(0);view.advance(250);await sleep(0);}
async function beginWriting(view){await endFeedback(view);assert.equal(view.element('practiceWritingPanel').hidden,false);return view.element('practiceHeroWord').textContent;}
function typeWriting(view,value,extra={}){const input=view.element('practiceWritingInput');input.value=value;input.emit('input',extra);}

test('writing comparison preserves accents, double letters and punctuation; normalizes NFC, case, spacing and apostrophe typography',()=>{
 for(const [typed,expected] of [['CAFFE\u0300','caffè'],[' mi   chiamo ','mi chiamo'],['un po\u2019',"un po'"],['CONGRATULAZIONI!','Congratulazioni!']])assert.equal(practice.writingMatches(typed,expected),true);
 for(const [typed,expected] of [['caffe','caffè'],['caffé','caffè'],['caffè!','caffè'],['capello','cappello'],['mi chiamo','mi chiamano'],['','']])assert.equal(practice.writingMatches(typed,expected),false);
});
test('optional writing waits for answer audio, hides the spelling, then flashes green and closes only after the complete correct input',async()=>{
 const view=await writingView();assert.equal(view.element('practiceWritingToggle').getAttribute('aria-pressed'),'true');assert.equal(view.element('practiceWritingPanel').hidden,true);assert.equal(view.element('practiceHeroWord').hidden,false);assert.equal(view.element('quizNext').disabled,true);
 view.element('quizNext').click();assert.equal(view.element('practiceHero').hidden,false);
 const word=await beginWriting(view);assert.equal(view.element('practiceHeroWord').hidden,true);assert.equal(view.element('practiceHeroImage').alt,'Obrázek k procvičování');assert.equal(view.doc.activeElement,view.element('practiceWritingInput'));
 typeWriting(view,word.slice(0,-1));assert.equal(view.element('practiceWritingInput').readOnly,false);assert.equal(view.element('practiceWritingPanel').hidden,false);
 typeWriting(view,word);assert.equal(view.element('practiceWritingInput').readOnly,true);assert.ok(view.element('practiceWritingInput').classList.contains('is-correct'));assert.equal(view.element('quizNext').disabled,true);
 view.advance(599);assert.equal(view.element('practiceWritingPanel').hidden,false);view.advance(1);assert.equal(view.element('practiceWritingPanel').hidden,true);assert.equal(view.element('practiceHeroWord').hidden,false);assert.equal(view.element('quizNext').disabled,true);await endFeedback(view);assert.equal(view.element('quizNext').disabled,false);assert.equal(view.doc.activeElement,view.element('quizNext'));
});
test('half-second hints preserve the draft and a repeated click restarts the hint window',async()=>{
 const view=await writingView();const word=await beginWriting(view),draft=word.slice(0,2);typeWriting(view,draft);view.element('practiceWritingHint').click();assert.equal(view.element('practiceHeroWord').hidden,false);assert.equal(view.element('practiceWritingInput').value,draft);
 view.advance(499);assert.equal(view.element('practiceHeroWord').hidden,false);view.advance(1);assert.equal(view.element('practiceHeroWord').hidden,true);
 assert.equal(view.element('practiceWritingHintStatus').textContent,`Nápověda 1: ${word}`);assert.equal(view.element('practiceWritingHintStatus').children[1].lang,'it');
 view.element('practiceWritingHint').click();view.advance(300);view.element('practiceWritingHint').click();view.advance(200);assert.equal(view.element('practiceHeroWord').hidden,false);view.advance(300);assert.equal(view.element('practiceHeroWord').hidden,true);assert.equal(view.element('practiceWritingInput').value,draft);
 assert.equal(view.element('practiceWritingHintStatus').textContent,`Nápověda 3: ${word}`);typeWriting(view,draft);assert.equal(view.element('practiceWritingHintStatus').textContent,'');
});
test('accent entry through composition is not accepted early; Enter explains an incorrect spelling',async()=>{
 const ids=['vit-0285','vit-0366','vit-0334','vit-0292'];const view=await writingView({items:vocabulary.items.filter(i=>ids.includes(i.uid))});const word=await beginWriting(view);const plain=word.normalize('NFD').replace(/[\u0300-\u036f]/g,'');assert.notEqual(word,plain);
 typeWriting(view,plain);view.element('practiceWritingInput').emit('keydown',{key:'Enter'});assert.equal(view.element('practiceWritingInput').getAttribute('aria-invalid'),'true');assert.equal(view.element('practiceWritingPanel').hidden,false);
 view.element('practiceWritingInput').emit('compositionstart');typeWriting(view,word.toUpperCase().normalize('NFD'),{isComposing:true});assert.equal(view.element('practiceWritingInput').readOnly,false);view.element('practiceWritingInput').emit('compositionend');assert.equal(view.element('practiceWritingInput').readOnly,true);view.advance(600);assert.equal(view.element('practiceWritingPanel').hidden,true);
});
test('audio replay while writing keeps the draft and spelling hidden; green confirmation cannot be cancelled by replay or hints',async()=>{
 const view=await writingView();const word=await beginWriting(view),draft=word.slice(0,2);typeWriting(view,draft);view.element('practiceWritingHint').click();view.element('quizReplay').click();await sleep(0);assert.equal(view.element('practiceHeroWord').hidden,true);assert.equal(view.element('practiceWritingInput').value,draft);endSound(view);await sleep(0);assert.equal(view.element('practiceWritingInput').value,draft);
 typeWriting(view,word);view.element('quizReplay').click();view.element('practiceWritingHint').click();view.advance(600);assert.equal(view.element('practiceWritingPanel').hidden,true);assert.equal(view.element('quizNext').disabled,true);await endFeedback(view);assert.equal(view.element('quizNext').disabled,false);
});
test('writing can be enabled on an already-read card or disabled mid-draft without locking Next or losing the picture',async()=>{
 const view=await practiceView();await readyQuestion(view);correctChoice(view).click();await endFeedback(view);view.element('practiceWritingToggle').click();assert.equal(view.element('practiceWritingPanel').hidden,false);const word=view.element('practiceHeroWord').textContent;typeWriting(view,word.slice(0,2));view.element('practiceWritingHint').click();
 view.element('practiceWritingToggle').click();assert.equal(view.element('practiceWritingPanel').hidden,true);assert.equal(view.element('practiceHeroWord').hidden,false);assert.equal(view.element('quizNext').disabled,false);view.advance(500);assert.equal(view.element('practiceHeroWord').hidden,false);
 view.element('practiceWritingToggle').click();assert.equal(view.element('practiceWritingPanel').hidden,false);typeWriting(view,word);view.advance(600);view.element('practiceWritingToggle').click();view.element('practiceWritingToggle').click();assert.equal(view.element('practiceWritingPanel').hidden,true);
});
test('failed or stalled answer audio keeps the spelling visible and permits retry before writing',async()=>{
 for(const timeout of [false,true]){const view=await writingView();if(timeout)view.advance(20000);else view.players.find(p=>p.handlers.error).handlers.error();await sleep(0);assert.equal(view.element('practiceWritingPanel').hidden,true);assert.equal(view.element('practiceHeroWord').hidden,false);assert.equal(view.element('quizNext').disabled,false);
  view.element('quizReplay').click();await sleep(0);assert.equal(view.element('quizNext').disabled,true);await endFeedback(view);assert.equal(view.element('practiceWritingPanel').hidden,false);
 }
});
test('leaving or bfcache restoration clears hint and writing callbacks; keyboard digits never answer a picture while typing',async()=>{
 const view=await writingView();const word=await beginWriting(view);view.element('practiceWritingHint').click();view.doc.emit('keydown',{key:'1',target:view.element('practiceWritingInput')});assert.equal(view.element('practiceWritingPanel').hidden,false);
 view.element('quizBack').click();view.advance(10000);assert.equal(view.state.view,'gallery');assert.equal(view.element('practiceWritingPanel').hidden,true);
 view.element('quizTab').click();view.element('quizStart').click();await readyQuestion(view);correctChoice(view).click();await beginWriting(view);typeWriting(view,view.element('practiceHeroWord').textContent);view.emit('pagehide');view.emit('pageshow',{persisted:true});view.advance(1000);assert.equal(view.element('quizSetup').hidden,false);assert.equal(view.element('practiceWritingPanel').hidden,true);
});
test('writing summary counts successful entries and hints without changing learner selections or persisting a draft',async()=>{
 const view=await app({items:fourItems,blocked:true});view.element('quizTab').click();view.element('practiceWritingToggle').click();view.element('quizStart').click();
 for(let n=0;n<4;n++){await readyQuestion(view);correctChoice(view).click();const word=await beginWriting(view);if(n===0)view.element('practiceWritingHint').click();typeWriting(view,word);view.advance(600);await endFeedback(view);view.element('quizNext').click();}
 assert.equal(view.element('quizEnd').hidden,false);assert.match(view.element('quizResult').textContent,/Správné zápisy: 4\. Použití nápovědy: 1/);assert.equal(view.local.getItem(learners.KEY),null);
});


test('feedback audio owns the large card until its real end; rapid Next and replay cannot cut it short',async()=>{
 const view=await practiceView();await readyQuestion(view);correctChoice(view).click();const before=view.element('quizPosition').textContent,plays=view.players.reduce((n,p)=>n+p.playCount,0);
 assert.equal(view.element('quizNext').disabled,true);assert.equal(view.element('quizReplay').disabled,true);
 view.element('quizNext').click();view.element('quizReplay').click();view.advance(5000);await sleep(0);
 assert.equal(view.element('quizPosition').textContent,before);assert.equal(view.players.reduce((n,p)=>n+p.playCount,0),plays);
 endSound(view);await sleep(0);view.advance(250);assert.equal(view.element('quizNext').disabled,false);
});
test('practice starts a separate playback at zero even when rewinding a finished media element is asynchronous',async()=>{
 const view=await practiceView({delayedSeek:true});await readyQuestion(view);const first=view.players.find(p=>p.played);correctChoice(view).click();await sleep(0);
 const feedback=view.players.find(p=>p.handlers.ended);assert.ok(feedback);assert.equal(feedback.starts.at(-1),0);assert.notEqual(feedback,first);
 first.handlers.ended?.();await sleep(0);assert.equal(view.element('quizNext').disabled,true);
});
test('successful writing restores the card and reads it again; Next waits for this final reading',async()=>{
 const view=await writingView();const word=await beginWriting(view),before=view.players.reduce((n,p)=>n+p.playCount,0);typeWriting(view,word);view.advance(600);await sleep(0);
 assert.equal(view.element('practiceWritingPanel').hidden,true);assert.equal(view.element('practiceHeroWord').hidden,false);assert.equal(view.players.reduce((n,p)=>n+p.playCount,0),before+1);assert.equal(view.element('quizNext').disabled,true);
 endSound(view);await sleep(0);view.advance(250);assert.equal(view.element('quizNext').disabled,false);assert.match(view.element('quizMessage').textContent,/Správně napsáno/);
});

test('writing toggles cannot unlock Next while audio or its trailing pause owns the card',async()=>{
 const view=await practiceView();await readyQuestion(view);correctChoice(view).click();
 for(let n=0;n<4;n++)view.element('practiceWritingToggle').click();assert.equal(view.element('quizNext').disabled,true);
 endSound(view);await sleep(0);view.element('practiceWritingToggle').click();view.element('practiceWritingToggle').click();view.advance(249);assert.equal(view.element('quizNext').disabled,true);view.advance(1);assert.equal(view.element('quizNext').disabled,false);
});
test('turning writing off during green confirmation still reads the completed word exactly once',async()=>{
 const view=await writingView();const word=await beginWriting(view);typeWriting(view,word);const before=view.players.reduce((n,p)=>n+p.playCount,0);view.element('practiceWritingToggle').click();view.advance(600);await sleep(0);
 assert.equal(view.element('practiceWritingPanel').hidden,true);assert.equal(view.players.reduce((n,p)=>n+p.playCount,0),before+1);assert.equal(view.element('quizNext').disabled,true);await endFeedback(view);assert.equal(view.element('quizNext').disabled,false);
});
test('a final post-writing audio error or timeout offers retry and never traps the completed answer',async()=>{
 for(const timeout of [false,true]){const view=await writingView();const word=await beginWriting(view);typeWriting(view,word);view.advance(600);await sleep(0);const attempt=view.players.find(p=>p.handlers.ended);
  if(timeout)view.advance(20000);else attempt.handlers.error();await sleep(0);assert.equal(view.element('practiceWritingPanel').hidden,true);assert.equal(view.element('quizNext').disabled,false);assert.equal(view.element('quizReplay').disabled,false);
  view.element('quizReplay').click();await sleep(0);assert.equal(view.element('quizNext').disabled,true);await endFeedback(view);assert.equal(view.element('quizNext').disabled,false);assert.equal(view.element('practiceWritingPanel').hidden,true);
 }
});
test('leaving during the final reading or its trailing pause cancels every old transition',async()=>{
 for(const trailing of [false,true]){const view=await writingView();const word=await beginWriting(view);typeWriting(view,word);view.advance(600);const attempt=view.players.find(p=>p.handlers.ended),lateEnd=attempt.handlers.ended;
  if(trailing){lateEnd();await sleep(0);}view.element('quizBack').click();lateEnd();view.advance(10000);await sleep(0);assert.equal(view.state.view,'gallery');assert.equal(view.element('practiceWritingPanel').hidden,true);assert.equal(view.element('quizRound').hidden,true);
 }
});


// Real Italian gallery module: complete optional sentence map plus inherited loop timing.
function loopPlayer(view){return view.players.find(p=>p.handlers.ended&&!p.paused);}
function setLoop(view,mode='sentence-word'){change(view,'studyLoopMode',mode);}
async function loopPhase(view){const player=loopPlayer(view);assert.ok(player);player.position=2;player.ended=true;player.handlers.ended();await sleep(0);view.advance(2000);await sleep(0);}
function pictureLabels(view){return view.element('sentencePictures').querySelectorAll('figcaption').map(n=>n.textContent);}
test('all1116 reviewed Italian sentence rows resolve1–5 exact image meanings and spans',()=>{
 let total=0;
 for(const item of vocabulary.items){const refs=model.sentencePictures(item,pictures,vocabulary.items);assert.ok(refs.length>=1&&refs.length<=5,item.uid);assert.equal(new Set(refs.map(r=>r.item.image)).size,refs.length);for(const r of refs)assert.equal(item.sentenceIt.slice(r.start,r.end),r.text);total+=refs.length;}
 assert.equal(Object.keys(pictures.entries).length,1116);assert.equal(total,2631);
});
test('Italian sentence map handles elided nouns and rejects stale, foreign, retired and malformed references',()=>{
 const item=vocabulary.items.find(i=>i.uid==='vit-0617');assert.equal(model.sentencePictures(item,pictures,vocabulary.items)[0].text,'acqua');
 for(const mode of ['foreign','sentence','translation','meaning','span','unknown','order','shape','duplicate']){
  const m=JSON.parse(JSON.stringify(pictures)),r=m.entries['vit-0083'],target=vocabulary.items.find(i=>i.uid==='vit-0083');
  if(mode==='foreign')m.language='en';if(mode==='sentence')r.sourceSentenceIt+='x';if(mode==='translation')r.sourceSentenceCz+='x';if(mode==='meaning')r.concepts[0].sourceCz+='x';if(mode==='span')r.concepts[0].start=true;if(mode==='unknown')r.concepts[0].uid='vit-9999';if(mode==='order')r.concepts.reverse();if(mode==='shape')r.concepts=null;if(mode==='duplicate')r.concepts[1]=r.concepts[0];assert.deepEqual(model.sentencePictures(target,m,vocabulary.items),[],mode);
 }
 const retired=vocabulary.items.map(i=>i.uid===item.uid?{...i,active:false}:i);assert.deepEqual(model.sentencePictures(item,pictures,retired),[]);
});
test('Italian pictures show above the sentence then restore its large target word using one fully reloaded player',async()=>{
 const v=await app();v.openStudy('vit-0083');setLoop(v);v.element('studyLoopToggle').click();assert.deepEqual(pictureLabels(v),['oggi','gonna','nero','camicia','bianco']);assert.equal(v.element('promptText').lang,'it');assert.equal(v.element('studyLoopTranslation').textContent,v.state.currentItem.sentenceCz);const player=loopPlayer(v);assert.match(player.url,/sentences/);assert.equal(player.starts.at(-1),0);
 await loopPhase(v);assert.equal(v.element('sentencePictures').hidden,true);assert.equal(v.element('promptText').textContent,'gonna');assert.equal(v.element('studyLoopTranslation').textContent,'sukně');assert.equal(loopPlayer(v),player);assert.equal(player.loadCount,2);assert.equal(player.starts.at(-1),0);v.element('studyLoopStop').click();
});
test('Italian loop waits for true ended and complete gap; stale ended after load cannot cut the next word',async()=>{
 const v=await app({items:vocabulary.items.slice(0,2)});v.openStudy('vit-0001');setLoop(v);v.element('studyLoopToggle').click();const p=loopPlayer(v),first=p.handlers.ended;v.advance(60000);await sleep(0);assert.equal(p.playCount,1);p.ended=true;p.handlers.ended();await sleep(0);v.advance(1999);await sleep(0);assert.equal(p.playCount,1);v.advance(1);await sleep(0);assert.equal(p.playCount,2);first();p.handlers.ended();await sleep(0);v.advance(10000);await sleep(0);assert.equal(p.playCount,2);await loopPhase(v);assert.equal(v.state.currentItem.uid,'vit-0002');v.element('studyLoopStop').click();
});
test('Italian personal A hard single-card loop uses context outside A without changing its profile',async()=>{
 const local=storage(),value=learners.empty();value.profiles.A.selected=['vit-0083'];value.profiles.A.hard=['vit-0083'];local.setItem(learners.KEY,JSON.stringify(value));const before=local.getItem(learners.KEY);const v=await app({local});change(v,'learnerSelect','A');v.element('learnerHardFilter').click();v.openStudy('vit-0083');setLoop(v);v.element('studyLoopToggle').click();assert.equal(v.state.sequence.length,1);assert.equal(pictureLabels(v).length,5);await loopPhase(v);await loopPhase(v);assert.equal(v.state.currentItem.uid,'vit-0083');assert.equal(pictureLabels(v).length,5);assert.equal(local.getItem(learners.KEY),before);v.returnToGallery();assert.equal(local.getItem(learners.KEY),before);
});
test('Italian pause/resume restarts the same phase; stop restores manual question and a late callback cannot restart sound',async()=>{
 const v=await app();v.openStudy('vit-0083');const original=v.element('promptText').textContent;setLoop(v);v.element('studyLoopToggle').click();const p=loopPlayer(v),late=p.handlers.ended;p.position=.6;v.element('studyLoopToggle').click();assert.ok(p.paused);v.element('studyLoopToggle').click();assert.equal(loopPlayer(v),p);assert.equal(p.starts.at(-1),0);v.element('studyLoopStop').click();late();v.advance(120000);await sleep(0);assert.equal(v.element('promptText').textContent,original);assert.equal(v.element('sentencePictures').hidden,true);assert.equal(loopPlayer(v),undefined);
});
test('Italian loop error, timeout and rejected play pause the same card and do not skip',async()=>{
 for(const failure of ['error','timeout','reject']){const v=await app({audioReject:failure==='reject'});v.openStudy('vit-0083');setLoop(v);v.element('studyLoopToggle').click();const p=loopPlayer(v);if(failure==='error')p.handlers.error();if(failure==='timeout')v.advance(90000);await sleep(0);assert.match(v.element('studyLoopStatus').textContent,/pozastavená/);assert.equal(v.state.currentItem.uid,'vit-0083');assert.equal(loopPlayer(v),undefined);v.element('studyLoopStop').click();}
});
test('Italian optional missing pictures preserve sentence audio; failed tiles and detached events never stop or alter a new phase',async()=>{
 for(const pictureManifest of [null,{}]){const v=await app({pictureManifest});v.openStudy('vit-0083');setLoop(v);v.element('studyLoopToggle').click();assert.equal(v.element('sentencePictures').hidden,true);assert.ok(loopPlayer(v));v.element('studyLoopStop').click();}
 const v=await app();v.openStudy('vit-0083');setLoop(v);v.element('studyLoopToggle').click();const p=loopPlayer(v),old=v.element('sentencePictures').querySelector('img');old.emit('error');assert.equal(pictureLabels(v).length,4);assert.equal(loopPlayer(v),p);for(const img of v.element('sentencePictures').querySelectorAll('img'))img.emit('error');assert.equal(v.element('sentencePictures').hidden,true);assert.equal(v.element('studyView').classList.contains('sentence-context'),false);await loopPhase(v);old.emit('error');assert.equal(v.element('promptText').textContent,'gonna');assert.equal(v.element('sentencePictures').hidden,true);v.element('studyLoopStop').click();
});
test('Italian delayed picture metadata waits for a new sentence and never changes currently playing audio',async()=>{
 let resolve;const pending=new Promise(done=>resolve=done);const v=await app({pictureDeferred:pending});v.state.query='sukně';v.selectionChanged();v.openStudy('vit-0083');setLoop(v);v.element('studyLoopToggle').click();const p=loopPlayer(v);assert.equal(v.element('sentencePictures').hidden,true);resolve(pictures);await sleep(0);assert.equal(v.element('sentencePictures').hidden,true);assert.equal(loopPlayer(v),p);await loopPhase(v);await loopPhase(v);assert.equal(pictureLabels(v).length,5);v.element('studyLoopStop').click();
});
test('Italian loop leaves no autostart through pagehide, bfcache or reload and keeps manual sentence guessing unchanged',async()=>{
 const v=await app();v.openStudy('vit-0083');v.practices[1].click();assert.equal(v.element('answerCard').classList.contains('hidden'),true);assert.equal(v.element('sentencePictures').hidden,true);setLoop(v);v.element('studyLoopToggle').click();const p=loopPlayer(v);v.emit('pagehide');v.emit('pageshow',{persisted:true});assert.ok(p.paused);assert.equal(loopPlayer(v),undefined);const reopened=await app({local:v.local,session:v.session,url:v.win.location.href});assert.equal(reopened.players.some(p=>p.played),false);assert.equal(reopened.element('sentencePictures').hidden,true);
});
test('Italian words-only loop follows the explicit filtered sequence and keeps sentence images hidden',async()=>{
 const v=await app({items:vocabulary.items.slice(0,3)});v.openStudy('vit-0001','random');const order=v.state.sequence.map(model.key),start=v.state.index;setLoop(v,'words');v.element('studyLoopToggle').click();for(let i=1;i<=4;i++){await loopPhase(v);assert.equal(v.state.currentItem.uid,order[(start+i)%order.length]);assert.equal(v.element('sentencePictures').hidden,true);}v.returnToGallery();assert.equal(v.state.view,'gallery');assert.equal(loopPlayer(v),undefined);
});

test('approved refresh reuses new meanings in old text and preserves homographs',()=>{
 const row=id=>vocabulary.items.find(i=>i.id===id);
 const concepts=id=>model.sentencePictures(row(id),pictures,vocabulary.items);
 assert.equal(row(28).sentenceIt,'Compro pane e latte.');
 assert.deepEqual(concepts(28).map(c=>c.item.it),['comprare','pane','e','latte']);
 assert.deepEqual(concepts(604).map(c=>c.item.it),['mettere','tre','bicchiere','pulito','tavolo']);
 assert.equal(concepts(867).find(c=>c.text==='porta').item.uid,'vit-0682');
 assert.equal(concepts(936).find(c=>c.text==='mostra').item.uid,'vit-0805');
 for(const id of [728,956])assert.ok(!concepts(id).some(c=>c.item.it==='vento'));
 const latest=model.select(vocabulary.items,{recentCount:20});
 assert.deepEqual(new Set(latest.map(i=>i.id)),new Set(Array.from({length:20},(_,i)=>1097+i)));
});

test('new word loops show context then its own correct word without changing profiles',async()=>{
 const v=await app();v.openStudy('vit-1097');setLoop(v);v.element('studyLoopToggle').click();
 assert.deepEqual(pictureLabels(v),['oggi','portare','figlio','museo']);
 assert.equal(v.element('promptText').textContent,'Oggi porto mio figlio al museo.');
 assert.equal(v.element('studyLoopTranslation').textContent,'Dnes beru svého syna do muzea.');
 await loopPhase(v);
 assert.equal(v.element('sentencePictures').hidden,true);
 assert.equal(v.element('promptText').textContent,'oggi');
 assert.equal(v.element('studyLoopTranslation').textContent,'dnes');
 v.element('studyLoopStop').click();
});

test('new ambiguous picture motifs cannot be distractors for their close meanings',()=>{
 for(const heads of [['risposta','sì'],['nuovo','zaino'],['studiare','leggere'],['sedersi','accomodarsi']]){
  const left=vocabulary.items.find(i=>i.it===heads[0]),right=vocabulary.items.find(i=>i.it===heads[1]);
  assert.ok(quizCatalog.entries[left.uid].conflicts.some(group=>quizCatalog.entries[right.uid].conflicts.includes(group)));
 }
});

const flush=async()=>{for(let n=0;n<12;n++)await Promise.resolve();};
const clone=value=>JSON.parse(JSON.stringify(value));
const cat=vocabulary.items[0];
function active(view){return view.players.find(p=>!p.paused);}
function ended(view){const player=active(view);assert.ok(player);player.ended=true;player.paused=true;player.handlers.ended?.();}
const memory=require('../../docs/vocabulary-it/memory.js');
const memoryPool=memory.choose(vocabulary.items,audio,quizCatalog,()=>.5);
const memorySaved=v=>JSON.parse(v.session.getItem(memory.KEY));
const memoryButton=(v,n)=>v.element('memoryBoard').children[n].querySelector('button');
async function memoryView(count=2,options={}){
 const v=await app(options);v.element('memoryTab').click();change(v,'memoryPlayerCount',String(count));
 v.element('memoryNames').querySelectorAll('input').forEach((input,i)=>{input.value=['Jana','Eva','Petr','Tom'][i];input.emit('input');});
 v.element('memoryStart').click();await flush();return v;
}
async function memoryHear(v,n){memoryButton(v,n).click();await until(()=>active(v));assert.match(active(v).url,/-it\.mp3$/);ended(v);await flush();v.advance(2000);await flush();}
async function memoryFinishReward(v){await until(()=>active(v));ended(v);await flush();v.advance(2000);await flush();}
async function memoryPair(v,a,b){await memoryHear(v,a);await memoryHear(v,b);v.advance(1000);await flush();if(v.element('memoryReward').open)await memoryFinishReward(v);}
function memoryPositions(g,uid){return g.deck.flatMap((x,i)=>x===uid?[i]:[]);}

test('IT memory chooses12 distinct compatible meanings with Italian audio and keeps source metadata intact',()=>{
 const before=JSON.stringify([vocabulary,audio,quizCatalog]);assert.equal(memoryPool.length,12);
 const game=memory.newGame(memoryPool,['Jana']);assert.equal(game.deck.length,24);assert.equal(new Set(game.deck).size,12);
 for(const uid of new Set(game.deck))assert.equal(memoryPositions(game,uid).length,2);
 const changed=clone(audio);changed.items[cat.uid].it=null;assert.equal(memory.choose([cat],changed,quizCatalog).length,0);
 const sameAudio=clone(audio);sameAudio.items[vocabulary.items[1].uid].it=sameAudio.items[cat.uid].it;
 assert.equal(memory.choose([cat,vocabulary.items[1]],sameAudio,quizCatalog).length,1);
 assert.equal(memory.choose(memoryPool.slice(0,11),audio,quizCatalog).length,11);
 assert.equal(JSON.stringify([vocabulary,audio,quizCatalog]),before);
});
test('IT memory keeps consecutive successful turns for one named player and cycles1–4 players on misses',()=>{
 for(let n=1;n<=4;n++){
  let g=memory.newGame(memoryPool,['Jana','Eva','Petr','Tom'].slice(0,n));
  assert.throws(()=>memory.settle(g,0,24));assert.throws(()=>memory.settle(g,0,0));
  g=memory.settle(g,0,g.deck.findIndex(x=>x!==g.deck[0]));assert.equal(g.active,1%n);
  const owner=g.active;for(const uid of new Set(g.deck)){g=memory.settle(g,...memoryPositions(g,uid));assert.equal(g.active,owner);}
  assert.equal(Object.keys(g.owners).length,12);assert.equal(Object.values(g.owners).filter(x=>x===owner).length,12);
  assert.throws(()=>memory.settle(g,...memoryPositions(g,g.deck[0])));
 }
});
test('IT memory opens24 numbered backs, short names and projector view without leaking Italian answers',async()=>{
 const v=await memoryView(4);assert.equal(v.state.view,'memory');assert.match(v.win.location.href,/game=memory-pairs/);
 assert.equal(v.element('memoryBoard').children.length,24);assert.equal(v.element('memoryBoard').querySelectorAll('img').length,0);
 v.element('memoryBoard').children.forEach((slot,n)=>{const b=slot.querySelector('button');assert.equal(b.textContent,String(n+1));assert.equal(b.getAttribute('aria-label'),`Kartička ${n+1}, zavřená`);});
 assert.deepEqual(memorySaved(v).game.players,['Jana','Eva','Petr','Tom']);assert.equal(v.element('memoryScores').children.length,4);
 v.element('memoryProjector').click();assert.equal(v.element('memoryView').classList.contains('memory-projector'),true);
});
test('IT memory waits for Italian audio completion and two-second Czech hint and ignores rapid extra clicks',async()=>{
 const v=await memoryView();memoryButton(v,0).click();await until(()=>active(v));const p=active(v);
 assert.match(p.url,/-it\.mp3$/);assert.equal(v.element('memoryBoard').querySelector('.memory-word').lang,'it');
 assert.equal(v.element('memoryBoard').querySelectorAll('.memory-translation').length,1);
 memoryButton(v,1).click();v.advance(2000);await flush();assert.equal(v.element('memoryBoard').querySelectorAll('.memory-translation').length,0);
 assert.equal(memoryButton(v,1).disabled,true);assert.equal(v.players.filter(p=>p.playCount>0).length,1);
 ended(v);await flush();assert.equal(memoryButton(v,1).disabled,false);assert.equal(memorySaved(v).game.turns,0);
});
test('IT memory awards a pair once, leaves two grey holes and preserves the same player for another pair',async()=>{
 const v=await memoryView(3),g=memorySaved(v).game,[a,b]=memoryPositions(g,g.deck[0]);
 await memoryHear(v,a);await memoryHear(v,b);assert.equal(v.element('memoryBoard').querySelectorAll('.memory-match').length,2);
 v.advance(1000);await flush();assert.equal(v.element('memoryBoard').querySelectorAll('.memory-empty').length,2);
 assert.equal(memorySaved(v).game.active,0);assert.match(v.element('memoryScores').children[0].textContent,/Jana.*Dvojice: 1/);
 await memoryFinishReward(v);const uid=g.deck.find(x=>x!==g.deck[0]);await memoryPair(v,...memoryPositions(g,uid));assert.equal(memorySaved(v).game.active,0);assert.equal(Object.keys(memorySaved(v).game.owners).length,2);
});
test('IT memory mismatch closes both cards and changes to the next player',async()=>{
 const v=await memoryView(3),g=memorySaved(v).game;await memoryPair(v,0,g.deck.findIndex(x=>x!==g.deck[0]));
 assert.equal(memorySaved(v).game.active,1);assert.equal(v.element('memoryBoard').querySelectorAll('img').length,0);assert.equal(v.element('memoryBoard').children.length,24);
});
test('IT memory restores completed turns and original selection after reload without autoplay',async()=>{
 const v=await memoryView(),g=memorySaved(v).game;await memoryPair(v,...memoryPositions(g,g.deck[0]));
 memoryButton(v,g.deck.findIndex(x=>x!==g.deck[0])).click();await until(()=>active(v));v.emit('pagehide');
 const reloaded=await app({session:v.session,local:v.local,url:v.win.location.href+'&topics=topic-01'});assert.equal(reloaded.state.view,'memory');assert.equal(active(reloaded),undefined);
 reloaded.element('memoryResume').click();assert.equal(reloaded.element('memoryBoard').children.length,24);assert.deepEqual([...reloaded.state.topics],['topic-01']);
 assert.equal(reloaded.element('memoryBoard').querySelectorAll('.memory-empty').length,2);assert.equal(reloaded.element('memoryBoard').querySelectorAll('img').length,0);assert.equal(memorySaved(reloaded).game.turns,1);
 const saved=memorySaved(reloaded);assert.deepEqual(memory.restore(saved,vocabulary.items,audio,quizCatalog),saved.game);
 const bad=clone(saved);bad.game.deck[0]='ven-0001';assert.equal(memory.restore(bad,vocabulary.items,audio,quizCatalog),null);
 const changed=clone(audio);changed.items[g.deck[0]].it=null;assert.equal(memory.restore(saved,vocabulary.items,changed,quizCatalog),null);
});
test('IT memory respects A–D selections and hard words plus gallery filters without modifying profiles',async()=>{
 const saved=learners.empty();saved.profiles.A.selected=memoryPool.map(i=>i.uid);saved.profiles.A.hard=[...saved.profiles.A.selected];saved.profiles.B.selected=[vocabulary.items[1].uid];
 const raw=JSON.stringify(saved),local=storage(new Map([[learners.KEY,raw],['vocabulary-en.memory-pairs.v1','unrelated']]));
 const v=await app({local});change(v,'learnerSelect','A');v.element('learnerHardFilter').click();const before=JSON.stringify([...local.map]);
 v.element('memoryTab').click();assert.match(v.element('memorySelection').textContent,/Uživatel A.*Jen obtížná/);assert.equal(v.element('memoryStart').disabled,false);v.element('memoryStart').click();
 assert.ok(memorySaved(v).game.deck.every(uid=>memoryPool.some(i=>i.uid===uid)));await memoryHear(v,0);assert.equal(JSON.stringify([...local.map]),before);
 v.element('memoryBack').click();v.state.query='nonexistent-xyz';v.selectionChanged();v.element('memoryTab').click();assert.equal(v.element('memoryStart').disabled,true);
 v.element('memorySetupChange').click();v.state.query='';v.state.recentCount=1;v.selectionChanged();v.element('memoryTab').click();assert.equal(v.element('memoryStart').disabled,true);
 assert.equal(local.getItem(learners.KEY),raw);assert.equal(local.getItem('vocabulary-en.memory-pairs.v1'),'unrelated');
});
test('IT memory failures offer retry or explicit skip and never borrow the Czech channel',async()=>{
 const v=await memoryView(2,{audioReject:true});memoryButton(v,0).click();await flush();v.advance(2000);await flush();
 assert.equal(v.element('memorySkip').hidden,false);assert.equal(memorySaved(v).game.turns,0);assert.ok(v.players.filter(p=>p.playCount).every(p=>/-it\.mp3$/.test(p.url)));
 v.setAudioReject(false);v.element('memoryRetry').click();await until(()=>active(v));ended(v);await flush();v.advance(2000);await flush();assert.equal(memoryButton(v,1).disabled,false);
 const none=await memoryView(2,{manifest:null});assert.equal(none.element('memoryStart').disabled,true);assert.equal(active(none),undefined);
});
test('IT memory confirms leaving for gallery, practice or settings and cancels stale audio when approved',async()=>{
 const v=await memoryView();memoryButton(v,0).click();await until(()=>active(v));const p=active(v);
 v.win.confirm=()=>false;for(const id of ['galleryTab','quizTab','settingsTab']){v.element(id).click();assert.equal(v.state.view,'memory');}
 v.win.confirm=()=>true;v.element('quizTab').click();assert.equal(v.state.view,'quiz');assert.equal(p.paused,true);v.advance(10000);await flush();assert.equal(memorySaved(v).game.turns,0);
 v.element('memoryTab').click();v.element('memoryResume').click();v.win.confirm=()=>false;v.win.location.href='https://example.test/PythonMF/vocabulary-it/#card='+cat.uid;v.emit('hashchange');assert.equal(v.state.view,'memory');assert.match(v.win.location.href,/memory-pairs/);
});
test('IT memory finishes12 pairs with tie, player collections and replay of the same vocabulary',async()=>{
 const g=memory.newGame(memoryPool,['Jana','Eva']),uids=[...new Set(g.deck)];g.owners=Object.fromEntries(uids.slice(0,11).map((uid,n)=>[uid,n<6?0:1]));g.active=1;g.turns=11;
 const session=storage();session.setItem(memory.KEY,JSON.stringify({version:1,filters:{},game:g,source:memory.signature(g.deck,vocabulary.items,audio)}));
 const v=await app({session,url:'https://example.test/PythonMF/vocabulary-it/#game=memory-pairs'});v.element('memoryResume').click();await memoryPair(v,...memoryPositions(g,uids[11]));
 assert.equal(v.element('memoryEnd').hidden,false);assert.match(v.element('memoryResult').textContent,/Remíza/);assert.equal(v.element('memoryCollections').children.length,2);assert.equal(v.element('memoryBoard').querySelectorAll('.memory-empty').length,24);
 v.element('memoryAgain').click();assert.equal(v.element('memoryEnd').hidden,true);assert.equal(Object.keys(memorySaved(v).game.owners).length,0);assert.deepEqual([...new Set(memorySaved(v).game.deck)].sort(),uids.sort());
});
test('IT memory works with blocked storage and never starts or resumes audio from its link',async()=>{
 const v=await memoryView(1,{blocked:true,url:'https://example.test/PythonMF/vocabulary-it/#game=memory-pairs'});
 assert.equal(v.element('memoryBoard').children.length,24);assert.match(v.element('memoryStorageNotice').textContent,/nepodařilo uložit/);assert.equal(active(v),undefined);
 const missing=await app({failQuiz:true});missing.element('memoryTab').click();assert.equal(missing.element('memoryStart').disabled,true);
});

async function memoryAward(v){const g=memorySaved(v).game,[a,b]=memoryPositions(g,g.deck[0]);await memoryHear(v,a);await memoryHear(v,b);v.advance(1000);await flush();return vocabulary.items.find(i=>i.uid===g.deck[0]);}
test('IT memory reward shows a large source image and Italian word only for exactly two seconds after a match',async()=>{
 const v=await memoryView(),item=await memoryAward(v),dialog=v.element('memoryReward');
 assert.equal(dialog.open,true);assert.equal(dialog.hidden,false);assert.equal(v.element('memoryRewardWord').textContent,item.it);
 let prevented=false,stopped=false;dialog.emit('cancel',{preventDefault:()=>{prevented=true;}});dialog.emit('keydown',{key:'Escape',stopPropagation:()=>{stopped=true;}});assert.equal(prevented&&stopped,true);assert.equal(dialog.open,true);
 assert.equal(v.element('memoryRewardImage').src,new URL('../'+item.image,v.win.location.href).toString());
 assert.equal(v.element('memoryRewardWord').textContent.includes(item.cz),false);assert.match(active(v).url,/-it\.mp3$/);
 assert.equal(v.players.filter(p=>p.playCount).length,3);assert.equal(Object.keys(memorySaved(v).game.owners).length,1);
 ended(v);await flush();v.advance(1999);await flush();assert.equal(dialog.open,true);assert.equal(v.element('memoryBoard').querySelector('button').disabled,true);
 v.advance(1);await flush();assert.equal(dialog.open,false);assert.equal(dialog.hidden,true);assert.equal(memorySaved(v).game.active,0);
 const next=v.element('memoryBoard').querySelector('button');assert.equal(next.disabled,false);assert.equal(v.doc.activeElement,next);
});
test('IT memory reward closes after two seconds but a longer Italian recording keeps the next turn locked until ended',async()=>{
 const v=await memoryView();await memoryAward(v);const p=active(v);v.advance(2000);await flush();
 assert.equal(v.element('memoryReward').open,false);assert.equal(v.element('memoryBoard').querySelector('button').disabled,true);
 v.element('memoryBoard').querySelector('button').click();assert.equal(v.players.filter(p=>p.playCount).length,3);
 ended(v);await flush();assert.equal(p.paused,true);assert.equal(v.element('memoryBoard').querySelector('button').disabled,false);assert.equal(memorySaved(v).game.turns,1);
});
test('IT memory reward never appears or adds a third playback for a mismatch',async()=>{
 const v=await memoryView(),g=memorySaved(v).game;await memoryPair(v,0,g.deck.findIndex(x=>x!==g.deck[0]));
 assert.notEqual(v.element('memoryReward').open,true);assert.equal(v.players.filter(p=>p.playCount).length,2);assert.equal(memorySaved(v).game.active,1);
});
test('IT memory interrupted reward is cancelled and the awarded pair survives reload without replay or duplicate scoring',async()=>{
 const v=await memoryView();await memoryAward(v);const p=active(v);v.emit('pagehide');assert.equal(p.paused,true);assert.equal(v.element('memoryReward').hidden,true);
 v.advance(5000);await flush();const raw=v.session.getItem(memory.KEY),reloaded=await app({session:v.session,url:v.win.location.href});
 assert.equal(active(reloaded),undefined);reloaded.element('memoryResume').click();assert.notEqual(reloaded.element('memoryReward').open,true);
 assert.equal(reloaded.element('memoryBoard').querySelectorAll('.memory-empty').length,2);assert.equal(reloaded.session.getItem(memory.KEY),raw);assert.equal(memorySaved(reloaded).game.turns,1);
});
test('IT memory failed reward audio preserves the earned pair, unlocks play and never substitutes Czech',async()=>{
 const v=await memoryView(),g=memorySaved(v).game,[a,b]=memoryPositions(g,g.deck[0]);await memoryHear(v,a);await memoryHear(v,b);v.setAudioReject(true);v.advance(1000);await flush();
 assert.equal(v.element('memoryReward').open,true);v.advance(2000);await flush();assert.equal(v.element('memoryReward').hidden,true);
 assert.equal(Object.keys(memorySaved(v).game.owners).length,1);assert.equal(memorySaved(v).game.active,0);assert.equal(v.element('memoryBoard').querySelector('button').disabled,false);
 assert.match(v.element('memoryStatus').textContent,/Dodatečný zvuk/);assert.ok(v.players.filter(p=>p.playCount).every(p=>/-it\.mp3$/.test(p.url)));
});
test('IT memory shows the last reward before the final result, then completes the game',async()=>{
 const g=memory.newGame(memoryPool,['Jana']),uids=[...new Set(g.deck)];g.owners=Object.fromEntries(uids.slice(0,11).map(uid=>[uid,0]));g.turns=11;
 const session=storage();session.setItem(memory.KEY,JSON.stringify({version:1,filters:{},game:g,source:memory.signature(g.deck,vocabulary.items,audio)}));
 const v=await app({session,url:'https://example.test/PythonMF/vocabulary-it/#game=memory-pairs'});v.element('memoryResume').click();const [a,b]=memoryPositions(g,uids[11]);await memoryHear(v,a);await memoryHear(v,b);v.advance(1000);await flush();
 assert.equal(v.element('memoryReward').open,true);assert.equal(v.element('memoryEnd').hidden,true);assert.equal(Object.keys(memorySaved(v).game.owners).length,12);
 await memoryFinishReward(v);assert.equal(v.element('memoryEnd').hidden,false);assert.match(v.element('memoryResult').textContent,/všech 12/);assert.equal(v.doc.activeElement,v.element('memoryResult'));
});
test('IT memory chooses twelve compatible real cards with existing Italian MP3 and full-size images',()=>{
 const realAudio=JSON.parse(fs.readFileSync(path.join(root,'data/vocabulary-it-audio.json'),'utf8'));
 const pool=memory.choose(vocabulary.items,realAudio,quizCatalog,()=>.5);assert.equal(pool.length,12);
 for(const item of pool)for(const file of [item.image,item.thumbnail,model.audioRecord(item,realAudio).it])assert.ok(fs.statSync(path.join(root,file)).size>0,file);
 assert.equal(memory.KEY,'vocabulary-it.memory-pairs.v1');
});
