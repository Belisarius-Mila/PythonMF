/* Four-picture listening rounds. Read-only learner access; no learner writes. */
(function(root){
  "use strict";
  const M=typeof module!=="undefined"&&module.exports?require("./model.js"):root.VocabularyModel;
  const KEY="vocabulary-en.picture-quiz.v1";
  const word=value=>M.normalize(value).replace(/[^a-z0-9]+/g,"");
  const homophones=["to two too","there their they're","right write","know no","i eye","for four","one won","see sea","by buy bye","where wear","here hear","sun son","flower flour","week weak"];
  const soundGroups=new Map(homophones.flatMap((group,index)=>group.split(" ").map(term=>[word(term),`homophone-${index}`])));
  function sound(item,audio){
    const value=word(M.audioRecord(item,audio)?.spokenEn || item.en);
    return soundGroups.get(value)||value;
  }
  function eligible(items,audio,catalog){
    if(catalog?.schemaVersion!==1)return [];
    return items.filter(item=>{
      const entry=catalog.entries?.[item.uid],record=M.audioRecord(item,audio);
      return M.isActive(item) && M.teachingType(item)==="word" && item.image && record?.en && entry
        && entry.en===item.en && entry.cz===item.cz && entry.image===item.image && Array.isArray(entry.conflicts)
        && ["objects","colors","numbers"].includes(entry.format);
    });
  }
  function compatible(a,b,audio,catalog){
    const left=catalog.entries[a.uid],right=catalog.entries[b.uid];
    if(!left||!right)return false;
    return left.format===right.format && a.uid!==b.uid && sound(a,audio)!==sound(b,audio) && word(a.cz)!==word(b.cz)
      && a.image.toLowerCase()!==b.image.toLowerCase()
      && (!a.imageStem || !b.imageStem || word(a.imageStem)!==word(b.imageStem))
      && !(left.conflicts || []).some(group=>(right.conflicts || []).includes(group))
      && !(a.related || []).some(link=>link.uid===b.uid) && !(b.related || []).some(link=>link.uid===a.uid);
  }
  function question(target,pool,audio,catalog,random=Math.random){
    const candidates=M.shuffle(pool.filter(item=>compatible(target,item,audio,catalog)),random);
    function fill(chosen,start){
      if(chosen.length===4)return chosen;
      for(let i=start;i<candidates.length;i++){
        if(candidates.length-i<4-chosen.length)break;
        if(chosen.every(item=>compatible(item,candidates[i],audio,catalog))){
          const result=fill([...chosen,candidates[i]],i+1);if(result)return result;
        }
      }
      return null;
    }
    const choices=fill([target],0);
    return choices?{target,choices:M.shuffle(choices,random)}:null;
  }
  function sanitize(value={},groups=[]){
    return {learner:["A","B","C","D"].includes(value.learner)?value.learner:"all",hard:value.hard===true,
      topic:groups.some(g=>g.id===value.topic)?value.topic:"",recentCount:M.recentCount(value.recentCount)};
  }
  function create({doc,win,getData,getAudio,getCatalog,getPersonal,isAvailable,onOpen,onClose,play,stop}){
    const names=["quizSetup","quizLearner","quizTopic","quizHard","quizHardLabel","quizRecentOnly","quizRecentCount","quizPoolNotice","quizStart","quizRound","quizPosition","quizReplay","quizChange","quizMessage","quizChoices","quizNext","quizEnd","quizResult","quizAgain","quizEndChange","quizBack"];
    const ui=Object.fromEntries(names.map(id=>[id,doc.getElementById(id)]));
    let filters=sanitize(),pool=[],targets=[],sequence=[],index=0,correct=0,answered=0,phase="setup",epoch=0,opened=false,current=null,buttons=[],signature="",heard=false,lastAudio=null,lastCatalog=null;
    try{filters=sanitize(JSON.parse(win.sessionStorage.getItem(KEY)||"{}"),getData().catalog.groups);}catch(_){}
    for(const group of getData().catalog.groups){const option=doc.createElement("option");option.value=group.id;option.textContent=group.label;ui.quizTopic.append(option);}
    function save(){try{win.sessionStorage.setItem(KEY,JSON.stringify(filters));}catch(_){} }
    function controls(){
      ui.quizLearner.value=filters.learner;
      ui.quizLearner.querySelectorAll("option").forEach(option=>{option.disabled=option.value!=="all"&&!isAvailable();});
      ui.quizTopic.value=filters.topic;ui.quizHard.checked=filters.hard;
      ui.quizHardLabel.textContent=filters.learner==="all"?"Jen obtížná (společný výběr)":`Jen obtížná uživatele ${filters.learner}`;
      ui.quizRecentOnly.checked=filters.recentCount>0;ui.quizRecentCount.disabled=!filters.recentCount;ui.quizRecentCount.value=String(filters.recentCount || 20);
    }
    function selection(){
      const all=getData().items;
      if(filters.learner!=="all"&&!isAvailable())return [];
      let chosen=filters.learner==="all"?all:getPersonal(filters.learner,filters.hard);
      if(filters.learner==="all"&&filters.hard)chosen=chosen.filter(item=>item.hardTraining);
      return M.select(chosen,{topics:filters.topic?[filters.topic]:[],recentCount:filters.recentCount},all);
    }
    function refresh(){
      const selected=selection(),next=eligible(selected,getAudio(),getCatalog());
      const changed=signature!==next.map(M.key).join(",");signature=next.map(M.key).join(",");pool=next;
      if(changed||lastAudio!==getAudio()||lastCatalog!==getCatalog())targets=pool.filter(item=>question(item,pool,getAudio(),getCatalog(),()=>.5));
      lastAudio=getAudio();lastCatalog=getCatalog();
      const invalidated=opened&&phase!=="setup"&&changed;
      if(invalidated)setup();
      controls();ui.quizStart.disabled=targets.length===0;
      const pending=!getAudio()||!getCatalog();
      ui.quizPoolNotice.textContent=getCatalog()===false?"Výběr obrázků pro hru se nepodařilo načíst. Obnov stránku; Přehled můžeš dál používat.":getAudio()===false?"Zvuk pro hru se nepodařilo načíst. Obnov stránku; Přehled můžeš dál používat.":filters.learner!=="all"&&!isAvailable()?"Osobní výběry nejsou dostupné. Můžeš zvolit Vše nebo obnovit stránku.":pending?"Připravuji obrázky a zvuk…":targets.length
        ? `Ve filtru ${M.countLabel(selected.length)}. Pro tuto hru ${M.countLabel(targets.length)}. Všechny čtyři možnosti budou z tohoto výběru.`
        : `Ve filtru ${M.countLabel(selected.length)}, z toho ${M.countLabel(pool.length)} s vhodným obrázkem a zvukem. Potřebujeme čtyři vzájemně odlišné možnosti. Zkus větší počet nových karet nebo širší výběr.`;
      if(invalidated){ui.quizPoolNotice.textContent="Výběr se změnil. Spusť nové kolo. "+ui.quizPoolNotice.textContent;ui.quizSetup.scrollIntoView({block:"start"});}
    }
    function setup(){
      epoch++;stop();phase="setup";current=null;buttons=[];ui.quizChoices.replaceChildren();
      ui.quizSetup.hidden=false;ui.quizRound.hidden=true;ui.quizEnd.hidden=true;
    }
    function open(){opened=true;setup();refresh();onOpen();}
    function leave(){opened=false;setup();}
    function configure(){
      const count=ui.quizRecentOnly.checked?M.recentCount(ui.quizRecentCount.value):0;
      if(ui.quizRecentOnly.checked&&!count){ui.quizPoolNotice.textContent="Počet musí být celé číslo od 1 do 5000.";ui.quizStart.disabled=true;return;}
      filters=sanitize({learner:ui.quizLearner.value,hard:ui.quizHard.checked,topic:ui.quizTopic.value,recentCount:count},getData().catalog.groups);
      save();refresh();
    }
    function message(text){ui.quizMessage.textContent=text;}
    async function speak(feedback=false){
      const ticket=++epoch,item=current?.target;if(!item)return;
      stop();
      if(!feedback){message("Poslouchej…");buttons.forEach(button=>button.disabled=true);}
      try{
        const completed=await play(item);
        if(ticket!==epoch||!opened)return;
        if(!completed)return;
        if(!feedback&&phase==="question"){heard=true;message("Vyber obrázek, který patří ke slovu.");buttons.forEach(button=>button.disabled=false);}
      }catch(_){
        if(ticket!==epoch||!opened)return;
        if(feedback)message("Správný obrázek je zvýrazněný. Zvuk se nepodařilo přehrát; můžeš ho zopakovat.");
        else {message("Zvuk se nepodařilo přehrát. Stiskni Zopakovat slovo.");buttons.forEach(button=>button.disabled=true);}
      }
    }
    function finish(){
      epoch++;stop();phase="end";current=null;ui.quizRound.hidden=true;ui.quizEnd.hidden=false;
      ui.quizResult.textContent=`Správně na první pokus: ${correct} z ${answered}.`;
      ui.quizAgain.focus({preventScroll:true});
    }
    function next(){
      epoch++;stop();
      if(index>=sequence.length){finish();return;}
      current=question(sequence[index],pool,getAudio(),getCatalog());
      if(!current){setup();refresh();return;}
      phase="loading";heard=false;buttons=[];ui.quizChoices.replaceChildren();ui.quizNext.disabled=true;ui.quizReplay.disabled=true;
      ui.quizPosition.textContent=`Slovíčko ${index+1} z ${sequence.length}`;ui.quizNext.textContent=index+1===sequence.length?"Dokončit kolo":"Další →";
      message("Připravuji čtyři obrázky…");const ticket=epoch;let loaded=0;
      for(const [number,item] of current.choices.entries()){
        const button=doc.createElement("button");button.type="button";button.className="quiz-choice";button.disabled=true;
        button.dataset.uid=item.uid;button.setAttribute("aria-label",`Vybrat obrázek ${number+1}`);
        const image=doc.createElement("img");image.alt=`Obrázek ${number+1}`;image.width=384;image.height=384;
        const caption=doc.createElement("span");caption.className="quiz-caption";caption.lang="en";caption.textContent="\u00a0";
        const mark=doc.createElement("span");mark.className="quiz-mark";mark.setAttribute("aria-hidden","true");
        button.append(image,caption,mark);ui.quizChoices.append(button);buttons.push(button);
        button.addEventListener("click",()=>answer(item.uid));
        let settled=false;
        const ready=()=>{if(settled||ticket!==epoch||!opened)return;settled=true;loaded++;if(loaded===4){phase="question";ui.quizReplay.disabled=false;void speak();}};
        image.addEventListener("load",ready,{once:true});
        image.addEventListener("error",()=>{
          if(ticket!==epoch||!opened)return;
          epoch++;stop();phase="image-error";buttons.forEach(b=>b.disabled=true);ui.quizReplay.disabled=true;ui.quizNext.disabled=false;ui.quizNext.textContent="Přeskočit otázku →";
          message("Jeden obrázek se nepodařilo načíst. Otázka se nezapočítá. Můžeš ji přeskočit nebo změnit výběr.");
        },{once:true});
        image.src=new win.URL(`../${item.thumbnail||item.image}`,win.location.href).href;
        if(image.complete&&image.naturalWidth>0)ready();
      }
      ui.quizPosition.focus({preventScroll:true});
      ui.quizRound.scrollIntoView({block:"start"});
    }
    function answer(uid){
      if(phase!=="question"||!heard||!current.choices.some(item=>item.uid===uid))return;
      phase="answered";answered++;const right=uid===current.target.uid;if(right)correct++;
      epoch++;stop();buttons.forEach(button=>{
        button.disabled=true;
        if(button.dataset.uid===current.target.uid){button.classList.add("is-correct");button.querySelector(".quiz-caption").textContent=current.target.en;button.querySelector(".quiz-mark").textContent="✓";button.setAttribute("aria-label",`Správně: ${current.target.en}`);}
        else if(button.dataset.uid===uid){button.classList.add("is-wrong");button.querySelector(".quiz-mark").textContent="×";button.setAttribute("aria-label","Nesprávný obrázek");}
      });
      message(right?"Správně! Poslechni si slovo ještě jednou.":"Tentokrát jiný obrázek. Správný je označený zeleně. Poslechni si slovo ještě jednou.");
      ui.quizNext.disabled=false;void speak(true);
    }
    function start(){
      refresh();if(!targets.length)return;
      epoch++;stop();sequence=M.shuffle(targets);index=0;correct=0;answered=0;
      ui.quizSetup.hidden=true;ui.quizRound.hidden=false;ui.quizEnd.hidden=true;next();
    }
    for(const id of ["quizLearner","quizTopic","quizHard","quizRecentOnly","quizRecentCount"])ui[id].addEventListener("change",configure);
    ui.quizRecentCount.addEventListener("input",configure);
    ui.quizStart.addEventListener("click",start);ui.quizAgain.addEventListener("click",start);
    ui.quizNext.addEventListener("click",()=>{if(!["answered","image-error"].includes(phase))return;index++;next();});
    ui.quizReplay.addEventListener("click",()=>{if(["question","answered"].includes(phase))void speak(phase==="answered");});
    for(const id of ["quizChange","quizEndChange"])ui[id].addEventListener("click",()=>{setup();refresh();ui.quizSetup.scrollIntoView({block:"start"});ui.quizLearner.focus({preventScroll:true});});
    ui.quizBack.addEventListener("click",()=>{leave();onClose();});
    refresh();
    return {open,leave,refresh,close:()=>{leave();onClose();}};
  }
  const api={KEY,eligible,compatible,question,sanitize,create};
  if(typeof module!=="undefined"&&module.exports)module.exports=api;else root.VocabularyQuiz=api;
})(globalThis);
