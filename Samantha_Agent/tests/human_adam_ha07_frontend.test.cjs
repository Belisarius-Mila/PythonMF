const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const html=JSON.parse(fs.readFileSync(0,'utf8'));
const start=html.indexOf('function createHumanAdamInterrupt('),end=html.indexOf('  async function sendOwnedWork()',start);
assert(start>0&&end>start);const ctx=vm.createContext({AbortController,structuredClone,console});vm.runInContext(html.slice(start,end),ctx);
const identity='a'.repeat(32),protocol={interrupt_protocol:1,interrupt_path:'/api/human-adam/work/interrupt'};
const base={enabled:true,error:'',operation:{operation_id:identity,turn_id:'turn-current',lifecycle_state:'running',delivery_state:'pending',
 capabilities:{interrupt:true},scope:{workstream_id:'project-current',thread_id:'thread-current',connection_generation:3}}};
const view=()=>structuredClone(base);
function harness(values=new Map()){
 let drafts={composer:'Další rozepsaný pokyn',append:'Neodeslané upřesnění'},post=null,refreshes=0;
 const posts=[],timers=new Map();let count=0;
 const receipt=(state='accepted',outcome='waiting')=>({command_id:'ha07-'+identity,expected_turn_id:'turn-current',state,outcome});
 const envelope=()=>({ok:true,operations:[{...view().operation,interrupt:receipt()}]});
 const host={setTimeout(fn){timers.set(++count,fn);return count;},clearTimeout:id=>timers.delete(id),
  storage:{getItem:k=>values.get(k),setItem:(k,v)=>values.set(k,v)},getDrafts:()=>structuredClone(drafts),
  restoreDrafts:value=>{if(!drafts.composer)drafts.composer=value.composer;if(!drafts.append)drafts.append=value.append;},
  post:async(body,signal)=>{posts.push({body,signal});return post?post(body,signal):envelope();},
  refresh:()=>refreshes++,onChange:()=>{}};
 const form=ctx.createHumanAdamInterrupt(host);
 return {form,posts,host,values,receipt,envelope,setPost:fn=>post=fn,getDrafts:()=>drafts,setDrafts:v=>drafts=v,getRefreshes:()=>refreshes,timers};
}
let passed=0;async function test(name,fn){await fn();console.log('PASS '+name);passed++;}
(async()=>{
 await test('one exact POST and ACK stays distinct from interruption',async()=>{
  const h=harness();h.form.configure(protocol,view());assert(h.form.snapshot().canStop);await h.form.submit();await h.form.submit();
  assert.equal(h.posts.length,1);assert.equal(h.form.snapshot().receipt.outcome,'waiting');assert.equal(h.getRefreshes(),1);
  assert.deepEqual(JSON.parse(JSON.stringify(h.posts[0].body)),{workstream_id:'project-current',operation_id:identity,
   command_id:'ha07-'+identity,expectedTurnId:'turn-current',confirmed:true});
 });
 await test('double click, pause and lost reply never resend',async()=>{
  const h=harness();let reject;h.setPost(()=>new Promise((_,r)=>reject=r));h.form.configure(protocol,view());const pending=h.form.submit();
  await h.form.submit();assert.equal(h.posts.length,1);h.form.pause();reject(Error('lost'));await pending;
  await h.form.submit();assert.equal(h.posts.length,1);assert.equal(h.getDrafts().append,'Neodeslané upřesnění');
 });
 await test('reload recovers only the original reference and both unsent drafts',async()=>{
  const h=harness();h.setPost(()=>{throw Error('lost');});h.form.configure(protocol,view());await h.form.submit();
  const reloaded=harness(h.values);reloaded.setDrafts({composer:'',append:''});reloaded.form.configure(protocol,view());
  assert(reloaded.form.snapshot().requested);assert.equal(reloaded.getDrafts().composer,'Další rozepsaný pokyn');
  assert.equal(reloaded.getDrafts().append,'Neodeslané upřesnění');await reloaded.form.submit();assert.equal(reloaded.posts.length,0);
 });
 await test('late reply cannot retarget another workstream',async()=>{
  const h=harness();let resolve;h.setPost(()=>new Promise(r=>resolve=r));h.form.configure(protocol,view());const pending=h.form.submit();
  const other=view();other.operation.scope.workstream_id='project-other';other.operation.operation_id='b'.repeat(32);
  h.form.configure(protocol,other);resolve(h.envelope());await pending;assert.equal(h.form.snapshot().receipt,null);
 });
 await test('terminal interruption and completion race remain distinct',async()=>{
  for(const state of ['interrupted','completed']){
   const h=harness(),v=view();v.operation.lifecycle_state=state;v.operation.delivery_state='confirmed';v.operation.capabilities.interrupt=false;
   v.operation.interrupt=h.receipt('accepted',state);h.form.configure(protocol,v);assert.equal(h.form.snapshot().receipt.outcome,state);
   assert.equal(h.form.snapshot().canStop,false);await h.form.submit();assert.equal(h.posts.length,0);
  }
 });
 await test('a claimed stop without matching parent proof fails closed',async()=>{
  const h=harness(),v=view();v.operation.interrupt=h.receipt('accepted','interrupted');h.form.configure(protocol,v);
  assert(h.form.snapshot().error);assert.equal(h.form.snapshot().canStop,false);
 });
 await test('unsupported protocol and unavailable capability cannot dispatch',async()=>{
  for(const disabled of [null,{...protocol,interrupt_path:'https://foreign.example'}]){
   const h=harness();h.form.configure(disabled,view());await h.form.submit();assert.equal(h.posts.length,0);
  }
  const h=harness(),v=view();v.operation.capabilities.interrupt=false;h.form.configure(protocol,v);await h.form.submit();assert.equal(h.posts.length,0);
 });
 await test('read outcome changes UI without a second POST or draft loss',async()=>{
  const h=harness();h.form.configure(protocol,view());await h.form.submit();const v=view();
  v.operation.lifecycle_state='interrupted';v.operation.delivery_state='confirmed';v.operation.interrupt=h.receipt('accepted','interrupted');
  h.form.configure(protocol,v);assert.equal(h.form.snapshot().receipt.outcome,'interrupted');assert.equal(h.posts.length,1);
  assert.equal(h.getDrafts().composer,'Další rozepsaný pokyn');assert.equal(h.getDrafts().append,'Neodeslané upřesnění');
 });
 console.log(`${passed} HA07 frontend scenarios passed`);
})().catch(error=>{console.error(error);process.exitCode=1;});
