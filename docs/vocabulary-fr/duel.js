/* Two-player listening duel. Timed answers and points belong to the server. */
(function(root){
  'use strict';
  const M=typeof module!=='undefined'&&module.exports?require('./model.js'):root.VocabularyFRModel;
  const Memory=typeof module!=='undefined'&&module.exports?require('./memory.js'):root.VocabularyFRMemory;
  const KEY='vocabulary-fr.duel-session.v1',API='/api/vocabulary-fr/rooms';
  const tokenPattern=/^[a-f0-9]{64}$/,roomPattern=/^[a-f0-9]{24}$/;
  function random(win){const bytes=new Uint8Array(32);win.crypto.getRandomValues(bytes);return Array.from(bytes,b=>b.toString(16).padStart(2,'0')).join('');}

  function create({doc,win,fetcher=root.fetch.bind(root),AudioClass=root.Audio,ImageClass=win.Image}){
    const ids=['duelView','duelStatus','duelStorage','duelSetup','duelName','duelSelection','duelEnter','duelRoom','duelInvitePanel','duelInvite','duelCopy','duelProgress','duelStart','duelResume','duelRetry','duelSkip','duelChangeFilter','duelAnnouncement','duelCountdown','duelBoard','duelFeedback','duelImage','duelWord','duelRoundResult','duelNext','duelEnd','duelResult','duelAgain','duelPicker','duelTopic','duelPart','duelLevel','duelType','duelRecent','duelQuery','duelPoolNotice','duelApply','duelCancel','duelScores','duelBack'];
    ids.push('duelTiming','duelTextSeconds','duelImageSeconds','duelTimingNotice');
    const ui=Object.fromEntries(ids.map(id=>[id,doc.getElementById(id)]));
    const route=new URLSearchParams(new URL(win.location.href).hash.slice(1));
    const audio=new AudioClass(),images=new Map(),loadedImages=new Map();
    let data,manifest,quiz,revision='',selection=[],candidates=[],snapshot=null,session=null;
    let available=false,active=false,network=false,sending=false,picking=false,candidateValid=false,epoch=0,pollTimer=null;
    let work=null,windowState=null,windowTimer=null,cancelAudio=null,boardKey='';
    let clockBase={local:0,server:0};
    const now=()=>win.performance?.now?.()??Date.now();
    const serverNow=()=>clockBase.server+now()-clockBase.local;
    const status=text=>{ui.duelStatus.textContent=text;};
    const itemFor=uid=>data.items.find(item=>item.uid===uid);
    const source=path=>new URL('../'+path,win.location.href).toString();
    function save(){try{win.sessionStorage.setItem(KEY,JSON.stringify(session));}catch(_){ui.duelStorage.textContent='Přístup zůstává v tomto panelu. Obnovení po zavření není dostupné, protože prohlížeč nepovolil uložení.';}}
    function stopAudio(){cancelAudio?.();cancelAudio=null;audio.pause();}
    function cancelWork(){
      if(work){work.cancelled=true;for(const [id,resolve] of work.waits){win.clearTimeout(id);resolve();}}
      work=null;stopAudio();
    }
    function cancelWindow(){win.clearTimeout(windowTimer);windowTimer=null;windowState=null;boardKey='';ui.duelBoard.hidden=true;ui.duelCountdown.hidden=true;}
    function wait(local,ms){return new Promise(resolve=>{const id=win.setTimeout(()=>{local.waits.delete(id);resolve();},ms);local.waits.set(id,resolve);});}
    async function bounded(fn,ms=8000){
      const controller=new root.AbortController();let timer;
      const deadline=new Promise((_,reject)=>{timer=win.setTimeout(()=>{controller.abort();reject(Error('Spojení trvá příliš dlouho. Připoj se znovu.'));},ms);});
      try{return await Promise.race([fn(controller.signal),deadline]);}finally{win.clearTimeout(timer);}
    }
    async function read(path,text=false){
      return bounded(async signal=>{const response=await fetcher(path,{signal,cache:'no-store'});if(!response.ok)throw Error('Podklady nebo služba duelu nejsou dostupné.');return text?response.text():response.json();},20000);
    }
    function play(path){
      stopAudio();audio.src=source(path);audio.load();
      return new Promise(resolve=>{
        let done=false;
        const finish=ok=>{if(done)return;done=true;win.clearTimeout(timer);audio.removeEventListener('ended',ended);audio.removeEventListener('error',failed);if(cancelAudio===cancel)cancelAudio=null;resolve(ok);};
        const ended=()=>finish(true),failed=()=>finish(false),cancel=()=>finish(false),timer=win.setTimeout(failed,20000);
        cancelAudio=cancel;audio.addEventListener('ended',ended);audio.addEventListener('error',failed);
        try{Promise.resolve(audio.play()).catch(failed);}catch(_){failed();}
      });
    }
    function image(path){
      if(images.has(path))return images.get(path);
      const task=new Promise((resolve,reject)=>{
        const picture=new ImageClass();let done=false;
        const finish=ok=>{if(done)return;done=true;win.clearTimeout(timer);picture.onload=picture.onerror=null;if(ok){loadedImages.set(path,picture);resolve(picture);}else reject(Error('Obrázek se nepodařilo načíst.'));};
        const timer=win.setTimeout(()=>finish(false),20000);
        picture.onload=()=>finish(true);picture.onerror=()=>finish(false);picture.src=source(path);
        if(picture.decode)void picture.decode().then(()=>finish(true),()=>finish(false));
      });
      images.set(path,task);void task.catch(()=>images.delete(path));return task;
    }
    async function post(action,payload={},authenticated=true){
      const path=action==='create'?API:API+'/'+session.room+'/'+action;
      const headers={'Content-Type':'application/json'};if(authenticated)headers.Authorization='Bearer '+session.token;
      const started=now();
      const value=await bounded(async signal=>{
        const response=await fetcher(path,{method:'POST',headers,body:JSON.stringify(payload),signal,cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer'});
        const result=await response.json();if(!response.ok){const error=Error(result.error||'Akce se nepodařila.');error.status=response.status;throw error;}return result;
      });
      // A monotonic clock plus measured round trip avoids relying on wall clocks.
      if(Number.isFinite(value.serverTime)&&(!snapshot||value.revision>=snapshot.revision))clockBase={local:now(),server:value.serverTime*1000+(now()-started)/2};
      return value;
    }
    function accept(value){
      if(value.protocol!==1||value.mode!=='duel'||value.catalog!==revision||value.room!==session.room||![0,1].includes(value.you)||!Array.isArray(value.choices)||![0,12].includes(value.choices.length)||value.choices.some(uid=>!itemFor(uid))||!Number.isFinite(value.serverTime))throw Error('Partie neodpovídá této verzi duelu.');
      if(snapshot&&value.revision<snapshot.revision)return;
      if(snapshot&&value.round!==snapshot.round){picking=false;candidates=[];cancelWork();cancelWindow();}
      snapshot=value;network=true;render();syncPhase();
    }
    function schedule(){win.clearTimeout(pollTimer);if(active)pollTimer=win.setTimeout(()=>{void poll();},600);}
    function disconnect(message){leave();status(message||'Spojení se přerušilo. Pokračuj opětovným zapnutím zvuku.');}
    async function poll(){
      if(!active)return;if(sending){schedule();return;}
      const ticket=epoch;
      try{const value=await post('sync');if(ticket===epoch&&active)accept(value);}
      catch(error){if(ticket===epoch)disconnect(error.message);}
      finally{if(ticket===epoch)schedule();}
    }
    async function command(action,payload={}){
      if(sending||!active||!snapshot)return false;
      sending=true;const ticket=epoch;let failure=null;render();
      try{const value=await post(action,{requestId:random(win),expectedRound:snapshot.round,expectedStage:snapshot.stage,...payload});if(ticket===epoch&&active)accept(value);return true;}
      catch(error){if(ticket===epoch){if(error.status)failure=error.message;else disconnect('Spojení se přerušilo. Připoj se znovu; uloženou odpověď ověříme bez opakovaného kliknutí.');}return false;}
      finally{if(ticket===epoch){sending=false;render();if(failure)status(failure);schedule();}}
    }
    function syncPhase(){
      if(!active||!network||snapshot.paused){cancelWork();cancelWindow();return;}
      if(snapshot.phase==='duel_choose'){
        cancelWork();
        if(snapshot.choices.some(uid=>!loadedImages.has(itemFor(uid).thumbnail))){disconnect('Obrázky ještě nejsou připravené. Pokračuj a kolo připravíme znovu.');return;}
        const key=snapshot.round+':'+snapshot.stage;
        if(windowState?.key!==key){
          cancelWindow();
          const opens=now()+snapshot.opensAt*1000-serverNow();
          // A late/reloaded client must receive a fresh full window, not a fraction.
          if(opens<now()-150){disconnect('Časové okno dorazilo pozdě. Pokračuj a současné kolo zopakujeme.');return;}
          const pictureAt=snapshot.pictureAt??snapshot.opensAt+2;
          if(!Number.isFinite(pictureAt)||!Number.isFinite(snapshot.closesAt)||pictureAt<=snapshot.opensAt||snapshot.closesAt<=pictureAt){disconnect('Herní služba poslala neplatné časování.');return;}
          windowState={key,opens,pictureAt:opens+(pictureAt-snapshot.opensAt)*1000,closes:opens+(snapshot.closesAt-snapshot.opensAt)*1000,choice:snapshot.ownAnswer,closedSent:snapshot.closed};
        }
        tick();return;
      }
      cancelWindow();
      if(!['duel_intro','duel_result'].includes(snapshot.phase)){cancelWork();return;}
      const key=snapshot.round+':'+snapshot.stage;
      if(work?.key===key)return;
      cancelWork();if(snapshot.acks.includes(snapshot.you))return;
      const local={key,stage:snapshot.stage,cancelled:false,waits:new Map(),failed:null,imagesReady:false};work=local;
      const intro=snapshot.phase==='duel_intro',item=intro?null:itemFor(snapshot.target);
      const sound=intro?snapshot.promptAudio:M.audioRecord(item,manifest)?.fr;
      const paths=intro?snapshot.choices.map(uid=>itemFor(uid).thumbnail):[item.image];
      const prepared=Promise.all(paths.map(image)).then(()=>true,()=>false);
      const heard=intro?play(sound):prepared.then(loaded=>{
        if(!loaded||local.cancelled||!active)return false;
        render();return play(sound);
      });
      const minimum=intro?wait(local,3000):prepared.then(loaded=>loaded&&!local.cancelled?wait(local,2000):undefined);
      void (async()=>{
        const [played,loaded]=await Promise.all([heard,prepared,minimum]);
        if(local.cancelled||work!==local||!active)return;
        local.imagesReady=loaded;
        if(!loaded||!played){local.failed=loaded?'audio':'images';render();status(loaded?'Zvuk se nepodařilo přehrát. Zopakuj ho nebo výslovně pokračuj bez zvuku.':'Obrázky se nepodařilo načíst. Zopakuj přípravu; čas na odpověď ještě neběží.');return;}
        await command('heard',{stage:local.stage});
      })();
    }
    function tick(){
      win.clearTimeout(windowTimer);
      if(!windowState||!active||!network||snapshot.paused)return;
      const left=windowState.closes-now(),visible=now()>=windowState.opens&&left>0;
      ui.duelBoard.hidden=!visible;ui.duelCountdown.hidden=!visible;
      ui.duelCountdown.textContent=Math.max(0,Math.ceil(left/1000))+' s';
      renderBoard(!active||!network||snapshot.paused||sending);
      ui.duelAnnouncement.hidden=visible;
      if(!visible)ui.duelAnnouncement.textContent=left>0?'Připraveno…':'Kolo skončilo. Čekáme na uzavření odpovědí.';
      if(left<=-180&&!windowState.closedSent&&!sending&&!snapshot.closed&&now()>=(windowState.retryAt||0)){
        const current=windowState;current.closedSent=true;
        void command('closed').then(ok=>{if(!ok&&active&&windowState===current){current.closedSent=false;current.retryAt=now()+600;}});
      }
      const pictureAt=windowState.pictureAt;
      const boundary=now()<windowState.opens?windowState.opens:now()<pictureAt?pictureAt:now()<windowState.closes?windowState.closes:now()<windowState.closes+180?windowState.closes+180:Infinity;
      windowTimer=win.setTimeout(tick,Math.max(1,Math.min(40,boundary-now())));
    }
    function renderBoard(locked){
      if(!windowState)return;
      const choice=snapshot.ownAnswer??windowState.choice;
      const key=windowState.key+':'+choice;
      if(boardKey!==key){
        boardKey=key;ui.duelBoard.replaceChildren();
        snapshot.choices.forEach((uid,index)=>{
          const item=itemFor(uid),button=doc.createElement('button'),picture=loadedImages.get(item.thumbnail),word=doc.createElement('span');
          button.type='button';button.className='duel-card';button.setAttribute('aria-pressed',String(choice===index));
          button.setAttribute('aria-label',`Kartička ${index+1}: ${item.fr}`);picture.alt='';word.lang='fr';word.textContent=item.fr;
          button.append(picture,word);button.addEventListener('click',()=>{
            if(!windowState||!active||!network||snapshot.paused||sending||now()<windowState.opens||now()>=windowState.closes||windowState.choice!==null||snapshot.ownAnswer!==null)return;
            windowState.choice=index;render();void command('answer',{index});
          });ui.duelBoard.append(button);
        });
      }
      const textOnly=now()<windowState.pictureAt;
      for(const button of ui.duelBoard.children){
        button.disabled=locked||choice!==null;
        button.classList.toggle('duel-text-only',textOnly);
        button.querySelector('img').hidden=textOnly;
      }
    }
    function render(){
      ui.duelSetup.hidden=Boolean(snapshot);ui.duelRoom.hidden=!snapshot;ui.duelEnter.disabled=!available||sending;
      if(!snapshot)return;
      ui.duelView.dataset.playing=String(snapshot.phase!=='waiting');
      const locked=!active||!network||snapshot.paused||sending,host=snapshot.you===0,finished=snapshot.phase==='finished';
      const timingSupported=[2,3,4].includes(snapshot.textSeconds)&&[1,2].includes(snapshot.imageSeconds);
      ui.duelTiming.hidden=!host;
      ui.duelTextSeconds.value=String(snapshot.textSeconds??2);ui.duelImageSeconds.value=String(snapshot.imageSeconds??1);
      ui.duelTextSeconds.disabled=ui.duelImageSeconds.disabled=!host||!active||!network||sending||!timingSupported;
      ui.duelTimingNotice.textContent=!timingSupported?'Změna časů vyžaduje aktualizaci herní služby.':`Pro další kola: text ${snapshot.textSeconds} s + obrázek ${snapshot.imageSeconds} s = ${snapshot.textSeconds+snapshot.imageSeconds} s. Rozehrané kolo se nemění.`;
      ui.duelResume.hidden=active;ui.duelResume.disabled=sending||!available;
      ui.duelInvitePanel.hidden=!session.invite||session.mode!=='host'||snapshot.players[1]!==null;
      const invite=new URL('duel.html',win.location.href);invite.hash=new URLSearchParams({room:session.room,invite:session.invite||''}).toString();ui.duelInvite.value=invite.toString();
      ui.duelStart.hidden=!host||snapshot.phase!=='waiting';ui.duelStart.disabled=locked||!snapshot.players.every(p=>p?.connected);
      ui.duelNext.hidden=!host||snapshot.phase!=='duel_between';ui.duelNext.disabled=locked;
      ui.duelAgain.hidden=!host;ui.duelAgain.disabled=locked;ui.duelEnd.hidden=!finished;
      ui.duelChangeFilter.hidden=!host||snapshot.phase==='waiting';ui.duelChangeFilter.disabled=locked;
      ui.duelPicker.hidden=!host||!picking;ui.duelCancel.disabled=sending;
      ui.duelApply.disabled=locked||!candidateValid;
      for(const id of ['duelTopic','duelPart','duelLevel','duelType','duelRecent','duelQuery'])ui[id].disabled=locked;
      ui.duelRetry.hidden=!work?.failed||snapshot.acks.includes(snapshot.you);ui.duelSkip.hidden=work?.failed!=='audio'||snapshot.acks.includes(snapshot.you);
      ui.duelRetry.disabled=ui.duelSkip.disabled=locked;
      ui.duelProgress.textContent=`Kolo ${snapshot.question} z ${snapshot.questionCount} · ${snapshot.poolCount} slov v zásobě`;
      const showing=['duel_result','duel_between','finished'].includes(snapshot.phase);
      ui.duelFeedback.hidden=!showing;ui.duelAnnouncement.hidden=showing||snapshot.phase==='waiting';
      if(showing){
        const item=itemFor(snapshot.target),picture=loadedImages.get(item.image);
        if(picture&&ui.duelImage!==picture){picture.id='duelImage';picture.width=600;picture.height=600;ui.duelImage=picture;ui.duelFeedback.replaceChildren(picture,ui.duelWord,ui.duelRoundResult);}
        ui.duelImage.hidden=!picture;ui.duelImage.alt=item.fr;ui.duelWord.textContent=item.fr;
        const target=snapshot.choices.indexOf(snapshot.target);
        ui.duelRoundResult.textContent=snapshot.players.map((p,i)=>`${p.name}: ${snapshot.answers?.[i]===target?'správně (+1)':snapshot.answers?.[i]===undefined?'bez odpovědi':'chybná odpověď'}`).join(' · ');
      }else if(snapshot.phase==='duel_intro')ui.duelAnnouncement.textContent=snapshot.question===1?'Začíná nové kolo':'Další kolo';
      ui.duelScores.replaceChildren();snapshot.players.forEach((p,i)=>{
        const panel=doc.createElement('div'),name=doc.createElement('strong'),score=doc.createElement('span'),presence=doc.createElement('span');
        panel.className='memory-player memory-player-'+i;name.textContent=p?p.name+(i===snapshot.you?' (ty)':''):'Čekáme na spoluhráče';score.textContent='Počet bodů: '+snapshot.scores[i];presence.textContent=p?.connected?'Připojeno':'Odpojeno';panel.append(name,score,presence);ui.duelScores.append(panel);
      });
      if(finished)ui.duelResult.textContent=snapshot.scores[0]===snapshot.scores[1]?'Remíza!':`Vyhrává ${snapshot.players[snapshot.scores[0]>snapshot.scores[1]?0:1].name}!`;
      renderBoard(locked);
      if(!active||!network)status('Hra čeká na návrat. Pokračuj se zapnutým zvukem.');
      else if(snapshot.paused)status('Čekáme na připojení spoluhráče.');
      else if(snapshot.phase==='waiting')status(snapshot.players[1]?'Oba jste připraveni. Vyzyvatel může zahájit hru.':'Pošli pozvánku spoluhráči.');
      else if(snapshot.phase==='duel_intro')status('Posloucháme české zadání a připravujeme obrázky na obou počítačích.');
      else if(snapshot.phase==='duel_choose')status(snapshot.ownAnswer!==null||windowState?.choice!==null&&windowState?.choice!==undefined?'Odpověď je zamčená. Vyhodnotíme ji po skončení kola.':'Vyber správnou kartičku. Máš jednu odpověď.');
      else if(snapshot.phase==='duel_result')status('Poslechni si správné francouzské slovíčko.');
      else if(snapshot.phase==='duel_between')status(host?'Oba jste dokončili poslech. Můžeš spustit další kolo.':'Další kolo spustí vyzyvatel.');
      else if(finished)status('Všech 12 kol je dokončených. Další hru zahájíte ve stejné místnosti.');
    }
    function choosePool(){
      const pool=M.select(data.items,{topics:ui.duelTopic.value?[ui.duelTopic.value]:[],parts:ui.duelPart.value?[ui.duelPart.value]:[],levels:ui.duelLevel.value?[ui.duelLevel.value]:[],teachingType:ui.duelType.value,query:ui.duelQuery.value,recentCount:Number(ui.duelRecent.value)});
      candidates=Memory.duelPool(pool,manifest,quiz);
      const enough=Memory.choose(candidates,manifest,quiz,()=>.5).length===12;candidateValid=enough;
      ui.duelPoolNotice.textContent=enough?`Zásoba: ${candidates.length} slov. Vylosujeme 12 různých zadání; pomocné kartičky se mohou opakovat.`:'Potřebujeme alespoň 12 odlišných obrázků s oběma zvuky. Rozšiř filtr.';
      render();if(!enough)ui.duelApply.disabled=true;
    }
    async function enter(){
      if(sending||!available)return;
      sending=true;const ticket=++epoch;render();
      try{
        const sample=data.items.find(i=>M.audioRecord(i,manifest)?.fr);
        if(!await play(M.audioRecord(sample,manifest).fr))throw Error('Zvuk se nepodařilo zapnout. Klikni na vstup znovu.');
        if(ticket!==epoch)return;
        if(!session){
          const name=Array.from(ui.duelName.value.trim()).slice(0,12).join('');if(!name)throw Error('Zadej svoje jméno.');
          session={version:1,name,token:random(win),requestId:random(win),uids:selection.map(i=>i.uid),room:route.get('room')||'',invite:route.get('invite')||random(win),mode:route.has('room')?'guest':'host'};save();
        }
        let value;
        if(session.mode==='guest'&&!session.joined){value=await post('join',{name:session.name,playerToken:session.token,invite:session.invite},false);session.joined=true;save();}
        else if(session.room)value=await post('ready');
        else{value=await post('create',{mode:'duel',name:session.name,playerToken:session.token,invite:session.invite,uids:session.uids,requestId:session.requestId},false);session.room=value.room;save();}
        if(ticket!==epoch)return;
        active=true;network=true;sending=false;win.history.replaceState(null,'','duel.html#room='+session.room);accept(value);schedule();
      }catch(error){if(ticket===epoch){sending=false;render();status(error.message||'Připojení se nepodařilo.');}}
    }
    function leave(){
      const prior=active;active=false;network=false;sending=false;epoch++;win.clearTimeout(pollTimer);cancelWork();cancelWindow();
      if(prior&&session?.room)void fetcher(API+'/'+session.room+'/leave',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+session.token},body:'{}',credentials:'omit',keepalive:true}).catch(()=>{});
      render();
    }
    async function init(){
      try{
        const texts=await Promise.all(['vocabulary-fr-v2.json','vocabulary-fr-audio.json','vocabulary-fr-quiz.json'].map(name=>read('../data/'+name,true)));
        [data,manifest,quiz]=texts.map(JSON.parse);data.catalog={groups:data.groups,parents:data.parents};
        const digest=await win.crypto.subtle.digest('SHA-256',new TextEncoder().encode(texts.join('\0')));revision=Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,'0')).join('');
        const requested=route.get('words')?.split(',');selection=Memory.duelPool(requested?data.items.filter(i=>requested.includes(i.uid)):data.items,manifest,quiz);
        if(route.has('room')&&!roomPattern.test(route.get('room')))throw Error('Pozvánka není platná.');
        try{const stored=JSON.parse(win.sessionStorage.getItem(KEY));if(stored?.version===1&&tokenPattern.test(stored.token)&&['host','guest'].includes(stored.mode)&&stored.name&&((stored.room&&stored.room===route.get('room'))||(!stored.room&&!route.has('room'))))session=stored;}catch(_){}
        if(route.has('room')&&!session&&!tokenPattern.test(route.get('invite')||''))throw Error('Otevři původní pozvánku; v tomto panelu chybí přístup do hry.');
        if(session)ui.duelName.value=session.name;
        for(const [id,labels,all] of [['duelPart',M.posLabels,'Všechny druhy'],['duelLevel',M.levelLabels,'Všechny obtížnosti'],['duelType',M.teachingTypeLabels,'Všechny typy']]){
          for(const [value,label] of [['',all],...Object.entries(labels)]){const option=doc.createElement('option');option.value=value;option.textContent=label;ui[id].append(option);}ui[id].value='';
        }
        for(const topic of [{id:'',label:'Všechny okruhy'},...data.groups]){const option=doc.createElement('option');option.value=topic.id;option.textContent=topic.label;ui.duelTopic.append(option);}
        ui.duelTopic.value='';ui.duelRecent.value='0';ui.duelQuery.value='';
        const info=await read(API+'/health');
        if(info.protocol!==1||info.catalog!==revision||!info.games?.includes('duel'))throw Error('Herní služba zatím tento duel nepodporuje. Je potřeba aktualizovat také samostatný herní server.');
        available=route.has('room')||Memory.choose(selection,manifest,quiz,()=>.5).length===12;
        ui.duelSelection.textContent=route.has('room')?'Připojíš se do společného duelu.':`Zásoba z filtru: ${selection.length} slov. Hra má 12 různých zadání.`;
        ui.duelEnter.textContent=session?'Pokračovat a zapnout zvuk':route.has('room')?'Vstoupit a zapnout zvuk':'Založit duel a zapnout zvuk';
        status(available?'Zadej jméno a zapni zvuk.':'Rozšiř filtr: potřebujeme 12 odlišných obrázků s českým i francouzským zvukem.');
      }catch(error){available=false;status(error.message||'Duel se nepodařilo načíst.');}
      render();
    }
    ui.duelEnter.addEventListener('click',()=>{void enter();});ui.duelResume.addEventListener('click',()=>{void enter();});
    ui.duelStart.addEventListener('click',()=>{void command('start');});ui.duelNext.addEventListener('click',()=>{void command('next');});
    for(const id of ['duelTextSeconds','duelImageSeconds'])ui[id].addEventListener('change',()=>{
      if(snapshot?.you!==0||ui[id].disabled)return;
      void command('timing',{textSeconds:Number(ui.duelTextSeconds.value),imageSeconds:Number(ui.duelImageSeconds.value)});
    });
    ui.duelAgain.addEventListener('click',()=>{void command('rematch');});
    ui.duelChangeFilter.addEventListener('click',()=>{if(snapshot?.you!==0)return;picking=true;choosePool();ui.duelPicker.scrollIntoView({block:'nearest'});});
    for(const id of ['duelTopic','duelPart','duelLevel','duelType','duelRecent'])ui[id].addEventListener('change',choosePool);
    ui.duelQuery.addEventListener('input',choosePool);ui.duelCancel.addEventListener('click',()=>{picking=false;render();});
    ui.duelApply.addEventListener('click',()=>{
      if(!picking||snapshot?.you!==0||ui.duelApply.disabled)return;
      if(snapshot.phase!=='finished'&&!win.confirm('Začít novou hru s tímto filtrem? Dosavadní skóre se vynuluje. Hráči a pozvánka zůstanou.'))return;
      void command('restart',{uids:candidates.map(i=>i.uid)});
    });
    ui.duelRetry.addEventListener('click',()=>{cancelWork();syncPhase();});
    ui.duelSkip.addEventListener('click',()=>{if(work?.failed==='audio'&&work.imagesReady)void command('heard',{stage:work.stage});});
    ui.duelCopy.addEventListener('click',()=>{void Promise.resolve(win.navigator?.clipboard?.writeText(ui.duelInvite.value)||Promise.reject(Error('clipboard'))).then(()=>status('Pozvánka je zkopírovaná.'),()=>status('Označ odkaz v poli a zkopíruj ho ručně.'));});
    ui.duelBack.addEventListener('click',event=>{if(snapshot&&snapshot.phase!=='finished'&&!win.confirm('Opustit duel? Spoluhráč počká na tvůj návrat.'))event.preventDefault();else leave();});
    win.addEventListener('pagehide',leave);doc.addEventListener('visibilitychange',()=>{if(doc.hidden)leave();});
    return {init,enter,poll,command,leave,getState:()=>snapshot};
  }
  const api={KEY,create};if(typeof module!=='undefined'&&module.exports)module.exports=api;else{root.VocabularyFRDuel=api;void create({doc:root.document,win:root.window}).init();}
})(globalThis);
