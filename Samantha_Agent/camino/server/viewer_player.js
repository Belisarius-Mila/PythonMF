"use strict";
// Only server-proven adjacent checkpoint segments auto-advance. Never skip gaps.
const caminoAudioPlayers = Array.from(document.querySelectorAll("audio"));
for (const player of caminoAudioPlayers) {
  player.addEventListener("play", () => {
    for (const other of caminoAudioPlayers) if (other !== player) other.pause();
  });
  player.addEventListener("ended", async () => {
    const id = player.dataset.next;
    const next = id ? document.getElementById(id) : null;
    if (!next || !caminoAudioPlayers.includes(next)) return;
    try {
      next.currentTime = 0;
      await next.play();
    } catch {
      next.focus();
      const status = document.getElementById("audioPlaybackStatus");
      if (status) status.textContent = "Další úsek spusť tlačítkem přehrát. Prohlížeč automatické pokračování nepovolil nebo médium není dostupné.";
    }
  });
}
