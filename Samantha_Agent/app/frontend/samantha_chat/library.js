(function(root){
  'use strict';
  function safeSource(value){try{if(typeof value!=='string'||/[\x00-\x1f]/.test(value))return '';const u=new URL(value);return ['http:','https:'].includes(u.protocol)&&!u.username&&!u.password?u.href:'';}catch(_){return '';}}
  function create(doc,client,act){
    const el=id=>doc.getElementById(id);let fingerprint='',epoch=0,loaded=null,pending=false,lastRequest=null;
    el('librarySearch').onclick=()=>act(()=>client.librarySearch(el('libraryQuery').value));
    el('libraryQuery').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.isComposing){e.preventDefault();act(()=>client.librarySearch(el('libraryQuery').value));}});
    async function read(id,offset=0,digest=''){
      const ticket=epoch;lastRequest={id,offset,digest};pending=true;el('libraryMore').disabled=true;
      el('libraryReadingStatus').textContent='Načítám uložený text…';
      try{
        const data=await client.libraryDetail(id,offset,digest);if(ticket!==epoch)return;
        if(data.item.id!==id||data.offset!==offset||offset&&data.sha256!==digest)throw Error('Část textu neodpovídá původní položce. Otevři ji znovu.');
        if(offset===0){el('libraryText').textContent=data.text;el('libraryTitle').textContent=data.item.title;el('libraryMeta').textContent=[data.item.content_kind,data.item.book_author,data.item.book_location].filter(Boolean).join(' · ');const url=safeSource(data.item.source_url);el('librarySource').hidden=!url;el('librarySource').href=url;}
        else el('libraryText').textContent+=data.text;
        loaded=data;el('libraryMore').textContent='Načíst další část uloženého textu';el('libraryMore').hidden=!data.more;
        el('libraryReadingStatus').textContent=!data.item.text_available?'U položky není dostupný uložený text.':`Zobrazeno ${data.next_offset} z ${data.total_chars} znaků uloženého textu.${data.more?' Další část načteš tlačítkem.':' Uložený text je zobrazený celý.'}`;
      }catch(error){if(ticket===epoch){el('libraryReadingStatus').textContent=error.message;el('libraryMore').textContent='Zkusit načtení znovu';el('libraryMore').hidden=false;}}
      finally{if(ticket===epoch){pending=false;el('libraryMore').disabled=false;}}
    }
    el('libraryMore').onclick=()=>{if(!pending&&lastRequest){const r=loaded?{id:loaded.item.id,offset:loaded.next_offset,digest:loaded.sha256}:lastRequest;void read(r.id,r.offset,r.digest);}};
    function render(c){
      const view=c.state?.library||{},next=JSON.stringify([c.token,c.state?.room_id,view]);
      el('librarySearch').disabled=!c.online||c.busy||Boolean(c.state?.busy);
      if(next===fingerprint)return;
      fingerprint=next;epoch++;loaded=null;lastRequest=null;pending=false;el('libraryResults').replaceChildren();
      el('libraryText').textContent='';el('libraryReadingStatus').textContent='';el('libraryReader').hidden=true;el('librarySource').hidden=true;el('libraryMore').hidden=true;
      el('libraryStatus').textContent=view.notice||(view.items?`${view.count} výsledků z ${view.catalog_count} položek; zobrazeno ${view.items.length}.`:'Zeptej se Samanthy na vlastní Knihovnu nebo napiš hledaný výraz.');
      if(!c.state)return;
      if(view.revision)el('libraryPanel').open=true;
      (view.items||[]).forEach((item,index)=>{
        const card=doc.createElement('div');card.className='library-card';
        if(item.image){const img=doc.createElement('img');img.alt='';img.loading='lazy';img.src='/api/library/attachment?'+new URLSearchParams({id:item.id,attachment_id:item.image.attachment_id,variant:item.image.variant});card.appendChild(img);}
        const title=doc.createElement('h3');title.textContent=`[${index+1}] ${item.title}`;card.appendChild(title);
        for(const text of [[item.category_label,item.book_author,item.book_location].filter(Boolean).join(' · '),item.preview]){const p=doc.createElement('p');p.textContent=text;card.appendChild(p);}
        const button=doc.createElement('button');button.type='button';button.textContent='Otevřít';button.onclick=()=>act(()=>client.libraryOpen(item.id));card.appendChild(button);el('libraryResults').appendChild(card);
      });
      if(view.selected_id){el('libraryReader').hidden=false;void read(view.selected_id);}
    }
    return {render};
  }
  const api={create,safeSource};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.SamanthaLibrary=api;
})(typeof window==='undefined'?globalThis:window);
