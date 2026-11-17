(function(root){
  'use strict';
  const KEY='samantha-shared-chat-client';
  function uuid(crypto){const bytes=new Uint8Array(16);crypto.getRandomValues(bytes);return Array.from(bytes,v=>v.toString(16).padStart(2,'0')).join('');}
  function cached(storage,key){try{const value=JSON.parse(storage.getItem(key)||'null');return value&&typeof value==='object'&&!Array.isArray(value)?value:null;}catch(_){return null;}}
  class Client {
    constructor({fetch,storage,tabStorage,crypto,render=()=>{},setTimer=(fn,delay)=>root.setTimeout(fn,delay),clearTimer=id=>root.clearTimeout(id)}){
      Object.assign(this,{fetch,storage,tabStorage,crypto,render,setTimer,clearTimer});
      this.editor=tabStorage.getItem('samantha-chat-editor')||uuid(crypto);tabStorage.setItem('samantha-chat-editor',this.editor);
      this.token=storage.getItem(KEY)||'';this.state=null;this.online=false;this.text='';this.dirty=false;this.editVersion=0;this.epoch=0;this.busy=false;this.claiming=false;this.error='';this.chain=Promise.resolve();this.timer=null;
      this.pending=cached(tabStorage,'samantha-chat-pending');
      this.recovery=cached(tabStorage,'samantha-chat-draft');
    }
    notify(){this.render(this);}
    async api(payload){
      const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000);
      try{
        let response;
        try{response=await this.fetch(payload?'/api/samantha-chat/action':'/api/samantha-chat/state',payload?{
          method:'POST',signal:controller.signal,headers:{'Content-Type':'application/json'},body:JSON.stringify({...payload,editor_id:this.editor,...(this.token?{client_token:this.token}:{})})
        }:{signal:controller.signal,headers:{'X-Samantha-Client':this.token,'X-Samantha-Editor':this.editor}});}
        catch(_){const error=new Error('Spojení s Cockpitem není ověřené. Zachovej text a obnov stav původní zprávy.');error.connectionUnknown=true;throw error;}
        const data=await response.json();if(!response.ok||!data.ok)throw new Error(data.message||'Stav rozhovoru není ověřený.');return data;
      }finally{clearTimeout(timer);}
    }
    apply(data){
      if(data.needs_setup)return;
      if(this.state && data.room_id===this.state.room_id && data.draft.revision<this.state.draft.revision)return;
      this.state=data;this.online=true;
      if(this.pending && this.pending.room_id!==data.room_id)this.pending=null;
      if(!this.dirty)this.text=data.draft.text;
      if(this.recovery && this.recovery.room_id===data.room_id && this.recovery.text===data.draft.text){this.recovery=null;this.tabStorage.removeItem('samantha-chat-draft');}
      if(this.pending && this.pending.room_id===data.room_id && (data.submission?.client_message_id===this.pending.client_message_id||data.messages.some(m=>m.client_message_id===this.pending.client_message_id))){
        this.pending=null;this.tabStorage.removeItem('samantha-chat-pending');
      }
    }
    async refresh(){
      if(!this.token){this.notify();return;}
      const epoch=this.epoch;
      try{const data=await this.api();if(epoch!==this.epoch||this.busy)return;this.apply(data);this.error='';}
      catch(error){if(epoch!==this.epoch||this.busy)return;this.error=error.message;this.online=false;}
      this.notify();
    }
    enqueue(fn){
      const work=async()=>{this.busy=true;this.epoch++;this.notify();try{return await fn();}catch(error){this.error=error.message;if(error.connectionUnknown)this.online=false;throw error;}finally{this.busy=false;this.notify();}};
      const promise=this.chain.then(work,work);this.chain=promise.catch(()=>{});return promise;
    }
    async setup(action,name,code){
      const key='samantha-chat-setup-'+action;let request=cached(this.tabStorage,key);
      if(!request||request.name!==name||request.code!==code){request={action,name,request_id:uuid(this.crypto),...(code===undefined?{}:{code})};this.tabStorage.setItem(key,JSON.stringify(request));}
      return this.enqueue(async()=>{const data=await this.api(request);this.token=data.client_token;this.storage.setItem(KEY,this.token);this.tabStorage.removeItem(key);this.apply(data);this.error='';});
    }
    async pair(){return this.enqueue(async()=>{this.apply(await this.api({action:'pair'}));this.error='';});}
    async claim(){
      this.claiming=true;
      try{return await this.enqueue(async()=>{const data=await this.api({action:'claim',expected_revision:this.state.draft.revision,takeover:true});this.apply(data);this.error='';});}
      finally{this.claiming=false;this.notify();}
    }
    setText(text){
      if(!this.state||(!this.state.draft.can_edit&&!this.claiming))return;
      this.text=text;this.dirty=true;this.editVersion++;
      this.recovery={room_id:this.state.room_id,text};this.tabStorage.setItem('samantha-chat-draft',JSON.stringify(this.recovery));
      this.clearTimer(this.timer);this.timer=this.setTimer(()=>{void this.flush().catch(()=>{});},350);this.notify();
    }
    async flush(){
      this.clearTimer(this.timer);
      return this.enqueue(async()=>{
        if(!this.dirty)return;
        const version=this.editVersion,text=this.text;
        const data=await this.api({action:'draft',text,expected_revision:this.state.draft.revision});
        if(version===this.editVersion)this.dirty=false;
        this.apply(data);this.error='';
      });
    }
    async send(){
      await this.flush();
      return this.enqueue(async()=>{
        if(this.dirty)throw new Error('Nejprve dokonči přenos rozepsaného textu.');
        let request=this.pending;
        if(!request){request={action:'send',room_id:this.state.room_id,expected_revision:this.state.draft.revision,client_message_id:this.state.draft.client_message_id};this.tabStorage.setItem('samantha-chat-pending',JSON.stringify(request));this.pending=request;}
        if(request.room_id!==this.state.room_id)throw new Error('Předchozí zpráva patří jinému rozhovoru.');
        const {room_id,...payload}=request;void room_id;
        this.apply(await this.api(payload));this.error='';
      });
    }
    async restore(){const value=this.recovery?.text;if(value===undefined)return;await this.claim();this.setText(value);await this.flush();}
    disconnect(){this.storage.removeItem(KEY);this.epoch++;this.clearTimer(this.timer);this.token='';this.state=null;this.online=false;this.pending=null;this.text='';this.dirty=false;this.error='';this.notify();}
  }
  function attach(doc){
    const el=id=>doc.getElementById(id);let fingerprint='';
    const client=new Client({fetch:root.fetch.bind(root),storage:root.localStorage,tabStorage:root.sessionStorage,crypto:root.crypto,render(c){
      el('setup').hidden=Boolean(c.token);el('chat').hidden=!c.state;
      el('connection').textContent=c.state?`${c.online?'Připojeno':'Spojení není ověřené'}: ${c.state.name} · ${c.state.client_label}`:c.token?'Obnovuji připojení…':'Vyber rozhovor nebo připoj telefon.';
      el('status').textContent=c.error;
      el('draftStatus').textContent=!c.state?'':c.dirty?'Rozepsaný text zatím není přenesený na druhé zařízení.':c.state.draft.text?'Rozepsaný text je uložený pro obě zařízení.':c.state.draft.can_edit?'Můžeš psát nebo diktovat. Text se přenáší automaticky.':'Pro psaní na tomto zařízení stiskni „Psát / diktovat zde“.';
      el('disconnect').hidden=!c.token;el('disconnect').disabled=c.busy;
      if(!c.state)return;
      el('pairPanel').hidden=!c.state.host;el('pairCode').textContent=c.state.pair_code||'';
      const draft=c.state.draft;
      el('input').readOnly=!draft.can_edit&&!c.claiming;
      if(el('input').value!==c.text)el('input').value=c.text;
      el('claim').disabled=c.busy||!c.online;el('send').disabled=c.busy||!c.online||(!c.pending&&(c.state.busy||(!c.text.trim()&&!c.dirty)));
      el('send').textContent=c.pending?'Ověřit odeslání':'Odeslat';
      const status=c.state.submission?.status;
      el('work').textContent=status==='pending'?'Samantha odpovídá…':status==='delivery_unknown'?'Dokončení předchozí zprávy není ověřené. Obnov stav; novou kopii neodesílej.':status==='not_sent'?'Zpráva nebyla odeslaná. Text je zachovaný; můžeš ji odeslat znovu.':'';
      el('recovery').hidden=!c.recovery||c.recovery.room_id!==c.state.room_id||c.recovery.text===draft.text;
      el('recoveryText').textContent=c.recovery?.text||'';
      const next=JSON.stringify(c.state.messages);
      if(next!==fingerprint){
        const log=el('messages'),bottom=log.scrollHeight-log.scrollTop-log.clientHeight<80;
        log.replaceChildren();
        for(const message of c.state.messages){
          for(const [kind,title,text] of [['user','Ty',message.user_text],['assistant','Samantha',message.answer]]){
            if(!text)continue;const node=doc.createElement('div');node.className='message '+kind;
            const who=doc.createElement('strong');who.textContent=title;node.appendChild(who);node.appendChild(doc.createTextNode(text));log.appendChild(node);
          }
        }
        fingerprint=next;if(bottom)log.scrollTop=log.scrollHeight;
      }
    }});
    function act(fn){void Promise.resolve().then(fn).catch(error=>{client.error=error.message;client.notify();});}
    el('create').onclick=()=>act(()=>client.setup('create',el('name').value));
    el('join').onclick=()=>act(()=>client.setup('join','iPhone',el('code').value.trim()));
    el('pair').onclick=()=>act(()=>client.pair());
    el('claim').onclick=()=>{el('input').readOnly=false;el('input').focus();act(()=>client.claim());};
    el('input').addEventListener('input',event=>{try{client.setText(event.target.value);}catch(_){client.error='Text se nepodařilo místně zachovat. Nezavírej okno; text můžeš zkopírovat.';client.notify();}});
    el('input').addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&event.key==='Enter'&&!event.isComposing&&!el('send').disabled){event.preventDefault();act(()=>client.send());}});
    el('send').onclick=()=>act(()=>client.send());el('refresh').onclick=()=>act(()=>client.refresh());
    el('recover').onclick=()=>act(()=>client.restore());el('disconnect').onclick=()=>client.disconnect();
    async function poll(){await client.refresh();root.setTimeout(poll,2000);}
    doc.addEventListener('visibilitychange',()=>{if(!doc.hidden)void client.refresh();});
    root.addEventListener('online',()=>{void client.refresh();});
    void poll();return client;
  }
  if(typeof module!=='undefined'&&module.exports)module.exports={Client};
  if(root.document)attach(root.document);
})(typeof window==='undefined'?globalThis:window);
