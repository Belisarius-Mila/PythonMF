const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function fixture() {
  class Element {
    constructor() { this.children=[]; this.events={}; this.value=''; this.dataset={}; }
    addEventListener(n,f) { this.events[n]=f; }
    append(...nodes) { this.children.push(...nodes); }
    replaceChildren(...nodes) { this.children=nodes; this.value=''; }
    get options() { return this.children; }
  }
  const nodes = new Map(), document = new Element(), window = new Element();
  document.getElementById = id => {if(!nodes.has(id)) nodes.set(id,new Element()); return nodes.get(id);};
  document.createElement = () => new Element();
  document.body = {dataset: {mapUrl:'/camino-api/viewer/map-data'}};
  const el = document.getElementById;
  const stats={fetches:0,tiles:0,fits:0,drawings:[], timers:new Map()};
  const map={layers:new Set(), setView(){return this;}, closePopup(){},
    fitBounds(){stats.fits++;},hasLayer(l){return this.layers.has(l);},removeLayer(l){this.layers.delete(l);}};
  const layer={addTo(){return this;},clearLayers(){stats.drawings=[];}};
  const tiles={events:{},addTo(m){stats.tiles++; m.layers.add(this);return this;},on(n,f){this.events[n]=f;}};
  const L={map:()=>map, layerGroup:()=>layer, tileLayer:(url,opts)=>{
    assert.equal(url,'https://tile.openstreetmap.org/{z}/{x}/{y}.png');
    assert.equal(opts.crossOrigin,'anonymous'); assert.equal(opts.referrerPolicy,'origin');
    return tiles;
  }};
  for(const kind of ['circleMarker','polyline']) L[kind]=(coords,opts)=>({
    bindPopup(popup){this.popup=popup;return this;},addTo(){stats.drawings.push({kind,coords,opts,popup:this.popup});return this;}
  });
  window.L=L;
  let data={points:[]}, fail=false, deferred, serial=0;
  const context={document,window,L,Option:function(text,value){this.textContent=text;this.value=value;},AbortController,
    setTimeout(fn,ms){const id=++serial;stats.timers.set(id,{fn,ms});return id;},clearTimeout(id){stats.timers.delete(id);},
    async fetch(url,opts){stats.fetches++;assert.equal(url,'/camino-api/viewer/map-data');assert.equal(opts.cache,'no-store');
      if(deferred) return new Promise(resolve=>{deferred=resolve;});
      if(fail) throw Error('offline'); return {ok:true,json:async()=>data};}};
  vm.runInNewContext(fs.readFileSync('camino/server/map_assets/map.js','utf8'),context);
  return {el,document,window,stats,map,tiles,context,
    setData(points){data={points};},setFail(v){fail=v;},defer(){deferred=true;},resolve(points){deferred({ok:true,json:async()=>({points})});deferred=null;}};
}
const point=(id,day='2026-09-25',extra={})=>({id,title:'<img src=x onerror=bad()>',day,time:'10:00:00',utc_ms:id,
  latitude:0,longitude:id/1000,accuracy_m:8,uncertain:false,connect_previous:id>1,
  href:`/camino-api/viewer/days/${day}#moment-${id}`,...extra});
const settle=()=>new Promise(resolve=>setImmediate(resolve));

test('consent, empty state, late points, grouping, text safety and stable viewport',async()=>{
  const f=fixture(); assert.equal(f.stats.fetches,0); assert.equal(f.stats.tiles,0);
  f.el('open-map').events.click(); await settle();
  assert.equal(f.stats.tiles,0); assert.match(f.el('status').textContent,/nejsou/);
  f.setData([point(1),point(2,'2026-09-25',{longitude:.001})]);
  await f.el('refresh').events.click();
  assert.equal(f.stats.fits,1); assert.equal(f.stats.drawings.filter(x=>x.kind==='circleMarker').length,1);
  const popup=f.stats.drawings.find(x=>x.kind==='circleMarker').popup;
  assert.equal(popup.children.length,3); assert.match(popup.children[1].textContent,/<img/);
  assert.equal(popup.children[1].innerHTML,undefined);
  f.setData([point(1),point(2),point(3,'2026-09-26',{connect_previous:false})]);
  await f.el('refresh').events.click(); assert.equal(f.stats.fits,1);
  f.el('day').value='2026-09-26'; f.el('day').events.change();
  assert.equal(f.stats.fits,2); assert.equal(f.stats.drawings.length,1);
  await f.el('refresh').events.click(); assert.equal(f.el('day').value,'2026-09-26');
  assert.equal(f.stats.fits,2); assert.equal(f.el('points').children.length,1);
});
test('refresh failures and revoked projection clear stale private layers and links',async()=>{
  const f=fixture(); f.setData([point(1)]);f.el('open-map').events.click();await settle();
  f.setFail(true); await f.el('refresh').events.click();
  assert.equal(f.stats.drawings.length,0);assert.equal(f.el('points').children.length,0);
  assert.equal(f.map.layers.size,0); assert.match(f.el('status').textContent,/Staré body jsou skryté/);
  f.setFail(false);f.setData([]);await f.el('refresh').events.click();assert.equal(f.stats.drawings.length,0);
});
test('hidden pages stop polling, reject in-flight stale data and refresh on return',async()=>{
  const f=fixture(); f.setData([point(1)]);f.el('open-map').events.click();await settle();
  assert.ok([...f.stats.timers.values()].some(t=>t.ms===60000));
  f.defer(); const running=f.el('refresh').events.click();
  f.document.hidden=true;f.document.events.visibilitychange();
  f.resolve([point(2)]);await running;
  assert.equal(f.stats.drawings.length,0);assert.equal(f.stats.timers.size,0);
  f.document.hidden=false;f.document.events.visibilitychange();await settle();
  assert.equal(f.stats.drawings.length,1);assert.equal(f.stats.fits,1);
  f.tiles.events.tileerror();assert.match(f.el('tile-status').textContent,/podkladu/);
  f.window.events.pagehide();assert.equal(f.stats.drawings.length,0);
  f.window.events.pageshow();await settle();assert.equal(f.stats.drawings.length,1);
});
test('diary hash opens exact card without playing media',()=>{
  const events={},details={},article={querySelector(){return details;},scrollIntoView(){this.scrolled=true;}};
  const id='moment-00000000-0000-0000-0000-000000000001';
  vm.runInNewContext(fs.readFileSync('camino/server/viewer_player.js','utf8'),{
    window:{location:{hash:'#'+id},addEventListener(n,f){events[n]=f;}},
    document:{querySelectorAll(){return [];},getElementById(key){return key===id?article:null;}}
  });
  assert.equal(details.open,true);assert.equal(article.scrolled,true);assert.ok(events.hashchange);
});
