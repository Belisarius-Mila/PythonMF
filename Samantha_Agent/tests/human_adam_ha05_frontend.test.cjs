const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const html = JSON.parse(fs.readFileSync(0, 'utf8'));
const start = html.indexOf('function createHumanAdamWorkMonitor(');
const end = html.indexOf('  async function sendOwnedWork()', start);
assert(start > 0 && end > start);
const context = vm.createContext({AbortController, structuredClone, console});
vm.runInContext(html.slice(start, end), context);
const create = context.createHumanAdamWorkMonitor;
const base = Date.parse('2026-11-12T12:00:00Z');
const scope = {workstream_id:'project-current',thread_id:'thread-current',connection_generation:3};
const protocol = {schema_version:1,server_owned:true,start_path:'/api/human-adam/work/start',read_path:'/api/human-adam/work',replays_on_restart:false};
const id = 'a'.repeat(32), client = 'human-adam-request-1';
function operation(changes={}) {
  return {schema_version:1,operation_id:id,client_request_id:client,scope:{...scope},thread_id:scope.thread_id,
    turn_id:'turn-current',revision:2,cursor:2,lifecycle_state:'running',delivery_state:'pending',
    created_at:new Date(base).toISOString(),updated_at:new Date(base+500).toISOString(),
    events:[{cursor:2,kind:'turn_started',at:new Date(base+500).toISOString()}],event_gap:false,resync_required:false,
    read_only:true,writes_performed:false,capabilities:{steer:false,interrupt:false,replay:false},...changes};
}
const frame = (op=operation(), changes={}) => ({ok:true,schema_version:1,server_generation:'server-1',
  read_only:true,writes_performed:false,operations:op?[op]:[],...changes});
