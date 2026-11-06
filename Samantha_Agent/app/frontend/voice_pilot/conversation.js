/* 15/P2-A: transport controller. No URL, credential, fetch or automatic start.
 * A future authenticated server broker owns creation, sideband, role and expiry.
 * The only frontend command is session.close; backend tasks are never touched.
 */
(function(root) {
  "use strict";
  class VoiceConversation {
    constructor({broker, mediaDevices, PeerConnection, audio, onState=()=>{}, onEvent=()=>{},
                 setTimer=setTimeout, clearTimer=clearTimeout, maxSeconds=300}) {
      this.broker=broker;
      this.mediaDevices=mediaDevices;
      this.PeerConnection=PeerConnection;
      this.audio=audio;
      this.onState=onState;
      this.onEvent=onEvent;
      this.setTimer=setTimer;
      this.clearTimer=clearTimer;
      if (!Number.isInteger(maxSeconds) || maxSeconds<15 || maxSeconds>600) throw new Error("Neplatná délka pilotu.");
      this.maxSeconds=maxSeconds;
      this.state="idle";
      this.generation=0;
      this.microphone=null;
      this.peer=null;
      this.channel=null;
      this.sessionId=null;
      this.creationAttempted=false;
      this.finalUsage=false;
      this.seconds=0;
      this.muted=false;
      this.seen=new Set();
      this.timers=[];
      this.notify("Mikrofon je vypnutý.");
    }
    notify(message) {
      this.onState({state:this.state,message,microphone:Boolean(this.microphone),
        muted:this.muted,seconds:this.seconds,finalUsage:this.finalUsage});
    }
    timer(action, delay) {
      const id=this.setTimer(action,delay);
      this.timers.push(id);
      return id;
    }
    releaseMicrophone() {
      if (this.microphone) this.microphone.getTracks().forEach(track=>track.stop());
      this.microphone=null;
    }
    cleanup() {
      this.generation++;
      this.timers.forEach(id=>this.clearTimer(id));
      this.timers=[];
      this.releaseMicrophone();
      const channel=this.channel;
      this.channel=null;
      if(channel) channel.close();
      if(this.peer) this.peer.close();
      this.peer=null;
      this.audio.pause();
      this.audio.srcObject=null;
    }
    abandon(id) {
      // One cleanup attempt; never create another session on uncertainty.
      Promise.resolve().then(()=>this.broker.abandon(id)).catch(()=>{});
    }
    fail(message) {
      if(this.state==="closed" || this.state==="disconnected") return;
      if(this.sessionId) this.abandon(this.sessionId);
      this.state="disconnected";
      this.finalUsage=false;
      this.cleanup();
      this.notify(message);
    }
    async start() {
      if(this.state!=="idle") return; // Explicit new instance needed after any attempt.
      if(!this.broker || typeof this.broker.create!=="function" || typeof this.broker.abandon!=="function") {
        this.notify("Živý pilot zatím není aktivovaný. Mikrofon zůstává vypnutý.");
        return;
      }
      if(!this.mediaDevices || !this.PeerConnection) {
        this.notify("Prohlížeč nepodporuje hlasové spojení. Použij textový Human–Adam.");
        return;
      }
      const generation=++this.generation;
      const current=()=>generation===this.generation;
      this.state="connecting";
      let awaitingMicrophone=true;
      this.notify("Čekám na oprávnění mikrofonu. Povol mikrofon v žádosti Chromu nebo Safari. Pokud se žádost neukáže, ukonči čekání a zkontroluj Nastavení → Aplikace → Chrome → Mikrofon.");
      this.timer(()=>this.fail(awaitingMicrophone
        ? "Přístup k mikrofonu nebyl potvrzený. Zkontroluj oprávnění Chromu nebo Safari a této stránky. Hlasová relace nebyla vytvořena. Pozdější povolení tento pokus nespustí."
        : "Spojení překročilo časový limit; automaticky je neopakuji."),20000);
      try {
        const stream=await this.mediaDevices.getUserMedia({audio:{echoCancellation:true,noiseSuppression:true}});
        awaitingMicrophone=false;
        if(!current()) { stream.getTracks().forEach(track=>track.stop()); return; }
        this.microphone=stream;
        this.notify("Mikrofon je zapnutý; připojuji rozhovor…");
        const peer=new this.PeerConnection();
        this.peer=peer;
        peer.addEventListener("track",event=>{
          if(!current() || !["connecting","active"].includes(this.state)) return;
          this.audio.srcObject=event.streams[0];
          Promise.resolve(this.audio.play()).catch(()=>{
            if(current()) this.notify("Stiskni přehrávání, aby byl hlas slyšet. Mikrofon je zapnutý.");
          });
        });
        peer.addEventListener("connectionstatechange",()=>{
          if(current() && ["failed","disconnected","closed"].includes(peer.connectionState)) {
            this.fail("Hlasové spojení se přerušilo. Práce Adama běží nezávisle; zkontroluj textový stav.");
          }
        });
        stream.getAudioTracks().forEach(track=>peer.addTrack(track,stream));
        const channel=peer.createDataChannel("oai-events");
        this.channel=channel;
        channel.addEventListener("message",({data})=>{
          if(!current()) return;
          try {
            if(typeof data!=="string" || data.length>65536) throw new Error("Invalid event");
            this.receive(JSON.parse(data));
          } catch(_error) {
            this.fail("Událost hlasu se nepodařilo ověřit. Mikrofon je vypnutý; nic neopakuji.");
          }
        });
        channel.addEventListener("close",()=>{
          if(current() && this.state!=="closed") this.fail("Hlas skončil bez potvrzené konečné spotřeby.");
        });
        const offer=await peer.createOffer();
        if(!current()) return;
        await peer.setLocalDescription(offer);
        if(!current()) return;
        if(peer.iceGatheringState!=="complete") {
          await new Promise((resolve,reject)=>{
            const onState=()=>{
              if(!current() || peer.iceGatheringState==="complete") {
                peer.removeEventListener("icegatheringstatechange",onState);
                resolve();
              }
            };
            this.timer(()=>{peer.removeEventListener("icegatheringstatechange",onState);reject(new Error("ICE timeout"));},10000);
            peer.addEventListener("icegatheringstatechange",onState);
            onState();
          });
        }
        if(!current()) return;
        const sdp=peer.localDescription && peer.localDescription.sdp;
        if(typeof sdp!=="string" || !sdp.startsWith("v=0") || sdp.length>60000) throw new Error("SDP required");
        this.creationAttempted=true;
        const result=await this.broker.create({sdp}); // Exactly one attempt; trusted server builds config.
        const id=result && result.session && result.session.id;
        if(!current()) {if(typeof id==="string" && id) this.abandon(id); return;}
        if(typeof id==="string" && id) this.sessionId=id;
        if(!this.sessionId || !result.transport || typeof result.transport.sdp!=="string") throw new Error("Invalid answer");
        await peer.setRemoteDescription({type:"answer",sdp:result.transport.sdp});
        // HTTP creation starts the session. NEVER send session.start here.
      } catch(_error) {
        if(current()) {
          const microphoneErrors={
            NotAllowedError:"Přístup k mikrofonu nebyl povolený. Na iPhonu ověř Nastavení → Aplikace → Chrome → Mikrofon a oprávnění této HTTPS stránky. Hlasová relace nebyla vytvořena.",
            SecurityError:"Prohlížeč přístup k mikrofonu zablokoval. Ověř oprávnění prohlížeče a této HTTPS stránky. Hlasová relace nebyla vytvořena.",
            NotFoundError:"Prohlížeč nenašel mikrofon. Ověř zvukový vstup zařízení. Hlasová relace nebyla vytvořena.",
            NotReadableError:"Mikrofon se nepodařilo otevřít. Ověř, zda jej nepoužívá hovor nebo jiná aplikace. Hlasová relace nebyla vytvořena.",
          };
          const message=this.creationAttempted
            ? "Výsledek vytvoření hlasového spojení je nejistý. Nové spojení automaticky nevytvářím."
            : awaitingMicrophone
              ? (Object.prototype.hasOwnProperty.call(microphoneErrors,_error?.name) ? microphoneErrors[_error.name]
                : "Mikrofon se nepodařilo otevřít. Ověř oprávnění a zvukový vstup zařízení. Hlasová relace nebyla vytvořena.")
              : "Hlasové spojení se nepodařilo spustit. Použij textový Human–Adam.";
          this.fail(message);
        }
      }
    }
    receive(event) {
      if(!event || typeof event!=="object" || typeof event.event_id!=="string" || !event.event_id || event.event_id.length>200) throw new Error("Event ID required");
      if(this.seen.has(event.event_id) || ["closed","disconnected"].includes(this.state)) return;
      if(this.seen.size>=4096 && !["session.usage.updated","session.closed"].includes(event.type)) {this.stop();return;}
      if(this.seen.size<4096) this.seen.add(event.event_id);
      if(event.type==="session.started") {
        if(!event.session || event.session.id!==this.sessionId) throw new Error("Session mismatch");
        if(this.state!=="connecting") return;
        this.timers.forEach(id=>this.clearTimer(id));
        this.timers=[];
        this.state="active";
        this.timer(()=>this.stop(),this.maxSeconds*1000);
        this.notify("Rozhovor běží. Mikrofon je zapnutý. Toto je čtecí AI hlas.");
      } else if(event.type==="session.usage.updated" || event.type==="session.closed") {
        const seconds=event.usage && event.usage.seconds;
        const valid=typeof seconds==="number" && Number.isFinite(seconds) && seconds>=this.seconds;
        if(valid) this.seconds=seconds;
        if(event.type==="session.closed") {
          this.finalUsage=valid;
          this.state="closed";
          this.cleanup();
          this.notify(valid ? "Rozhovor skončil. Mikrofon je vypnutý; spotřeba potvrzená." : "Rozhovor skončil. Konečná spotřeba není potvrzená.");
        } else this.notify(this.state==="active" ? "Rozhovor běží. Mikrofon je zapnutý." : "Dokončuji rozhovor; mikrofon je vypnutý.");
      } else if(event.type==="error") this.stop();
      // Transcripts are display data only, never a send or confirmation command.
      if(["session.input_transcript.delta","session.output_transcript.delta"].includes(event.type)) {
        if(typeof event.delta!=="string" || event.delta.length>4096) throw new Error("Invalid transcript");
        this.onEvent(event);
      }
    }
    muteOutput(muted=true) {
      if(this.state!=="active" || !this.microphone) return;
      this.muted=Boolean(muted);
      this.audio.muted=this.muted; // Cuts playback only; microphone and backend remain independent.
      this.notify(this.muted ? "Hlas je ztišený. Mikrofon zůstává zapnutý." : "Hlas je zapnutý.");
    }
    stop() {
      if(["idle","closing","closed","disconnected"].includes(this.state)) return;
      if(this.state==="connecting") {
        this.fail("Připojování ukončeno. Mikrofon je vypnutý; případné vytvoření spojení ověří server.");
        return;
      }
      this.state="closing";
      this.releaseMicrophone();
      this.audio.muted=true;
      this.audio.pause(); // Stop audible speech immediately; drain only the event transport.
      this.notify("Mikrofon je vypnutý. Čekám na konečnou spotřebu; úlohy Adama pokračují.");
      try {
        if(!this.channel || this.channel.readyState!=="open") throw new Error("Channel closed");
        this.channel.send(JSON.stringify({type:"session.close"}));
        this.timer(()=>this.fail("Rozhovor nemá potvrzené ukončení ani konečnou spotřebu."),10000);
      } catch(_error) {this.fail("Ukončení hlasu není potvrzené; server musí ověřit spotřebu.");}
    }
    dispose() {if(!["idle","closed","disconnected"].includes(this.state)) this.fail("Stránka byla opuštěna. Mikrofon je vypnutý.");else this.cleanup();}
  }
  root.SamanthaVoiceConversation=VoiceConversation;
  if(typeof module!=="undefined" && module.exports) module.exports={VoiceConversation};
})(typeof globalThis!=="undefined" ? globalThis : window);
