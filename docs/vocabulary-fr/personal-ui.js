(function(root){
  'use strict';
  function create({doc,win,data,model,onOpen,onClose,onChange}){
    const P=root.VocabularyFRPersonal,repository=P.store(()=>win.localStorage);
    const ids=['personalNotice','personalCount','personalGroups','personalSearch','personalSave','personalBack','personalImport','personalFile','personalExport','personalImportMode','personalImportPanel','personalPreview','personalUnknown','personalUnknownConfirm'];
    const ui=Object.fromEntries(ids.map(id=>[id,doc.getElementById(id)]));
    let snapshot={raw:null,value:P.empty()},baseline=null,draft=null,available=true,opened=false,epoch=0,imported=null,importBase=null;
    const notice=text=>{ui.personalNotice.textContent=text;};
    const dirty=()=>draft&&baseline&&JSON.stringify(draft)!==JSON.stringify(baseline.value);
    function load(){
      try{snapshot=repository.read();available=true;}
      catch(error){available=false;notice(error.message);}
      doc.getElementById('personalStorageNotice').textContent=available?'Označení zůstává v tomto prohlížeči. Na jiné zařízení ho přeneseš souborem.':'Osobní označení nelze načíst. Zobrazuje se celý slovník; uložená data nepřepisuji.';
    }
    function clearImport(){imported=null;importBase=null;ui.personalImportPanel.hidden=true;ui.personalImportMode.value='';ui.personalUnknownConfirm.checked=false;}
    function sync(){
      if(!draft)return;
      const hard=new Set(draft.hard),active=data.items.filter(model.isActive),missing=P.unknown(draft,data.items);
      ui.personalCount.textContent=`${active.length} slov celkem · ${active.filter(i=>hard.has(i.uid)).length} obtížných${missing.length?` · ${missing.length} neznámých UID zachováno`:''}`;
      ui.personalGroups.querySelectorAll('.personal-word-check').forEach(input=>{input.checked=hard.has(input.dataset.uid);});
      ui.personalUnknown.hidden=!missing.length;ui.personalUnknown.textContent=missing.length?`Neznámá UID (${missing.length}): ${missing.slice(0,50).join(', ')}${missing.length>50?' …':''}. Zůstanou v záloze a zatím se nezobrazí ve slovníku.`:'';
      doc.getElementById('personalUnknownLabel').hidden=!missing.length;
      ui.personalSave.disabled=!available||(Boolean(imported)&&!ui.personalImportMode.value)||(missing.length>0&&!ui.personalUnknownConfirm.checked);
      ui.personalImport.disabled=ui.personalExport.disabled=!available;
    }
    function render(){
      if(!draft)return;
      const query=model.normalize(ui.personalSearch.value),items=data.items.filter(i=>model.isActive(i)&&(!query||model.normalize(`${i.fr} ${i.cz}`).includes(query)));
      const fragment=doc.createDocumentFragment();
      for(const group of model.buckets(items,{groupBy:'topic',sort:'recommended'},data.catalog)){
        const section=doc.createElement('section');section.className='vocab-section';
        const heading=doc.createElement('h2');heading.textContent=`${group.label} · ${group.items.length}`;section.append(heading);
        const grid=doc.createElement('div');grid.className='vocab-grid';
        for(const item of group.items){
          const label=doc.createElement('label');label.className='learner-tile';
          const input=doc.createElement('input');input.type='checkbox';input.className='personal-word-check';input.dataset.uid=item.uid;input.disabled=!available;input.setAttribute('aria-label',`Obtížné: ${item.fr} — ${item.cz}`);
          input.addEventListener('change',()=>{
            epoch++;clearImport();const set=new Set(draft.hard);input.checked?set.add(item.uid):set.delete(item.uid);draft={...P.empty(),hard:[...set]};notice('Neuložené změny. Potvrď je tlačítkem Uložit.');sync();
          });
          const picture=doc.createElement('span');picture.className='tile-picture';
          const image=doc.createElement('img');image.alt='';image.loading='lazy';image.width=384;image.height=384;image.src=new URL(`../${item.thumbnail||item.image}`,win.location.href).href;picture.append(image);
          const fr=doc.createElement('span');fr.lang='fr';fr.textContent=item.fr;
          const cz=doc.createElement('span');cz.lang='cs';cz.className='learner-translation';cz.textContent=item.cz;
          label.append(input,picture,fr,cz);grid.append(label);
        }
        section.append(grid);fragment.append(section);
      }
      if(!items.length){const p=doc.createElement('p');p.textContent='Žádné slovíčko neodpovídá hledání.';fragment.append(p);}
      ui.personalGroups.replaceChildren(fragment);sync();
    }
    function open(){
      if(opened)return;
      epoch++;load();baseline=snapshot;draft=P.validate(snapshot.value);opened=true;ui.personalSearch.value='';clearImport();onOpen();render();
      if(available)notice('Zaškrtni obtížná slova nad celým slovníkem. Změny se projeví až po Uložit.');
    }
    function close(){
      if(dirty()&&!win.confirm('Odejít bez uložení obtížných slov?'))return false;
      epoch++;opened=false;draft=null;baseline=null;clearImport();ui.personalGroups.replaceChildren();onClose();return true;
    }
    function preview(){
      if(!imported)return;
      const mode=ui.personalImportMode.value;
      if(mode)draft=P.proposal(importBase,imported,mode);
      else draft=P.validate(importBase);
      ui.personalUnknownConfirm.checked=false;
      ui.personalPreview.textContent=`Soubor: ${imported.hard.length} označení. ${mode?`${mode==='add'?'Přidání':'Nahrazení'}: výsledkem je ${draft.hard.length} označení. Potvrď tlačítkem Uložit.`:'Zvol Přidat ke stávajícím, nebo Nahradit stávající. Zatím se nic neuložilo.'}`;
      render();
      // Admit unknown IDs in the file even before a mode is selected.
      if(!mode){const missing=P.unknown(imported,data.items);if(missing.length){ui.personalUnknown.hidden=false;ui.personalUnknown.textContent=`Soubor obsahuje ${missing.length} neznámých UID: ${missing.slice(0,50).join(', ')}. Při importu zůstanou zachovaná.`;}}
    }
    ui.personalSearch.addEventListener('input',render);
    ui.personalBack.addEventListener('click',close);
    ui.personalUnknownConfirm.addEventListener('change',sync);
    ui.personalImportMode.addEventListener('change',()=>{epoch++;try{preview();}catch(error){ui.personalSave.disabled=true;notice(error.message);}});
    ui.personalImport.addEventListener('click',()=>{ui.personalFile.value='';ui.personalFile.click();});
    ui.personalFile.addEventListener('change',async()=>{
      const file=ui.personalFile.files?.[0];if(!file||!opened||!available)return;
      const ticket=++epoch;
      try{
        if(file.size>P.MAX_BYTES)throw Error('Soubor je příliš velký.');
        const value=P.parse(await file.text());if(ticket!==epoch||!opened)return;
        imported=value;importBase=P.validate(draft);ui.personalImportMode.value='';ui.personalImportPanel.hidden=false;notice('Načtený soubor je pouze návrh. Uložená označení se nezměnila.');preview();
      }catch(error){if(ticket===epoch)notice(`Soubor nebyl načten: ${error.message} Předchozí návrh je zachovaný.`);}
      finally{if(ticket===epoch)ui.personalFile.value='';}
    });
    ui.personalSave.addEventListener('click',()=>{
      if(!opened||!draft||ui.personalSave.disabled)return;
      try{
        snapshot=repository.write(draft,baseline.raw);baseline=snapshot;draft=P.validate(snapshot.value);epoch++;clearImport();render();onChange();notice('Uloženo v tomto prohlížeči.');
      }catch(error){notice(error.message);}
    });
    ui.personalExport.addEventListener('click',()=>{
      try{
        const value=repository.read().value,blob=new win.Blob([JSON.stringify(value,null,2)],{type:'application/json'}),url=win.URL.createObjectURL(blob);
        const link=doc.createElement('a');link.href=url;link.download='Vocabulary_FR_Jana_obtizna.json';doc.body.append(link);link.click();link.remove();win.setTimeout(()=>win.URL.revokeObjectURL(url),1000);
        notice('Export obsahuje aktuálně uložená označení. Neuložené úpravy v něm nejsou.');
      }catch(error){notice(`Export se nepodařilo připravit: ${error.message}`);}
    });
    win.addEventListener('storage',event=>{
      if(event.key!==P.KEY&&event.key!==null)return;
      epoch++;
      if(opened&&(dirty()||imported)){notice('Označení změnilo jiné okno. Tvůj návrh zůstává otevřený; před uložením načti aktuální stav.');return;}
      load();if(opened){baseline=snapshot;draft=P.validate(snapshot.value);render();}onChange();
    });
    load();return {open,close,get available(){return available;},get isOpen(){return opened;},filter:(items,hard)=>P.selection(items,snapshot.value,hard)};
  }
  root.VocabularyFRPersonalUI={create};
})(globalThis);
