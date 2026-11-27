const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {browser,storage,flush}=require('./fixtures/vocabulary_fr_eclair_browser.js');
const {finalText,mediaPath}=require('../../docs/vocabulary-fr/eclair.js');
const origin=process.env.ECLAIR_TEST_ORIGIN;
async function control(seconds){const r=await fetch(origin+'/test/advance',{method:'POST',body:JSON.stringify({seconds})});assert.equal(r.status,200);}
async function settle(...views){for(let n=0;n<4;n++){await Promise.all(views.map(v=>v.app.poll()));await flush();}}
async function waitPhase(phase,...views){for(let n=0;n<120;n++){await settle(...views);if(views.every(v=>v.app.state.phase===phase))return;await new Promise(r=>setTimeout(r,5));}assert.deepEqual(views.map(v=>v.app.state.phase),views.map(()=>phase));}
async function advance(ms,...views){await control(ms/1000);for(const v of views)v.advance(ms);await settle(...views);}
async function pair(t,options={}){
 const a=await browser(origin,options);t.after(()=>a.close());await a.app.enter();assert.ok(a.app.state,a.element('Status').textContent);
 const b=await browser(origin,{url:a.element('Invite').value,name:'Míla',...options.guest});t.after(()=>b.close());await b.app.enter();await settle(a,b);return [a,b];
}
async function start(a,b,waitPrepare=true){await b.app.mutate('confirm');await settle(a,b);assert.equal(a.app.state.confirmed[1],true,b.element('Status').textContent);await a.app.mutate('start');await settle(a,b);assert.notEqual(a.app.state.phase,'waiting',a.element('Status').textContent);if(waitPrepare)await waitPhase('eclair_prepare',a,b);}
function click(view,column,text){const button=view.element(column==='pronoun'?'Pronouns':'Verbs').children.find(n=>n.dataset.text===text);assert.ok(button,text);button.click();return button;}

