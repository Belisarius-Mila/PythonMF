/* Only an explicitly installed authenticated broker can mount the live panel.
 * Loading this file alone never requests a microphone or creates a session.
 */
window.mountSamanthaVoicePilot=function(broker) {
  "use strict";
  const byId=id=>document.getElementById(id);
  const start=byId("start"), stop=byId("stop"), mute=byId("mute");
  if(start.dataset.mounted) throw new Error("Hlasový panel je již připojený.");
  start.dataset.mounted="true";
  const transcript={input:"",output:""};
  const conversation=new window.SamanthaVoiceConversation({
    broker,mediaDevices:navigator.mediaDevices,PeerConnection:window.RTCPeerConnection,audio:byId("audio"),
    onState(state) {
      byId("status").textContent=state.message;
      start.disabled=state.state!=="idle";
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
  start.addEventListener("click",()=>conversation.start());
  stop.addEventListener("click",()=>conversation.stop());
  mute.addEventListener("click",()=>conversation.muteOutput(!conversation.muted));
  window.addEventListener("pagehide",()=>conversation.dispose());
  return conversation;
};
