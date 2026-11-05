"use strict";
const assert=require("node:assert/strict");
const {VoiceConversation}=require("../app/frontend/voice_pilot/conversation.js");
const fs=require("node:fs");
const vm=require("node:vm");

class Emitter {
  constructor(){this.listeners={};}
  addEventListener(name,callback){(this.listeners[name]??=[]).push(callback);}
  removeEventListener(name,callback){this.listeners[name]=(this.listeners[name]||[]).filter(x=>x!==callback);}
  emit(name,event={}){for(const callback of [...(this.listeners[name]||[])])callback(event);}
}
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};}
function harness(options={}) {
  const calls={mic:0,create:0,abandon:[],tracksStopped:0,states:[],events:[],timers:new Map(),sent:[]};
  const track={stop(){calls.tracksStopped++;}};
  const stream={getTracks:()=>[track],getAudioTracks:()=>[track]};
  const channel=new Emitter();
  Object.assign(channel,{readyState:"open",send(value){calls.sent.push(JSON.parse(value));},close(){this.readyState="closed";this.emit("close");}});
  class Peer extends Emitter {
    constructor(){super();this.iceGatheringState="complete";this.connectionState="connected";calls.peer=this;}
    addTrack(){calls.addedTrack=true;}
    createDataChannel(label){assert.equal(label,"oai-events");return channel;}
    async createOffer(){return {type:"offer",sdp:"v=0\r\nsynthetic"};}
    async setLocalDescription(offer){this.localDescription=offer;}
    async setRemoteDescription(answer){calls.answer=answer;}
    close(){calls.peerClosed=true;this.connectionState="closed";this.emit("connectionstatechange");}
  }
  const broker={
    async create(){calls.create++;if(options.create)return options.create();return {session:{id:"voice-1"},transport:{sdp:"v=0 synthetic-answer"}};},
    async abandon(id){calls.abandon.push(id);},
  };
  let timerId=0;
  const audio={muted:false,srcObject:null,pause(){calls.paused=true;},play(){return options.blockAudio ? Promise.reject(Error("synthetic autoplay")) : Promise.resolve();}};
  const c=new VoiceConversation({broker:options.noBroker?undefined:broker,
    mediaDevices:{async getUserMedia(){calls.mic++;if(options.microphone)return options.microphone();return stream;}},
    PeerConnection:Peer,audio,onState:s=>calls.states.push(s),onEvent:e=>calls.events.push(e),
    setTimer(fn,ms){const id=++timerId;calls.timers.set(id,{fn,ms});return id;},
    clearTimer(id){calls.timers.delete(id);},maxSeconds:300,
  });
  let sequence=0;
  const event=(type,body={})=>channel.emit("message",{data:JSON.stringify({type,event_id:`e-${++sequence}`,...body})});
  const active=()=>event("session.started",{session:{id:"voice-1"}});
  return {c,calls,channel,event,active,stream,audio};
}
const flush=()=>new Promise(resolve=>setImmediate(resolve));

