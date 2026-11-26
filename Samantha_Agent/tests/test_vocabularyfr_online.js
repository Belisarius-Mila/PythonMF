const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {Element,fixture,storage,flush,until}=require('./fixtures/vocabulary_fr_dom.js');
const online=require('../../docs/vocabulary-fr/online.js'),memory=require('../../docs/vocabulary-fr/memory.js');
const html=fs.readFileSync(path.resolve(__dirname,'../../docs/vocabulary-fr/online.html'),'utf8');
const base=fixture.make();
// Enough independent synthetic meanings to play a wholly different second round.
for(let n=19;n<=36;n++){
 const uid=`vfr-${String(n).padStart(4,'0')}`,fr=`mot test ${n}`,cz=`testovací význam ${n}`;
 const item={...base.data.items[0],id:n,uid,fr,cz,image:`assets/vocabulary-fr-v2/images/fixture-${n}.webp`,thumbnail:`assets/vocabulary-fr-v2/thumbs/fixture-${n}.webp`,related:[]};
 base.data.items.push(item);base.audio.items[uid]={...base.audio.items['vfr-0001'],uid,sourceFr:fr,sourceCz:cz,fr:`assets/vocabulary-fr-audio/fixture/${uid}-fr.mp3`};
 base.quiz.entries[uid]={...base.quiz.entries['vfr-0001'],uid,fr,cz,image:item.image,thumbnail:item.thumbnail,pieces:[fr]};
}
const files=[base.data,base.audio,base.quiz],texts=files.map(JSON.stringify);
const revision=crypto.createHash('sha256').update(texts.join('\0')).digest('hex');
const uids=memory.choose(base.data.items,base.audio,base.quiz,()=>.5).map(i=>i.uid);
const room='d'.repeat(24);

function bridge(){
 let state=null,hostToken=null,guestToken=null,invite=null,failed=false,loseFlip=false,loseRematch=false;
 const requests=[];
 const result=(status,value)=>({ok:status===200,status,json:async()=>structuredClone(value)});
 function view(you){const value=structuredClone(state);value.you=you;return value;}
 function board(){state.cards=state.deck.map((uid,index)=>({index,state:state.owners[uid]!==undefined?'matched':state.open.includes(index)?'open':'hidden',...(state.owners[uid]!==undefined||state.open.includes(index)?{uid}:{})}));}
 async function fetcher(url,options={}){
  if(failed)throw Error('offline');
  const names=['vocabulary-fr-v2.json','vocabulary-fr-audio.json','vocabulary-fr-quiz.json'];
  const n=names.findIndex(name=>String(url).endsWith(name));if(n>=0)return {ok:true,text:async()=>texts[n]};
  if(String(url).endsWith('/health'))return result(200,{protocol:1,catalog:revision});
  const payload=JSON.parse(options.body),action=String(url).split('/').at(-1),token=options.headers.Authorization?.replace('Bearer ','');requests.push({url:String(url),payload,token});
  if(action==='rooms'){
   hostToken=payload.playerToken;invite=payload.invite;
   state={protocol:1,room,revision:1,catalog:revision,players:[{name:payload.name,connected:true},null],owners:{},active:0,turns:0,round:1,phase:'waiting',stage:0,focus:null,reward:null,acks:[],paused:false,deck:payload.uids.flatMap(uid=>[uid,uid]),open:[]};board();return result(200,view(0));
  }
  if(action==='join'){
   if(payload.invite!==invite)return result(403,{error:'Pozvánka není platná.'});
   if(guestToken&&guestToken!==payload.playerToken)return result(409,{error:'Obě místa jsou už obsazená.'});
   guestToken=payload.playerToken;state.players[1]={name:payload.name,connected:true};state.revision++;return result(200,view(1));
  }
  const you=token===hostToken?0:token===guestToken?1:null;if(you===null)return result(403,{error:'Neplatný přístup.'});
  if(action==='leave'){state.players[you].connected=false;state.paused=true;state.revision++;}
  if(action==='ready'){state.players[you].connected=true;state.paused=!state.players.every(p=>p?.connected);state.revision++;}
  if(action==='start'){state.phase='choose';state.revision++;}
  if(action==='flip'){
   if(state.phase!=='choose'||state.active!==you||state.paused)return result(409,{error:'Teď nehraješ.'});
   state.open.push(payload.index);state.focus=payload.index;state.phase='reveal';state.stage++;state.acks=[];state.revision++;board();
   if(loseFlip){loseFlip=false;throw Error('reply lost');}
  }
  if(action==='heard'){
   if(!state.acks.includes(you))state.acks.push(you);state.revision++;
   if(state.acks.length===2){if(state.phase==='reveal')state.phase=state.open.length===1?'choose':'compare';else if(state.phase==='reward'){state.phase=Object.keys(state.owners).length===12?'finished':'choose';state.reward=null;}}
  }
  if(action==='rematch'||action==='restart'){if(payload.uids)state.deck=payload.uids.flatMap(uid=>[uid,uid]);state.phase='choose';state.owners={};state.open=[];state.round++;state.turns=0;state.active=0;state.acks=[];state.reward=null;state.revision++;board();if(loseRematch){loseRematch=false;throw Error('reply lost');}}
  return result(200,view(you));
 }
 return {fetcher,requests,get state(){return state;},set failed(value){failed=value;},set loseFlip(value){loseFlip=value;},set loseRematch(value){loseRematch=value;},reward(uid){state.owners[uid]=state.active;state.open=[];state.turns++;state.reward=uid;state.phase='reward';state.stage++;state.acks=[];state.revision++;board();},mismatch(){state.active=1-state.active;state.open=[];state.turns++;state.phase='choose';state.revision++;board();}};
}

