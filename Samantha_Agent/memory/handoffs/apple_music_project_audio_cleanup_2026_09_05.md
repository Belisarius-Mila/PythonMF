Nazev: Projektové audio mimo Apple Music
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-09-05

Co se resilo:
- Pracovní audio znečišťovalo hudební knihovnu. Starší oprava Edge TTS sama
  nezabránila importům při dvojkliku nebo obecném otevření audio souboru.

Co je hotove:
- Po přesném potvrzení globální brzdy odstraněno 144 předem vybraných záznamů
  přes persistent ID. Knihovna klesla z 1169 na 1025 záznamů; množina ostatních
  ID i obsah vlastních playlistů zůstaly shodné.
- Všech 37 místních souborů Music zůstalo na disku. Projektové zdroje mají
  nezměněné kontrolní součty. Šestnáct nejasných nahrávek nebylo vybráno.
- Soukromá obnovovací kopie má 117 unikátních audio souborů, 5 159 732 bajtů.
  Pro 37 místních záznamů jde o přesné kopie; pro dalších 107 o dohledané
  projektové zdroje podle názvu, nikoli prokázaně totožné historické importy.
- MP3, M4A, AIFF a WAV mají výchozí QuickTime Player. Ověřeno také přes
  NSWorkspace pro konkrétní soubory, bez jejich importu nebo přehrávání.
- M4A vyžadovalo skutečný typ `com.apple.m4a-audio`; samotné nastavení
  `public.mpeg-4-audio` nepokrývalo otevření konkrétního M4A.
- Osm existujících testů Edge TTS a F5-TTS přehrávání prošlo. Generátory už
  používají `afplay`; produkční kód ani umístění projektových assetů se neměnily.
- AGENTS.md zakazuje obecné macOS `open` nad projektovým audiem.

Co neni hotove:
- Zobrazení a synchronizace na iPhonu nebyly z tohoto Macu ověřeny.

Dalsi krok:
- Běžný poslech přes QuickTime, `afplay` nebo prohlížeč. Případný nesoulad
  na iPhonu nejdřív diagnostikovat, znovu nemaž automaticky další záznamy.

Navrhovane dalsi kroky:
- Žádná další infrastruktura není potřeba. Při návratu problému ověřit
  skutečnou asociaci souboru a nové záznamy Music podle persistent ID.

Zmenene nebo relevantni soubory:
- AGENTS.md; memory/projects/tts_edge_audio_tools.md; memory/LESSONS_LEARNED.md.
- Soukromé důkazy: data/private/music_cleanup/2026-09-05_apple_music/
  obsahuje manifest.json, execution.jsonl, library_before.json,
  library_after.json, prehled_uklidu.md, provest_uklid.py a audio/.

Bezpecnost / neukladat:
- Názvy osobních nahrávek, playlisty, katalog, audio a konkrétní ID nepatří do
  Gitu. Soukromý jednorázový skript není obecná schopnost pro další mazání.
- Tato autorizace platila jen pro odsouhlasených 144 záznamů a čtyři formáty;
  není trvalým souhlasem k dalšímu mazání ani změnám systémových asociací.
