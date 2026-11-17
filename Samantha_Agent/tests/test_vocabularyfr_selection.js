const test=require('node:test');
const {assert,fixture,vocabulary,audio,sentenceAudio,quizCatalog,pictures,model,learners,practice,app,flush,until,change,active,ended,loop,phase,clone,storage}=require('./fixtures/vocabulary_fr_dom.js');
const cat=vocabulary.items[0];

test('FR selection reads counts and stable latest IDs from data, with eighteen independent topics',()=>{
 const before=JSON.stringify(vocabulary);assert.equal(vocabulary.groups.length,18);
 assert.equal(model.select(vocabulary.items,{query:'velo'})[0].fr,'vélo');
 assert.deepEqual(model.select(vocabulary.items,{recentCount:2}).map(i=>i.id),[17,18]);
 assert.deepEqual(model.select(vocabulary.items,{topics:['topic-01']}).map(i=>i.uid),[cat.uid]);
 assert.equal(JSON.stringify(vocabulary),before);
});
test('FR/CZ prompts and sentence language preserve accents and complete text',()=>{
 assert.equal(model.studyPrompt(cat,{direction:'frToCz'}).language,'fr');
 assert.equal(model.studyPrompt(cat,{direction:'czToFr'}).text,'kočka');
 assert.equal(model.studyPrompt(cat,{direction:'frToCz',practice:'sentences'}).text,cat.sentenceFr);
 assert.equal(model.studyPrompt({...cat,sentenceFr:''},{practice:'sentences'}).available,false);
});
test('each word and sentence audio channel remains independently available under partial manifests',()=>{
 for(const [original,read] of [[audio,model.audioRecord],[sentenceAudio,model.sentenceAudioRecord]])for(const missing of ['fr','cz']){
  const manifest=clone(original);manifest.status='partial';manifest.items[cat.uid][missing]=null;
  const result=read(cat,manifest);assert.equal(result[missing],null);assert.ok(result[missing==='fr'?'cz':'fr']);
 }
 const none=clone(audio);none.status='not-generated';none.items[cat.uid].fr=none.items[cat.uid].cz=null;
 assert.equal(model.audioRecord(cat,none).fr,null);
});
test('audio rejects source drift and foreign manifests and quarantines unsafe channels independently',()=>{
 for(const field of ['sourceFr','sourceCz','uid']){const m=clone(audio);m.items[cat.uid][field]+='changed';assert.equal(model.audioRecord(cat,m),null);}
 for(const field of ['sourceSentenceFr','sourceSentenceCz']){const m=clone(sentenceAudio);m.items[cat.uid][field]+='changed';assert.equal(model.sentenceAudioRecord(cat,m),null);}
 for(const values of [{language:'it'},{kind:'sentences'},{schemaVersion:2},{status:'promised'}])assert.equal(model.audioRecord(cat,{...audio,...values}),null);
 for(const bad of ['https://example.test/a.mp3','../a.mp3','assets/vocabulary-it-audio/a.mp3','assets/vocabulary-fr-audio/../a.mp3','assets/vocabulary-fr-audio//a.mp3','assets/vocabulary-fr-audio/a.mp3?token=x']){
  const m=clone(audio);m.items[cat.uid].fr=bad;const result=model.audioRecord(cat,m);assert.equal(result.fr,null,bad);assert.ok(result.cz);
 }
});
test('French writing accepts NFC, case and phone apostrophes while preserving meaning-changing accents and ligatures',()=>{
 for(const [typed,expected] of [[' VE\u0301LO ','vélo'],['L’AMI',"l'ami"],['CŒUR','cœur']])assert.equal(practice.writingMatches(typed,expected),true);
 for(const [typed,expected] of [['ou','où'],['sur','sûr'],['a','à'],['oeuf','œuf'],['lami',"l'ami"]])assert.equal(practice.writingMatches(typed,expected),false);
 assert.equal(practice.record(cat,quizCatalog).displayMode,'whole-word');
});
test('four-picture questions avoid same French text, image, related meanings and editorial conflicts',()=>{
 const question=practice.question(cat,vocabulary.items,quizCatalog,()=>.5);assert.equal(question.choices.length,4);
 assert.equal(practice.compatible(cat,{...cat,uid:'vfr-9000'},quizCatalog),false);
 const altered=clone(quizCatalog);altered.entries[vocabulary.items[1].uid].conflicts=['ambiguous'];altered.entries[cat.uid].conflicts=['ambiguous'];
 assert.equal(practice.compatible(cat,vocabulary.items[1],altered),false);
});
test('FR profiles and backups refuse IT/EN identifiers, retain retired IDs and do not read old L/HT',()=>{
 const data=learners.empty();data.profiles.A={selected:['vfr-9999',cat.uid],hard:[cat.uid],pin:null};
 assert.equal(learners.KEY,'vocabulary-fr.learners.v1');assert.deepEqual(learners.parseBackup(JSON.stringify(learners.backup(data))).profiles.A.selected,['vfr-9999',cat.uid]);
 assert.throws(()=>learners.parseBackup(JSON.stringify({...learners.backup(data),kind:'vocabulary-it.learner-backup'})));
 data.profiles.A.selected=['vit-0001'];assert.throws(()=>learners.validate(data));
});
test('gallery opens with missing or slow audio and absent optional pictures, without auto playing',async()=>{
 for(const options of [{manifest:null,sentenceManifest:null,pictureManifest:null},{slowAudio:true}]){
  const view=await app(options);assert.equal(view.state.items.length,vocabulary.items.length);assert.equal(view.players.some(p=>p.playCount),false);
  view.openStudy(cat.uid);assert.equal(view.state.currentItem.fr,'chat');assert.match(view.element('audioAvailability').textContent,/Francouzský zvuk/);
 }
});
test('French and Czech explicit playback buttons are independent and never label Czech as French',async()=>{
 const m=clone(audio);m.status='partial';m.items[cat.uid].fr=null;
 const view=await app({manifest:m});view.openStudy(cat.uid);view.element('revealButton').click();
 assert.equal(view.element('speakAnswerButton').disabled,true);assert.equal(view.element('speakCzechButton').disabled,false);
 view.element('speakCzechButton').click();assert.match(active(view).url,/-cz\.mp3$/);ended(view);await flush();
 view.speakAnswer();assert.match(view.element('messageStrip').textContent,/Francouzský zvuk/);assert.equal(active(view),undefined);
 const frenchOnly=clone(audio);frenchOnly.status='partial';frenchOnly.items[cat.uid].cz=null;
 const second=await app({manifest:frenchOnly});second.openStudy(cat.uid);second.element('revealButton').click();second.speakAnswer();assert.match(active(second).url,/-fr\.mp3$/);second.stopAudioPlayback();
});
test('prompt playback follows direction and sentence channels independently',async()=>{
 const m=clone(sentenceAudio);m.status='partial';m.items[cat.uid].fr=null;
 const view=await app({sentenceManifest:m});view.openStudy(cat.uid);view.setPracticeMode('sentences');
 view.speakPrompt();assert.match(active(view).url,/sentences.*-cz\.mp3$/);view.stopAudioPlayback();
 view.directions.find(b=>b.dataset.direction==='frToCz').click();view.speakPrompt();assert.equal(active(view),undefined);assert.match(view.element('messageStrip').textContent,/Zvuk/);
});
test('loop pauses on the same target when FR is missing, even with usable Czech audio',async()=>{
 const m=clone(sentenceAudio);m.status='partial';m.items[cat.uid].fr=null;
 const view=await app({sentenceManifest:m});view.openStudy(cat.uid);loop(view);await flush();
 assert.equal(view.state.currentItem.uid,cat.uid);assert.equal(active(view),undefined);assert.match(view.element('studyLoopStatus').textContent,/pozastavená/);
 assert.match(view.element('studyLoopStatus').textContent,/Francouzský zvuk/);assert.equal(view.element('studyLoopToggle').textContent,'▶ Pokračovat');
 assert.equal(view.element('sentencePictures').hidden,false);
});
test('sentence loop shows reviewed images outside the target filter, then restores the large word and one player',async()=>{
 const view=await app();view.state.topics=['topic-01'];view.selectionChanged();view.openStudy(cat.uid);loop(view);
 assert.deepEqual(view.element('sentencePictures').querySelectorAll('figcaption').map(n=>n.textContent),['chat','lune']);
 const player=active(view);await phase(view);assert.equal(active(view),player);assert.equal(view.element('sentencePictures').hidden,true);assert.equal(view.element('promptText').textContent,'chat');
 await phase(view);assert.equal(view.state.currentItem.uid,cat.uid);assert.equal(active(view),player);view.element('studyLoopStop').click();
});
test('loop uses ended plus selected gap, pause/resume, and ignores old events after rapid navigation',async()=>{
 const view=await app();view.openStudy(cat.uid);loop(view,'words');const first=active(view),stale=first.handlers.ended;
 view.advance(50000);await flush();assert.equal(view.state.currentItem.uid,cat.uid);
 view.element('studyLoopToggle').click();assert.equal(active(view),undefined);view.element('studyLoopToggle').click();assert.equal(active(view),first);
 ended(view);await flush();view.advance(1999);await flush();assert.equal(view.state.currentItem.uid,cat.uid);view.advance(1);await flush();assert.notEqual(view.state.currentItem.uid,cat.uid);
 const current=view.state.currentItem.uid;stale();await flush();assert.equal(view.state.currentItem.uid,current);view.element('studyLoopStop').click();
});
test('loop errors and rejected playback pause instead of silently advancing',async()=>{
 for(const rejected of [true,false]){
  const view=await app({audioReject:rejected});view.openStudy(cat.uid);loop(view,'words');if(!rejected)active(view).handlers.error();await flush();
  assert.match(view.element('studyLoopStatus').textContent,/pozastavená/);assert.equal(view.state.currentItem.uid,cat.uid);assert.equal(active(view),undefined);
 }
});
test('history, reload and bfcache restore position without restarting sound; gallery return focuses the last card',async()=>{
 const view=await app();view.openStudy(cat.uid);loop(view);view.emit('pagehide');await flush();assert.equal(active(view),undefined);
 view.emit('pageshow',{persisted:true});await flush();assert.equal(active(view),undefined);
 const restored=await app({session:view.session,local:view.local,url:view.win.location.href});assert.equal(active(restored),undefined);
 restored.returnToGallery();assert.equal(restored.state.view,'gallery');assert.equal(restored.doc.activeElement.id,`tile-${cat.uid}`);
});
test('changed or late picture maps cannot leak into manual guessing or change an active sentence',async()=>{
 const view=await app();view.openStudy(cat.uid);view.setPracticeMode('sentences');assert.equal(view.element('sentencePictures').hidden,true);
 const changed=clone(pictures);changed.entries[cat.uid].sourceSentenceFr+='changed';assert.deepEqual(model.sentencePictures(cat,changed,vocabulary.items),[]);
 let resolve;const deferred=new Promise(r=>resolve=r);const late=await app({pictureManifest:pictures,pictureDeferred:deferred});late.openStudy(cat.uid);loop(late);
 assert.equal(late.element('sentencePictures').hidden,true);resolve(pictures);await flush();assert.equal(late.element('sentencePictures').hidden,true);await phase(late);await phase(late);assert.equal(late.element('sentencePictures').hidden,false);late.stopAudioPlayback();
});
test('broken contextual images do not interrupt the sentence and all failures restore the original card',async()=>{
 const view=await app();view.openStudy(cat.uid);loop(view);const player=active(view);
 for(const figure of [...view.element('sentencePictures').children])figure.querySelector('img').emit('error');
 assert.equal(view.element('sentencePictures').hidden,true);assert.equal(active(view),player);view.stopAudioPlayback();
});
test('game excludes missing FR targets and reveals the missing French audio count',async()=>{
 const m=clone(audio);m.status='partial';m.items[cat.uid].fr=null;
 assert.equal(practice.eligible(vocabulary.items,m,quizCatalog).some(i=>i.uid===cat.uid),false);
 const view=await app({manifest:m});view.element('quizTab').click();assert.match(view.element('quizPoolNotice').textContent,/francouzský zvuk.*1/i);
});

