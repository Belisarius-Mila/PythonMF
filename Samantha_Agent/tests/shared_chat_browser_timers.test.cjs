'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const {webcrypto}=require('node:crypto');
const source=fs.readFileSync(require('node:path').join(__dirname,'../app/frontend/samantha_chat/app.js'),'utf8');
function storage(){const values=new Map();return {getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,String(v)),removeItem:k=>values.delete(k)};}
const callbacks=new Map();let sequence=0;
const window={
 setTimeout:function(callback,delay){assert.equal(this,window,'browser setTimeout requires the Window receiver');const id=++sequence;callbacks.set(id,{callback,delay});return id;},
 clearTimeout:function(id){assert.equal(this,window,'browser clearTimeout requires the Window receiver');callbacks.delete(id);}
};
const context={window,module:{exports:{}},setTimeout:window.setTimeout,clearTimeout:window.clearTimeout,Uint8Array,AbortController,console};
vm.runInNewContext(source,context);
const client=new context.module.exports.Client({fetch:async()=>{throw Error('Unexpected network');},storage:storage(),tabStorage:storage(),crypto:webcrypto});
client.state={room_id:'synthetic-room',draft:{can_edit:true,text:'',revision:1}};
client.setText('Synthetic browser draft');
assert.equal(client.dirty,true);assert.equal(client.text,'Synthetic browser draft');
assert.equal(callbacks.get(client.timer).delay,150);
assert.equal(JSON.parse(client.tabStorage.getItem('samantha-chat-draft')).text,'Synthetic browser draft');
client.setText('Updated draft');assert.equal(callbacks.size,1,'typing coalesces without postponing transfer');
client.disconnect();assert.equal(callbacks.size,0,'disconnect cancels the native timer');
console.log('PASS: native browser timer receiver, debounce replacement, local recovery and disconnect.');

// Exercise automatic typing -> debounce -> HTTP save, not just a manual flush.
(async()=>{
 const timers=new Map();let number=0,saves=0;
 const browser={
  setTimeout:function(fn,delay){assert.ok(this===browser||this===undefined,'invalid native setTimeout receiver');const id=++number;timers.set(id,{fn,delay});return id;},
  clearTimeout:function(id){assert.ok(this===browser||this===undefined,'invalid native clearTimeout receiver');timers.delete(id);}
 };
 const realm={window:browser,module:{exports:{}},setTimeout:browser.setTimeout,clearTimeout:browser.clearTimeout,Uint8Array,AbortController};vm.runInNewContext(source,realm);
 const automatic=new realm.module.exports.Client({storage:storage(),tabStorage:storage(),crypto:webcrypto,fetch:async(_path,options)=>{
  const body=JSON.parse(options.body);assert.equal(body.action,'draft','typing must never send a model message');saves++;
  return {ok:true,json:async()=>({ok:true,room_id:'automatic-room',draft:{can_edit:true,text:body.text,revision:body.expected_revision+1},messages:[]})};
 }});
 automatic.state={room_id:'automatic-room',draft:{can_edit:true,text:'',revision:1}};
 automatic.setText('Automatically shared synthetic text');
 timers.get(automatic.timer).fn();await new Promise(resolve=>setImmediate(resolve));await automatic.chain;
 assert.equal(saves,1);assert.equal(automatic.dirty,false);assert.equal(automatic.state.draft.text,'Automatically shared synthetic text');assert.equal(timers.size,0);
 console.log('PASS: browser-native debounce automatically saves one draft without submitting a question.');
})().catch(error=>{console.error(error);process.exitCode=1;});