async function client(server,{url='http://localhost/vocabulary-fr/online.html',session=storage(),name='Jana',blocked=false}={}){
 const doc=new Element('document');doc.doc=doc;doc.hidden=false;doc.getElementById=id=>doc.descendants().find(v=>v.id===id);doc.createElement=tag=>new Element(tag,doc);doc.body=doc;
 for(const [,id] of html.matchAll(/\bid="([^"]+)"/g)){const node=new Element('div',doc);node.id=id;doc.append(node);}
 doc.getElementById('onlineName').value=name;
 let now=0,id=0;const timers=new Map(),events={};
 const win={location:{href:url},crypto:crypto.webcrypto,navigator:{clipboard:{writeText:async()=>{}}},confirm:()=>true,addEventListener:(key,fn)=>(events[key]??=[]).push(fn),setTimeout:(fn,ms)=>{timers.set(++id,{fn,at:now+ms});return id;},clearTimeout:key=>timers.delete(key)};
 win.history={replaceState:(a,b,value)=>{win.location.href=new URL(value,win.location.href).toString();}};
 if(blocked)Object.defineProperty(win,'sessionStorage',{get(){throw Error('blocked');}});else win.sessionStorage=session;
 const players=[];class Audio {
  constructor(){this.handlers={};this.starts=[];this.paused=true;this.reject=false;this.loadCount=0;players.push(this);}
  load(){this.loadCount++;this.position=0;}pause(){this.paused=true;}
  play(){this.paused=false;this.starts.push(this.src);return this.reject?Promise.reject(Error('blocked')):Promise.resolve();}
  addEventListener(key,fn){this.handlers[key]=fn;}removeEventListener(key,fn){if(this.handlers[key]===fn)delete this.handlers[key];}
 }
 const api=online.create({doc,win,fetcher:server.fetcher,AudioClass:Audio});await api.init();
 return {api,doc,win,session,players,element:key=>doc.getElementById(key),advance:ms=>{now+=ms;for(const [key,t] of [...timers])if(t.at<=now){timers.delete(key);t.fn();}},ended:()=>{const p=players[0];assert.equal(p.paused,false);p.handlers.ended?.();},emit:key=>{for(const fn of events[key]||[])fn();}};
}
async function enter(view){const task=view.api.enter();await until(()=>!view.players[0].paused);view.ended();await task;await flush();}
async function pairClients(){const server=bridge(),a=await client(server);await enter(a);const b=await client(server,{url:a.element('onlineInvite').value,name:'Míla'});await enter(b);await a.api.poll();await a.api.command('start');await b.api.poll();return {server,a,b};}
async function finish(view){view.ended();view.advance(2000);await flush();await until(()=>!view.element('onlineBoard').children.length||view.players[0].paused);await flush();}
async function finishedGame(server,...clients){server.state.owners=Object.fromEntries(uids.map((uid,n)=>[uid,n%2]));server.state.phase='finished';server.state.revision++;for(const view of clients)await view.api.poll();}

