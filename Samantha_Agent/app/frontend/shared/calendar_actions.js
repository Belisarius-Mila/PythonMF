(() => {
  const storageKey="samantha.calendarEdit.pending.v1";
  let active=false, pending=null;
  const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
  async function api(payload,path="/api/calendar/edit") {
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),payload.action==="authorize"?210000:35000);
    try {
      const response=await fetch(path,{method:"POST",cache:"no-store",signal:controller.signal,headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
      const value=await response.json();if(!response.ok||!value.ok)throw new Error(value.message||"Kalendář nyní není dostupný.");return value;
    } finally {clearTimeout(timer);}
  }
  function update(root=document) {for(const button of root.querySelectorAll("button.calendar-action-button"))button.calendarActionUpdate?.();window.SamanthaCalendarDelete?.update(root);}
  function remember(id) {
    const raw=JSON.stringify({request_id:id});window.localStorage.setItem(storageKey,raw);
    if(window.localStorage.getItem(storageKey)!==raw)throw new Error("Úpravu se nepodařilo uchovat. Neodesláno.");
    pending=id;
  }
  function forget() {pending=null;try{window.localStorage.removeItem(storageKey);}catch(error){/* server journal remains authoritative */}}
  function dialog(prepared,onChanged,notice) {
    const modal=el("dialog"),form=el("form"),fields=el("fieldset"),heading=el("h2","Editovat"),title=el("textarea");
    const label=(text,input)=>{const n=el("label",text);n.append(input);return n;};
    const option=(value,text)=>{const n=el("option",text);n.value=String(value);return n;};
    title.value=prepared.form.title;title.maxLength=400;title.required=true;title.rows=3;title.setAttribute("aria-label","Název úkolu nebo události");
    const year=el("select"),month=el("select"),day=el("select"),time=el("input"),dates=el("div");
    dates.className="calendar-edit-date";
    const [y,m,d]=prepared.form.date.split("-").map(Number),today=new Date().getFullYear(),pad=n=>String(n).padStart(2,"0");
    for(let n=Math.min(y,today);n<=Math.max(y,today)+10;n++)year.append(option(n,n));
    ["leden","únor","březen","duben","květen","červen","červenec","srpen","září","říjen","listopad","prosinec"].forEach((name,i)=>month.append(option(i+1,name)));
    year.value=String(y);month.value=String(m);
    function days(selected=Number(day.value)||1) {const count=new Date(Date.UTC(Number(year.value),Number(month.value),0)).getUTCDate();day.replaceChildren(...Array.from({length:count},(_,i)=>option(i+1,i+1)));day.value=String(Math.min(selected,count));}
    days(d);month.addEventListener("change",()=>days());year.addEventListener("change",()=>days());
    time.type="time";time.step="60";time.required=true;time.value=prepared.form.time;time.disabled=prepared.event.all_day;
    dates.append(label("Den",day),label("Měsíc",month),label("Rok",year));
    const save=el("button","Uložit změny"),cancel=el("button","Zrušit"),status=el("p");save.type="submit";cancel.type="button";
    status.setAttribute("role","status");status.setAttribute("aria-live","polite");
    fields.append(label("Název",title),dates,label(prepared.event.all_day?"Celý den":"Čas · Praha",time));
    form.append(heading,el("p","Kalendář: "+prepared.calendar_title),fields,
      el("p",prepared.recurring?"Upraví se pouze tento výskyt. Délka a ostatní údaje zůstanou zachované.":"Délka a ostatní údaje zůstanou zachované."),save,cancel,status);
    modal.append(form);modal.className="calendar-edit-dialog";document.body.append(modal);
    let sending=false;
    const close=()=>{if(!sending){modal.close();modal.remove();active=false;update();}};
    cancel.addEventListener("click",close);
    modal.addEventListener("cancel",event=>{event.preventDefault();close();});
    form.addEventListener("submit",async event=>{
      event.preventDefault();if(sending||!form.reportValidity())return;
      if(!title.value.trim()){status.textContent="Vyplň název.";return;}
      const changes={title:title.value,date:`${year.value}-${pad(month.value)}-${pad(day.value)}`,time:time.value};
      try {remember(prepared.request_id);}catch(error){status.textContent=error.message;return;}
      sending=true;let keepOpen=false,recoveryResult=null;fields.disabled=true;save.disabled=true;cancel.disabled=true;status.textContent="Ukládám změny…";
      try {
        const value=await api({action:"update",request_id:prepared.request_id,changes,confirmed:true});
        if(value.state==="prepared"&&value.validation_error) {
          forget();keepOpen=true;status.textContent=value.validation_error;
        } else if(value.state==="verified") {forget();notice.textContent=value.message;onChanged(value);}
        else if(["changed","blocked"].includes(value.state)) {forget();notice.textContent=value.message;}
        else {pending=value.request_id;recoveryResult=value;notice.textContent=value.message||"Výsledek není potvrzený. Zvol Ověřit původní úpravu.";}
      } catch(error) {notice.textContent="Výsledek není potvrzený. Zvol Ověřit původní úpravu.";}
      finally {
        sending=false;
        if(keepOpen){fields.disabled=false;time.disabled=prepared.event.all_day;save.disabled=false;cancel.disabled=false;}
        else {close();active=false;update();showRecovery(recoveryResult||{});}
      }
    });
    modal.addEventListener("close",()=>{if(!sending){active=false;update();}});
    modal.showModal();title.focus();
  }
  function attach(host,row,{disabled=()=>false,onChanged=()=>{},context=()=>null}={}) {
    const wrap=el("div"),notice=el("span");wrap.className="calendar-actions";notice.setAttribute("role","status");notice.setAttribute("aria-live","polite");
    if(row.can_complete) {
      const done=el("button","Splněno");done.type="button";done.className="secondary calendar-action-button";
      done.setAttribute("aria-label","Splněno: "+row.title);done.calendarActionUpdate=()=>{done.disabled=active||disabled();};
      done.addEventListener("click",async()=>{
        if(active||disabled())return;active=true;update();
        const current=context();
        try {
          const value=await api({action:"set_completed",key:row.key,completed:true,confirmed:true,
            expected_selection_revision:current.selection_revision??current.revision,expected_labels_revision:current.labels_revision},"/api/calendar/agenda");
          notice.textContent="Splněno. Položka zůstává v kalendáři.";onChanged(value);
        } catch(error) {notice.textContent=error.message;}
        finally {active=false;update();}
      });wrap.append(done);
    }
    if(row.can_edit) {
      const edit=el("button","Editovat");edit.type="button";edit.className="secondary calendar-action-button";edit.setAttribute("aria-label","Editovat: "+row.title);
      edit.calendarActionUpdate=()=>{edit.disabled=active||disabled();};let setup=false;
      edit.addEventListener("click",async()=>{
        if(active||disabled())return;active=true;update();let opened=false;
        try {
          if(setup) {
            if(!window.confirm("Povolit na tomto Macu úpravy jednotlivých potvrzených událostí? macOS si může vyžádat přístup ke kalendářům."))return;
            notice.textContent=(await api({action:"authorize",confirmed:true})).message;setup=false;edit.textContent="Editovat";return;
          }
          const event=Object.fromEntries(["calendar_id","title","start","end","all_day"].map(k=>[k,row[k]]));
          const value=await api({action:"prepare",event});
          if(wrap.isConnected===false)return;
          if(value.state==="setup_required") {setup=true;edit.textContent="Povolit úpravy na Macu";notice.textContent=value.message;}
          else if(value.state==="prepared") {dialog(value,onChanged,notice);opened=true;}
          else {pending=value.request_id;notice.textContent=value.message;showRecovery(value);}
        } catch(error) {notice.textContent=error.message;}
        finally {if(!opened){active=false;update();}}
      });wrap.append(edit);
    }
    wrap.append(notice);host.append(wrap);update();return wrap;
  }
  let recovery=null,recoveryNeedsAuthorization=false;
  function showRecovery(value={}) {
    if(!pending)return;
    if(typeof value.needs_authorization==="boolean")recoveryNeedsAuthorization=value.needs_authorization;
    if(!recovery) {
      recovery=el("div");recovery.className="calendar-actions calendar-edit-recovery";
      const button=el("button","Ověřit původní úpravu"),notice=el("span");button.type="button";notice.setAttribute("role","status");recovery.append(button,notice);document.body.append(recovery);
      button.addEventListener("click",async()=>{
        if(active||!pending)return;
        if(recoveryNeedsAuthorization&&!window.confirm("Povolit opravenému kalendářovému helperu přístup na tomto Macu? macOS může zobrazit systémový dialog."))return;
        active=true;button.disabled=true;update();
        try {
          if(recoveryNeedsAuthorization){
            const value=await api({action:"authorize",confirmed:true});notice.textContent=value.message;
            recoveryNeedsAuthorization=false;return;
          }
          const value=await api({action:"recover",request_id:pending,confirmed:true});notice.textContent=value.message;
          recoveryNeedsAuthorization=value.needs_authorization===true;
          if(["verified","changed","blocked","prepared"].includes(value.state)) {forget();button.disabled=true;recovery.hidden=true;window.dispatchEvent(new Event("calendarChanged"));}
        } catch(error) {notice.textContent="Původní úpravu zatím nelze ověřit.";}
        finally {active=false;button.disabled=!pending;button.textContent=recoveryNeedsAuthorization?"Povolit přístup na Macu":"Ověřit původní úpravu";update();}
      });
    }
    recovery.hidden=false;recovery.children[0].disabled=false;recovery.children[0].textContent=recoveryNeedsAuthorization?"Povolit přístup na Macu":"Ověřit původní úpravu";
    recovery.children[1].textContent=value.message||(recoveryNeedsAuthorization?"Pro ověření původní úpravy povol přístup ke kalendářům na Macu.":"Kalendář čeká na ověření původní úpravy. Zápis znovu neposílej.");
  }
  window.SamanthaCalendarActions={attach,update,isBusy:()=>active};
  // Both browser receipt and server journal survive navigation/restart. No
  // mutation is replayed on startup or after a network timeout.
  try {const saved=JSON.parse(window.localStorage.getItem(storageKey)||"null");if(saved&&/^[a-f0-9]{32}$/.test(saved.request_id))pending=saved.request_id;}catch(error){/* server check below */}
  api({action:"current"}).then(value=>{if(value.request_id)pending=value.request_id;showRecovery(value);}).catch(()=>showRecovery());
})();
