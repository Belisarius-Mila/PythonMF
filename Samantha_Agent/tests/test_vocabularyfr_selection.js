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
 const view=await app({local});view.element('settingsTab').click();view.element('pinInput').value='4826';view.element('unlockButton').click();await until(()=>!view.element('learnerEditor').hidden);
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
