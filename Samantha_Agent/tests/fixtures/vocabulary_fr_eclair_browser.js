/* Real Eclair client, synthetic DOM/audio, and an injected HTTP transport. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {Element,storage,flush}=require('./vocabulary_fr_dom.js');
const eclair=require('../../../docs/vocabulary-fr/eclair.js');
const html=fs.readFileSync(path.resolve(__dirname,'../../../docs/vocabulary-fr/eclair.html'),'utf8');
async function browser(origin,{url=origin+'/vocabulary-fr/eclair.html',session=storage(),name='Jana',imageHold=false,fetcher,blockedStorage=false}={}){
 class Node extends Element{appendChild(node){this.append(node);return node;}select(){this.selected=true;}}
 const doc=new Node('document');doc.doc=doc;doc.hidden=false;doc.body=doc;
 doc.getElementById=id=>doc.descendants().find(n=>n.id===id);doc.createElement=tag=>new Node(tag,doc);
 for(const [,id] of html.matchAll(/\bid="([^"]+)"/g)){const n=new Node('div',doc);n.id=id;doc.append(n);}
 doc.getElementById('eclairName').value=name;doc.getElementById('eclairRounds').value='20';doc.getElementById('eclairSeconds').value='6';
 let now=0,counter=0;const timers=new Map(),events={},players=[],pendingImages=[],requests=[];
 const win={location:{href:url},performance:{now:()=>now},crypto:crypto.webcrypto,navigator:{clipboard:{writeText:async()=>{}}},
   addEventListener:(event,fn)=>(events[event]??=[]).push(fn),
   setTimeout:(fn,ms)=>{timers.set(++counter,{fn,at:now+ms});return counter;},clearTimeout:id=>timers.delete(id),
   setInterval:(fn,ms)=>{timers.set(++counter,{fn,at:now+ms,repeat:ms});return counter;},clearInterval:id=>timers.delete(id)};
 win.history={replaceState:(_a,_b,url)=>{win.location.href=new URL(url,win.location.href).toString();}};
 if(blockedStorage)Object.defineProperty(win,'sessionStorage',{get(){throw Error('storage blocked');}});else win.sessionStorage=session;
 class Audio{
  constructor(){this.handlers={};this.starts=[];this.reject=false;players.push(this);}
  load(){}pause(){}addEventListener(k,fn){this.handlers[k]=fn;}removeEventListener(k,fn){if(this.handlers[k]===fn)delete this.handlers[k];}
  play(){this.starts.push(this.src);if(this.reject)return Promise.reject(Error('audio blocked'));queueMicrotask(()=>this.handlers.ended?.());return Promise.resolve();}
 }
 class Image{decode(){return imageHold?new Promise(resolve=>pendingImages.push(resolve)):Promise.resolve();}}
 const transport=async (url,options={})=>{
  requests.push({url:String(url),payload:options.body?JSON.parse(options.body):null,token:options.headers?.Authorization});
  const run=()=>fetch(new URL(url,origin),{...options,headers:{...options.headers,...(options.method==='POST'?{Origin:origin}:{})}});
  return fetcher?fetcher(url,options,run):run();
 };
 const app=eclair.create({doc,win,fetcher:transport,AudioClass:Audio,ImageClass:Image});await app.init();
 function advance(ms){now+=ms;let count=0;while(true){const due=[...timers].filter(([,t])=>t.at<=now).sort((a,b)=>a[1].at-b[1].at);if(!due.length)break;if(++count>20000)throw Error('timer loop');const [id,t]=due[0];if(t.repeat)t.at+=t.repeat;else timers.delete(id);t.fn();}}
 return {app,doc,win,session,players,requests,events,timers,element:id=>doc.getElementById('eclair'+id),advance,
   event:(key,value={})=>(events[key]||[]).forEach(fn=>fn(value)),releaseImages:()=>pendingImages.splice(0).forEach(fn=>fn()),flush,
   close:()=>app.leave()};
}
module.exports={browser,storage,flush};