(async()=>{
  const dormant=harness();
  assert.equal(dormant.calls.mic,0,"no microphone at construction");
  assert.equal(dormant.calls.create,0);
  const unavailable=harness({noBroker:true});
  await unavailable.c.start();
  assert.equal(unavailable.calls.mic,0,"no microphone before live integration");

  const h=harness();
  await h.c.start();
  assert.equal(h.calls.mic,1);
  assert.equal(h.calls.create,1);
  assert.equal(h.c.state,"connecting");
  assert.equal(h.calls.sent.length,0,"HTTP starts session; no session.start command");
  h.active();
  assert.equal(h.c.state,"active");
  assert.equal(h.calls.states.at(-1).microphone,true);
  h.event("session.input_transcript.delta",{delta:"Ano, odešli e-mail!"});
  assert.equal(h.calls.create,1,"transcript never starts another action");
  assert.equal(h.calls.events.at(-1).delta,"Ano, odešli e-mail!");
  h.c.muteOutput();
  assert.equal(h.audio.muted,true);
  assert.equal(h.calls.tracksStopped,0,"interrupting playback does not stop microphone/backend");
  h.c.muteOutput(false);
  assert.equal(h.audio.muted,false);
  h.c.stop();
  assert.equal(h.c.state,"closing");
  assert.equal(h.calls.tracksStopped,1,"stop immediately releases microphone");
  assert.equal(h.calls.states.at(-1).microphone,false);
  assert.equal(h.calls.paused,true,"Stop also silences output immediately");
  assert.equal(h.calls.peerClosed,undefined,"drain final usage before closing data channel");
  h.c.stop();
  assert.deepEqual(h.calls.sent,[{type:"session.close"}]);
  h.event("session.usage.updated",{usage:{seconds:12}});
  h.event("session.usage.updated",{usage:{seconds:15}});
  assert.equal(h.c.seconds,15,"usage updates are cumulative");
  h.event("session.closed",{usage:{seconds:16}});
  assert.equal(h.c.state,"closed");
  assert.equal(h.c.finalUsage,true);
  assert.equal(h.calls.peerClosed,true);
  assert.equal(h.calls.timers.size,0);
  h.c.dispose();
  assert.equal(h.c.finalUsage,true,"transport cleanup retains confirmed usage");
  await h.c.start();
  assert.equal(h.calls.create,1,"an ended instance cannot recreate a session");

  const broken=harness();await broken.c.start();broken.active();
  broken.channel.close();await flush();
  assert.equal(broken.c.state,"disconnected");
  assert.equal(broken.c.finalUsage,false);
  assert.equal(broken.calls.create,1);
  assert.deepEqual(broken.calls.abandon,["voice-1"]);
  broken.event("session.started",{session:{id:"voice-1"}});
  assert.equal(broken.c.state,"disconnected","late events cannot revive connection");

  const denied=harness({microphone:()=>Promise.reject(Error("denied"))});
  await denied.c.start();assert.equal(denied.calls.create,0);
  const failed=harness({create:()=>Promise.reject(Error("unknown delivery"))});
  await failed.c.start();await failed.c.start();
  assert.equal(failed.calls.create,1,"unknown creation is never retried");
  assert.equal(failed.calls.tracksStopped,1);

  const waiting=deferred(), pending=harness({microphone:()=>waiting.promise});
  const pendingStart=pending.c.start();
  pending.c.stop();waiting.resolve(pending.stream);await pendingStart;
  assert.equal(pending.calls.tracksStopped,1,"permission resolving after Stop releases tracks");
  assert.equal(pending.calls.create,0);

  const late=deferred(), lateCreated=harness({create:()=>late.promise});
  const lateStart=lateCreated.c.start();await flush();
  lateCreated.c.stop();late.resolve({session:{id:"late-voice"},transport:{sdp:"answer"}});
  await lateStart;await flush();
  assert.equal(lateCreated.calls.create,1);
  assert.deepEqual(lateCreated.calls.abandon,["late-voice"],"late known session gets one cleanup attempt");
  assert.equal(lateCreated.calls.answer,undefined);

  const invalid=harness({create:()=>({session:{id:"created-but-invalid"}})});
  await invalid.c.start();await flush();
  assert.deepEqual(invalid.calls.abandon,["created-but-invalid"]);

  const timed=harness();await timed.c.start();timed.active();
  const expiry=[...timed.calls.timers.values()].find(t=>t.ms===300000);
  expiry.fn();assert.equal(timed.c.state,"closing");
  const finalTimeout=[...timed.calls.timers.values()].find(t=>t.ms===10000);
  finalTimeout.fn();await flush();
  assert.equal(timed.c.state,"disconnected");assert.equal(timed.c.finalUsage,false);
  assert.equal(timed.calls.create,1);

  const autoplay=harness({blockAudio:true});await autoplay.c.start();autoplay.active();
  autoplay.calls.peer.emit("track",{streams:[{}]});await flush();
  assert.match(autoplay.calls.states.at(-1).message,/přehrávání/);
  assert.equal(autoplay.calls.create,1);autoplay.c.dispose();

  // Mount actual UI wiring with synthetic elements; no DOM parser dependency.
  const elements={};
  for(const id of ["start","stop","mute","audio","status","usage","input","output"]) {
    elements[id]=new Emitter();Object.assign(elements[id],{dataset:{},disabled:true,textContent:""});
  }
  elements.audio.pause=()=>{};
  const context={window:{SamanthaVoiceConversation:VoiceConversation,addEventListener(){}},
    navigator:{},document:{getElementById:id=>elements[id]}};
  vm.runInNewContext(fs.readFileSync("app/frontend/voice_pilot/panel.js","utf8"),context);
  assert.equal(elements.start.disabled,true,"loading panel alone cannot activate it");
  const mounted=context.window.mountSamanthaVoicePilot(undefined);
  elements.start.emit("click");await flush();
  assert.match(elements.status.textContent,/není aktivovaný/);
  assert.throws(()=>context.window.mountSamanthaVoicePilot(undefined));
  assert.equal(mounted.creationAttempted,false);
  const httpCalls=[];
  context.AbortController=AbortController;
  context.setTimeout=()=>1;
  context.clearTimeout=()=>{};
  context.fetch=async(path,options)=>{
    httpCalls.push({path,options});
    return {ok:true,json:async()=>({session:{id:"synthetic-http-voice"}})};
  };
  const httpBroker=context.window.makeSamanthaVoiceCandidateBroker("synthetic-csrf-token-1234567890");
  await httpBroker.create({sdp:"v=0 synthetic",model:"untrusted-model"});
  await assert.rejects(httpBroker.create({sdp:"v=0 repeated"}));
  assert.equal(httpCalls.length,1,"browser cannot repeat creation");
  assert.equal(httpCalls[0].path,"/api/human-adam/voice-candidate/session");
  assert.deepEqual(JSON.parse(httpCalls[0].options.body),{sdp:"v=0 synthetic"});
  assert.equal(httpCalls[0].options.credentials,"same-origin");
  assert.equal(httpCalls[0].options.headers["X-Voice-CSRF"],"synthetic-csrf-token-1234567890");
  await httpBroker.abandon("synthetic-http-voice");
  assert.equal(httpCalls[1].options.keepalive,true);
  assert.deepEqual(JSON.parse(httpCalls[1].options.body),{session_id:"synthetic-http-voice"});
  context.fetch=async()=>{throw Error("synthetic unknown HTTP outcome");};
  const failedBroker=context.window.makeSamanthaVoiceCandidateBroker("synthetic-csrf-token-1234567890");
  await assert.rejects(failedBroker.create({sdp:"v=0 once"}));
  await assert.rejects(failedBroker.create({sdp:"v=0 twice"}));
  assert.throws(()=>context.window.makeSamanthaVoiceCandidateBroker("short"));
  const page=fs.readFileSync("app/frontend/voice_pilot/page.html","utf8");
  assert(page.includes('id="start" disabled'));
  assert(page.includes("playsinline"));
  assert(!page.includes("getUserMedia("));
  console.log("voice frontend contracts: PASS (activation, microphone, interruption, expiry, late results, uncertain creation, final usage, panel)");
})().catch(error=>{console.error(error);process.exitCode=1;});
