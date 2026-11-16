/* Italian spelling -> sound -> picture. All learner state is read-only. */
(function(root){
  "use strict";
  const M=typeof module!=="undefined"&&module.exports?require("./model.js"):root.VocabularyITModel;
  const norm=value=>M.normalize(value).replace(/[^a-z0-9]/g,"");
  function record(item,catalog){
    const r=catalog?.schemaVersion===1&&catalog.language==="it"&&catalog.kind==="spelling-pictures"?catalog.entries?.[item?.uid]:null;
    return r&&r.uid===item.uid&&r.it===item.it&&r.cz===item.cz&&r.image===item.image&&r.thumbnail===item.thumbnail
      &&Array.isArray(r.pieces)&&r.pieces.length>0&&r.pieces.length<=120&&r.pieces.every(p=>typeof p==="string"&&p.length>0)&&r.pieces.join("")===item.it
      &&Array.isArray(r.conflicts)&&r.conflicts.every(p=>typeof p==="string")&&["colors","objects"].includes(r.format)
      &&((r.reviewed===true&&r.displayMode==="syllables")||(r.reviewed===false&&r.displayMode==="whole-word"&&r.pieces.length===1))?r:null;
  }
  function eligible(items,audio,catalog){return items.filter(item=>M.isActive(item)&&item.image&&item.thumbnail&&M.audioRecord(item,audio)?.it&&record(item,catalog));}
  function meanings(value){return value.split(/[,;/]/).map(part=>norm(part.replace(/\([^)]*\)/g,""))).filter(Boolean);}
  function compatible(a,b,catalog){
    const x=record(a,catalog),y=record(b,catalog);
    return Boolean(x&&y&&M.isActive(a)&&M.isActive(b)&&a.uid!==b.uid&&norm(a.it)!==norm(b.it)&&a.image.toLowerCase()!==b.image.toLowerCase()
      &&x.format===y.format&&!meanings(a.cz).some(v=>meanings(b.cz).includes(v))
      &&!x.conflicts.some(group=>y.conflicts.includes(group))
      &&!(a.related||[]).some(link=>link.uid===b.uid)&&!(b.related||[]).some(link=>link.uid===a.uid));
  }
  function question(target,pool,catalog,random=Math.random){
    if(!M.isActive(target)||!record(target,catalog)||!pool.some(i=>i.uid===target.uid))return null;
    const candidates=M.shuffle(pool.filter(item=>compatible(target,item,catalog)),random);
    function fill(chosen,start){
      if(chosen.length===4)return chosen;
      for(let n=start;n<candidates.length;n++){
        if(candidates.length-n<4-chosen.length)break;
        if(chosen.every(i=>compatible(i,candidates[n],catalog))){const found=fill([...chosen,candidates[n]],n+1);if(found)return found;}
      }
      return null;
    }
    const choices=fill([target],0);return choices?{target,choices:M.shuffle(choices,random)}:null;
  }
  function create({doc,win,getData,getAudio,getCatalog,getSelection,getContext,onOpen,onClose,play,stop}){
    const ids=["quizSetup","quizStart","quizPoolNotice","quizSelection","quizSetupChange","quizRound","quizPosition","quizReplay","quizChange","quizMessage","quizChoices","quizNext","quizEnd","quizResult","quizAgain","quizErrors","quizEndChange","quizBack","practiceStrip","practiceWord","practiceNote","practiceHero","practiceHeroImage","practiceHeroWord","practiceHeroCz"];
    const ui=Object.fromEntries(ids.map(id=>[id,doc.getElementById(id)]));
    let opened=false,phase="setup",epoch=0,timers=new Set(),pool=[],targets=[],queue=[],index=0,current=null,buttons=[],mistakes=new Map(),firstCorrect=0,answered=0,repeated=0,skipped=0,initialCount=0,signature="",reviewRun=false,lastAudio=null,lastCatalog=null;
    function later(fn,ms){const id=win.setTimeout(()=>{timers.delete(id);fn();},ms);timers.add(id);return id;}
    function cancel(){epoch++;for(const id of timers)win.clearTimeout(id);timers.clear();stop();}
    function message(text){ui.quizMessage.textContent=text;}
    function setup(){cancel();phase="setup";current=null;buttons=[];ui.quizSetup.hidden=false;ui.quizRound.hidden=true;ui.quizEnd.hidden=true;ui.quizChoices.replaceChildren();}
    function refresh(){
      if(!opened)return;
      const chosen=getSelection(),audio=getAudio(),catalog=getCatalog();
      const next=eligible(chosen,audio,catalog),nextSignature=chosen.map(M.key).join(",");
      if(signature!==nextSignature||lastAudio!==audio||lastCatalog!==catalog){
        if(opened&&!["setup","end"].includes(phase))setup();
        signature=nextSignature;pool=next;lastAudio=audio;lastCatalog=catalog;targets=pool.filter(item=>question(item,pool,catalog,()=>.5));
      }
      const context=getContext(),labels=(context.topics||[]).map(id=>getData().groups.find(g=>g.id===id)?.label).filter(Boolean);
      ui.quizSelection.textContent=[context.learner!=="all"?`Uživatel ${context.learner}${context.onlyLearnerHard?" · obtížná slova":""}`:"Společná slovní zásoba",labels.join(" + "),(context.parts||[]).map(id=>M.posLabels[id]||id).join(" + "),(context.levels||[]).map(id=>M.levelLabels[id]||id).join(" + "),context.teachingType!=="all"?M.teachingTypeLabels[context.teachingType]:"",context.query?`Hledání: ${context.query}`:"",context.recentCount?`Posledních ${context.recentCount}`:""].filter(Boolean).join(" · ");
      ui.quizStart.disabled=!targets.length;
      ui.quizPoolNotice.textContent=audio===false?"Italský zvuk se nepodařilo načíst. Obnov stránku; přehled zůstává dostupný.":catalog===false?"Podklady procvičování se nepodařilo načíst. Obnov stránku; přehled zůstává dostupný.":!audio||!catalog?"Připravuji slova, obrázky a zvuk…":targets.length
        ?`Ve výběru ${M.countLabel(chosen.length)}. Procvičit lze ${M.countLabel(targets.length)}. Všechny čtyři možnosti budou z tvého výběru.`
        :`Ve výběru ${M.countLabel(chosen.length)}. Potřebujeme čtyři vzájemně odlišné obrázky s připraveným slovem a zvukem. Rozšiř filtr v Přehledu.`;
    }
    function open(){opened=true;setup();refresh();onOpen();}
    function leave(){opened=false;setup();}
    function begin(onlyMistakes=false){
      refresh();const selected=onlyMistakes?[...mistakes.values()].filter(i=>targets.some(t=>t.uid===i.uid)):targets;
      if(!selected.length)return;
      queue=M.shuffle(selected).map(item=>({item,review:false}));index=0;initialCount=queue.length;firstCorrect=answered=repeated=skipped=0;mistakes=new Map();reviewRun=onlyMistakes;
      ui.quizSetup.hidden=true;ui.quizEnd.hidden=true;ui.quizRound.hidden=false;next();
    }
    function finish(){cancel();phase="end";current=null;ui.quizRound.hidden=true;ui.quizEnd.hidden=false;
      ui.quizResult.textContent=`${reviewRun?"Opravné kolo. ":""}Na první pokus ${firstCorrect} z ${answered}. Opakování ${repeated}.${skipped?` Přeskočeno ${skipped}.`:""}`;
      ui.quizErrors.disabled=mistakes.size===0;ui.quizAgain.focus({preventScroll:true});}
    function imageError(ticket){
      if(ticket!==epoch||!opened||phase!=="loading")return;
      cancel();phase="image-error";buttons.forEach(b=>b.disabled=true);ui.quizReplay.disabled=true;ui.quizNext.disabled=false;ui.quizNext.textContent="Přeskočit otázku →";
      message("Některý obrázek se nepodařilo načíst. Otázku můžeš přeskočit; nezapočítá se mezi odpovědi.");
    }
    function next(){
      cancel();if(index>=queue.length){finish();return;}
      const entry=queue[index],q=question(entry.item,pool,getCatalog());if(!q){setup();refresh();return;}
      current={...q,review:entry.review,hadError:false};phase="loading";buttons=[];
      ui.quizChoices.replaceChildren();ui.practiceWord.replaceChildren();ui.practiceStrip.hidden=false;ui.practiceHero.hidden=true;ui.quizChoices.hidden=false;
      ui.quizNext.disabled=true;ui.quizReplay.disabled=true;ui.quizNext.textContent="Další →";
      ui.quizPosition.textContent=entry.review?`Opakování · ${index+1} z ${queue.length}`:`Slovíčko ${index+1} z ${initialCount}`;
      ui.practiceNote.textContent="";message("Připravuji čtyři obrázky…");
      const ticket=epoch;let loaded=0;
      for(const [n,item] of q.choices.entries()){
        const button=doc.createElement("button");button.type="button";button.className="quiz-choice practice-choice";button.disabled=true;button.dataset.uid=item.uid;button.setAttribute("aria-label",`Vybrat obrázek ${n+1}`);
        const image=doc.createElement("img");image.alt=`Obrázek ${n+1}`;image.width=384;image.height=384;
        const number=doc.createElement("span");number.className="practice-number";number.textContent=String(n+1);number.setAttribute("aria-hidden","true");
        const mark=doc.createElement("span");mark.className="quiz-mark";mark.setAttribute("aria-hidden","true");button.append(image,number,mark);buttons.push(button);ui.quizChoices.append(button);
        button.addEventListener("click",()=>answer(item.uid));let settled=false;
        const ready=()=>{if(settled||ticket!==epoch||!opened||phase!=="loading")return;settled=true;loaded++;if(loaded===4){ui.quizReplay.disabled=false;void present();}};
        image.addEventListener("load",ready,{once:true});image.addEventListener("error",()=>imageError(ticket),{once:true});
        image.src=new win.URL(`../${item.thumbnail}`,win.location.href).href;if(image.complete&&image.naturalWidth>0)ready();
      }
      later(()=>imageError(ticket),15000);ui.quizPosition.focus({preventScroll:true});ui.quizRound.scrollIntoView({block:"start"});
    }
    async function read(ticket,feedback=false){
      const deadline=later(()=>{
        if(ticket!==epoch||!opened)return;
        stop();
        if(feedback)message("Přehrávání se nedokončilo. Správná karta zůstává zobrazená; zvuk můžeš zopakovat.");
        else{phase="audio-error";buttons.forEach(b=>b.disabled=true);ui.quizNext.disabled=false;ui.quizNext.textContent="Přeskočit otázku →";message("Přehrávání se nedokončilo. Zopakuj slovo tlačítkem, nebo otázku přeskoč.");}
      },20000);
      try{
        const completed=await play(current.target);if(ticket!==epoch||!opened||!completed)return;
        if(!feedback){phase="question";buttons.forEach(b=>b.disabled=b.classList.contains("is-wrong"));message(current.hadError?"Zkus jiný obrázek. Slovo si můžeš znovu přehrát.":"Vyber obrázek. Můžeš použít i klávesy 1–4.");}
      }catch(_){
        if(ticket!==epoch||!opened)return;
        if(feedback)message("Správný obrázek i zápis jsou zobrazené. Zvuk zkus přehrát tlačítkem.");
        else{phase="audio-error";buttons.forEach(b=>b.disabled=true);ui.quizNext.disabled=false;ui.quizNext.textContent="Přeskočit otázku →";message("Zvuk se nepodařilo přehrát. Stiskni Zopakovat slovo, nebo otázku přeskoč.");}
      }finally{win.clearTimeout(deadline);timers.delete(deadline);}
    }
    function present(){
      cancel();const ticket=epoch,r=record(current.target,getCatalog());phase="presenting";buttons.forEach(b=>b.disabled=true);ui.quizNext.disabled=true;ui.quizNext.textContent="Další →";
      ui.practiceWord.replaceChildren();ui.practiceWord.classList.remove("is-joined");ui.practiceWord.setAttribute("aria-label",current.target.it);
      ui.practiceNote.textContent=r.reviewed?"":"U tohoto přejatého výrazu ukazujeme celý zápis.";
      const nodes=r.pieces.map(piece=>{const span=doc.createElement("span");span.textContent=piece;span.className="spelling-piece is-pending";span.setAttribute("aria-hidden","true");ui.practiceWord.append(span);return span;});
      message("Podívej se na zápis slova…");
      function join(){if(ticket!==epoch||!opened)return;nodes.forEach(n=>n.classList.remove("is-pending"));ui.practiceWord.classList.add("is-joined");later(()=>{if(ticket===epoch&&opened)ui.practiceWord.textContent=current.target.it;},350);message("Poslouchej italské slovo…");void read(ticket);}
      if(win.matchMedia?.("(prefers-reduced-motion: reduce)").matches){join();return;}
      const interval=Math.max(65,Math.min(260,1600/nodes.length));
      nodes.forEach((node,n)=>later(()=>{if(ticket===epoch&&opened)node.classList.remove("is-pending");},n*interval));
      later(join,nodes.length*interval+450);
    }
    function replay(){
      if(!current||["setup","loading","image-error","end"].includes(phase))return;
      if(phase==="answer"){cancel();void read(epoch,true);return;}
      // A direct gesture retries playback without an animation delay (Safari).
      cancel();phase="presenting";ui.quizNext.disabled=true;ui.quizNext.textContent="Další →";ui.practiceWord.classList.add("is-joined");
      ui.practiceWord.querySelectorAll(".spelling-piece").forEach(n=>n.classList.remove("is-pending"));buttons.forEach(b=>b.disabled=true);message("Poslouchej italské slovo…");void read(epoch);
    }
    function answer(uid){
      if(phase!=="question"||!current)return;
      const button=buttons.find(b=>b.dataset.uid===uid);if(!button||button.disabled)return;
      if(uid!==current.target.uid){current.hadError=true;mistakes.set(current.target.uid,current.target);button.disabled=true;button.classList.add("is-wrong");button.querySelector(".quiz-mark").textContent="×";button.setAttribute("aria-label","Nesprávná volba");message("Tohle není správný obrázek. Zkus jiný; slovo zůstává stejné.");return;}
      cancel();phase="answer";buttons.forEach(b=>b.disabled=true);if(current.review)repeated++;else{answered++;if(!current.hadError)firstCorrect++;else queue.push({item:current.target,review:true});}
      ui.quizChoices.hidden=true;ui.practiceStrip.hidden=true;ui.practiceHero.hidden=false;ui.practiceHeroWord.textContent=current.target.it;ui.practiceHeroCz.textContent=current.target.cz;
      const heroTicket=epoch,heroTarget=current.target;let fallback=false;ui.practiceHeroImage.onerror=()=>{if(!fallback&&heroTicket===epoch&&phase==="answer"){fallback=true;ui.practiceHeroImage.src=new win.URL(`../${heroTarget.thumbnail}`,win.location.href).href;}};
      ui.practiceHeroImage.alt=current.target.it;ui.practiceHeroImage.src=new win.URL(`../${current.target.image}`,win.location.href).href;
      ui.quizNext.disabled=false;ui.quizNext.textContent=index+1===queue.length?"Dokončit kolo":"Další →";
      message(current.hadError?(current.review?"Správně. Po kole můžeš znovu procvičit chyby.":"Správně. Tohle slovo si v kole ještě zopakuješ."):"Správně. Prohlédni si obrázek i zápis slova.");ui.practiceHeroWord.focus({preventScroll:true});void read(epoch,true);
    }
    function advance(){if(!["answer","image-error","audio-error"].includes(phase))return;if(phase!=="answer")skipped++;index++;next();}
    function key(event){if(!opened||phase!=="question"||event.altKey||event.ctrlKey||event.metaKey||event.repeat||/INPUT|TEXTAREA|SELECT/.test(event.target?.tagName||""))return;const n=Number(event.key)-1;if(n>=0&&n<4){event.preventDefault();buttons[n]?.click();}}
    ui.quizStart.addEventListener("click",()=>begin());ui.quizAgain.addEventListener("click",()=>begin());ui.quizErrors.addEventListener("click",()=>begin(true));
    ui.quizReplay.addEventListener("click",replay);ui.quizNext.addEventListener("click",advance);
    for(const id of ["quizChange","quizSetupChange","quizEndChange","quizBack"])ui[id].addEventListener("click",()=>{leave();onClose();});
    doc.addEventListener("keydown",key);win.addEventListener("pagehide",leave);win.addEventListener("pageshow",event=>{if(event.persisted&&opened){setup();refresh();}});
    return {open,leave,refresh,close:()=>{leave();onClose();}};
  }
  const api={record,eligible,compatible,question,create};if(typeof module!=="undefined"&&module.exports)module.exports=api;else root.VocabularyITPractice=api;
})(globalThis);
