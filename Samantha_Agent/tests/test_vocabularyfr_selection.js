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

const memory=require('../../docs/vocabulary-fr/memory.js');
const memoryPool=memory.choose(vocabulary.items,audio,quizCatalog,()=>.5);
test('FR online entry transfers only twelve chosen hard-word IDs and preserves personal state',async()=>{
 const personalKey='vocabulary-fr.personal-hard.v1';const local=storage(new Map([[personalKey,JSON.stringify({schema:1,kind:'vocabulary-fr.personal-hard-backup',language:'fr',hard:memoryPool.map(i=>i.uid)})]]));
 const v=await app({local});v.element('personalHard').click();v.element('memoryTab').click();const before=JSON.stringify([...local.map]);
 assert.equal(v.element('memoryOnline').disabled,false);v.element('memoryOnline').click();const url=new URL(v.win.location.href),ids=new URLSearchParams(url.hash.slice(1)).get('words').split(',');
 assert.ok(url.pathname.endsWith('/online.html'));assert.equal(ids.length,12);assert.equal(new Set(ids).size,12);assert.ok(ids.every(uid=>memoryPool.some(i=>i.uid===uid)));assert.equal(JSON.stringify([...local.map]),before);
});
test('FR online entry cannot bypass a selection with fewer than twelve usable pictures',async()=>{
 const v=await app();v.state.query='chat';v.selectionChanged();v.element('memoryTab').click();const before=v.win.location.href;
 assert.equal(v.element('memoryOnline').disabled,true);v.element('memoryOnline').click();assert.equal(v.win.location.href,before);
});
test('FR duel entry keeps the whole filtered pool and the original personal page unchanged',async()=>{
 const origin='https://fixture-mac.fixture-tail.ts.net:8443',v=await app({url:cockpitFrenchUrl(origin)}),opened=[];
 v.win.open=url=>opened.push(url);v.element('memoryTab').click();const before=v.win.location.href,local=JSON.stringify([...v.local.map]);
 assert.equal(v.element('memoryDuel').disabled,false);v.element('memoryDuel').click();
 const url=new URL(opened[0]),pool=new URLSearchParams(url.hash.slice(1)).get('words').split(',');
 assert.equal(url.origin,origin);assert.equal(url.pathname,'/vocabulary-fr/duel.html');assert.equal(pool.length,vocabulary.items.length);assert.ok(pool.length>12);
 assert.equal(v.win.location.href,before);assert.equal(JSON.stringify([...v.local.map]),local);
 v.element('memorySetupChange').click();v.state.query='chat';v.selectionChanged();v.element('memoryTab').click();assert.equal(v.element('memoryDuel').disabled,true);v.element('memoryDuel').click();assert.equal(opened.length,1);
});
test('FR duel requires both language channels while pairs remain usable without Czech audio',async()=>{
 const partial=clone(audio);for(const item of Object.values(partial.items))item.cz=null;
 const v=await app({manifest:partial});v.element('memoryTab').click();assert.equal(v.element('memoryOnline').disabled,false);assert.equal(v.element('memoryDuel').disabled,true);
});
const cockpitGameOrigin='https://fixture-friendly-family-game.trycloudflare.com';
const cockpitFrenchUrl=origin=>'https://belisarius-mila.github.io/PythonMF/vocabulary-fr/#'+new URLSearchParams({onlineOrigin:origin});
test('La phrase éclair opens directly from the main navigation at the verified game origin without personal filters',async()=>{
 const origin='https://fixture-mac.fixture-tail.ts.net:8443',v=await app({url:cockpitFrenchUrl(origin)}),opened=[];
 v.win.open=url=>opened.push(url);
 v.state.query='chat';v.selectionChanged();const local=JSON.stringify([...v.local.map]),before=v.win.location.href;assert.equal(v.element('eclairTab').disabled,false);v.element('eclairTab').click();
 const target=new URL(opened[0]);assert.equal(target.origin,origin);assert.equal(target.pathname,'/vocabulary-fr/eclair.html');assert.equal(target.hash,'');
 assert.equal(v.win.location.href,before);assert.equal(JSON.stringify([...v.local.map]),local);
 v.element('memoryTab').click();const memoryUrl=v.win.location.href,memoryLocal=JSON.stringify([...v.local.map]);v.element('memoryEclair').click();assert.equal(opened[1],opened[0]);assert.equal(v.win.location.href,memoryUrl);assert.equal(JSON.stringify([...v.local.map]),memoryLocal);
});
test('private Tailscale game uses only its dedicated HTTPS port and survives reload',async()=>{
 const origin='https://fixture-mac.fixture-tail.ts.net:8443',session=storage(),first=await app({url:cockpitFrenchUrl(origin),session}),opened=[];
 first.win.open=url=>opened.push(url);first.element('memoryTab').click();first.element('memoryOnline').click();assert.equal(new URL(opened[0]).origin,origin);
 const next=await app({url:first.win.location.href,session});next.win.open=url=>opened.push(url);next.element('memoryTab').click();next.element('memoryOnline').click();assert.equal(new URL(opened[1]).origin,origin);
 for(const bad of [origin.replace(':8443',''),origin.replace(':8443',':8770'),origin.replace(':8443',':443'),origin+'/path','http://fixture-mac.fixture-tail.ts.net:8443','https://user@fixture-mac.fixture-tail.ts.net:8443',origin+'.untrusted.example']){
  const view=await app({url:cockpitFrenchUrl(bad)}),wrong=[];view.win.open=url=>wrong.push(url);view.element('memoryTab').click();view.element('memoryOnline').click();assert.equal(wrong.length,0);
 }
});
test('Cockpit entry opens the chosen hard words directly and preserves the original French tab and personal data',async()=>{
 const personalKey='vocabulary-fr.personal-hard.v1',local=storage(new Map([[personalKey,JSON.stringify({schema:1,kind:'vocabulary-fr.personal-hard-backup',language:'fr',hard:memoryPool.map(i=>i.uid)})]]));
 const v=await app({url:cockpitFrenchUrl(cockpitGameOrigin),local});v.element('personalHard').click();v.element('memoryTab').click();
 const before=v.win.location.href,personal=JSON.stringify([...local.map]),opened=[];v.win.open=(...args)=>{opened.push(args);return null;};v.element('memoryOnline').click();
 assert.equal(opened.length,1);const url=new URL(opened[0][0]),params=new URLSearchParams(url.hash.slice(1));
 assert.equal(url.origin,cockpitGameOrigin);assert.equal(url.pathname,'/vocabulary-fr/online.html');assert.equal(params.size,1);
 assert.equal(params.get('words').split(',').length,12);assert.ok(params.get('words').split(',').every(uid=>memoryPool.some(i=>i.uid===uid)));
 assert.deepEqual(opened[0].slice(1),['_blank','noopener,noreferrer']);assert.equal(v.win.location.href,before);assert.equal(JSON.stringify([...local.map]),personal);
 assert.equal(v.session.getItem('vocabulary-fr.online-origin.v1'),cockpitGameOrigin);assert.match(v.element('memoryPoolNotice').textContent,/nové kartě/);
});
test('the Cockpit game address survives route changes and reload and a fresh launch replaces the prior temporary address',async()=>{
 const session=storage(),first=await app({url:cockpitFrenchUrl(cockpitGameOrigin),session});first.element('memoryTab').click();
 const reloaded=await app({url:first.win.location.href,session}),opened=[];reloaded.win.open=url=>opened.push(url);reloaded.element('memoryTab').click();reloaded.element('memoryOnline').click();
 assert.equal(new URL(opened[0]).origin,cockpitGameOrigin);
 const newer='https://fixture-next-family-game.trycloudflare.com',fresh=await app({url:cockpitFrenchUrl(newer),session});fresh.win.open=url=>opened.push(url);fresh.element('memoryTab').click();fresh.element('memoryOnline').click();assert.equal(new URL(opened[1]).origin,newer);
});
test('an arbitrary URL or credentials cannot be used as the remote game address',async()=>{
 for(const origin of ['javascript:alert(1)','https://untrusted.example','http://fixture-friendly-family-game.trycloudflare.com',cockpitGameOrigin+'/path',cockpitGameOrigin+'?token=x',cockpitGameOrigin+'#x',cockpitGameOrigin+':8443','https://name:secret@fixture-friendly-family-game.trycloudflare.com',cockpitGameOrigin+'.untrusted.example']){
  const v=await app({url:cockpitFrenchUrl(origin)}),opened=[];v.win.open=url=>opened.push(url);v.element('memoryTab').click();v.element('memoryOnline').click();assert.equal(opened.length,0);assert.equal(new URL(v.win.location.href).origin,'https://belisarius-mila.github.io');
 }
});
test('a Cockpit entry works with blocked storage for the current page without moving the personal app',async()=>{
 const v=await app({url:cockpitFrenchUrl(cockpitGameOrigin),blocked:true}),opened=[];v.win.open=url=>opened.push(url);v.element('memoryTab').click();v.element('memoryOnline').click();assert.equal(new URL(opened[0]).origin,cockpitGameOrigin);assert.equal(new URL(v.win.location.href).origin,'https://belisarius-mila.github.io');
});
test('the Cockpit game shortcut cannot open a room with too few selected pictures',async()=>{
 const v=await app({url:cockpitFrenchUrl(cockpitGameOrigin)}),opened=[];v.win.open=url=>opened.push(url);v.state.query='chat';v.selectionChanged();v.element('memoryTab').click();v.element('memoryOnline').click();assert.equal(v.element('memoryOnline').disabled,true);assert.equal(opened.length,0);
});
const memorySaved=v=>JSON.parse(v.session.getItem(memory.KEY));
test('permanent hosting configuration replaces an expired tunnel and preserves personal data and filters',async()=>{
 const origin='https://fixture-french-pairs.onrender.com',hosting={schemaVersion:1,origin},session=storage(new Map([['vocabulary-fr.online-origin.v1',cockpitGameOrigin]]));
 const v=await app({hosting,session,url:cockpitFrenchUrl('https://other-service.onrender.com')}),opened=[];
 v.win.open=url=>opened.push(url);v.element('memoryTab').click();const context=JSON.stringify(v.context()),personal=JSON.stringify([...v.local.map]);
 v.element('memoryOnline').click();assert.equal(new URL(opened[0]).origin,origin);assert.equal(JSON.stringify(v.context()),context);assert.equal(JSON.stringify([...v.local.map]),personal);
 assert.equal(new URLSearchParams(new URL(opened[0]).hash.slice(1)).get('words').split(',').length,12);
});
test('late hosting metadata updates an already open pairs screen without blocking the vocabulary',async()=>{
 let resolve;const pending=new Promise(done=>{resolve=done;}),v=await app({hostingDeferred:pending}),opened=[];
 v.win.open=url=>opened.push(url);v.element('memoryTab').click();assert.equal(v.element('memoryStart').disabled,false);
 resolve({schemaVersion:1,origin:'https://fixture-late-fr.onrender.com'});await flush();
 v.element('memoryOnline').click();assert.equal(new URL(opened[0]).origin,'https://fixture-late-fr.onrender.com');
});
test('invalid hosting metadata and a fragment alone cannot enable arbitrary Render services',async()=>{
 for(const hosting of [null,{schemaVersion:2,origin:'https://fixture-fr.onrender.com'},...['https://foreign.example','http://fixture-fr.onrender.com','https://fixture-fr.onrender.com/path','https://name:secret@fixture-fr.onrender.com','https://fixture-fr.onrender.com:8443','https://fixture-fr.onrender.com?x=1'].map(origin=>({schemaVersion:1,origin}))]){
  const v=await app({hosting,url:cockpitFrenchUrl('https://another-fr.onrender.com')}),opened=[];v.win.open=url=>opened.push(url);v.element('memoryTab').click();v.element('memoryOnline').click();assert.equal(opened.length,0);
 }
});
const memoryButton=(v,n)=>v.element('memoryBoard').children[n].querySelector('button');
async function memoryView(count=2,options={}){
 const v=await app(options);v.element('memoryTab').click();change(v,'memoryPlayerCount',String(count));
 v.element('memoryNames').querySelectorAll('input').forEach((input,i)=>{input.value=['Jana','Eva','Petr','Tom'][i];input.emit('input');});
 v.element('memoryStart').click();await flush();return v;
}
async function memoryHear(v,n){memoryButton(v,n).click();await until(()=>active(v));assert.match(active(v).url,/-fr\.mp3$/);ended(v);await flush();v.advance(2000);await flush();}
async function memoryFinishReward(v){await until(()=>active(v));ended(v);await flush();v.advance(2000);await flush();}
async function memoryPair(v,a,b){await memoryHear(v,a);await memoryHear(v,b);v.advance(1000);await flush();if(v.element('memoryReward').open)await memoryFinishReward(v);}
function memoryPositions(g,uid){return g.deck.flatMap((x,i)=>x===uid?[i]:[]);}

