"""Same-origin read-only translation window; refreshing never sends a model turn."""
PAGE = """<!doctype html><html lang="cs"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ScienceNews — překlad</title><style>
body{max-width:850px;margin:auto;padding:24px;font:18px/1.6 system-ui;color:#172033}
pre{white-space:pre-wrap;font:inherit}a{overflow-wrap:anywhere}</style>
<h1>Český překlad zprávy</h1><p id="status" role="status">Ověřuji stav překladu…</p>
<a id="source" target="_blank" rel="noopener noreferrer"></a><pre id="text"></pre>
<script>
const id = new URLSearchParams(location.search).get('id');
let started = Date.now();
async function poll(){
 try{
  const response=await fetch('/api/science-news/translation?id='+encodeURIComponent(id));
  const data=await response.json();
  if(!response.ok||!data.ok)throw new Error(data.message||'Stav není ověřený.');
  if(data.state==='completed'){
   document.querySelector('h1').textContent=data.title;
   document.getElementById('text').textContent=data.translation;
   const url=new URL(data.source_url);
   if(url.protocol==='https:'&&!url.username&&!url.password){
    document.getElementById('source').href=url.href;
    document.getElementById('source').textContent='Otevřít původní zprávu';
   }
   document.getElementById('status').textContent='Český překlad zdrojové zprávy.';return;
  }
  if(data.state==='attention'||Date.now()-started>240000)throw new Error('Překlad vyžaduje ověření. Další pokus se automaticky nespustí.');
  document.getElementById('status').textContent=data.state==='not_started'?'Překlad zatím nebyl zahájen. Podrobnosti najdeš u zprávy v Cockpitu.':'Připravuji překlad…';
  if(data.state!=='not_started'||Date.now()-started<10000)setTimeout(poll,2000);
 }catch(error){document.getElementById('status').textContent=error.message;}
}
poll();</script></html>"""