test('online stays silent until explicit entry and unavailable service cannot start a room',async()=>{
 const server=bridge(),a=await client(server);assert.equal(a.players[0].starts.length,0);assert.equal(server.requests.length,0);
 assert.equal(a.element('onlineEnter').disabled,false);server.failed=true;const b=await client(server);assert.equal(b.element('onlineEnter').disabled,true);assert.match(b.element('onlineStatus').textContent,/načíst/);
});
test('private invitation joins two independent sessions with tokens only in Authorization/body',async()=>{
 const {server,a,b}=await pairClients();assert.notEqual(a.session,b.session);assert.equal(a.api.getState().you,0);assert.equal(b.api.getState().you,1);
 assert.equal(a.element('onlineBoard').children.length,24);assert.equal(b.element('onlineBoard').children.length,24);
 assert.ok(server.requests.some(r=>r.url.endsWith('/join')));assert.match(b.win.location.href,/\#room=/);assert.doesNotMatch(b.win.location.href,/invite/);
 const secret=JSON.parse(a.session.getItem(online.KEY)).token;assert.ok(server.requests.every(r=>!r.url.includes(secret)));assert.ok(server.requests[0].payload.uids.length===12);assert.ok(!('personalHard' in server.requests[0].payload));
});
test('both clients hear the same flip and each must finish its own audio and two-second Czech hint',async()=>{
 const {server,a,b}=await pairClients();await a.api.command('flip',{index:10});await b.api.poll();
 assert.equal(a.element('onlineBoard').querySelectorAll('.memory-translation').length,1);assert.equal(b.element('onlineBoard').querySelectorAll('.memory-translation').length,1);
 a.advance(2000);b.advance(2000);await flush();assert.equal(server.requests.filter(r=>r.url.endsWith('/heard')).length,0);
 a.ended();await flush();assert.equal(server.state.phase,'reveal');b.ended();await flush();await a.api.poll();assert.equal(server.state.phase,'choose');
 assert.equal(a.players.length,1);assert.equal(b.players.length,1);assert.equal(a.players[0].starts[1],b.players[0].starts[1]);assert.equal(a.element('onlineBoard').querySelectorAll('.memory-translation').length,0);
});
test('a second lower-numbered card plays its own word rather than the higher first card',async()=>{
 const {server,a,b}=await pairClients();await a.api.command('flip',{index:10});await b.api.poll();await finish(a);await finish(b);await a.api.poll();
 await a.api.command('flip',{index:1});await b.api.poll();
 const uid=server.state.deck[1];assert.ok(a.players[0].src.endsWith(base.audio.items[uid].fr));assert.ok(b.players[0].src.endsWith(base.audio.items[uid].fr));
 const hint=a.element('onlineBoard').querySelector('.memory-translation');assert.equal(hint.textContent,base.data.items.find(i=>i.uid===uid).cz);
});
test('a revealed card primes the full reward image and matching does not download it again',async()=>{
 const {server,a,b}=await pairClients(),image=a.element('onlineRewardImage');let source='',assignments=0;
 Object.defineProperty(image,'src',{get:()=>source,set:value=>{source=value;assignments++;}});
 await a.api.command('flip',{index:0});await b.api.poll();const uid=server.state.deck[0];
 assert.ok(source.endsWith(base.data.items.find(i=>i.uid===uid).image));assert.equal(assignments,1);assert.equal(Boolean(a.element('onlineReward').open),false);
 await finish(a);await finish(b);await a.api.poll();await a.api.command('flip',{index:1});await b.api.poll();
 assert.equal(assignments,1);image.emit('error');await finish(a);await finish(b);server.reward(uid);await a.api.poll();
 assert.equal(a.element('onlineReward').open,true);assert.equal(assignments,1);assert.equal(image.hidden,true);
});
test('reward has only French, closes after two seconds and waits for the longer audio on both clients',async()=>{
 const {server,a,b}=await pairClients(),uid=uids[0];server.reward(uid);await a.api.poll();await b.api.poll();
 assert.equal(a.element('onlineReward').open,true);assert.equal(b.element('onlineReward').open,true);assert.equal(a.element('onlineRewardWord').textContent,base.data.items.find(i=>i.uid===uid).fr);
 assert.equal(a.element('onlineReward').querySelectorAll('.memory-translation').length,0);assert.equal(a.element('onlineBoard').querySelectorAll('.memory-empty').length,2);
 a.advance(1999);await flush();assert.equal(a.element('onlineReward').open,true);a.advance(1);b.advance(2000);await flush();assert.equal(a.element('onlineReward').open,false);assert.equal(a.element('onlineBoard').querySelector('button').disabled,true);
 a.ended();await flush();assert.equal(server.state.phase,'reward');b.ended();await flush();await a.api.poll();assert.equal(server.state.phase,'choose');assert.equal(a.api.getState().active,0);
});
test('audio rejection requires explicit retry or skip and never borrows Czech',async()=>{
 const {server,a,b}=await pairClients();a.players[0].reject=true;await a.api.command('flip',{index:0});await b.api.poll();a.advance(2000);await flush();
 assert.equal(a.element('onlineRetry').hidden,false);assert.equal(server.requests.filter(r=>r.url.endsWith('/heard')).length,0);
 a.players[0].reject=false;a.element('onlineRetry').click();await flush();await finish(a);await finish(b);await a.api.poll();assert.equal(server.state.phase,'choose');assert.ok(a.players[0].starts.every(url=>/-fr\.mp3$/.test(url)));
 await a.api.command('flip',{index:1});await b.api.poll();a.players[0].handlers.error?.();a.advance(2000);await flush();assert.equal(a.element('onlineSkip').hidden,false);a.element('onlineSkip').click();await flush();assert.ok(server.requests.some(r=>r.url.endsWith('/heard')));
});
test('lost flip response recovers from snapshot without resending the mutation or creating another room',async()=>{
 const {server,a}=await pairClients();server.loseFlip=true;await a.api.command('flip',{index:4});await a.api.poll();
 assert.equal(a.api.getState().phase,'reveal');assert.equal(server.requests.filter(r=>r.url.endsWith('/flip')).length,1);assert.equal(server.requests.filter(r=>r.url.endsWith('/rooms')).length,1);
});
test('pagehide cancels sound and reward; reload requires explicit reentry without duplicate points',async()=>{
 const {server,a,b}=await pairClients();server.reward(uids[0]);await a.api.poll();await b.api.poll();a.emit('pagehide');await flush();assert.equal(a.players[0].paused,true);assert.equal(a.element('onlineReward').hidden,true);
 const reloaded=await client(server,{url:a.win.location.href,session:a.session});assert.equal(reloaded.players[0].starts.length,0);assert.match(reloaded.element('onlineEnter').textContent,/Pokračovat/);
 await enter(reloaded);assert.equal(reloaded.api.getState().owners[uids[0]],0);assert.equal(Object.keys(reloaded.api.getState().owners).length,1);
});
test('network outage disables clicks and recovery preserves the same room and turn',async()=>{
 const {server,a}=await pairClients();server.failed=true;await a.api.poll();assert.equal(a.element('onlineBoard').querySelector('button').disabled,true);assert.match(a.element('onlineStatus').textContent,/Spojení/);
 server.failed=false;await a.api.poll();assert.equal(a.element('onlineBoard').querySelector('button').disabled,false);assert.equal(a.api.getState().room,room);assert.equal(a.api.getState().active,0);
});
test('blocked storage keeps current room in memory and explains the missing reload recovery',async()=>{
 const server=bridge(),a=await client(server,{blocked:true});await enter(a);assert.ok(a.api.getState().room);assert.match(a.element('onlineStorage').textContent,/Obnovení/);
});
test('unconfirmed leave keeps game running and confirmed leave stops it',async()=>{
 const {a}=await pairClients();let prevented=false;a.win.confirm=()=>false;a.element('onlineBack').emit('click',{preventDefault(){prevented=true;}});assert.equal(prevented,true);assert.equal(a.element('onlineResume').hidden,true);
 a.win.confirm=()=>true;a.element('onlineBack').click();assert.equal(a.element('onlineResume').hidden,false);
});
test('invalid or incomplete invitations cannot start a new or unrelated room',async()=>{
 const server=bridge();for(const hash of ['#room=foreign','#room='+room,'#room='+room+'&invite=bad']){const a=await client(server,{url:'http://localhost/vocabulary-fr/online.html'+hash});assert.equal(a.element('onlineEnter').disabled,true);assert.equal(server.requests.length,0);}
});
test('waiting room notices changed presence even when its game revision did not change',async()=>{
 const {server,a}=await pairClients();server.state.phase='waiting';server.state.revision++;await a.api.poll();assert.equal(a.element('onlineStart').disabled,false);
 server.state.players[1].connected=false;await a.api.poll();assert.equal(a.element('onlineStart').disabled,true);
});
test('finished collections replay is not cancelled by ordinary presence polling',async()=>{
 const {server,a}=await pairClients();server.state.owners=Object.fromEntries(uids.map(uid=>[uid,0]));server.state.phase='finished';server.state.revision++;await a.api.poll();
 a.element('onlineCollections').querySelector('button').click();assert.equal(a.players[0].paused,false);await a.api.poll();assert.equal(a.players[0].paused,false);a.ended();
});
test('a stalled request times out and rechecks state without replaying a move',async()=>{
 const {server,a}=await pairClients(),normal=server.fetcher;let stall=true;
 // A separate client can restore the same private session with a stalled transport.
 const transport={fetcher:async(url,options)=>{if(stall&&String(url).endsWith('/flip')){await normal(url,options);return new Promise(()=>{});}return normal(url,options);}};
 const b=await client(transport,{url:a.win.location.href,session:a.session});await enter(b);const pending=b.api.command('flip',{index:7});await flush();b.advance(8000);await pending;stall=false;await b.api.poll();
 assert.equal(b.api.getState().phase,'reveal');assert.equal(server.requests.filter(r=>r.url.endsWith('/flip')).length,1);
});
test('host starts different words while both clients keep the room, names, access and invitation',async()=>{
 const {server,a,b}=await pairClients();await finishedGame(server,a,b);
 const oldDeck=[...server.state.deck],urls=[a.win.location.href,b.win.location.href],sessions=[a.session.getItem(online.KEY),b.session.getItem(online.KEY)];
 assert.equal(a.element('onlineNewWords').hidden,false);assert.equal(b.element('onlineNewWords').hidden,true);
 a.element('onlineNewWords').click();assert.equal(a.element('onlinePicker').hidden,false);assert.equal(a.element('onlineCandidates').children.length,12);
 const preview=a.element('onlineCandidates').textContent;await a.api.poll();assert.equal(a.element('onlineCandidates').textContent,preview);
 a.element('onlineNextStart').click();await until(()=>server.state.round===2);await flush();await b.api.poll();
 const sent=server.requests.filter(r=>r.url.endsWith('/rematch'));assert.equal(sent.length,1);assert.equal(sent[0].payload.uids.length,12);
 assert.ok(sent[0].payload.uids.every(uid=>!oldDeck.includes(uid)));assert.deepEqual(new Set(server.state.deck),new Set(sent[0].payload.uids));
 for(const [n,view] of [a,b].entries()){
  assert.equal(view.api.getState().room,room);assert.equal(view.api.getState().round,2);assert.deepEqual(view.api.getState().owners,{});assert.equal(view.api.getState().turns,0);
  assert.equal(view.win.location.href,urls[n]);assert.equal(view.session.getItem(online.KEY),sessions[n]);assert.equal(view.element('onlinePicker').hidden,true);
  assert.equal(view.element('onlineBoard').querySelectorAll('.memory-empty').length,0);assert.equal(view.players[0].starts.length,1);
 }
 assert.deepEqual(server.state.players.map(p=>p.name),['Jana','Míla']);
 assert.equal(server.requests.filter(r=>r.url.endsWith('/rooms')).length,1);assert.equal(server.requests.filter(r=>r.url.endsWith('/join')).length,1);
 await a.api.command('flip',{index:0});await b.api.poll();assert.equal(a.players[0].src,b.players[0].src);
});
test('small topic cannot silently repeat old words; choosing a broader topic and cancelling preserves scores',async()=>{
 const {server,a}=await pairClients();await finishedGame(server,a);const scores=structuredClone(server.state.owners);
 a.element('onlineNewWords').click();a.element('onlineTopic').value='topic-18';a.element('onlineTopic').emit('change');
 assert.equal(a.element('onlineNextStart').disabled,true);assert.match(a.element('onlineCandidatesInfo').textContent,/není dost/);
 a.element('onlineTopic').value='';a.element('onlineTopic').emit('change');assert.equal(a.element('onlineNextStart').disabled,false);
 a.element('onlineNextCancel').click();assert.equal(a.element('onlinePicker').hidden,true);assert.deepEqual(server.state.owners,scores);
 assert.equal(server.requests.filter(r=>r.url.endsWith('/rematch')).length,0);
});
test('disconnect locks the new-round picker and a lost rematch reply recovers without another room or rematch',async()=>{
 const {server,a,b}=await pairClients();await finishedGame(server,a,b);a.element('onlineNewWords').click();
 server.failed=true;await a.api.poll();assert.equal(a.element('onlineNextStart').disabled,true);assert.equal(a.element('onlineTopic').disabled,true);
 server.failed=false;await a.api.poll();assert.equal(a.element('onlineNextStart').disabled,false);
 server.loseRematch=true;a.element('onlineNextStart').click();await until(()=>server.state.round===2);await flush();await a.api.poll();await b.api.poll();
 assert.equal(a.api.getState().round,2);assert.equal(b.api.getState().round,2);assert.equal(a.element('onlinePicker').hidden,true);
 assert.equal(server.requests.filter(r=>r.url.endsWith('/rematch')).length,1);assert.equal(server.requests.filter(r=>r.url.endsWith('/join')).length,1);
});
test('same-words rematch remains available without transmitting a replacement selection',async()=>{
 const {server,a,b}=await pairClients();await finishedGame(server,a,b);const before=[...server.state.deck];
 a.element('onlineAgain').click();await until(()=>server.state.round===2);await flush();await b.api.poll();
 assert.deepEqual(server.state.deck,before);assert.equal(b.api.getState().round,2);assert.equal('uids' in server.requests.find(r=>r.url.endsWith('/rematch')).payload,false);
});

test('host changes filters during play and can cancel back without leaving either client',async()=>{
 const {server,a,b}=await pairClients();const before=structuredClone(server.state),sessions=[a.session.getItem(online.KEY),b.session.getItem(online.KEY)];
 assert.equal(a.element('onlineChangeFilter').hidden,false);assert.equal(b.element('onlineChangeFilter').hidden,true);
 a.element('onlineChangeFilter').click();assert.equal(a.element('onlinePicker').hidden,false);assert.equal(a.element('onlineCandidates').children.length,12);
 a.element('onlineQuery').value='neexistuje';a.element('onlineQuery').emit('input');assert.equal(a.element('onlineNextStart').disabled,true);
 a.element('onlineNextCancel').click();assert.equal(a.element('onlinePicker').hidden,true);
 assert.deepEqual(server.state,before);assert.equal(server.requests.filter(r=>r.url.endsWith('/leave')||r.url.endsWith('/restart')).length,0);
 assert.deepEqual([a.session.getItem(online.KEY),b.session.getItem(online.KEY)],sessions);
 a.element('onlineChangeFilter').click();a.element('onlineQuery').value='';a.element('onlineQuery').emit('input');
 a.element('onlinePart').value='interjection';a.element('onlinePart').emit('change');
 assert.ok(a.element('onlineCandidates').children.length<12);assert.equal(a.element('onlineNextStart').disabled,true);
 a.element('onlinePart').value='';a.element('onlinePart').emit('change');assert.equal(a.element('onlineNextStart').disabled,false);
 a.win.confirm=()=>false;a.element('onlineNextStart').click();await flush();assert.equal(server.state.round,1);
 a.win.confirm=()=>true;server.loseRematch=true;a.element('onlineNextStart').click();await until(()=>server.state.round===2);await flush();await a.api.poll();await b.api.poll();
 assert.equal(server.requests.filter(r=>r.url.endsWith('/restart')).length,1);assert.equal(server.requests.filter(r=>r.url.endsWith('/rooms')).length,1);assert.equal(server.requests.filter(r=>r.url.endsWith('/join')).length,1);
 for(const view of [a,b]){assert.equal(view.api.getState().round,2);assert.equal(view.api.getState().room,room);assert.deepEqual(view.api.getState().owners,{});assert.equal(view.element('onlinePicker').hidden,true);}
 assert.deepEqual([a.session.getItem(online.KEY),b.session.getItem(online.KEY)],sessions);
});
test('filter restart cancels old reward sound and guest cannot open the picker',async()=>{
 const {server,a,b}=await pairClients();b.element('onlineChangeFilter').click();assert.equal(b.element('onlinePicker').hidden,true);
 server.reward(uids[0]);await a.api.poll();await b.api.poll();a.advance(2000);b.advance(2000);await flush();
 a.element('onlineChangeFilter').click();a.element('onlineNextStart').click();await until(()=>server.state.round===2);await flush();await b.api.poll();
 for(const view of [a,b]){assert.equal(view.players[0].paused,true);assert.equal(view.element('onlineReward').hidden,true);view.advance(20000);}
 await flush();assert.equal(server.requests.filter(r=>r.url.endsWith('/heard')).length,0);assert.deepEqual(server.state.owners,{});
});
test('completed game can change filter without requiring twelve entirely different meanings',async()=>{
 const {server,a,b}=await pairClients();await finishedGame(server,a,b);a.element('onlineChangeFilter').click();
 assert.equal(a.element('onlinePicker').hidden,false);assert.equal(a.element('onlineNextStart').disabled,false);
 a.element('onlineNextStart').click();await until(()=>server.state.round===2);await flush();await b.api.poll();
 assert.equal(server.requests.filter(r=>r.url.endsWith('/restart')).length,1);assert.equal(b.api.getState().round,2);
});

// Exercise the actual duel UI with separate clocks, DOMs, storage and players.
const duel=require('../../docs/vocabulary-fr/duel.js');
const duelHtml=fs.readFileSync(path.resolve(__dirname,'../../docs/vocabulary-fr/duel.html'),'utf8');
function duelBridge(){
 let state=null,host=null,guest=null,invite=null;
 const bridge={now:0,failed:false,loseAnswer:false,loseRestart:false,games:['pairs','duel'],requests:[]};
 const time=()=>1800000000+bridge.now/1000;
 const result=(value,status=200)=>({ok:status===200,status,json:async()=>structuredClone(value)});
 function question(){state.choices=[state.pool[state.question-1],...state.pool.filter(uid=>uid!==state.pool[state.question-1]).slice(0,11)];state.answers={};state.closed=[];state.acks=[];state.phase='duel_intro';state.since=time();state.stage++;state.revision++;}
 function advance(){
  if(state.paused)return;
  if(state.phase==='duel_intro'&&state.acks.length===2&&time()-state.since>=3){state.phase='duel_choose';state.stage++;state.opensAt=time()+1.5;state.closesAt=state.opensAt+3;state.revision++;}
  else if(state.phase==='duel_choose'&&state.closed.length===2&&time()>=state.closesAt){for(let i=0;i<2;i++)state.scores[i]+=Number(state.answers[i]===0);state.phase='duel_result';state.stage++;state.acks=[];state.since=time();state.revision++;}
  else if(state.phase==='duel_result'&&state.acks.length===2&&time()-state.since>=2){state.phase=state.question===12?'finished':'duel_between';state.revision++;}
 }
 function view(you){
  const showing=['duel_result','duel_between','finished'].includes(state.phase);
  return {protocol:1,mode:'duel',room,revision:state.revision,catalog:revision,you,players:state.players,round:state.round,stage:state.stage,phase:state.phase,question:state.question,questionCount:12,poolCount:state.pool.length,pool:you===0?state.pool:null,choices:state.phase==='waiting'?[]:state.choices,
   promptAudio:state.phase==='duel_intro'?base.audio.items[state.choices[0]].cz:null,target:showing?state.choices[0]:null,scores:state.scores,ownAnswer:state.answers[you]??null,answers:showing?state.answers:null,acks:state.acks,closed:state.closed.includes(you),serverTime:time(),opensAt:state.opensAt,closesAt:state.closesAt,paused:state.paused,expires:time()+86400};
 }
 bridge.fetcher=async(url,options={})=>{
  if(bridge.failed)throw Error('offline');
  const n=['vocabulary-fr-v2.json','vocabulary-fr-audio.json','vocabulary-fr-quiz.json'].findIndex(name=>String(url).endsWith(name));
  if(n>=0)return {ok:true,text:async()=>texts[n]};
  if(String(url).endsWith('/health'))return result({protocol:1,catalog:revision,games:bridge.games});
  const payload=JSON.parse(options.body),action=String(url).split('/').at(-1),token=options.headers.Authorization?.replace('Bearer ','');bridge.requests.push({action,payload,token});
  if(action==='rooms'){
   host=payload.playerToken;invite=payload.invite;
   state={players:[{name:payload.name,connected:true},null],pool:payload.uids,question:1,round:1,stage:0,revision:1,scores:[0,0],answers:{},closed:[],acks:[],phase:'waiting',paused:false,choices:[]};return result(view(0));
  }
  if(action==='join'){
   if(invite!==payload.invite)return result({error:'Neplatná pozvánka'},403);
   guest=payload.playerToken;state.players[1]={name:payload.name,connected:true};state.revision++;return result(view(1));
  }
  const you=token===host?0:token===guest?1:-1;if(you<0)return result({error:'Neplatný přístup'},403);
  advance();
  if(action==='ready'){state.players[you].connected=true;state.paused=!state.players.every(p=>p?.connected);if(state.phase==='duel_choose')question();state.revision++;}
  if(action==='leave'){state.players[you].connected=false;state.paused=true;if(state.phase==='duel_choose')question();state.revision++;}
  if(action==='start')question();
  if(action==='heard'){if(!state.acks.includes(you))state.acks.push(you);state.revision++;}
  if(action==='answer'){
   if(state.phase!=='duel_choose'||time()<state.opensAt||time()>=state.closesAt||state.answers[you]!==undefined)return result({error:'Odpověď je uzavřená'},409);
   state.answers[you]=payload.index;state.revision++;if(bridge.loseAnswer){bridge.loseAnswer=false;throw Error('lost answer');}
  }
  if(action==='closed'){if(!state.closed.includes(you))state.closed.push(you);state.revision++;}
  if(action==='next'){state.question++;question();}
  if(action==='rematch'||action==='restart'){
   if(payload.uids)state.pool=payload.uids;state.question=1;state.round++;state.scores=[0,0];question();
   if(bridge.loseRestart){bridge.loseRestart=false;throw Error('lost restart');}
  }
  advance();return result(view(you));
 };
 Object.defineProperty(bridge,'state',{get:()=>state});return bridge;
}
async function duelClient(server,{url='http://localhost/vocabulary-fr/duel.html',session=storage(),name='Jana',blocked=false,failImage=false,holdImage=false,clockOffset=0}={}){
 const doc=new Element('document');doc.doc=doc;doc.hidden=false;doc.getElementById=id=>doc.descendants().find(node=>node.id===id);doc.createElement=tag=>new Element(tag,doc);doc.body=doc;
 for(const [,id] of duelHtml.matchAll(/\bid="([^"]+)"/g)){const node=new Element('div',doc);node.id=id;doc.append(node);}
 doc.getElementById('duelName').value=name;
 let now=server.now+clockOffset,id=0;const timers=new Map(),events={},pendingImages=[];
 const win={location:{href:url},performance:{now:()=>now},crypto:crypto.webcrypto,navigator:{clipboard:{writeText:async()=>{}}},confirm:()=>true,addEventListener:(key,fn)=>(events[key]??=[]).push(fn),setTimeout:(fn,ms)=>{timers.set(++id,{fn,at:now+ms});return id;},clearTimeout:key=>timers.delete(key)};
 win.history={replaceState:(a,b,value)=>{win.location.href=new URL(value,win.location.href).toString();}};
 if(blocked)Object.defineProperty(win,'sessionStorage',{get(){throw Error('blocked');}});else win.sessionStorage=session;
 const players=[];class Audio {
  constructor(){this.handlers={};this.starts=[];this.paused=true;this.reject=false;players.push(this);}
  load(){}pause(){this.paused=true;}play(){this.paused=false;this.starts.push(this.src);return this.reject?Promise.reject(Error('blocked')):Promise.resolve();}
  addEventListener(key,fn){this.handlers[key]=fn;}removeEventListener(key,fn){if(this.handlers[key]===fn)delete this.handlers[key];}
 }
 const imageElements=[];class Image extends Element {
  constructor(){super('img',doc);this.assignments=0;imageElements.push(this);}
  set src(value){this._src=value;this.assignments++;}get src(){return this._src;}
  decode(){if(failImage)return Promise.reject(Error('image'));if(holdImage)return new Promise(resolve=>pendingImages.push(resolve));return Promise.resolve();}
 }
 const api=duel.create({doc,win,fetcher:server.fetcher,AudioClass:Audio,ImageClass:Image});await api.init();
 return {api,doc,win,players,session,imageElements,element:key=>doc.getElementById(key),advance:ms=>{now+=ms;server.now=Math.max(server.now,now-clockOffset);for(const [key,t] of [...timers])if(t.at<=now){timers.delete(key);t.fn();}},ended:()=>{const p=players[0];p.paused=true;p.handlers.ended?.();},emit:key=>{for(const fn of events[key]||[])fn();},releaseImages:()=>{holdImage=false;for(const fn of pendingImages)fn();},holdNextImages:()=>{holdImage=true;},fixImages:()=>{failImage=false;}};
}
async function enterDuel(view){const task=view.api.enter();await until(()=>!view.players[0].paused);view.ended();await task;await flush();}
async function duelClients(){const server=duelBridge(),a=await duelClient(server);await enterDuel(a);const b=await duelClient(server,{url:a.element('duelInvite').value,name:'Míla'});await enterDuel(b);await a.api.poll();await a.api.command('start');await b.api.poll();return {server,a,b};}
async function duelWindow(a,b){a.ended();b.ended();a.advance(3000);b.advance(3000);await flush();await a.api.poll();await b.api.poll();a.advance(1500);b.advance(1500);await flush();}
async function duelClose(a,b){a.advance(3000);b.advance(3000);await flush();assert.equal(a.element('duelBoard').hidden,true);assert.equal(b.element('duelBoard').hidden,true);a.advance(200);b.advance(200);await flush();await a.api.poll();await b.api.poll();}

test('duel starts silently, keeps its own session, and refuses an older server without this game',async()=>{
 const server=duelBridge(),a=await duelClient(server);assert.equal(a.players[0].starts.length,0);assert.equal(server.requests.length,0);assert.equal(a.element('duelEnter').disabled,false);
 assert.notEqual(duel.KEY,online.KEY);server.games=['pairs'];const old=await duelClient(server);assert.equal(old.element('duelEnter').disabled,true);assert.match(old.element('duelStatus').textContent,/server/);
});
test('duel transfers the full filter pool and two separate invitations retain room identity',async()=>{
 const {server,a,b}=await duelClients();const sent=server.requests.find(r=>r.action==='rooms').payload;
 assert.equal(sent.mode,'duel');assert.equal(sent.uids.length,base.data.items.length);assert.ok(sent.uids.length>12);
 assert.equal(a.api.getState().you,0);assert.equal(b.api.getState().you,1);assert.notEqual(a.session,b.session);assert.doesNotMatch(b.win.location.href,/invite/);
 assert.equal(a.element('duelBoard').hidden,true);assert.equal(b.element('duelNext').hidden,true);assert.match(a.players[0].src,/-cz\.mp3$/);
});
test('duel waits for the Czech audio, all images and three seconds before displaying exactly twelve French-labelled cards',async()=>{
 const {server,a,b}=await duelClients();a.advance(3000);b.advance(3000);await flush();assert.equal(server.state.phase,'duel_intro');
 a.ended();b.ended();await flush();await a.api.poll();await b.api.poll();assert.equal(a.element('duelBoard').hidden,true);
 a.advance(1500);b.advance(1500);await flush();
 for(const view of [a,b]){assert.equal(view.element('duelBoard').children.length,12);assert.equal(view.element('duelBoard').hidden,false);assert.equal(view.element('duelBoard').children[0].querySelector('span').lang,'fr');assert.equal(view.element('duelCountdown').textContent,'3 s');}
 assert.deepEqual(a.api.getState().choices,b.api.getState().choices);a.element('duelBoard').children[0].click();a.element('duelBoard').children[1].click();await flush();assert.equal(server.requests.filter(r=>r.action==='answer').length,1);
 a.advance(2999);assert.equal(a.element('duelBoard').hidden,false);a.advance(1);assert.equal(a.element('duelBoard').hidden,true);
});
test('duel shows only large French text for two seconds, then the prepared images for exactly the final second',async()=>{
 const {server,a,b}=await duelClients();await duelWindow(a,b);
 function check(view,textOnly){
  assert.equal(view.element('duelBoard').hidden,false);assert.equal(view.element('duelBoard').children.length,12);
  for(const card of view.element('duelBoard').children){assert.equal(card.classList.contains('duel-text-only'),textOnly);assert.equal(card.querySelector('img').hidden,textOnly);assert.equal(card.querySelector('span').lang,'fr');assert.ok(card.querySelector('span').textContent);}
 }
 for(const view of [a,b])check(view,true);
 a.advance(1999);b.advance(1999);await flush();for(const view of [a,b])check(view,true);
 const images=a.element('duelBoard').querySelectorAll('img');
 a.advance(1);b.advance(1);await flush();for(const view of [a,b])check(view,false);
 await a.api.poll();await b.api.poll();for(const view of [a,b])check(view,false);
 assert.deepEqual(a.element('duelBoard').querySelectorAll('img'),images);assert.ok(images.every(img=>img.assignments===1));
 a.advance(999);b.advance(999);for(const view of [a,b])check(view,false);
 a.advance(1);b.advance(1);for(const view of [a,b])assert.equal(view.element('duelBoard').hidden,true);
 assert.equal(server.requests.filter(r=>r.action==='answer').length,0);
});
test('duel accepts a first click in either visual phase and revealing pictures never unlocks a previous answer',async()=>{
 const {server,a,b}=await duelClients();await duelWindow(a,b);
 a.element('duelBoard').children[0].click();await flush();assert.equal(a.api.getState().ownAnswer,0);
 a.advance(2000);b.advance(2000);await flush();
 for(const card of a.element('duelBoard').children){assert.equal(card.disabled,true);assert.equal(card.querySelector('img').hidden,false);}
 a.element('duelBoard').children[1].click();b.element('duelBoard').children[1].click();await flush();
 assert.equal(server.requests.filter(r=>r.action==='answer').length,2);assert.equal(b.api.getState().ownAnswer,1);assert.equal(a.api.getState().ownAnswer,0);
 a.advance(1000);b.advance(1000);assert.equal(a.element('duelBoard').hidden,true);assert.equal(b.element('duelBoard').hidden,true);
});
test('duel result awards either or both players and waits for both French playbacks before host Next',async()=>{
 const {server,a,b}=await duelClients();await duelWindow(a,b);a.element('duelBoard').children[0].click();b.element('duelBoard').children[1].click();await flush();
 assert.equal(b.api.getState().answers,null);await duelClose(a,b);
 for(const view of [a,b]){assert.equal(view.element('duelFeedback').hidden,false);assert.equal(view.element('duelWord').textContent,base.data.items[0].fr);assert.match(view.players[0].src,/-fr\.mp3$/);assert.match(view.element('duelScores').textContent,/Počet bodů: 1/);assert.equal(view.element('duelNext').hidden,true);}
 a.ended();a.advance(2000);b.advance(2000);await flush();await a.api.poll();assert.equal(a.element('duelNext').hidden,true);
 b.ended();await flush();await a.api.poll();await b.api.poll();assert.equal(a.element('duelNext').hidden,false);assert.equal(b.element('duelNext').hidden,true);
 a.element('duelNext').click();await flush();await b.api.poll();assert.equal(b.api.getState().question,2);assert.match(b.players[0].src,/-cz\.mp3$/);
});
test('duel image failure cannot start the clock or be bypassed by skipping sound',async()=>{
 const server=duelBridge(),a=await duelClient(server,{failImage:true});await enterDuel(a);const b=await duelClient(server,{url:a.element('duelInvite').value});await enterDuel(b);await a.api.poll();await a.api.command('start');await b.api.poll();
 a.ended();b.ended();a.advance(3000);b.advance(3000);await flush();assert.equal(server.state.phase,'duel_intro');assert.equal(a.element('duelRetry').hidden,false);assert.equal(a.element('duelSkip').hidden,true);
 a.fixImages();a.element('duelRetry').click();await flush();a.ended();a.advance(3000);b.advance(3000);await flush();await a.api.poll();assert.equal(server.state.phase,'duel_choose');
});
test('duel slow image loading holds the shared intro after sound ends',async()=>{
 const server=duelBridge(),a=await duelClient(server,{holdImage:true});await enterDuel(a);const b=await duelClient(server,{url:a.element('duelInvite').value});await enterDuel(b);await a.api.poll();await a.api.command('start');await b.api.poll();
 a.ended();b.ended();a.advance(3000);b.advance(3000);await flush();assert.equal(server.state.phase,'duel_intro');assert.equal(a.element('duelBoard').hidden,true);
 a.releaseImages();await flush();assert.equal(server.state.phase,'duel_choose');
});
test('duel audio failure offers explicit skip and never substitutes the other language',async()=>{
 const {server,a,b}=await duelClients();a.players[0].handlers.error?.();b.ended();a.advance(3000);b.advance(3000);await flush();
 assert.equal(a.element('duelSkip').hidden,false);assert.equal(server.state.phase,'duel_intro');a.element('duelSkip').click();await flush();assert.equal(server.state.phase,'duel_choose');assert.match(a.players[0].starts.at(-1),/-cz\.mp3$/);
});
test('duel filter cancel sends nothing; confirmed restart keeps players, invitation and sessions',async()=>{
 const {server,a,b}=await duelClients(),sessions=[a.session.getItem(duel.KEY),b.session.getItem(duel.KEY)],urls=[a.win.location.href,b.win.location.href];
 b.element('duelChangeFilter').click();assert.equal(b.element('duelPicker').hidden,true);
 a.element('duelChangeFilter').click();a.element('duelQuery').value='nothing';a.element('duelQuery').emit('input');assert.equal(a.element('duelApply').disabled,true);
 a.element('duelCancel').click();assert.equal(server.requests.filter(r=>r.action==='restart'||r.action==='leave').length,0);
 a.element('duelChangeFilter').click();a.element('duelQuery').value='';a.element('duelQuery').emit('input');a.element('duelRecent').value='20';a.element('duelRecent').emit('change');assert.equal(a.element('duelApply').disabled,false);
 a.win.confirm=()=>false;a.element('duelApply').click();await flush();assert.equal(server.state.round,1);
 a.win.confirm=()=>true;a.element('duelApply').click();await flush();await b.api.poll();assert.equal(server.state.round,2);assert.equal(server.state.pool.length,20);
 assert.deepEqual([a.session.getItem(duel.KEY),b.session.getItem(duel.KEY)],sessions);assert.deepEqual([a.win.location.href,b.win.location.href],urls);assert.equal(server.requests.filter(r=>r.action==='rooms').length,1);assert.equal(server.requests.filter(r=>r.action==='join').length,1);
});
test('duel same-pool new game resets scores without another invite and guest waits',async()=>{
 const {server,a,b}=await duelClients();server.state.phase='finished';server.state.scores=[8,9];server.state.revision++;await a.api.poll();await b.api.poll();const pool=[...server.state.pool];
 assert.equal(b.element('duelAgain').hidden,true);a.element('duelAgain').click();await flush();await b.api.poll();assert.deepEqual(server.state.pool,pool);assert.deepEqual(b.api.getState().scores,[0,0]);assert.equal(b.api.getState().round,2);assert.equal(server.requests.filter(r=>r.action==='rooms').length,1);
});
test('duel lost answer response and reload require explicit resume, with no automatic duplicate answer',async()=>{
 const {server,a,b}=await duelClients();await duelWindow(a,b);server.loseAnswer=true;a.element('duelBoard').children[0].click();await flush();
 assert.equal(a.element('duelResume').hidden,false);assert.equal(a.element('duelBoard').hidden,true);assert.equal(server.requests.filter(r=>r.action==='answer').length,1);
 const again=await duelClient(server,{url:a.win.location.href,session:a.session});assert.equal(again.players[0].starts.length,0);await enterDuel(again);await b.api.poll();assert.equal(again.api.getState().phase,'duel_intro');assert.equal(again.api.getState().question,1);assert.deepEqual(again.api.getState().scores,[0,0]);assert.equal(server.requests.filter(r=>r.action==='answer').length,1);
});
test('duel pagehide cancels timers and sound; blocked storage remains usable with a clear notice',async()=>{
 const {server,a,b}=await duelClients();await duelWindow(a,b);a.emit('pagehide');await flush();a.advance(10000);await flush();assert.equal(a.element('duelBoard').hidden,true);assert.equal(a.players[0].paused,true);assert.equal(server.requests.filter(r=>r.action==='closed').length,0);
 const other=duelBridge(),view=await duelClient(other,{blocked:true});await enterDuel(view);assert.ok(view.api.getState().room);assert.match(view.element('duelStorage').textContent,/Obnovení/);
});
test('duel timing tolerates different local monotonic clock origins on the two devices',async()=>{
 const server=duelBridge(),a=await duelClient(server,{clockOffset:10000000});await enterDuel(a);const b=await duelClient(server,{url:a.element('duelInvite').value,clockOffset:30000000});await enterDuel(b);await a.api.poll();await a.api.command('start');await b.api.poll();
 await duelWindow(a,b);assert.equal(a.element('duelBoard').hidden,false);assert.equal(b.element('duelBoard').hidden,false);a.advance(3000);b.advance(3000);assert.equal(a.element('duelBoard').hidden,true);assert.equal(b.element('duelBoard').hidden,true);
});
test('duel lost restart reply is verified by explicit reentry without repeating the restart',async()=>{
 const {server,a,b}=await duelClients();server.loseRestart=true;a.element('duelChangeFilter').click();a.element('duelApply').click();await flush();assert.equal(a.element('duelResume').hidden,false);
 await enterDuel(a);await b.api.poll();assert.equal(a.api.getState().round,2);assert.equal(b.api.getState().round,2);assert.equal(server.requests.filter(r=>r.action==='restart').length,1);assert.equal(server.requests.filter(r=>r.action==='rooms').length,1);
});
test('duel late window delivery never gives one player a shortened answer window',async()=>{
 const {server,a,b}=await duelClients();a.ended();b.ended();a.advance(3000);b.advance(3000);await flush();
 server.now+=4000;await a.api.poll();assert.equal(a.element('duelResume').hidden,false);assert.equal(a.element('duelBoard').hidden,true);assert.equal(server.state.phase,'duel_intro');
 await enterDuel(a);assert.equal(a.api.getState().question,1);assert.deepEqual(a.api.getState().scores,[0,0]);
});
test('duel moves already decoded images into cards and feedback without assigning their URL again',async()=>{
 const {a,b}=await duelClients();await duelWindow(a,b);
 assert.equal(a.imageElements.length,12);assert.ok(a.element('duelBoard').querySelectorAll('img').every(img=>a.imageElements.includes(img)&&img.assignments===1));
 a.element('duelBoard').children[0].click();await flush();await a.api.poll();assert.ok(a.element('duelBoard').querySelectorAll('img').every(img=>img.assignments===1));
 await duelClose(a,b);assert.equal(a.imageElements.length,13);assert.ok(a.imageElements.includes(a.element('duelImage')));assert.equal(a.element('duelImage').assignments,1);
 await a.api.poll();assert.equal(a.element('duelImage').assignments,1);
});
test('duel French feedback and its minimum display time wait for the large image to load',async()=>{
 const {server,a,b}=await duelClients();await duelWindow(a,b);a.holdNextImages();await duelClose(a,b);
 assert.equal(a.players[0].starts.length,2);assert.equal(a.element('duelImage').hidden,true);a.advance(2000);b.advance(2000);b.ended();await flush();assert.equal(server.state.phase,'duel_result');
 a.releaseImages();await flush();assert.equal(a.players[0].starts.length,3);assert.equal(a.element('duelImage').hidden,false);a.ended();await flush();assert.equal(server.state.phase,'duel_result');
 a.advance(2000);await flush();assert.equal(server.state.phase,'duel_between');
});
