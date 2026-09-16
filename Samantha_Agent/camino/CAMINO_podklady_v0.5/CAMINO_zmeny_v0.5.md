# Camino — změny v0.5

**Datum:** 16. září 2026

## Potvrzený nový požadavek

Během pouti má Jana z vlastního MacBooku nebo iPhonu přes soukromý Tailscale přístup k automaticky aktualizovanému read-only **Camino Vieweru**. Viewer ukazuje povolené fotografie, video proxy, text komentářů/úvah a původní povolené audio. `Jen pro mě` je z Vieweru vyloučeno už na úrovni zdrojové projekce. Domácí MacBook má po dobu cesty fungovat jako server; stávající Cockpit je rozcestník/health panel, nikoli jediná cesta k Vieweru.

## Dopad na prioritu

- Camino Viewer se přesouvá do **P0 před cestou**.
- P1 zůstává jen jednorázové systémové sdílení dalším členům rodiny.
- Film a trasa zůstávají P2 po návratu.
- Release cíl P0 je nejpozději **2. října 2026**.

## Nová pravidla

- U12–U14: Viewer, automatická aktualizace, server/Cockpit.
- D11–D16: oddělená Viewer služba, deriváty, plán regenerace, Tailscale-only, sanitizace metadat, atomická publikace.
- F74–F86: viewer-safe projekce, HTML/timeline, média, audio/text, rebuild, stav, autorizace, invalidace, launchd, Cockpit a vzdálený test.
- T081–T095: soukromí Vieweru, Safari Mac/iPhone, metadata, video seek, audio, pending stavy, rebuild, výpadky, restart, Cockpit, tailnet a generální vzdálená zkouška.
- C08c–C08f: samostatné vývojové kroky Vieweru.
- C00 rozšířen o read-only audit Tailscale/Serve, napájení/uspávání, launchd, Cockpitu a Viewer readiness.

## Co se nemění

Originály jsou neměnné, jeden hlavní iPhone zůstává jediným editorem, `Jen pro mě` smí AI zpracovat pro osobní deník, ale nesmí do rodinných/filmových výstupů. Viewer není veřejný web a nepoužívá Tailscale Funnel.
