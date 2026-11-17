'use strict';
const assert=require('node:assert/strict');
const {webcrypto}=require('node:crypto');
const {Client,startPolling}=require('../app/frontend/samantha_chat/app.js');
const base=process.argv[2];
function store(){const data=new Map();return {getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,String(v)),removeItem:k=>data.delete(k)};}
let loseSend=false,holdGet=false,releaseGet=null,sendCalls=0,offline=false;
async function fetcher(path,options={}){
  if(offline)throw new Error('synthetic network outage');
  const action=options.body?JSON.parse(options.body).action:null;
  if(action==='send')sendCalls++;
  const response=await fetch(base+path,{...options,headers:{...options.headers,...(options.method?{Origin:base}:{})}});
  if(action==='send'&&loseSend){loseSend=false;throw new Error('Lost HTTP reply after server acceptance');}
  if(!options.method&&holdGet){holdGet=false;await new Promise(resolve=>{releaseGet=resolve;});}
  return response;
}
function client(storage=store(),tabStorage=store()){
  return new Client({fetch:fetcher,storage,tabStorage,crypto:webcrypto,setTimer:()=>1,clearTimer:()=>{}});
}
(async()=>{
  const host=client(),phone=client();
  await host.setup('create','Mint');await host.pair();
  await phone.setup('join','iPhone',host.state.pair_code);
  assert.equal(phone.state.room_id,host.state.room_id);
  await host.librarySearch('recepty');await phone.refresh();
  assert.equal(phone.state.library.items.length,1);
  const recipe=phone.state.library.items[0].id;
  await phone.libraryOpen(recipe);await host.refresh();
  assert.equal(host.state.library.selected_id,recipe);
  const detail=await host.libraryDetail(recipe);assert.match(detail.text,/Syntetický recept/);
  assert.equal(sendCalls,0,'library search/open/read must not send a question');
  await phone.claim();phone.setText('Otázka namluvená na telefonu');await phone.flush();
  await host.refresh();assert.equal(host.text,'Otázka namluvená na telefonu');assert.equal(host.state.draft.can_edit,false);
  // Continuous input must reach the real second HTTP client before dictation ends.
  phone.setTimer=(fn,ms)=>setTimeout(fn,ms);phone.clearTimer=id=>clearTimeout(id);
  const listeners={};const browser={setTimeout,clearTimeout,addEventListener:(name,fn)=>{listeners[name]=fn;}};
  const doc={hidden:false,addEventListener:()=>{}};
  let observedDuringInput=false,firstVisibleMs=null;const started=performance.now(),originalRender=host.render;
  host.render=c=>{if(c.text.startsWith('Průběžný diktát ')){observedDuringInput=true;if(firstVisibleMs===null)firstVisibleMs=Math.round(performance.now()-started);}originalRender(c);};
  const stop=startPolling(host,doc,browser);
  try{
    for(let n=0;n<12;n++){phone.setText('Průběžný diktát '+n);await new Promise(resolve=>setTimeout(resolve,80));}
    assert.equal(observedDuringInput,true,'Mint must receive text before continuous typing ends');
    await phone.flush();await host.refresh();assert.equal(host.text,'Průběžný diktát 11');
  }finally{stop();phone.clearTimer(phone.timer);phone.timer=null;phone.setTimer=()=>1;phone.clearTimer=()=>{};}
  console.log('Synthetic first visible dictation ms:',firstVisibleMs);
  await host.claim();host.setText('Otázka ručně opravená na Mintu');await host.flush();
  phone.setText('Opožděný telefonní diktát');await assert.rejects(phone.flush());
  assert.equal(phone.recovery.text,'Opožděný telefonní diktát');
  await host.refresh();assert.equal(host.text,'Otázka ručně opravená na Mintu');
  await host.send();assert.equal(host.state.messages.length,1);assert.equal(host.state.messages[0].answer,'Hotovo');
  await phone.refresh();assert.equal(phone.state.messages[0].user_text,'Otázka ručně opravená na Mintu');
  await host.claim();
  holdGet=true;const stale=host.refresh();
  for(let n=0;n<100&&!releaseGet;n++)await new Promise(resolve=>setTimeout(resolve,5));
  assert.ok(releaseGet,'held state reply must arrive');
  host.setText('Druhá aktuální otázka');await host.flush();releaseGet();await stale;
  assert.equal(host.text,'Druhá aktuální otázka','a late GET must not restore a superseded draft');
  loseSend=true;await assert.rejects(host.send());assert.ok(host.pending);
  const reload=client(host.storage,host.tabStorage);await reload.refresh();
  assert.equal(reload.pending,null);assert.equal(reload.state.messages.length,2);
  assert.equal(sendCalls,2,'reload must only GET, never resend a message');
  offline=true;await reload.refresh();assert.equal(reload.online,false);
  assert.equal(reload.state.messages.length,2,'offline must keep the visible history');
  offline=false;await reload.refresh();assert.equal(reload.online,true);assert.equal(sendCalls,2);
  const before=sendCalls;await reload.claim();reload.setText('Text při nedostupném úložišti');await reload.flush();
  const originalSet=reload.tabStorage.setItem;
  reload.tabStorage.setItem=(key,value)=>{if(key==='samantha-chat-pending')throw new Error('storage unavailable');return originalSet(key,value);};
  await assert.rejects(reload.send());assert.equal(reload.pending,null);
  await assert.rejects(reload.send());assert.equal(sendCalls,before,'every submission attempt must store its identity before network send');
  holdGet=true;releaseGet=null;const leaving=reload.refresh();
  for(let n=0;n<100&&!releaseGet;n++)await new Promise(resolve=>setTimeout(resolve,5));
  assert.ok(releaseGet);reload.disconnect();releaseGet();await leaving;
  assert.equal(reload.state,null,'a late GET must not reconnect a deliberately disconnected device');
  assert.equal(reload.token,'');
  console.log('PASS: paired iPhone/Mint, manual takeover, conflict preservation, stale GET, reconnect and lost send reply.');
})().catch(error=>{console.error(error);process.exitCode=1;});
