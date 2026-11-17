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
      (!query || normalize(`${item.en} ${item.cz}`).includes(query)));
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
    const language = context.sort === "cz" ? "cz" : "en";
    const collator = new Intl.Collator(language === "cz" ? "cs" : "en", {sensitivity:"base",numeric:true});
    const recommendedRank = item => Math.max(0,groups.findIndex(group=>group.id===item.primaryGroup))*10000+(item.galleryOrder ?? item.order ?? 0);
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
  function audioRecord(item, manifest) {
    const record=manifest?.items?.[String(item?.id)];
    return record && record.sourceEn===item.en && record.sourceCz===item.cz ? record : null;
  }
  function sentenceAudioRecord(item, manifest) {
    const record=manifest?.kind==="sentences" ? manifest.items?.[item?.uid] : null;
    return record && record.uid===item.uid && record.sourceEn===item.en && record.sourceCz===item.cz
      && record.sourceSentenceEn===item.sentenceEn && record.sourceSentenceCz===item.sentenceCz
      && [item.sentenceEn,item.sentenceCz,record.en,record.cz].every(value=>typeof value==="string" && value.trim()) ? record : null;
  }
  function studyPrompt(item, context = {}) {
    const english = context.direction === "enToCz";
    if (context.practice !== "sentences") return {
      text: english ? item.en : item.cz,
      label: english ? "Řekni česky" : "Řekni anglicky",
      language: english ? "en" : "cs", available: true,
    };
    const available = [item.sentenceEn,item.sentenceCz].every(value => typeof value === "string" && value.trim());
    return {
      text: available ? (english ? item.sentenceEn : item.sentenceCz) : "Věta zatím není doplněná.",
      label: english ? "Řekni větu česky" : "Řekni větu anglicky",
      language: available ? (english ? "en" : "cs") : "cs", available,
    };
  }
  function sentencePictures(item, manifest, items=[]) {
    if (manifest?.schemaVersion!==1 || manifest.language!=="en" || manifest.kind!=="sentence-pictures" || manifest.maxPictures!==5) return [];
    const record=manifest.entries?.[item?.uid];
    if (!record || record.reviewed!==true || record.sourceEn!==item.en || record.sourceCz!==item.cz
        || record.sourceSentenceEn!==item.sentenceEn || record.sourceSentenceCz!==item.sentenceCz
        || typeof item.sentenceEn!=="string" || !Array.isArray(items) || !Array.isArray(record.concepts) || !record.concepts.length || record.concepts.length>5) return [];
    const known=new Map(items.filter(isActive).map(entry=>[key(entry),entry])), seen=new Set(), images=new Set(), result=[];
    let end=-1;
    for (const ref of record.concepts) {
      const concept=known.get(ref?.uid);
      if (!concept || concept.en!==ref.sourceEn || concept.cz!==ref.sourceCz || typeof concept.image!=="string" || !concept.image || typeof concept.thumbnail!=="string" || !concept.thumbnail
          || seen.has(ref.uid) || images.has(concept.image) || typeof ref.text!=="string" || !ref.text.trim()
          || !Number.isInteger(ref.start) || !Number.isInteger(ref.end) || ref.start<0 || ref.start<end
          || ref.end<=ref.start || ref.end>item.sentenceEn.length || item.sentenceEn.slice(ref.start,ref.end)!==ref.text) return [];
      const boundary=/[\p{L}\p{N}_’']/u;
      if (boundary.test(item.sentenceEn[ref.start-1] || "") || boundary.test(item.sentenceEn[ref.end] || "")) return [];
      seen.add(ref.uid);images.add(concept.image);end=ref.end;
      result.push({item:concept,text:ref.text,start:ref.start,end:ref.end});
    }
    return result;
  }
  const api = {normalize,key,select,buckets,ordered,shuffle,restoreSequence,audioRecord,sentenceAudioRecord,studyPrompt,sentencePictures,posLabels,levelLabels,countLabel,groupInfo,isActive,teachingType,teachingTypeLabels,recentCount,latestIds};
  if (typeof module !== "undefined" && module.exports) module.exports=api;
  else root.VocabularyModel=api;
})(globalThis);
