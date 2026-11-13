const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");
const root=path.resolve(__dirname,"../../docs");
const model=require(path.join(root,"vocabulary-en/model.js"));
const vocabulary=JSON.parse(fs.readFileSync(path.join(root,"data/vocabulary-en.json"),"utf8"));
const audio=JSON.parse(fs.readFileSync(path.join(root,"data/vocabulary-en-audio.json"),"utf8"));
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
  matches(selector){if(selector.startsWith("."))return this.classList.contains(selector.slice(1));if(selector.startsWith("[data-"))return selector.slice(6,-1) in this.dataset;return this.tagName===selector;}
  querySelectorAll(selector){return this.descendants().filter(node=>node.matches(selector));}querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
  getBoundingClientRect(){return {top:160,width:140,height:180};} focus(){this.doc.activeElement=this;}scrollIntoView(){this.doc.scrolled=this.id;}
}
function storage(map=new Map()){return {map,getItem:key=>map.get(key)||null,setItem:(key,value)=>map.set(key,String(value))};}
async function app({items=vocabulary.items,url="https://example.test/PythonMF/vocabulary-en/",session=storage(),local=storage(),blocked=false,manifest=audio,failData=false,slowAudio=false}={}){
  const doc=new Element("document");doc.doc=doc;doc.title="Vocabulary";
  doc.getElementById=id=>doc.descendants().find(node=>node.id===id)||null;
  doc.createElement=tag=>new Element(tag,doc);doc.createDocumentFragment=()=>new Element("fragment",doc);
  const appRoot=new Element("main",doc);appRoot.dataset={jsonUrl:"../data/vocabulary-en.json",audioUrl:"../data/vocabulary-en-audio.json"};doc.append(appRoot);
  for(const [,id] of html.matchAll(/\bid="([^"]+)"/g)){const node=new Element("div",doc);node.id=id;appRoot.append(node);}
  for(const [data,values] of [["direction",["czToEn","enToCz"]],["label",["en","cz"]]])for(const value of values){const button=new Element("button",doc);button.dataset[data]=value;appRoot.append(button);}
  const listeners={};let scroll=0;const location={href:url};const historyEntries=[{url,state:null}];let historyIndex=0;
  const win={location,innerHeight:844,addEventListener:(name,fn)=>(listeners[name]??=[]).push(fn),scrollTo:value=>{scroll=value.top||0;},get scrollY(){return scroll;},requestAnimationFrame:fn=>fn()};
  const emit=(name,extra={})=>{for(const fn of listeners[name]||[])fn(extra);};
  const travel=delta=>{if(!historyEntries[historyIndex+delta])return;historyIndex+=delta;location.href=historyEntries[historyIndex].url;emit("popstate");emit("hashchange");};
  win.history={get state(){return historyEntries[historyIndex].state;},replaceState:(state,unused,url)=>{location.href=new URL(url,location.href).href;historyEntries[historyIndex]={url:location.href,state};},pushState:(state,unused,url)=>{location.href=new URL(url,location.href).href;historyEntries.splice(historyIndex+1);historyEntries.push({url:location.href,state});historyIndex++;},back:()=>travel(-1),forward:()=>travel(1)};
  if(blocked){Object.defineProperty(win,"sessionStorage",{get(){throw Error("blocked")}});Object.defineProperty(win,"localStorage",{get(){throw Error("blocked")}});}else{win.sessionStorage=session;win.localStorage=local;}
  const players=[];class AudioFixture {constructor(url){this.url=url;this.handlers={};this.currentTime=0;players.push(this);}addEventListener(name,fn){this.handlers[name]=fn;}removeEventListener(name,fn){if(this.handlers[name]===fn)delete this.handlers[name];}pause(){this.paused=true;}play(){this.played=true;return Promise.resolve();}}
  const data={...vocabulary,items};
  const ctx=vm.createContext({document:doc,window:win,URL,URLSearchParams,Audio:AudioFixture,console,fetch:async url=>{if(slowAudio && url.includes("audio"))return new Promise(()=>{});if(failData && !url.includes("audio"))throw Error("offline");if(manifest===null && url.includes("audio"))throw Error("audio unavailable");return {ok:true,json:async()=>url.includes("audio")?manifest:data};}});
  vm.runInContext(fs.readFileSync(path.join(root,"vocabulary-en/model.js"),"utf8"),ctx);
  vm.runInContext(source.replace('void init();','globalThis.ready=init();')+'\nglobalThis.api={state,context,buildSelection,orderedSelection,openStudy,moveStudy,newRandomRound,returnToGallery,renderGallery,selectionChanged,applyRoute,speakPrompt,speakAnswer,stopAudioPlayback};',ctx);
  await ctx.ready;
  return {...ctx.api,doc,win,emit,players,session,local,historyEntries,element:id=>doc.getElementById(id),directions:doc.querySelectorAll("[data-direction]"),labels:doc.querySelectorAll("[data-label]")};
}
const sample=vocabulary.items.slice(0,4);
test("switching translation direction preserves current card and the ordered selection",async()=>{
  const view=await app({items:sample});view.openStudy(sample[0].uid);const first=view.state.currentItem.uid;const sequence=[...view.state.sequence];view.directions[1].click();assert.equal(view.state.currentItem.uid,first);assert.deepEqual([...view.state.sequence],sequence);view.moveStudy(1);assert.notEqual(view.state.currentItem.uid,first);assert.equal(view.state.revealed,false);
});
test("explicit random practice shows every card once in each of three rounds despite direction changes",async()=>{
  const view=await app();view.element("shuffleButton").click();
  for(let round=0;round<3;round++){
    const seen=new Set();for(let i=0;i<425;i++){view.directions[i%2].click();assert.ok(!seen.has(view.state.currentItem.uid));seen.add(view.state.currentItem.uid);if(i<424)view.element("nextButton").click();}
    assert.equal(seen.size,425);assert.equal(view.element("nextButton").hidden,true);assert.match(view.element("roundStatus").textContent,/konec/);if(round<2)view.element("newRoundButton").click();
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
  const animals=model.select(vocabulary.items,{topics:["topic-06"]});const benjiAnimals=model.select(vocabulary.items,{topics:["topic-06"],sources:["benji"]});assert.equal(animals.length,39);assert.equal(benjiAnimals.length,6);
  const union=model.select(vocabulary.items,{topics:["topic-06","topic-05"],sources:["benji"],parts:["noun"]});assert.ok(union.every(i=>i.sourceIds.includes("benji") && i.partOfSpeech.includes("noun") && i.topicIds.some(t=>["topic-06","topic-05"].includes(t))));assert.ok(union.length>6);
  assert.equal(model.select(vocabulary.items,{query:"orisky"})[0].en,"nuts");assert.equal(model.select(vocabulary.items,{query:"orange"}).length,2);
});
test("gallery is the default; all 425 tiles occur once and language never changes order",async()=>{
  const view=await app();assert.equal(view.state.view,"gallery");assert.equal(view.element("studyView").hidden,true);const tiles=view.element("galleryGroups").querySelectorAll(".vocab-tile");assert.equal(tiles.length,425);assert.equal(new Set(tiles.map(t=>t.dataset.uid)).size,425);
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
  const cat=vocabulary.items.find(i=>i.en==="cat");const wrong={items:{[cat.id]:{sourceEn:"cat",sourceCz:"špatně",en:"wrong.mp3"}}};assert.equal(model.audioRecord(cat,wrong),null);const view=await app({manifest:null});assert.equal(view.element("galleryGroups").querySelectorAll(".vocab-tile").length,425);view.openStudy(cat.uid);view.speakPrompt();assert.match(view.element("messageStrip").textContent,/neni pripraveny/);
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
  const numbers=model.ordered(vocabulary.items,{topics:["topic-11"],sort:"recommended"},vocabulary.catalog);assert.deepEqual(numbers.slice(0,12).map(i=>i.en),["one","two","three","four","five","six","seven","eight","nine","ten","eleven","twelve"]);assert.ok(!numbers.some(i=>i.en==="second"));assert.equal(new Set(vocabulary.items.map(model.key)).size,425);
});
test("a broken vocabulary request has an explicit error and does not claim an empty loaded dictionary",async()=>{
  const view=await app({failData:true});assert.equal(view.element("totalCount").textContent,"—");assert.match(view.element("galleryNotice").textContent,/nepodařilo/);assert.equal(view.element("shuffleButton").disabled,true);
});

test("a pending audio request never delays the gallery or prevents a bottom-bar return",async()=>{
  const view=await app({slowAudio:true});assert.equal(view.element("galleryGroups").querySelectorAll(".vocab-tile").length,425);view.openStudy("ven-0020");assert.equal(view.element("backBottomButton").hidden,false);view.element("backBottomButton").click();assert.equal(view.state.view,"gallery");assert.equal(view.doc.activeElement.id,"tile-ven-0020");
});
test("reloading the gallery preserves the frozen random order for browser Forward",async()=>{
  const before=await app();before.state.sources=["benji"];before.selectionChanged();before.openStudy("","random");before.moveStudy(1);
  const uid=before.state.currentItem.uid,order=Array.from(before.state.sequence,i=>i.uid),studyUrl=before.win.location.href;
  before.returnToGallery();
  const after=await app({url:before.win.location.href,session:before.session,local:before.local});
  after.win.history.pushState({vocabularyEN:1,kind:"study",fromGallery:true},"",studyUrl);after.applyRoute();
  assert.equal(after.state.currentItem.uid,uid);assert.deepEqual(Array.from(after.state.sequence,i=>i.uid),order);assert.deepEqual([...after.state.sources],["benji"]);assert.equal(after.state.mode,"random");
});
