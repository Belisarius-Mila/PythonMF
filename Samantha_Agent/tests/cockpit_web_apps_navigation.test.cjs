const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const test=require('node:test');
const source=fs.readFileSync(path.join(__dirname,'../app/frontend/cockpit/app.js'),'utf8');
function setup(open=()=>null){
  class Element{constructor(tag){this.tagName=tag;this.children=[];this.events={};}appendChild(node){this.children.push(node);}addEventListener(name,fn){this.events[name]=fn;}set innerHTML(value){this.children=[];}}
  const list=new Element('div'),messages=[],errors=[],calls=[],desktop=[],scan=[];
  const context={URL,Date,document:{createElement:tag=>new Element(tag)},window:{location:{href:'https://cockpit.example.test/#servis'},open:(...args)=>{calls.push(args);return open(...args);}},webAppsList:list,showMessage:(...args)=>messages.push(args),recordFrontendError:error=>errors.push(error),openDesktopApp:app=>desktop.push(app.id),openScanDocu:()=>scan.push(true)};
  vm.runInNewContext(source.slice(source.indexOf('function webAppTargetUrl('),source.indexOf('function openJanickaModal('))+source.slice(source.indexOf('function openWebApp('),source.indexOf('function openEmailHub('))+'\nglobalThis.api={renderWebApps,openWebApp};',context);
  return {...context.api,list,messages,errors,calls,desktop,scan};
}
const app={id:'vocabulary-en',kind:'GitHub Pages',title:'Vocabulary EN',url:'https://belisarius-mila.github.io/PythonMF/vocabulary-en/'};
test('catalog web applications are native links, usable without popup JavaScript and without a reused window',()=>{
  const view=setup();view.renderWebApps([app]);const link=view.list.children[0].children[1];
  assert.equal(link.tagName,'a');assert.equal(link.target,'_blank');assert.equal(link.rel,'noopener');assert.equal(link.events.click,undefined);
  const url=new URL(link.href);assert.equal(url.origin,new URL(app.url).origin);assert.equal(url.pathname,new URL(app.url).pathname);assert.ok(url.searchParams.has('cockpit_cache'));assert.equal(view.calls.length,0);
});
test('repeated programmatic opens use a fresh target and do not inspect stale cross-origin window handles',()=>{
  const view=setup(()=>Object.defineProperty({},'location',{get(){throw Error('old window');}}));
  view.openWebApp(app);view.openWebApp(app);assert.equal(view.calls.length,2);
  for(const call of view.calls){assert.equal(new URL(call[0]).pathname,new URL(app.url).pathname);assert.deepEqual(call.slice(1),['_blank','noopener']);}
  assert.equal(view.errors.length,0);assert.equal(view.messages.length,2);assert.ok(view.messages.every(message=>message[1].startsWith(app.url)));
});
test('a blocked or throwing window open retains a clickable destination; unsupported schemes never launch',()=>{
  for(const open of [()=>null,()=>{throw Error('blocked');}]){
    const view=setup(open);assert.doesNotThrow(()=>view.openWebApp(app));assert.equal(view.messages.length,1);assert.ok(view.messages[0][1].startsWith(app.url));
  }
  const view=setup();view.openWebApp({...app,url:'javascript:alert(1)'});assert.equal(view.calls.length,0);assert.equal(view.messages[0].length,1);
});
test('desktop launch and ScanDocu remain explicit actions rather than external links',()=>{
  const view=setup();const desktop={id:'desktop',launch_type:'desktop',url:'/unused'},scan={id:'scandocu',url:'/scandocu'};view.renderWebApps([desktop,scan]);
  for(const card of view.list.children){const button=card.children[1];assert.equal(button.tagName,'button');button.events.click();}
  assert.deepEqual(view.desktop,['desktop']);assert.equal(view.scan.length,1);assert.equal(view.calls.length,0);
});
