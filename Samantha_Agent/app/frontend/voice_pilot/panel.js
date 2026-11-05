/* Only an explicitly installed authenticated broker can mount the live panel.
 * Loading this file alone never requests a microphone or creates a session.
 */
window.mountSamanthaVoicePilot=function(broker,options) {
  "use strict";
  options=options || {};
  const byId=id=>document.getElementById(id);
  const start=byId("start"), stop=byId("stop"), mute=byId("mute");
  if(start.dataset.mounted) throw new Error("Hlasový panel je již připojený.");
  start.dataset.mounted="true";
  const transcript={input:"",output:""};
  const consent=byId("consent");
  const allowed=()=>!options.requireConsent || consent.checked;
  const conversation=new window.SamanthaVoiceConversation({
    broker,maxSeconds:options.maxSeconds || 300,mediaDevices:navigator.mediaDevices,PeerConnection:window.RTCPeerConnection,audio:byId("audio"),
    onState(state) {
      byId("status").textContent=state.message;
      if(typeof options.onState==="function") options.onState(state);
      start.disabled=state.state!=="idle" || !allowed();
      stop.disabled=!["connecting","active"].includes(state.state);
      mute.disabled=state.state!=="active";
      mute.textContent=state.muted ? "Zapnout hlas" : "Ztišit hlas";
      byId("usage").textContent=`Hlas: ${state.seconds} s. ${state.finalUsage ? "Konečná spotřeba potvrzená." : "Konečná spotřeba zatím není potvrzená."}`;
    },
    onEvent(event) {
      const side=event.type==="session.input_transcript.delta" ? "input" : "output";
      transcript[side]=(transcript[side]+event.delta).slice(-12000);
      byId(side).textContent=transcript[side]; // Transcript is never HTML or a command.
    },
  });
  start.addEventListener("click",()=>{if(allowed()) conversation.start();});
  if(options.requireConsent) consent.addEventListener("change",()=>{start.disabled=conversation.state!=="idle" || !allowed();});
  stop.addEventListener("click",()=>conversation.stop());
  mute.addEventListener("click",()=>conversation.muteOutput(!conversation.muted));
  window.addEventListener("pagehide",()=>conversation.dispose());
  return conversation;
};

window.makeSamanthaVoiceCandidateBroker=function(csrfToken,confirmation) {
  "use strict";
  if(typeof csrfToken!=="string" || csrfToken.length<24) throw new Error("Chybí serverové oprávnění pilotu.");
  let attempted=false;
  async function post(path,body) {
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),15000);
    try {
      const result=await fetch(path,{method:"POST",credentials:"same-origin",cache:"no-store",
        signal:controller.signal,keepalive:path.endsWith("/close"),
        headers:{"Content-Type":"application/json","X-Voice-CSRF":csrfToken},body:JSON.stringify(body)});
      if(!result.ok) throw new Error("Hlasové spojení není potvrzené; požadavek neopakuj.");
      return await result.json();
    } finally {clearTimeout(timer);}
  }
  return {
    create({sdp}) {
      if(attempted) return Promise.reject(new Error("Tento pokus už byl odeslán; další relaci nevytvářím."));
      attempted=true;
      return post("/api/human-adam/voice-candidate/session",confirmation ? {sdp,confirmation} : {sdp});
    },
    renew() {return post("/api/human-adam/voice-candidate/new",{confirmation});},
    abandon(session_id) {return post("/api/human-adam/voice-candidate/close",{session_id});},
  };
};