test('pure presentation helpers keep opaque assets and tied maximum scores',()=>{
 assert.equal(mediaPath('/eclair-media/'+'a'.repeat(64)+'.mp3'),true);
 for(const s of ['https://evil.test/a.mp3','/eclair-media/../rounds.json','javascript:alert(1)'])assert.equal(mediaPath(s),false);
 assert.match(finalText({players:[{name:'A'},{name:'B'}],scores:[40,40],maxScore:40}),/Remíza/);
 const css=fs.readFileSync(path.resolve(__dirname,'../../docs/vocabulary-fr/eclair.css'),'utf8');
 assert.match(css,/\.eclair-choices\{display:grid;grid-template-columns:minmax\(0,1fr\) minmax\(0,1fr\)/);
 assert.match(css,/@media\(max-width:760px\)/);assert.match(css,/\.solved/);assert.match(css,/\.wrong/);
 assert.match(css,/@media\(min-width:761px\) and \(max-height:780px\)/);assert.match(css,/eclair-in-game \.eclair-card\{min-height:2\.1rem/);
});

test('two real HTTP clients play all20 rounds, two columns, result audio, handshake and tie',{skip:!origin},async t=>{
 const [a,b]=await pair(t);assert.equal(a.element('Start').disabled,true);assert.equal(b.element('Options').hidden,true);
 assert.equal(b.win.location.href.includes('#'),false);await start(a,b);
 assert.equal(a.app.state.phase,'eclair_prepare');assert.equal(a.element('Pronouns').children.length,0);assert.match(a.element('Prompt').textContent,/mluví/);
 assert.equal(a.doc.body.classList.contains('eclair-in-game'),true);assert.equal(a.element('InvitePanel').hidden,true);
 for(let round=1;round<=20;round++){
  await advance(2000,a,b);assert.equal(a.app.state.phase,'eclair_active');assert.equal(a.element('Pronouns').children.length,8);assert.equal(a.element('Verbs').children.length,6);
  assert.deepEqual(a.app.state.verbCards,b.app.state.verbCards);
  for(const v of [a,b]){click(v,'pronoun','elle');click(v,'verb','parle');}
  for(let n=0;n<30&&![a,b].every(v=>v.app.state.ownColumns.pronoun.solved&&v.app.state.ownColumns.verb.solved);n++){await settle(a,b);await new Promise(r=>setTimeout(r,2));}
  assert.ok([a,b].every(v=>v.app.state.ownColumns.pronoun.solved&&v.app.state.ownColumns.verb.solved),JSON.stringify([a,b].map(v=>({own:v.app.state.ownColumns,status:v.element('Status').textContent,answers:v.requests.filter(r=>r.url.endsWith('/answer')).map(r=>r.payload)}))));assert.equal(a.element('PronounNotice').textContent,'✓ Správně · +1 bod');
  assert.equal(a.app.state.phase,'eclair_active');await advance(6000,a,b);
  assert.equal(a.app.state.scores[0],round*2);assert.equal(a.app.state.scores[1],round*2);
  assert.equal(a.element('Sentence').textContent,'Il parle.');assert.match(a.element('Variant').textContent,/Elle parle/);
  if(round<20){await a.app.mutate('next');await settle(a,b);assert.equal(a.app.state.phase,'eclair_wait_guest');assert.equal(b.element('Confirm').hidden,false);await b.app.mutate('confirm');await waitPhase('eclair_prepare',a,b);}
 }
 assert.equal(a.app.state.phase,'finished');assert.match(a.element('Final').textContent,/Remíza/);
 assert.equal(a.players[0].starts.filter(x=>x.includes('/eclair-media/')).length,20);
 await a.app.mutate('rematch');await settle(a,b);await b.app.mutate('confirm');await settle(a,b);
 assert.equal(a.app.state.roundIndex,1);assert.deepEqual(a.app.state.scores,[0,0]);assert.equal(a.app.state.room,b.app.state.room);
});

test('wrong column locks for1s, other column remains live, full deadline stays authoritative',{skip:!origin},async t=>{
 const [a,b]=await pair(t);await start(a,b);await advance(2000,a,b);
 click(a,'pronoun','je');await settle(a,b);assert.equal(a.element('Pronouns').children.every(n=>n.disabled),true);
 assert.equal(a.element('Verbs').children.some(n=>!n.disabled),true);assert.match(a.element('PronounNotice').textContent,/✕/);
 click(a,'verb','parle');await settle(a,b);await advance(1000,a,b);click(a,'pronoun','il');await settle(a,b);
 assert.equal(a.app.state.phase,'eclair_active');await advance(5000,a,b);assert.deepEqual(a.app.state.scores,[2,0]);
});

test('lost answer response recovers same access without replaying the answer',{skip:!origin},async t=>{
 let lose=false,offline=false;
 const [a,b]=await pair(t,{fetcher:async(url,options,run)=>{if(offline)throw Error('offline');const response=await run();if(lose&&String(url).endsWith('/answer')){lose=false;offline=true;throw Error('lost response');}return response;}});
 await start(a,b);await advance(2000,a,b);lose=true;click(a,'verb','parle');await flush();await flush();
 await new Promise(r=>setTimeout(r,50));offline=false;a.advance(1000);await flush();await new Promise(r=>setTimeout(r,50));await settle(a,b);
 assert.equal(a.app.state.ownColumns.verb.solved,true);assert.equal(a.requests.filter(r=>r.url.endsWith('/answer')).length,1);
 await advance(6000,a,b);assert.deepEqual(a.app.state.scores,[1,0]);
});

test('result audio plays once across polls and reload, manual replay and playback failure remain usable',{skip:!origin},async t=>{
 const [a,b]=await pair(t);await start(a,b);await advance(8000,a,b);await settle(a,b);
 const count=()=>a.players[0].starts.filter(x=>x.includes('/eclair-media/')).length;
 assert.equal(count(),1);await settle(a,b);assert.equal(count(),1);
 const saved=a.session,url=a.win.location.href;a.close();await flush();
 const restored=await browser(origin,{url,session:saved});t.after(()=>restored.close());await restored.app.resume();await settle(restored,b);
 assert.equal(restored.players[0].starts.filter(x=>x.includes('/eclair-media/')).length,0);
 restored.players[0].reject=true;restored.element('Repeat').click();await flush();await flush();
 assert.match(restored.element('AudioNotice').textContent,/nepodařilo/);assert.equal(restored.element('Next').disabled,false);
});

test('reconnect backs off1/2/4/8s, returns to the same room, and permanent access errors stop retries',{skip:!origin},async t=>{
 let offline=false,denied=false;
 const [a,b]=await pair(t,{fetcher:async(url,options,run)=>{if(offline)throw Error('offline');if(denied&&String(url).endsWith('/sync'))return {ok:false,status:403,json:async()=>({error:'Přístup odmítnut.'})};return run();}});
 const room=a.app.state.room;offline=true;await a.app.poll();
 for(const delay of [1000,2000,4000,8000]){const before=a.requests.filter(r=>r.url.endsWith('/ready')).length;a.advance(delay-1);await flush();assert.equal(a.requests.filter(r=>r.url.endsWith('/ready')).length,before);a.advance(1);await flush();await flush();assert.equal(a.requests.filter(r=>r.url.endsWith('/ready')).length,before+1);}
 offline=false;a.event('online');for(let n=0;n<80&&a.element('Resume').hidden===false;n++){await flush();await new Promise(r=>setTimeout(r,2));}
 await settle(a,b);assert.equal(a.app.state.room,room);assert.equal(a.element('Resume').hidden,true);
 denied=true;await a.app.poll();const before=a.requests.length;a.advance(32000);await flush();assert.equal(a.requests.length,before);assert.match(a.element('Status').textContent,/odmítnut/);
});

test('preload barrier tolerates missing pictures and blocked session storage without blocking gameplay',{skip:!origin},async t=>{
 const [a,b]=await pair(t,{blockedStorage:true,guest:{imageHold:true}});assert.match(a.element('Storage').textContent,/nepovolil/);
 await start(a,b,false);assert.equal(a.app.state.phase,'eclair_loading');await advance(1000,a,b);assert.equal(a.app.state.phase,'eclair_loading');
 b.advance(6000);await waitPhase('eclair_prepare',a,b);assert.equal(a.app.state.phase,'eclair_prepare');await advance(2000,a,b);assert.equal(a.app.state.phase,'eclair_active');
});

test('uncertain creation keeps one request identity and leaving cancels late callbacks',{skip:!origin},async t=>{
 let lose=true;const fetcher=async(url,options,run)=>{const r=await run();if(String(url)==='/api/vocabulary-fr/rooms'&&lose){lose=false;throw Error('lost create response');}return r;};
 const view=await browser(origin,{fetcher});t.after(()=>view.close());view.element('Rounds').value='30';view.element('Seconds').value='10';
 await view.app.enter();assert.equal(view.app.state,null);view.close();
 const restored=await browser(origin,{fetcher,session:view.session});t.after(()=>restored.close());
 assert.match(restored.element('Enter').textContent,/Ověřit původní/);assert.equal(restored.element('Rounds').value,'30');assert.equal(restored.element('Seconds').value,'10');assert.equal(restored.element('Name').disabled,true);
 await restored.app.enter();assert.ok(restored.app.state);
 const creates=[...view.requests,...restored.requests].filter(r=>r.url==='/api/vocabulary-fr/rooms');assert.equal(creates.length,2);assert.equal(creates[0].payload.requestId,creates[1].payload.requestId);assert.equal(restored.app.state.settings.rounds,30);
 const before=restored.requests.length;restored.close();restored.advance(30000);await flush();assert.equal(restored.requests.length,before+1);
});

test('malformed invite and unavailable service cannot silently create a different game',async t=>{
 const invalid=await browser(origin||'http://localhost',{url:(origin||'http://localhost')+'/vocabulary-fr/eclair.html#room=bad&invite=bad'});t.after(()=>invalid.close());
 assert.equal(invalid.element('Enter').disabled,true);assert.match(invalid.element('Status').textContent,/Pozvánka/);assert.equal(invalid.requests.length,0);
 const unavailable=await browser('http://localhost',{fetcher:async()=>({ok:true,json:async()=>({protocol:1,games:['pairs','duel']})})});t.after(()=>unavailable.close());assert.equal(unavailable.element('Enter').disabled,true);assert.match(unavailable.element('Status').textContent,/zatím/);
});
