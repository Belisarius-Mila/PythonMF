/* Local learner data only; shared vocabulary and media are never written. */
(function(root){
  "use strict";
  const IDS=["A","B","C","D"], KEY="vocabulary-en.learners.v1", ITERATIONS=100000;
  const empty=()=>({schema:1,kind:"vocabulary-en.learners",profiles:Object.fromEntries(IDS.map(id=>[id,{selected:[],hard:[],pin:null}]))});
  const fail=message=>{throw new Error(message);};
  function list(value){
    if(!Array.isArray(value)||value.length>5000||value.some(id=>typeof id!=="string"||!/^ven-[a-zA-Z0-9-]{1,60}$/.test(id)))fail("Soubor obsahuje neplatný seznam slovíček.");
    return [...new Set(value)];
  }
  function profile(value,withPin){
    if(!value||typeof value!=="object")fail("Chybí data uživatele.");
    const selected=list(value.selected),hard=list(value.hard),set=new Set(selected);
    if(hard.some(id=>!set.has(id)))fail("Obtížná slova musí patřit do slovní zásoby.");
    let pin=null;
    if(withPin && value.pin!==null){
      if(!value.pin||value.pin.iterations!==ITERATIONS||!/^[a-f0-9]{32}$/.test(value.pin.salt)||!/^[a-f0-9]{64}$/.test(value.pin.hash))fail("Uložený PIN nelze ověřit.");
      pin={salt:value.pin.salt,hash:value.pin.hash,iterations:ITERATIONS};
    }
    return withPin?{selected,hard,pin}:{selected,hard};
  }
  function validate(value,backup=false){
    if(!value||value.schema!==1||value.kind!==(backup?"vocabulary-en.learner-backup":"vocabulary-en.learners")||!value.profiles||Object.keys(value.profiles).length!==4||IDS.some(id=>!Object.hasOwn(value.profiles,id)))fail("Toto není podporovaná záloha Vocabulary EN.");
    return {schema:1,kind:value.kind,profiles:Object.fromEntries(IDS.map(id=>[id,profile(value.profiles[id],!backup)]))};
  }
  function store(getStorage){
    return {
      read(){
        try{const raw=getStorage().getItem(KEY);return {raw,value:raw===null?empty():validate(JSON.parse(raw))};}
        catch(error){fail("Místní výběry nelze načíst. Společný slovník můžeš dál používat. "+error.message);}
      },
      write(value,expectedRaw){
        const checked=validate(value),text=JSON.stringify(checked),storage=getStorage();
        if(storage.getItem(KEY)!==expectedRaw)fail("Výběry se mezitím změnily v jiném okně. Nejdřív zavři úpravy a znovu je otevři.");
        try{storage.setItem(KEY,text);}catch(_){fail("Výběr se nepodařilo uložit. Úpravy zůstávají otevřené; zkontroluj dostupné úložiště prohlížeče.");}
        if(storage.getItem(KEY)!==text)fail("Uložení výběru nelze potvrdit. Nejdřív ověř data po novém otevření Nastavení.");
        return {raw:text,value:checked};
      }
    };
  }
  function backup(value){const checked=validate(value);return {schema:1,kind:"vocabulary-en.learner-backup",profiles:Object.fromEntries(IDS.map(id=>[id,profile(checked.profiles[id],false)]))};}
  function parseBackup(text){
    if(typeof text!=="string"||text.length>1000000)fail("Záloha je příliš velká.");
    let value;try{value=JSON.parse(text);}catch(_){fail("Záloha není platný JSON soubor.");}
    return validate(value,true);
  }
  const hex=bytes=>Array.from(bytes,b=>b.toString(16).padStart(2,"0")).join("");
  async function hashPin(pin,salt,crypto){
    if(!crypto?.subtle)fail("Tento prohlížeč nepodporuje ověření PINu. Otevři web přes HTTPS v aktuálním prohlížeči.");
    const material=await crypto.subtle.importKey("raw",new TextEncoder().encode(pin),"PBKDF2",false,["deriveBits"]);
    return hex(new Uint8Array(await crypto.subtle.deriveBits({name:"PBKDF2",hash:"SHA-256",salt:Uint8Array.from(salt.match(/../g),s=>parseInt(s,16)),iterations:ITERATIONS},material,256)));
  }
  async function makePin(pin,crypto){
    if(!/^\d{4,8}$/.test(pin))fail("Zvol PIN se 4 až 8 číslicemi.");
    if(!crypto?.getRandomValues)fail("Prohlížeč nepodporuje vytvoření PINu.");
    const salt=hex(crypto.getRandomValues(new Uint8Array(16)));
    return {salt,hash:await hashPin(pin,salt,crypto),iterations:ITERATIONS};
  }
  async function verifyPin(pin,record,crypto){
    if(!/^\d{4,8}$/.test(pin)||!record)return false;
    const hash=await hashPin(pin,record.salt,crypto);let difference=0;
    for(let i=0;i<hash.length;i++)difference|=hash.charCodeAt(i)^record.hash.charCodeAt(i);
    return difference===0;
  }
  function selection(items,value,id,hard=false){
    if(id==="all")return items;
    if(!IDS.includes(id))return [];
    const p=value.profiles[id],selected=new Set(p.selected),difficult=new Set(p.hard);
    return items.filter(item=>selected.has(item.uid)&&(!hard||difficult.has(item.uid)));
  }
  const api={IDS,KEY,empty,validate,store,backup,parseBackup,makePin,verifyPin,selection};
  if(typeof module!=="undefined"&&module.exports)module.exports=api;else root.VocabularyLearners=api;
})(globalThis);