test('FR memory chooses12 distinct compatible meanings with French audio and keeps source metadata intact',()=>{
 const before=JSON.stringify([vocabulary,audio,quizCatalog]);assert.equal(memoryPool.length,12);
 const game=memory.newGame(memoryPool,['Jana']);assert.equal(game.deck.length,24);assert.equal(new Set(game.deck).size,12);
 for(const uid of new Set(game.deck))assert.equal(memoryPositions(game,uid).length,2);
 const changed=clone(audio);changed.items[cat.uid].fr=null;assert.equal(memory.choose([cat],changed,quizCatalog).length,0);
 const sameAudio=clone(audio);sameAudio.items[vocabulary.items[1].uid].fr=sameAudio.items[cat.uid].fr;
 assert.equal(memory.choose([cat,vocabulary.items[1]],sameAudio,quizCatalog).length,1);
 assert.equal(memory.choose(memoryPool.slice(0,11),audio,quizCatalog).length,11);
 assert.equal(JSON.stringify([vocabulary,audio,quizCatalog]),before);
});
test('FR memory keeps consecutive successful turns for one named player and cycles1–4 players on misses',()=>{
 for(let n=1;n<=4;n++){
  let g=memory.newGame(memoryPool,['Jana','Eva','Petr','Tom'].slice(0,n));
  assert.throws(()=>memory.settle(g,0,24));assert.throws(()=>memory.settle(g,0,0));
  g=memory.settle(g,0,g.deck.findIndex(x=>x!==g.deck[0]));assert.equal(g.active,1%n);
  const owner=g.active;for(const uid of new Set(g.deck)){g=memory.settle(g,...memoryPositions(g,uid));assert.equal(g.active,owner);}
  assert.equal(Object.keys(g.owners).length,12);assert.equal(Object.values(g.owners).filter(x=>x===owner).length,12);
  assert.throws(()=>memory.settle(g,...memoryPositions(g,g.deck[0])));
 }
});
test('FR memory opens24 numbered backs, short names and projector view without leaking French answers',async()=>{
 const v=await memoryView(4);assert.equal(v.state.view,'memory');assert.match(v.win.location.href,/game=memory-pairs/);
 assert.equal(v.element('memoryBoard').children.length,24);assert.equal(v.element('memoryBoard').querySelectorAll('img').length,0);
 v.element('memoryBoard').children.forEach((slot,n)=>{const b=slot.querySelector('button');assert.equal(b.textContent,String(n+1));assert.equal(b.getAttribute('aria-label'),`Kartička ${n+1}, zavřená`);});
 assert.deepEqual(memorySaved(v).game.players,['Jana','Eva','Petr','Tom']);assert.equal(v.element('memoryScores').children.length,4);
 v.element('memoryProjector').click();assert.equal(v.element('memoryView').classList.contains('memory-projector'),true);
});
test('FR memory waits for French audio completion and two-second Czech hint and ignores rapid extra clicks',async()=>{
 const v=await memoryView();memoryButton(v,0).click();await until(()=>active(v));const p=active(v);
 assert.match(p.url,/-fr\.mp3$/);assert.equal(v.element('memoryBoard').querySelector('.memory-word').lang,'fr');
 assert.equal(v.element('memoryBoard').querySelectorAll('.memory-translation').length,1);
 memoryButton(v,1).click();v.advance(2000);await flush();assert.equal(v.element('memoryBoard').querySelectorAll('.memory-translation').length,0);
 assert.equal(memoryButton(v,1).disabled,true);assert.equal(v.players.filter(p=>p.playCount>0).length,1);
 ended(v);await flush();assert.equal(memoryButton(v,1).disabled,false);assert.equal(memorySaved(v).game.turns,0);
});
test('FR memory awards a pair once, leaves two grey holes and preserves the same player for another pair',async()=>{
 const v=await memoryView(3),g=memorySaved(v).game,[a,b]=memoryPositions(g,g.deck[0]);
 await memoryHear(v,a);await memoryHear(v,b);assert.equal(v.element('memoryBoard').querySelectorAll('.memory-match').length,2);
 v.advance(1000);await flush();assert.equal(v.element('memoryBoard').querySelectorAll('.memory-empty').length,2);
 assert.equal(memorySaved(v).game.active,0);assert.match(v.element('memoryScores').children[0].textContent,/Jana.*Dvojice: 1/);
 await memoryFinishReward(v);const uid=g.deck.find(x=>x!==g.deck[0]);await memoryPair(v,...memoryPositions(g,uid));assert.equal(memorySaved(v).game.active,0);assert.equal(Object.keys(memorySaved(v).game.owners).length,2);
});
test('FR memory mismatch closes both cards and changes to the next player',async()=>{
 const v=await memoryView(3),g=memorySaved(v).game;await memoryPair(v,0,g.deck.findIndex(x=>x!==g.deck[0]));
 assert.equal(memorySaved(v).game.active,1);assert.equal(v.element('memoryBoard').querySelectorAll('img').length,0);assert.equal(v.element('memoryBoard').children.length,24);
});
test('FR memory restores completed turns and original selection after reload without autoplay',async()=>{
 const v=await memoryView(),g=memorySaved(v).game;await memoryPair(v,...memoryPositions(g,g.deck[0]));
 memoryButton(v,g.deck.findIndex(x=>x!==g.deck[0])).click();await until(()=>active(v));v.emit('pagehide');
 const reloaded=await app({session:v.session,local:v.local,url:v.win.location.href+'&topics=topic-01'});assert.equal(reloaded.state.view,'memory');assert.equal(active(reloaded),undefined);
 reloaded.element('memoryResume').click();assert.equal(reloaded.element('memoryBoard').children.length,24);assert.deepEqual([...reloaded.state.topics],['topic-01']);
 assert.equal(reloaded.element('memoryBoard').querySelectorAll('.memory-empty').length,2);assert.equal(reloaded.element('memoryBoard').querySelectorAll('img').length,0);assert.equal(memorySaved(reloaded).game.turns,1);
 const saved=memorySaved(reloaded);assert.deepEqual(memory.restore(saved,vocabulary.items,audio,quizCatalog),saved.game);
 const bad=clone(saved);bad.game.deck[0]='ven-0001';assert.equal(memory.restore(bad,vocabulary.items,audio,quizCatalog),null);
 const changed=clone(audio);changed.items[g.deck[0]].fr=null;assert.equal(memory.restore(saved,vocabulary.items,changed,quizCatalog),null);
});
test('FR memory respects Jana hard words and every gallery filter without writing personal or legacy state',async()=>{
 const personalKey='vocabulary-fr.personal-hard.v1',legacy='legacy untouched';
 const local=storage(new Map([[personalKey,JSON.stringify({schema:1,kind:'vocabulary-fr.personal-hard-backup',language:'fr',hard:memoryPool.map(i=>i.uid)})],[learners.KEY,legacy],['vocabulary-en.memory-pairs.v1','unrelated']]));
 const v=await app({local});v.element('personalHard').click();const before=JSON.stringify([...local.map]);
 v.element('memoryTab').click();assert.match(v.element('memorySelection').textContent,/Jen obtížná/);assert.equal(v.element('memoryStart').disabled,false);v.element('memoryStart').click();
 assert.ok(memorySaved(v).game.deck.every(uid=>memoryPool.some(i=>i.uid===uid)));await memoryHear(v,0);assert.equal(JSON.stringify([...local.map]),before);
 v.element('memoryBack').click();change(v,'searchInput','chat');v.element('searchInput').emit('input');v.element('memoryTab').click();assert.equal(v.element('memoryStart').disabled,true);
 v.element('memorySetupChange').click();v.state.query='';v.state.topics=['topic-01'];v.selectionChanged();v.element('memoryTab').click();assert.equal(v.element('memoryStart').disabled,true);
 assert.equal(local.getItem(learners.KEY),legacy);assert.equal(local.getItem('vocabulary-en.memory-pairs.v1'),'unrelated');
});
test('FR memory failures offer retry or explicit skip and never borrow the Czech channel',async()=>{
 const v=await memoryView(2,{audioReject:true});memoryButton(v,0).click();await flush();v.advance(2000);await flush();
 assert.equal(v.element('memorySkip').hidden,false);assert.equal(memorySaved(v).game.turns,0);assert.ok(v.players.filter(p=>p.playCount).every(p=>/-fr\.mp3$/.test(p.url)));
 v.setAudioReject(false);v.element('memoryRetry').click();await until(()=>active(v));ended(v);await flush();v.advance(2000);await flush();assert.equal(memoryButton(v,1).disabled,false);
 const none=await memoryView(2,{manifest:null});assert.equal(none.element('memoryStart').disabled,true);assert.equal(active(none),undefined);
});
test('FR memory confirms leaving for gallery, practice or settings and cancels stale audio when approved',async()=>{
 const v=await memoryView();memoryButton(v,0).click();await until(()=>active(v));const p=active(v);
 v.win.confirm=()=>false;for(const id of ['galleryTab','quizTab','settingsTab']){v.element(id).click();assert.equal(v.state.view,'memory');}
 v.win.confirm=()=>true;v.element('quizTab').click();assert.equal(v.state.view,'quiz');assert.equal(p.paused,true);v.advance(10000);await flush();assert.equal(memorySaved(v).game.turns,0);
 v.element('memoryTab').click();v.element('memoryResume').click();v.win.confirm=()=>false;v.win.location.href='https://example.test/PythonMF/vocabulary-fr/#card='+cat.uid;v.emit('hashchange');assert.equal(v.state.view,'memory');assert.match(v.win.location.href,/memory-pairs/);
});
test('FR memory finishes12 pairs with tie, player collections and replay of the same vocabulary',async()=>{
 const g=memory.newGame(memoryPool,['Jana','Eva']),uids=[...new Set(g.deck)];g.owners=Object.fromEntries(uids.slice(0,11).map((uid,n)=>[uid,n<6?0:1]));g.active=1;g.turns=11;
 const session=storage();session.setItem(memory.KEY,JSON.stringify({version:1,filters:{},game:g,source:memory.signature(g.deck,vocabulary.items,audio)}));
 const v=await app({session,url:'https://example.test/PythonMF/vocabulary-fr/#game=memory-pairs'});v.element('memoryResume').click();await memoryPair(v,...memoryPositions(g,uids[11]));
 assert.equal(v.element('memoryEnd').hidden,false);assert.match(v.element('memoryResult').textContent,/Remíza/);assert.equal(v.element('memoryCollections').children.length,2);assert.equal(v.element('memoryBoard').querySelectorAll('.memory-empty').length,24);
 v.element('memoryAgain').click();assert.equal(v.element('memoryEnd').hidden,true);assert.equal(Object.keys(memorySaved(v).game.owners).length,0);assert.deepEqual([...new Set(memorySaved(v).game.deck)].sort(),uids.sort());
});
test('FR memory works with blocked storage and never starts or resumes audio from its link',async()=>{
 const v=await memoryView(1,{blocked:true,url:'https://example.test/PythonMF/vocabulary-fr/#game=memory-pairs'});
 assert.equal(v.element('memoryBoard').children.length,24);assert.match(v.element('memoryStorageNotice').textContent,/nepodařilo uložit/);assert.equal(active(v),undefined);
 const missing=await app({failQuiz:true});missing.element('memoryTab').click();assert.equal(missing.element('memoryStart').disabled,true);
});

