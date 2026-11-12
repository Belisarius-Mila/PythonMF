const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const html = JSON.parse(fs.readFileSync(0, 'utf8'));
function between(start, end) {
  const a = html.indexOf(start), b = html.indexOf(end, a + start.length);
  assert(a >= 0 && b > a, `missing ${start}`);
  return html.slice(a, b);
}
let document;
class Element {
  constructor(tag='div') {
    this.tagName = tag.toUpperCase(); this.children = []; this.parentNode = null;
    this.attributes = {}; this.dataset = {}; this.hidden = false; this.open = false;
    this.style = {setProperty:(key,value)=>{this.style[key]=value;}};
    this._text = ''; this.value = ''; this.scrollHeight = 1000; this.scrollTop = 0; this.clientHeight = 300;
    this.classList = {toggle(){},contains(){return false;}};
  }
  set textContent(value) { this._text = String(value); this.children.forEach(c=>c.parentNode=null); this.children=[]; }
  get textContent() { return this._text + this.children.map(c=>c.textContent).join(''); }
  get options() { return this.querySelectorAll('option'); }
  appendChild(child) { return this.insertBefore(child, null); }
  append(...children) { children.forEach(c=>this.appendChild(c)); }
  insertBefore(child, before) {
    if (child.parentNode) child.remove();
    const index = before ? this.children.indexOf(before) : this.children.length;
    this.children.splice(index, 0, child); child.parentNode = this; return child;
  }
  remove() { if(this.parentNode) { const p=this.parentNode; p.children.splice(p.children.indexOf(this),1); this.parentNode=null; } }
  replaceChildren(...children) { this.textContent=''; this.append(...children); }
  contains(child) { return this===child || this.children.some(c=>c.contains(child)); }
  setAttribute(key,value) { this.attributes[key]=value; }
  addEventListener() {}
  focus() { document.activeElement=this; }
  querySelectorAll(selector) {
    const all=[];
    const visit=node=>{for(const child of node.children) {if(selector.startsWith('.') ? child.className===selector.slice(1) : child.tagName===selector.toUpperCase())all.push(child);visit(child);}};
    visit(this); return all;
  }
}
const elements = new Map();
document = {
  getElementById(name) { if(!elements.has(name))elements.set(name,new Element());return elements.get(name); },
  createElement:tag=>new Element(tag),
  createTextNode:text=>{const n=new Element('#text');n.textContent=text;return n;},
  documentElement:new Element('html'), activeElement:null,
};
const names=['workStateBox','workStateTitle','workStateDescription','workStateElapsed','workStateAxes',
  'projectContinuityReasons','projectContinuityMeta','developmentProject','developmentHandoff','workStateObserved','workStateEvidence','mobileStatusText','mobileStatusSummary','input','chat','latestAnswerBtn'];
