(function(root){
  "use strict";
  function create({doc,win,data,model,onOpen,onClose,onChange}){
    const L=root.VocabularyLearners;
    const names=["settingsUser","settingsTitle","settingsMode","pinInput","pinRepeat","pinRepeatLabel","unlockButton","pinPanel","learnerEditor","settingsGroups","settingsSearch","learnerCount","saveLearner","cancelLearner","backupLearners","importLearners","learnerFile","settingsNotice","learnerNotice"];
    const ui=Object.fromEntries(names.map(id=>[id,doc.getElementById(id)]));
    const repository=L.store(()=>win.localStorage);
    let snapshot={raw:null,value:L.empty()},available=true,draft=null,baseline=null,id="A",hardMode=false,epoch=0,opened=false;
    function notice(message){ui.settingsNotice.textContent=message;}
    function load(){
      try{snapshot=repository.read();available=true;ui.learnerNotice.textContent="Výběry A–D se ukládají jen v tomto prohlížeči. Pro přenos použij zálohu.";}
      catch(error){available=false;ui.learnerNotice.textContent=error.message;}
      ui.backupLearners.disabled=!available;ui.unlockButton.disabled=!available;
    }
    function prepare(){
      epoch++;draft=null;baseline=null;ui.pinInput.value="";ui.pinRepeat.value="";ui.settingsSearch.value="";
      ui.pinPanel.hidden=false;ui.learnerEditor.hidden=true;ui.settingsUser.value=id;ui.settingsUser.disabled=hardMode;
      ui.settingsTitle.textContent=hardMode?`Obtížná slova uživatele ${id}`:`Slovní zásoba ${id}`;
      ui.importLearners.disabled=hardMode;
      ui.settingsMode.textContent=hardMode?"Zaškrtni slova, která ti dělají problém. Vybíráš jen ze své slovní zásoby.":"Zaškrtni vlastní slovní zásobu. Uložení změní pouze tohoto uživatele.";
      const exists=Boolean(snapshot.value.profiles[id].pin);
      ui.pinRepeatLabel.hidden=exists;ui.unlockButton.textContent=exists?"Odemknout úpravy":"Zvolit PIN a otevřít úpravy";
      ui.unlockButton.disabled=!available;
      notice(!available?ui.learnerNotice.textContent:exists?"Zadej svůj PIN. Běžné procvičování PIN nevyžaduje.":"Při prvním výběru si zvol PIN se 4 až 8 číslicemi. PIN se uloží spolu s výběrem.");
    }
    function close(force=false){
      if(!force&&draft&&JSON.stringify(draft)!==JSON.stringify(baseline.value.profiles[id])&&!win.confirm("Odejít bez uložení výběru?"))return false;
      epoch++;opened=false;draft=null;baseline=null;ui.pinInput.value="";ui.pinRepeat.value="";ui.settingsGroups.replaceChildren();onClose();return true;
    }
    function open(nextId="A",hard=false){
      if(opened&&!close())return;
      id=L.IDS.includes(nextId)?nextId:"A";hardMode=hard;opened=true;load();prepare();onOpen();
    }
    function counts(){
      const known=new Set(data.items.map(item=>item.uid));
      ui.learnerCount.textContent=`Vybráno ${draft.selected.filter(uid=>known.has(uid)).length} slovíček · obtížných ${draft.hard.filter(uid=>known.has(uid)).length}`;
    }
    function change(items,checked){
      epoch++;
      const key=hardMode?"hard":"selected",set=new Set(draft[key]);
      for(const item of items)checked?set.add(item.uid):set.delete(item.uid);
      draft[key]=[...set];
      if(!hardMode){const selected=new Set(draft.selected);draft.hard=draft.hard.filter(uid=>selected.has(uid));}
      synchronize();
    }
    function synchronize(){
      const chosen=new Set(draft[hardMode?"hard":"selected"]);
      ui.settingsGroups.querySelectorAll(".learner-word-check").forEach(input=>{input.checked=chosen.has(input.dataset.uid);});
      ui.settingsGroups.querySelectorAll(".learner-group-check").forEach(input=>{
        const ids=JSON.parse(input.dataset.ids),n=ids.filter(uid=>chosen.has(uid)).length;input.checked=n===ids.length;input.indeterminate=n>0&&n<ids.length;
      });counts();
    }
    function render(){
      const query=model.normalize(ui.settingsSearch.value),chosen=new Set(draft.selected);
      const items=data.items.filter(item=>(!hardMode||chosen.has(item.uid))&&(!query||model.normalize(`${item.en} ${item.cz}`).includes(query)));
      const groups=model.buckets(items,{groupBy:"topic",sort:"recommended"},data.catalog),fragment=doc.createDocumentFragment();
      for(const group of groups){
        const section=doc.createElement("section");section.className="vocab-section";
        const heading=doc.createElement("h3");heading.textContent=group.label;section.append(heading);
        const groupLabel=doc.createElement("label");groupLabel.className="check-option";
        const groupCheck=doc.createElement("input");groupCheck.type="checkbox";groupCheck.className="learner-group-check";groupCheck.dataset.ids=JSON.stringify(group.items.map(item=>item.uid));
        groupCheck.addEventListener("change",()=>change(group.items,groupCheck.checked));
        const text=doc.createElement("span");text.textContent=`Vybrat všechna zobrazená slovíčka v tématu (${group.items.length})`;groupLabel.append(groupCheck,text);section.append(groupLabel);
        const grid=doc.createElement("div");grid.className="vocab-grid";
        for(const item of group.items){
          const label=doc.createElement("label");label.className="learner-tile";
          const check=doc.createElement("input");check.type="checkbox";check.className="learner-word-check";check.dataset.uid=item.uid;check.setAttribute("aria-label",`${hardMode?"Obtížné":"Do slovní zásoby"}: ${item.en}`);
          check.addEventListener("change",()=>change([item],check.checked));
          const picture=doc.createElement("span");picture.className="tile-picture";
          if(item.thumbnail||item.image){const image=doc.createElement("img");image.alt="";image.loading="lazy";image.width=384;image.height=384;image.src=new URL(`../${item.thumbnail||item.image}`,win.location.href).href;image.addEventListener("error",()=>{image.hidden=true;picture.textContent="Bez obrázku";},{once:true});picture.append(image);}
          const en=doc.createElement("span");en.lang="en";en.textContent=item.en;
          const cz=doc.createElement("span");cz.lang="cs";cz.className="learner-translation";cz.textContent=item.cz;
          label.append(check,picture,en,cz);grid.append(label);
        }
        section.append(grid);fragment.append(section);
      }
      if(!groups.length){const text=doc.createElement("p");text.textContent=hardMode?"V tomto výběru nemáš žádná slovíčka. Nejdřív je přidej do své slovní zásoby v Nastavení.":"Žádné slovíčko neodpovídá hledání.";fragment.append(text);}
      ui.settingsGroups.replaceChildren(fragment);synchronize();
    }
    ui.unlockButton.addEventListener("click",async()=>{
      const ticket=++epoch,pin=ui.pinInput.value,repeat=ui.pinRepeat.value;ui.unlockButton.disabled=true;notice("Ověřuji PIN…");
      try{
        const current=repository.read(),profile=current.value.profiles[id];
        let record=profile.pin;
        if(record){if(!await L.verifyPin(pin,record,win.crypto))throw new Error("PIN není správný.");}
        else {if(pin!==repeat)throw new Error("Zadané PINy se neshodují.");record=await L.makePin(pin,win.crypto);}
        if(ticket!==epoch||!opened)return;
        baseline=current;draft={selected:[...profile.selected],hard:[...profile.hard],pin:record};
        ui.pinPanel.hidden=true;ui.learnerEditor.hidden=false;ui.saveLearner.textContent=hardMode?"Uložit obtížná slova":"Uložit slovní zásobu";
        notice("Úpravy se projeví až po uložení. PIN slouží jako místní pojistka, nejde o internetový účet.");render();
      }catch(error){if(ticket===epoch)notice(error.message);}
      finally{if(ticket===epoch){ui.pinInput.value="";ui.pinRepeat.value="";ui.unlockButton.disabled=!available;}}
    });
    ui.settingsUser.addEventListener("change",()=>{
      const next=ui.settingsUser.value;
      if(draft&&JSON.stringify(draft)!==JSON.stringify(baseline.value.profiles[id])&&!win.confirm("Změnit uživatele bez uložení výběru?")){ui.settingsUser.value=id;return;}
      id=L.IDS.includes(next)?next:"A";load();prepare();
    });
    ui.settingsSearch.addEventListener("input",()=>{if(draft)render();});
    ui.cancelLearner.addEventListener("click",()=>close());
    ui.saveLearner.addEventListener("click",()=>{
      if(!draft)return;
      try{
        const next={...baseline.value,profiles:{...baseline.value.profiles,[id]:draft}};
        snapshot=repository.write(next,baseline.raw);available=true;const edited=id;close(true);onChange(edited);
      }catch(error){notice(error.message);}
    });
    ui.backupLearners.addEventListener("click",()=>{
      try{
        const saved=repository.read(),blob=new win.Blob([JSON.stringify(L.backup(saved.value),null,2)],{type:"application/json"}),url=win.URL.createObjectURL(blob);
        const link=doc.createElement("a");link.href=url;link.download="Vocabulary_EN_vybery.json";doc.body.append(link);link.click();link.remove();win.setTimeout(()=>win.URL.revokeObjectURL(url),1000);
        notice("Záloha obsahuje uložené výběry A–D, bez PINů a bez neuložených úprav.");
      }catch(error){notice("Zálohu se nepodařilo připravit. "+error.message);}
    });
    ui.importLearners.addEventListener("click",()=>{if(!draft||hardMode)return;ui.learnerFile.value="";ui.learnerFile.click();});
    ui.learnerFile.addEventListener("change",async()=>{
      const file=ui.learnerFile.files?.[0];if(!file||!draft||hardMode)return;
      const ticket=epoch,target=id;
      try{
        if(file.size>1000000)throw new Error("Záloha je příliš velká.");
        const imported=L.parseBackup(await file.text());if(ticket!==epoch||!opened||!draft)return;
        const known=new Set(data.items.map(item=>item.uid)),p=imported.profiles[target],unknown=p.selected.filter(uid=>!known.has(uid)).length;
        draft={...draft,selected:[...p.selected],hard:[...p.hard]};render();
        notice(`Načtený návrh pro ${target}: ${p.selected.length} slov, ${p.hard.length} obtížných. ${unknown?`${unknown} slov zatím není v této verzi slovníku. `:""}Potvrď tlačítkem Uložit. Ostatní uživatelé i zdejší PIN zůstanou zachovaní.`);
      }catch(error){if(ticket===epoch)notice(error.message);}
      finally{if(ticket===epoch)ui.learnerFile.value="";}
    });
    win.addEventListener("storage",event=>{if(event.key!==L.KEY&&event.key!==null)return;load();onChange();});
    load();
    return {open,close,get available(){return available;},filter:(items,user,hard)=>L.selection(items,snapshot.value,user,hard)};
  }
  root.VocabularyLearnerUI={create};
})(globalThis);
