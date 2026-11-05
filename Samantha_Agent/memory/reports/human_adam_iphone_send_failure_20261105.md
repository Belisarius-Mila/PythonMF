# 05/P1-B — selhání mobilní přejímky a lokální oprava odesílání

Datum: 2026-11-05. Autor: Data. Větev: `data/parallel-20261104`.
Pracovní proud: `layer-human-adam-development`.

## Stav přejímky

Míla potvrdil push a nasazení 05/P1-B. Převzetí původních commitů Data jako
`1b6fd61e` a `ccece787` je doložené v historii main a Willově integračním handoffu.
Přejímka však **není uzavřená**:

- Bod 1 na Macu: Míla potvrdil OK.
- Bod 2 na iPhonu: původní Mac zpráva byla viditelná, odeslaný dotaz zmizel
  bez odpovědi, zjevného zahájení práce nebo chybové hlášky. Totéž nastalo
  u dalšího ad hoc dotazu. Tyto dotazy Data znovu neodesílal.

## Čtecí diagnostika

- Dokumentace `tailscale_setup.md` popisuje soukromý HTTPS Serve na 443 do
  `127.0.0.1:8770` a zachovaný starší tailnetový TCP vstup na 8770.
  Živý `serve status --json` potvrdil HTTPS proxy. HTTPS a lokální health
  měly stejný PID i code stamp; hostname ani privátní konfigurace nejsou v zápisu.
- Živý GET status aktivního Human–Adam proudu obsahoval jen jeden dokončený
  přejímací dotaz, bez aktivního tahu či dalšího uloženého doručení. Obsahy
  soukromých zpráv, identifikátory vlákna a logy nebyly přeneseny do Gitu.
- Servírované HTML odpovídalo UI zdroji této větve před opravou. V kontrolovaném
  bezpečnostním logu nebyla dnešní odmítnutí `/api/human-adam/send`.
  Absence tohoto záznamu není důkazem, že žádný POST nepřišel: log neobsahuje
  všechny běžné přístupy. Z dostupných údajů nelze určit přesnou chybu na iPhonu.
- Žádný POST send, nový modelový tah, restart, změna Serve nebo provozních dat.

## Reprodukovaná chyba

Původní `sendMessage` vymazal editor a nastavil sendInFlight před vytvořením
client ID a serializací požadavku. Výjimka v této přípravě ležela mimo try/finally
HTTP části: dotaz se neodeslal, editor byl prázdný a obsluha mohla zůstat blokovaná
bez viditelné chyby. Regresní test proti původnímu kódu selhal.

Další problém: po nejistém výsledku GET status mohl vrátit poslední potvrzenou
historii bez daného ID a optimistický dotaz z chatu odstranit. Upozornění bylo
jen v horním stavovém řádku. Samotný obecný status human_adam_send_failed navíc
nedokazuje, že server před chybou nic nepřijal; nemá povolovat vrácení textu
do editoru k novému odeslání.

Toto jsou doložené slabiny odpovídající příznakům. **Konkrétní výjimka iPhonu
není prokázaná**; selhání crypto API v testu je syntetická injekce, nikoli
tvrzení o chování Mílova telefonu.

## Lokální změna

- Příprava ID, času, JSON a optimistického stavu proběhne před vymazáním editoru.
  Pokud selže, text i záměr zůstanou beze změny a zobrazí se chyba; počet POSTů 0.
- Selhání nebo nedostupnost crypto.randomUUID použije dosavadní fallback pro
  korelační ID. Nejde o autentizační token. Chyba doplňkového zvuku nezablokuje send.
- Viditelné upozornění u editoru zachová kopii nejistého dotazu i při obnovení
  historie. Kopie je needitovatelná, bez tlačítka opakovat; neukládá se do browser
  storage ani jiného nového trvalého úložiště.
- Po nejistém výsledku se další send blokuje. Obnovení stavu je jen čtení;
  upozornění zruší pouze completed + delivery_confirmed se stejným client ID
  a známým thread ID. Jiná zpráva, jiné vlákno nebo nepotvrzené dokončení nestačí.
- Jen potvrzené busy odmítnutí vrací původní draft, aniž přepíše novější rozepsaný
  text. Obecné selhání nebo síťová chyba zůstává nejisté, nikdy se automaticky neopakuje.
- Klient App Serveru, session hub, runtime, role, SDK a e-mailové moduly nezměněné.

## Ověření

- FAIL → PASS u skutečně extrahované JS obsluhy; žádné modelové volání.
- **150 cílených testů PASS**, bez skipů: UI, HumanAdamService, session hub,
  Codex klient. Nový Node VM kontrakt provádí synteticky přípravu před POST,
  crypto fallback, chybu zvuku, ztracené spojení, obecné serverové selhání,
  busy odmítnutí, zachování při refreshi, blokaci druhého POST a korelaci dokončení.
- **Úplná Cockpit brána PASS: 2 374 testů, 0 chyb a selhání, 5 PDF skipů bez ReportLabu** (523,365 s unit testů). Whitespace a syntax Python/JavaScript/shell PASS.
- Lokální logy pouze v ignorované `.venv`: `iphone-send-before.log`,
  `iphone-send-targeted.log`, `iphone-send-full-gate.log`.

## Další krok a omezení

Oprava je pouze v pracovní kopii. Bez push, integrace do main a nasazení;
produkční přejímka iPhone tedy stále FAIL. Po samostatně autorizovaném převzetí
a nasazení načíst čerstvou stránku a zopakovat jediný neškodný test. Úspěch
nelze odvodit z Node VM ani ze zdravého HTTPS health.

Při případném dalším selhání už má UI zachovat text a viditelně rozlišit
neodeslanou přípravu od nejistého výsledku. Přejímku uzavřít až po Mílově
potvrzení skutečného výsledku na iPhonu. Technický reconnect App Serveru
zůstává samostatným bodem.

Změněný kód/testy: `human_adam_ui.py`, `test_human_adam_ui.py`,
`human_adam_send_frontend.test.cjs`, `luna_release_frontend.test.cjs`.
Kanonický handoff, TVBCP, registry a LL aktualizovány ve stejném kroku.
