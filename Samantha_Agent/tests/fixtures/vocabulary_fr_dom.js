/* Run the real FR modules against a synthetic DOM and synthetic fixtures only. */
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'../../../docs');
const fixture=require('./vocabulary_fr_client.js');
const baseline=fixture.make(),vocabulary=baseline.data,audio=baseline.audio,sentenceAudio=baseline.sentenceAudio,quizCatalog=baseline.quiz,pictures=baseline.pictures;
const model=require(path.join(root,'vocabulary-fr/model.js')),learners=require(path.join(root,'vocabulary-fr/learners.js')),practice=require(path.join(root,'vocabulary-fr/practice.js'));
const html=fs.readFileSync(path.join(root,'vocabulary-fr/index.html'),'utf8'),source=fs.readFileSync(path.join(root,'vocabulary-fr/gallery.js'),'utf8');
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
async function app({items=vocabulary.items,url="https://example.test/PythonMF/vocabulary-fr/",session=storage(),local=storage(),blocked=false,manifest=audio,sentenceManifest=sentenceAudio,failData=false,slowAudio=false,audioReject=false,reducedMotion=false,failQuiz=false,delayedSeek=false,dataOverride={},pictureManifest=pictures,pictureDeferred=null,quizManifest=quizCatalog}={}){
  const doc=new Element("document");doc.doc=doc;doc.title="Vocabulary";
  doc.getElementById=id=>doc.descendants().find(node=>node.id===id)||null;
  doc.createElement=tag=>new Element(tag,doc);doc.createDocumentFragment=()=>new Element("fragment",doc);
  const appRoot=new Element("main",doc);appRoot.dataset={jsonUrl:"../data/vocabulary-fr-v2.json",audioUrl:"../data/vocabulary-fr-audio.json"};doc.append(appRoot);doc.body=appRoot;
  for(const [,id] of html.matchAll(/\bid="([^"]+)"/g)){const node=new Element("div",doc);node.id=id;appRoot.append(node);}
  for(const [data,values] of [["direction",["czToFr","frToCz"]],["label",["fr","cz"]],["practice",["words","sentences"]],["galleryMode",["learn","listen"]]])for(const value of values){const button=new Element("button",doc);button.dataset[data]=value;appRoot.append(button);}
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
  const ctx=vm.createContext({document:doc,window:win,URL,URLSearchParams,TextEncoder,Audio:AudioFixture,console,fetch:async url=>{if(url.includes("sentence-pictures.json")){if(pictureManifest===null)throw Error("optional unavailable");return {ok:true,json:async()=>pictureDeferred?await pictureDeferred:pictureManifest};}if(url.includes("-quiz.json")){if(failQuiz)throw Error("quiz unavailable");return {ok:true,json:async()=>quizManifest};}if(slowAudio && url.includes("audio"))return new Promise(()=>{});if(failData && !url.includes("audio"))throw Error("offline");const selected=url.includes("sentence-audio")?sentenceManifest:manifest;if(selected===null && url.includes("audio"))throw Error("audio unavailable");return {ok:true,json:async()=>url.includes("audio")?selected:data};}});
  vm.runInContext(fs.readFileSync(path.join(root,"vocabulary-fr/model.js"),"utf8"),ctx);
  for(const name of ['learners.js','learner-ui.js','practice.js'])vm.runInContext(fs.readFileSync(path.join(root,'vocabulary-fr',name),'utf8'),ctx);
  vm.runInContext(source.replace('void init();','globalThis.ready=init();')+'\nglobalThis.api={state,context,buildSelection,orderedSelection,openStudy,moveStudy,newRandomRound,returnToGallery,renderGallery,selectionChanged,applyRoute,speakPrompt,speakAnswer,stopAudioPlayback,setPracticeMode,playStudyChannel};',ctx);
  await ctx.ready;
  return {...ctx.api,doc,win,emit,advance,players,setAudioReject:value=>{rejectPlayback=value;},session,local,historyEntries,element:id=>doc.getElementById(id),directions:doc.querySelectorAll("[data-direction]"),labels:doc.querySelectorAll("[data-label]"),practices:doc.querySelectorAll("[data-practice]"),galleryModes:doc.querySelectorAll("[data-gallery-mode]")};
}

const flush=async()=>{for(let n=0;n<12;n++)await Promise.resolve();};
async function until(check){for(let n=0;n<100;n++){if(check())return;await new Promise(r=>setTimeout(r,5));}throw Error('Timed out');}
function change(view,id,value){const node=view.element(id);if(typeof value==='boolean')node.checked=value;else node.value=value;node.emit('change');}
function active(view){return view.players.find(p=>!p.paused);}
function ended(view){const player=active(view);assert.ok(player);player.ended=true;player.paused=true;player.handlers.ended?.();}
function loop(view,mode='sentence-word'){change(view,'studyLoopMode',mode);view.element('studyLoopToggle').click();}
async function phase(view){ended(view);await flush();view.advance(2000);await flush();}
function clone(value){return structuredClone(value);}
module.exports={assert,fixture,vocabulary,audio,sentenceAudio,quizCatalog,pictures,model,learners,practice,app,flush,until,change,active,ended,loop,phase,clone,storage};
