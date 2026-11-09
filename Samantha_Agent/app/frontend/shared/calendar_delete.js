(() => {
  const endpoint="/api/calendar/delete";
  const date=new Intl.DateTimeFormat("cs-CZ",{timeZone:"Europe/Prague",dateStyle:"long",timeStyle:"short"});
  let active=false;
  async function api(payload) {
    const controller=new AbortController(), timer=setTimeout(()=>controller.abort(),payload.action==="authorize"?210000:35000);
    try {
      const response=await fetch(endpoint,{method:"POST",cache:"no-store",signal:controller.signal,headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
      const value=await response.json();if(!response.ok||!value.ok)throw new Error(value.message||"Výsledek smazání není potvrzený.");return value;
    } finally {clearTimeout(timer);}
  }
  function attach(host,row,{disabled=()=>false,onDeleted=()=>{}}={}) {
    const wrap=document.createElement("div"), button=document.createElement("button"), notice=document.createElement("span");
    wrap.className="calendar-delete";button.type="button";button.className="secondary calendar-delete-button";
    button.textContent="Smazat z kalendáře";button.setAttribute("aria-label","Smazat z kalendáře: "+row.title);
    notice.setAttribute("role","status");notice.setAttribute("aria-live","polite");wrap.append(button,notice);host.append(wrap);
    const event=Object.fromEntries(["calendar_id","title","start","end","all_day"].map(k=>[k,row[k]]));
    let pending=null, setup=false, deleted=false, uncertain=false;
    button.calendarDeleteUpdate=()=>{button.disabled=active||Boolean(window.SamanthaCalendarActions?.isBusy())||(!uncertain&&disabled())||deleted;};
    function apply(value) {
      notice.textContent=value.message||"";
      if(value.state==="deleted") {deleted=true;uncertain=false;button.textContent="Smazáno";try{onDeleted();}catch(error){/* known deletion stays final even if refresh fails */}}
      else if(["unknown","pending"].includes(value.state)) {uncertain=true;button.textContent="Ověřit původní smazání";}
      else if(["changed","blocked"].includes(value.state)) {deleted=true;button.textContent="Obnov přehled";}
    }
    button.addEventListener("click",async()=>{
      if(active||window.SamanthaCalendarActions?.isBusy()||(!uncertain&&disabled())||deleted)return;
      active=true;update(document);notice.textContent=setup?"Připravuji povolení na Macu…":"Ověřuji událost…";
      try {
        if(setup) {
          if(!window.confirm("Povolit na tomto Macu mazání jednotlivých potvrzených událostí? macOS si může vyžádat přístup ke kalendářům.")) {notice.textContent="Zrušeno.";return;}
          const value=await api({action:"authorize",confirmed:true});notice.textContent=value.message;setup=false;button.textContent="Smazat z kalendáře";return;
        }
        if(uncertain&&pending) {apply(await api({action:"recover",request_id:pending.request_id,confirmed:true}));return;}
        const value=await api({action:"prepare",event});
        if(wrap.isConnected===false)return;
        if(value.state==="setup_required") {setup=true;notice.textContent=value.message;button.textContent="Povolit mazání na Macu";return;}
        pending=value;
        if(value.state!=="prepared") {apply(value);return;}
        const when=value.event.all_day?new Intl.DateTimeFormat("cs-CZ",{timeZone:"UTC",dateStyle:"long"}).format(new Date(value.start_day?value.start_day+"T12:00:00Z":value.event.start))+" · celý den":date.format(new Date(value.event.start));
        if(!window.confirm(`Smazat z kalendáře „${value.calendar_title}“?\n\n${value.event.title}\n${when}\n\n${value.recurring?"Smaže se pouze tento výskyt. Ostatní opakování zůstanou.":"Smaže se tato událost."}`)) {pending=null;notice.textContent="Zrušeno. Událost zůstává v kalendáři.";return;}
        // Once POST may have started, only this identity's read-only recovery
        // is available, including after timeout. No second prepare/delete.
        uncertain=true;button.textContent="Ověřit původní smazání";
        apply(await api({action:"delete",request_id:pending.request_id,confirmed:true}));
      } catch(error) {
        notice.textContent=uncertain?"Výsledek není potvrzený. Ověř pouze původní smazání.":error.message;
      } finally {active=false;update(document);}
    });
    button.calendarDeleteUpdate();return wrap;
  }
  function update(root) {for(const button of root.querySelectorAll("button.calendar-delete-button"))button.calendarDeleteUpdate?.();}
  window.SamanthaCalendarDelete={attach,update};
})();
