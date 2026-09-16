# C01b — audio pod zámkem a vědomé pokračování

Zahájeno výslovným pokynem Míly 2026-09-15 po přijetí C01a.
**Stav: C01b 0.2.0 (2) přijato v prototypovém rozsahu; krátký test zámku a T016/T018–T021/T024/T059 PASS v dosavadním rozsahu. T059 prošel po řízeném zopakování.**
Aktuální výsledky určuje [report C01b](../docs/C01b_BACKGROUND_AUDIO_REPORT.md).

## Rozsah

- Již spuštěné a ověřeně běžící audio pokračuje po zámku / přechodu do pozadí.
- Nový Start a Pokračovat vyžadují aktivní odemčenou aplikaci; žádné Siri,
  vzdálené povely, automatický restart či ovládání libovolnými sluchátky.
- Hovor, zastavení média či změna skutečného vstupu pozastaví recorder ihned,
  následně se pokusí uzavřít a ověřit dostupnou část. Neověřený soubor se zachová.
- Přerušeno nabízí Pokračovat a Ukončit. Pokračovat vytvoří samostatný soubor
  téže session s odkazem na předchozí část; původní soubor se nepřepisuje.
- Pauza je změřený interval od zaznamenané události přerušení do vědomého
  pokračování, nikoli přesný počet chybějících zvukových vzorků. Neznámý čas je null.
- Nové soubory mají completeUntilFirstUserAuthentication. Ochrana původních
  nahrávek z C01a se nemění, žádná migrace ani plošné vypnutí ochrany dat.
- Vestavěný mikrofon a dostupná HFP sluchátka; UI ukazuje skutečnou route.
- Místní upozornění jen při již uděleném oprávnění, bez soukromého textu;
  doručení za každého stavu telefonu se neslibuje.

## Automatizované ověření

- Zámek nesmí ukončit běžící recorder, ale nesmí zahájit novou či opožděnou aktivaci.
- Přerušení ihned pozastaví vstup, opakované události dokončí část právě jednou.
- Konec hovoru / návrat / route změna samy mikrofon nezapnou.
- Pokračování zachová typ a session, vytvoří nové ID, odkaz na předchozí část a pauzu.
- Neúspěšné pokračování neztratí předchozí část; dovolí vědomý nový pokus.
- Přehrání zachované části nezruší rozpracované pokračování.
- Původní JSON bez continuation se načte beze změny; dokončené soubory a evidence
  zůstávají create-only. Nesprávná vazba na session / typ se odmítne.
- Znovu ověřit UI přehrávání a zachování syntetického vzorku po relaunch.

## Fyzická přejímka — pouze iPhone, uživatel vědomě nahrává

