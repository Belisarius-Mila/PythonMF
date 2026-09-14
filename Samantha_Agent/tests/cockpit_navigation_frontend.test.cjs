const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const listeners = {};
const document = {activeElement:null,addEventListener(name,fn){(listeners[name] ||= []).push(fn);}};
class Element {
  constructor(tag='DIV', parent=null) {
    this.tagName=tag;this.parent=parent;this.children=[];if(parent)parent.children.push(this);
    this.inert=false;this.disabled=false;this.style={zIndex:''};this.attrs={};this.tabIndex=['BUTTON','INPUT'].includes(tag)?0:-1;
    const classes=new Set();this.classList={contains:x=>classes.has(x),add:x=>classes.add(x),remove:x=>classes.delete(x),toggle:(x,v)=>{if(v)classes.add(x);else classes.delete(x);}};
  }
  get isConnected(){return this===document.body||!!this.parent?.isConnected;}
  contains(e){return e===this||this.children.some(c=>c.contains(e));}
  closest(selector){if(selector==='[inert]')return this.inert?this:this.parent?.closest(selector);return this.matches(selector)?this:this.parent?.closest(selector);}
  matches(selector){return selector.split(',').map(x=>x.trim().toUpperCase()).includes(this.tagName);}
  hasAttribute(name){return name in this.attrs;}
  getClientRects(){return this.classList.contains('hidden')||(this.parent&&!this.parent.getClientRects().length)?[]:[{}];}
  querySelectorAll(selector){return this.children.flatMap(c=>[c,...c.querySelectorAll(selector)]).filter(c=>selector==='h2, h3'?['H2','H3'].includes(c.tagName):['BUTTON','INPUT','H2'].includes(c.tagName));}
  querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
  focus(){if(!this.getClientRects().length||this.closest('[inert]'))return;document.activeElement=this;for(const fn of listeners.focusin||[])fn({target:this});}
}
document.body=new Element('BODY');document.activeElement=document.body;
const header=new Element('HEADER',document.body), trigger=new Element('BUTTON',header), main=new Element('MAIN',document.body);
const protectedBackground=new Element('DIV',document.body);protectedBackground.inert=true;
const makeModal=()=>{const e=new Element('DIV',document.body);e.classList.add('hidden');const h=new Element('H2',e),first=new Element('BUTTON',e),last=new Element('BUTTON',e);return {e,h,first,last};};
const a=makeModal(),b=makeModal();let deny=false;
const context={window:{},document,MutationObserver:class{observe(){}},setTimeout(){}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../app/frontend/cockpit/navigation.js'),'utf8'),context);
const api=context.window.SamanthaNavigation.createDialogs({dialogs:[{element:a.e,close:()=>a.e.classList.add('hidden')},{element:b.e,close:()=>{if(!deny)b.e.classList.add('hidden');}}],fallbackFocus:trigger});
const key=(name,extra={})=>{const e={key:name,preventDefault(){this.defaultPrevented=true;},stopPropagation(){},...extra};for(const fn of listeners.keydown||[])fn(e);return e;};
trigger.focus();a.e.classList.remove('hidden');api.sync();assert.equal(document.activeElement,a.h);assert.equal(main.inert,true);
a.last.focus();assert.ok(key('Tab').defaultPrevented);assert.equal(document.activeElement,a.first);assert.ok(key('Tab',{shiftKey:true}).defaultPrevented);assert.equal(document.activeElement,a.last);
b.e.classList.remove('hidden');api.sync();assert.equal(api.top(),b.e);assert.equal(a.e.inert,true);assert.equal(document.activeElement,b.h);
assert.equal(key('Escape',{isComposing:true}).defaultPrevented,undefined);api.sync();assert.equal(api.top(),b.e);
deny=true;key('Escape');api.sync();assert.equal(api.top(),b.e);assert.equal(main.inert,true);
deny=false;key('Escape');api.sync();assert.equal(api.top(),a.e);assert.equal(a.e.inert,false);assert.equal(document.activeElement,a.last);
key('Escape');api.sync();assert.equal(api.top(),null);assert.equal(document.activeElement,trigger);assert.equal(main.inert,false);assert.equal(protectedBackground.inert,true);
// Activation order, rather than fixed DOM order, determines the front layer.
b.e.classList.remove('hidden');api.sync();a.e.classList.remove('hidden');api.sync();assert.equal(api.top(),a.e);assert.ok(Number(a.e.style.zIndex)>Number(b.e.style.zIndex));key('Escape');api.sync();assert.equal(api.top(),b.e);
console.log('Cockpit navigation: focus, Tab, nested Escape, denied close, composition, inert restoration and activation order OK');
