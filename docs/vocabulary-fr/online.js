/* Two clients share server-owned turns; no personal vocabulary is uploaded. */
(function(root){
  'use strict';
  const M=typeof module!=='undefined'&&module.exports?require('./model.js'):root.VocabularyFRModel;
  const Memory=typeof module!=='undefined'&&module.exports?require('./memory.js'):root.VocabularyFRMemory;
  const KEY='vocabulary-fr.online-session.v1',API='/api/vocabulary-fr/rooms';
  const tokenPattern=/^[a-f0-9]{64}$/,roomPattern=/^[a-f0-9]{24}$/;
  function random(win){const bytes=new Uint8Array(32);win.crypto.getRandomValues(bytes);return Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');}
  function create({doc,win,fetcher=root.fetch.bind(root),AudioClass=root.Audio}){
    const ids=['onlineView','onlineBack','onlineStatus','onlineStorage','onlineSetup','onlineName','onlineSelection','onlineEnter','onlineRoom','onlineInvitePanel','onlineInvite','onlineCopy','onlineProgress','onlineStart','onlineResume','onlineRetry','onlineSkip','onlineBoard','onlineScores','onlineEnd','onlineResult','onlineAgain','onlineNewWords','onlinePicker','onlineTopic','onlineCandidatesInfo','onlineCandidates','onlineShuffle','onlineNextStart','onlineNextCancel','onlineCollections','onlineReward','onlineRewardImage','onlineRewardWord'];
    const ui=Object.fromEntries(ids.map(id=>[id,doc.getElementById(id)]));
    const audio=new AudioClass();let data=null,manifest=null,quiz=null,revision='',selection=[],snapshot=null,session=null,active=false,network=false,sending=false,pollTimer=null,stage=null,epoch=0,available=false;
    let cancelAudio=null,picking=false,candidates=[];
    const route=new URLSearchParams(new URL(win.location.href).hash.slice(1));
    const status=text=>{ui.onlineStatus.textContent=text;};
    function save(){try{win.sessionStorage.setItem(KEY,JSON.stringify(session));}catch(_){ui.onlineStorage.textContent='Obnovení po zavření tohoto panelu není dostupné. Pozvánka dál funguje pro spoluhráče.';}}
    function hideReward(){if(ui.onlineReward.open)ui.onlineReward.close();ui.onlineReward.hidden=true;}
    function stopAudio(){cancelAudio?.();cancelAudio=null;audio.pause();}
    function cancelStage(){if(stage){stage.cancelled=true;win.clearTimeout(stage.timer);stage.visualResolve?.();}stage=null;stopAudio();hideReward();}
    async function bounded(work,ms=8000){
      const controller=new root.AbortController();let timer;
      const deadline=new Promise((_,reject)=>{timer=win.setTimeout(()=>{controller.abort();reject(Error('Spojení trvá příliš dlouho. Ověř znovu stav partie.'));},ms);});
      try{return await Promise.race([work(controller.signal),deadline]);}finally{win.clearTimeout(timer);}
    }
    async function read(path,text=false){
      return bounded(async signal=>{const response=await fetcher(path,{cache:'no-store',signal}).catch(()=>{throw Error(text?'Slovník a společnou hru se nepodařilo načíst.':'Společná hra je momentálně nedostupná.');});if(!response.ok)throw Error(text?'Slovník se nepodařilo načíst.':'Společná hra je momentálně nedostupná.');return text?response.text():response.json();},text?20000:8000);
    }
    function play(path){
      stopAudio();audio.src=new URL('../'+path,win.location.href).toString();audio.load();
      return new Promise(resolve=>{
        let done=false;
        const finish=ok=>{if(done)return;done=true;audio.pause();audio.removeEventListener('ended',ended);audio.removeEventListener('error',failed);win.clearTimeout(timer);if(cancelAudio===cancel)cancelAudio=null;resolve(ok);};
        const ended=()=>finish(true),failed=()=>finish(false),cancel=()=>finish(false),timer=win.setTimeout(failed,20000);
        cancelAudio=cancel;audio.addEventListener('ended',ended);audio.addEventListener('error',failed);
        try{Promise.resolve(audio.play()).catch(failed);}catch(_){failed();}
      });
    }
    async function post(action,payload={},authenticated=true){
      const path=action==='create'?API:API+'/'+session.room+'/'+action;
      const headers={'Content-Type':'application/json'};if(authenticated)headers.Authorization='Bearer '+session.token;
      return bounded(async signal=>{
        const response=await fetcher(path,{method:'POST',headers,body:JSON.stringify(payload),cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer',signal}).catch(()=>{throw Error('Spojení se nepodařilo dokončit. Zkus pokračovat znovu.');});
        let result;try{result=await response.json();}catch(_){throw Error('Společná hra je momentálně nedostupná.');}
        if(!response.ok){const error=Error(result.error||'Partii se nepodařilo načíst.');error.status=response.status;throw error;}
        return result;
      });
    }
    function accept(value){
      if(value.protocol!==1||value.catalog!==revision||value.room!==session.room||!Array.isArray(value.cards)||value.cards.length!==24||![0,1].includes(value.you))throw Error('Partie neodpovídá této verzi slovníku.');
      if(snapshot&&value.revision<snapshot.revision)return;
      const changed=!snapshot||value.revision!==snapshot.revision||!network||JSON.stringify(value.players)!==JSON.stringify(snapshot.players);
      if(snapshot&&snapshot.round!==value.round){cancelStage();picking=false;candidates=[];}
      snapshot=value;network=true;
      if(changed)render();
      syncStage();
    }
    function schedule(){win.clearTimeout(pollTimer);if(active)pollTimer=win.setTimeout(()=>{void poll();},network?600:1600);}
    async function poll(){
      if(!active)return;
      if(sending){schedule();return;}
      const ticket=epoch;
      try{const value=await post('sync');if(ticket!==epoch||!active)return;accept(value);}
      catch(error){if(ticket!==epoch)return;network=false;cancelStage();render();status(error.status===410||error.status===403?error.message:'Spojení vypadlo. Čekáme na návrat k partii.');if([403,404,410].includes(error.status)){active=false;ui.onlineResume.hidden=false;}}
      finally{if(ticket===epoch)schedule();}
    }
    async function command(action,payload={}){
      if(sending||!active)return;
      sending=true;const ticket=epoch;render();
      try{const value=await post(action,{requestId:random(win),expectedRound:snapshot.round,expectedStage:snapshot.stage,...payload});if(ticket===epoch&&active)accept(value);}
      catch(error){if(ticket===epoch){status(error.message||'Ověřuji stav partie po výpadku spojení.');if(!error.status){network=false;cancelStage();}}}
      finally{if(ticket===epoch){sending=false;render();schedule();}}
    }
    function currentUid(){return snapshot.phase==='reward'?snapshot.reward:snapshot.cards[snapshot.focus]?.uid;}
    function chooseNext(){
      if(snapshot?.phase!=='finished'||snapshot.you!==0)return;
      const previous=new Set(Object.keys(snapshot.owners)),topic=ui.onlineTopic.value;
      const pool=M.select(data.items,{topics:topic?[topic]:[]}).filter(item=>!previous.has(item.uid));
      candidates=Memory.choose(pool,manifest,quiz);picking=true;
      ui.onlineCandidates.replaceChildren();
      candidates.forEach(item=>{const word=doc.createElement('li');word.lang='fr';word.textContent=item.fr;ui.onlineCandidates.append(word);});
      ui.onlineCandidatesInfo.textContent=candidates.length===12?'Připraveno 12 nových dvojic. Spoluhráč zůstává ve stejné místnosti.':'V tomto okruhu není dost jiných obrázků se zvukem pro 12 dvojic. Zvol širší okruh.';
      render();
    }
    function primeReward(item){
      const source=new URL('../'+item.image,win.location.href).toString();
      if(ui.onlineRewardImage.src!==source){ui.onlineRewardImage.src=source;ui.onlineRewardImage.hidden=false;}
    }
    function syncStage(){
      if(!active||!network||snapshot.paused){cancelStage();return;}
      if(!['reveal','reward'].includes(snapshot.phase)){if(stage)cancelStage();return;}
      const key=snapshot.round+':'+snapshot.stage;
      if(stage?.key===key)return;
      cancelStage();
      if(snapshot.acks.includes(snapshot.you))return;
      const item=data.items.find(i=>i.uid===currentUid());if(!item)return;
      primeReward(item);
      const ticket=epoch,local={key,cancelled:false,failed:false,hint:true,timer:null,visualResolve:null};stage=local;
      local.visual=new Promise(resolve=>{local.visualResolve=resolve;local.timer=win.setTimeout(()=>{local.hint=false;hideReward();if(stage===local)render();resolve();},2000);});
      if(snapshot.phase==='reward'){
        ui.onlineRewardWord.textContent=item.fr;
        ui.onlineReward.hidden=false;ui.onlineReward.showModal();ui.onlineRewardWord.focus({preventScroll:true});
      }
      render();
      void (async()=>{const heard=await play(M.audioRecord(item,manifest).fr);await local.visual;if(local.cancelled||ticket!==epoch||stage!==local)return;if(!heard){local.failed=true;render();status('Zvuk se nepodařilo přehrát. Zopakuj ho nebo výslovně pokračuj bez zvuku.');return;}await command('heard',{stage:snapshot.stage});})();
    }
    function render(){
      ui.onlineSetup.hidden=Boolean(snapshot);ui.onlineRoom.hidden=!snapshot;
      ui.onlineEnter.disabled=!available||sending;
      if(!snapshot)return;
      const locked=!active||!network||snapshot.paused||sending,finished=snapshot.phase==='finished';
      ui.onlineView.dataset.paused=String(locked);ui.onlineInvitePanel.hidden=!session.invite||session.mode!=='host'||snapshot.players[1]!==null;
      const invitation=new URL('online.html',win.location.href);invitation.hash=new URLSearchParams({room:session.room,invite:session.invite||''}).toString();ui.onlineInvite.value=invitation.toString();
      ui.onlineStart.hidden=snapshot.phase!=='waiting'||snapshot.you!==0;ui.onlineStart.disabled=locked||!snapshot.players.every(p=>p?.connected);
      ui.onlineResume.hidden=active;ui.onlineResume.disabled=sending||!available;ui.onlineRetry.hidden=ui.onlineSkip.hidden=!stage?.failed;
      ui.onlineEnd.hidden=!finished;ui.onlineAgain.hidden=snapshot.you!==0;ui.onlineAgain.disabled=locked;
      ui.onlineNewWords.hidden=snapshot.you!==0;ui.onlineNewWords.disabled=locked;
      ui.onlinePicker.hidden=!finished||snapshot.you!==0||!picking;
      ui.onlineTopic.disabled=ui.onlineShuffle.disabled=ui.onlineNextCancel.disabled=locked;
      ui.onlineNextStart.disabled=locked||candidates.length!==12;
      ui.onlineProgress.textContent=`Nalezeno ${Object.keys(snapshot.owners).length} z 12 dvojic · ${snapshot.turns} tahů`;
      const byUid=new Map(data.items.map(i=>[i.uid,i]));
      ui.onlineBoard.replaceChildren();
      snapshot.cards.forEach(card=>{
        const slot=doc.createElement('div');slot.className='memory-slot';
        if(card.state==='matched'){slot.className+=' memory-empty';slot.setAttribute('aria-label',`Prázdné místo ${card.index+1}`);ui.onlineBoard.append(slot);return;}
        if(snapshot.phase==='compare'&&snapshot.cards.filter(c=>c.state==='open').every(c=>c.uid===card.uid)&&card.state==='open')slot.classList.add('memory-match');
        const button=doc.createElement('button');button.type='button';button.className='memory-card'+(card.state==='open'?' memory-face':'');button.disabled=locked||snapshot.phase!=='choose'||snapshot.active!==snapshot.you||card.state==='open';
        const number=doc.createElement('span');number.className='memory-number';number.textContent=String(card.index+1);button.append(number);
        const item=byUid.get(card.uid);button.setAttribute('aria-label',item?`Kartička ${card.index+1}: ${item.fr}`:`Kartička ${card.index+1}, zavřená`);
        if(card.state==='open'&&item){
          const image=doc.createElement('img');image.src=new URL('../'+item.thumbnail,win.location.href).toString();image.alt='';image.addEventListener('error',()=>{image.hidden=true;});
          const word=doc.createElement('span');word.lang='fr';word.className='memory-word';word.textContent=item.fr;button.append(image,word);
          if(stage?.hint&&snapshot.phase==='reveal'&&card.index===snapshot.focus){const cz=doc.createElement('span');cz.lang='cs';cz.className='memory-translation';cz.textContent=item.cz;button.append(cz);}
        }
        button.addEventListener('click',()=>{void command('flip',{index:card.index});});slot.append(button);ui.onlineBoard.append(slot);
      });
      ui.onlineScores.replaceChildren();
      snapshot.players.forEach((player,index)=>{
        const panel=doc.createElement('div');panel.className='memory-player memory-player-'+index+(index===snapshot.active&&!finished?' memory-current':'');
        const name=doc.createElement('strong');name.textContent=player?player.name+(index===snapshot.you?' (ty)':''):'Čekáme na spoluhráče';
        const score=doc.createElement('span');score.textContent='Dvojice: '+Object.values(snapshot.owners).filter(owner=>owner===index).length;
        const state=doc.createElement('span');state.textContent=player?.connected?'Připojeno':'Odpojeno';panel.append(name,score,state);ui.onlineScores.append(panel);
      });
      if(finished){
        const scores=snapshot.players.map((_,i)=>Object.values(snapshot.owners).filter(v=>v===i).length);
        ui.onlineResult.textContent=scores[0]===scores[1]?'Remíza!':`Vyhrává ${snapshot.players[scores[0]>scores[1]?0:1].name}!`;
        ui.onlineCollections.replaceChildren();snapshot.players.forEach((player,index)=>{
          const details=doc.createElement('details'),summary=doc.createElement('summary'),list=doc.createElement('div');list.className='memory-collection';summary.textContent=player.name+' · získané dvojice';details.append(summary);
          Object.entries(snapshot.owners).filter(([,owner])=>owner===index).forEach(([uid])=>{const item=byUid.get(uid),button=doc.createElement('button'),image=doc.createElement('img'),word=doc.createElement('span');button.type='button';image.src=new URL('../'+item.thumbnail,win.location.href).toString();image.alt='';word.textContent=item.fr;button.append(image,word);button.addEventListener('click',()=>{void play(M.audioRecord(item,manifest).fr);});list.append(button);});details.append(list);ui.onlineCollections.append(details);
        });
      }
      if(!active)status('Partie je pozastavená. Připoj se znovu se zapnutým zvukem.');
      else if(!network)status('Spojení vypadlo. Čekáme na návrat k partii.');
      else if(snapshot.paused)status('Partie je pozastavená. Čekáme na připojení spoluhráče.');
      else if(snapshot.phase==='waiting')status(snapshot.players[1]?'Oba jste v místnosti. Zakladatel může zahájit hru.':'Pošli soukromý odkaz spoluhráči.');
      else if(finished)status(snapshot.you===0?'Všech 12 dvojic je nalezených. Můžeš připravit další partii tady ve stejné místnosti.':'Všech 12 dvojic je nalezených. Počkej tady, zakladatel může připravit další partii.');
      else if(snapshot.phase==='choose')status(snapshot.active===snapshot.you?'Jsi na tahu. Vyber '+(snapshot.cards.some(c=>c.state==='open')?'druhou':'první')+' kartičku.':`Na tahu: ${snapshot.players[snapshot.active].name}.`);
      else if(!stage?.failed)status(snapshot.phase==='compare'?'Porovnej oba obrázky…':snapshot.phase==='reward'?'Správně! Poslechni si slovo ještě jednou.':'Posloucháme na obou počítačích…');
    }
    async function enter(){
      if(sending||!available)return;
      sending=true;const ticket=++epoch;render();
      try{
        // Start on this user gesture, then reuse this same element for remote turns.
        const heard=await play(M.audioRecord(data.items.find(i=>M.audioRecord(i,manifest)?.fr),manifest).fr);
        if(!heard)throw Error('Zvuk se nepodařilo zapnout. Klikni na vstup znovu.');
        if(ticket!==epoch)return;
        if(!session){
          const name=Array.from(ui.onlineName.value.trim()).slice(0,12).join('');if(!name)throw Error('Zadej svoje jméno.');
          session={version:1,name,token:random(win),requestId:random(win),uids:selection.map(i=>i.uid),room:route.get('room')||'',invite:route.get('invite')||random(win),mode:route.has('room')?'guest':'host'};save();
        }
        let value;
        if(session.mode==='guest'&&!session.joined){value=await post('join',{name:session.name,playerToken:session.token,invite:session.invite},false);session.joined=true;save();}
        else if(session.room){value=await post('ready');}
        else{value=await post('create',{name:session.name,playerToken:session.token,invite:session.invite,uids:session.uids,requestId:session.requestId},false);session.room=value.room;save();}
        active=true;network=true;sending=false;
        win.history.replaceState(null,'','online.html#room='+session.room);accept(value);schedule();
      }catch(error){
        status(error.message||'Připojení se nepodařilo. Zkus pokračovat znovu.');
        if(ticket===epoch){sending=false;ui.onlineEnter.disabled=false;ui.onlineResume.disabled=false;}
      }
    }
    function leave(){
      const prior=active;active=false;network=false;epoch++;sending=false;win.clearTimeout(pollTimer);cancelStage();
      if(prior&&session?.room)void fetcher(API+'/'+session.room+'/leave',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+session.token},body:'{}',credentials:'omit',keepalive:true}).catch(()=>{});
      render();
    }
    async function init(){
      try{
        const texts=await Promise.all(['vocabulary-fr-v2.json','vocabulary-fr-audio.json','vocabulary-fr-quiz.json'].map(name=>read('../data/'+name,true)));
        [data,manifest,quiz]=texts.map(JSON.parse);data.catalog={groups:data.groups,parents:data.parents};
        ui.onlineTopic.replaceChildren();
        [{id:'',label:'Všechny okruhy'},...(data.groups||[])].forEach(group=>{const option=doc.createElement('option');option.value=group.id;option.textContent=group.label;ui.onlineTopic.append(option);});
        const digest=await win.crypto.subtle.digest('SHA-256',new TextEncoder().encode(texts.join('\0')));revision=Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
        const requested=route.get('words')?.split(',');const pool=requested?data.items.filter(i=>requested.includes(i.uid)):data.items;selection=Memory.choose(pool,manifest,quiz,()=>.5);
        if(route.has('room')&&!roomPattern.test(route.get('room')))throw Error('Pozvánka není platná.');
        try{const stored=JSON.parse(win.sessionStorage.getItem(KEY));if(stored?.version===1&&tokenPattern.test(stored.token)&&stored.mode&&stored.name&&((stored.room&&stored.room===route.get('room'))||(!stored.room&&!route.has('room'))))session=stored;}catch(_){}
        if(route.has('room')&&!session&&!tokenPattern.test(route.get('invite')||''))throw Error('V tomto prohlížeči chybí přístup k partii. Otevři původní pozvánku.');
        if(session)ui.onlineName.value=session.name;
        ui.onlineSelection.textContent=route.has('room')?'Připojíš se ke společné partii.':`Připraveno ${selection.length} různých dvojic ze zvolených slovíček.`;
        const info=await read(API+'/health');
        if(info.protocol!==1||info.catalog!==revision)throw Error('Společná hra používá jinou verzi slovníku. Obnov stránku.');
        available=route.has('room')||selection.length===12;
        ui.onlineEnter.textContent=session?'Pokračovat a zapnout zvuk':route.has('room')?'Vstoupit a zapnout zvuk':'Založit partii a zapnout zvuk';
        status(available?'Zadej jméno a připoj se se zapnutým zvukem.':'Výběr potřebuje 12 různých obrázků s francouzským zvukem. Rozšiř ho v Přehledu.');
      }catch(error){available=false;status(error.message||'Společná hra je momentálně nedostupná.');}
      render();
    }
    ui.onlineEnter.addEventListener('click',()=>{void enter();});ui.onlineResume.addEventListener('click',()=>{void enter();});
    ui.onlineStart.addEventListener('click',()=>{void command('start');});ui.onlineAgain.addEventListener('click',()=>{void command('rematch');});
    ui.onlineNewWords.addEventListener('click',()=>{ui.onlineTopic.value='';chooseNext();});
    ui.onlineTopic.addEventListener('change',chooseNext);ui.onlineShuffle.addEventListener('click',chooseNext);
    ui.onlineNextCancel.addEventListener('click',()=>{picking=false;candidates=[];render();});
    ui.onlineNextStart.addEventListener('click',()=>{if(picking&&candidates.length===12)void command('rematch',{uids:candidates.map(item=>item.uid)});});
    ui.onlineRetry.addEventListener('click',()=>{cancelStage();syncStage();});ui.onlineSkip.addEventListener('click',()=>{if(stage?.failed){stage.failed=false;void command('heard',{stage:snapshot.stage});}});
    ui.onlineCopy.addEventListener('click',()=>{const copy=win.navigator?.clipboard?.writeText(ui.onlineInvite.value);void Promise.resolve(copy||Promise.reject(Error('clipboard'))).then(()=>status('Pozvánka je zkopírovaná. Pošli ji spoluhráči.'),()=>status('Odkaz můžeš označit v poli a zkopírovat ručně.'));});
    ui.onlineBack.addEventListener('click',event=>{if(snapshot&&snapshot.phase!=='finished'&&!win.confirm('Opustit společnou partii? Spoluhráč počká na tvůj návrat.'))event.preventDefault();else leave();});
    ui.onlineReward.addEventListener('cancel',event=>event.preventDefault());ui.onlineRewardImage.addEventListener('error',()=>{ui.onlineRewardImage.hidden=true;});
    win.addEventListener('pagehide',leave);doc.addEventListener('visibilitychange',()=>{if(doc.hidden)leave();});
    return {init,enter,poll,leave,command,getState:()=>snapshot};
  }
  const api={KEY,create};if(typeof module!=='undefined'&&module.exports)module.exports=api;else{root.VocabularyFROnline=api;void create({doc:root.document,win:root.window}).init();}
})(globalThis);
