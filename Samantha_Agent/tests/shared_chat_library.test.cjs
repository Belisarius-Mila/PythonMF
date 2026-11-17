'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const {create,safeSource}=require('../app/frontend/samantha_chat/library.js');
const settle=async()=>{for(let n=0;n<20;n++)await Promise.resolve();};
class Element{
 constructor(){this.children=[];this.textContent='';this.hidden=false;this.disabled=false;this.value='';}
 addEventListener(){} appendChild(v){this.children.push(v);} replaceChildren(){this.children=[];}
 set innerHTML(_){throw Error('HTML injection forbidden');}
}
function fixture(read){
 const elements=new Map(),doc={getElementById:id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);},createElement:()=>new Element()};
 const client={token:'synthetic-token',online:true,busy:false,state:{room_id:'room',library:{}},libraryDetail:read,librarySearch:async()=>{},libraryOpen:async()=>{}};
 const ui=create(doc,client,fn=>void fn());return {client,ui,el:doc.getElementById};
}
function item(id){return {id,title:'Synthetic '+id,category_label:'Recepty',preview:'<img src=x onerror=alert(1)>',content_kind:'Uložený text',text_available:true,source_url:'https://example.test/source'};}
function page(id,text,offset=0,more=false){return {ok:true,item:item(id),text,offset,next_offset:offset+text.length,total_chars:more?8:offset+text.length,more,sha256:'synthetic-hash'};}
function show(f,id,revision=1){f.client.state.library={revision,items:[item(id)],selected_id:id,count:1,catalog_count:4};f.ui.render(f.client);}
test('late previous item read and disconnect cannot expose the wrong text',async()=>{
 let finish;const f=fixture(async id=>id==='first'?new Promise(r=>finish=r):page(id,'SECOND'));
 show(f,'first');show(f,'second',2);await settle();assert.equal(f.el('libraryText').textContent,'SECOND');
 finish(page('first','OLD'));await settle();assert.equal(f.el('libraryText').textContent,'SECOND');
 assert.equal(f.el('libraryResults').children[0].children[2].textContent,'<img src=x onerror=alert(1)>');
 f.client.token='';f.client.state=null;f.ui.render(f.client);assert.equal(f.el('libraryText').textContent,'');assert.equal(f.el('libraryReader').hidden,true);
});
test('whole stored text is paged with original digest, including explicit retry after failure',async()=>{
 const requests=[];let fail=true;const f=fixture(async(id,offset,digest)=>{
  requests.push({id,offset,digest});if(fail){fail=false;throw Error('Synthetic offline');}
  return page(id,offset?'EFGH':'ABCD',offset,!offset);
 });
 show(f,'study');await settle();assert.match(f.el('libraryReadingStatus').textContent,/offline/);
 f.el('libraryMore').onclick();await settle();assert.equal(f.el('libraryText').textContent,'ABCD');
 f.el('libraryMore').onclick();await settle();assert.equal(f.el('libraryText').textContent,'ABCDEFGH');
 assert.deepEqual(requests.at(-1),{id:'study',offset:4,digest:'synthetic-hash'});assert.equal(f.el('libraryMore').hidden,true);
 assert.match(f.el('libraryReadingStatus').textContent,/celý/);
});
test('only credential-free HTTP sources can become clickable links',()=>{
 for(const value of ['javascript:alert(1)','data:text/html,hi','file:///private','https://user:secret@example.test','https://example.test/\nprivate'])assert.equal(safeSource(value),'');
 assert.equal(safeSource('https://example.test/source'),'https://example.test/source');
});