async function readyGame(view){
 for(const image of view.element('quizChoices').querySelectorAll('img'))image.emit('load');
 for(let n=0;n<35;n++){view.advance(100);await flush();}
 ended(view);await flush();
}
function correct(view){const word=view.element('practiceWord').textContent;return view.element('quizChoices').children.find(b=>vocabulary.items.find(i=>i.uid===b.dataset.uid)?.fr===word);}
async function game({writing=false,...options}={}){
 const view=await app({items:vocabulary.items.slice(0,4),...options});view.element('quizTab').click();if(writing)view.element('practiceWritingToggle').click();view.element('quizStart').click();await readyGame(view);return view;
}
async function feedbackEnd(view){ended(view);await flush();view.advance(250);await flush();}
test('adult practice waits for complete FR audio, uses a fresh feedback player and blocks rapid Next or replay',async()=>{
 const view=await game({delayedSeek:true});const first=view.players.find(p=>p.playCount);correct(view).click();await flush();
 const second=active(view);assert.notEqual(first,second);assert.equal(second.starts.at(-1),0);const position=view.element('quizPosition').textContent;
 view.element('quizNext').click();view.element('quizReplay').click();view.advance(5000);await flush();assert.equal(view.element('quizPosition').textContent,position);assert.equal(view.element('quizNext').disabled,true);
 await feedbackEnd(view);assert.equal(view.element('quizNext').disabled,false);
});
test('writing starts after feedback, 500ms hint preserves the draft, and final reading owns Next',async()=>{
 const view=await game({writing:true});correct(view).click();assert.equal(view.element('practiceWritingPanel').hidden,true);await feedbackEnd(view);
 assert.equal(view.element('practiceWritingPanel').hidden,false);const input=view.element('practiceWritingInput'),word=view.element('practiceHeroWord').textContent;
 input.value=word.slice(0,1);input.emit('input');view.element('practiceWritingHint').click();assert.equal(view.element('practiceHeroWord').hidden,false);view.advance(499);assert.equal(view.element('practiceHeroWord').hidden,false);view.advance(1);assert.equal(view.element('practiceHeroWord').hidden,true);assert.equal(input.value,word.slice(0,1));
 assert.equal(view.element('practiceWritingHintStatus').children[1].lang,'fr');input.value=word;input.emit('input');assert.equal(input.readOnly,true);
 view.advance(600);await flush();assert.equal(view.element('practiceWritingPanel').hidden,true);assert.equal(view.element('quizNext').disabled,true);assert.ok(active(view));await feedbackEnd(view);assert.equal(view.element('quizNext').disabled,false);
});
test('IME composition and leaving during writing cannot accept an unfinished accent or revive old hint callbacks',async()=>{
 const view=await game({writing:true});correct(view).click();await feedbackEnd(view);
 const input=view.element('practiceWritingInput'),word=view.element('practiceHeroWord').textContent;input.emit('compositionstart');input.value=word;input.emit('input',{isComposing:true});assert.equal(input.readOnly,false);
 input.emit('compositionend');assert.equal(input.readOnly,true);view.emit('pagehide');view.advance(2000);await flush();assert.equal(active(view),undefined);
});
test('actual settings save, PIN and backup import affect only the unlocked FR learner, leaving IT/EN storage intact',async()=>{
 const original=learners.empty();original.profiles.A.pin=await learners.makePin('4826',require('node:crypto').webcrypto);original.profiles.A.selected=[cat.uid];original.profiles.B.selected=['vfr-0002'];
 const local=storage(new Map([[learners.KEY,JSON.stringify(original)],['vocabulary-it.learners.v1','old-it'],['vocabulary-en.learners.v1','old-en']]));
 const view=await app({local});view.element('settingsTab').click();view.element('legacySettingsButton').click();view.element('pinInput').value='4826';view.element('unlockButton').click();await until(()=>!view.element('learnerEditor').hidden);
 const replacement=learners.backup(learners.empty());replacement.profiles.A={selected:['vfr-0003','vfr-9999'],hard:['vfr-0003']};replacement.profiles.B.selected=['vfr-0004'];const raw=JSON.stringify(replacement);
 view.element('learnerFile').files=[{size:raw.length,text:async()=>raw}];view.element('learnerFile').emit('change');await until(()=>view.element('settingsNotice').textContent.includes('Načtený návrh'));view.element('saveLearner').click();
 const after=learners.store(()=>local).read().value;assert.deepEqual(after.profiles.A.selected,['vfr-0003','vfr-9999']);assert.deepEqual(after.profiles.A.pin,original.profiles.A.pin);assert.deepEqual(after.profiles.B,original.profiles.B);
 assert.equal(local.getItem('vocabulary-it.learners.v1'),'old-it');assert.equal(local.getItem('vocabulary-en.learners.v1'),'old-en');
});
test('learner storage refuses concurrent writes, invalid hard subsets and corrupted backups without replacing state',()=>{
 const local=storage(),store=learners.store(()=>local),base=store.read();local.setItem(learners.KEY,JSON.stringify(learners.empty()));assert.throws(()=>store.write(base.value,base.raw));
 const invalid=learners.empty();invalid.profiles.A.hard=[cat.uid];assert.throws(()=>learners.validate(invalid));assert.throws(()=>learners.parseBackup('{broken'));
});
test('invalid source catalog and foreign deep links fail visibly, while blocked storage keeps common gallery usable',async()=>{
 const invalid=await app({dataOverride:{language:'it'}});assert.equal(invalid.state.data,null);assert.match(invalid.element('galleryNotice').textContent,/Slovník/);
 const blocked=await app({blocked:true});assert.equal(blocked.state.items.length,vocabulary.items.length);blocked.openStudy(cat.uid);assert.equal(blocked.state.currentItem.uid,cat.uid);
 const foreign=await app({url:'https://example.test/vocabulary-fr/#card=vit-0001'});assert.equal(foreign.state.view,'gallery');assert.match(foreign.element('galleryNotice').textContent,/slovníku|slovíčko/);
});

