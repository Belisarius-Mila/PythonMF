"use strict";
const M = globalThis.VocabularyModel;
const appRoot = document.querySelector("[data-json-url]");
const DATA_URL = appRoot?.dataset.jsonUrl || "../data/vocabulary-en.json";
const AUDIO_DATA_URL = appRoot?.dataset.audioUrl || "../data/vocabulary-en-audio.json";
const SENTENCE_AUDIO_URL = "../data/vocabulary-en-sentence-audio.json";
const QUIZ_DATA_URL = "../data/vocabulary-en-quiz.json";
const galleryModeHint=document.getElementById("galleryModeHint");
const ui = Object.fromEntries(["galleryView","studyView","totalCount","totalLabel","searchInput","topicPicker","topicFilters","topicSummary","clearTopicsButton","filterSelect","teachingTypeSelect","groupSelect","sortSelect","sizeButton","partFilters","levelFilters","sourceFilters","continueButton","shuffleButton","resetButton","emptyResetButton","sectionNav","galleryNotice","galleryGroups","emptyState","galleryFooter","backButton","backBottomButton","studyPosition","wordImage","pictureFallback","speakPromptButton","promptLabel","promptText","messageStrip","revealButton","answerCard","answerEn","answerCz","sentenceBox","sentenceEn","sentenceCz","speakAnswerButton","roundStatus","previousButton","nextButton","newRoundButton"].map(id => [id,document.getElementById(id)]));
const defaults = () => ({filter:"all",teachingType:"all",query:"",topics:[],sources:[],parts:[],levels:[],groupBy:"topic",sort:"recommended",labelLanguage:"en",direction:"czToEn",practice:"words",large:false,learner:"all",onlyLearnerHard:false,recentCount:0});
const state = {data:null,audioManifest:null,sentenceAudioManifest:null,items:[],...defaults(),galleryMode:"learn",currentItem:null,revealed:false,view:"gallery",sequence:[],index:0,mode:"ordered",lastUid:"",visitId:"",fromGallery:false,anchorOffset:120};
const loopUI=Object.fromEntries(["studyLoopMode","studyLoopGap","studyLoopToggle","studyLoopStop","studyLoopStatus","studyLoopTranslation"].map(id=>[id,document.getElementById(id)]));
// Runtime only: history, reload and bfcache never start sound automatically.
const studyLoop={mode:"words",gap:2000,active:false,running:false,phase:"words",generation:0,cancelWait:null};
let loopAudio=null;
let galleryTranslation=null;
let learnerUI=null;
let quizUI=null,quizCatalog=null;
const learnerSelect=document.getElementById("learnerSelect"),learnerHardFilter=document.getElementById("learnerHardFilter"),editLearnerHard=document.getElementById("editLearnerHard");
const STORAGE_KEY="vocabulary-en.navigation.v1", LAST_KEY="vocabulary-en.last-card.v1";
function context() { return Object.fromEntries(Object.keys(defaults()).map(key => [key,Array.isArray(state[key]) ? [...state[key]] : state[key]])); }
function sanitizeContext(value={}) {
  const result=defaults();
  for(const [key,allowed] of Object.entries({filter:["all","selected","hard"],teachingType:["all","word","interaction","idiom"],groupBy:["topic","part","level","none"],sort:["recommended","en","cz"],labelLanguage:["en","cz"],direction:["czToEn","enToCz"],practice:["words","sentences"]})) if(allowed.includes(value[key]))result[key]=value[key];
  const groups=(state.data?.catalog?.groups || []).map(group=>group.id);
  for(const [key,allowed] of Object.entries({topics:groups,sources:["benji"],parts:[...Object.keys(M.posLabels),"expression"],levels:["1","2","3","unclassified"]}))result[key]=Array.isArray(value[key]) ? [...new Set(value[key].filter(v=>allowed.includes(String(v))).map(String))].slice(0,50) : [];
  result.query=typeof value.query==="string" ? value.query.slice(0,200) : "";
  result.large=value.large===true;
  result.learner=["A","B","C","D"].includes(value.learner)?value.learner:"all";
  result.onlyLearnerHard=result.learner!=="all"&&value.onlyLearnerHard===true;
  result.recentCount=M.recentCount(value.recentCount);
  return result;
}
function readStorage(storage,key) { try { const value=storage.getItem(key); return value && value.length<100000 ? JSON.parse(value) : null; } catch(_){return null;} }
function savedNavigation() { try{return readStorage(window.sessionStorage,STORAGE_KEY);}catch(_){return null;} }
function savedLast() { try{return readStorage(window.localStorage,LAST_KEY);}catch(_){return null;} }
function persist() {
  const saved={version:1,revision:state.data?.revision,context:context(),sequence:state.sequence.map(M.key),currentUid:state.currentItem ? M.key(state.currentItem) : state.lastUid,mode:state.mode,view:state.view,visitId:state.visitId,fromGallery:state.fromGallery,anchorOffset:state.anchorOffset};
  try{window.sessionStorage.setItem(STORAGE_KEY,JSON.stringify(saved));}catch(_){}
  if(state.lastUid)try{window.localStorage.setItem(LAST_KEY,JSON.stringify({uid:state.lastUid,context:context()}));}catch(_){}
}
function routeUrl(kind,uid="") {
  const params=new URLSearchParams(), current=context();
  if(kind==="quiz")params.set("game","listen-pictures");
  if(uid)params.set(kind==="study" ? "card" : "last",uid);
  for(const key of Object.keys(defaults())) {
    const value=current[key], fallback=defaults()[key];
    if(Array.isArray(value)){if(value.length)params.set(key,value.join(","));}
    else if(value!==fallback)params.set(key,String(value));
  }
  const url=new URL(window.location.href);url.hash=params.toString();return url.pathname+url.search+url.hash;
}
function writeHistory(kind,method="replaceState") {
  try{window.history[method]({vocabularyEN:1,kind,visitId:state.visitId,fromGallery:state.fromGallery},"",routeUrl(kind,kind==="study" ? M.key(state.currentItem) : state.lastUid));}catch(_){}
}
function route() {
  const params=new URLSearchParams(new URL(window.location.href).hash.slice(1));
  const raw={};
  for(const key of Object.keys(defaults()))if(params.has(key))raw[key]=Array.isArray(defaults()[key]) ? params.get(key).split(",") : ["large","onlyLearnerHard"].includes(key) ? params.get(key)==="true" : params.get(key);
  return {hasContext:Object.keys(raw).length>0,context:sanitizeContext(raw),card:params.get("card") || "",last:params.get("last") || "",game:params.get("game")==="listen-pictures"};
}
function personalItems(){return learnerUI?learnerUI.filter(state.items,state.learner,state.onlyLearnerHard):state.items;}
function buildSelection(){return M.select(personalItems(),context(),state.items);}
function orderedSelection(){return M.ordered(personalItems(),context(),state.data?.catalog,state.items);}
function updateCounts(selection=buildSelection()) {
  ui.totalCount.textContent=String(selection.length);
  ui.totalLabel.textContent=`${M.countLabel(selection.length).replace(/^\d+ /, "")} ve výběru`;
}
function syncControls(){
  if(!learnerUI?.available){state.learner="all";state.onlyLearnerHard=false;}
  learnerSelect.value=state.learner;learnerSelect.disabled=!learnerUI?.available;
  learnerHardFilter.disabled=editLearnerHard.disabled=state.learner==="all"||!learnerUI?.available;
  learnerHardFilter.setAttribute("aria-pressed",String(state.onlyLearnerHard));
  ui.searchInput.value=state.query;ui.filterSelect.value=state.filter;ui.teachingTypeSelect.value=state.teachingType;ui.groupSelect.value=state.groupBy;ui.sortSelect.value=state.sort;
  ui.sizeButton.setAttribute("aria-pressed",String(state.large));ui.galleryView.classList.toggle("large-tiles",state.large);
  document.getElementById("recentOnly").checked=state.recentCount>0;
  document.getElementById("recentCount").disabled=!state.recentCount;
  document.getElementById("recentCount").value=String(state.recentCount || 20);
  document.querySelectorAll("[data-label]").forEach(button=>button.setAttribute("aria-pressed",String(button.dataset.label===state.labelLanguage)));
  document.querySelectorAll("[data-direction]").forEach(button=>button.setAttribute("aria-pressed",String(button.dataset.direction===state.direction)));
  document.querySelectorAll("[data-practice]").forEach(button=>button.setAttribute("aria-pressed",String(button.dataset.practice===state.practice)));
  for(const [id,key] of [["topicFilters","topics"],["partFilters","parts"],["levelFilters","levels"],["sourceFilters","sources"]])ui[id].querySelectorAll("input").forEach(input=>{input.checked=state[key].includes(input.value);});
  const labels=state.topics.map(id=>state.data?.catalog?.groups.find(group=>group.id===id)?.label).filter(Boolean);
  ui.topicSummary.textContent=labels.length ? labels.join(" + ") : "Všechna témata";
  syncStudyLoopControls();
}
function syncGalleryMode(){
  document.querySelectorAll("[data-gallery-mode]").forEach(button=>button.setAttribute("aria-pressed",String(button.dataset.galleryMode===state.galleryMode)));
  galleryModeHint.textContent=state.galleryMode==="listen" ? "Kliknutí přehraje EN." : "Kliknutí otevře kartu.";
  ui.galleryGroups.querySelectorAll(".vocab-tile").forEach(tile=>tile.setAttribute("aria-label",state.galleryMode==="listen" ? `Přehrát anglicky: ${tile.dataset.en}` : `Učit se: ${tile.dataset.caption}`));
}
function setGalleryMode(mode){
  if(state.view!=="gallery" || !["learn","listen"].includes(mode))return;
  stopAudioPlayback();state.galleryMode=mode;syncGalleryMode();
}
function clearGalleryTranslation(){
  const previous=galleryTranslation;if(!previous)return;
  galleryTranslation=null;window.clearTimeout(previous.timer);
  previous.caption.textContent=previous.text;previous.caption.lang=previous.lang;
}
function flashGalleryTranslation(item,tile){
  const caption=tile?.querySelector(".tile-label");if(!caption || !item.cz)return;
  const flash={caption,text:caption.textContent,lang:caption.lang,timer:null};
  galleryTranslation=flash;caption.textContent=item.cz;caption.lang="cs";
  flash.timer=window.setTimeout(()=>{if(galleryTranslation===flash)clearGalleryTranslation();},1000);
}
async function speakGalleryItem(item,tile){
  if(state.view!=="gallery" || state.galleryMode!=="listen")return;
  stopAudioPlayback();const token=playbackToken;
  flashGalleryTranslation(item,tile);
  const record=M.audioRecord(item,state.audioManifest);
  if(!record?.en){galleryModeHint.textContent="Zvuk zatím není připravený. Zkus to za chvíli.";return;}
  galleryModeHint.textContent=`Anglicky: ${item.en}`;
  try{await playOneAudio(record.en,token);}catch(error){
    if(token===playbackToken && state.view==="gallery" && state.galleryMode==="listen")galleryModeHint.textContent=error.message;
  }
}
function makeCheckOptions(target,options,key){
  for(const option of options){
    const label=document.createElement("label");label.className="check-option";
    const input=document.createElement("input");input.type="checkbox";input.value=option.id;
    const text=document.createElement("span");text.textContent=option.label;label.append(input,text);
    input.addEventListener("change",()=>{state[key]=input.checked ? [...new Set([...state[key],option.id])] : state[key].filter(id=>id!==option.id);selectionChanged();});
    target.append(label);
  }
}
function buildFilterControls(){
  makeCheckOptions(ui.topicFilters,state.data?.catalog?.groups || [],"topics");
  makeCheckOptions(ui.partFilters,Object.entries(M.posLabels).filter(([id])=>id!=="other").map(([id,label])=>({id,label})),"parts");
  makeCheckOptions(ui.levelFilters,Object.entries(M.levelLabels).map(([id,label])=>({id,label})),"levels");
  makeCheckOptions(ui.sourceFilters,[{id:"benji",label:"Benji"}],"sources");
}
function markLast(){
  ui.galleryGroups.querySelectorAll(".vocab-tile").forEach(tile=>{
    const selected=tile.dataset.uid===state.lastUid;tile.classList.toggle("is-last",selected);
    const old=tile.querySelector(".last-caption");if(old)old.remove();
    if(selected){const caption=document.createElement("span");caption.className="last-caption";caption.textContent="Tady jsme skončili";tile.append(caption);}
  });
  ui.continueButton.hidden=!state.lastUid || !orderedSelection().some(item=>M.key(item)===state.lastUid);
}
function renderGallery(){
  stopAudioPlayback();
  if(!learnerUI?.available){state.learner="all";state.onlyLearnerHard=false;}
  const groups=M.buckets(buildSelection(),context(),state.data?.catalog),fragment=document.createDocumentFragment();
  const firstForParent=new Map();let imageIndex=0;
  for(const group of groups){
    const section=document.createElement("section");section.className="vocab-section";section.id=`section-${group.id}`;
    const heading=document.createElement("h2");heading.className="section-title";heading.textContent=group.label;
    const count=document.createElement("span");count.textContent=M.countLabel(group.items.length);heading.append(count);
    const grid=document.createElement("div");grid.className="vocab-grid";
    if(group.parentId && !firstForParent.has(group.parentId))firstForParent.set(group.parentId,section.id);
    for(const item of group.items){
      const tile=document.createElement("button");tile.className="vocab-tile";tile.type="button";tile.dataset.uid=M.key(item);tile.id=`tile-${M.key(item)}`;
      const labelText=state.labelLanguage==="cz" ? item.cz : item.en;
      tile.dataset.en=item.en;tile.dataset.caption=labelText;
      tile.setAttribute("aria-label",`Učit se: ${labelText}`);
      const picture=document.createElement("span");picture.className="tile-picture";
      if(item.thumbnail || item.image){
        const image=document.createElement("img");image.alt="";image.width=384;image.height=384;image.decoding="async";image.loading=imageIndex++<8 ? "eager" : "lazy";
        image.src=new URL(`../${item.thumbnail || item.image}`,window.location.href).toString();
        image.addEventListener("error",()=>{image.hidden=true;picture.textContent="Bez obrázku";},{once:true});picture.append(image);
      }else picture.textContent="Bez obrázku";
      const caption=document.createElement("span");caption.className="tile-label";caption.textContent=labelText;caption.lang=state.labelLanguage==="cz" ? "cs" : "en";
      tile.append(picture,caption);tile.addEventListener("click",()=>{if(state.galleryMode==="listen")void speakGalleryItem(item,tile);else openStudy(M.key(item),"ordered",tile);});grid.append(tile);
    }
    section.append(heading,grid);fragment.append(section);
  }
  ui.galleryGroups.replaceChildren(fragment);ui.galleryGroups.setAttribute("aria-busy","false");ui.sectionNav.replaceChildren();
  if(state.groupBy==="topic")for(const parent of state.data?.catalog?.parents || []){
    const first=firstForParent.get(parent.id);if(!first)continue;
    const link=document.createElement("a");link.href=`#${first}`;link.textContent=parent.label;
    link.addEventListener("click",event=>{event.preventDefault();document.getElementById(first)?.scrollIntoView({block:"start"});});ui.sectionNav.append(link);
  }
  ui.emptyState.hidden=groups.length>0;ui.galleryFooter.hidden=!groups.length;ui.shuffleButton.disabled=!groups.length;
  syncControls();syncGalleryMode();updateCounts();markLast();
}
function selectionChanged(){
  if(state.view!=="gallery")return;
  renderGallery();writeHistory("gallery");persist();
  ui.galleryNotice.textContent=`Ve výběru ${M.countLabel(buildSelection().length)}.${state.groupBy === "level" || state.levels.length ? " Náročnost je orientační návrh pro výuku." : ""}`;
  if(state.learner!=="all"&&!personalItems().length)ui.galleryNotice.textContent=state.onlyLearnerHard?`Uživatel ${state.learner} nemá označená obtížná slova. Použij Výběr obtížných slov.`:`Uživatel ${state.learner} zatím nemá vlastní slovní zásobu. Vyber ji v Nastavení.`;
}
function resetFilters(){Object.assign(state,{filter:"all",teachingType:"all",query:"",topics:[],sources:[],parts:[],levels:[],learner:"all",onlyLearnerHard:false,recentCount:0});selectionChanged();}
function switchView(kind){
  if(kind!=="quiz")quizUI?.leave();
  state.view=kind;ui.galleryView.hidden=kind!=="gallery";ui.studyView.hidden=kind!=="study";
  document.getElementById("quizView").hidden=kind!=="quiz";
  document.getElementById("quizTab").setAttribute("aria-pressed",String(kind==="quiz"));
  document.getElementById("settingsView").hidden=kind!=="settings";
  document.getElementById("settingsTab").setAttribute("aria-pressed",String(kind==="settings"));
  document.getElementById("galleryTab").setAttribute("aria-pressed",String(kind==="gallery"||kind==="study"));
  document.title=kind==="study" && state.currentItem ? `${state.currentItem.en} · Vocabulary EN` : "Vocabulary EN · Slovíčka v obrázcích";
}
function openQuiz({fromHistory=false}={}){
  if(!quizUI)return;
  if(state.view==="settings"&&!learnerUI?.close())return;
  if(state.view!=="quiz")persist();
  quizUI.open();
  if(!fromHistory)writeHistory("quiz","pushState");
}
function returnFromQuiz(){
  if(state.view!=="quiz")return;
  if(window.history.state?.vocabularyEN===1&&window.history.state?.kind==="quiz")window.history.back();
  else showGallery({render:true});
}
function freshVisit(){return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2,10)}`;}
function openStudy(uid,mode="ordered",tile=null){
  stopAudioPlayback();let sequence=orderedSelection();
  if(mode==="random")sequence=M.shuffle(sequence);
  if(!sequence.length)return;
  let index=sequence.findIndex(item=>M.key(item)===uid);if(index<0)index=0;
  state.sequence=sequence;state.index=index;state.mode=mode;state.currentItem=sequence[index];state.revealed=false;state.lastUid=M.key(state.currentItem);
  state.anchorOffset=tile ? tile.getBoundingClientRect().top : 120;
  state.visitId=freshVisit();state.fromGallery=true;
  ui.topicPicker.open=false;writeHistory("gallery");switchView("study");renderCurrentItem();writeHistory("study","pushState");persist();
  window.scrollTo({top:0});ui.studyPosition.focus({preventScroll:true});
}
function renderCurrentItem(){
  const item=state.currentItem;if(!item)return;
  const sentencePractice=state.practice==="sentences",prompt=M.studyPrompt(item,context());
  ui.studyView.classList.toggle("sentence-practice",sentencePractice);
  ui.studyView.setAttribute("aria-label",sentencePractice ? "Procvičování vět" : "Učení slovíčka");
  ui.promptLabel.textContent=prompt.label;
  ui.promptText.textContent=prompt.text;ui.promptText.lang=prompt.language;
  ui.wordImage.hidden=!item.image;ui.pictureFallback.hidden=Boolean(item.image);
  if(item.image)ui.wordImage.src=new URL(`../${item.image}`,window.location.href).toString();else ui.wordImage.removeAttribute("src");
  ui.wordImage.alt=state.direction==="czToEn" ? item.cz : item.en;
  ui.answerEn.textContent=item.en;ui.answerCz.textContent=item.cz;ui.sentenceEn.textContent=item.sentenceEn || "";ui.sentenceCz.textContent=item.sentenceCz || "";
  ui.sentenceBox.hidden=!(item.sentenceEn || item.sentenceCz);ui.answerCard.classList.toggle("hidden",!state.revealed || !prompt.available);
  ui.revealButton.hidden=state.revealed;
  ui.revealButton.disabled=!prompt.available;
  ui.speakPromptButton.textContent=sentencePractice ? "♪ Přehrát větu" : "♪ Přehrát zadání";
  ui.speakAnswerButton.hidden=false;
  ui.speakAnswerButton.textContent=sentencePractice ? "♪ Přehrát překlad" : "♪ Přehrát odpověď";
  ui.messageStrip.textContent=!prompt.available ? "U tohoto slovíčka ještě chybí anglická nebo česká věta. Přepni na Slovíčko nebo pokračuj dál." : sentencePractice ? (state.revealed ? "Porovnej svou větu s odpovědí. Překlad si můžeš také poslechnout." : "Zkus říct celou větu. Zadání si můžeš přehrát.") : state.revealed ? "Poslechni si odpověď nebo pokračuj na další slovíčko." : "Nejdřív si odpověď zkus říct. Pak ji můžeš odhalit.";
  const studyContext=context();
  const group=M.groupInfo(item,studyContext,state.data?.catalog);
  const groupItems=state.sequence.filter(entry=>M.groupInfo(entry,studyContext,state.data?.catalog).id===group.id);
  const groupPosition=groupItems.findIndex(entry=>M.key(entry)===M.key(item))+1;
  ui.studyPosition.textContent=state.mode==="random" ? `Zamíchané procvičování · ${state.index+1} z ${state.sequence.length}` : `${group.label} · ${groupPosition} z ${groupItems.length}${groupItems.length===state.sequence.length ? "" : ` · celkem ${state.index+1}/${state.sequence.length}`}`;
  ui.previousButton.disabled=state.index===0;const next=state.sequence[state.index+1];
  ui.nextButton.hidden=!next;ui.newRoundButton.hidden=Boolean(next) || state.mode!=="random";
  const nextGroup=next ? M.groupInfo(next,context(),state.data?.catalog) : null;
  const boundary=next && state.mode==="ordered" && nextGroup.id!==group.id;
  ui.nextButton.textContent=boundary ? `Dál: ${nextGroup.label} →` : "Další →";
  ui.roundStatus.textContent=next ? boundary ? "Poslední slovíčko této skupiny. Dál začíná další skupina." : "" : "To je konec tohoto výběru. Můžeš se vrátit na přehled.";
  syncControls();primeCurrentAudio(item);
  ui.studyView.classList.toggle("loop-practice",studyLoop.active);
  loopUI.studyLoopTranslation.hidden=!studyLoop.active;
  ui.speakPromptButton.hidden=studyLoop.active;
  if(studyLoop.active)renderStudyLoopCard();
  document.title=state.view==="study" ? `${item.en} · Vocabulary EN` : document.title;
}

function syncStudyLoopControls(){
  loopUI.studyLoopMode.value=studyLoop.mode;
  loopUI.studyLoopGap.value=String(studyLoop.gap);
  loopUI.studyLoopToggle.textContent=studyLoop.running ? "Ⅱ Pozastavit" : studyLoop.active ? "▶ Pokračovat" : "▶ Spustit smyčku";
  loopUI.studyLoopToggle.disabled=!state.currentItem || !state.sequence.length;
  loopUI.studyLoopStop.hidden=!studyLoop.active;
}
function interruptStudyLoop(exit=true){
  studyLoop.generation++;
  studyLoop.running=false;
  if(studyLoop.cancelWait){studyLoop.cancelWait();studyLoop.cancelWait=null;}
  if(exit){
    studyLoop.active=false;
    loopUI.studyLoopTranslation.hidden=true;
    ui.studyView.classList.remove("loop-practice");
    loopUI.studyLoopStatus.textContent="Smyčka opakuje aktuální výběr anglicky, český překlad zůstává na obrazovce.";
  }
  syncStudyLoopControls();
}
function renderStudyLoopCard(){
  const item=state.currentItem, sentence=studyLoop.phase==="sentences";
  ui.studyView.classList.toggle("sentence-practice",sentence);
  ui.studyView.setAttribute("aria-label","Kontinuální procvičování");
  ui.promptLabel.textContent=sentence ? "VĚTA ANGLICKY" : "SLOVÍČKO ANGLICKY";
  ui.promptText.textContent=sentence ? item.sentenceEn || "Věta zatím není doplněná." : item.en;
  ui.promptText.lang="en";
  loopUI.studyLoopTranslation.textContent=sentence ? item.sentenceCz || "" : item.cz;
  ui.wordImage.alt=item.cz;
  ui.revealButton.hidden=true;ui.answerCard.classList.add("hidden");ui.speakAnswerButton.hidden=true;
  ui.messageStrip.textContent="";
  ui.roundStatus.textContent=`Opakování výběru · ${state.index+1}/${state.sequence.length}`;
}
function pauseStudyLoop(message="Pozastaveno. Pokračovat přehraje aktuální úsek od začátku."){
  if(!studyLoop.active)return;
  interruptStudyLoop(false);stopAudioPlayback({keepStudyLoop:true});
  loopUI.studyLoopStatus.textContent=message;
}
function exitStudyLoop(){
  stopAudioPlayback();
  if(state.view==="study")renderCurrentItem();
}
function loopDelay(generation){
  return new Promise(resolve=>{
    const timer=window.setTimeout(()=>{if(generation===studyLoop.generation)studyLoop.cancelWait=null;resolve(generation===studyLoop.generation);},studyLoop.gap);
    studyLoop.cancelWait=()=>{window.clearTimeout(timer);resolve(false);};
  });
}
function loopIsCurrent(generation){return studyLoop.running && state.view==="study" && generation===studyLoop.generation;}
async function runStudyLoop(generation){
  try{
    while(loopIsCurrent(generation)){
      const item=state.currentItem, sentence=studyLoop.phase==="sentences";
      const record=sentence ? M.sentenceAudioRecord(item,state.sentenceAudioManifest) : M.audioRecord(item,state.audioManifest);
      renderCurrentItem();
      if(!record?.en)throw new Error(sentence ? "Chybí ověřený zvuk této věty. Zkus Slovíčka nebo jinou kartu." : "Chybí ověřený zvuk tohoto slovíčka.");
      loopUI.studyLoopStatus.textContent=sentence ? "Posloucháš větu. Potom se zobrazí a přečte slovíčko." : "Posloucháš slovíčko. Po dočtení a pauze následuje další karta.";
      // Keep one user-unlocked element for Safari; load() resets each source,
      // including the single-card wrap, without reusing a pending seek.
      if(!loopAudio)loopAudio=new Audio();
      const completed=await playOneAudio(record.en,playbackToken,{player:loopAudio,timeoutMs:90000});
      if(!completed || !loopIsCurrent(generation))return;
      loopUI.studyLoopStatus.textContent="Pauza po dočtení…";
      if(!await loopDelay(generation) || !loopIsCurrent(generation))return;
      if(sentence){studyLoop.phase="words";}
      else{
        studyLoop.phase=studyLoop.mode==="sentence-word" ? "sentences" : "words";
        state.index=(state.index+1)%state.sequence.length;
        state.currentItem=state.sequence[state.index];state.lastUid=M.key(state.currentItem);state.revealed=false;
        writeHistory("study");persist();
      }
    }
  }catch(error){
    if(loopIsCurrent(generation))pauseStudyLoop(`${error.message} Smyčka je pozastavená; můžeš pokračovat nebo ji ukončit.`);
  }
}
function startStudyLoop(){
  if(state.view!=="study" || !state.currentItem || !state.sequence.length)return;
  const resume=studyLoop.active;
  stopAudioPlayback({keepStudyLoop:true});interruptStudyLoop(false);
  studyLoop.active=true;studyLoop.running=true;
  if(!resume)studyLoop.phase=studyLoop.mode==="sentence-word" ? "sentences" : "words";
  syncStudyLoopControls();
  void runStudyLoop(studyLoop.generation);
}
function setPracticeMode(mode){
  if(state.view!=="study" || !["words","sentences"].includes(mode))return;
  stopAudioPlayback();state.practice=mode;state.revealed=false;
  renderCurrentItem();writeHistory("study");persist();
}
function moveStudy(delta){
  const index=state.index+delta;if(state.view!=="study" || index<0 || index>=state.sequence.length)return;
  stopAudioPlayback();state.index=index;state.currentItem=state.sequence[index];state.lastUid=M.key(state.currentItem);state.revealed=false;
  renderCurrentItem();writeHistory("study");persist();window.scrollTo({top:0});
}
function newRandomRound(){
  if(!state.sequence.length)return;
  const last=state.lastUid;state.sequence=M.shuffle(state.sequence);
  if(state.sequence.length>1 && M.key(state.sequence[0])===last)[state.sequence[0],state.sequence[1]]=[state.sequence[1],state.sequence[0]];
  state.index=0;state.currentItem=state.sequence[0];state.lastUid=M.key(state.currentItem);state.revealed=false;stopAudioPlayback();renderCurrentItem();writeHistory("study");persist();window.scrollTo({top:0});
}
function focusLast(){
  const tile=state.lastUid ? document.getElementById(`tile-${state.lastUid}`) : null;
  if(!tile)return;
  window.requestAnimationFrame(()=>{
    const offset=Math.max(20,Math.min(Number(state.anchorOffset)||120,window.innerHeight*.5));
    window.scrollTo({top:Math.max(0,window.scrollY+tile.getBoundingClientRect().top-offset),behavior:"auto"});tile.focus({preventScroll:true});
  });
}
function showGallery({render=false}={}){
  stopAudioPlayback();if(state.currentItem)state.lastUid=M.key(state.currentItem);
  switchView("gallery");if(render)renderGallery();else markLast();writeHistory("gallery");persist();focusLast();
}
function returnToGallery(){
  if(state.view!=="study")return;
  stopAudioPlayback();persist();
  if(state.fromGallery && window.history.state?.vocabularyEN===1 && window.history.state?.kind==="study")window.history.back();
  else showGallery({render:true});
}
function applyRoute({initial=false}={}){
  stopAudioPlayback();
  const current=route(),saved=savedNavigation(),last=savedLast();
  if(initial)Object.assign(state,current.hasContext ? current.context : sanitizeContext(saved?.context || last?.context || {}));
  if(!learnerUI?.available){state.learner="all";state.onlyLearnerHard=false;}
  if(current.game&&quizUI){openQuiz({fromHistory:true});return;}
  if(current.card){
    const target=state.items.find(item=>M.key(item)===current.card);
    if(!target){state.lastUid="";state.currentItem=null;switchView("gallery");renderGallery();ui.galleryNotice.textContent=state.data.items.some(item=>M.key(item)===current.card && !M.isActive(item))?"Tato karta byla vyřazena z nabídky. Vyber si jiné slovíčko.":"Odkazované slovíčko už v tomto slovníku není. Vyber si jiné.";writeHistory("gallery");return;}
    if(!initial && current.hasContext)Object.assign(state,current.context);
    if(!learnerUI?.available){state.learner="all";state.onlyLearnerHard=false;}
    if(!personalItems().some(item=>M.key(item)===current.card)){
      state.currentItem=null;switchView("gallery");renderGallery();ui.galleryNotice.textContent=`Slovíčko není v aktuálním výběru uživatele ${state.learner}. Změň osobní filtr nebo slovní zásobu.`;writeHistory("gallery");return;
    }
    state.sequence=saved?.revision===state.data?.revision && saved?.currentUid===current.card && Array.isArray(saved.sequence) ? M.restoreSequence(saved.sequence.slice(0,5000),orderedSelection()) : orderedSelection();
    if(!state.sequence.some(item=>M.key(item)===current.card)){
      Object.assign(state,{filter:"all",teachingType:"all",query:"",topics:[],sources:[],parts:[],levels:[],recentCount:0});state.sequence=orderedSelection();renderGallery();
    }
    state.index=state.sequence.findIndex(item=>M.key(item)===current.card);state.currentItem=target;state.lastUid=current.card;
    state.mode=saved?.currentUid===current.card && saved.mode==="random" ? "random" : "ordered";
    state.fromGallery=window.history.state?.vocabularyEN===1 && window.history.state?.fromGallery===true;
    state.visitId=window.history.state?.visitId || saved?.visitId || freshVisit();state.anchorOffset=Number(saved?.anchorOffset)||120;
    state.revealed=false;switchView("study");renderCurrentItem();writeHistory("study");persist();
    if(initial){window.scrollTo({top:0});ui.studyPosition.focus({preventScroll:true});}
  }else{
    if(initial){
      state.lastUid=current.last || saved?.currentUid || last?.uid || "";
      state.anchorOffset=Number(saved?.anchorOffset)||120;
      state.sequence=saved?.revision===state.data?.revision && Array.isArray(saved.sequence) ? M.restoreSequence(saved.sequence.slice(0,5000),state.items) : [];
      state.mode=saved?.mode==="random" ? "random" : "ordered";
      state.visitId=saved?.visitId || "";
    }
    if(!state.items.some(item=>M.key(item)===state.lastUid))state.lastUid="";
    showGallery({render:true});
  }
}

const audioCache=new Map();
let currentAudio=null,currentPlaybackCancel=null,playbackToken=0;
function audioRecord(item){return state.practice==="sentences" ? M.sentenceAudioRecord(item,state.sentenceAudioManifest) : M.audioRecord(item,state.audioManifest);}
function audioUrl(relativePath) {
  return new URL(`../${relativePath}`, window.location.href).toString();
}

function cachedAudio(relativePath) {
  if (!relativePath) {
    return null;
  }
  const url = audioUrl(relativePath);
  if (!audioCache.has(url)) {
    if (audioCache.size >= 16) {
      const oldest = [...audioCache.keys()].find(key => audioCache.get(key) !== currentAudio);
      if (oldest) { audioCache.get(oldest).pause(); audioCache.delete(oldest); }
    }
    const audio = new Audio(url);
    audio.preload = "auto";
    audioCache.set(url, audio);
  }
  return audioCache.get(url);
}

function primeCurrentAudio(item) {
  const record = audioRecord(item);
  if (!record) {
    return;
  }
  [record.en, record.cz].forEach((relativePath) => cachedAudio(relativePath));
}

function stopAudioPlayback({keepStudyLoop=false}={}) {
  if(!keepStudyLoop)interruptStudyLoop();
  clearGalleryTranslation();
  playbackToken += 1;
  if (currentPlaybackCancel) {
    const cancel = currentPlaybackCancel;
    currentPlaybackCancel = null;
    cancel();
  }
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
}

function playOneAudio(relativePath, token, {player=null,timeoutMs=0}={}) {
  return new Promise((resolve, reject) => {
    const audio = player || cachedAudio(relativePath);
    if (!audio || token !== playbackToken) {
      resolve(false);
      return;
    }

    currentAudio = audio;
    if(player){audio.src=audioUrl(relativePath);audio.load();}
    else audio.currentTime = 0;
    let settled = false;
    let watchdog=null;
    const finish = (completed, error = null) => {
      if (settled) {
        return;
      }
      settled = true;
      if(watchdog!==null)window.clearTimeout(watchdog);
      if(error)audio.pause();
      audio.removeEventListener("ended", onEnded);
      audio.removeEventListener("error", onError);
      if (currentAudio === audio) {
        currentAudio = null;
        currentPlaybackCancel = null;
      }
      if (error) {
        reject(error);
      } else {
        resolve(completed);
      }
    };
    const onEnded = () => {if(!player || audio.ended===true)finish(true);};
    const onError = () => finish(false, new Error("Zvuk se nepodařilo přehrát."));
    currentPlaybackCancel = () => {
      audio.pause();
      audio.currentTime = 0;
      finish(false);
    };
    audio.addEventListener("ended", onEnded);
    audio.addEventListener("error", onError, { once: true });
    if(timeoutMs)watchdog=window.setTimeout(()=>{audio.pause();finish(false,new Error("Přehrávání zvuku se nedokončilo včas."));},timeoutMs);
    audio.play().catch(() => onError());
  });
}

async function playAudioSequence(relativePaths) {
  const paths = relativePaths.filter(Boolean);
  if (!paths.length) {
    ui.messageStrip.textContent = state.practice==="sentences" ? "Zvuk pro tuto větu zatím není připravený. Můžeš se učit podle textu." : "Zvuk pro toto slovicko zatim neni pripraveny.";
    return;
  }
  stopAudioPlayback();
  const token = playbackToken;
  try {
    for (const relativePath of paths) {
      if (token !== playbackToken) {
        return;
      }
      const completed = await playOneAudio(relativePath, token);
      if (!completed) {
        return;
      }
    }
  } catch (error) {
    ui.messageStrip.textContent = error.message;
  }
}

function speakPrompt() {
  if(studyLoop.active)return;
  if (!state.currentItem) {
    return;
  }
  const record = audioRecord(state.currentItem);
  const relativePath = state.direction === "czToEn" ? record?.cz : record?.en;
  playAudioSequence([relativePath]);
}

function speakAnswer() {
  if(studyLoop.active)return;
  if (!state.currentItem || (state.practice === "sentences" && !state.revealed)) {
    return;
  }
  const record = audioRecord(state.currentItem);
  playAudioSequence(state.practice==="sentences" ? [state.direction==="czToEn" ? record?.en : record?.cz] : [record?.en, record?.cz]);
}

function bindEvents(){
  loopUI.studyLoopToggle.addEventListener("click",()=>{if(studyLoop.running)pauseStudyLoop();else startStudyLoop();});
  loopUI.studyLoopStop.addEventListener("click",exitStudyLoop);
  loopUI.studyLoopMode.addEventListener("change",()=>{
    const mode=loopUI.studyLoopMode.value;if(!["words","sentence-word"].includes(mode))return;
    if(studyLoop.active)pauseStudyLoop("Režim změněn. Spusť Pokračovat.");
    studyLoop.mode=mode;studyLoop.phase=mode==="sentence-word" ? "sentences" : "words";
    if(studyLoop.active)renderCurrentItem();syncStudyLoopControls();
  });
  loopUI.studyLoopGap.addEventListener("change",()=>{
    const gap=Number(loopUI.studyLoopGap.value);if(![1000,2000,4000,6000].includes(gap))return;
    if(studyLoop.active)pauseStudyLoop("Prodleva změněna. Spusť Pokračovat.");
    studyLoop.gap=gap;syncStudyLoopControls();
  });
  document.getElementById("settingsTab").addEventListener("click",()=>learnerUI?.open(state.learner));
  document.getElementById("galleryTab").addEventListener("click",()=>{if(state.view==="settings")learnerUI?.close();else if(state.view==="study")returnToGallery();else if(state.view==="quiz")quizUI?.close();});
  document.getElementById("quizTab").addEventListener("click",()=>{if(state.view!=="quiz")openQuiz();});
  const recentInput=document.getElementById("recentCount"),recentOnly=document.getElementById("recentOnly");
  function changeRecent(){
    const count=recentOnly.checked?M.recentCount(recentInput.value):0;
    if(recentOnly.checked&&!count){ui.galleryNotice.textContent="Počet musí být celé číslo od 1 do 5000.";return;}
    state.recentCount=count;selectionChanged();
  }
  recentInput.addEventListener("change",changeRecent);recentOnly.addEventListener("change",changeRecent);
  learnerSelect.addEventListener("change",()=>{state.learner=learnerSelect.value;state.onlyLearnerHard=false;selectionChanged();});
  learnerHardFilter.addEventListener("click",()=>{if(state.learner!=="all"){state.onlyLearnerHard=!state.onlyLearnerHard;selectionChanged();}});
  editLearnerHard.addEventListener("click",()=>{if(state.learner!=="all")learnerUI?.open(state.learner,true);});
  document.querySelectorAll("[data-gallery-mode]").forEach(button=>button.addEventListener("click",()=>setGalleryMode(button.dataset.galleryMode)));
  document.querySelectorAll("[data-label]").forEach(button=>button.addEventListener("click",()=>{state.labelLanguage=button.dataset.label;renderGallery();writeHistory("gallery");persist();}));
  document.querySelectorAll("[data-direction]").forEach(button=>button.addEventListener("click",()=>{state.direction=button.dataset.direction;stopAudioPlayback();renderCurrentItem();if(state.currentItem && state.view==="study")writeHistory("study");persist();}));
  document.querySelectorAll("[data-practice]").forEach(button=>button.addEventListener("click",()=>setPracticeMode(button.dataset.practice)));
  ui.searchInput.addEventListener("input",()=>{state.query=ui.searchInput.value.slice(0,200);selectionChanged();});
  for(const [id,key] of [["filterSelect","filter"],["teachingTypeSelect","teachingType"],["groupSelect","groupBy"],["sortSelect","sort"]])ui[id].addEventListener("change",()=>{state[key]=ui[id].value;selectionChanged();});
  ui.sizeButton.addEventListener("click",()=>{state.large=!state.large;syncControls();writeHistory("gallery");persist();});
  ui.clearTopicsButton.addEventListener("click",()=>{state.topics=[];selectionChanged();});
  ui.resetButton.addEventListener("click",resetFilters);ui.emptyResetButton.addEventListener("click",resetFilters);
  ui.continueButton.addEventListener("click",()=>openStudy(state.lastUid));
  ui.shuffleButton.addEventListener("click",()=>openStudy("","random"));
  ui.backButton.addEventListener("click",returnToGallery);ui.backBottomButton.addEventListener("click",returnToGallery);ui.previousButton.addEventListener("click",()=>moveStudy(-1));ui.nextButton.addEventListener("click",()=>moveStudy(1));ui.newRoundButton.addEventListener("click",newRandomRound);
  ui.revealButton.addEventListener("click",()=>{if(!state.currentItem || !M.studyPrompt(state.currentItem,context()).available)return;state.revealed=true;renderCurrentItem();});
  ui.speakPromptButton.addEventListener("click",speakPrompt);ui.wordImage.addEventListener("click",speakPrompt);ui.speakAnswerButton.addEventListener("click",speakAnswer);
  ui.wordImage.addEventListener("error",()=>{ui.wordImage.hidden=true;ui.pictureFallback.hidden=false;});
  document.addEventListener("keydown",event=>{if(event.key==="Escape"){if(state.view==="study"){event.preventDefault();returnToGallery();}else if(state.view==="quiz"){event.preventDefault();quizUI?.close();}}});
  window.addEventListener("popstate",()=>{stopAudioPlayback();applyRoute();});
  window.addEventListener("hashchange",()=>{const current=route();if(current.game||state.view==="quiz"||current.card && (state.view!=="study" || M.key(state.currentItem)!==current.card)){stopAudioPlayback();applyRoute();}});
  window.addEventListener("pagehide",()=>{persist();quizUI?.leave();stopAudioPlayback();});
  window.addEventListener("pageshow",event=>{if(event.persisted){stopAudioPlayback();if(state.view==="gallery")focusLast();else if(state.view==="study")renderCurrentItem();}});
}
async function readJson(url){const response=await fetch(url,{cache:"no-store"});if(!response.ok)throw new Error(`HTTP ${response.status}`);return response.json();}
async function init(){
  bindEvents();
  // A slow or missing pronunciation file must never hold the picture atlas closed.
  void readJson(AUDIO_DATA_URL).then(manifest=>{
    state.audioManifest=manifest;if(state.currentItem)primeCurrentAudio(state.currentItem);quizUI?.refresh();
  }).catch(()=>{state.audioManifest=false;ui.galleryNotice.textContent="Zvuk se nepodařilo načíst. Slovíčka můžeš dál procházet.";quizUI?.refresh();});
  void readJson(QUIZ_DATA_URL).then(data=>{if(data?.schemaVersion!==1||!data.entries||typeof data.entries!=="object"||Array.isArray(data.entries))throw new Error("Neplatný výběr obrázků.");quizCatalog=data;quizUI?.refresh();}).catch(()=>{quizCatalog=false;quizUI?.refresh();});
  void readJson(SENTENCE_AUDIO_URL).then(manifest=>{
    state.sentenceAudioManifest=manifest;if(state.currentItem && state.practice==="sentences")primeCurrentAudio(state.currentItem);
  }).catch(()=>{}); // Sentence text and word audio work even if this optional file is unavailable.
  let data;
  try {data=await readJson(DATA_URL);} catch (_) {data=null;}
  if(!Array.isArray(data?.items) || !Array.isArray(data?.catalog?.groups) || !Array.isArray(data?.catalog?.parents)){
    ui.galleryGroups.replaceChildren();ui.galleryGroups.setAttribute("aria-busy","false");ui.totalCount.textContent="—";ui.shuffleButton.disabled=true;
    ui.galleryNotice.textContent="Slovník se nepodařilo načíst. Zkus obnovit stránku.";return;
  }
  state.data=data;state.items=data.items.filter(M.isActive);
  if(globalThis.VocabularyLearnerUI&&globalThis.VocabularyLearners)learnerUI=globalThis.VocabularyLearnerUI.create({doc:document,win:window,data,model:M,
    onOpen:()=>{stopAudioPlayback();switchView("settings");window.scrollTo({top:0});},
    onClose:()=>showGallery({render:true}),
    onChange:edited=>{if(edited){state.learner=edited;}if(state.view==="gallery"){selectionChanged();}else if(state.view==="study"){applyRoute();}quizUI?.refresh();}
  });
  else document.getElementById("learnerNotice").textContent="Osobní výběry se nepodařilo načíst. Zkus obnovit stránku; společný slovník zůstává dostupný.";
  if(globalThis.VocabularyQuiz)quizUI=globalThis.VocabularyQuiz.create({doc:document,win:window,getData:()=>state.data,getAudio:()=>state.audioManifest,getCatalog:()=>quizCatalog,
    getPersonal:(id,hard)=>learnerUI?.filter(state.items,id,hard)||[],isAvailable:()=>Boolean(learnerUI?.available),
    onOpen:()=>{stopAudioPlayback();switchView("quiz");window.scrollTo({top:0});},onClose:returnFromQuiz,
    play:item=>{stopAudioPlayback();return playOneAudio(M.audioRecord(item,state.audioManifest)?.en,playbackToken);},stop:stopAudioPlayback});
  document.getElementById("quizTab").disabled=!quizUI;
  buildFilterControls();renderGallery();applyRoute({initial:true});
}
void init();