async function memoryAward(v){const g=memorySaved(v).game,[a,b]=memoryPositions(g,g.deck[0]);await memoryHear(v,a);await memoryHear(v,b);v.advance(1000);await flush();return vocabulary.items.find(i=>i.uid===g.deck[0]);}
test('FR memory reward shows a large source image and French word only for exactly two seconds after a match',async()=>{
 const v=await memoryView(),item=await memoryAward(v),dialog=v.element('memoryReward');
 assert.equal(dialog.open,true);assert.equal(dialog.hidden,false);assert.equal(v.element('memoryRewardWord').textContent,item.fr);
 let prevented=false,stopped=false;dialog.emit('cancel',{preventDefault:()=>{prevented=true;}});dialog.emit('keydown',{key:'Escape',stopPropagation:()=>{stopped=true;}});assert.equal(prevented&&stopped,true);assert.equal(dialog.open,true);
 assert.equal(v.element('memoryRewardImage').src,new URL('../'+item.image,v.win.location.href).toString());
 assert.equal(v.element('memoryRewardWord').textContent.includes(item.cz),false);assert.match(active(v).url,/-fr\.mp3$/);
 assert.equal(v.players.filter(p=>p.playCount).length,3);assert.equal(Object.keys(memorySaved(v).game.owners).length,1);
 ended(v);await flush();v.advance(1999);await flush();assert.equal(dialog.open,true);assert.equal(v.element('memoryBoard').querySelector('button').disabled,true);
 v.advance(1);await flush();assert.equal(dialog.open,false);assert.equal(dialog.hidden,true);assert.equal(memorySaved(v).game.active,0);
 const next=v.element('memoryBoard').querySelector('button');assert.equal(next.disabled,false);assert.equal(v.doc.activeElement,next);
});
test('FR memory reward closes after two seconds but a longer French recording keeps the next turn locked until ended',async()=>{
 const v=await memoryView();await memoryAward(v);const p=active(v);v.advance(2000);await flush();
 assert.equal(v.element('memoryReward').open,false);assert.equal(v.element('memoryBoard').querySelector('button').disabled,true);
 v.element('memoryBoard').querySelector('button').click();assert.equal(v.players.filter(p=>p.playCount).length,3);
 ended(v);await flush();assert.equal(p.paused,true);assert.equal(v.element('memoryBoard').querySelector('button').disabled,false);assert.equal(memorySaved(v).game.turns,1);
});
test('FR memory reward never appears or adds a third playback for a mismatch',async()=>{
 const v=await memoryView(),g=memorySaved(v).game;await memoryPair(v,0,g.deck.findIndex(x=>x!==g.deck[0]));
 assert.notEqual(v.element('memoryReward').open,true);assert.equal(v.players.filter(p=>p.playCount).length,2);assert.equal(memorySaved(v).game.active,1);
});
test('FR memory interrupted reward is cancelled and the awarded pair survives reload without replay or duplicate scoring',async()=>{
 const v=await memoryView();await memoryAward(v);const p=active(v);v.emit('pagehide');assert.equal(p.paused,true);assert.equal(v.element('memoryReward').hidden,true);
 v.advance(5000);await flush();const raw=v.session.getItem(memory.KEY),reloaded=await app({session:v.session,url:v.win.location.href});
 assert.equal(active(reloaded),undefined);reloaded.element('memoryResume').click();assert.notEqual(reloaded.element('memoryReward').open,true);
 assert.equal(reloaded.element('memoryBoard').querySelectorAll('.memory-empty').length,2);assert.equal(reloaded.session.getItem(memory.KEY),raw);assert.equal(memorySaved(reloaded).game.turns,1);
});
test('FR memory failed reward audio preserves the earned pair, unlocks play and never substitutes Czech',async()=>{
 const v=await memoryView(),g=memorySaved(v).game,[a,b]=memoryPositions(g,g.deck[0]);await memoryHear(v,a);await memoryHear(v,b);v.setAudioReject(true);v.advance(1000);await flush();
 assert.equal(v.element('memoryReward').open,true);v.advance(2000);await flush();assert.equal(v.element('memoryReward').hidden,true);
 assert.equal(Object.keys(memorySaved(v).game.owners).length,1);assert.equal(memorySaved(v).game.active,0);assert.equal(v.element('memoryBoard').querySelector('button').disabled,false);
 assert.match(v.element('memoryStatus').textContent,/Dodatečný zvuk/);assert.ok(v.players.filter(p=>p.playCount).every(p=>/-fr\.mp3$/.test(p.url)));
});
test('FR memory shows the last reward before the final result, then completes the game',async()=>{
 const g=memory.newGame(memoryPool,['Jana']),uids=[...new Set(g.deck)];g.owners=Object.fromEntries(uids.slice(0,11).map(uid=>[uid,0]));g.turns=11;
 const session=storage();session.setItem(memory.KEY,JSON.stringify({version:1,filters:{},game:g,source:memory.signature(g.deck,vocabulary.items,audio)}));
 const v=await app({session,url:'https://example.test/PythonMF/vocabulary-fr/#game=memory-pairs'});v.element('memoryResume').click();const [a,b]=memoryPositions(g,uids[11]);await memoryHear(v,a);await memoryHear(v,b);v.advance(1000);await flush();
 assert.equal(v.element('memoryReward').open,true);assert.equal(v.element('memoryEnd').hidden,true);assert.equal(Object.keys(memorySaved(v).game.owners).length,12);
 await memoryFinishReward(v);assert.equal(v.element('memoryEnd').hidden,false);assert.match(v.element('memoryResult').textContent,/všech 12/);assert.equal(v.doc.activeElement,v.element('memoryResult'));
});