const flush = async () => { for(let i=0;i<12;i++)await Promise.resolve(); };
function harness(initial=frame()) {
  let time=base, nextTimer=0, visible=true, response=initial;
  const timers=new Map(), values=new Map(), reads=[], changes=[], ends=[];
  const host={now:()=>time,visible:()=>visible,
    setTimeout(fn,delay){const id=++nextTimer;timers.set(id,{fn,at:time+delay});return id;},clearTimeout:id=>timers.delete(id),
    storage:{getItem:key=>values.get(key),setItem:(key,value)=>values.set(key,value)},
    onChange:value=>changes.push(structuredClone(value)),onTerminal:(value,flags)=>ends.push({value,flags}),
    read:async(query,signal)=>{reads.push({query,signal,at:time});return typeof response==='function'?response(query,signal):structuredClone(response);},
  };
  const monitor=create(host);
  return {host,monitor,reads,changes,ends,values,timers,
    setResponse(value){response=value;},setVisible(value){visible=value;},
    async advance(ms=0){const until=time+ms;let count=0;
      while(true){const due=[...timers].filter(([,v])=>v.at<=until).sort((a,b)=>a[1].at-b[1].at)[0];if(!due)break;
        assert(++count<1000,'unbounded timer loop');time=due[1].at;timers.delete(due[0]);due[1].fn();await flush();}
      time=until;await flush();},
  };
}
let passed=0;
async function test(name,fn){await fn();passed++;console.log(`PASS ${name}`);}
(async()=>{
  await test('no advertised API means no speculative polling',async()=>{
    const h=harness();h.monitor.configure(null,scope);await h.advance(5000);assert.equal(h.reads.length,0);assert.equal(h.monitor.snapshot().enabled,false);
  });
  await test('discovery then cursor polling within 2 seconds',async()=>{
    const h=harness();h.monitor.configure(protocol,scope);assert(h.monitor.snapshot().blocked);
    await h.advance();assert.equal(h.reads.length,1);assert.equal(h.reads[0].query.cursor,'0');
    h.setResponse(frame(operation({revision:3,cursor:3,events:[{cursor:3,kind:'tool_started',at:new Date(base+800).toISOString()}]})));
    await h.advance(750);assert.equal(h.reads.length,2);assert.equal(h.reads[1].query.cursor,'2');
    assert.equal(h.monitor.snapshot().operation.events.at(-1).kind,'tool_started');
    assert(h.reads[1].at-h.reads[0].at<2000);assert(h.monitor.snapshot().blocked);
  });
  await test('terminal state stops reads and notification happens once',async()=>{
    const h=harness(frame(null));h.monitor.configure(protocol,scope);await h.advance();h.monitor.expect(client);
    h.monitor.accepted(frame(operation(),{accepted:true,read_only:false,writes_performed:true}));
    h.setResponse(frame(operation({lifecycle_state:'completed',delivery_state:'confirmed',revision:4,cursor:4,events:[]})));
    await h.advance();const count=h.reads.length;await h.advance(60000);
    assert.equal(h.reads.length,count);assert.equal(h.ends.length,1);assert.equal(h.ends[0].flags.notify,true);
    h.monitor.configure(protocol,{...scope});await h.advance(5000);assert.equal(h.reads.length,count);
  });
  await test('reload resumes reference through GET without replay or terminal sound',async()=>{
    const first=harness(frame(null));first.monitor.configure(protocol,scope);await first.advance();first.monitor.expect(client);
    first.monitor.accepted(frame(operation()));first.setResponse(frame(operation()));await first.advance();
    const second=harness(frame(operation({lifecycle_state:'completed',delivery_state:'confirmed'})));
    for(const [key,value]of first.values)second.values.set(key,value);
    second.monitor.configure(protocol,scope);await second.advance();
    assert.equal(second.reads[0].query.operation_id,id);assert.equal(second.ends.length,1);assert.equal(second.ends[0].flags.notify,false);
    const stored=[...second.values.values()].join('');assert(!stored.includes('user_text'));assert(!stored.includes('message:'));
  });
  await test('lost admission searches original client identity and never resends',async()=>{
    const h=harness(frame(null));h.monitor.configure(protocol,scope);await h.advance();h.monitor.expect(client);h.monitor.uncertain();
    h.setResponse(frame(operation()));await h.advance();assert.equal(h.reads.at(-1).query.client_message_id,client);
    assert.equal(h.monitor.snapshot().operation.operation_id,id);assert.equal(h.monitor.snapshot().error,'');
  });
  await test('unverified delivery stays blocked and is not polled forever',async()=>{
    const h=harness(frame(operation({lifecycle_state:'unverified',delivery_state:'unknown'})));
    h.monitor.configure(protocol,scope);await h.advance();const count=h.reads.length;await h.advance(30000);
    assert.equal(h.reads.length,count);assert(h.monitor.snapshot().blocked);assert.equal(h.ends[0].value.lifecycle_state,'unverified');
  });
  await test('scope switch aborts old read and rejects its late result',async()=>{
    const h=harness();let resolve;h.setResponse(()=>new Promise(r=>resolve=r));h.monitor.configure(protocol,scope);await h.advance();
    const previous=h.reads[0];h.setResponse(frame(null));h.monitor.configure(protocol,{...scope,workstream_id:'project-other'});await h.advance();
    resolve(frame());await flush();assert(previous.signal.aborted);assert.equal(h.monitor.snapshot().operation,null);
    assert(!h.changes.at(-1).error);
  });
  await test('foreign thread or generation cannot resolve a watched operation',async()=>{
    for(const change of [{thread_id:'other'},{connection_generation:2},{workstream_id:'project-other'}]){
      const h=harness(frame(null));h.monitor.configure(protocol,scope);await h.advance();h.monitor.expect(client);h.monitor.uncertain();
      h.setResponse(frame(operation({scope:{...scope,...change}})));await h.advance();
      assert.equal(h.monitor.snapshot().operation,null);assert(h.monitor.snapshot().blocked);assert(h.monitor.snapshot().error);
    }
  });
  await test('older revision cannot overwrite a newer measurement',async()=>{
    const h=harness(frame(operation({revision:6,cursor:6,events:[]})));h.monitor.configure(protocol,scope);await h.advance();
    h.setResponse(frame(operation({revision:4,cursor:4})));await h.advance(750);
    assert.equal(h.monitor.snapshot().cursor,6);assert(h.monitor.snapshot().error);assert.equal(h.monitor.snapshot().operation.revision,6);
  });
  await test('delayed admission does not replace newer read proof',async()=>{
    const h=harness(frame(null));h.monitor.configure(protocol,scope);await h.advance();h.monitor.expect(client);
    h.setResponse(frame(operation({revision:5,cursor:5,events:[]})));await h.advance(750);
    assert.equal(h.monitor.accepted(frame(operation(),{read_only:false,writes_performed:true})),true);
    assert.equal(h.monitor.snapshot().cursor,5);assert.equal(h.monitor.snapshot().error,'');
  });
  await test('conflicting historical event and terminal resurrection are rejected',async()=>{
    const h=harness();h.monitor.configure(protocol,scope);await h.advance();
    h.setResponse(frame(operation({revision:3,cursor:3,events:[{cursor:2,kind:'tool_finished',at:new Date(base+500).toISOString()}]})));
    await h.advance(750);assert(h.monitor.snapshot().error);assert.equal(h.monitor.snapshot().operation.events[0].kind,'turn_started');
    const done=harness(frame(operation({lifecycle_state:'completed',delivery_state:'confirmed'})));
    done.monitor.configure(protocol,scope);await done.advance();done.setResponse(frame(operation({revision:3,cursor:3,events:[]})));
    done.monitor.refresh();await done.advance();assert.equal(done.monitor.snapshot().operation.lifecycle_state,'completed');assert(done.monitor.snapshot().error);
  });
  await test('gap applies full snapshot and discards incomplete local history',async()=>{
    const h=harness();h.monitor.configure(protocol,scope);await h.advance();
    h.setResponse(frame(operation({revision:10,cursor:10,resync_required:true,event_gap:true,
      events:[{cursor:10,kind:'completion_updated',at:new Date(base+1000).toISOString()}],lifecycle_state:'awaiting_completion'})));
    await h.advance(750);assert.equal(h.monitor.snapshot().operation.events.length,1);assert.equal(h.monitor.snapshot().cursor,10);
    await h.advance(750);assert.equal(h.reads.at(-1).query.cursor,'10');
  });
  await test('read failure uses bounded backoff and automatically recovers',async()=>{
    const h=harness();h.monitor.configure(protocol,scope);await h.advance();h.setResponse(()=>{throw new Error('PRIVATE_ERROR');});
    await h.advance(750);assert(h.monitor.snapshot().error);assert(!h.monitor.snapshot().error.includes('PRIVATE'));
    await h.advance(1000);await h.advance(2000);const before=h.reads.length;
    h.setResponse(frame(operation({revision:3,cursor:3,events:[]})));await h.advance(4000);
    assert.equal(h.reads.length,before+1);assert.equal(h.monitor.snapshot().error,'');
  });
  await test('hung request has deadline and never overlaps another reader',async()=>{
    const h=harness();h.setResponse((_query,signal)=>new Promise((_resolve,reject)=>signal.addEventListener('abort',()=>reject(new Error('aborted')))));
    h.monitor.configure(protocol,scope);await h.advance();await h.advance(4999);assert.equal(h.reads.length,1);
    await h.advance(1);assert(h.reads[0].signal.aborted);assert(h.monitor.snapshot().error);await h.advance(1000);assert.equal(h.reads.length,2);
  });
  await test('hidden browser slows reads; pagehide stops and pageshow resumes',async()=>{
    const h=harness();h.setVisible(false);h.monitor.configure(protocol,scope);await h.advance();await h.advance(4999);assert.equal(h.reads.length,1);
    h.monitor.pause();await h.advance(20000);assert.equal(h.reads.length,1);h.monitor.resume();await h.advance();assert.equal(h.reads.length,2);
    h.setVisible(true);h.monitor.wake();await h.advance();assert.equal(h.reads.length,3);
  });
  await test('storage denial still allows server discovery',async()=>{
    const h=harness();h.host.storage={getItem(){throw Error('denied');},setItem(){throw Error('denied');}};
    h.monitor.configure(protocol,scope);await h.advance();assert.equal(h.monitor.snapshot().operation.operation_id,id);
  });
  await test('no private error or fabricated percent in rendered model',async()=>{
    const h=harness();h.monitor.configure(protocol,scope);await h.advance();
    assert(!context.humanAdamLiveSummary(h.monitor.snapshot()).includes('%'));
    h.setResponse(frame(operation({lifecycle_state:'completed',delivery_state:'unknown'})));await h.advance(750);
    assert(h.monitor.snapshot().error);assert.match(context.humanAdamLiveSummary(h.monitor.snapshot()),/není ověřen/);
  });
  await test('actual owned sender posts once; loss, double click and preparation failure never replay',async()=>{
    const ownedStart=html.indexOf('  async function sendOwnedWork()');
    const ownedEnd=html.indexOf('  async function sendMessage(event)',ownedStart);
    const sendStart=html.indexOf('  async function sendMessage(event)');
    const sendEnd=html.indexOf('  composer.addEventListener("submit", sendMessage);',sendStart);
    for(const mode of ['ok','loss','preparation','disconnected']){
      const calls=[], accepted=[], elements=new Map();let blocked=false;
      const s={AbortController,console,activeWorkstreamId:scope.workstream_id,
        lastSession:{thread_id:scope.thread_id,connection_generation:3,messages:[]},
        busy:false,sessionConnected:mode!=='disconnected',sendInFlight:false,sessionTurnBusy:false,pendingSubmission:null,
        voiceStarting:false,voiceRecording:false,voiceTranscribing:false,lunaReleaseStatusLoaded:true,
        writeIntentArmed:true,deliveryUncertain:false,input:{value:'Přesné zadání'},notice:{textContent:''},
        document:{getElementById:id=>{if(!elements.has(id))elements.set(id,{hidden:false});return elements.get(id);}},
        messageId:()=>{if(mode==='preparation')throw Error('no identity');return client;},
        shouldInterceptLunaReleaseCommand:()=>false,
        clearMessageInput(){s.input.value='';},syncControls(){},updateMobileStatusSummary(){},
        runSendUiBestEffort:fn=>{try{fn();}catch{}},primeCompletionMediaSound:async()=>{},
        renderSession:session=>{s.lastSession=session;},showSendFailure(){},
        window:{setTimeout:()=>1,clearTimeout(){}},
        workMonitor:{snapshot:()=>({enabled:true,blocked}),expect:()=>{blocked=true;},
          accepted:value=>{accepted.push(value);return true;},uncertain:()=>{blocked=true;}},
        api:async(path,options)=>{calls.push({path,options});if(mode==='loss')throw Error('lost ACK');return frame();},
      };
      vm.createContext(s);vm.runInContext(html.slice(ownedStart,ownedEnd)+html.slice(sendStart,sendEnd),s);
      await s.sendMessage({preventDefault(){}});await s.sendMessage({preventDefault(){}});
      if(mode==='preparation'||mode==='disconnected'){assert.equal(calls.length,0);assert.equal(s.input.value,'Přesné zadání');continue;}
      assert.equal(calls.length,1);assert.equal(calls[0].path,'/api/human-adam/work/start');
      const body=JSON.parse(calls[0].options.body);assert.equal(body.confirmed,true);assert.equal(body.workstream_id,scope.workstream_id);
      assert.equal(body.client_message_id,client);assert.equal(body.write_intent,true);assert.equal(s.writeIntentArmed,false);
      assert.equal(s.input.value,'');assert.equal(s.sendInFlight,false);
      if(mode==='loss'){assert.equal(s.pendingSubmission.clientId,client);assert.equal(accepted.length,0);}
      else assert.equal(accepted.length,1);
    }
  });
  console.log(`HA-05 monitor: ${passed} scenarios PASS`);
})().catch(error=>{console.error(error);process.exitCode=1;});
