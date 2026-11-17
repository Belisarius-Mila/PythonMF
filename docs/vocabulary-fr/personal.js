/* Private browser-only hard UIDs. The full inventory is always implicit. */
(function(root){
  'use strict';
  const KEY='vocabulary-fr.personal-hard.v1',MAX_BYTES=1000000,MAX_IDS=5000;
  const empty=()=>({schema:1,kind:'vocabulary-fr.personal-hard-backup',language:'fr',hard:[]});
  const fail=message=>{throw new Error(message);};
  function validate(value){
    if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).sort().join(',')!=='hard,kind,language,schema'
      ||value.schema!==1||value.kind!=='vocabulary-fr.personal-hard-backup'||value.language!=='fr'
      ||!Array.isArray(value.hard)||value.hard.length>MAX_IDS
      ||value.hard.some(uid=>typeof uid!=='string'||!/^vfr-[0-9]{4,10}$/.test(uid))
      ||new Set(value.hard).size!==value.hard.length)fail('Toto není platný FR soubor osobních obtížných slov.');
    return {...empty(),hard:[...value.hard]};
  }
  function parse(text){
    if(typeof text!=='string'||new TextEncoder().encode(text).length>MAX_BYTES)fail('Soubor je příliš velký.');
    let value;try{value=JSON.parse(text);}catch(_){fail('Soubor není platný JSON.');}
    return validate(value);
  }
  function store(getStorage){return {
    read(){
      try{const raw=getStorage().getItem(KEY);return {raw,value:raw===null?empty():parse(raw)};}
      catch(_){fail('Osobní označení nelze načíst. Uložená data nepřepisuji; celý slovník je dál dostupný.');}
    },
    write(value,expectedRaw){
      const checked=validate(value),text=JSON.stringify(checked);let storage;
      try{storage=getStorage();if(storage.getItem(KEY)!==expectedRaw)fail('Označení změnilo jiné okno. Tvůj návrh zůstává otevřený; zavři ho a načti aktuální stav.');}
      catch(error){fail(error.message||'Úložiště není dostupné. Návrh zůstává otevřený.');}
      try{storage.setItem(KEY,text);}catch(_){fail('Označení se nepodařilo uložit. Návrh zůstává otevřený; úložiště může být plné nebo blokované.');}
      try{if(storage.getItem(KEY)!==text)throw Error();}
      catch(_){fail('Uložení nelze potvrdit. Návrh zůstává otevřený; nejdřív ověř aktuální uložený stav.');}
      return {raw:text,value:checked};
    }
  };}
  function selection(items,value,onlyHard=false){const hard=new Set(value.hard);return onlyHard?items.filter(item=>hard.has(item.uid)):items;}
  function unknown(value,items){const known=new Set(items.map(item=>item.uid));return value.hard.filter(uid=>!known.has(uid));}
  function proposal(current,imported,mode){
    validate(current);validate(imported);
    if(!['add','replace'].includes(mode))fail('Nejdřív zvol Přidat, nebo Nahradit.');
    return validate({...empty(),hard:mode==='add'?[...new Set([...current.hard,...imported.hard])]:[...imported.hard]});
  }
  const api={KEY,MAX_BYTES,empty,validate,parse,store,selection,unknown,proposal};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.VocabularyFRPersonal=api;
})(globalThis);
