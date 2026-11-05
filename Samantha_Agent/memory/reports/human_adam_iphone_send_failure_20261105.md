# 05/P1-B — selhání mobilní přejímky a lokální oprava odesílání

Datum: 2026-11-05. Autor: Data. Větev: `data/parallel-20261104`.
Pracovní proud: `layer-human-adam-development`.

## Integrace Willem — 2026-11-05 11:08 CET

Na Mílův výslovný pokyn je zdroj 5363238b po prvním dokončeném e-mailovém
p+n převzatý k samostatnému druhému vydání. Will zkontroloval zachování
korelačního ID, potvrzovacího důkazu a žádného automatického opakování.
250 cílených testů UI/profilů/klienta/hubu/recovery v aktuálním main PASS,
logs/data_iphone_integration_targeted_20261105.log. Jen paměťové konflikty
ručně sloučené, původní vývojová historie zachovaná. Produkční SDK se nemění.

Další krok je registrované druhé p+n a ověření skutečně servírovaného zdroje.
Fyzický iPhone test musí po návratu provést Míla; úspěch se z Node/HTTP
neodvozuje. Historická část níže popisuje stav při Datově předání.

## Stav přejímky

Míla potvrdil push a nasazení 05/P1-B. Převzetí původních commitů Data jako
`1b6fd61e` a `ccece787` je doložené v historii main a Willově integračním handoffu.
**Aktualizace 2026-11-05 11:41 CET: bod 2 na iPhonu PASS.** Míla po úpravě potvrdil
doručenou odpověď a správnou testovací značku z předchozího tahu. Normální
odeslání a návaznost Mac → iPhone jsou tím uživatelsky ověřené. Návrat
během rozpracované odpovědi, kontrola duplicit a technický reconnect App Serveru
zůstávají samostatně neověřené. UI oprava byla převzata z `5363238b` do main
jako `6972ea5c`; nový živý audit nasazení se při tomto paměťovém zápisu neprováděl.

Původní průběh před opravou:

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

UI oprava je nyní doložená v main jako `6972ea5c`. Míla po úpravě potvrdil
úspěšnou odpověď na iPhonu a návaznost testovací značky. Původní selhání bodu 2
je tím po uživatelském retestu uzavřené; přesný původní spouštěč nebyl dodatečně
prokázán. Tento zápis nepředstírá nový audit runtime ani další nasazení.

Další krok: zkontrolovat návrat na Mac a jediné zobrazení zpráv (bod 3),
potom samostatně obnovu stránky během rozpracované odpovědi (bod 4). Tyto
výsledky nejsou obsažené v samotné úspěšné odpovědi na iPhonu. Technický
reconnect App Serveru a SDK pilot zůstávají samostatnými body.

Změněný kód/testy: `human_adam_ui.py`, `test_human_adam_ui.py`,
`human_adam_send_frontend.test.cjs`, `luna_release_frontend.test.cjs`.
Kanonický handoff, TVBCP, registry a LL aktualizovány ve stejném kroku.
