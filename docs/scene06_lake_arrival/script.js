'use strict';
(() => {
  const story = window.SCENE06_STORY;
  const el = Object.fromEntries(['picture','back','language','repeat','speech','speaker','en','cz','notes','hotspot','next','song','gate'].map(id => [id, document.getElementById(id)]));
  const images = {farewell:'../scene05_log_bridge/scene05_friends_farewell_smooth_q90.webp', arrival:'arrival.webp', duckfrog:'duckfrog.webp', flyotter:'flyotter.webp', final:'final.webp'};
  const descriptions = {farewell:'Kamarádi se loučí s Loganem; Bruno drží lampu',arrival:'Kamarádi přicházejí k jezeru',duckfrog:'Kamarádi zdraví Daisy a Freddieho u jezera',flyotter:'Kamarádi zdraví Dotty a Ollieho u jezera',final:'Přátelé společně slaví na břehu jezera'};
  const spots = {light:[70,35,18,20,'Klepni na světlo'],daisy:[42,47,19,36,'Pozdrav Daisy'],drum:[69,68,19,28,'Klepni na listový bubínek'],dotty:[8,26,22,25,'Pozdrav Dotty'],shells:[55,53,12,20,'Klepni na mušle'],song:[28,70,40,18,'Přehraj jezerní písničku']};
  let index=-1, busy=false, done=false, generation=0, currentAudio=null, cancelPending=null, notes=0, context=null, oscillators=[];
  let bilingual=true; try { bilingual=localStorage.getItem('mmtx-language-mode') !== 'en'; } catch (_) {}
  const show=(node,yes)=>node.classList.toggle('hidden',!yes);
  function controls() {
    const row=story[index], active=index>=0&&!busy&&!done, waiting=!!(row && row[4]);
    el.language.disabled=busy; el.repeat.disabled=index<0||busy; show(el.next,active&&!waiting); el.next.disabled=!active||waiting;
    show(el.hotspot,active&&waiting); el.hotspot.disabled=!active||!waiting;
    show(el.song,done&&!busy); el.song.disabled=!done||busy;
    el.language.textContent=bilingual?'EN + CZ':'EN'; el.language.setAttribute('aria-pressed',String(bilingual)); show(el.cz,bilingual);
  }
  function stop() {
    el.notes.classList.toggle('singing',false); generation++; if(currentAudio){currentAudio.pause();currentAudio=null;} if(cancelPending){const cancel=cancelPending;cancelPending=null;cancel();}
    for(const osc of oscillators){try {osc.stop();}catch(_) {}} oscillators=[];
    if(context && context.state==='running') context.suspend().catch(()=>{});
    busy=false; if(index===story.length-1)done=true; controls();
  }
  function audio(path, token) {
    return new Promise(resolve=>{
      if(!path || token!==generation || document.hidden){resolve();return;}
      const player=new Audio(path); currentAudio=player; let ended=false;
      const finish=()=>{if(ended)return; ended=true;clearTimeout(timer);if(currentAudio===player)currentAudio=null;if(cancelPending===finish)cancelPending=null;resolve();};
      const timer=setTimeout(()=>{player.pause();finish();},15000); cancelPending=finish;
      player.addEventListener('ended',finish,{once:true}); player.addEventListener('error',finish,{once:true});
      try {const promise=player.play();if(promise && promise.catch)promise.catch(finish);}catch(_){finish();}
    });
  }
  async function playLine(i) {
    if(i<0||busy)return; busy=true;const token=++generation;const row=story[i];
    el.picture.src=images[row[3]];el.picture.alt=descriptions[row[3]];el.speaker.textContent=row[0];el.en.textContent=row[1];el.cz.textContent=row[2];show(el.speech,true);
    el.speech.classList.toggle('align-right',row[4]==='dotty');
    if(row[4]){const [x,y,w,h,label]=spots[row[4]];Object.assign(el.hotspot.style,{left:x+'%',top:y+'%',width:w+'%',height:h+'%'});el.hotspot.setAttribute('aria-label',label);}
    controls();const number=String(i).padStart(3,'0');
    await audio((window.SCENE06_AUDIO.en||{})[number],token);
    if(token===generation && bilingual)await audio((window.SCENE06_AUDIO.cs||{})[number],token);
    if(token!==generation)return;
    busy=false;if(i===story.length-1)done=true;controls();
  }
  function addNote(){notes++;const n=document.createElement('span');n.className='note';n.textContent='♪';n.setAttribute('aria-hidden','true');el.notes.appendChild(n);}
  function effect(kind){
    if(kind==='song')el.notes.classList.toggle('singing',true);
    try {const C=window.AudioContext||window.webkitAudioContext;if(!C)return;if(!context)context=new C();if(context.state==='suspended')context.resume().catch(()=>{});
      const tones=kind==='song'?[392,440,523,659]:kind==='shells'?[720,900]:kind==='drum'?[180]:kind==='dotty'?[440]:[540];
      for(let i=0;i<tones.length;i++){const osc=context.createOscillator(), gain=context.createGain();osc.type=kind==='dotty'?'sawtooth':'sine';osc.frequency.value=tones[i];const t=context.currentTime+i*.23;gain.gain.setValueAtTime(.0001,t);gain.gain.exponentialRampToValueAtTime(.08,t+.02);gain.gain.exponentialRampToValueAtTime(.0001,t+.18);osc.connect(gain);gain.connect(context.destination);osc.start(t);osc.stop(t+.2);oscillators.push(osc);osc.onended=()=>{oscillators=oscillators.filter(x=>x!==osc);};}
    }catch(_){}
  }
  el.gate.addEventListener('click',()=>{if(index>=0)return;show(el.gate,false);index=0;playLine(index);});
  el.next.addEventListener('click',()=>{if(busy||index<0||done||story[index][4])return;index++;playLine(index);});
  el.hotspot.addEventListener('click',async()=>{if(busy||index<0||done||!story[index][4])return;const kind=story[index][4];busy=true;const token=++generation;controls();effect(kind);await new Promise(resolve=>{const timer=setTimeout(resolve,kind==='song'?950:500);cancelPending=()=>{clearTimeout(timer);resolve();};});if(token!==generation)return;cancelPending=null;el.notes.classList.toggle('singing',false);if(['daisy','drum','dotty','shells'].includes(kind))addNote();busy=false;index++;playLine(index);});
  el.repeat.addEventListener('click',()=>{if(!busy&&index>=0)playLine(index);});
  el.language.addEventListener('click',()=>{if(busy)return;bilingual=!bilingual;try{localStorage.setItem('mmtx-language-mode',bilingual?'en-cz':'en');}catch(_){}controls();});
  el.song.addEventListener('click',async()=>{if(busy||!done)return;busy=true;const token=++generation;controls();effect('song');await new Promise(resolve=>{const timer=setTimeout(resolve,950);cancelPending=()=>{clearTimeout(timer);resolve();};});if(token!==generation)return;cancelPending=null;el.notes.classList.toggle('singing',false);busy=false;controls();});
  el.back.addEventListener('click',stop);window.addEventListener('pagehide',stop);document.addEventListener('visibilitychange',()=>{if(document.hidden)stop();});
  controls();
})();
