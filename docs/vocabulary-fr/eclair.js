(function(root){
  'use strict';
  const API='/api/vocabulary-fr/rooms', KEY='vocabulary-fr.eclair.session.v1';
  const TOKEN=/^[a-f0-9]{64}$/, ROOM=/^[a-f0-9]{24}$/;
  const PHASES=['waiting','eclair_loading','eclair_prepare','eclair_active','eclair_result','eclair_wait_guest','finished'];
  const mediaPath=path=>typeof path==='string'&&/^\/eclair-media\/[a-f0-9]{64}\.(mp3|webp|png|svg)$/.test(path);
  const resultKey=s=>s.room+':'+s.round;
  const random=win=>{const b=new Uint8Array(32);win.crypto.getRandomValues(b);return Array.from(b,n=>n.toString(16).padStart(2,'0')).join('');};
  function finalText(s){
    const a=s.players[0].name,b=s.players[1].name,[x,y]=s.scores;
    return x===y?`Remíza! ${a} i ${b}: ${x} z ${s.maxScore} bodů.`:`Vyhrává ${x>y?a:b}. ${a}: ${x}, ${b}: ${y}. Maximum pro každého: ${s.maxScore} bodů.`;
  }
  function create({doc,win,fetcher=root.fetch.bind(root),AudioClass=root.Audio,ImageClass=root.Image}){
    const ids=['Back','Status','Storage','Setup','Name','Options','Rounds','Seconds','Rules','Enter','Room','InvitePanel','Invite','Copy','Scores','Progress','Timer','Confirm','Start','Resume','Next','Again','Play','Prompt','Pronouns','Verbs','PronounNotice','VerbNotice','Hint','Segments','Feedback','Sentence','Variant','RoundPoints','Repeat','AudioNotice','End','Final'];
    const ui=Object.fromEntries(ids.map(v=>[v,doc.getElementById('eclair'+v)]));
    const route=new URLSearchParams(new URL(win.location.href).hash.slice(1));
    const invitation=ROOM.test(route.get('room')||'')&&TOKEN.test(route.get('invite')||'')?{room:route.get('room'),invite:route.get('invite')}:null;
    const audio=new AudioClass(),cachedImages=new Map(),pendingColumns=new Set();
    let session=null,snapshot=null,health=null,active=false,busy=false,connected=false,exited=false;
    let pollTimer=null,recoveryTimer=null,recoveryCount=0,recovering=false,epoch=0;
    let clock={server:0,local:0},boardKey='',hintKey='',prepareKey='',playing=0;
    let cancelAudio=null,played=new Set();
    const now=()=>win.performance?.now?.()??Date.now();
    const serverNow=()=>clock.server+now()-clock.local;
    const status=message=>{if(ui.Status.textContent!==message)ui.Status.textContent=message;};
    function save(){
      if(!session)return;
      session.played=Array.from(played).slice(-1000);
      try{win.sessionStorage.setItem(KEY,JSON.stringify(session));}
      catch(_){ui.Storage.textContent='Prohlížeč nepovolil uložení přístupu. Nezavírej tento panel; připojení teď zůstává v něm.';}
    }
    function stopAudio(){playing++;cancelAudio?.();cancelAudio=null;audio.pause();}
    function play(path){
      stopAudio();
      return new Promise(resolve=>{
        if(!path){resolve(false);return;}
        let done=false,timer;
        const finish=value=>{if(done)return;done=true;win.clearTimeout(timer);audio.removeEventListener('ended',ended);audio.removeEventListener('error',failed);if(cancelAudio===failed)cancelAudio=null;resolve(value);};
        const ended=()=>finish(true),failed=()=>finish(false);
        cancelAudio=failed;timer=win.setTimeout(failed,20000);
        audio.addEventListener('ended',ended);audio.addEventListener('error',failed);
        audio.src=new URL(path,win.location.href).toString();audio.load();
        try{Promise.resolve(audio.play()).catch(failed);}catch(_){failed();}
      });
    }
    async function sample(){
      if(!health?.eclair?.sampleAudio)return false;
      const ok=await play(health.eclair.sampleAudio);
      if(!ok)ui.AudioNotice.textContent='Ukázku nelze přehrát. Hra zůstává dostupná; vzor můžeš později přehrát tlačítkem.';
      return ok;
    }
    async function request(path,payload,token){
      const controller=new root.AbortController();let timer;
      const headers={'Content-Type':'application/json'};if(token)headers.Authorization='Bearer '+token;
      const start=now();
      const task=(async()=>{
        const response=await fetcher(path,{method:payload===undefined?'GET':'POST',headers,body:payload===undefined?undefined:JSON.stringify(payload),signal:controller.signal,cache:'no-store',credentials:'omit',referrerPolicy:'no-referrer'});
        let value;
        try{value=await response.json();}catch(_){throw Object.assign(Error('Herní služba na této adrese není dostupná. Otevři Francouzštinu Jana z Cockpitu.'),{status:response.status});}
        if(!response.ok)throw Object.assign(Error(value.error||'Spojení se nepodařilo.'),{status:response.status});
        if(Number.isFinite(value.serverTime)&&(!snapshot||value.revision>=snapshot.revision))clock={server:value.serverTime*1000+(now()-start)/2,local:now()};
        return value;
      })();
      const deadline=new Promise((_,reject)=>{timer=win.setTimeout(()=>{controller.abort();reject(Error('Spojení trvá příliš dlouho.'));},10000);});
      try{return await Promise.race([task,deadline]);}finally{win.clearTimeout(timer);}
    }
    const post=(action,payload={})=>request(API+'/'+session.room+'/'+action,payload,session.token);
    function valid(s){
      return s?.protocol===1&&s.mode==='eclair'&&s.room===session.room&&s.catalog===health.catalog&&s.eclairCatalog===health.eclair.catalog&&
        PHASES.includes(s.phase)&&[0,1].includes(s.you)&&Array.isArray(s.players)&&s.players.length===2&&
        Number.isInteger(s.round)&&s.round>0&&Number.isInteger(s.revision)&&Number.isFinite(s.serverTime)&&
        Array.isArray(s.pronounCards)&&Array.isArray(s.verbCards)&&s.pronounCards.length<9&&s.verbCards.length<7&&
        [...s.pronounCards,...s.verbCards].every(c=>typeof c.id==='string'&&typeof c.text==='string')&&
        Array.isArray(s.segments)&&s.segments.every(s=>typeof s.text==='string'&&(!s.image||mediaPath(s.image)))&&
        (!s.result?.audio||mediaPath(s.result.audio));
    }
    function accept(s){
      if(!valid(s))throw Object.assign(Error('Partie neodpovídá této verzi hry. Ověř novou pozvánku.'),{status:409});
      if(snapshot&&s.revision<snapshot.revision)return;
      if(snapshot&&snapshot.round!==s.round){stopAudio();prepareKey='';}
      snapshot=s;connected=true;render();phaseWork();
    }
    function recoverable(error){return !error.status||error.status===408||error.status===429||error.status>=500;}
    function disconnected(error){
      active=false;connected=false;busy=false;pendingColumns.clear();epoch++;
      win.clearTimeout(pollTimer);win.clearTimeout(recoveryTimer);stopAudio();
      recovering=!exited&&recoverable(error);render();status((error.message||'Spojení se přerušilo.')+(recovering?' Obnovuji připojení ke stejné partii.':''));
      if(recovering)scheduleRecovery();
    }
    function scheduleRecovery(){
      win.clearTimeout(recoveryTimer);
      if(!recovering||doc.hidden)return;
      recoveryTimer=win.setTimeout(()=>{void recover();},Math.min(8000,1000*2**Math.min(recoveryCount++,3)));
    }
    async function recover(){
      if(!recovering||busy||exited)return;
      busy=true;const turn=epoch;
      try{
        const value=await post('ready');if(turn!==epoch||exited)return;
        active=true;recovering=false;recoveryCount=0;prepareKey='';accept(value);schedule();
      }catch(error){if(turn===epoch){busy=false;disconnected(error);}}finally{if(turn===epoch){busy=false;render();}}
    }
    function schedule(){win.clearTimeout(pollTimer);if(active&&!doc.hidden&&!exited)pollTimer=win.setTimeout(()=>{void poll();},snapshot?.phase==='eclair_active'?250:600);}
    async function poll(){
      const turn=epoch;if(!active||exited)return;
      try{const value=await post('sync');if(turn===epoch&&!exited)accept(value);}
      catch(error){if(turn===epoch)disconnected(error);}finally{if(turn===epoch)schedule();}
    }
    async function mutate(action,extra={},column=null){
      if(!active||!connected||!snapshot||exited||(!column&&busy)||(column&&pendingColumns.has(column)))return;
      const turn=epoch,payload={requestId:random(win),expectedRound:snapshot.round,expectedStage:snapshot.stage,...extra};
      if(column)pendingColumns.add(column);else busy=true;render();
      try{const value=await post(action,payload);if(turn===epoch&&!exited)accept(value);}
      catch(error){
        if(turn===epoch){if(error.status===409){status(error.message);void poll();}else disconnected(error);}
      }finally{if(turn===epoch){if(column)pendingColumns.delete(column);else busy=false;render();}}
    }
    function imageReady(path){
      if(cachedImages.has(path))return cachedImages.get(path);
      const task=new Promise(resolve=>{
        const image=new ImageClass();let done=false;
        const end=()=>{if(done)return;done=true;win.clearTimeout(timer);image.onload=image.onerror=null;resolve();};
        const timer=win.setTimeout(end,6000);image.onload=image.onerror=end;image.src=new URL(path,win.location.href).toString();
        if(image.decode)void image.decode().then(end,end);
      });cachedImages.set(path,task);return task;
    }
    function phaseWork(){
      if(!active||!snapshot)return;
      if(snapshot.phase==='eclair_loading'&&!snapshot.prepared){
        const key=resultKey(snapshot);if(prepareKey===key)return;prepareKey=key;const turn=epoch;
        void Promise.all(snapshot.segments.filter(s=>s.image).map(s=>imageReady(s.image))).then(()=>{
          if(turn===epoch&&snapshot?.phase==='eclair_loading'&&!snapshot.prepared&&!exited)void mutate('prepared');
        });
      }
      if(snapshot.result){
        const key=resultKey(snapshot);if(played.has(key))return;played.add(key);save();
        void playResult();
      }
    }
    async function playResult(){
      const s=snapshot;if(!s?.result||!active)return;
      if(!s.result.audio){ui.AudioNotice.textContent='Vzor není dostupný. Můžeš pokračovat podle zobrazené věty.';return;}
      ui.AudioNotice.textContent='Vzor · poslech správné francouzské věty.';
      const ticket=playing+1,ok=await play(s.result.audio);
      if(snapshot?.round===s.round&&ticket===playing)ui.AudioNotice.textContent=ok?'Vzor · poslech správné francouzské věty.':'Zvuk se nepodařilo přehrát. Použij Přehrát vzor; další kolo není blokované.';
    }
    const glyphs={'score':'+1','calendar':'▦','day-timeline':'☀ · ☾','name-badge':'🏷','knowledge':'💡','complete':'✓','need':'!','price':'€','word':'Aa','lesson':'📖','recipe':'☰','time':'◷'};
    function segmentNode(s){
      if(s.image||s.visual){
        const figure=doc.createElement('figure');figure.className='eclair-picture';
        if(s.image){const image=doc.createElement('img');image.alt='';image.width=144;image.height=144;image.src=s.image;image.addEventListener('error',()=>{image.hidden=true;});figure.appendChild(image);}
        else{const icon=doc.createElement('span');icon.className='eclair-visual';icon.setAttribute('aria-hidden','true');icon.textContent=s.visual==='number'?({deux:'2',huit:'8',dix:'10',cinquante:'50'}[s.text]||'#'):(glyphs[s.visual]||'◇');figure.appendChild(icon);}
        const caption=doc.createElement('figcaption');caption.textContent=s.text;figure.appendChild(caption);return figure;
      }
      const span=doc.createElement('span');span.className='eclair-segment';span.textContent=s.text;return span;
    }
    function renderHints(){
      const key=snapshot?resultKey(snapshot)+':'+(snapshot.phase==='waiting'?'waiting':'shown'):'';if(key===hintKey)return;hintKey=key;
      ui.Hint.replaceChildren();ui.Segments.replaceChildren();
      for(const segment of snapshot?.segments||[])(segment.role==='hint_only'?ui.Hint:ui.Segments).appendChild(segmentNode(segment));
    }
    function renderChoices(){
      const s=snapshot,on=s?.phase==='eclair_active';
      const key=on?s.pronounCards.concat(s.verbCards).map(c=>c.id).join(':'):'';
      if(key!==boardKey){
        boardKey=key;ui.Pronouns.replaceChildren();ui.Verbs.replaceChildren();
        if(on)for(const [column,cards,container] of [['pronoun',s.pronounCards,ui.Pronouns],['verb',s.verbCards,ui.Verbs]])for(const card of cards){
          const button=doc.createElement('button');button.type='button';button.className='eclair-card';button.dataset.card=card.id;button.dataset.text=card.text;
          button.addEventListener('click',()=>{if(!button.disabled)void mutate('answer',{column,cardId:card.id},column);});container.appendChild(button);
        }
      }
      for(const [column,container,notice] of [['pronoun',ui.Pronouns,ui.PronounNotice],['verb',ui.Verbs,ui.VerbNotice]]){
        const own=s?.ownColumns?.[column],locked=Boolean(own&&serverNow()<own.lockUntil*1000),solved=Boolean(own?.solved);
        for(const button of container.children){
          const chosen=solved&&button.dataset.text===own.chosen,wrong=locked&&button.dataset.card===own.wrong;
          button.disabled=!active||!connected||!on||solved||locked||pendingColumns.has(column)||serverNow()>=s.deadlineAt*1000;
          button.className='eclair-card'+(chosen?' solved':wrong?' wrong':button.disabled?' locked':'');
          button.textContent=(chosen?'✓ ':wrong?'✕ ':'')+button.dataset.text;button.setAttribute('aria-pressed',chosen?'true':'false');
        }
        const message=solved?'✓ Správně · +1 bod':locked?'✕ Tento sloupec je na 1 s zamčený.':on?'Vyber jednu kartu.':s?.phase==='eclair_prepare'?'Volby se objeví po přípravě.':'';
        if(notice.textContent!==message)notice.textContent=message;
      }
    }
    function renderScores(){
      ui.Scores.replaceChildren();for(let n=0;n<2;n++){
        const row=doc.createElement('div');row.className='eclair-score'+(snapshot?.you===n?' own':'');
        const name=doc.createElement('span');name.textContent=(snapshot?.players[n]?.name||'Čekáme na spoluhráče')+(snapshot?.players[n]&&!snapshot.players[n].connected?' · odpojený':'');
        const points=doc.createElement('strong');points.textContent=String(snapshot?.scores[n]??0)+' bodů';row.appendChild(name);row.appendChild(points);ui.Scores.appendChild(row);
      }
    }
    function render(){
      const s=snapshot;ui.Setup.hidden=Boolean(session?.room&&session.complete);ui.Room.hidden=!ui.Setup.hidden;
      doc.body.classList.toggle('eclair-in-game',Boolean(s&&s.phase!=='waiting'));
      ui.Options.hidden=Boolean(invitation)||Boolean(session?.pending==='join');ui.Enter.disabled=busy||!health?.eclair;
      ui.Name.disabled=Boolean(session?.pending);ui.Rounds.disabled=Boolean(session?.pending);ui.Seconds.disabled=Boolean(session?.pending);
      if(session?.pending)ui.Enter.textContent='Ověřit původní vstup a zapnout zvuk';
      ui.Resume.hidden=!session?.complete||active;ui.Resume.disabled=busy;
      if(!s)return;
      const host=s.you===0,enabled=active&&connected&&!busy,phase=s.phase;
      ui.InvitePanel.hidden=!host||phase!=='waiting';ui.Invite.value=session.inviteUrl||'';
      ui.Progress.textContent=`Kolo ${s.roundIndex} z ${s.roundCount} · ${s.settings.seconds} s na odpověď · maximum ${s.maxScore} bodů`;
      ui.Confirm.hidden=!(s.you===1&&((phase==='waiting'&&!s.confirmed[1])||phase==='eclair_wait_guest'));
      ui.Confirm.textContent=phase==='waiting'?`Souhlasím: ${s.settings.rounds} kol, ${s.settings.seconds} s`:'Jsem připravený na další kolo';ui.Confirm.disabled=!enabled;
      ui.Start.hidden=!(host&&phase==='waiting');ui.Start.disabled=!enabled||!s.confirmed[1]||!s.players.every(p=>p?.connected);
      ui.Next.hidden=!(host&&phase==='eclair_result');ui.Next.disabled=!enabled;
      ui.Again.hidden=!(host&&phase==='finished');ui.Again.disabled=!enabled;
      ui.Play.hidden=!['eclair_loading','eclair_prepare','eclair_active'].includes(phase);
      ui.Prompt.textContent=s.promptCs||'';renderHints();renderChoices();renderScores();
      ui.Feedback.hidden=!s.result;ui.End.hidden=phase!=='finished';
      if(s.result){ui.Sentence.textContent=s.result.sentenceFr;ui.Variant.hidden=s.result.variantFr===s.result.sentenceFr;ui.Variant.textContent='Tvoje varianta: '+s.result.variantFr;
        ui.RoundPoints.textContent=s.players.map((p,n)=>`${p.name}: +${s.result.points[n]}`).join(' · ');ui.Repeat.disabled=!active||!s.result.audio;}
      if(phase==='finished')ui.Final.textContent=finalText(s);
      if(active){
        const messages={waiting:s.you===1?(s.confirmed[1]?'Nastavení potvrzené. Hru zahájí zakladatel.':'Potvrď nastavení společné hry.'):(s.players[1]?'Po potvrzení nastavení můžeš zahájit hru.':'Pošli soukromou pozvánku spoluhráči.'),eclair_loading:'Připravuji obrázky pro oba hráče…',eclair_prepare:'Přečti si českou větu. Za chvíli se objeví volby.',eclair_active:'Vybírej v libovolném pořadí. Každý sloupec se hodnotí samostatně.',eclair_result:host?'Výsledek kola. Až budete připravení, nabídni další kolo.':'Výsledek kola. Čekáme na nabídku dalšího kola.',eclair_wait_guest:host?'Čekáme na potvrzení spoluhráče.':'Potvrď, že jsi připravený pokračovat.',finished:'Hra dokončena. Novou partii můžete začít ve stejné místnosti.'};status(messages[phase]);
      }
      tick();
    }
    function tick(){
      const s=snapshot;if(!s)return;
      const end=s.phase==='eclair_prepare'?s.startAt:s.phase==='eclair_active'?s.deadlineAt:null;
      ui.Timer.textContent=end===null?'':Math.max(0,(end*1000-serverNow())/1000).toFixed(1)+' s';
      if(s.phase==='eclair_active')renderChoices();
    }
    async function enter(){
      if(busy||!health?.eclair||exited)return;busy=true;ui.Enter.disabled=true;const turn=epoch;
      try{
        if(!session||session.complete){
          const name=ui.Name.value.trim();if(!name||Array.from(name).length>12)throw Object.assign(Error('Zadej jméno o 1–12 znacích.'),{status:400});
          session={token:random(win),name,played:[],pending:invitation?'join':'create'};
          if(invitation)Object.assign(session,invitation);
          else Object.assign(session,{invite:random(win),createId:random(win),rounds:Number(ui.Rounds.value),seconds:Number(ui.Seconds.value)});
          played=new Set();save();
        }
        await sample();
        if(turn!==epoch||exited)return;
        const value=session.pending==='join'?await request(API+'/'+session.room+'/join',{name:session.name,playerToken:session.token,invite:session.invite}):await request(API,{mode:'eclair',name:session.name,playerToken:session.token,invite:session.invite,requestId:session.createId,rounds:session.rounds,seconds:session.seconds});
        if(turn!==epoch||exited)return;
        session.host=session.pending==='create';session.room=value.room;session.complete=true;delete session.pending;
        if(session.host){const url=new URL('eclair.html',win.location.href);url.hash=new URLSearchParams({room:session.room,invite:session.invite}).toString();session.inviteUrl=url.toString();}
        save();active=true;connected=true;accept(value);schedule();
      }catch(error){status((error.message||'Vstup se nepodařil.')+' Pokud není jasný výsledek spojení, stejným tlačítkem ověř původní vstup.');ui.Enter.textContent=session?.pending?'Ověřit původní vstup a zapnout zvuk':'Vstoupit a zapnout zvuk';}
      finally{busy=false;render();}
    }
    async function resume(){
      if(busy||!session?.complete||exited)return;busy=true;render();const turn=epoch;
      try{await sample();if(turn!==epoch||exited)return;const s=await post('ready');if(turn!==epoch||exited)return;active=true;recovering=false;recoveryCount=0;prepareKey='';accept(s);schedule();}
      catch(error){disconnected(error);}finally{busy=false;render();}
    }
    function leave(){
      if(exited)return;exited=true;active=false;recovering=false;epoch++;win.clearTimeout(pollTimer);win.clearTimeout(recoveryTimer);win.clearInterval(ticker);stopAudio();
      if(session?.complete)void fetcher(API+'/'+session.room+'/leave',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+session.token},body:'{}',keepalive:true,credentials:'omit',referrerPolicy:'no-referrer'}).catch(()=>{});
    }
    ui.Enter.addEventListener('click',()=>{void enter();});ui.Resume.addEventListener('click',()=>{void resume();});
    ui.Confirm.addEventListener('click',()=>{void mutate('confirm');});ui.Start.addEventListener('click',()=>{void mutate('start');});
    ui.Next.addEventListener('click',()=>{void mutate('next');});ui.Again.addEventListener('click',()=>{void mutate('rematch');});ui.Repeat.addEventListener('click',()=>{void playResult();});
    ui.Copy.addEventListener('click',()=>{void Promise.resolve().then(()=>win.navigator.clipboard.writeText(ui.Invite.value)).then(()=>status('Pozvánka je zkopírovaná.'),()=>{ui.Invite.focus();ui.Invite.select();status('Vyber a zkopíruj celý odkaz v poli pozvánky.');});});
    ui.Back.addEventListener('click',leave);win.addEventListener('pagehide',leave);
    win.addEventListener('online',()=>{if(recovering)void recover();});
    win.addEventListener('pageshow',event=>{if(event.persisted&&exited){exited=false;epoch++;active=false;connected=false;ticker=win.setInterval(tick,100);render();status('Po návratu do panelu pokračuj a zapni zvuk.');}});
    doc.addEventListener('visibilitychange',()=>{
      if(doc.hidden){win.clearTimeout(pollTimer);stopAudio();return;}
      if(recovering)void recover();else if(active)void poll();
    });
    let ticker=win.setInterval(tick,100);
    async function init(){
      try{
        if((route.has('room')||route.has('invite'))&&!invitation)throw Error('Pozvánka není úplná nebo platná. Požádej zakladatele o celý odkaz.');
        try{const value=JSON.parse(win.sessionStorage.getItem(KEY)||'null');if(value&&TOKEN.test(value.token||'')&&(!value.room||ROOM.test(value.room))&&(!value.complete||ROOM.test(value.room||''))&&typeof value.name==='string'&&(!value.pending||TOKEN.test(value.invite||''))&&(value.pending!=='create'||TOKEN.test(value.createId||''))&&(!invitation||value.room===invitation.room)){session=value;played=new Set(Array.isArray(value.played)?value.played.filter(v=>typeof v==='string').slice(-1000):[]);ui.Name.value=value.name;}}catch(_){}
        if(invitation){ui.Options.hidden=true;ui.Enter.textContent='Připojit se a zapnout zvuk';win.history.replaceState(null,'',new URL(win.location.href).pathname);}
        health=await request(API+'/health');
        if(!health.eclair||!health.games?.includes('eclair'))throw Error('La phrase éclair na této adrese zatím není připravená. Otevři Francouzštinu Jana z Cockpitu po aktualizaci herní služby.');
        if(session?.pending==='create'){ui.Rounds.value=String(session.rounds);ui.Seconds.value=String(session.seconds);}
        ui.Rules.textContent+=` K dispozici je ${health.eclair.roundCount} ověřených vět.`;
        render();status(session?.complete?'Pokračuj ve své partii a zapni zvuk.':session?.pending?'Ověř původní vstup. Použijeme stejné jméno, nastavení a přístup.':invitation?'Zadej jméno a připoj se ke společné hře.':'Vyber počet kol a čas; po založení pošli spoluhráči pozvánku.');
      }catch(error){ui.Enter.disabled=true;status(error.message);}
    }
    return {init,leave,enter,resume,poll,recover,mutate,get state(){return snapshot;},get session(){return session;}};
  }
  const api={create,finalText,mediaPath,resultKey};if(typeof module==='object'&&module.exports)module.exports=api;else root.VocabularyFREclair=api;
  if(root.document?.getElementById('eclairSetup')){const app=create({doc:root.document,win:root});void app.init();}
})(typeof window!=='undefined'?window:globalThis);