| Test | Postup a důkaz | Aktuální stav |
|---|---|---|
| Krátká kontrola zámku | Offline Start, slyšitelná značka, zamknout asi 30 s, mluvit i pod zámkem, odemknout, značka, Stop, poslech celého vzorku. Délka/velikost z metadat; nejde o T016. | Funkční zámek/pokračování/přehrání PASS podle Míly 2026-09-15, 0.2.0 (2); metadata, úplnost poslechu a offline režim samostatně nepotvrzeny. |
| T016 | 30 minut převážně pod zámkem, průběžné neosobní zvukové značky; Stop a celý poslech, skutečná délka/velikost. Jediný soubor v C01b není důkaz segmentace C01c. | PASS podle Míly 2026-09-16. CoreDevice metadata: 30:24,406, 175 147 072 B, 48 kHz mono, dokončeno bez příznaku přerušení; režim Letadlo, celý poslech OK. Přehrávání při zamčené obrazovce neběželo, což není kritérium T016. |
| T018 | Dostupná sluchátka: skutečný vstup, stání/chůze a zámek; slyšitelný hlas, zapsat limity větru/připojení. Bez dostupných sluchátek neuvádět PASS. | PASS podle Míly 2026-09-16: AirPods zobrazené jako aktivní mikrofon, několikaminutové záznamy ve stoje i za chůze, zámek, celý poslech a bez výpadků. Vítr nebyl přítomen, odolnost proti větru zůstává NEOVĚŘENA. |
| T019 | Uživatel zajistí příchozí hovor, jednou ignoruje a jednou přijme. Zachovaný zvuk před přerušením, nic z hovoru ani samovolné pokračování; Pokračovat až po ukončení hovoru. Agent nikomu nevolá. | PASS podle Míly 2026-09-16: ignorovaný i přijatý příchozí hovor, obě části přehratelné, nic z hovoru v audu a žádné samovolné pokračování. Technická metadata potvrzují dvě přerušené první části a jejich samostatná vědomá pokračování stejné session s pauzami 43,153 s a 112,272 s. |
| T020 | Odpojit/připojit skutečně aktivní mikrofon; přerušení, ověření staré části, vědomé pokračování a nová část stejné session s mezerou. | PASS podle Míly 2026-09-16: odpojení AirPods přerušilo záznam, pokračování použilo mikrofon iPhonu, opětovné připojení ukončilo druhou část a AirPods se staly aktivním vstupem až při dalším vědomém pokračování. Všechny části přehratelné, bez samovolného pokračování. Metadata potvrzují tři samostatné části jedné session a dvě přerušení. |
| T021 — prototyp | Během záznamu nelze spustit player ani druhý recorder; přepnutí aplikace nezruší běžící audio. Video / integrace Momentu až C04. | PASS podle Míly 2026-09-16 v rozsahu C01b: volba typu a Přehrát neaktivní, druhý recorder nešel spustit, po návratu z jiné aplikace pokračovala stejná Úvaha a čas narostl, jedna část bez přerušení a celý poslech OK. Metadata poslední Úvahy: 56,350 s, 48 kHz mono, `interrupted=false`, bez continuation. Plný T021 se po integraci videa/Momentu zopakuje v C04. |
| T024 — hranice C01b | Za rozpracovaného audia nuceně zavřít aplikaci. Po otevření žádný mikrofon, dokončené části zůstávají přehratelné, neověřený pokus je přiznaný. Žádný slib záchrany otevřeného souboru. | PASS podle Míly 2026-09-16. Snímek po relaunchi ukazuje Připraveno 00:00, vědomý Start, jednu neověřenou/neúplnou položku a zachované přehratelné části. Metadata potvrzují jeden nový samostatný pokus se `started.json` a bez `completed.json`; předchozí dokončená session zůstala zachovaná. Pád proběhl v nové samostatné Úvaze, nikoli v continuation, což kanonický T024 neomezuje. |
| T059 | Zámek po prvním odemknutí oproti restartu před prvním odemknutím; žádný automatický záznam/čtení chráněných dat před odemknutím, po něm zachované části. | PASS po řízeném zopakování 2026-09-16. Ochrana/restart: před prvním odemknutím bylo zařízení pro vývojové služby nedostupné, po odemknutí `Připraveno 00:00`, žádné samovolné nahrávání, počet neúplných zůstal 1 a soubor byl přehratelný. Opakování: všechny značky před zámkem, tři pod zámkem i po odemčení slyšitelné; jedna nepřerušená část. Metadata: 107,801 s, 48 kHz mono, `interrupted=false`. První 53,567s pokus měl při souvislém souboru neslyšitelný vyslovený úsek pod zámkem; je zachovaný jako nevysvětlené nereprodukované pozorování. Token/fronta v C01b neexistují. Název vstupu nebyl ve výsledné odpovědi zopakován. |

Každý výsledek musí obsahovat datum, verzi aplikace, telefon/iOS, kroky,
skutečnost, důkaz a PASS/FAIL/BLOCKED/NEPROVEDENO. Poslech potvrzuje člověk.
Audio zůstává na telefonu; pro report se čtou jen technická metadata.

Po každém Mílou oznámeném výsledku Adam bez další žádosti výsledek vyhodnotí,
řekne, zda odpovídá návrhu nebo vyžaduje vývoj, a rovnou uvede podmínky,
přesný postup a kritéria PASS následujícího neprovedeného testu. Pokud chování
odpovídá návrhu, pouhé dokončení testu není důvodem ke změně kódu. Při FAIL se
nejdřív zaznamená přesný projev, potom se opraví C01b a zopakuje jen dotčený
scénář; C01c se tím automaticky nezahajuje.

## Zastavení

C01b není přijaté pouze na základě testů či buildu. C01c (automatické segmenty,
60s checkpoint, journal a obnova během zápisu) se tímto nezahajuje.
G0/G1 a připravenost na pouť zůstávají otevřené. Žádný push/deploy ani nákup
členství nejsou součástí tohoto pokynu.
