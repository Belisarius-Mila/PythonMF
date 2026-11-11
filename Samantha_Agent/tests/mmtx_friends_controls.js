"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "../../docs");
class Element {
  constructor(tag = "div") { this.tagName = tag; this.children = []; this.dataset = {}; this.events = {}; this.attributes = {}; this.style = {setProperty(){}}; this.hidden = false; this.disabled = false; this.textContent = ""; this.className = ""; this.classes = new Set(); this.classList = {add:(...x)=>x.forEach(v=>this.classes.add(v)),remove:(...x)=>x.forEach(v=>this.classes.delete(v)),toggle:(x,on)=>on ? this.classes.add(x) : this.classes.delete(x),contains:x=>this.classes.has(x)}; }
  set innerHTML(_) { this.children = []; } get innerHTML() { return ""; }
  setAttribute(k,v) { this.attributes[k] = v; } getAttribute(k) { return this.attributes[k]; }
  appendChild(child) { this.children.push(child); return child; } append(...children) { this.children.push(...children); }
  addEventListener(k,fn) { (this.events[k] ||= []).push(fn); }
  querySelectorAll(selector) { return this.children.flatMap(child => [...((selector === "button" && child.tagName === "button") || (selector === ".clearing-dictionary-item" && child.className.includes("clearing-dictionary-item")) ? [child] : []), ...child.querySelectorAll(selector)]); }
  click() { if (!this.disabled) for (const fn of this.events.click || []) fn({target:this,stopPropagation(){}}); }
  getBoundingClientRect() { return {width:1000,height:550,left:0,top:0}; }
}
function environment(storageThrows = false) {
  const elements = new Map(); const audio = []; const utterances = []; const timers = [];
  const node = id => { if (!elements.has(id)) elements.set(id,new Element()); return elements.get(id); };
  class Audio {
    constructor(src) { this.src = src; this.paused = false; audio.push(this); }
    play() { return Promise.resolve(); } pause() { this.paused = true; }
  }
  const synth = {getVoices:()=>[{lang:"en-US",name:"English"},{lang:"cs-CZ",name:"Czech"}],speak:u=>utterances.push(u),cancel(){},addEventListener(){}};
  const window = {Audio,SpeechSynthesisUtterance:class {constructor(text){this.text=text;}},speechSynthesis:synth,localStorage:{getItem(){if(storageThrows)throw Error("blocked");return null;},setItem(){if(storageThrows)throw Error("blocked");}},setTimeout:fn=>{timers.push(fn);return timers.length;},clearTimeout(){},setInterval(){},clearInterval(){},addEventListener(){},location:{search:"?scene=intro4"}};
  const document = {getElementById:node,createElement:tag=>new Element(tag),body:new Element()};
  const context = vm.createContext({window,document,Audio,SpeechSynthesisUtterance:window.SpeechSynthesisUtterance,URLSearchParams,console,fetch:async()=>({ok:true}),setTimeout:window.setTimeout,clearTimeout(){}});
  vm.runInContext(fs.readFileSync(path.join(root,"friends_player.js"),"utf8"),context);
  return {window,context,node,audio,utterances,timers};
}
async function flush() { for(let n=0;n<16;n++) await Promise.resolve(); }
function makePlayer(env) { const names={panel:"panel",language:"language",repeat:"repeat",next:"next",speaker:"speaker",text:"text",czech:"czech",count:"count",status:"status"};const nodes=Object.fromEntries(Object.entries(names).map(([k,v])=>[k,env.node(v)]));const p=new env.window.MMTXFriendsPlayer(nodes);p.setActive(true);return p; }
async function engine() {
  const e=environment();const p=makePlayer(e);const line={speaker:"Benji",textEn:"Hello.",textCz:"Ahoj.",audioEn:"en.mp3",audioCz:"cs.mp3"};
  let done=false;p.present(line).then(v=>done=v);assert.equal(e.audio.length,1);assert.equal(e.node("next").disabled,true);assert.equal(e.node("czech").hidden,true);
  e.audio.at(-1).onended();await flush();assert.equal(e.audio.length,1);assert.equal(done,false);assert.equal(e.node("next").disabled,false);e.node("next").click();await flush();assert.equal(done,true);
  p.present(line);p.changeMode();assert.equal(e.node("czech").textContent,"Ahoj.");assert.equal(e.audio.length,2);p.changeMode();e.audio.at(-1).onended();await flush();assert.equal(e.audio.at(-1).src,"cs.mp3");assert.equal(e.node("next").disabled,true);
  const stale=e.audio.at(-1).onended;const cancelled=e.audio.at(-1);p.changeMode();assert.equal(cancelled.paused,true);assert.equal(e.node("next").disabled,false);
  p.present({...line,textEn:"New line."});stale();await flush();assert.equal(p.busy,true);assert.equal(e.node("text").textContent,"New line.");e.audio.at(-1).onerror();await flush();assert.equal(p.failed,"en");p.changeMode();p.changeMode();assert.equal(p.failed,"en");assert.equal(e.node("next").disabled,true);
  e.node("repeat").click();e.audio.at(-1).onended();await flush();assert.equal(e.audio.at(-1).src,"cs.mp3");e.audio.at(-1).onerror();await flush();assert.equal(p.failed,"cs");p.changeMode();assert.equal(p.failed,"");assert.equal(e.node("next").disabled,false);
  let stopped; p.present(line).then(v=>stopped=v);const old=e.audio.at(-1).onended;p.stop();old();await flush();assert.equal(stopped,false);assert.equal(p.line,null);
  p.mode=2;const spoken=p.speak({textEn:"yellow",textCz:"žlutá"});assert.equal(p.locked,true);e.utterances.at(-1).onend();await flush();assert.equal(e.utterances.at(-1).lang,"cs-CZ");e.utterances.at(-1).onend();await spoken;assert.equal(p.locked,false);assert.equal(e.node("next").hidden,true);
  let action=0;p.setAction("Next picture ▶",()=>action++);e.node("next").click();e.node("next").click();assert.equal(action,1);
  const blocked=environment(true);const b=makePlayer(blocked);assert.equal(b.mode,0);b.changeMode();assert.equal(b.mode,1);
}
async function integration() {
  const e=environment();const c=e.context;const run=code=>vm.runInContext(code,c);
  for(const name of ["scene01_audio_manifest.js","forest_school_audio_manifest.js"])run(fs.readFileSync(path.join(root,name),"utf8"));
  const source=fs.readFileSync(path.join(root,"script_intro_v2.js"),"utf8");run(source.slice(0,source.indexOf("const requestedScene =")));
  const clips=run("[...benjiBunnyDialogue,...friendsOwlIntro,...friendsHouseIntro,...owlGardenOutroDialogue].flatMap(line=>[line.audioEn,line.audioCz]).filter(Boolean)");
  for(const url of clips){const file=url.split("?")[0];assert.ok(fs.existsSync(path.join(root,file)),file);assert.deepEqual(fs.readFileSync(path.join(root,file)),fs.readFileSync(path.join(root,"../MatysekANJ/web_mmtx",file)));}
  assert.equal(run("friendsBenjiCzech.length"),9);
  const n=e.node;const state=()=>run("state");
  async function endAudio(){assert.ok(e.audio.at(-1)?.onended,"audio callback");e.audio.at(-1).onended();await flush();}
  async function endSpeech(){assert.ok(e.utterances.at(-1)?.onend,"speech callback");e.utterances.at(-1).onend();await flush();}
  async function next(){assert.equal(n("friendsNext").disabled,false);n("friendsNext").click();await flush();}
  run('state.audioUnlocked=true; setScene("benjiBunny")');await flush();
  for(let i=0;i<9;i++){assert.equal(n("friendsText").textContent,run(`benjiBunnyDialogue[${i}].textEn`));assert.equal(n("friendsNext").disabled,true);await endAudio();await next();}
  assert.equal(state().currentScene,"benjiBunny");assert.equal(state().dialoguePhase,"practice");await next();assert.equal(state().currentScene,"owlGarden");
  for(let i=0;i<3;i++){await endSpeech();await next();}assert.equal(state().owlGardenPhase,"play");assert.equal(n("friendsNext").hidden,true);
  for(let i=0;i<3;i++){
    run(`state.owlGardenActiveId=owlGardenGroups[${i}].id;state.owlGardenCurrentNumbers[owlGardenGroups[${i}].id]=owlGardenGroups[${i}].correctCount;void confirmOwlGardenCurrentGroup()`);await flush();await endSpeech();
  }
  assert.equal(run("friendsPlayer.busy"),true);assert.equal(n("friendsRepeat").disabled,true);
  const voicesDuringEffect=e.utterances.length;
  n("friendsLanguage").click();n("friendsLanguage").click();n("friendsLanguage").click();
  assert.equal(e.utterances.length,voicesDuringEffect,"language toggle must not overlap the fanfare");
  await endAudio();assert.equal(state().owlGardenPhase,"review");await endSpeech();await next();assert.equal(n("friendsNext").textContent,"Next picture ▶");await next();assert.equal(state().owlGardenPhase,"outro");
  for(let i=0;i<2;i++){await endAudio();await next();}assert.equal(state().currentScene,"houseBunny");
  for(let i=0;i<2;i++){await endSpeech();await next();}
  while(e.timers.length)e.timers.shift()();await flush();assert.equal(state().houseBunnyPhase,"waiting");await endSpeech();
  run('state.houseBunnyTargetId="yellow";void handleHouseBunnySelection("red")');await flush();assert.equal(state().houseBunnyPhase,"retry");await endSpeech();assert.equal(state().houseBunnyPhase,"waiting");
  run('void handleHouseBunnySelection("yellow")');await flush();assert.equal(state().houseBunnyImageStep,1);await endSpeech();assert.equal(state().houseBunnyImageStep,1);await next();assert.equal(state().houseBunnyImageStep,2);
  e.timers.shift()();await flush();assert.equal(state().houseBunnyImageStep,3);
  run('setScene("intro4")');while(e.timers.length)e.timers.shift()();await flush();assert.equal(state().currentScene,"intro4");assert.equal(run("friendsPlayer.active"),false);
  run('setScene("benjiBunny")');const stale=e.audio.at(-1).onended;run('setScene("intro4")');stale();await flush();assert.equal(state().currentScene,"intro4");assert.equal(run("friendsPlayer.line"),null);
}
(async()=>{await engine();await integration();console.log("Friends controller modes, errors, cancellation, four chapters and game actions: OK");})().catch(error=>{console.error(error);process.exitCode=1;});
