/* Numbered, local-only classroom pairs. Personal vocabulary is read-only. */
(function(root){
  'use strict';
  const M=typeof module!=='undefined'&&module.exports?require('./model.js'):root.VocabularyFRModel;
  const Q=typeof module!=='undefined'&&module.exports?require('./practice.js'):root.VocabularyFRPractice;
  const KEY='vocabulary-fr.memory-pairs.v1', PAIRS=12, CARDS=PAIRS*2;
  const names=values=>values.slice(0,4).map((v,i)=>Array.from(String(v||'').trim()).slice(0,12).join('')||`Hráč ${i+1}`);
  function uniform(catalog){
    return {...catalog,entries:Object.fromEntries(Object.entries(catalog?.entries||{}).map(([uid,e])=>[uid,{...e,format:'objects'}]))};
  }
  function compatible(a,b,audio,catalog){
    const thumbnailKey=item=>item.thumbnail?.split('/').at(-1);
    const left=thumbnailKey(a),right=thumbnailKey(b);
    return !(left&&right&&left===right)&&M.audioRecord(a,audio)?.fr!==M.audioRecord(b,audio)?.fr&&Q.compatible(a,b,catalog);
  }
  function choose(items,audio,catalog,random=Math.random){
    const pool=Q.eligible(items,audio,catalog).filter(i=>!i.imageMissing), meta=uniform(catalog);
    let best=[];
    for(let attempt=0;attempt<32;attempt++){
      const selected=[];
      for(const item of M.shuffle(pool,random)){
        if(selected.every(other=>compatible(item,other,audio,meta)))selected.push(item);
        if(selected.length===PAIRS)return selected;
      }
      if(selected.length>best.length)best=selected;
    }
    return best;
  }
  function duelPool(items,audio,catalog){
    return Q.eligible(items,audio,catalog).filter(item=>!item.imageMissing&&M.audioRecord(item,audio)?.cz);
  }
  function newGame(items,players,random=Math.random){
    if(items.length!==PAIRS||new Set(items.map(M.key)).size!==PAIRS||!Array.isArray(players)||players.length<1||players.length>4)throw Error(`Pexeso potřebuje ${PAIRS} různých významů a 1–4 hráče.`);
    return {deck:M.shuffle(items.flatMap(i=>[M.key(i),M.key(i)]),random),players:names(players),owners:{},active:0,turns:0};
  }
  function settle(game,a,b){
    if(!Number.isInteger(a)||!Number.isInteger(b)||a<0||b<0||a>=CARDS||b>=CARDS||a===b||Object.hasOwn(game.owners,game.deck[a])||Object.hasOwn(game.owners,game.deck[b]))throw Error('Neplatný tah.');
    const result={...game,owners:{...game.owners},turns:game.turns+1};
    if(game.deck[a]===game.deck[b])result.owners[game.deck[a]]=game.active;
    else result.active=(game.active+1)%game.players.length;
    return result;
  }
  function signature(deck,items,audio){
    const known=new Map(items.map(i=>[M.key(i),i]));
    return JSON.stringify([...new Set(deck)].sort().map(uid=>{
      const i=known.get(uid);return i?[uid,i.fr,i.cz,i.image,i.thumbnail,M.audioRecord(i,audio)?.fr]:null;
    }));
  }
  function restore(saved,items,audio,catalog){
    try{
      const g=saved?.game;
      if(saved.version!==1||!g||!Array.isArray(g.deck)||g.deck.length!==CARDS||!Array.isArray(g.players)||g.players.length<1||g.players.length>4||g.players.some(p=>typeof p!=='string'||!p.trim()||Array.from(p).length>12)||!Number.isInteger(g.active)||g.active<0||g.active>=g.players.length||!Number.isInteger(g.turns)||g.turns<0||g.turns>100000||!g.owners||typeof g.owners!=='object'||Array.isArray(g.owners))return null;
      const counts=new Map();for(const uid of g.deck){if(typeof uid!=='string')return null;counts.set(uid,(counts.get(uid)||0)+1);}
      if(counts.size!==PAIRS||[...counts.values()].some(n=>n!==2)||Object.keys(g.owners).length>g.turns||Object.entries(g.owners).some(([uid,p])=>!counts.has(uid)||!Number.isInteger(p)||p<0||p>=g.players.length))return null;
      const known=new Map(Q.eligible(items,audio,catalog).map(i=>[M.key(i),i]));
      const selected=[...counts.keys()].map(uid=>known.get(uid));if(selected.some(i=>!i))return null;
      const meta=uniform(catalog);if(selected.some((i,n)=>selected.slice(n+1).some(j=>!compatible(i,j,audio,meta))))return null;
      if(saved.source!==signature(g.deck,items,audio))return null;
      return JSON.parse(JSON.stringify(g));
    }catch(_){return null;}
  }
  function create({doc,win,getData,getAudio,getCatalog,getSelection,getContext,sanitizeContext,onOpen,onClose,play,stop,getOnlineOrigin=()=>null}){
    const remoteKey='vocabulary-fr.online-origin.v1';
    function verifiedOrigin(value){
      try{const url=new URL(value),temporary=!url.port&&/^[a-z0-9]+(?:-[a-z0-9]+)+\.trycloudflare\.com$/.test(url.hostname),privateGame=url.port==='8443'&&/^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+ts\.net$/.test(url.hostname);return url.protocol==='https:'&&!url.username&&!url.password&&!url.search&&!url.hash&&url.pathname==='/'&&(temporary||privateGame)&&url.origin===value?url.origin:null;}catch(_){return null;}
    }
    const entry=new URLSearchParams(new URL(win.location.href).hash.slice(1));
    let remoteOrigin=null;
    if(entry.has('onlineOrigin')){
      remoteOrigin=verifiedOrigin(entry.get('onlineOrigin'));
      try{if(remoteOrigin)win.sessionStorage.setItem(remoteKey,remoteOrigin);else win.sessionStorage.removeItem?.(remoteKey);}catch(_){}
    }else try{remoteOrigin=verifiedOrigin(win.sessionStorage.getItem(remoteKey));}catch(_){}
    function currentOrigin(){
      const value=getOnlineOrigin();
      // Only the exact reviewed configuration can select a permanent service.
      if(typeof value==='string'&&/^https:\/\/[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.onrender\.com$/.test(value))return value;
      return remoteOrigin;
    }
    const ids=['memoryDuel','memoryOnline','memoryView','memorySetup','memorySelection','memorySetupChange','memoryPlayerCount','memoryNames','memoryPoolNotice','memoryStorageNotice','memoryStart','memoryResume','memoryRound','memoryBoard','memoryScores','memoryStatus','memoryProgress','memoryRetry','memorySkip','memoryEnd','memoryResult','memoryCollections','memoryAgain','memoryNew','memoryChange','memoryBack','memoryProjector','memoryReward','memoryRewardImage','memoryRewardWord'];
    const ui=Object.fromEntries(ids.map(id=>[id,doc.getElementById(id)]));
    let filters=sanitizeContext(getContext()), gameFilters=null, game=null, source='', selected=[], opened=false, busy=false, error=false, success=false, openCards=[], hint=-1, epoch=0, draftNames=['Hráč 1','Hráč 2'], saved=null;
    const waits=new Map();
    let rewarding=false;
    function status(s){ui.memoryStatus.textContent=s;}
    function finished(){return game&&Object.keys(game.owners).length===PAIRS;}
    function sanitize(value={}){return sanitizeContext(value);}
    function pool(f=filters){return getSelection(f);}
    function save(){
      if(!game)return;
      saved={version:1,filters:gameFilters,game,source};
      try{win.sessionStorage.setItem(KEY,JSON.stringify(saved));ui.memoryStorageNotice.textContent='';}
      catch(_){ui.memoryStorageNotice.textContent='Partie funguje, ale v tomto panelu se ji nepodařilo uložit pro obnovení stránky.';}
    }
    function hideReward(){
      if(ui.memoryReward.open)ui.memoryReward.close();
      ui.memoryReward.hidden=true;
    }
    function primeReward(item){
      ui.memoryRewardImage.hidden=false;
      ui.memoryRewardImage.src=new URL('../'+item.image,win.location.href).toString();
    }
    async function reward(item,ticket){
      primeReward(item);ui.memoryRewardWord.textContent=item.fr;
      ui.memoryReward.hidden=false;ui.memoryReward.showModal();ui.memoryRewardWord.focus({preventScroll:true});
      let heard=true;
      await Promise.all([delay(2000,ticket).then(()=>{if(ticket===epoch)hideReward();}),
        (async()=>{try{heard=await play(item);}catch(_){heard=false;}})()]);
      return heard;
    }
    function cancel(){
      epoch++;stop();for(const [id,resolve] of waits){win.clearTimeout(id);resolve(false);}waits.clear();busy=false;error=false;success=false;openCards=[];hint=-1;
      rewarding=false;hideReward();
      ui.memoryRetry.hidden=ui.memorySkip.hidden=true;
    }
    function delay(ms,ticket){return new Promise(resolve=>{const id=win.setTimeout(()=>{waits.delete(id);resolve(ticket===epoch&&opened);},ms);waits.set(id,resolve);});}
    function renderNames(){
      ui.memoryNames.replaceChildren();
      const n=Number(ui.memoryPlayerCount.value)||2;
      for(let i=0;i<n;i++){
        const label=doc.createElement('label');label.textContent=`Hráč ${i+1}`;
        const input=doc.createElement('input');input.type='text';input.maxLength=12;input.value=draftNames[i]||`Hráč ${i+1}`;input.autocomplete='off';
        input.addEventListener('input',()=>{draftNames[i]=input.value;});label.append(input);ui.memoryNames.append(label);
      }
    }
    function controls(){
      const labels=filters.topics.map(id=>getData().catalog.groups.find(g=>g.id===id)?.label).filter(Boolean);
      ui.memorySelection.textContent=[filters.personalHard?'Jen obtížná':'Všechna slovíčka',labels.join(' + '),filters.parts.map(id=>M.posLabels[id]||id).join(' + '),filters.levels.map(id=>M.levelLabels[id]||id).join(' + '),filters.teachingType!=='all'?M.teachingTypeLabels[filters.teachingType]:'',filters.query?`Hledání: ${filters.query}`:'',filters.recentCount?`Posledních ${filters.recentCount}`:''].filter(Boolean).join(' · ');
    }
    function refresh(){
      if(!opened)return;
      filters=sanitize(getContext());
      const ready=Boolean(getAudio()&&getCatalog());
      selected=ready?choose(pool(),getAudio(),getCatalog(),()=>.5):[];
      ui.memoryStart.disabled=selected.length!==PAIRS;ui.memoryOnline.disabled=selected.length!==PAIRS;
      ui.memoryDuel.disabled=!ready||choose(duelPool(pool(),getAudio(),getCatalog()),getAudio(),getCatalog(),()=>.5).length!==PAIRS;
      ui.memoryPoolNotice.textContent=!ready?'Připravuji obrázky a zvuk…':selected.length===PAIRS?`Ve výběru ${pool().length} karet. Připraveno ${PAIRS} různých dvojic · ${CARDS} kartiček.`:`Pro plán potřebujeme ${PAIRS} dostatečně odlišných obrázků s francouzským zvukem. Rozšiř témata nebo výběr (${pool().length} karet ve filtru).`;
      if(currentOrigin())ui.memoryPoolNotice.textContent+=' Společná hra se otevře v nové kartě; tento výběr zůstane zachovaný.';
      if(getAudio()===false||getCatalog()===false)ui.memoryPoolNotice.textContent='Obrázky nebo zvuk pro pexeso se nepodařilo načíst. Zkus obnovit stránku.';
      ui.memoryResume.hidden=!saved||saved.game?.deck?.length!==CARDS;
      if(saved?.game?.deck?.length&&saved.game.deck.length!==CARDS)ui.memoryPoolNotice.textContent+=' Starší partie má jiný počet kartiček. Pro nový formát spusť novou partii.';
      ui.memoryResume.textContent=saved?.game?.players?`Pokračovat v partii (${saved.game.players.join(', ')})`:'Pokračovat v partii';
      controls();
    }
    function draw(){
      if(!game)return;
      ui.memoryView.classList.add('memory-playing');
      const byUid=new Map(getData().items.map(i=>[M.key(i),i]));
      ui.memorySetup.hidden=true;ui.memoryRound.hidden=false;ui.memoryEnd.hidden=!finished()||rewarding;
      ui.memoryProgress.textContent=`Nalezeno ${Object.keys(game.owners).length} z ${PAIRS} dvojic · ${game.turns} ${game.turns===1?'tah':game.turns>=2&&game.turns<=4?'tahy':'tahů'}`;
      ui.memoryBoard.replaceChildren();
      game.deck.forEach((uid,index)=>{
        const slot=doc.createElement('div');slot.className='memory-slot';
        if(success&&openCards.includes(index))slot.classList.add('memory-match');
        if(Object.hasOwn(game.owners,uid)){slot.classList.add('memory-empty');slot.setAttribute('aria-label',`Prázdné místo ${index+1}`);ui.memoryBoard.append(slot);return;}
        const item=byUid.get(uid),face=openCards.includes(index),button=doc.createElement('button');button.type='button';button.className='memory-card'+(face?' memory-face':'');button.disabled=busy||face;button.setAttribute('aria-label',face?`Kartička ${index+1}: ${item.fr}`:`Kartička ${index+1}, zavřená`);
        const number=doc.createElement('span');number.className='memory-number';number.textContent=String(index+1);button.append(number);
        if(face){
          const image=doc.createElement('img');image.src=new URL('../'+(item.thumbnail||item.image),win.location.href).toString();image.alt='';
          image.addEventListener('error',()=>{image.hidden=true;});
          const word=doc.createElement('span');word.className='memory-word';word.lang='fr';word.textContent=item.fr;button.append(image,word);
          if(hint===index){const cz=doc.createElement('span');cz.className='memory-translation';cz.lang='cs';cz.textContent=item.cz;button.append(cz);}
        }
        button.addEventListener('click',()=>flip(index));slot.append(button);
        if(face){const replay=doc.createElement('button');replay.type='button';replay.className='memory-replay';replay.textContent='♪';replay.setAttribute('aria-label',`Zopakovat francouzsky: ${item.fr}`);replay.disabled=busy;replay.addEventListener('click',()=>repeat(item));slot.append(replay);}
        ui.memoryBoard.append(slot);
      });
      ui.memoryScores.replaceChildren();
      game.players.forEach((name,index)=>{
        const panel=doc.createElement('div');panel.className='memory-player memory-player-'+index+(game.active===index&&!finished()?' memory-current':'');
        const label=doc.createElement('strong');label.textContent='🃏 '+name;
        const count=doc.createElement('span');count.textContent=`Dvojice: ${Object.values(game.owners).filter(n=>n===index).length}`;panel.append(label,count);
        if(game.active===index&&!finished()){const turn=doc.createElement('span');turn.className='memory-turn';turn.textContent='NA TAHU';panel.append(turn);}ui.memoryScores.append(panel);
      });
      if(finished()){
        const scores=game.players.map((_,i)=>Object.values(game.owners).filter(n=>n===i).length),max=Math.max(...scores),winners=game.players.filter((_,i)=>scores[i]===max);
        const unit=max<=4?'dvojice':'dvojic';
        ui.memoryResult.textContent=game.players.length===1?`Našel/a jsi všech ${PAIRS} dvojic!`:winners.length>1?`Remíza: ${winners.join(', ')} · ${max} ${unit}.`:`Vyhrává ${winners[0]} · ${max} ${unit}!`;
        ui.memoryCollections.replaceChildren();
        game.players.forEach((name,i)=>{
          const details=doc.createElement('details'),summary=doc.createElement('summary');summary.textContent=`${name} · získané dvojice`;details.append(summary);
          const list=doc.createElement('div');list.className='memory-collection';
          Object.entries(game.owners).filter(([,owner])=>owner===i).forEach(([uid])=>{const item=byUid.get(uid),b=doc.createElement('button');b.type='button';const img=doc.createElement('img');img.src=new URL('../'+(item.thumbnail||item.image),win.location.href).toString();img.alt='';const text=doc.createElement('span');text.textContent=`${item.fr} · ${item.cz}`;b.append(img,text);b.addEventListener('click',()=>repeat(item));list.append(b);});details.append(list);ui.memoryCollections.append(details);
        });
      }
    }
    async function repeat(item){
      if(busy)return;busy=true;const ticket=epoch;draw();
      try{await play(item);}catch(_){if(ticket===epoch)status('Zvuk se nepodařilo přehrát. Zkus ho zopakovat.');}
      if(ticket===epoch&&opened){busy=false;draw();}
    }
    async function resolveTurn(){
      if(openCards.length===2){
        const matched=game.deck[openCards[0]]===game.deck[openCards[1]],player=game.players[game.active];
        busy=true;success=matched;status(matched?`Správná dvojice · ${player}!`:'Porovnej oba obrázky…');draw();const ticket=epoch;
        if(!await delay(1000,ticket))return;
        const item=getData().items.find(i=>M.key(i)===game.deck[openCards[0]]);
        game=settle(game,...openCards);save();openCards=[];success=false;busy=rewarding=matched;draw();
        let heard=true;
        if(matched){status('Správně! Poslechni si slovo ještě jednou.');heard=await reward(item,ticket);}
        if(ticket!==epoch||!opened)return;
        busy=rewarding=false;draw();
        status((finished()?`Všech ${PAIRS} dvojic je nalezených.`:matched?`${player} získává dvojici a hraje znovu.`:`Na tahu: ${game.players[game.active]}.`)+(heard?'':' Dodatečný zvuk se nepodařilo přehrát; dvojice platí.'));
        if(finished()){ui.memoryEnd.scrollIntoView({block:'start'});ui.memoryResult.focus({preventScroll:true});}
        else if(matched)ui.memoryBoard.querySelector('button')?.focus({preventScroll:true});
      }else{busy=false;draw();status(`Vyber druhou kartičku · ${game.players[game.active]}.`);}
    }
    async function reveal(index){
      busy=true;error=false;hint=index;const ticket=epoch;ui.memoryRetry.hidden=ui.memorySkip.hidden=true;draw();status('Posloucháme…');
      const item=getData().items.find(i=>M.key(i)===game.deck[index]);
      primeReward(item);
      let failed=false;
      await Promise.all([delay(2000,ticket).then(()=>{if(ticket===epoch&&opened){hint=-1;draw();}}),(async()=>{try{if(!await play(item))failed=true;}catch(_){failed=true;}})()]);
      if(ticket!==epoch||!opened)return;
      if(failed){error=true;ui.memoryRetry.hidden=ui.memorySkip.hidden=false;status('Zvuk se nepodařilo přehrát. Zkus ho zopakovat nebo pokračuj bez zvuku.');return;}
      await resolveTurn();
    }
    function flip(index){
      if(!opened||!game||busy||finished()||openCards.includes(index)||Object.hasOwn(game.owners,game.deck[index]))return;
      openCards.push(index);void reveal(index);
    }
    function approveLeave(){return !game||finished()||win.confirm('Opustit rozehranou partii? Ve stejném panelu v ní můžeš později pokračovat.');}
    function setup(){cancel();ui.memorySetup.hidden=false;ui.memoryRound.hidden=ui.memoryEnd.hidden=true;ui.memoryView.classList.remove('memory-playing');ui.memoryView.classList.remove('memory-projector');ui.memoryProjector.setAttribute('aria-pressed','false');doc.querySelector('[data-json-url]')?.classList.remove('memory-projector-shell');refresh();}
    function start(same=false){
      if((game&&!finished()||!game&&saved?.game&&Object.keys(saved.game.owners||{}).length<(Array.isArray(saved.game.deck)?new Set(saved.game.deck).size:0))&&!win.confirm('Spustit novou partii a nahradit rozehranou hru?'))return;
      const count=Number(ui.memoryPlayerCount.value)||2;
      const chosen=same&&game?[...new Set(game.deck)].map(uid=>getData().items.find(i=>M.key(i)===uid)):choose(pool(),getAudio(),getCatalog());
      if(chosen.length!==PAIRS){refresh();return;}
      const players=same&&game?game.players:Array.from(ui.memoryNames.querySelectorAll('input')).map(i=>i.value);
      if(!same&&players.length!==count)return;
      cancel();game=newGame(chosen,players);gameFilters={...filters,topics:[...filters.topics]};source=signature(game.deck,getData().items,getAudio());save();draw();status(`Na tahu: ${game.players[0]}. Vyber první kartičku.`);ui.memoryView.scrollIntoView({block:'start'});
    }
    function resume(){
      const f=sanitize(saved?.filters),restored=restore(saved,pool(f),getAudio(),getCatalog());
      if(!restored){ui.memoryPoolNotice.textContent='Uložená partie už neodpovídá slovům nebo dostupné zásobě. Spusť novou hru.';return;}
      cancel();game=restored;gameFilters=f;filters=f;source=saved.source;draftNames=[...game.players];ui.memoryPlayerCount.value=String(game.players.length);renderNames();controls();draw();status(finished()?'Dokončená partie.':`Pokračujeme · ${game.players[game.active]}. Vyber první kartičku.`);
    }
    try{const raw=win.sessionStorage.getItem(KEY);if(raw&&raw.length<20000){const value=JSON.parse(raw);if(value?.version===1&&Array.isArray(value.game?.players)&&value.game.players.length>=1&&value.game.players.length<=4&&value.game.players.every(n=>typeof n==='string'&&Array.from(n).length<=12))saved=value;}}catch(_){}
    ui.memoryOnline.addEventListener('click',()=>{
      if(selected.length!==PAIRS)return;
      const target=currentOrigin(),url=target?new URL('/vocabulary-fr/online.html',target):new URL('online.html',win.location.href);
      url.hash=new URLSearchParams({words:selected.map(i=>i.uid).join(',')}).toString();
      if(target&&target!==new URL(win.location.href).origin&&typeof win.open==='function')win.open(url.toString(),'_blank','noopener,noreferrer');
      else win.location.href=url.toString();
    });
    for(const id of ['eclairTab','memoryEclair']){const button=doc.getElementById(id);if(button){button.disabled=false;button.addEventListener('click',()=>{
      const target=currentOrigin(),url=target?new URL('/vocabulary-fr/eclair.html',target):new URL('eclair.html',win.location.href);
      if(target&&target!==new URL(win.location.href).origin&&typeof win.open==='function')win.open(url.toString(),'_blank','noopener,noreferrer');
      else win.location.href=url.toString();
    });}}
    ui.memoryDuel.addEventListener('click',()=>{
      if(ui.memoryDuel.disabled)return;
      const words=duelPool(pool(),getAudio(),getCatalog()),target=currentOrigin();
      const url=target?new URL('/vocabulary-fr/duel.html',target):new URL('duel.html',win.location.href);
      url.hash=new URLSearchParams({words:words.map(item=>item.uid).join(',')}).toString();
      if(target&&target!==new URL(win.location.href).origin&&typeof win.open==='function')win.open(url.toString(),'_blank','noopener,noreferrer');
      else win.location.href=url.toString();
    });
    ui.memoryPlayerCount.value='2';renderNames();
    ui.memorySetupChange.addEventListener('click',()=>{if(approveLeave()){leave();onClose();}});
    ui.memoryPlayerCount.addEventListener('change',()=>{if(![1,2,3,4].includes(Number(ui.memoryPlayerCount.value)))ui.memoryPlayerCount.value='2';draftNames=Array.from(ui.memoryNames.querySelectorAll('input')).map(i=>i.value);renderNames();});
    ui.memoryStart.addEventListener('click',()=>start());ui.memoryResume.addEventListener('click',resume);
    ui.memoryAgain.addEventListener('click',()=>start(true));ui.memoryNew.addEventListener('click',()=>start());ui.memoryChange.addEventListener('click',setup);
    ui.memoryBack.addEventListener('click',()=>{if(approveLeave()){leave();onClose();}});
    ui.memoryReward.addEventListener('cancel',event=>event.preventDefault());
    ui.memoryReward.addEventListener('keydown',event=>{if(event.key==='Escape')event.stopPropagation();});
    ui.memoryRewardImage.addEventListener('error',()=>{ui.memoryRewardImage.hidden=true;});
    ui.memoryRetry.addEventListener('click',()=>{if(error)void reveal(openCards.at(-1));});
    ui.memorySkip.addEventListener('click',()=>{if(!error)return;error=false;ui.memoryRetry.hidden=ui.memorySkip.hidden=true;void resolveTurn();});
    ui.memoryProjector.addEventListener('click',()=>{ui.memoryView.classList.toggle('memory-projector');doc.querySelector('[data-json-url]')?.classList.toggle('memory-projector-shell');ui.memoryProjector.setAttribute('aria-pressed',String(ui.memoryView.classList.contains('memory-projector')));});
    function leave(){save();opened=false;cancel();ui.memoryView.classList.remove('memory-projector');ui.memoryProjector.setAttribute('aria-pressed','false');doc.querySelector('[data-json-url]')?.classList.remove('memory-projector-shell');}
    return {open:()=>{opened=true;setup();onOpen();},leave,refresh,canLeave:approveLeave,close:()=>{if(approveLeave()){leave();onClose();}},checkpoint:()=>save()};
  }
  const api={KEY,PAIRS,CARDS,choose,duelPool,newGame,settle,signature,restore,create};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.VocabularyFRMemory=api;
})(globalThis);
