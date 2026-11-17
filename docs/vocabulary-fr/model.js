/* Shared selection and navigation rules; no DOM, network, or learner writes. */
(function (root) {
  "use strict";
  const posLabels = {noun:"Podstatná jména",verb:"Slovesa",adjective:"Přídavná jména",adverb:"Příslovce",pronoun:"Zájmena",number:"Číslovky",preposition:"Předložky",conjunction:"Spojky",article:"Členy",determiner:"Určující slova",particle:"Částice",interjection:"Citoslovce","verb-modal":"Způsobová slovesa",other:"Další výrazy"};
  const teachingTypeLabels = {word:"Slovíčka",interaction:"Interakce",idiom:"Fráze"};
  const isActive = item => item.active !== false;
  const teachingType = item => item.teachingType || "word";
  const countLabel = n => `${n} ${n === 1 ? "slovíčko" : n >= 2 && n <= 4 ? "slovíčka" : "slovíček"}`;
  const levelLabels = {1:"Názorné a základní",2:"Běžné použití",3:"Potřebuje větu"};
  const normalize = value => String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("cs").trim();
  const key = item => String(item.uid || item.id);
  const any = (selected, values) => !selected.length || values.some(value => selected.includes(String(value)));
  function recentCount(value) {
    if(typeof value!=="number" && (typeof value!=="string" || !/^[0-9]+$/.test(value)))return 0;
    const count=Number(value);
    return Number.isSafeInteger(count) && count>0 && count<=5000 ? count : 0;
  }
  function latestIds(items, value) {
    const count=recentCount(value);
    return count ? new Set(items.filter(isActive).slice().sort((a,b)=>Number(b.id)-Number(a.id)).slice(0,count).map(key)) : null;
  }
  function select(items, context = {}, allItems = items) {
    const query = normalize(context.query);
    const latest=latestIds(allItems,context.recentCount);
    const topics = context.topics || [], sources = context.sources || [], parts = context.parts || [], levels = context.levels || [];
    return items.filter(item =>
      isActive(item) && (!latest || latest.has(key(item))) && (!context.teachingType || context.teachingType === "all" || teachingType(item) === context.teachingType) &&
      (context.filter !== "selected" || item.selected) && (context.filter !== "hard" || item.hardTraining) &&
      any(topics, item.topicIds || []) && any(sources, item.sourceIds || []) &&
      // Keep the former multiword filter usable in old links. New controls
      // use teachingType independently from grammatical part of speech.
      any(parts, [...(item.partOfSpeech || []), ...(item.expressionType === "phrase" ? ["expression"] : [])]) &&
      any(levels, [item.difficultyBand || "unclassified"]) &&
      (!query || normalize(`${item.fr} ${item.cz}`).includes(query)));
  }
  function groupInfo(item, context = {}, catalog = {}) {
    const groupBy = context.groupBy || "topic";
    const topic = (catalog.groups || []).find(group => group.id === item.primaryGroup);
    if (groupBy === "none") return {id:"all", label:"Všechna vybraná slovíčka"};
    if (groupBy === "part") {const id=item.partOfSpeech?.[0] || "other"; return {id,label:posLabels[id] || "Další výrazy"};}
    if (groupBy === "level") {const id=String(item.difficultyBand || "unclassified"); return {id,label:levelLabels[id] || "Zatím nezařazené"};}
    return {id:topic?.id || "unclassified",label:topic?.label || "Další slovíčka",parentId:topic?.parentId};
  }
  function buckets(items, context, catalog = {}) {
    const groups = catalog.groups || [], byId = new Map(groups.map(group => [group.id, group]));
    const groupBy = context.groupBy || "topic";
    const idFor = item => groupBy === "none" ? "all" : groupBy === "part" ? item.partOfSpeech?.[0] || "other" : groupBy === "level" ? String(item.difficultyBand || "unclassified") : item.primaryGroup || "unclassified";
    const labelFor = id => groupBy === "none" ? "Všechna vybraná slovíčka" : groupBy === "part" ? posLabels[id] || "Další výrazy" : groupBy === "level" ? levelLabels[id] || "Zatím nezařazené" : byId.get(id)?.label || "Další slovíčka";
    const preferred = groupBy === "topic" ? groups.map(group => group.id) : groupBy === "part" ? Object.keys(posLabels) : ["1","2","3","unclassified"];
    const map = new Map();
    for (const item of items.filter(isActive)) {
      const id = idFor(item);
      if (!map.has(id)) map.set(id, {id,label:labelFor(id),parentId:byId.get(id)?.parentId,items:[]});
      map.get(id).items.push(item);
    }
    const language = context.sort === "cz" ? "cz" : "fr";
    const collator = new Intl.Collator(language === "cz" ? "cs" : "fr", {sensitivity:"base",numeric:true});
    const recommendedRank = item => Math.max(0,groups.findIndex(group=>group.id===item.primaryGroup))*10000+(item.galleryOrder ?? item.order ?? item.id ?? 0);
    const compare = (a,b) => (context.sort === "recommended" || !context.sort ? recommendedRank(a) - recommendedRank(b) : collator.compare(a[language],b[language])) || key(a).localeCompare(key(b));
    return [...map.values()].sort((a,b) => {
      const rank = id => preferred.includes(id) ? preferred.indexOf(id) : preferred.length;
      return rank(a.id)-rank(b.id) || a.label.localeCompare(b.label,"cs");
    }).map(group => ({...group,items:group.items.sort(compare)}));
  }
  function ordered(items, context, catalog, allItems=items) { return buckets(select(items,context,allItems),context,catalog).flatMap(group => group.items); }
  function shuffle(items, random = Math.random) {
    const result = [...items];
    for (let i=result.length-1;i>0;i--) { const j=Math.floor(random()*(i+1)); [result[i],result[j]]=[result[j],result[i]]; }
    return result;
  }
  function restoreSequence(keys, items) {
    const known = new Map(items.filter(isActive).map(item => [key(item),item]));
    return [...new Set(keys)].filter(id => known.has(id)).map(id => known.get(id));
  }
  const audioStatuses=new Set(["not-generated","partial","complete"]);
  function mediaPath(path,kind){return typeof path==="string" && new RegExp(`^assets/vocabulary-fr-${kind}/[a-zA-Z0-9_/-]+\\.mp3$`).test(path) && !path.includes("..") && !path.includes("//");}
  function checkedAudio(item,manifest,kind){
    if(manifest?.schemaVersion!==1 || manifest.language!=="fr" || manifest.kind!==kind || !audioStatuses.has(manifest.status))return null;
    const record=manifest.items?.[item?.uid];
    if(!record || record.uid!==item?.uid || record.sourceFr!==item.fr || record.sourceCz!==item.cz)return null;
    if(kind==="sentences" && (record.sourceSentenceFr!==item.sentenceFr || record.sourceSentenceCz!==item.sentenceCz
        || ![item.sentenceFr,item.sentenceCz].every(value=>typeof value==="string" && value.trim())))return null;
    const namespace=kind==="sentences" ? "sentences" : "audio";
    // Validate each channel independently. A missing/unsafe FR path never borrows CZ.
    return {...record,fr:mediaPath(record.fr,namespace) ? record.fr : null,cz:mediaPath(record.cz,namespace) ? record.cz : null};
  }
  function audioRecord(item,manifest){return checkedAudio(item,manifest,"words");}
  function sentenceAudioRecord(item,manifest){return checkedAudio(item,manifest,"sentences");}
  function studyPrompt(item, context = {}) {
    const french = context.direction === "frToCz";
    if (context.practice !== "sentences") return {
      text: french ? item.fr : item.cz,
      label: french ? "Řekni česky" : "Řekni francouzsky",
      language: french ? "fr" : "cs", available: true,
    };
    const available = [item.sentenceFr,item.sentenceCz].every(value => typeof value === "string" && value.trim());
    return {
      text: available ? (french ? item.sentenceFr : item.sentenceCz) : "Věta zatím není doplněná.",
      label: french ? "Řekni větu česky" : "Řekni větu francouzsky",
      language: available ? (french ? "fr" : "cs") : "cs", available,
    };
  }
  function sentencePictures(item, manifest, items=[]) {
    if (manifest?.schemaVersion!==1 || manifest.language!=="fr" || manifest.kind!=="sentence-pictures" || manifest.maxPictures!==5) return [];
    const record=manifest.entries?.[item?.uid];
    if (!record || record.reviewed!==true || record.sourceFr!==item.fr || record.sourceCz!==item.cz
        || record.sourceSentenceFr!==item.sentenceFr || record.sourceSentenceCz!==item.sentenceCz
        || typeof item.sentenceFr!=="string" || !Array.isArray(items) || !Array.isArray(record.concepts) || !record.concepts.length || record.concepts.length>5) return [];
    const known=new Map(items.filter(isActive).map(entry=>[key(entry),entry])), seen=new Set(), images=new Set(), result=[];
    let end=-1;
    for (const ref of record.concepts) {
      const concept=known.get(ref?.uid);
      if (!concept || concept.fr!==ref.sourceFr || concept.cz!==ref.sourceCz || typeof concept.image!=="string" || !concept.image || typeof concept.thumbnail!=="string" || !concept.thumbnail
          || seen.has(ref.uid) || images.has(concept.image) || typeof ref.text!=="string" || !ref.text.trim()
          || !Number.isInteger(ref.start) || !Number.isInteger(ref.end) || ref.start<0 || ref.start<end
          || ref.end<=ref.start || ref.end>item.sentenceFr.length || item.sentenceFr.slice(ref.start,ref.end)!==ref.text) return [];
      const boundary=/[\p{L}\p{N}_]/u;
      if (boundary.test(item.sentenceFr[ref.start-1] || "") || boundary.test(item.sentenceFr[ref.end] || "")) return [];
      seen.add(ref.uid);images.add(concept.image);end=ref.end;
      result.push({item:concept,text:ref.text,start:ref.start,end:ref.end});
    }
    return result;
  }
  const api = {normalize,key,select,buckets,ordered,shuffle,restoreSequence,audioRecord,sentenceAudioRecord,studyPrompt,sentencePictures,posLabels,levelLabels,countLabel,groupInfo,isActive,teachingType,teachingTypeLabels,recentCount,latestIds};
  if (typeof module !== "undefined" && module.exports) module.exports=api;
  else root.VocabularyFRModel=api;
})(globalThis);