const scope=Object.fromEntries(names.map(name=>[name,document.getElementById(name)]));
Object.assign(scope,{
  document,URL,console,currentWorkState:null,statusReadSequence:0,workReadSequence:0,
  activeWorkstreamId:'project-current',activeWorkstreamLabel:'Aktuální projekt',
  deliveryUncertain:false,sendInFlight:false,sessionTurnBusy:false,lastSession:null,
  renderedExchanges:new Map(),chatRenderKey:'',chatRenderedThread:'',imageCandidatesByMessage:new Map(),
  activeSpeechButton:null,stopCount:0,activeWorkView:'Current',
  reconcilePendingSubmission(){},syncControls(){},projectContinuity:null,
  stopAnswerSpeech(){scope.stopCount++;scope.activeSpeechButton=null;},
  answerSpeechControl:()=>new Element('button'),
  imageCandidateStatus:()=> 'Návrh',
  formatTime:value=>value || 'čas neuveden',
  requestAnimationFrame:fn=>fn(),
  window:{location:{href:'https://samantha.example/human-adam/'},innerHeight:800,
    setTimeout:fn=>{fn();return 1;},visualViewport:null},
});
const source=[
  between('function publicationTargetLabel','function elapsedClock'),
  between('function elapsedClock','function stopTurnTimer'),
  between('function safeAnswerLink','function workspaceRequiresWorkDetail'),
  between('function imageCandidateCard','async function prepareImageCandidate'),
  between('async function api(path','async function loadStatus'),
  between('async function connect()','function scrollTvbcpToEnd'),
  between('function updateComposerLayout','function showPanel'),
  between('function updateDevelopmentHandoffs','async function loadProjectContinuity'),
].join('\n');
vm.createContext(scope);vm.runInContext(source,scope);
const run=code=>vm.runInContext(code,scope);
function tags(node,tag){return node.querySelectorAll(tag);}
const session={thread_id:'thread-current',connection_generation:2,messages:[]};
const state={schema_version:1,read_only:true,writes_performed:false,consistent:true,
  scope:{workstream_id:'project-current',thread_id:'thread-current',connection_generation:2},
  summary:{state:'ready'},connection:{state:'connected'},model:{state:'idle'},completion:{state:'none'},
  publication:{state:'recorded',outcome:'unverified'},history:[],incidents:[],observed_at:'2026-11-12T12:00:00Z'};
