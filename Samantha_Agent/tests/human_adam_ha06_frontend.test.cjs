const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const html=JSON.parse(fs.readFileSync(0,'utf8'));
const a=html.indexOf('function createHumanAdamSteer('),b=html.indexOf('  async function sendOwnedWork()',a);
assert(a>0&&b>a);
const context=vm.createContext({AbortController,structuredClone,console});vm.runInContext(html.slice(a,b),context);
const base=Date.parse('2026-11-12T12:00:00Z'),identity='a'.repeat(32);
const protocol={command_protocol:1,steer_path:'/api/human-adam/work/steer',command_read_path:'/api/human-adam/work/command'};
const operation={operation_id:identity,turn_id:'turn-current',lifecycle_state:'running',capabilities:{steer:true},
 scope:{workstream_id:'project-current',thread_id:'thread-current',connection_generation:3}};
const view=()=>({enabled:true,error:'',operation:structuredClone(operation)});
const flush=async()=>{for(let n=0;n<15;n++)await Promise.resolve();};
function harness(){
 let time=base,timerId=0,commandIndex=0,lastBody=null,postMode='accepted',reader=null;
 const timers=new Map(),values=new Map(),posts=[],reads=[],changes=[];
 const envelope=(state='accepted',body=lastBody,revision=1)=>({ok:true,schema_version:1,read_only:true,writes_performed:false,
  workstream_id:body.workstream_id,operation_id:body.operation_id,command_revision:revision,command:{command_id:body.command_id,
   expected_turn_id:body.expectedTurnId,state,reason:'',updated_at:new Date(time).toISOString(),created_at:new Date(base).toISOString(),
   text:body.text,accepted_into_turn:state==='accepted',permission_scope:'original_turn'}});
 const host={
  setTimeout(fn,delay){const id=++timerId;timers.set(id,{fn,at:time+delay});return id;},clearTimeout:id=>timers.delete(id),
  storage:{getItem:key=>values.get(key),setItem:(key,value)=>values.set(key,value)},
  newCommandId:operationId=>`ha06-${operationId}-${(++commandIndex).toString(16).padStart(32,'0')}`,
  onChange:value=>changes.push(structuredClone(value)),
  post:async(body,signal)=>{posts.push({body,signal});lastBody=structuredClone(body);
   if(typeof postMode==='function')return postMode(body,signal);if(postMode==='loss')throw Error('PRIVATE_HTTP_ERROR');return envelope(postMode);},
  read:async(query,signal)=>{reads.push({query,signal});return reader?reader(query,signal):envelope();},
 };
 const form=context.createHumanAdamSteer(host);
 return {form,host,posts,reads,changes,values,envelope,timers,
  setPost:value=>{postMode=value;},setRead:value=>{reader=value;},
  async advance(ms=0){const end=time+ms;let count=0;while(true){const next=[...timers].filter(([,v])=>v.at<=end).sort((x,y)=>x[1].at-y[1].at)[0];if(!next)break;
    assert(++count<1000,'timer runaway');time=next[1].at;timers.delete(next[0]);next[1].fn();await flush();}time=end;await flush();},
 };
}
let passed=0;async function test(name,fn){await fn();passed++;console.log('PASS '+name);}
(async()=>{
 await test('ten explicit appends target same turn and never a new task',async()=>{
  const h=harness();h.form.configure(protocol,view());for(let n=0;n<10;n++){h.form.setDraft('Upřesnění '+n);assert.equal(await h.form.submit(),true);}
  assert.equal(h.posts.length,10);assert.equal(new Set(h.posts.map(c=>c.body.command_id)).size,10);
  for(const {body}of h.posts){assert.equal(body.operation_id,identity);assert.equal(body.expectedTurnId,'turn-current');assert.equal(body.confirmed,true);
   assert.deepEqual(Object.keys(body).sort(),['command_id','confirmed','expectedTurnId','operation_id','text','workstream_id'].sort());}
  assert.equal(h.form.snapshot().draft,'');
 });
 await test('unknown acknowledgement is read by same identity without POST replay',async()=>{
  const h=harness();h.form.configure(protocol,view());h.form.setDraft('Původní doplnění');h.setPost('loss');await h.form.submit();
  assert(h.form.snapshot().unresolved);assert.equal(h.form.snapshot().draft,'Původní doplnění');
  await h.form.submit();assert.equal(h.posts.length,1);await h.advance();assert.equal(h.reads.length,1);
  assert.equal(h.reads[0].query.command_id,h.posts[0].body.command_id);assert.equal(h.form.snapshot().receipt.state,'accepted');
 });
 await test('rejection and end-of-turn preserve unsent text',async()=>{
  const h=harness();h.form.configure(protocol,view());h.form.setDraft('Zachovat');h.setPost('rejected');assert.equal(await h.form.submit(),false);
  assert.equal(h.form.snapshot().draft,'Zachovat');const ended=view();ended.operation.lifecycle_state='completed';ended.operation.capabilities.steer=false;
  h.form.configure(protocol,ended);await h.form.submit();assert.equal(h.posts.length,1);assert.equal(h.form.snapshot().draft,'Zachovat');
 });
 await test('terminal race during POST never forwards text into a new turn',async()=>{
  const h=harness();let resolve;h.setPost(()=>new Promise(r=>resolve=r));h.form.configure(protocol,view());h.form.setDraft('Racing draft');
  const sending=h.form.submit();await flush();const ended=view();ended.operation.lifecycle_state='completed';h.form.configure(protocol,ended);
  resolve(h.envelope('rejected'));await sending;assert.equal(h.form.snapshot().draft,'Racing draft');assert.equal(h.posts.length,1);assert.equal(h.form.snapshot().canSubmit,false);
 });
 await test('draft changed during accepted POST is retained',async()=>{
  const h=harness();let resolve;h.setPost(()=>new Promise(r=>resolve=r));h.form.configure(protocol,view());h.form.setDraft('First');const sending=h.form.submit();
  h.form.setDraft('Next unsent text');resolve(h.envelope());await sending;assert.equal(h.form.snapshot().draft,'Next unsent text');
 });
 await test('late read of previous command cannot poison a new accepted command',async()=>{
  const h=harness();h.form.configure(protocol,view());h.form.setDraft('First');await h.form.submit();
  const old=h.envelope();let resolve;h.setRead(()=>new Promise(r=>resolve=r));h.form.verify();await h.advance();
  h.form.setDraft('Second');await h.form.submit();const current=h.form.snapshot().receipt.command_id;
  resolve(old);await flush();assert.equal(h.form.snapshot().receipt.command_id,current);assert.equal(h.form.snapshot().error,'');assert.equal(h.posts.length,2);
 });
 await test('double click and pause/resume perform no second POST',async()=>{
  const h=harness();let resolve;h.setPost(()=>new Promise(r=>resolve=r));h.form.configure(protocol,view());h.form.setDraft('Only once');const sending=h.form.submit();
  await h.form.submit();assert.equal(h.posts.length,1);h.form.pause();h.form.resume();resolve(h.envelope());await sending;await h.advance();
  assert.equal(h.posts.length,1);assert.equal(h.form.snapshot().receipt.state,'accepted');
 });
 await test('new project rejects late response and does not silently retarget old draft',async()=>{
  const h=harness();let resolve;h.setPost(()=>new Promise(r=>resolve=r));h.form.configure(protocol,view());h.form.setDraft('Old project text');const sending=h.form.submit();
  const other=view();other.operation.scope.workstream_id='project-other';other.operation.operation_id='b'.repeat(32);h.form.configure(protocol,other);
  resolve(h.envelope());await sending;assert.equal(h.form.snapshot().receipt,null);assert(h.form.snapshot().detachedDraft);assert.equal(h.form.snapshot().canSubmit,false);
  assert.equal(h.form.snapshot().draft,'Old project text');await h.form.submit();assert.equal(h.posts.length,1);
 });
 await test('unavailable capability or protocol cannot append',async()=>{
  for(const disabled of [null,{...protocol,steer_path:'https://foreign.example'}]){const h=harness();h.form.configure(disabled,view());h.form.setDraft('Text');await h.form.submit();assert.equal(h.posts.length,0);}
  const h=harness(),v=view();v.operation.capabilities.steer=false;h.form.configure(protocol,v);h.form.setDraft('Text');await h.form.submit();assert.equal(h.posts.length,0);
 });
 await test('accepted and unverified work is not mislabelled as a finished turn',async()=>{
  for(const [state,finished]of [['accepted',false],['unverified',false],['awaiting_completion',true],['completed',true]]){
   const h=harness(),v=view();v.operation.lifecycle_state=state;v.operation.capabilities.steer=false;h.form.configure(protocol,v);h.form.setDraft('Keep');
   assert.equal(h.form.snapshot().finished,finished);assert.equal(h.form.snapshot().canSubmit,false);await h.form.submit();assert.equal(h.posts.length,0);
  }
 });
 await test('reload remembers only reference and restores rejected command text through GET',async()=>{
  const first=harness();first.form.configure(protocol,view());first.form.setDraft('Private user command');first.setPost('loss');await first.form.submit();
  const second=harness();for(const [key,value]of first.values)second.values.set(key,value);const body=first.posts[0].body;
  assert(![...second.values.values()].join('').includes('Private user command'));
  second.setRead(()=>second.envelope('rejected',body));second.form.configure(protocol,view());await second.advance();
  assert.equal(second.posts.length,0);assert.equal(second.form.snapshot().draft,'Private user command');assert.equal(second.form.snapshot().receipt.state,'rejected');
 });
 await test('foreign identity or changed permission scope is not confirmation',async()=>{
  for(const change of [p=>p.operation_id='b'.repeat(32),p=>p.command.expected_turn_id='other',p=>p.command.permission_scope='broader']){
   const h=harness();h.form.configure(protocol,view());h.form.setDraft('Retain');h.setPost(()=>{const p=h.envelope();change(p);return p;});
   h.setRead(()=>{const p=h.envelope();change(p);return p;});await h.form.submit();await h.advance();
   assert.equal(h.form.snapshot().receipt,null);assert.equal(h.form.snapshot().draft,'Retain');assert(h.form.snapshot().error);assert.equal(h.posts.length,1);
  }
 });
 await test('explicit unverified receipt stops automatic reads and blocks retransmission',async()=>{
  const h=harness();h.form.configure(protocol,view());h.form.setDraft('Unknown');h.setPost('unverified');await h.form.submit();await h.advance(30000);
  assert.equal(h.reads.length,0);assert(h.form.snapshot().unresolved);await h.form.submit();assert.equal(h.posts.length,1);
  h.form.verify();await h.advance();assert.equal(h.reads.length,1);assert.equal(h.posts.length,1);
 });
 await test('missing receipt and read failures have bounded retries, never new POST',async()=>{
  const h=harness();h.form.configure(protocol,view());h.form.setDraft('Unknown');h.setPost('loss');h.setRead(()=>({ok:true,schema_version:1,operation_id:identity,workstream_id:'project-current',command:null}));
  await h.form.submit();await h.advance(100000);assert.equal(h.reads.length,8);assert.equal(h.posts.length,1);assert(h.form.snapshot().unresolved);
 });
 await test('POST deadline becomes readback only and preparation failure never clears text',async()=>{
  const h=harness();h.setPost((_body,signal)=>new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>reject(Error('aborted')))));
  h.form.configure(protocol,view());h.form.setDraft('Timeout');const sending=h.form.submit();await h.advance(10000);await sending;
  assert.equal(h.posts.length,1);assert.equal(h.reads.length,1);assert.equal(h.form.snapshot().receipt.state,'accepted');
  const broken=harness();broken.host.newCommandId=()=>{throw Error('unavailable');};broken.form.configure(protocol,view());broken.form.setDraft('Keep');await broken.form.submit();
  assert.equal(broken.posts.length,0);assert.equal(broken.form.snapshot().draft,'Keep');
 });
 console.log(`HA-06 append UI: ${passed} scenarios PASS`);
})().catch(error=>{console.error(error);process.exitCode=1;});