// Personal-hard scenarios use only synthetic learner selections.
{
const test=require('node:test');
const {assert,app,storage,fixture,vocabulary,learners,flush,change,active,loop,phase}=require('./fixtures/vocabulary_fr_dom.js');
const P=require('../../docs/vocabulary-fr/personal.js');
const backup=hard=>({...P.empty(),hard});
const ids=vocabulary.items.map(i=>i.uid);
async function importFile(v,hard,{raw=JSON.stringify(backup(hard)),text=null}={}){
 v.element('personalFile').files=[{size:Buffer.byteLength(raw),text:text||(async()=>raw)}];v.element('personalFile').emit('change');await flush();
}
function editor(v){v.element('settingsTab').click();assert.equal(v.state.view,'personal');}
function mark(v,uid,checked){const c=v.element('personalGroups').querySelectorAll('.personal-word-check').find(c=>c.dataset.uid===uid);assert.ok(c);c.checked=checked;c.emit('change');}
const hardCount=v=>v.buildSelection().length;

test('strict FR personal contract rejects foreign formats, duplicates, invalid IDs, extra state and oversized input',()=>{
 assert.deepEqual(P.parse(JSON.stringify(backup(ids.slice(0,3)))).hard,ids.slice(0,3));
 for(const value of [{...backup([]),schema:2},{...backup([]),language:'it'},{...backup([]),kind:'vocabulary-fr.learner-backup'},backup(['vit-0001']),backup([ids[0],ids[0]]),backup(['vfr-0001<script>']),{...backup([]),pin:'1234'}])assert.throws(()=>P.parse(JSON.stringify(value)));
 assert.throws(()=>P.parse('x'.repeat(1000001)));assert.throws(()=>P.parse('{broken'));
});
test('All uses the current inventory including future cards, never a fixed selected list',()=>{
 const value=backup([ids[0]]),next=[...vocabulary.items,{uid:'vfr-8000',active:true}];
 assert.equal(P.selection(next,value,false).length,19);assert.equal(P.selection(next,value,true).length,1);
 assert.deepEqual(Object.keys(value).sort(),['hard','kind','language','schema']);
});
test('editor includes every topic, persists marking and unmarking after explicit save and reload, without touching A–D or other apps',async()=>{
 const legacyValue=learners.empty();legacyValue.profiles.A={selected:[ids[0]],hard:[ids[0]],pin:{salt:'00'.repeat(16),hash:'01'.repeat(32),iterations:100000}};const legacy=JSON.stringify(legacyValue),local=storage(new Map([[learners.KEY,legacy],['vocabulary-it.learners.v1','old-it'],['vocabulary-en.learners.v1','old-en']]));
 const v=await app({local});assert.equal(hardCount(v),18);assert.equal(local.getItem(P.KEY),null);editor(v);
 assert.equal(v.element('personalGroups').querySelectorAll('h2').length,18);
 mark(v,ids[0],true);assert.equal(local.getItem(P.KEY),null);v.element('personalSave').click();assert.match(v.element('personalNotice').textContent,/Uloženo/);
 v.element('personalBack').click();v.element('personalHard').click();assert.equal(hardCount(v),1);
 const reload=await app({local});reload.element('personalHard').click();assert.equal(hardCount(reload),1);editor(reload);mark(reload,ids[0],false);reload.element('personalSave').click();
 const again=await app({local});again.element('personalHard').click();assert.equal(hardCount(again),0);assert.equal(local.getItem(learners.KEY),legacy);assert.equal(local.getItem('vocabulary-it.learners.v1'),'old-it');assert.equal(local.getItem('vocabulary-en.learners.v1'),'old-en');
});
test('loading an import changes nothing, and adding versus replacing have separate explicit previews',async()=>{
 const local=storage(new Map([[P.KEY,JSON.stringify(backup([ids[0]]))]]));const v=await app({local});editor(v);const before=local.getItem(P.KEY);
 await importFile(v,[ids[1],ids[2]]);assert.equal(local.getItem(P.KEY),before);assert.equal(v.element('personalSave').disabled,true);assert.match(v.element('personalPreview').textContent,/2 označení/);
 change(v,'personalImportMode','add');assert.match(v.element('personalPreview').textContent,/3 označení/);assert.equal(local.getItem(P.KEY),before);
 change(v,'personalImportMode','replace');assert.match(v.element('personalPreview').textContent,/2 označení/);assert.equal(local.getItem(P.KEY),before);
 v.element('personalSave').click();assert.deepEqual(P.parse(local.getItem(P.KEY)).hard,ids.slice(1,3));
});
test('unknown UIDs are disclosed, retained only after explicit acknowledgment, and round trip in export',async()=>{
 const v=await app();editor(v);await importFile(v,[ids[0],'vfr-9000']);assert.match(v.element('personalUnknown').textContent,/vfr-9000/);
 change(v,'personalImportMode','add');assert.equal(v.element('personalSave').disabled,true);change(v,'personalUnknownConfirm',true);v.element('personalSave').click();
 assert.deepEqual(P.parse(v.local.getItem(P.KEY)).hard,[ids[0],'vfr-9000']);
 let blob;v.win.URL={createObjectURL:b=>{blob=b;return 'blob:synthetic';},revokeObjectURL:()=>{}};v.element('personalExport').click();
 const exported=P.parse(await blob.text());assert.deepEqual(exported.hard,[ids[0],'vfr-9000']);assert.equal(exported.kind,'vocabulary-fr.personal-hard-backup');
});
test('quota failure, silent storage no-op and failed readback never claim Saved or discard the open draft',async()=>{
 for(const mode of ['quota','noop','readback']){
  const local=storage(new Map([[P.KEY,JSON.stringify(backup([ids[0]]))]])),v=await app({local});editor(v);mark(v,ids[1],true);const old=local.getItem(P.KEY),set=local.setItem,get=local.getItem;let wrote=false;
  local.setItem=(k,value)=>{if(k!==P.KEY)return set(k,value);if(mode==='quota')throw Error('full');if(mode==='noop')return;set(k,value);wrote=true;};
  local.getItem=k=>{if(k===P.KEY&&mode==='readback'&&wrote)throw Error('blocked');return get(k);};
  v.element('personalSave').click();assert.doesNotMatch(v.element('personalNotice').textContent,/^Uloženo/);assert.equal(v.state.view,'personal');assert.equal(v.element('personalGroups').querySelectorAll('.personal-word-check')[1].checked,true);
  if(mode!=='readback')assert.equal(get(P.KEY),old);
 }
});
test('corrupt or inaccessible storage stays untouched while All remains usable without PIN',async()=>{
 const local=storage(new Map([[P.KEY,'{broken']]));const v=await app({local});assert.equal(hardCount(v),18);editor(v);assert.equal(v.element('personalSave').disabled,true);assert.equal(local.getItem(P.KEY),'{broken');assert.match(v.element('personalNotice').textContent,/nelze načíst/);
 const blocked=await app({blocked:true});assert.equal(hardCount(blocked),18);assert.equal(blocked.element('personalHard').disabled,true);
});
test('conflicting tab writes preserve both the stored other-tab state and the unsaved local draft',async()=>{
 const local=storage(),v=await app({local});editor(v);mark(v,ids[0],true);local.setItem(P.KEY,JSON.stringify(backup([ids[1]])));v.emit('storage',{key:P.KEY});v.element('personalSave').click();
 assert.deepEqual(P.parse(local.getItem(P.KEY)).hard,[ids[1]]);assert.match(v.element('personalNotice').textContent,/jiné okno/);assert.equal(v.element('personalGroups').querySelectorAll('.personal-word-check')[0].checked,true);
});
test('invalid files and late file reads never replace current editor changes',async()=>{
 const v=await app();editor(v);mark(v,ids[0],true);await importFile(v,[],{raw:'{"kind":"foreign"}'});assert.match(v.element('personalNotice').textContent,/nebyl načten/);
 let resolve;await importFile(v,[],{text:()=>new Promise(r=>resolve=r)});mark(v,ids[1],true);resolve(JSON.stringify(backup([ids[2]])));await flush();v.element('personalSave').click();assert.deepEqual(P.parse(v.local.getItem(P.KEY)).hard,[ids[0],ids[1]]);
});
test('hard selection is common to gallery, listening, study, loops and practice, with topics and honest small pools',async()=>{
 const local=storage(new Map([[P.KEY,JSON.stringify(backup(ids.slice(0,4)))]])),v=await app({local});v.element('personalHard').click();assert.equal(hardCount(v),4);
 assert.equal(v.element('galleryGroups').querySelectorAll('.vocab-tile').length,4);
 v.galleryModes.find(b=>b.dataset.galleryMode==='listen').click();v.element('galleryGroups').querySelectorAll('.vocab-tile')[0].click();await flush();assert.ok(active(v));v.stopAudioPlayback();
 v.openStudy(ids[0]);assert.equal(v.state.sequence.length,4);loop(v,'words');await phase(v);assert.ok(v.state.sequence.every(i=>ids.slice(0,4).includes(i.uid)));v.stopAudioPlayback();v.returnToGallery();
 v.element('quizTab').click();assert.match(v.element('quizSelection').textContent,/Jen obtížná/);assert.match(v.element('quizPoolNotice').textContent,/4/);assert.equal(v.element('quizStart').disabled,false);v.element('quizBack').click();
 v.state.topics=[vocabulary.groups[0].id];v.selectionChanged();assert.equal(hardCount(v),1);v.element('quizTab').click();assert.equal(v.element('quizStart').disabled,true);assert.match(v.element('quizPoolNotice').textContent,/čtyři|4|alespoň/i);
});

test('new catalog card appears in All while stale legacy profile and personal hard remain separate',async()=>{
 const legacy=learners.empty();legacy.profiles.A.selected=[ids[0]];
 const local=storage(new Map([[learners.KEY,JSON.stringify(legacy)],[P.KEY,JSON.stringify(backup([ids[0]]))]]));
 const newCard={...vocabulary.items[0],uid:'vfr-8000',id:99,fr:'nouveau'};
 const v=await app({local,items:[...vocabulary.items,newCard],url:'https://example.test/vocabulary-fr/#learner=A'});
 assert.equal(hardCount(v),19);v.element('personalHard').click();assert.equal(hardCount(v),1);v.element('personalAll').click();assert.equal(hardCount(v),19);
});

}