(async()=>{
  scope.session=session;scope.state=structuredClone(state);
  run('renderWorkState(state,session)');
  assert.equal(scope.mobileStatusText.textContent,'Připojeno · Adam čeká na zadání');
  scope.state.summary.state='verifying';scope.state.completion.state='verifying';
  run('renderWorkState(state,session)');
  assert.match(scope.workStateTitle.textContent,/Ověřuji výsledek/);
  assert.match(scope.mobileStatusText.textContent,/Ověřuji výsledek/);
  for(const mutate of [s=>s.scope.workstream_id='other',s=>s.scope.thread_id='other',
    s=>s.scope.connection_generation=1,s=>s.read_only=false,s=>s.writes_performed=true,s=>s.consistent=false]){
    scope.state=structuredClone(state);mutate(scope.state);run('renderWorkState(state,session)');
    assert.equal(scope.currentWorkState,null);assert.match(scope.workStateTitle.textContent,/není ověřen/);
  }
  scope.state=structuredClone(state);scope.state.summary.state='unverified';scope.state.incidents=[{source:'completion',code:'source_unavailable'}];
  run('renderWorkState(state,session)');assert.match(scope.workStateAxes.textContent,/Dokončování: neověřeno/);
  assert(!scope.workStateAxes.textContent.includes('Dokončování: neprobíhá'));
  scope.state=structuredClone(state);scope.state.summary.state='running';scope.state.model={state:'running',operation:{started_at:'2026-11-12T12:00:00Z'}};
  scope.state.incidents=[{code:'receipt_attention'}];
  run('renderWorkState(state,session)');
  assert.equal(scope.workStateTitle.textContent,'Adam pracuje');
  assert.match(scope.workStateEvidence.textContent,/účtenka vyžaduje kontrolu/);
  assert(!scope.mobileStatusText.textContent.includes('účtenka'));
  scope.currentWorkState=null;scope.sessionTurnBusy=true;run('updateMobileStatusSummary()');
  assert.match(scope.mobileStatusText.textContent,/Stav práce není ověřen/,'stale busy flag cannot assert running work');scope.sessionTurnBusy=false;
  scope.deliveryUncertain=true;run('updateMobileStatusSummary()');
  assert.match(scope.mobileStatusText.textContent,/neposílej znovu/);scope.deliveryUncertain=false;
  scope.state.publication={state:'recorded',outcome:'deployment_verified',verified_head:'a'.repeat(40),operation:{deployment_target:'github_pages'}};
  run('renderWorkState(state,session)');
  assert.match(scope.workStateEvidence.textContent,/dodatečně ověřeno/);
  assert.match(scope.workStateEvidence.textContent,/Web projektu \(GitHub Pages\)/);
  assert.equal(run('publicationTargetLabel("cockpit")'),'Cockpit Samanthy');
  assert.equal(run('publicationTargetLabel("other")'),'Cíl nasazení neověřen');

  scope.text='# Výsledek\n\n- **Hotovo**\n- [Zdroj](https://example.com/a)\n\n```js\n<script>bad()</script>\n```\n\n<img src=x onerror=bad()>\n[Zlé](javascript:bad) [Data](data:text/html,bad) https://example.com/next.';
  const answer=run('answerContent(text)');
  assert.equal(tags(answer,'h3').length,1);assert.equal(tags(answer,'ul').length,1);
  assert.equal(tags(answer,'strong')[0].textContent,'Hotovo');
  assert.equal(tags(answer,'a').length,2);assert.equal(tags(answer,'script').length,0);assert.equal(tags(answer,'img').length,0);
  assert.equal(tags(answer,'pre')[0].textContent,'<script>bad()</script>\n');
  assert(answer.textContent.includes('<img src=x onerror=bad()>'));
  for(const a of tags(answer,'a')){assert.equal(a.rel,'noopener noreferrer');assert(a.href.startsWith('https://'));}
  for(const value of ['javascript:bad','data:text/html,bad','file:///tmp/a','//evil.example','https://user:pass@example.com','https://example.com/\nwrong']){
    scope.link=value;assert.equal(run('safeAnswerLink(link)'),'');
  }
  scope.link='/api/private/artifact';assert.equal(run('safeAnswerLink(link)'),'https://samantha.example/api/private/artifact');
  scope.long='Dlouhé zadání. '.repeat(100);
  const prompt=run('bubble(long,"human","čas")');
  assert.equal(tags(prompt,'details').length,1);assert.equal(tags(prompt,'details')[0].open,false);
  assert.equal(tags(prompt,'div')[0].textContent,scope.long);
  scope.candidate={version:1,status:'generated',prompt:'Původní celý prompt',parameters:{}};
  const card=run('imageCandidateCard(candidate)');assert.equal(tags(card,'details')[0].open,false);
  assert(card.textContent.includes('Původní celý prompt'));

  scope.session={...session,messages:[{client_message_id:'m1',user_text:scope.long,answer:scope.text,delivery_confirmed:true,status:'completed'}]};
  run('renderSession(session)');
  const original=scope.chat.children[0], originalPrompt=tags(original,'details')[0];originalPrompt.open=true;
  const replyButton=tags(original,'button')[0];replyButton.focus();scope.activeSpeechButton=replyButton;
  const stops=scope.stopCount;scope.chat.scrollTop=0;
  scope.session=structuredClone(scope.session);run('renderSession(session)');
  assert.equal(scope.chat.children[0],original);assert.equal(document.activeElement,replyButton);
  assert.equal(originalPrompt.open,true);assert.equal(scope.stopCount,stops);assert.equal(scope.chat.scrollTop,0);
  scope.session.messages.push({client_message_id:'m2',user_text:'Další dotaz',status:'pending'});run('renderSession(session)');
  assert.equal(scope.chat.children[0],original);assert.equal(scope.stopCount,stops);assert.equal(scope.chat.scrollTop,0);
  scope.session={...scope.session,thread_id:'another-thread',messages:[]};run('renderSession(session)');
  assert.equal(scope.chat.children.length,1);assert.match(scope.chat.textContent,/Zatím tu není/);assert(scope.stopCount>stops);

  run('renderProjectContinuity(null)');assert.match(scope.projectContinuityMeta.textContent,/nelze bezpečně ověřit/);
  assert.equal(scope.developmentProject.options.length,1);
  run('setWorkView("Results",true)');
  assert.equal(document.getElementById('workViewResults').hidden,false);
  assert.equal(document.getElementById('workViewCurrent').hidden,true);
  assert.equal(document.getElementById('workTabResults').tabIndex,0);
  assert.equal(document.activeElement,document.getElementById('workTabResults'));
  run('setWorkView("Service")');assert.equal(document.getElementById('workViewService').hidden,false);
  run('setWorkView("invalid")');assert.equal(document.getElementById('workViewCurrent').hidden,false);
  scope.window.visualViewport={height:400,offsetTop:60};scope.input.scrollHeight=800;scope.chat.scrollTop=0;
  run('updateComposerLayout()');assert.equal(scope.input.style.height,'100px');assert.equal(scope.chat.scrollTop,0);
  assert.equal(document.documentElement.style['--ha-viewport-height'],'400px');
  assert.equal(document.documentElement.style['--ha-viewport-top'],'60px');

  const pending=[];scope.fetch=(path,options)=>new Promise((resolve,reject)=>pending.push({path,options,resolve,reject}));
  const request=()=>run('api("/api/human-adam/status")').then(value=>({value}),error=>({error}));
  const resolve=(i,value)=>pending[i].resolve({ok:true,json:async()=>value});
  const old=request(),newer=request();resolve(1,{which:'new'});assert.equal((await newer).value.which,'new');
  resolve(0,{which:'old'});assert.equal((await old).error.staleStatus,true);
  const foreign=request();scope.activeWorkstreamId='different';resolve(2,{});assert.equal((await foreign).error.staleStatus,true);
  scope.activeWorkstreamId='project-current';const beforeWrite=request();
  const write=run('api("/api/human-adam/profile",{method:"POST",body:"{}"})');
  resolve(3,{});assert.equal((await beforeWrite).error.staleStatus,true);resolve(4,{ok:true});await write;
  assert.equal(pending.filter(p=>p.options.method==='POST').length,1,'read generation must never duplicate a write');
  assert(pending.filter(p=>p.path.endsWith('/status')).every(p=>!p.options.method),'all status requests stay read-only');
  const workRequest=()=>run('api("/api/human-adam/workspace")').then(value=>({value}),error=>({error}));
  const workOld=workRequest(),workNew=workRequest();resolve(6,{which:'new work'});assert.equal((await workNew).value.which,'new work');
  resolve(5,{});assert.equal((await workOld).error.staleWork,true);
  const foreignWork=workRequest();scope.activeWorkstreamId='other';resolve(7,{});assert.equal((await foreignWork).error.staleWork,true);
  scope.activeWorkstreamId='project-current';
  const failedOld=request();const fresh=request();pending[8].reject(Error('old transport failure'));assert.equal((await failedOld).error.staleStatus,true);
  resolve(9,{ok:true});await fresh;
  const malformedOld=workRequest();const newerWork=workRequest();
  pending[10].resolve({ok:true,json:async()=>{throw Error('old malformed JSON');}});
  assert.equal((await malformedOld).error.staleWork,true);resolve(11,{ok:true});await newerWork;
  scope.setBusy=value=>{scope.busy=value;};scope.notice=new Element();scope.busy=false;
  scope.renderStatus=()=>{};
  for(const unavailable of [false,true]){
    const calls=[];scope.api=async(path,options={})=>{calls.push({path,options});
      if(path==='/api/human-adam/connect')return {ok:true};
      if(unavailable)throw Error('synthetic status read failure');
      return {ok:true,work_state:state};
    };
    await run('connect()');
    assert.equal(calls.length,2);assert.equal(calls.filter(call=>call.options.method==='POST').length,1);
    assert.equal(calls[1].path,'/api/human-adam/status');assert.equal(scope.busy,false);
    if(unavailable){assert.match(scope.notice.textContent,/Aktuální stav práce se nepodařilo ověřit/);assert(!scope.notice.textContent.includes('Připojení selhalo'));}
  }
  console.log('HA-02 PASS: scoped state, safe links/markup, collapsed prompts, stable focus/speech/scroll, views, viewport and stale reads');
})().catch(error=>{console.error(error);process.exitCode=1;});
