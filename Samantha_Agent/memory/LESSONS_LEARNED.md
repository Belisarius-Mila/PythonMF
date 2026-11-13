# Lessons Learned (LL)

Tento soubor je stručný registr ověřených řešení problémů, které se mohou vrátit
nebo jejichž princip lze znovu použít v jiné části projektu.

## Jak LL používat

- Při známém, podobném nebo opakovaném problému nejdřív prohledej tento soubor.
- Nový záznam přidej až po prakticky ověřeném řešení, ne při pouhém návrhu.
- Stejný problém neduplikuj; nové upřesnění doplň k existujícímu záznamu.
- Záznam drž krátký. Provozní historii nech v handoffu nebo TVBCP.
- Neukládej sem hesla, tokeny, soukromý obsah ani jiné citlivé údaje.

## Šablona

### LL-066 — Filmový worker musí najít nástroje i při startu z launchd

- Problém: render v terminálu prošel, ale zdrojový náhled spuštěný z Cockpitu selhal před vytvořením pracovních souborů; launchd PATH neobsahoval místní FFmpeg/FFprobe.
- Typ: opakující se
- Řešení nalezeno: 15102026
- Řešení: pouze dítěti filmové fronty přidat známé `/opt/homebrew/bin` a `/usr/local/bin` za dosavadní PATH. Neměnit prostředí rodiče, LaunchAgents ani službu Camino. Ověřit dohledání obou nástrojů pod službovým PATH a skutečný background render; terminálový render s bohatším PATH sám nestačí.

### LL-NNN — Stručný název

- Problém:
- Typ: opakující se | jednorázový
- Řešení nalezeno: DDMMRRRR
- Řešení:

## Záznamy

### LL-104 — Ukončení hlasu není konec úlohy ani potvrzení ceny

- Stav 2026-11-07: placený pilot 15/P2 Míla kompletně zrušil jako nerelevantní pro Agenta SDK Samantha. Níže uvedené zkušenosti jsou historické obecné poznatky, nejsou pokynem projekt obnovit. Provedený rozsah odstranění je v paid_voice_retirement_20261107.md.

- Problém: spojení hlasu, přepis a backendová práce mají odlišný životní cyklus. Výpadek může zanechat nepotvrzenou spotřebu a opakování vytvoření může založit další placenou relaci.
- Typ: opakující se
- Řešení nalezeno: 05112026
- Řešení: hlasový adaptér oddělit od vlastníka úlohy. Přepis není souhlas; čtecí pilot dostává jen snapshot callback. usage.seconds je kumulativní, konečný až z platného session.closed; bez něj nepředstírat konečnou cenu. Vytvoření neopakovat, pozdní známé session ID předat důvěryhodnému brokeru k úklidu. Při Stop ihned uvolnit mikrofon, data channel držet jen do finální události či timeoutu. Browserový časovač nenahrazuje serverovou kontrolu délky ani fakturační strop.
- Ověření: 132 cílených testů PASS včetně 26 nových, skutečné metody snapshot nad syntetickým stavem a Node browserových scénářů. Jde o neaktivovaný základ, nikoli živou hlasovou přejímku; voice_conversation_p2a_20261105.md.
- Doplnění 15/P2-B: kandidát a placená zkouška jsou dvě odlišná oprávnění. Serverová rezervace jednoho grantu musí přežít restart a vzniknout před API; při neznámém vytvoření nezakládat další relaci. Sideband reflektované audio nemá event_id, proto jej před obecným parserem vyřadit a neukládat. 32 brokerových testů, se souvisejícími moduly 91 PASS; voice_conversation_p2b_20261105.md.
- Doplnění 15/P2-C: místní framework Python může mít prázdné systémové CA úložiště, přestože OpenAI/httpx přes certifi funguje. Pro voice HTTPS/WSS explicitně použít již instalovaný ověřovaný CA bundle, nikdy nevypínat certifikát či hostname. Je-li původní session.start prokazatelně nezkoušený, nový transport může využít stejný schválený modelový pokus jen s hashem původního proof a společným create-only start claimem; jakákoli nejistota po startu zůstává blokovaná. Živý důkaz: právě jeden modelový start, final usage 47 s, český marker a nenulové PCM; voice_conversation_probe_20261105.md.

- Doplnění 15/P2-D: při připojení ke skutečnému Cockpitu číst jen již existující _hub; .hub/active_service mohou cold obnovou vytvořit stav. Server fixuje proud i thread a odmítne změnu výběru. Browser cookie dědí síťovou důvěru, není osobní autentizace; exact Origin/CSRF + explicitní cenový souhlas před create. Nový pokus až po closed/final usage, ne po refreshi nebo chybě. Novou audio roli bez reasoning_effort aktivovat až na kompatibilním parseru, odděleně od kódu; při převzetí zachovat cizí role.

- Doplnění 15/P2-E (06112026): společná hláška HTTPS/prohlížeč nerozlišuje secure context, getUserMedia a RTCPeerConnection. Tyto podmínky kontrolovat zvlášť a blokaci popsat před cenovým souhlasem; zaškrtnutí nemůže povolit mikrofon na HTTP. Tailscale šifruje přenos, ale HTTP stránka tím nezískává browserový secure context; localhost platí pro zařízení prohlížeče. Neodhadovat HTTPS URL ani nekonfigurovat proxy bez provozního oprávnění.

- Doplnění 15/P2-F (06112026): getUserMedia může zůstat nevyřízené. Čekání odlišit od připojování; nejprve Stop, pak ověřit iOS oprávnění aplikace a webu. Zachovat timeout, generaci pokusu a uvolnění pozdní stopy bez create. Neodvozovat zamítnutí jen z čekání; jména chyb mapovat na bezpečné instrukce, neposílat jejich raw text.

- Doplnění 15/P2-G (06112026): callback browserového setTimeout/clearTimeout uložený do instance a volaný this.timerMethod získá cizí receiver. Může skončit Illegal invocation ještě před getUserMedia a mimo try. Výchozí wrappery volat přes globalThis; testovat defaultní cestu s browserovým receiver kontraktem, nikoli jen injektovaný fake/Node timer. Zaseknutá hláška není důkaz čekajícího OS dialogu. V tomto případě 0 mic calls před opravou → 1 po opravě, 0 paid calls; fyzická přejímka zůstává samostatná.

### LL-095 — Unix socket nezaručuje shodný aplikační protokol

### LL-103 — Chybový text modelu nemusí znamenat ztracený obrazový výsledek

- Problém: jeden obrazový tah vrátil dvě dokončené imageGeneration položky s platnými PNG, ale text tvrdil chybu a doporučoval nové odeslání.
- Typ: opakující se
- Řešení nalezeno: 05112026
- Řešení: před jakýmkoli dalším modelem ověřit původní terminální účtenku a uložené artefakty. Jedinečné platné výstupy převzít jako samostatné varianty (omezená dávka), duplicity sloučit; UI oznámí ověřené uložení místo nepravdivé rady k opakování. Při opravě pouze zpracování výsledku lze lokálně přehrát původní journal, pokud modelový klient, instrukce, oprávnění a input hashes zůstávají přesně stejné. Změna exekučního otisku, vadná účtenka nebo výstup přehrání blokuje. Ověřeno skutečnými dvěma PNG z jednoho tahu a regresí bez nového RPC/modelu.

### LL-102 — Dokumentovaný sandbox musí potvrdit skutečný App Server

- Problém: server 0.163.0 odmítl dokumentované readOnly.access; vygenerované schéma místo něj zpřístupňuje pojmenovaný permission profile přes explicitní experimentalApi.
- Typ: opakující se
- Řešení nalezeno: 05112026
- Řešení: nejprve schéma konkrétního binárního serveru a neplacený command/exec preflight. Pro Ateliér pouze vlastní per-thread profil s minimálním systémovým čtením a jedním snapshot root, bez sítě/zápisu; žádná změna globální konfigurace nebo restart. Potvrdit přesný activePermissionProfile, cwd, model a never approval, bez širšího fallbacku. project_doc_max_bytes=0 je nutné znovu předat i při resume. Globální priority/Fast nepřebírat do Standard pilotu: explicitní serviceTierForTurn=default. Běžný textový klient zůstává bez opt-in a beze změny protokolu.
- Ověřeno znovu 07112026 u kalendářového návrhu: stejný named profile potvrzen prázdným thread/start bez modelového tahu; skutečný syntetický e-mailový tah pak uspěl bez kalendářových dat a nástrojů. Vypnout také zděděné browser/computer use, pluginy a image generation podle skutečného experimentalFeature/list. K návrhu neposílat přehled kalendářů; celý původní EML svázat digestem, uložit jediný pokus a nejistý výsledek neopakovat.
- Doplnění 11112026: `unknown field result_buffered_for_ns` při Code Mode exec není zákaz čtení složky; selhal i `pwd`. Ověřit skutečné serverInfo.version odděleně od instalovaného CLI a přímý read-only command/exec. Na peer0.163.0 / CLI0.167.0 prošlo čtení obou AGENTS.md. Lokální per-thread vypnutí code_mode/code_mode_host nemění sandbox; přijetí přepínačů ani RPC čtení samo nedokládá následné použití nástroje modelem. Neopakovat automaticky původní modelový tah.

### LL-101 — Unix socket nezaručuje shodný aplikační protokol

- Problém: kandidátní SDK konfigurace s `app-server proxy --sock` vypadá jako náhrada přímého Unix spojení; současná Samantha ale používá WebSocket a CLI proxy přenáší prosté bajty.
- Typ: opakující se
- Řešení nalezeno: 05112026
- Řešení: ověřit skutečný protokol nad socketem dvěma kontrolami. SDK/CLI proxy proti proudové fixture funguje; proti WebSocket fixture skončí deadline, zatímco současný UnixSocketAppServerTransport se připojí. Nepoužívat proxy jako náhradu tohoto transportu a po nejistém výsledku nevytvářet fallback vlákno ani další tah. Deadline ukončuje pouze proxy, nikoli sdílený server; výchozí SDK approvals je nutné výslovně odmítnout.
- Ověření: 105 cílených testů PASS včetně 12 nových pro krok C, jen syntetické sockety. Navazující skutečný reconnect současného transportu 5. 11. 12:50 CET: 17/17 kontrol PASS, A/B/A stejné existující idle vlákno, pouze threadId + excludeTurns:true bez override; původní procesy/socket i celý rollout zachované, žádný modelový tah. Míla potvrdil body 1–4; 05/P1 uzavřené. Reporty codex_sdk_p1c_20261105.md a codex_p1_reconnect_20261105.md.

### LL-100 — Celý vstup sám nezaručuje pravdivý koncept odpovědi

- Problém: agent obdržel celý text i HTML a správně shrnul požadovaný postup, ale koncept mohl zaměnit požadované podání za již hotový úkon nebo tvrdit nepřiloženou přílohu; editor přitom odesílá pouze text.
- Typ: opakující se
- Řešení nalezeno: 05112026
- Řešení: ověřit původní EML digest a celý vstup, oddělit požadavky od provedených úkonů i odpověď osobě od formálního podání. Zadání musí uvést skutečné možnosti editoru, termíny a chybějící podklady; oslovení odvodit z doložené osoby a podpis doplnit podle místní identity jen novému konceptu. Dvě skutečné zkoušky Terra/high po úpravě zachovaly termín, správný postup, oslovení a podpis bez tvrzení o příloze; stará karta zůstala zachovaná. Jednotlivý úspěch není obecná záruka kvality a původní text přepsaný uživatelem nelze bez historie zpětně doložit.

### LL-098 — Úspěšný prázdný IMAP SEARCH není chyba hodinové dávky

- Problém: iCloud vrací při nulovém počtu nových UID `OK, [None]`; klient očekával jen bytes a nechal hodinovou kontrolu nedokončenou. Minutový retry potom zpracoval nově příchozí zprávu mimo celou hodinu.
- Typ: opakující se
- Řešení nalezeno: 05112026
- Řešení: převést pouze úspěšné `OK, [None]` na prázdný seznam UID; skutečné NO/BAD a vadné odpovědi dál odmítat. Prázdnou hodinu dokončit bez FETCH/modelu a bez posunu kurzoru. Regrese reprodukovala původní selhání; po opravě nová zpráva v 10:19 čeká na 11:00. Ověřeno skutečným iCloud vstupem i cílenými testy; diagnostické čtení kurzory nemění.

### LL-096 — Git archive ve vnořeném projektu už používá relativní kořen

- Problém: izolovaný test s projektem v kořeni Gitu prošel, ale příprava runtime ve skutečném Samantha_Agent pod rodičovským PythonMF skončila pathspec chybou; prefix podprojektu byl přidaný dvakrát.
- Typ: opakující se
- Řešení nalezeno: 05112026
- Řešení: při `git -C podprojekt archive HEAD` použít cesty relativní k podprojektu a stejné relativní názvy v archivu. Nepřidávat znovu `rev-parse --show-prefix`. Instalační fixture musí mít stejný vnořený projekt jako produkční checkout. Ověřeno na skutečném repozitáři (původní pathspec exit 128, relativní archive exit 0) a třinácti instalačními regresními testy.

### LL-095 — Úspěšný test oznámení patří ke konkrétnímu nastavení

- Problém: po změně notifikační adresy nebo cílového odkazu by starý úspěšný test klamně potvrzoval nové nastavení; pád po HTTP pokusu by zase mohl způsobit dvojí zvuk.
- Typ: opakující se
- Řešení nalezeno: 04112026
- Řešení: svázat test s revizí webhooku/odkazu a před sítí trvale zapsat pokus. Stejné request ID vrací původní stav; přerušené `sending` přejde na nejistý výsledek bez retry. API přijetí označit jako přijetí, fyzický zvuk/klepnutí ověřit na telefonu. Lokální testy ověřily změnu revize, dvojklik, souběh, pád po rezervaci a žádné opakování po restartu.

### LL-094 — Změna UIDVALIDITY nesmí sama znovu spustit celou historii

- Problém: po přestavbě IMAP schránky se staré UID nepoužijí; reset kurzoru na nulu by bez rozhodnutí uživatele znovu posuzoval historickou poštu.
- Typ: opakující se
- Řešení nalezeno: 04112026
- Řešení: porovnat uložené UIDVALIDITY před SEARCH/FETCH a při změně zdroj zastavit s konkrétní chybou. Zachovat původní pozici; nové vymezení historie je explicitní servisní krok. Regrese FAIL→PASS ověřila nulový SEARCH/FETCH/modelový pokus i zachování starého UID a kurzoru v repository.

### LL-093 — Preference důležitosti je výslovné vodítko, ne přeskočení celého e-mailu

- Problém: odstranění karty může znamenat vyřízení i omyl; automatické učení z něj by potlačovalo další důležitou poštu. Pravidlo jen podle odesílatele je příliš široké.
- Typ: opakující se
- Řešení nalezeno: 04112026
- Řešení: učit jen výslovnou volbou, v rozsahu účtu + přesné adresy + podobného předmětu. Uložit atomicky, dvojklik sloučit a umožnit deaktivaci. Předat shodu modelu vedle kompletního textu/HTML, nevyřazovat před čtením a nepřepisovat modelový verdikt. Testy ověřily restart, rozsah pravidla, zrušení, zachování současné karty/SMTP potvrzení i plného konce textu při shodné preferenci; falešný model mohl ponechat nový e-mail důležitý.
- Upřesnění Míly 5. 11.: „Příště nezobrazovat“ je oddělený vratný seznam visibility_preferences pro hodinovou nedůležitou poštu. Filtruje až po plném posouzení a jen při important=false; důležitý výsledek se zobrazí i při shodném pravidle. Staré importance_preferences se nekonvertují. Zrušení pravidla obnoví existující přehled; položky, kurzory, koncepty a schránka se filtrem nemění. Doménové, HTTP a Node regrese: email_visibility_20261105.md.
- Doplnění12.11.: dekódování zobrazovaného jména může odkrýt čárku bez uvozovek. Pro pravidla nevybírat první položku z getaddresses; přijmout jen jedinou koncovou <adresu> bez dalších adres/skupin v prefixu. Dvě skutečné adresy dál odmítnout. Chybu zobrazit vedle použité akce, nikoli pouze na začátku dlouhé stránky. Doménové/HTTP/Node regrese FAIL→PASS, report email_visibility_sender_20261112.md.

### LL-092 — Výchozí hodnoty Pydantic nejsou volitelná pole strict výstupu modelu

- Problém: syntetický klient přijal schéma, ale skutečný App Server/Model je odmítl jako `invalid_json_schema`; Pydantic vynechal pole s výchozími hodnotami z `required`.
- Typ: opakující se
- Řešení nalezeno: 04112026
- Řešení: výstupní schéma musí vyžadovat všechny vlastnosti objektu, včetně `important` a `reply_subject`. Lokální výchozí hodnoty zachovat pro kompatibilitu starých záznamů. Testovat tento kontrakt i u vnořených objektů, ne pouze předání schématu falešnému klientovi. Doloženo skutečným HTTP 400, regresí FAIL→PASS, 65 cílenými scénáři a jedním úspěšným živým pilotem Terry. Chybové události zachytit v soukromé diagnostické účtence; neplatné schéma neopakovat automaticky. Oficiální podklad: https://developers.openai.com/api/docs/guides/structured-outputs.

### LL-091 — Potvrzené SMTP přijetí nepřeváděj na nové odeslání při chybě QUIT nebo kopie

- Problém: server může zprávu přijmout a až potom selže ukončení relace nebo IMAP kopie; opakování celého postupu by poslalo druhý e-mail.
- Typ: opakující se
- Řešení nalezeno: 04112026
- Řešení: evidovat sending před sítí a SMTP výsledek odděleně od QUIT/kopie. Potvrzený výsledek vrátit idempotentně, chybějící potvrzení ponechat nejisté bez retry. Testy odpovědí ověřily QUIT a kopii po přijetí, přerušení, přesný otisk obálky/textu a dvě souběžná potvrzení s jediným SMTP pokusem. Stejný princip už používá rodinný kalendář.

### LL-090 — Dlouhé modelové posouzení nesmí držet zámek uživatelských karet

- Problém: společný zámek přes celé síťové/modelové posouzení blokoval vyřazení nebo úpravu už připravených karet.
- Typ: opakující se
- Řešení nalezeno: 04112026
- Řešení: samostatný zámek serializuje pozorovací cykly, krátké uživatelské operace mají svůj zámek a všechny změny stavu používají existující atomický repository transaction. Test s pozastaveným modelem ověřil, že lze vyřadit jinou kartu a po dokončení modelu se ani jedna změna neztratí. Nepřenášet dlouhý I/O zámek do UI.

### LL-089 — Úplné modelové čtení nesmí použít zkrácený náhled zprávy

- Problém: e-mailové náhledy mají znakové limity; ani přítomnost původního EML sama neprokazuje, že model dostal konec dlouhého textu.
- Typ: opakující se
- Řešení nalezeno: 04112026
- Řešení: pro obsahový agentní cyklus použít explicitní úplnou MIME cestu bez ořezu textu a HTML, zachovat dosavadní náhledové limity a testovat unikátní marker až za jejich hranicí přímo ve vstupu modelu. Syntetická zpráva přes 200 000 znaků ověřila text, HTML i původní EML; běžný omezený náhled zůstal zachovaný.

### LL-084 — Výmaz projektu zahrnuje historii fronty a nezařazené pracovní kopie

- Problém: samotné odstranění projektových řádků a finálních médií ponechá texty v přijatých obálkách, dříve smazané záznamy, karanténu a odvozeniny; stará fronta může projekt znovu založit.
- Typ: opakující se
- Řešení nalezeno: 24102026
- Řešení: inventář odvozovat ze všech trvalých vazeb včetně accepted manifestů po opravě projekce a již smazaných místních Momentů. Nejasně přiřazené starší kopie blokují výmaz k auditu. Společný zámek chrání přenos/render/recovery, uložený plán dovolí pokračovat po pádu. Osobní obsah fronty odstranit, zachovat pouze UUID/otisky/kurzor proti obnovení a databáze zkompaktovat; telefon potvrzuje ACK až po vlastním výmazu. Ověřeno syntetickým kontraktem a skutečným Core Data SQLite/WAL; fyzický telefon po vydání zvlášť. Viz `camino/docs/PROJECT_TRASH_REPORT.md`.

### LL-079 — Změna složené stránky vyžaduje nový kontrolní otisk

- Problém: nový panel prošel statickou bránou, ale plné p+n zastavila původní očekávaná délka složeného Cockpitu.
- Typ: opakující se
- Řešení nalezeno: 23102026
- Řešení: po kontrole skutečného diffu spočítat přes load_frontend_page délku, počet řádků a SHA-256 celé výsledné stránky; aktualizovat pouze příslušný EXPECTED_PAGES fixture a spustit stejný cílený kontrakt. Kontroly neodstraňovat ani nesnižovat. Ověřeno 1 FAIL → 1 PASS; plnou bránu následně vždy znovu provede registrované p+n.

### LL-078 — Nepřesná citace old nesmí spustit další placený modelový pokus

- Problém: Luna dodala funkční vícesouborový návrh, ale nepřesně citovaný okolní řádek testu znemožnil jednoznačné převzetí.
- Typ: opakující se
- Řešení nalezeno: 20102026
- Řešení: Zachovat původní odpověď a kontrolu rozsahu. Po jedné kontrole opravit pouze kotvu old přes review_anchors s přesným otiskem; path/new od Luny zůstanou shodné. Shodné vybrané zdroje/kontext/role, nová izolovaná kopie a testy vážou aktuální čistý head. Navazující účtenka odkazuje na původní modelový tah, nová modelová spotřeba je nula. Změna kontextu se odmítne. Ověřeno skutečným Camino/JS návrhem 4 FAIL → 4 PASS i převzetím, bez dalšího modelu a bez oslabení původní validace.

### LL-077 — Trvalé smazání filmové varianty zahrnuje všechny pracovní pokusy

- Problém: odstranění samotného finálního MP4 ponechá velké segmenty, PNG a neúplné pokusy; opakovaný starý render požadavek může variantu obnovit.
- Typ: opakující se
- Řešení nalezeno: 20102026
- Řešení: potvrdit přesnou variantu a její inventář, vyloučit aktivní worker a cizí odkazy, před prvním unlink atomicky zapsat stav mazání bez mediální kopie. Odstranit všechny pracovní pokusy přes ověřené deskriptory; ponechat pouze malá metadata blokující staré request ID. Po pádu dokončit jen zbývající soubory potvrzené sady. Synteticky ověřeno odstranění všech pokusů, izolace podobných variant, souběh, přerušení a GET/HEAD/Range 404. Diskové bloky otevřeného souboru může OS držet do uzavření posledního přehrávání/stahování.

- Doplnění 20. 10.: skutečný renderer zveřejňuje MP4 přes interní hardlink z pracovního MP4. Zákaz všech hardlinků blokoval každé hotové video; zjednodušený fake tento rozdíl skryl. Inventář musí ověřit, že všechny názvy stejného inode leží uvnitř jedné potvrzené varianty; před každým unlink kontrolovat zbývající počet a po přerušení ho nově odvodit. Pracovní podadresáře procházet pouze přes ověřené deskriptory s limity. Skutečný render → smazání, cizí třetí odkaz a přerušení uprostřed interní dvojice jsou povinné regrese.

- Doplnění 10. 11. pro Ateliér: zrušení kartičky nestačí, obrazová data jsou i v AI input snapshotech a výsledkovém JSON. Mazací rozsah musí zahrnout tyto kopie, zachovat obsahově sdílené objekty a zablokovat pozdější recover původních obrázků. Před unlink uchovat jen neobrazovou účtenku; přerušené mazání dokončit pod stejným ID. Regrese ověřují skutečné unlink, chybějící finální JSON commit, sdílení, AI souběh a zachování textu.

- Doplnění 10. 11. pro galerii Ateliéru: po fyzickém smazání zachovaná textová metadata nejsou dostupným obrazovým návrhem. Filtr galerie, odkazy historie, uložený výběr a porovnání musí zohlednit existenci obrázku; lidské textové zadání se vykreslí bez prázdného rámečku. Neznámé právě dokončené AI výstupy ale neskrývat jen kvůli staršímu snímku místnosti. Regrese zahrnuje smazání právě vybraného návrhu i nový výstup před obnovou snímku.

### LL-076 — TTS může vracet prázdný zvuk i po aktualizaci knihovny

- Problém: původní endpoint denní sovy vracel HTTP 403 s edge-tts 7.2.8 a `NoAudioReceived` také s 7.3.1; selhal i skutečný cloudový běh.
- Typ: opakující se
- Řešení nalezeno: 20102026
- Řešení: v samostatné sériové denní rutině použít pro jednu TTS operaci Microsoft endpoint `api.msedgeservices.com/tts/cognitiveservices/websocket/v1`, po úspěchu i chybě obnovit původní nastavení knihovny. Neměnit text, hlas ani rychlost a nepřepisovat předchozí audio při chybě. Skutečný canonical local-preview vytvořil platnou 23,376s MP3; 24 cílených testů prošlo. Produkční výsledek vždy ověřit zvlášť přes workflow head a veřejný JS/MP3. [Upstream incident](https://github.com/rany2/edge-tts/issues/490).

### LL-075 — Záloha živého archivu potřebuje vlastní rozsah a skutečně zastavenou službu

- Problém: zelená projektová záloha PythonMF nepokrývala živé Camino v Application Support. Návrat z launchctl bootout navíc ještě neznamenal dokončené zastavení; první pokus proto nevytvořil snapshot a služba vyžadovala řízený návrat.
- Typ: opakující se
- Řešení nalezeno: 19102026
- Řešení: samostatný doplněk do ověřeného připojeného šifrovaného cíle; zámek filmových zápisů, po stop čekat na skutečné unloaded, pak stávající offline zámek a SQLite backup API včetně WAL. Ověřit všechny soubory SHA-256 a archiv vůči mediálním účtenkám. I po chybné odpovědi stop vyčkat na unloaded; samotné enable službu po bootout nevrátí. Timeout bootout musí pokrýt 330s ukončovací interval vlastní definice. V finally vrátit původně běžící vlastní službu, čekat na autentizovaný správný archiv a teprve pak vydat dokončený manifest. Při chybě zachovat soubory a nejprve zjistit stav; neopakovat slepě. Ověřeno na živém archivu a regresí asynchronního stop; úplný nový Mac má vlastní přejímku.

### LL-074 — Delegace ze síťově uzavřeného editoru potřebuje místní serverový kanál

- Problém: App Server sandbox s networkAccess=false odmítá i HTTP na localhost; vlastní nový App Server z editoru by navíc dědil jeho omezení.
- Typ: opakující se
- Řešení nalezeno: 17102026
- Řešení: Zachovat sandbox. Server povolí souborový IPC kanál pouze pro aktuální autorizovaný writable tah, ověří projekt/thread/message a určí workspace i centrální roli sám. Nejvýše jeden úkol, jednorázové převzetí, zrušení grantu v finally i při chybě. Skutečný command/exec v networkAccess=false potvrdil funkční IPC bez rozšíření sítě. Nezaměňovat platnou syntetickou zkoušku za fyzickou přejímku nasazeného portálu.

### LL-073 — Krátké zadání není krátký kontext kontrolora

- Problém: Čtecí Sol dostal 165 bajtů dat, ale implicitní kontext vytvořil 18 337 tokenů; režie může převážit užitečnou práci.
- Typ: opakující se
- Řešení nalezeno: 17102026
- Řešení: Pro pevnou datovou rutinu samostatný jednorázový kontext, pouze potřebné instrukce a podklady, per-thread vypnuté nástroje/konektory/MCP/hooky/paměti/dovednosti a projektové instrukce. Stejný podklad klesl na 10 995 tokenů; měřit stále celý hlavní model i kontrolora. Limit přijetí po dokončení není tvrdý fakturační strop. Nezvyšovat limit jen pro průchod testu a neopakovat automaticky.

### LL-072 — Tailscale audit služby potřebuje explicitní CLI režim

- Problém: V launchd prostředí bez TERM macOS Tailscale vrací s exit 0 chybu GUI místo JSON; ochrana pak selže po úspěšném převzetí Lunou.
- Typ: opakující se
- Řešení nalezeno: 17102026
- Řešení: Pouze čtecímu Tailscale subprocessu předat TAILSCALE_BE_CLI=1, neměnit rodičovské prostředí, síť ani služby. Pojmenovat ochrannou fázi samostatně. Test s minimálním launchd prostředím vrací přesný původní snapshot Camino/Serve/autosave.

### LL-071 — Spotřeba p+n zahrnuje i předání a dohled

- Problém: Samotná levná sazba pomocníka nedokazuje úsporu celého workflow; kumulativní thread total, cached input a reasoning se snadno započítají dvakrát.
- Typ: opakující se
- Řešení nalezeno: 17102026
- Řešení: Změřit rozdíl počítadel původního Adama a celou spotřebu čerstvého pomocníka i jednorázového modelového převzetí. Cached input je část vstupu, reasoning část výstupu. Chybějící telemetrie zůstane neznámá; Standard kreditní odhad označit zvlášť od vyúčtování. Ověřeno živým modelovým tahem, přímým p+n A a testy normalizace/soukromé projekce.

Doplnění 17102026 k LL-071: Nativní modelový pomocník navíc zdvojuje roli, pokud worker již sám volá Lunu. Společný submit_release nyní audituje a spouští jednu Lunu přímo; programové wait_for_release je připnuté k job ID, timeout neprovádí retry. Ověřeno všemi 33 proudy a skutečným syntetickým tahem bez publikace; z počtu vrstev samotného nevyvozovat procento úspory.

### LL-070 — Doporučený nástupce modelu není schválená náhrada

- Problém: Pevné jméno modelu zastaví delegaci po jeho stažení; automatický
  přechod na default nebo doporučené upgrade může změnit cenu i kompatibilitu.
- Typ: opakující se
- Řešení nalezeno: 17102026
- Řešení: Jedna centrální role s cenově posouzenými a skutečně otestovanými
  kandidáty, živý katalog ověřující model/úsilí a neměnný otisk volby v jobu.
  Kandidátský probe používá pouze syntetický vstup a nic neschvaluje ani
  nepublikuje. Bez schválené kompatibilní náhrady se zastaví před push.
  Ověřeno integračními testy a skutečnými read-only zkouškami nové role.
- Doplnění 05112026: novou roli nelze přidat do sdíleného JSON jen podle
  parseru hlavního checkoutu. Ověřit také skutečné vlastněné runtime kopie
  (zejména hodinový e-mailový agent), které odmítají neznámé KNOWN_ROLES.
  Aktivaci blokovat do kompatibilního nasazení a registrovaného upgrade;
  modelová politika se má zpřístupnit až odpovídajícímu běžícímu procesu.
  Ověřeno živým AST čtením kopie ac9f3bed a testy blokované / kompatibilní
  aktivace v interior_ai_activation.py. Následný skutečný registrovaný upgrade
  5. 11. na 2fe0481e zachoval celý business otisk i nastavení; instalovaný parser
  úspěšně načetl sdílený JSON s novou rolí.
  Totéž ověřeno pro audio roli bez reasoning_effort: další registrovaný upgrade
  2fe0481e → 11b4ce64 zachoval stav i všechny dosavadní bindingy; skutečný
  instalovaný parser načetl Voice i Interior. 141 následných kontrol PASS.

### LL-069 — Obecné p+n musí zmrazit projekt i registrovaný cíl

- Problém: Stejný Git head může patřit předání různých projektů, ale jejich
  runtime a veřejný web vyžadují jiný způsob nasazení a jiný důkaz.
- Typ: opakující se
- Řešení nalezeno: 17102026
- Řešení: Potvrzení svázat s oběma heads, původním projektem a serverovým
  cílem; hlídat je i před push a při interním kroku. Použít registrovaný
  publisher, pro web ověřit jeho cestu. Již zarovnaný main plně otestovat
  bez dalšího push. Rozšířená účtenka nesmí měnit starý striktní modelový
  kontrakt. Ověřeno 286 integračními testy a skutečnými suchými běhy Luny;
  pravidla v `technical/luna_release_orchestration.md`.

### LL-068 — Prázdný úklid nedokazuje funkční autosave

- Problém: Automatická retence držela 12 dvojic, ale proces po ukončení
  původní relace neběžel. Cockpit proto dlouho správně nenabízel úklid,
  zatímco nouzová kopie byla zastaralá. Starý textový převod současných
  zpráv navíc vytvářel pouze hlavičku.
- Typ: opakující se
- Řešení nalezeno: 16102026
- Řešení: Nezávislý proces neukončovat s terminálem, po startu ověřit čerstvou
  kopii a v panelu prioritně ukazovat běh, stáří a chybu posledního pokusu.
  Nulový počet kandidátů není zdravotní kontrola. Rozpoznávat i současné
  zprávy, nepřepisovat projekt cizí relací a chránit předchozí úspěšnou dvojici.
  Trvalý LaunchAgent je samostatně schvalovaná systémová konfigurace.
  Při prvním obnovení je automatické mazání vypnuté a starší historie zachovaná.
  Na tomto Macu přímý shellový start z launchd nemohl otevřít skript na Ploše;
  ověřený start přes projektový Python drží worker jako dítě a předává ukončení.
  Úspěšná registrace služby sama nestačí: vyžadovat nové uložení a zkoušku
  automatické obnovy. Při zastavování čekat pouze na původní ověřené PID,
  protože správce služby mezitím může spustit náhradu.

### LL-067 — Do objemu projektu nepatří publikační klony a sestavené výstupy

- Problém: Kvantitativní přehled ukazoval 877 153 lokálních řádků, protože
  sečetl také celý publikační klon a Swift build cache. Starší oprava
  dočasných adresářů a Python prostředí byla přítomná, ale tyto cesty nepokrývala.
- Typ: opakující se
- Řešení nalezeno: 16102026
- Řešení: Při průchodu vynechat provozní publikační workspace, obvyklé
  build/závislostní adresáře a každý vnořený Git kořen (`.git` adresář i soubor),
  nikoli jen konkrétní název starého klonu. Zachovat skutečné lokální zdroje
  mimo Git; symlinky nečíst. Ověřit agregaci i API a skutečné read-only měření.
  Místní výsledek přibližně 347 tisíc řádků / 2 143 souborů, 12 cílených
  testů PASS. Nasazení je samostatný krok; staré soubory se nemažou.

### LL-065 — Přejmenovaná a smazaná příloha nesmí zablokovat metadata frontu

- Problém: Klient vyřadí smazaný Asset, ale historický název přílohy zůstane
  u živého Momentu. Server správně odmítne neexistující cíl a zastaví i další data.
- Typ: opakující se
- Řešení nalezeno: 14102026
- Řešení: Původní odmítnutou obálku zachovat. Storno dovolovat jen s místním
  tombstonem, skutečným 422 a čerstvým důkazem, že pořadí nebylo přijato.
  Server vložený originál znovu validuje a vyžaduje globálně nedeklarovaný
  Asset; storno zachová všechny hodnoty Momentu a spotřebuje jeho revizi.
  Nepřeskakovat cursor, nepřepisovat přijatou historii a neobnovovat smazané médium.
  Skutečné Swift obálky → API, retry/reopen a negativní důkazy PASS; 68 Swift
  a plná brána 1925/1925 PASS. Míla po IPA18 potvrdil funkčnost; Mac přijal
  jedno vymezené storno a navazující operace/média. Starých 740 paketů a
  234 mediálních účtenek přesně zachovaných, úplný SHA audit PASS.
  Doplnění 15. 10.: při smazání audio session musí být potlačen i dosud
  neposlaný playback layout, včetně pozdního backfillu. Přidělené obálky
  neodstraňovat. Pro již odmítnutý layout použít pouze vymezené storno
  s místním tombstonem a čerstvým důkazem 404/nepřijetí, zachovat originál.
  Skutečné Swift → API testy a retry/reopen PASS; Míla po IPA19 potvrdil
  přenos, Mac přijal audio storno a navazující metadata/média. Běžnou
  validaci a deklarované zdroje neobcházet.

### LL-064 — Zvuk po spojení PCM segmentů potřebuje souvislé PTS vzorků

- Problém: Milisekundové časové značky pracovních MKV se při spojení
  překryly o osm PCM vzorků; strict MP4 mux odmítl Non-monotonic DTS.
- Typ: opakující se
- Řešení nalezeno: 12102026
- Řešení: Po concat nastavit audio timebase 1/48000 a PTS podle počtu
  skutečně přijatých vzorků (`asettb=1/48000,asetpts=N/SR/TB`), potom mix
  a AAC. Kontrolovat délku obou stop a celý decode; neoslabovat `-xerror`.
  Regrese má 20 zlomkových střihů; oba skutečné 200s profily prošly.

### LL-063 — Vícevrstvé iPhone MPO nelze přímo smyčkovat jako fotografii

- Problém: JPEG/MPO s další obrazovou vrstvou resetoval video filtry;
  část fotografií skončila bez obrazu, přesto segment měl plnou audio délku.
- Typ: opakující se
- Řešení nalezeno: 12102026
- Řešení: Ze zdrojového originálu načíst hlavní obraz (seek 0), EXIF
  orientaci a ICC převod do sRGB; vytvořit pracovní PNG bez metadat,
  zachovat celý rám a originál včetně dalších vrstev. Na výsledku ověřit
  i přesný počet snímků, nejen délku kontejneru. Syntetické dvouvrstvé
  MPO i skutečné 720p/1080p se všemi 25 záběry prošly.
- Doplnění 05112026 pro Ateliér: iPhone soubor s příponou JPG může Pillow
  klasifikovat jako MPO a is_animated=true kvůli pomocné vrstvě. Neodmítat
  jej jako animaci a nezvyšovat kvůli tomu MB/Mpx limity. Explicitně povolit
  MPO jako JPEG, načíst hlavní obraz, zachovat celý originál a nadále odmítat
  skutečné PNG/WebP animace. Tři skutečné 4032 × 2268 fotografie a orientovaný
  dvouvrstvý syntetický vzorek ověřené; interior_iphone_jpeg_mpo_20261105.md.
- Doplnění 23102026: rozlišení originálu fotografie není limit výstupního
  videa. Platný JPEG 5918 × 3860 blokoval společný 4096px vstupní limit.
  Sdílený dekodér připraví hlavní obraz do cílového rozměru (Lanczos, celý
  rám, ICC/sRGB), při zachování limitů 64 MiB/64 Mpx/16384 px. Video/HDR
  brány zůstávají. Ověřit i okraje a snímky obou profilů, ne pouze probe.
  Skutečný originál a dosavadní střihy/jobs před/po hashově shodné.

### LL-062 — Konečná Mac sada potřebuje vlastní původ a read-only archiv

- Problém: Potvrzená konečnost Mac dat byla zaměněna za další telefonní
  uzavření, zatímco Cockpit nabízel pouze syntetickou ukázku.
- Typ: opakující se
- Řešení nalezeno: 12102026
- Řešení: Po výslovném vlastnickém potvrzení konečnosti lze uložit
  samostatný projekt s původem `owner_confirmed_mac`, bez fingovaných
  telefonních front. Archivní DB otevírat `mode=ro`, nikoli přes
  zapisující/migrující konstruktory; manifest uložit mimo archiv i Git.
  Sdílený validátor zachová účtenky, hashe, revize a soukromí. Ověřeno
  na skutečném dni 6. 10.: 30 zdrojů, přesně shodný archiv před/po a
  funkční Cockpit přehled v odděleném HTTP náhledu, bez restartu Camina.

### LL-061 — GitHub brána musí připravit skutečný Git i serverové závislosti

- Problém: Na macOS 14 byl moderní Homebrew Git v PATH, ale aplikace přes
  `xcrun` zvolila starší Apple Git bez `--attr-source`. Nový serverový test
  současně neměl `httpx`, protože workflow instaloval jen root requirements.
- Typ: opakující se
- Řešení nalezeno: 12102026
- Řešení: CI vybere dostupný Xcode přes `DEVELOPER_DIR`, před testy ověří
  skutečný `xcrun --find git` a podporu `--attr-source`, instaluje oba
  requirements a zahrne serverový soubor do cache i triggeru. Ověřeno na
  macOS 15/Xcode 26.3, Apple Git 2.50.1: GitHub běh `38266173656` success,
  1876 testů OK (10 skip). Není nutná změna produkčního kódu ani restart
  běžícího Camina; fail-closed whitespace kontrola zůstává zachovaná.

### LL-060 — GitHub push může použít ověřené CLI přihlášení místo Keychain

- Problém: HTTPS push blokoval macOS Keychain `-25308`, zatímco staré
  přihlášení GitHub CLI bylo neplatné.
- Typ: opakující se
- Řešení nalezeno: 12102026
- Řešení: Dokončit nové GitHub device přihlášení a ověřit `gh auth status`,
  přesné heads a push guard. Pro jediný již schválený push použít
  `git -c credential.helper= -c 'credential.helper=!gh auth git-credential' push …`;
  tento příkaz nepotřebuje změnu globálního helperu ani token v argv.
  Ověřeno na přesném P2-B fast-forwardu. CLI může při nedostupném Keychain
  uložit přihlášení do místního souboru; ověřit soukromá práva a nikdy
  nevypisovat ani necommitovat jeho obsah.

- Doplnění 17102026: registrovaný GitHub batch před jediným HTTPS push
  umí vybrat již platné CLI přihlášení podle tohoto postupu. Ověření CLI
  přihlášení neukládá výstup, helper platí pouze pro daný příkaz a globální
  konfigurace se nemění. Ostatní remotes zachované; cílené testy PASS.

### LL-059 — Izolovaný Camino release musí obsahovat nové importy

- Problém: P2-B server importoval filmový modul a pomocnou knihovnu, které
  selektivní `git archive` releasu neobsahoval; běh ze zdrojového stromu to
  neodhalil.
- Typ: opakující se
- Řešení nalezeno: 11102026
- Řešení: Při novém serverovém importu doplnit závislosti do `RELEASE_PATHS`
  a před nasazením spustit izolovaný `python -I` import pouze z výsledného
  archivu. Opravený P2-B release takto prošel; provozní upgrade je samostatný
  krok po GitHub pushi.

### LL-058 — Syntetický film nesmí namlouvat přejímací instrukci

- Problém: TTS komentář vyslovil technický požadavek „Na konci musí být slyšet…“
  a skončil 9,225 s před koncem filmu; úplné dekódování ani kontrola posledního
  zvuku neodhalily nevhodný obsah a polohu věty.
- Typ: opakující se
- Řešení nalezeno: 11102026
- Řešení: V syntetickém scénáři použít přirozenou samostatnou závěrečnou větu,
  umístit konec zdrojového hlasu jednu sekundu před konec obrazu a ověřit
  skutečný čas ticha ve finálním MP4. Nový běh P2-A a test časové osy prošly;
  lidský poslech nové verze zůstává samostatnou přejímkou.

### LL-057 — Otočení testovacího videa prokazuje matice a dekódovaný obraz

- Problém: FFmpeg 8.1 při syntetické zkoušce po `-metadata:s:v:0 rotate=90`
  nevytvořil display matrix; údaj v příkazu tak nebyl důkazem testu rotace.
- Typ: opakující se
- Řešení nalezeno: 10102026
- Řešení: Vstupní `-display_rotation:v:0 90` před stream-copy; přes FFprobe
  ověřit skutečnou matici a přes dekódovaný snímek výslednou orientaci bez
  ořezu. Ověřeno v `tests/test_camino_film.py` a syntetickém běhu P2-A;
  fyzické přehrání zůstává samostatná přejímka.

### LL-056 — Selektivní odstranění média musí zachovat sekvenci, ale upravit inventář obnovy

- Problém: Reset journalu/identity rozbije spojení; ponechané verified položky
  fyzicky smazaných médií zase způsobí recovery_mismatch nebo chybějící soubor.
- Typ: opakující se
- Řešení nalezeno: 03102026
- Řešení: Pro samostatně schválený úklid používat přesný seznam ID a hashů,
  živý inventář obou stran a zkoušku na kopiích. iOS mazat přes vlastní API
  aplikace s trvalým tombstonem; u oboustranného fyzického smazání vyřadit jen
  příslušné media položky journalu. Accepted metadata obálky, sekvence, cursor,
  identita a přihlášení zůstávají. Mac změnit offline jen pro stejné cíle,
  včetně chunků a Viewer kopií. Ověřit FK, retry bez obnovení smazaného obsahu,
  nový Moment, úplný recovery proof a pak skutečný kontakt telefonu.
  Nejde o podporu běžného serverového delete API ani návod na reset archivu.

- Doplnění 20. 10.: po zastavení přenosu mezi metadata a médii může lokální smazání ponechat přijatý Asset na Macu bez session, účtenky a originálu. Prázdná fronta telefonu tedy neprokazuje úplný Mac den. Pro schválenou jednorázovou opravu ověřit přesné ID/body hash a absenci všech mediálních protějšků i živých vazeb, na kopii projít filmový validátor; offline po snapshotu odebrat jen tyto živé Asset řádky. Accepted obálky, kurzor, identity a ostatní tabulky zachovat. Čtyři video řádky odstraněné, 44 zdrojů dne a 304 celkových originálů ověřených; nejde o obecný serverový delete kontrakt.

### LL-055 — Camino „Mac není dostupný“ může být odmítnutý místní zápis

- Problém: Po servisní obnově telefonu sync journal zůstal beze změn a aplikace
  střídala nedostupný Mac a požadavek na kontrolu inventáře.
- Typ: opakující se
- Řešení nalezeno: 02102026
- Řešení: Získat doménu/kód skutečné chyby bez userInfo či citlivého obsahu.
  Cocoa 513 s POSIX 13 byl atomický zápis journalu do Sync vlastněného rootem
  (0755), nikoli síť. „Writable“ v devicectl není důkaz práv procesu aplikace.
  Ověřit vlastníka adresáře přímo v procesu; původní adresář zachovat a nový
  vytvořit samotnou aplikací. Až potom hodnotit síť/token (zde následoval 401).
  Prázdný journal ani úspěšný build nejsou důkaz přenosu; vyžadovat accepted
  metadata + verified médium současně na telefonu a Macu. Po empty bootstrapu
  ověřit i config trip vazbu a skutečný restart Mac služby.

### LL-054 — Opožděné soví workflow může po no-op publikovat starý web

- Problém: plánovaný běh přišel po oknu 03–08 CEST; generátor korektně
  skončil no-op, ale navazující Pages job zveřejnil staré zdrojové app.js.
- Typ: opakující se
- Řešení nalezeno: 29092026
- Řešení: publikační režim `--publish-owl` už nemá časové okno ani
  completed-day shortcut. Před uploadem vyžaduje čerstvě vytvořené MP3,
  platný header, shodné kopie, přesný dnešní selector v obou `app.js` a nové
  cache klíče v `app.js`/`index.html`; při chybě skončí fail-closed. Ověření:
  cílených 23 testů a plná brána 1843/1843. Po pushi znovu ověřit `headSha`,
  veřejný JS a MP3, ne jen zelený workflow.

### LL-053 — Mapa musí dědit aktuální Viewer projekci a čas pořízení

- Problém: řazení uploadem/kapitolou posune pozdě doručený bod; oddělená
  statická trasa nebo starý klientský popup může přežít změnu soukromí.
- Typ: opakující se
- Řešení nalezeno: 28092026
- Řešení: mapový JSON vždy z aktuální konzistentní viewer_snapshot, řadit
  capture UTC + ID, den podle původního místního času. Odkaz může vést do jiné
  aktuální kapitoly. Zrušit staré požadavky při skrytí stránky, vyčistit vrstvy,
  popupy i odkazy a po návratu znovu ověřit. Syntetické projekční/HTTP/Node
  testy v VIEWER_ROUTE_MAP_REPORT.md; Safari a živý podklad zvlášť NEOVĚŘENO.
  OSM navíc vyžaduje Referer: origin výjimka patří jen mapové stránce,
  běžný Viewer nadále no-referrer; podklad až po vědomém kliknutí.

### LL-052 — Úplný přenos neprokazuje přítomnost nepovinné GPS

- Problém: serverový model GPS existoval, ale iPhone posílal `location=null`;
  zelený počet úplných Momentů proto nebyl důkazem zaznamenané polohy.
- Typ: opakující se
- Řešení nalezeno: 27092026
- Řešení: ověřit celý řetězec capture → trvalý intent → Swift JSON → API →
  znovuotevřená DB, ne jen existenci pole či stav uploadu. U audia/videa
  zachovat bod začátku, přílohou jej neměnit. Test používá syntetické body;
  skutečný fix a telefonní přenos potvrdit zvlášť GPS1–GPS4. Podrobnosti
  `camino/docs/GPS_CAPTURE_REPORT.md`; staré body se nedoplňují.

### LL-051 — SideStore RemotePair port a Camino owner token jsou dvě různé překážky

- Problém: SideStore hlásil nedostupný telefon i se zapnutým LocalDevVPN;
  po importu Camino hlásilo obecné selhání obnovy i přes dostupný Cockpit.
- Typ: opakující se
- Řešení nalezeno: 26092026
- Řešení: SideStore 6032424 může držet starý RemotePair port. Skutečný zjistit
  přes Settings → Experimental Features → Network Discovery → local → Remote
  Pairing, ověřit zařízení a vložit do Connection Config. Port je proměnlivý,
  nekopírovat historickou hodnotu. Zelená Device Reachability a import byly
  fyzicky potvrzené až po této změně; restart ani změna masky samy nepomohly.
  Pro Camino přepnout LocalDevVPN na Tailscale. Dostupný Cockpit nedokazuje
  platnost owner tokenu: starý token vracel 401, aktuální 200. Po jeho výměně
  obnova prošla a server potvrdil oba flagy=false i následný nový přenos.

### LL-001 — Lokální kontrola sovy znečišťovala pracovní strom

- Problém: Opakované lokální generování sovího MP3 zapisovalo dvě MP3 a měnilo
  dva produkční `app.js`. `main` pak nebyl čistý, profilové workspaces se
  zablokovaly a bylo nutné soubory ručně uklízet a znovu dorovnávat.
- Typ: opakující se
- Řešení nalezeno: 29072026
- Řešení: Pro místní kontrolu používat `daily_3am.py --local-preview`. MP3 vznikne
  jen v ignorované složce `data/daily_3am/previews/`; produkční soubory ani denní
  stav se nezmění. Produkční MP3 vytváří až GitHub Pages workflow ve svém
  dočasném runneru.

### LL-002 — Slovníkové aplikace: konzistence kódu, mappingu a obrázků

- Doplnění 4. 11. 2026: historické opravy podle Order nelze použít na nově uspořádané CSV. Náhled starého Janina helperu by přepsal 10 jiných hesel. Doplňovat jen prázdné věty podle aktuálního FR/CZ a snímku souboru; použít existující bezpečný CSV store s ověřenou zálohou a konfliktní kontrolou. Celý původní řádek a L/HT ověřit po zápisu. Stávající helper má zůstat jen čtecím podkladem, dokud nebude samostatně opravený.

- Problém: Obrázky se nemusí zobrazovat, přestože mapping vypadá správně.
  Příčinou může být záměna variant aplikace nebo mappingu, neúplný `Pict`, jiná
  cesta na cílovém zařízení, starý obsah v paměti nebo rozdíl ve formátu či
  názvu souboru. Lokální obrázky navíc nemají znečišťovat Git.
- Typ: opakující se
- Řešení nalezeno: 29072026
- Řešení: Každou variantu aplikace udržovat odděleně. Kontrolovat celý řetězec
  `CSV -> mapping.json -> skutečný soubor v Pict -> dekódování aplikací`,
  ideálně diagnostikou přímo na cílovém zařízení včetně cest, počtů a
  kontrolních součtů. Mapping před změnou zálohovat, na zařízení nahrát do všech
  skutečně používaných míst a aplikaci restartovat. Chybějící obrázky doplňovat
  podle výsledku úplného auditu. Před webovým syncem navíc vypsat nepoužívané
  assety; bez samostatně potvrzeného mazání je zachovat. Lokální či iCloudové
  servisní obrázky držet mimo Git pomocí přesného lokálního exclude.

### LL-003 — Proměnlivý provozní stav neověřovat jen z projektové paměti

- Problém: Potvrzená aktivace rodinného kalendáře se po runtime kroku
  nepropsala do kanonické git-safe paměti. Pozdější bezpečný audit nečetl
  soukromou konfiguraci a aktivní souhrny proto vedly režim jako neověřený.
- Typ: opakující se
- Řešení nalezeno: 01082026
- Řešení: U dotazů typu `je aktivní`, `běží` nebo `je připraveno` nejprve
  použít dostupný redigovaný read-only live audit. Paměť používat jako
  historický kontext a bezpečnostní pravidla, ne jako důkaz současného runtime
  stavu. Po významné provozní změně zapsat git-safe redigovanou účtenku bez
  tajemství a soukromého obsahu.
- Doplnění 17102026: stejné pravidlo platí pro texty Cockpitu. Stav kalendáře
  zobrazovat z read-only auditu s časem kontroly; při chybě přiznat nejistotu,
  neodvozovat vypnutí. Kontrola existence DOM prvků prokazuje jejich přítomnost,
  nikoli napojené události nebo úspěch akce.

### LL-004 — Sdílený provozní stav nesmí být relativní k profilovému workspace

- Problém: Izolovaný profil hledal záznam poslední zálohy ve své kopii projektu,
  takže hlásil chybějící zálohu, i když ji kanonický projekt správně evidoval.
- Typ: opakující se
- Řešení nalezeno: 02082026
- Řešení: Provozní stav společný pro všechny profily rozpoznávat přes kanonický
  kořen projektu. Profilové workspaces stav pouze čtou nebo aktualizují ve
  společném umístění; nevytvářejí vlastní kopie, které by se mohly rozejít.

### LL-005 — Procvičování slovíček může zablokovat direct-main vývoj

- Problém: Slovníkové aplikace při běžném procvičování zapsaly příznaky `HT`
  přímo do verzovaných CSV. Zdrojový `main` tím zůstal pracovní, takže Knihovna
  správně povolila chat, ale bezpečnostní brána odmítla další zapisovací tah.
- Typ: opakující se
- Řešení nalezeno: 04082026
- Řešení: Nejdřív ukončit slovníkové aplikace, ověřit, že diff obsahuje jen
  očekávané změny `HT`, provést povinný společný audit všech tří slovníků,
  mappingů, vět a obrázků a potom změny uložit jako samostatný cílený commit.
  Tréninkový stav bez výslovného pokynu nezahazovat.

### LL-006 — Lokální katalog může omylem otevřít jen ukázková data

- Problém: Family Video Organizer v Cockpitu servíroval verzovanou veřejnou
  šablonu se třemi ukázkovými záznamy, přestože úplný soukromý balíček existoval.
  Generátor navíc nepočítal již zachované video, pokud chybělo v původním zdroji.
- Typ: opakující se
- Řešení nalezeno: 04082026
- Řešení: Lokální katalog má přednostně vybrat ověřený soukromý balíček a při
  jeho neúplnosti bezpečně spadnout na veřejnou šablonu. Po obnově balíčku
  ověřit počty dat, náhledů a skutečně existujících videí; generátor má jako
  dostupný započítat i již přítomný cílový soubor.

### LL-007 — Unit test nesmí číst živý iCloudový zdroj

- Problém: Plná checkpointová brána zůstala viset v testu hlavního stavu
  Cockpitu, protože test neizoloval načítání urgentních připomínek a sáhl do
  živého iCloudového zdroje.
- Typ: opakující se
- Řešení nalezeno: 05082026
- Řešení: Ve stavových unit testech stubovat všechny loadery napojené na externí
  nebo soukromé zdroje, včetně urgentních připomínek. Po opravě nejprve spustit
  přímo dříve visící test a potom celou plnou bránu.

### LL-008 — Modelová účtenka není důkaz serverového dokončení

- Problém: Human–Adam vystavil dokončovací účtenku a server vytvořil checkpoint,
  ale výsledek se doplnil jen do lokální odpovědi. Další modelový tah proto
  nemusel vědět, zda brána a Git operace skutečně uspěly.
- Typ: opakující se
- Řešení nalezeno: 05082026
- Řešení: Výsledek zapisovacího tahu ukládat jako samostatný redigovaný private
  serverový stav. Před dalším tahem jej ověřit proti historii `main` a čistotě
  workspace, zobrazit v Cockpitu a vložit do modelového kontextu. Neuzavřený,
  nejistý nebo neověřitelný stav nesmí nový zapisovací tah tiše přepsat.

### LL-009 — Dokončení nesmí být životně závislé na chatovém HTTP tahu

- Problém: I se správnou modelovou účtenkou a serverovou diagnostikou mohl pád
  nebo restart Cockpitu přerušit testovací bránu, checkpoint či převzetí do
  `main`; po návratu z chatu už neexistoval vykonavatel, který by přesně stejnou
  práci bezpečně dokončil.
- Typ: opakující se
- Řešení nalezeno: 05082026
- Řešení: Po přijetí platné účtenky uložit samostatnou private dokončovací úlohu
  s přesným otiskem WIP, Git základem a idempotentním klíčem. Worker běží mimo
  chatový tah, čekající úlohu obnoví po restartu a přechodnou chybu procesu
  brány zopakuje nejvýše jednou; chybu testů neopakuje. Idempotentní klíč uložený
  v commit traileru umožní dokončit zachovaný commit bez vytvoření druhého.

### LL-010 — iCloud placeholder není automaticky nové čekající doručení

- Problém: Cockpit počítal každý odložený iCloud soubor s chybou `EDEADLK` jako
  nové čekající stažení, i když už měl tentýž soubor úplně uložený v private
  indexu a připomenutí mohlo být dávno splněné. Karta proto trvale hlásila
  zaseknutý iCloud a opakovala pomalé hydratační pokusy.
- Typ: opakující se
- Řešení nalezeno: 05082026
- Řešení: Před hydratací porovnat přesnou cestu, velikost, čas změny a přítomnost
  uloženého těla. Pouze úplná shoda znamená bezpečně indexovaný nezměněný zdroj;
  nový, změněný nebo neúplný placeholder zůstává čekajícím stažením.

### LL-011 — Projektový audit nesmí tiše vydávat starý agregát za aktuální stav

- Problém: Automatické checkpointy správně aktualizovaly kanonické handoffy a
  TVBCP, ale ne souhrnný `ACTIVE_PROJECTS.md`. Systémový audit četl hlavně tento
  starší agregát, takže nové milníky opakoval jako zastaralý aktuální stav.
- Typ: opakující se
- Řešení nalezeno: 07082026
- Řešení: Před projektovým reportem porovnat Git stáří agregátu s kanonickými
  handoffy/TVBCP. Pokud je kanonická paměť novější, report musí drift viditelně
  přiznat a doporučit synchronizaci; nesmí starý souhrn prezentovat bez
  varování. Potvrzený Human–Adam checkpoint od 2026-08-07 aktualizuje handoff,
  TVBCP i primární řádek `ACTIVE_PROJECTS.md` v jediném commitu a při chybě
  trojici obnoví. Terminálové commity mimo tento workflow se dál dorovnávají
  ručně.
- Doplnění 05092026: Práce na zkratce v projektu Cockpit sama neobnovuje
  samostatný pozastavený proud Mobile Input. Jeho řádek se při práci na
  připomínkách 30082026 změnil na `active`, katalog zůstal `paused`, P2.
  Návrat pouze tohoto pole na `paused` odstranil rozpor i živou P1 kartu.
  Režim a prioritu souvisejícího proudu nepřebírat z právě vyvíjeného projektu;
  při skutečné změně režimu musí souhlasit katalog i souhrnný registr.
- Doplnění 17102026: ručně udržované podněty capability auditu nejsou zjištěné
  mezery ani aktuální úkoly. Odstranit pevné staré termíny a návrhy již hotové
  implementace; u provozního stavu odkázat na registrovaný živý audit.
  Projektový report uvede zdroj a čas podkladu odděleně od času sestavení,
  přizná neznámé stáří/neověřený provoz a při driftu nepřebírá konkrétní práci
  z agregátu. Čas commitu celého souboru není důkazem čerstvosti jeho řádků.

### LL-012 — IMAP složka s mezerou musí být při SELECT správně zakódovaná

- Problém: Trvalé mazání iCloud e-mailů z koše opakovaně selhávalo, protože
  skutečná složka `Deleted Messages` byla předána příkazu IMAP SELECT bez
  uvozovek a server ji odmítl jako chybný příkaz.
- Typ: opakující se
- Řešení nalezeno: 12082026
- Řešení: Před IMAP SELECT zakódovat název složky stejnou bezpečnou funkcí jako
  před MOVE/COPY. Při diagnostice nejdřív read-only ověřit skutečnou složku
  označenou `\\Trash` a jednoznačné nalezení kandidátů podle Message-ID; teprve
  potom opakovat samostatně potvrzené nevratné mazání.

### LL-013 — Checkpoint nemá blokovat veřejná média jen podle přípony

- Problém: Human–Adam odmítl veřejný obrázek webového prototypu, protože
  checkpoint považoval každé PNG, MP3 nebo jiné médium za citlivé bez ohledu na
  jeho skutečnou cestu.
- Typ: opakující se
- Řešení nalezeno: 12082026
- Řešení: Běžné obrázky, audio a video povolit v libovolné verzované části repa
  do 25 MiB na soubor. Nadále blokovat soukromé a env cesty i neprůhledné
  dokumenty a balíky; stejný kontrakt používat při checkpointu, převzetí i
  synchronizaci workspace z `main`.

### LL-014 — Vlákno s generovaným obrázkem může překročit rámec app-serveru

- Problém: Human–Adam se po vytvoření obrázku nedokázal znovu připojit, přestože
  Cockpit, app-server i privátní socket běžely. Obnova vlákna vrátila jeden
  WebSocket rámec o velikosti přibližně 18 MiB a klient jej odmítl původním
  limitem 8 MiB jako `MESSAGE_TOO_BIG`.
- Typ: opakující se
- Řešení nalezeno: 13082026; rozšířeno 02092026
- Řešení: U privátního Unix-socket transportu zachovat konečný limit. Původních
  32 MiB stačilo pro rámec kolem 18 MiB, ale dlouhá MMTX relace se čtyřmi dalšími
  obrazovými sadami dosáhla 46 323 050 B; ověřený limit je proto 64 MiB. Při
  podobné chybě nejdřív ověřit vnitřní příčinu WebSocket uzavření; samotná
  existence socketu a úspěšný `initialize` ještě nedokládají, že se vejde
  odpověď `thread/resume` s nahromaděnými médii.

### LL-015 — Obrazový výstup modelového tahu není automaticky kandidát chatu

- Problém: Human–Adam správně vytvořil několik `imageGeneration` výstupů, ale
  session hub persistoval pouze textovou odpověď. UI četlo jiné private
  kandidátní úložiště, takže obrázky existovaly uvnitř app-server vlákna, ale v
  chatu se nezobrazily.
- Typ: opakující se
- Řešení nalezeno: 13082026
- Řešení: Při potvrzeném dokončení tahu zachytit nejvýše osm dokončených
  obrazových položek, před veřejnou odpovědí je idempotentně a create-only
  importovat do private kandidátů a pro jednu zprávu zobrazit galerii. Base64
  data ani lokální cesty nepersistovat do session JSON a nevystavovat přes API.

### LL-016 — Retence podle dnů neomezuje autosave dlouhé relace

- Problém: Autosave každých deset minut ukládal celou rostoucí Codex relaci a
  třídenní retence proto chránila stovky téměř shodných velkých kopií. Ruční
  úklid fungoval, ale při dlouhé relaci uvolnil jen malou část prostoru.
- Typ: opakující se
- Řešení nalezeno: 14082026
- Řešení: Aktuální `latest` obnovu dál přepisovat každých deset minut, historický
  JSONL/TXT pár vytvářet nejvýše jednou za hodinu a po každém autosave
  automaticky ponechat pouze 12 nejnovějších časů. Stav autosave současně hlásí
  varování pod 30 GiB a kritický stav pod 15 GiB volného místa.

### LL-017 — Logická velikost souborů není zaručený zisk volného místa na APFS

- Problém: Cleanup správně smazal potvrzenou sadu starých autosave souborů, ale
  odhad uvolnění vznikl součtem jejich logických velikostí. Volné místo na SSD
  proto nevzrostlo o hlášený součet; copy-on-write bloky mohly být sdílené a
  souběžně místo používaly cache, VM/swap a otevřené smazané soubory.
- Typ: opakující se
- Řešení nalezeno: 15082026
- Řešení: Před cleanupem i po něm odděleně měřit logickou velikost, fyzicky
  alokované bloky a `df`. Uživatelům nikdy neslibovat logický součet jako
  skutečně uvolnitelné GiB. Proměnlivé cache a VM ověřit znovu po restartu;
  CloudKit ani jiné systémové cache nemazat automaticky.

### LL-018 — Dokončený app-server tah může ztratit transportní účtenku

- Problém: Codex lokálně dokončil tah a uložil finální odpověď i `task_complete`,
  ale Human–Adam neobdržel povinné `turn/completed` a správně ponechal doručení
  jako nejisté. Opakované odeslání by mohlo zdvojit už provedenou práci.
- Typ: opakující se
- Řešení nalezeno: 16082026
- Řešení: Zprávu nikdy automaticky neposílat znovu. Po transportní chybě přijmout
  dokončení jen z právě jednoho lokálního záznamu se shodným vláknem a client
  ID, shodnou finální odpovědí a následným `task_complete`; při jakékoli
  nejednoznačnosti zachovat `delivery_unknown` a vyžádat ruční recovery audit.

### LL-019 — Finální app-server událost nemusí opakovat vstupní položku

- Problém: Codex 0.147 poslal správnou `userMessage` přes `item/completed`, ale
  finální `turn/completed` obsahoval pouze výstupní položky. Klient dříve
  ověřený vstup zahodil, dokončený tah označil za nejistý a uzavřel spojení.
- Typ: opakující se
- Řešení nalezeno: 16082026
- Řešení: Zachovat dříve přijatou `userMessage` pouze při přesné shodě
  `clientId` a jen pokud finální tah neobsahuje žádnou uživatelskou položku.
  Pokud finále uživatelskou položku obsahuje, použít ji autoritativně a při
  neshodě dál selhat uzavřeně.

### LL-020 — Lokální pomocná aplikace se z iPhonu otevírá pod původem Cockpitu

- Problém: Cockpit mohl na Macu otevřít ScanDocu přes `127.0.0.1:8766`, ale na
  iPhonu stejná adresa ukazuje na telefon. Omezená náhradní revize přímo v kartě
  Cockpitu zároveň neukázala celý dokument a všechny nástroje ScanDocu.
- Typ: opakující se
- Řešení nalezeno: 22082026
- Řešení: Plné rozhraní lokální pomocné aplikace vést přes úzce allowlistovaný
  same-origin průchod pod Cockpitem. Konkrétní položku předávat jen neprůhledným
  bezpečným odkazem a na backendu jej znovu vyhodnotit proti kanonickému indexu;
  do klienta neposílat interní cestu ani skutečný identifikátor dokumentu.

### LL-021 — Historický handoff není aktuální ToDo

- Problém: Přehled „Co teď?“ doplňoval volná místa do pevného počtu tří kroků
  také z historických handoffů. Dokončené nebo neověřené návrhy tak vypadaly
  stejně závazně jako položky ze živé provozní fronty.
- Typ: opakující se
- Řešení nalezeno: 28082026
- Řešení: Aktuální ToDo sestavovat pouze z živé fronty a živě prokázaných
  rozporů. Handoffové kroky zobrazit odděleně jako návrhy z projektové paměti,
  vždy se zdrojem a stářím důkazu; počet aktuálních úkolů nikdy nedoplňovat na
  předem dané číslo.

### LL-022 — Push webových souborů není důkaz GitHub Pages publikace

- Problém: Nový VocabularyEN commit byl čistě na `main` i `origin/main`, ale
  poslední Pages workflow běželo nad starším commitem. Veřejná aplikace proto
  nový audio manifest a MP3 ještě neobsahovala.
- Typ: opakující se
- Řešení nalezeno: 29082026
- Řešení: Před tvrzením o produkci porovnat commit posledního úspěšného Pages
  workflow s cílovým commitem. Při neshodě spustit ruční Pages workflow a po
  jeho úspěchu nezávisle ověřit veřejný HTTP stav i shodu hashů manifestu,
  aplikačního JavaScriptu a reprezentativních assetů.

### LL-023 — Pages workflow může uspět dříve než úplná produkční účtenka

- Problém: GitHub workflow správně publikoval cílový commit, ale deployment se
  v API objevil o několik sekund později a lokální Python `urllib` navíc neměl
  použitelný certifikační řetězec. Produkce běžela, zatímco serverová účtenka
  dvakrát správně zůstala fail-closed.
- Typ: opakující se
- Řešení nalezeno: 29082026
- Řešení: Po dokončení přesného workflow omezeně čekat na success deployment
  stejného commitu a závěrečný HTTPS smoke provést přes systémový curl. Nejasný
  výsledek nikdy automaticky neopakovat; nejprve korelovat workflow ID,
  deployment ID, commit a veřejný HTTP stav.

### LL-024 — Server-owned operaci nesmí autorizovat ani blokovat modelová obálka

- Problém: Přesný uživatelský `p+n` byl správně autorizovaný, ale vadná
  modelová provozní obálka jej zablokovala ještě před serverovým backendem.
- Typ: opakující se
- Řešení nalezeno: 29082026
- Řešení: Pro přesný příkaz a deklarovaný produkční cíl vytvořit kanonický
  serverový požadavek bez ohledu na chybějící, platnou nebo vadnou modelovou
  obálku. Model smí dodat pouze viditelný text; autorizaci, volbu operace a
  produkční účtenku vlastní server.

### LL-025 — Python HTTPS klient na tomto Macu potřebuje projektový CA bundle

- Problém: Nový GitHub API klient přes `urllib` selhal na
  `CERTIFICATE_VERIFY_FAILED`, i když systémový `curl` stejné HTTPS API ověřil.
- Typ: opakující se
- Řešení nalezeno: 30082026
- Řešení: U dlouhodobého Python klienta vytvořit explicitní TLS context přes
  `ssl.create_default_context(cafile=certifi.where())`; chybu dál hlásit
  redigovaně a fail-closed. Systémový `curl` ponechat pro omezené diagnostické
  ověření, ne jako skrytý runtime fallback zapisovacího workflow.

### LL-026 — Unit test lokálního indexu nesmí dědit živý GitHub inbox

- Problém: Dva testy lokálního přehledu připomenutí zavolaly produkční GitHub
  synchronizaci z `.env`; otevřená skutečná Issue změnila jejich dočasné počty.
- Typ: opakující se
- Řešení nalezeno: 30082026
- Řešení: V každém unit testu lokálního indexu výslovně nahradit externí GitHub
  synchronizaci deterministickým neaktivním výsledkem. Živý inbox patří jen do
  samostatného integračního testu s přesnou korelací a bezpečnostními hranami.

### LL-027 — Migrace transkripce není jen výměna názvu modelu

- Problém: Nový `gpt-transcribe` používá místo jednoho `language` strukturovaná
  pole `languages` a `keywords`; lokální SDK je ještě nemusí mít v běžném
  podpisu a záložní multipartová `curl` cesta potřebuje správné názvy polí.
- Typ: opakující se
- Řešení nalezeno: 31082026
- Řešení: Zachovat endpoint i výstupní kontrakt, nová pole v SDK poslat přes
  `extra_body` a v multipart formuláři jako opakovaná `languages[]` a
  `keywords[]`. Ověřit obě cesty unit testy a jediným syntetickým API smoke bez
  soukromého audia; u klíčových slov následně hlídat i možné vložení
  nevysloveného termínu.

### LL-028 — Citlivý dokument nesmí automaticky zdědit plný OCR index

- Problém: Standardní import dokumentu ukládá extrahovaný text do soukromého
  fulltextového indexu. U bankovní smlouvy by tím zbytečně duplikoval rodné
  číslo, adresu a aktivační údaj, přestože pro hledání stačí bezpečný souhrn.
- Typ: opakující se
- Řešení nalezeno: 31082026
- Řešení: Pro citlivé bankovní dokumenty použít restricted import. Originál
  zachovat v private vaultu, úplné účetní identifikátory uložit jen do
  samostatných restricted metadat a do běžného indexu zapsat pouze maskovaný
  text. Surový OCR text, rodné číslo, adresu a aktivační údaje neindexovat ani
  neduplikovat do metadat.

### LL-029 — Přímý curl klient nesmí opakovat každou chybu 429 nebo 503

- Problém: Přímá multipartová cesta hlasového přepisu přes systémový `curl`
  neznala HTTP stav ani `Retry-After`; obecné opakování všech chyb by navíc
  zbytečně opakovalo kvótové a platební chyby.
- Typ: opakující se
- Řešení nalezeno: 03092026
- Řešení: Z odpovědi odděleně načíst pouze HTTP stav a `Retry-After`, opakovat
  nejvýše třikrát jen přesné dvojice `429/slow_down` a
  `503/server_is_overloaded`, bez hlavičky použít krátký exponenciální backoff
  s jitterem a celý běh držet v jednom časovém rozpočtu. Do logu propustit jen
  stav, kód, číslo pokusu a čekání; nikdy klíč, audio ani celé tělo chyby.

### LL-030 — Projektové audio a skutečné asociace Apple Music

- Problém: Opravený generátor s `afplay` nezabránil dalším importům pracovního
  audia při obecném otevření nebo dvojkliku; Music byla výchozí aplikací.
- Typ: opakující se
- Řešení nalezeno: 05092026
- Řešení: Projektové audio přehrávat explicitně přes `afplay`, browser nebo
  QuickTime. Po schválené změně asociací ověřit skutečnou aplikaci pro konkrétní
  soubor přes NSWorkspace, nestačí návratový kód nastavení. M4A na tomto Macu
  používá `com.apple.m4a-audio`, ne pouze `public.mpeg-4-audio`. Před úklidem
  Music sestavit seznam podle persistent ID, zachovat audio a ověřit ostatní
  záznamy i playlisty před/po; chybějící místní soubor neznamená chybějící
  záznam knihovny. Podrobnosti jsou v handoffu z 2026-09-05.

### LL-031 — Chybná výslovnost jedné hotové slovníkové MP3

- Problém: Aria četla samostatné `cat` jako jméno Kate; správný text v CSV
  ani opakované generování s interpunkcí chybu neodstranily.
- Typ: opakující se
- Řešení nalezeno: 05092026
- Řešení: pro anglické `cat` použít cílenou výjimku hlasu Jenny v generátoru
  a manifestu. Strojový přepis se změnil z `Kate.` na `Cat.`; poslech na
  cílovém zařízení zůstává závěrečnou kontrolou. Výjimku udržet při rebuild,
  zachovat učební text a změnit adresu MP3 kvůli cache. Testy ověřily úzký
  rozsah a opakované sestavení bez dalších generování. Publikaci Pages
  prokazovat zvlášť podle LL-022.

### LL-032 — Směr překladu nesmí resetovat historii losovaných karet

- Problém: VocabularyEN zahrnoval směr překladu do identity vybrané sady.
  Přepnutí směru proto při dalším losování vymazalo historii a mohlo vrátit
  již zobrazenou kartu před vyčerpáním sady. Počítadlo navíc nikdy neukázalo
  nulu a přechod do dalšího kola nebyl viditelný.
- Typ: opakující se
- Řešení nalezeno: 05092026
- Řešení: identitu sady odvozovat z filtru, okruhů a ID karet; směr mění jen
  zobrazení. Počítat dosud nezobrazená ID, oznámit konec kola a zamezit
  bezprostřednímu opakování při přechodu mezi koly. Reprodukční testy ověřily
  opravu i tři celá kola se změnami směru. Shodný text u různých významů
  není opakování stejné karty.

### LL-033 — Audit MMTX musí zahrnout i dialogy bez slovníčku

- Problém: Import kontrolující jen čtyři historické slovníčky hlásil úplnost,
  přestože v mluvených textech dalších scén, školních pokynech a narozeninách
  chybělo ve VocabularyEN 120 základních hesel.
- Typ: opakující se
- Řešení nalezeno: 05092026
- Řešení: porovnat i anglické klíče audio manifestů a deklarované texty
  úvodu/narozenin; ověřit shodu zdrojů s veřejným MMTX. Tvary slov mapovat
  explicitně, jména a domluvené výjimky zachovat. Nové heslo musí mít
  kurátorský CZ, Sentence, SentenceT, Benji a audio; neznámé budoucí slovo
  blokuje falešné hlášení úplnosti. Po doplnění prošel audit bez mezer,
  30 cílených testů a dekódování všech 239 nových MP3.

### LL-034 — Prázdný autosave TXT neznamená chybějící historii

- Problém: latest_session.txt obsahoval pouze hlavičku, přestože JSONL
  obsahoval přerušené zadání a důkazy uložených obrázků.
- Typ: opakující se
- Řešení nalezeno: 06092026
- Řešení: při povolené obnově číst zprávy response_item/message z JSONL,
  nikoli spoléhat jen na TXT export. Nevypisovat obrazové base64 ani celé
  interní obálky. Stav následně ověřit podle manifestu, receipts a souborů;
  poslední lidská zpráva hlásila 45 obrázků, na disku již bylo 47. Díky
  této kontrole se dogenerovaly pouze dvě zbývající položky z 49.


## 2026-09-06 — Oddělení offline lekcí bez ztráty postupu

- Typ: opakujici se.
- Problém: postup ukládaný podle číselné pozice by po přeuspořádání lekcí
  přiřadil rozepsaný kód jinému tématu.
- Řešení: trvalá ID v balíčku i postupu; migraci odvozovat z pevné původní
  mapy sedmi lekcí, nikoli z nového pořadí. Původní data zachovat, nový formát
  ukládat samostatně s byte-for-byte zálohou a detekcí konfliktu.
- Ověření: PythonSeSamanthou, 27 testů a skutečné Tk GUI; znovuotevření
  s obráceným pořadím zachovalo výběr, sedm pokusů i dokončení. Testy pouze
  nad dočasnými daty, žádný zásah do Mílova skutečného postupu.
- Další ověření 2026-09-06: třetí balíček byl přidán pouze do kurzy původního
  vydaného ZIPu 1.5. GUI dokončilo všech sedm lekcí a obnovilo postup; kontrolní
  porovnání zachovalo všech 79 původních distribuovaných souborů. Kompatibilitu
  nového obsahu dokazovat i proti skutečně vydané aplikaci, nejen aktuálním zdrojům.


## 2026-09-06 — Samostatný projekt versus pracovní proud Cockpitu

- Typ: opakujici se.
- Problém: nový aktivní tabulkový řádek v ACTIVE_PROJECTS automaticky podléhá
  invariantě úplnosti katalogu pracovních proudů. U samostatné učebny bez
  Cockpit integrace tak test katalogu odhalil chybějící vazbu.
- Řešení: samostatný terminálový projekt vést explicitně v textové části
  registru a přes index, projektovou paměť a handoff. Do tabulky pracovních
  proudů ho zařadit až spolu se skutečně dohodnutou integrací; nezakládat
  implicitně TVBCP jen kvůli registraci aplikace.
- Ověření: po přesunutí záznamu Python se Samanthou prošlo všech 28 testů
  test_human_adam_workstream_catalog a test_project_audit_report. Při příštím
  přidávání projektu spustit tyto testy až po finální úpravě registru.

## 2026-09-06 — Přenosný Python HTTPS klient bez pip závislostí na macOS

- Typ: opakujici se.
- Problém: Python.org instalace neměla CA bundle; urllib skončil na
  CERTIFICATE_VERIFY_FAILED. Souvisí s LL-025, zde však aplikace nesmí
  vyžadovat instalaci certifi na uživatelském Linuxu.
- Řešení: zachovat ssl.create_default_context() a na macOS přidat existující
  systémový /etc/ssl/cert.pem přes load_verify_locations. Na Linuxu ponechat
  standardní CA; nevypínat ověřování certifikátů a neměnit systémovou instalaci.
- Ověření: PythonSeSamanthou 1.4, skutečný HTTPS požadavek do OpenAI i navazující
  otázka prošly po této změně. Klíč ani osobní data se při ověření nevypisovaly.

## 2026-09-06 — Codex tutor přes ChatGPT nesmí tiše použít API přihlášení

- Typ: opakujici se.
- Problém: automatický Codex může dědit jiný způsob autentizace a API proměnné.
  Samotné forced_login_method může podle dokumentace odhlásit neslučitelný login.
- Řešení: před dotazem nejprve codex login status bez vynucení; API/unknown login
  odmítnout bez spuštění a bez logoutu. Až pro ověřené ChatGPT použít explicitní
  forced_login_method, čisté prostředí bez API proměnných a --ignore-user-config.
- Ověření: PythonSeSamanthou 1.5, testy odmítnutí API bez mutace přihlášení,
  skutečné ChatGPT Codex vysvětlení/doptání i odpověď v Tk okně na Macu.


## 2026-09-08 — Přerušitelná zvuková sekvence v Tk

- Typ: opakujici se.
- Problém: trénink musí čekat na dočtení věty a při změně výběru zabránit
  starým timerům pokračovat v nové sekvenci.
- Řešení: jeden vlastněný audio proces, jeden Tk timer a generační identita
  callbacku; při pauze nebo přepnutí zrušit timer i vlastní proces. Pokračování
  znovu přehraje přerušenou výpověď. Žádné globální ukončování přehrávačů.
- Ověření: testy čekání na audio, pauzy, pozdního callbacku, chyby hlasu a
  skutečný Tk průchod v Tréninku sloves; macOS Thomas dokončil ukázku.


## 2026-09-08 — Ověření samostatné VocabularyFR.app pro sdílený iCloud

- Typ: opakujici se.
- Problém: úspěšný zdrojový Tk běh nedokazuje správně zabalená data; PyInstaller
  onedir používá odkazy Frameworks → Resources. Finder může pod Desktopem
  přidávat metadata odmítaná strict codesign i po očištění.
- Řešení: nový izolovaný build ideálně v /private/tmp, kontrolovat skutečnou
  .app na dočasné kopii seedů, respektovat resource odkazy a ověřit podpis.
  Janina edice výslovně předává --data-dir vedle .app; nepřepíná na jiný CSV.
- Ověření: aktuální bundle prošel strict podpisem; z místní sdílené kopie
  fungovalo 406 řádků, 107 ilustrací a psaný recall. Data a stará .app nejprve
  zálohované, přenos porovnaný včetně odkazů a SHA-256.


### 2026-09-10 – Přehled terminálových relací Codexu
- Typ: opakující se.
- Problém: hledání podřetězce `codex` označovalo screen/shell a podpůrné procesy za konverzace; OS cwd skutečného Codexu navíc nemusí odpovídat projektu.
- Ověřené řešení: rozlišit nativní spustitelný soubor a argumenty služby, ověřit TTY a vlastnictví, projekt odvodit i z `-C` / `--cd`. Před potvrzeným signálem obnovit identitu včetně času startu; předky správce chránit. Prohlížečový test ukončení používal jen vlastní syntetické procesy.


### Screen na macOS obsahuje systémový login obal

- Problém: Kontrola vlastníka všech potomků odmítala běžný vlastní screen, protože macOS mezi něj a uživatelský program vkládá root proces login.
- Typ: opakující se
- Řešení nalezeno: 2026-09-12 08:31 CEST
- Řešení: Ověřit vlastního správce screenu a úzce rozpoznat přímého potomka login s přesnými argumenty pro stejného uživatele a ověřeným spustitelným souborem. Ostatní cizí procesy, Codex a služby zůstanou chráněné; před uzavřením znovu ověřit identitu i členství. Prohlížečový test se skutečným testovacím screenem prošel.


### 2026-09-12 – Ovládání MMTX musí sledovat skutečnou velikost obrazu

- Typ: opakující se.
- Problém: scéna s pevným poměrem stran může být kvůli výšce okna výrazně užší než viewport; samotný mobilní media query pak nechá příliš velký dialog a tlačítka zakryjí postavy.
- Řešení: rozložení odvodit od šířky kontejneru scény, zkrátit dialogovou kartu a v závěrečném obrazu umístit ovládání do volné části. Kontrolovat skutečné obdélníky prvků i screenshot, nejen průchod JavaScriptu.
- Ověření: scéna 5 prošla celým příběhem a pěti rozměry 1440×1000 až 390×844; dialog se nekříží s tlačítky a všech šest postav závěru je viditelných.


### 2026-09-12 – Počet objektů musí souhlasit i v přechodovém obrázku

- Typ: opakující se.
- Problém: tři správně animované klády překryl obraz hotového mostu jen se dvěma kládami; třetí se vizuálně objevila až v dalším obrazu. Samotný počet DOM prvků chybu neodhalil.
- Řešení: opravovat konkrétní překrývající ilustraci a při vizuálním retestu kontrolovat okamžik po animaci před následujícím krokem. Při výměně pod stejným názvem změnit verzi URL v preloadu i src.
- Ověření: browserový screenshot po třetím klepnutí před Benjiho přechodem ukazuje tři klády; veřejný WebP po publikaci přesně odpovídá opravenému souboru.


### LL-035 — Zkrácení instrukcí při zachování projektového kontraktu

- Problém: vstupní instrukce duplikovaly handoff návody; recovery navíc
  používalo slovní priority, zatímco AGENTS.md vyžadovalo 1–3.
- Typ: opakující se
- Řešení nalezeno: 12092026
- Řešení: jediný postup handoffu v session_recovery_rules.md, kontrakt TVBCP
  v project_tvbcp_rules.md a krátké situační odkazy z AGENTS.md. Při přesunu
  ověřit zachování povinností, platnost odkazů a původních historických zápisů.
  Rozlišovat terminálový commit od oprávnění modelu v Cockpitu. Změna Markdownu
  sama nedokazuje změnu serverových promptů ani zrychlení modelu.
- Ověření: 41 cílených testů, rychlá brána a kontrola odkazů prošly;
  bezpečnostní návody i historické záznamy zůstaly beze změn.
- Doplnění 2026-09-12: serverové prompty je nutné ověřit na skutečné cestě
  přes profilovou/lazy factory a start/resume vlákna. Starý zákaz TVBCP zápisu
  při milníku odporoval povinnému projektovému zápisu; nahrazen zápisem pouze
  při writable=true do správné kanonické dvojice, bez oprávnění ke commitu.
  Cílená sada 198 testů prošla. Aktivaci dokládá až samostatné nasazení a
  načtení nových instrukcí, nikoli samotný commit nebo zarovnání workspace.


### LL-036 — Fotografie na pozadí potřebují pevný cíl a bezpečné opakování

- Problém: limit původního snímku blokoval upload ještě před zmenšením; čekání
  na foto brzdilo novou kartu. Souběžné připojení a editace mohou přepsat metadata.
- Typ: opakující se
- Řešení nalezeno: 12092026
- Řešení: připravovat ihned po výběru mimo UI vlákno, kartu uložit samostatně
  a fotografii navázat na její neměnné ID. Opakovaný request musí mít stejné ID
  a kontrolu obsahu; archivní zápisy serializovat, registry zapisovat atomicky.
  Přenos po zavření stránky neslibovat. Při skrytí formulářových polí ověřit
  vypočtený display: pozdější display:grid může přebít obecné .hidden.
- Ověření: velké PNG/HEIC, ztracená odpověď po uložení bez duplicit, dvě karty,
  souběžná editace, neblokující obálka nové knihy a computed display desktop/mobil
  prošly na syntetických datech; 0 chyb JavaScriptu.

- Doplnění 2026-09-12 k LL-036: limit uploadu neomezuje celkové úložiště,
  pokud backend ještě ukládá originál, čitelnou kopii a náhled. Pro ilustrace
  použít jeden JPEG do 285 KiB a náhled do 20 KiB, při měření deduplikovat
  skutečné cesty. Zachovat zvláštní vyšší kvalitu dočasného OCR a podporovat
  také camera JPEG/MPO. Převod starých dat musí kontrolovat otisky i shodu
  metadat s registrem a mít ověřenou obnovu; úspora aktivního archivu není
  úsporou disku, pokud zůstává jednorázová záloha. Ověřeno testy a browserem.


### 2026-09-13 12:45 CEST — Připojení screenu zachovává běžící Codex

- Typ: opakující se.
- Problém: Po zavření terminálu může screen s Codexem pokračovat, ale uživatel k němu nemá otevřené okno. Úspěšné předání URI editoru samo neprokazuje připojení.
- Ověřené řešení: Rozlišit obnovu od ukončení a od `codex resume`; ověřený screen spustit přímo jako terminál VS Code přes `screen -d -r <socket>`. Připojený stav vyžaduje potvrzení převzetí. PID/start a ochrany ověřit znovu při jednorázovém převzetí.
- Ověření: Vývojové okno skutečného VS Code připojilo vlastní testovací screen a zachovalo PID screenu i vnitřních procesů. UI test používá náhradní DOM; skutečný první klik z Cockpitu zůstává samostatným ověřením.

Doplnění 12112026 — obnova Data po restartu ve druhém okně VS Code:
- Nejdřív `screen -ls` a kontrola běžících Codex procesů. Existující vlastní
  screen pouze připojit; po restartu Macu může zůstat jen obnovená historie
  terminálu, nikoli živá relace. Druhé okno vybrat přes nabídku Okno;
  Adamův terminál nenahrazovat ani nerozdělovat místo samostatného okna.
- Pokud `data_codex` chybí, určit poslední Datovu relaci podle `session_meta.cwd`
  v uložených JSONL a posledního tématu. Staré ID z paměti ani popisek TTY nejsou
  autoritativní: Data mezitím použil `/new`. Ověřit správný worktree a větev.
- Ve volném shellu druhého okna spustit
  `/usr/bin/screen -U -S data_codex /usr/local/bin/codex -C <Datův-worktree> resume <ověřené-session-id>`.
  Pro již běžící screen použít `screen -d -r data_codex`, nevytvářet druhý Codex.
  Volitelnou nabídku aktualizace při obnově přeskočit volbou Skip; neposílat
  nový pracovní pokyn jen kvůli otevření uložené konverzace.
- Prakticky ověřeno: obě samostatná okna VS Code, oba screeny Attached,
  Datův proces se správným ID a worktree na `data/parallel-20261104` a viditelná
  poslední odpověď s plánem Human–Adam i připravený vstup. Oba checkouty čisté;
  kód a služby nezměněné. Screen přežije odpojení terminálu, nikoli restart Macu.

### 2026-09-13 – Viditelná šipka může být zakrytá úvodním audio panelem

- Problém: návrat ve scénách MMTX 4 a 5 byl vidět, ale úvodní audio překryv zachytával kliknutí. Samotná kontrola href ani viditelnosti chybu neodhalila.
- Řešení: ovládací vrstvu umístit nad audio překryv a zachovat průhlednost ke kliknutí mimo tlačítka. Ověřit skutečný klik ještě před spuštěním příběhu.
- Ověření: návraty 4 → 3 a 5 → 4 prošly bez spuštění audia v desktopovém i mobilním viewportu. Celá navigační sada prošla 18/18.

### 2026-09-13 — Pomalou bránu zrychlovat podle měření skupin

- Problém: celkový čas plné brány neukazuje, zda zdržuje frontend, Git integrace nebo společná příprava; vede k neúčelnému opakování či škrtání testů.
- Typ: opakující se.
- Řešení: volitelné `--unit-test-timings PATH` nad kanonickou bránou zachová stejný manifest, pořadí a výsledky; report obsahuje jen názvy, počty a časy. Testový setUp/tearDown je v čase testu, importy a společná režie zvlášť. Běžné změny ověřovat cíleně; povinné rizikové/release brány zachovat.
- Ověření: 1649/1649 v jediném plném běhu; 88 Git/workspace testů zabralo 73,5 % času. Gate/smoke uvnitř pomalých testů jsou nahrazené. Podíl tvorby repozitáře a samotných Git operací vyžaduje další dílčí měření, nelze jej vydávat za doloženou příčinu nebo hotovou úsporu.
- Navazující ověření téhož dne: dva deploy testy mají přibližně třetinu času ve společné přípravě a 98 % v Git procesech celkem. Dokončit syntetický zdroj před klonováním ušetří druhý úvodní push/sync (87 → 53 procesů přípravy), bez cache či změn vlastních scénářů. Osm měřených běhů před/po a test nezávislosti dvou sad prošly; report `reports/cockpit_deploy_fixture_pilot_2026_09_13.md`. Plná brána 1650/1650 prošla. Nízký počet vzorků ani úspora jedné fixture nejsou záruka stejného zrychlení celé brány.

### 2026-09-13 — U nákladných Git testů změřit i systémový spouštěč

- Problém: Git integrační testy zabírají většinu brány; odstranění několika přípravných operací samo nezaručuje významné zrychlení celku.
- Typ: opakující se.
- Řešení: porovnat stejný dotaz přes `/usr/bin/git` a Git vybraný pomocí `xcrun --find git`. Na Macu lze jednou při startu zjistit platnou absolutní cestu a používat ji se stejnými parametry. Při nedostupnosti, chybě, timeoutu a mimo Mac zachovat původní cestu. Nejde o cache stavu ani o důvod škrtat testy; po změně vybraného toolchainu restart procesu.
- Ověření: stejný Apple Git, medián 33 vs 12 ms ve 30 vzorcích na kombinaci; sedm cílených testů prošlo. Stejných 1655/1655 testů prošlo před i po; unittest 453,73 → 340,30 s, úspora 113,43 s (25,0 %). Report `reports/cockpit_git_launcher_2026_09_13.md`; jeden pár úplných běhů není záruka stejné úspory na jiném stroji.
- Navazující ověření 14. 9.: sdílet jednou zjištěnou binárku také v checkpoint/deploy/batch/sync/takeover a společném Git test helperu; samostatné launchery jinak dál platí tutéž režii. Stejných 1656/1656 testů prošlo před i po; 307,14 → 261,43 s, úspora 45,71 s (14,88 % proti dnešnímu výchozímu stavu). Report `reports/cockpit_shared_git_2026_09_14.md`. Nový společný modul zařazen do povinné plné brány.

### 2026-09-14 — Při přesunu HTTP obsluh zachovat i kontrolní hranice

- Problém: přesun obsluhy z hlavního serveru může nechtěně změnit chybové odpovědi, hlavičky či pořadí autorizace; nový soubor také vypadne z původního CI/gate filtru.
- Typ: opakující se.
- Řešení: před přesunem zachytit HTTP kontrakty na izolovaném serveru se syntetickými daty, po přesunu porovnat stav/hlavičky/otisk těla. Ověřit odmítnutí před voláním backendu a skutečné vnější cesty/symlinky. Zahrnout nový modul do CI, kompilace a stejné povinné brány jako původní soubor. Před plným během rozšířit také existující inventuru adres frontendu o skutečný dispatch nového modulu.
- Ověření: dokumentový řez, 61/61 shodných HTTP kontraktů; 35 cílených testů a plná brána 1665/1665. Report `reports/cockpit_document_routes_2026_09_14.md`.
- Navazující ověření: archivační HTTP řez zachoval 53/53 kontraktů včetně MIME/disposition vložených příloh a čtení syntetického EML přes neprůhlednou referenci. Inventura adres aktualizovaná již před plnou bránou; 49 cílených testů a 1675/1675 celé sady. Report `reports/cockpit_email_archive_routes_2026_09_14.md`.

### 2026-09-14 — Grid panel může zabránit skutečnému posouvání potomka
- Projev: desktopový archiv má overflow-y:auto, ale seznam se roztáhne na celý obsah a scrollTop zůstává 0; body overflow:hidden skryje dolní zprávy.
- Příčina a řešení: automatické minimum nadřazených grid panelů; nastavit min-height:0 na panel seznamu i čtečky. Mobil již tuto hodnotu měl.
- Ověření: browser s dlouhým syntetickým seznamem, skutečný wheel posun až na poslední položku, otevření/detail/návrat a mobilní regrese. Samotná přítomnost overflow v CSS nestačí. Důkaz: reports/cockpit_email_archive_scroll_2026_09_14.md.

### 2026-09-14 11:53 CEST — Společná odezva nesmí záviset na otevřeném detailu
- Projev: akce zapíše zprávu, ale člověk ji nevidí, protože předek je zavřený details nebo překrytý dialogem.
- Řešení: společný panel nezávislý na scrollu a detailech; při modalu přesunout i live region do jeho přístupnostní oblasti. Zobrazení nesmí krást fokus, chyba nesmí sama zmizet.
- Ověření: skutečná viditelnost a překrytí přes elementFromPoint, zavřený detail, aktivní dialog, dlouhý text, blokovaný popup a síťová chyba; samotný textContent ani z-index nestačí. Důkaz: reports/cockpit_ui_u01_2026_09_14.json.

### 2026-09-14 14:18 CEST — Návrat a popup potřebují dostupnou náhradní cestu
- Projev: nákupní čtečka pouze zaměřovala opener; samostatná karta neměla návrat. Zablokovaný popup ukázal jen textovou adresu.
- Řešení: s openerem zaměřit původní okno a zavřít čtečku, bez něj navigovat na Cockpit; při odmítnutém zavření dát instrukci. Náhradní popup odkaz otevřít uživatelským kliknutím v nové kartě bez openeru, přijímat pouze HTTP(S).
- Ověření: samostatná i skutečně otevřená popup karta, uzavřený/nedostupný opener, odmítnuté zavření, zachovaný rozepsaný vstup a odstranění starého odkazu při další zprávě. Důkaz: reports/cockpit_ui_u02_2026_09_14.json.

### 2026-09-14 14:44 CEST — Kompaktní prázdný stav nesmí schovat chybu
- Projev: sbalení podle pouhého count=0 může skrýt selhání poskytovatele; grid se stretch zase natahuje nulové sousedy podle dlouhé fronty.
- Řešení: rozlišit ověřené prázdno, práci a chybu. Nuly sbalit, chyby/práci otevřít při změně stavu; stejný stav respektuje ruční rozbalení. Použít align-items:start a u dlouhých seznamů ověřit skutečné posouvání včetně klávesnice.
- Ověření: nedostupný zdroj a HTTP/provider chyba revize se zobrazí; poslední položka i původní akce zůstávají dosažitelné. Report: reports/cockpit_ui_u03_2026_09_14.json.

### 2026-09-14 15:11 CEST — Stránkování potřebuje HTTP propojení i ochranu před starou odpovědí
- Projev: backend umí offset, ale HTTP ho nepředá; uživatel zůstane na první stránce. Pomalá odpověď navíc může přepsat novější dotaz.
- Řešení: validovat parametry před poskytovatelem, předat limit/offset a použít pořadí požadavků v UI. Při chybě další stránky zachovat předchozí data a retry; nový dotaz resetuje stránku.
- Ověření: skutečné HTTP nad více než jednou stránkou včetně duplicitního indexového řádku, mimo rozsah, chyby a dotaz změněný během načítání. Návrat čtečky i blokovaný popup musí zachovat původní hledání. Důkaz: reports/cockpit_ui_u04_2026_09_14.json.

### 2026-09-14 15:25 CEST — Čekající práce není provozní porucha
- Projev: nové dokumenty, poznámky nebo čistý Git napřed drží hlavní přehled trvale ve varování; skutečná chyba zaniká.
- Řešení: použít existující prioritní frontu, práci hodnotit odděleně od provozu a chybějící zdroj neproměňovat v prázdný zelený inbox. Při selhání obnovy priorit odstranit zastaralé akční karty, ukázat neověřený stav a umožnit nové načtení.
- Ověření: syntetická práce, konflikt, divergence, chybějící záloha, výpadek/obnova API a zdroj/čas důkazu. Report: reports/cockpit_ui_u05_2026_09_14.json.

### 2026-09-14 18:36 CEST — Zavření dialogu není zahození rozepsané práce
- Projev: pevný seznam Escape zavře jinou vrstvu, Tab uteče za dialog a close/reopen vyčistí editor. Plovoucí návrat navíc může překrýt společná odezva.
- Řešení: jeden správce viditelných vrstev, původního fokusu a inertního pozadí; volat existující close obsluhy, uchovat drafty v DOM a reset ponechat explicitní. Návrat navázaný na hledání umístit k hledání.
- Ověření: skutečné Tab/Shift+Tab/Escape, vnořený náhled a Recovery, Janiččiny projekty/hledání se zobrazenou odezvou, draft nové i existující položky a hash/reload. Pouhý textContent neprokazuje dostupnost návratu. Report: reports/cockpit_ui_u06_2026_09_14.json.
- Doplnění 17102026: při členění Servisu zachovat DOM ID akcí a vracení fokusu, odstranit jen duplicitní zkratky včetně jejich bindingů. Nativní details ověřit Enter/mezerníkem; na 320 px zkoušet i rozbalené dlouhé výpisy a tabulku, protože overflow:hidden může obsah skrýt. Potvrzení zkoušet zrušením nad výhradně testovacími API. Report: reports/cockpit_ui_u07_2026_10_17.json.

### LL-037 — Podepisovaný iOS build mimo synchronizovanou Plochu

- Problém: CodeSign nad novým .app na Ploše selhal na resource fork/Finder information; inventura potvrdila FinderInfo.
- Typ: opakující se
- Řešení nalezeno: 15092026
- Řešení: nový DerivedData v /private/tmp, bez plošného mazání xattr ze zdrojů. Podepsaný build a codesign --verify --deep --strict prošly. Tým patří do ignorovaného LocalSigning.xcconfig.

### 2026-09-15 — Přerušení audia musí ukončit také stav přehrávání

- Kontext: Camino C01a, společná obsluha systémové události pro recorder a player.
- Problém: guard pouze pro záznam ignoroval přerušení poslechu; UI čekalo na další timer.
- Řešení: událost zpracovat přímo i ve stavu playing, ukončit player a aktualizovat UI; nové spuštění jen vědomou akcí.
- Ověření: regrese před opravou selhala; po opravě 30 testů, podepsaný iOS build a strict podpis OK. Testovat i bez dalšího ticku a s opakováním události; fyzický test zůstává samostatný.

### 2026-09-15 — UI test návratu nesmí znovu vytvořit ztracený vzorek

- Kontext: Camino, syntetická audio fixture pro XCTest v iOS simulátoru.
- Riziko: automatické vytvoření chybějícího vzorku při každém launchi by skrylo ztrátu dat mezi spuštěními.
- Řešení: náhodné oddělené UUID úložiště, explicitní seed pouze při prvním launchi; při návratu zakázat seed. Pomocný kód kompilovat pouze pro Debug simulátor.
- Ověření: 2 UI testy PASS, vizuální kontrola průběhu; binární program pro iPhone neobsahuje testovací vstupní značky.

### LL-038 — iPhone dostupný přes USB, ale CoreDevice neodpovídá

- Problém: Xcode ukazoval Connected a prázdný seznam aplikací, xcdevice available=true, ale devicectl info apps končilo timeoutem a log uváděl Failed to allocate RSD device.
- Typ: jednorázový
- Řešení nalezeno: 15092026
- Řešení: Přepojení kabelu nepomohlo; běžné ukončení a znovuotevření Xcode uživatelem obnovilo seznam aplikací, instalaci/spuštění i čtení metadat. Ověřit živými příkazy, samotné Connected nestačí. VPN se neměnila; příčinná souvislost s VPN nebyla prokázána.

### 2026-09-16 — Grafické seskupení pokračování není sloučení audio souborů

- Kontext: Camino C01b po telefonním přerušení a vědomém Pokračovat.
- Riziko: Karta „Část 1 / Část 2“ může vypadat jako přilepený jediný záznam a zakrýt, zda se původní médium přepsalo.
- Řešení: bez čtení audia porovnat snímek UI s technickými `started.json`/`completed.json`: rozdílná ID a CAF, první část `interrupted=true`, druhá má continuation na stejné session, předchozí část a evidovanou pauzu.
- Ověření: fyzický iPhone po hovoru měl dvě samostatná média; CoreDevice metadata potvrdila návaznost a UI je správně seskupilo. Samotný vzhled karty ani jediný součet času by nestačil.

### LL-039 — Připojené Bluetooth zařízení ještě není aktivní vstup

- Problém: Po připojení AirPods během přerušené nebo ukončované části může UI ukázat jejich skutečný mikrofon až při další vědomé aktivaci audio session; samotný stav Bluetooth proto neprokazuje změnu vstupu ani samovolné pokračování.
- Typ: opakující se
- Řešení nalezeno: 16092026
- Řešení: Posuzovat `currentRoute` při skutečně aktivní session a návaznost technických účtenek. U T020 potvrdit přerušenou část, explicitní continuation stejné session a nový aktivní vstup až po Pokračovat; nepovažovat pouhé připojení příslušenství za běžící mikrofon.

### 2026-09-16 — Sync musí použít příchozí Git atributy

- Kontext: Human–Adam profil přebírá fast-forward, který ve stejném commitu přidává importovaný Markdown s úmyslnými konci řádků a odpovídající `.gitattributes`.
- Problém: `git diff --check HEAD FETCH_HEAD` použil atributy starého checkoutu a bezpečný update falešně odmítl dříve, než mohl nový `.gitattributes` převzít.
- Řešení: preflight spustit jako `git --attr-source=FETCH_HEAD diff --check HEAD FETCH_HEAD`; ostatní kontroly čistoty, povolených cest, mazání a fast-forward zůstávají beze změny.
- Ověření: nový regresní test přidává atribut i Markdown ve stejném zdrojovém commitu; 192 souvisejících testů a rychlá kontrolní brána prošly.

### 2026-09-17 — AVAudioEngine tap nesmí zdědit MainActor

- Kontext: Camino C01c, Swift 6 strict concurrency a fyzický mikrofon.
- Problém: inline tap closure vytvořená v `@MainActor` metodě zdědila izolaci;
  `AVAudioEngine` ji zavolal na real-time audio frontě a runtime ukončil proces
  přes `_swift_task_checkIsolatedSwift`. Simulátorová syntetická média tuto
  cestu neprovedla.
- Řešení: callback vytvořit v explicitně `nonisolated` helperu a předat mu jen
  vlastní synchronizovaný `Sendable` stav. Nevypínat dynamické kontroly aktorů.
- Ověření: shodný podpis v pěti crash reportech, 52 Swift testů, 2 UI testy,
  arm64 build a strict podpis; fyzický Start/Stop zůstává samostatnou bránou.

### 2026-09-17 — Asynchronní reconciliace nesmí zahodit souběžný impuls

- Kontext: Camino C02b, background `URLSession` fronta po fyzickém výpadku sítě.
- Problém: jediný příznak `reconciling` odmítl callback, který dorazil během
  čekajícího serverového dotazu. Automatický průchod přitom neoznačil UI jako
  zaneprázdněné; ruční tlačítko vypadalo aktivně, ale klepnutí nic neudělalo a
  fronta mohla zůstat stát mezi dvojicemi částí.
- Řešení: žádosti koaleskovat do jednoho příznaku čekajícího dalšího průchodu a
  držet pravdivý busy stav po celou dobu drain loopu. Dostupná Wi-Fi smí spustit
  automatiku; ruční tlačítko je fallback, nikoli paralelní worker.
- Ověření: regresní test zachycuje žádost během aktivního průchodu; Swift 19/19.
  Podepsaný build 0.4.0 (2) po instalaci sám dokončil fyzickou 96MiB dávku 13/13
  bez dalšího klepnutí, se shodnou délkou a serverovým SHA-256.

### 2026-09-19 — Síťová politika dávky patří na každý URLRequest

- Kontext: Camino C02b, příprava mobilního testu T049 a background `URLSession`.
- Problém: kontrola typu sítě jen před plánováním nestačí při přechodu sítě;
  konfigurace background session připouští mobilní data. Velké uploadové
  požadavky měly individuální zákaz správně, malé session/status/finalize
  požadavky jej zatím neměly.
- Řešení: u všech čtyř druhů požadavků nastavit `allowsCellularAccess` a
  `allowsExpensiveNetworkAccess` podle povolení konkrétní dávky; bez grantu
  obojí `false`. Monitor rozlišuje i skutečné mobilní rozhraní. Před grantem
  zobrazit počet, objem a upozornění na možné opakování bajtů.
- Ověření: Swift 20/20, iOS build a UI test potvrzovací brány 1/1 PASS.
  Následný T049 s buildem 3 na iPhonu prošel v syntetickém mobilním rozsahu;
  nešlo o plné T049 se skutečně novým videem.

### 2026-09-19 — Mobilní grant není start nové dávky

- Kontext: Camino C02b, návrat testovací aplikace po povolení mobilních dat.
- Problém: `applicationBecameActive()` i změna sítě volaly reconciliaci, která
  mohla sama vytvořit serverovou relaci dosud nespouštěné dávky.
- Řešení: uložit vědomý první start do journalu a před serverovým voláním
  zadržet novou dávku s mobilním grantem. Po prvním startu nechat retry a
  obnovu pokračovat; starší journal obnovovat podle dosavadního kontraktu.
- Ověření: Swift 22/22 včetně nové a starší podoby journalu, simulátorový UI
  test, nepodepsaný iOS build a plná projektová brána 1719/1719 PASS. Fyzická
  část A na iPhonu s buildem 4: po grantu, návratu aplikace a obnově sítě
  telefon 0/13, server 0 relací. Po vědomém startu a pozdějším relaunchi s
  dostupnou sítí se stejná relace automaticky dokončila 13/13; otevření ještě
  bez sítě po force quit nebylo ověřeno.

### LL-040 — Viewer musí rozhodovat podle poslední přijaté revize

- Problém: Výběr každého serverového snapshotu zvlášť by pustil starší
  `diary` Moment, i když server už přijal novější zámek `owner_only`.
- Typ: opakující se
- Řešení nalezeno: 19092026
- Řešení: Před projekcí zvolit pro každé ID nejvyšší serverem přijatou revizi;
  `owner_only`, skrytí, neznámá hodnota nebo konflikt na stejné revizi se
  uzavřou. Výstup neobsahuje počty vyloučených položek.
- Ověření: Syntetický test zkouší obě pořadí staré a nové revize, neznámé
  soukromí i konflikt; C03a 9/9 a plná brána 1728/1728 PASS. Provozní Viewer
  ještě vyžaduje samostatnou integraci a fyzické ověření.

### LL-041 — Vstupní typy API ověř před dotazem do SQLite

- Problém: Pole ID s JSON typem pole by v dotazu SQLite skončilo jako chyba
  úložiště `503`, i když jde o neplatný klientský vstup `422`.
- Typ: opakující se
- Řešení nalezeno: 20092026
- Řešení: Striktně ověř tvar JSON, typ a kanonické UUID před použitím ve
  storage vrstvě. Pro soukromou databázi současně vyžaduj cestu mimo repozitář
  a práva 0600; širší práva odmítni při otevření.
- Ověření: C03b synteticky kontroluje chybné ID jako `422` bez posunu kurzoru
  a odmítnutí databáze s právy 0644. C03b je referenční kontrakt, ne běžící
  produkční server.

### LL-042 — Před mikrofonem ulož vazbu audia k Momentu

- Problém: Po pádu by dokončené audio bez trvalé identity cesty a soukromí
  šlo při obnově chybně připsat jinému Momentu nebo uvolnit do deníku.
- Typ: opakující se
- Řešení nalezeno: 20092026
- Řešení: Po vytvoření create-only audio journalu, ale před startem mikrofonu
  ulož stabilní session ID, Moment ID, Trip ID a soukromí. Po restartu navazuj
  jen ověřenou dokončenou session se shodným ID; neznámé nebo nedokončené
  médium zachovej a ukaž k ruční kontrole.
- Ověření: C04a má syntetický integrační test restartu a idempotence, Swift
  8/8, UI simulátoru 1/1 a nepodepsaný iOS build PASS. Fyzický pád během
  nahrávání nové aplikace na iPhonu zatím NEPROVEDEN.

### LL-043 — Create-only mediální soubor zapisuj bez kombinace Foundation voleb

- Problém: Kombinace `.atomic` a `.withoutOverwriting` u `Data.write` skončila
  při syntetickém C04b foto testu pádem Foundation místo ověřitelné chyby.
- Typ: opakující se
- Řešení nalezeno: 20092026
- Řešení: Po trvalém záměru otevři nový soubor `O_CREAT | O_EXCL` s právy 0600,
  zapiš celé bajty včetně krátkých zápisů a zavolej `fsync`. Při chybě
  záměr/soubor zachovej a nikdy nepotvrzuj uložení před kontrolou formátu,
  SHA-256, stabilní cestou a databázovou vazbou.
- Ověření: C04b syntetický foto/restart průchod a Swift 13/13 PASS; aplikace
  je nainstalovaná na iPhonu, fyzické chování foto/video se teprve zkouší.

### LL-044 — Podepisuj přes správný Xcode projekt a místní tým

- Problém: Xcode ukazoval přihlášený Personal Team v projektu CaminoAudio,
  zatímco příkazový podpis nového Camino hlásil `No Accounts` a žádný profil.
- Typ: opakující se
- Řešení nalezeno: 20092026
- Řešení: Ověř správné bundle ID a cíl projektu, otevři právě tento projekt
  v Xcode a nastav jeho tým v ignorovaném `LocalSigning.xcconfig`. Podepisuj
  nové ID automaticky a ověř profil včetně konkrétního telefonu; nepoužívej
  bundle ID staršího prototypu. Samostatnou příčinu rozporu účtu mezi GUI a
  příkazovým buildem tento průchod neurčil.
- Ověření: C04b potom získalo přesný profil, `codesign --verify` prošel a
  nové Camino 0.1.0 (1) se nainstalovalo a spustilo na iPhonu 14 Plus.

- Doplnění 23102026: samotný LocalSigning.xcconfig nestačí, pokud target v project.pbxproj obsahuje duplicitní DEVELOPMENT_TEAM. Odstranit target override při zachování ostatního projektu; Debug i Release musí přes showBuildSettings potvrdit stejný účinný tým a bundle ID bez výpisu hodnot. Osobní konfigurace zůstává ignorovaná; zdrojový WIP jinak blokuje i přepnutí čistých profilů.

### LL-045 — Den bez sovího řádku nesmí znovu nasadit starý zdrojový zvuk

- Problém: Pages workflow v den bez přesného CSV řádku nevytvořilo nové audio
  a znovu nahrálo zdrojový `app.js`, který ukazoval na historickou MP3.
- Typ: opakující se
- Řešení nalezeno: 21092026
- Řešení: V `OwlSpeech.csv` drž jeden řádek `default`. Přesné datum má
  přednost; bez něj generátor vytvoří z výchozí promluvy novou denní MP3 a
  přepne denní cache adresu. Výchozí cesty CSV/configu odvozuj z aktivního
  checkoutu, aby izolované testy nečetly jiný pracovní strom.
- Ověření: 19 cílených testů, dvě plné brány, workflow nad přesným produkčním
  commitem a veřejný `app.js`/MP3 s HTTP 200 prošly.

### LL-046 — Rizikový low-space scénář nejdřív odděl od skutečného měření

- Problém: Prahy přímo svázané se skutečnou kapacitou dovolovaly ověřit
  T060 jen zaplněním telefonu; audio, text a tepelný stav přitom neměly
  stejnou řízenou a automaticky dokazatelnou politiku.
- Typ: opakující se
- Řešení nalezeno: 21092026
- Řešení: Rozhodovací politiku drž jako čistou funkci nad injektovatelným
  zdrojem. Produkce čte systémovou kapacitu a tepelný stav, pouze Debug
  simulátor smí dodat řízenou hodnotu. Při neznámém stavu blokuj nový velký
  záznam, aktivní bezpečně dokonči, krátký zápis nech rozhodnout skutečným
  zápisem a nikdy automaticky nemaž originály.
- Ověření: C04b Swift 17/17, UI simulátoru 3/3, nepodepsané buildy pro
  simulátor i generic iOS a plná projektová brána 1740/1740 PASS. Integrační
  test zachoval starší originál
  byte-for-byte. Skutečný fyzický low-space a tepelný stres zůstávají
  samostatnou akceptací.

### LL-047 — Více tlačítek v jednom SwiftUI List řádku musí mít vlastní styl

- Problém: Klepnutí na Obnovit ve skrytém Momentu současně spustilo i tlačítko
  detailu ve stejném řádku `List`, takže archiv po správné obnově otevřel
  neočekávaný detail.
- Typ: opakující se
- Řešení nalezeno: 22092026
- Řešení: U samostatných akcí uvnitř jednoho SwiftUI `List` řádku nastavit
  explicitní `.buttonStyle(.borderless)` a každé tlačítko ověřit vlastním UI
  scénářem. C04d cílený test obnovy i následná celá matice 4/4 prošly.

### LL-048 — Retry fronty musí uchovat obálku a mobilní grant zmrazit dávku

- Problém: Nové sestavení JSON při retry může změnit bajty idempotentní
  operace; pouhé globální „mobilní data povolena“ zase může nechtěně zahrnout
  médium pořízené až po souhlasu.
- Typ: opakující se
- Řešení nalezeno: 23092026
- Řešení: Před prvním odesláním trvale uložit přesné bajty operace a její
  sekvenci. Mobilní souhlas navázat na aktuální ID dávky a ve stejné transakci
  otevřít nové ID pro všechny pozdější záznamy. Po výpadku vždy znovu číst
  serverový stav; lokální stav uploadu není důkaz `verified`.
- Ověření: C05b Swift 27/27, cílený UI relaunch/pause 1/1 a provozní workflow
  13/13 PASS; fyzická mobilní a síťová akceptace zůstává samostatná.

### LL-049 — Přímý workflow skript musí znát kořen projektu a vlastní port

- Problém: Registrovaný C05b příkaz prošel importem v unit testu, ale při
  přímém spuštění selhal na `ModuleNotFoundError`; po opravě narazil na port
  8766, který už dlouhodobě vlastní ScanDocu.
- Typ: opakující se
- Řešení nalezeno: 24092026
- Řešení: U přímo spouštěného skriptu vložit kořen projektu do `sys.path` ještě
  před projektovými importy a regresně spustit jeho skutečný soubor přes
  `--help`. Před přidělením pevného portu prohlédnout registr a živé listenery;
  dlouhodobým službám port nebrat a akceptačnímu procesu dát vlastní port.
- Ověření: Přímý vstup i registrovaný C05b lifecycle prošly, port 8767 zůstal
  loopback-only, ScanDocu na 8766 nebylo ukončeno ani změněno a plná projektová
  brána prošla 1770/1770 testů.

### LL-050 — Nezávislé skutečnosti nesmějí sdílet jeden zelený stav

- Problém: Ověřená kopie na Macu může v jednom souhrnném stavu zakrýt
  neověřenou další zálohu, čekající novější metadata nebo chybějící AI výsledek.
- Typ: opakující se
- Řešení nalezeno: 24092026
- Řešení: Modelovat Telefon, primární kopii, další zálohu a AI jako oddělené
  typované osy. Počty doménových položek držet odděleně od operací, souborů a
  bajtů. Pouhé uložení připojení ani dokončení přenosu nevydávat za zálohu;
  syntetické stavy povolit jen v Debug simulátoru.
- Ověření: C05c Swift 33/33, cílené UI 1/1, regresní UI pause 1/1, generic iOS
  build a plná projektová brána 1770/1770 PASS. Skutečná záloha a AI zůstávají
  samostatnou fyzickou a produkční akceptací.

### 2026-09-25 — Viewer za privátní proxy musí prefixovat i mediální odkazy

- Kontext: minimalistický Camino Viewer, přímý server a budoucí cesta `/camino-api`.
- Problém: správně otevřená HTML stránka ještě nezaručuje funkční média;
  absolutní `/viewer/...` bez proxy prefixu vedou na jiný backend.
- Řešení: explicitní povolený `root_path` předat také tvorbě navigace a médií,
  nepřebírat libovolný prefix z klientské hlavičky. Cockpit pouze odkazuje.
- Ověření: syntetický ASGI průchod přes `/camino-api/viewer/`, obrázek 200,
  zamčená stará mediální URL 404 a neautorizovaný přístup 401. Není to důkaz
  skutečného Serve, privátní sítě nebo vzdáleného Safari.

### 2026-09-25 — Doplnění audio pořadí nesmí změnit identitu již přenesených médií

- Kontext: Camino M2b, starý journal a server už mají přijaté Asset manifesty.
- Problém: přidání pořadí přímo do dříve poslaného create payloadu může
  porušit byte-exact retry nebo vyvolat identity konflikt; UUID není časová osa.
- Řešení: samostatný neměnný layout odvozený z dokončených účtenek, nová
  operace až po serverové schopnosti. Původní Asset ID/obálky se nemění,
  mezery zůstávají explicitní a chybějící úsek se automaticky nepřeskakuje.
- Ověření: Swift backfill zachoval přesné obálky i verified média přes restart;
  serverový test opačného doručení a pozdějšího prostředního úseku PASS.

### 2026-09-26 — Viewer grant nesmí přepsat původní create_trip

- Kontext: Camino M2c, samostatné provozní povolení soukromého HTML čtenáře.
- Problém: dodatečný přepis neměnného Trip payloadu by změnil identitu již
  přijaté operace; prostá kopie SQLite souboru může vynechat potvrzený WAL.
- Řešení: grant v samostatné tabulce, číst jej při každé projekci. Před
  upgradem použít SQLite backup API a potvrdit integritu/hash create-only kopie.
- Ověření: syntetický grant/revoke/regrant zachoval Trip i původní obálky,
  stará URL byla odmítnuta a snapshot obsahoval potvrzenou WAL transakci.

### 2026-09-26 — Tailscale GUI binárka potřebuje pod launchd CLI prostředí

- Kontext: první skutečný start spravované Camino služby na macOS.
- Problém: bez TERM/TERM_PROGRAM vrací aplikace Tailscale při `serve status
  --json` textovou chybu GUI, dokonce s návratovým kódem 0. JSON kontrola
  správně zabrání startu, ale terminálové testy problém neukazují.
- Řešení: vlastní plist má explicitní `TERM=dumb`; nepřebírat celé prostředí
  terminálu ani tajemství. Upgrade dovolí jen přesnou vlastní starší definici,
  kterou nejprve uchová v soukromé kopii. Při chybě bezpečně zastavit smyčku.
- Ověření: stejný read-only příkaz s minimálním prostředím bez TERM selhal,
  s `TERM=dumb` vrátil validní JSON. Test přesného upgradu a cizího plistu PASS;
  skutečný start je evidován samostatně v M2c reportu.

### 2026-09-26 — Dokončení obnovy musí zachovat byte-exact historii a zvládnout ztracenou odpověď

- Kontext: T058 změnil epochu, ale klient i server zůstávaly blokované.
- Problém: pouhé porovnání počtů nebo přepnutí flagů nedokazuje shodu;
  přepis epochy historických obálek by zničil jejich přesné retry identity.
- Řešení: explicitní shoda operací, revizí/soukromí a hashově ověřených médií,
  atomické uvolnění pod zámkem, účtenka vázaná na přesný požadavek. Staré
  přijaté obálky uchovat; novou epochu použít jen pro další operace.
- Ověření: syntetická obnova a opakování po ztrátě odpovědi PASS, rozdíly
  a nesprávná účtenka zůstávají blokované; pause a původní data se nemění.

### 2026-09-27 — Vyčerpaný mobilní souhlas není důkaz čekajícího přenosu

- Problém: po úspěšném videu se správně zrušil grant dávky, ale synchronize
  a networkChanged pak na mobilní síti hlásily Čeká na Wi-Fi i pro prázdnou frontu.
- Řešení: společná rozhodovací funkce nejprve rozliší úplnou dříve potvrzenou
  kopii od čekající práce. Žádné nové zelené potvrzení bez účtenky, identity
  serveru a úplného pokrytí; obnova a dosud nezařazená audio metadata blokují.
  Nové položky nesmějí zdědit předchozí grant. Stejná oprava musí být v obou
  vstupních cestách, nikoli jen v textu dashboardu.
- Ověření: lokální Swift regrese dokončení, nové dávky, chybějící účtenky,
  offline a recovery PASS. Fyzický retest čeká na novou podepsanou aktualizaci;
  serverově ověřený originál neprokazuje tehdejší stav celého journalu telefonu.

### 2026-09-27 — Název přílohy je revize metadat; audio session potřebuje vazbu před názvem

- Kontext: Camino B03, dodatečné názvy již přenesených fotografií/videí
  a celých hlasových komentářů.
- Problém: přidání názvu do původního Asset/layout manifestu poruší jeho
  neměnnou identitu. U audia může běžně odložený layout dorazit až za novou
  operací názvu, takže server nemůže ověřit příslušnost session k Momentu.
- Řešení: samostatná metadata revize s druhem a ID cíle, kontrola rodiče,
  capability attachment_title_v1 před odesíláním. Layout dané session zařadit
  před prvním názvem, ale staré přesné obálky a ověřené originály neměnit.
  Komentář počítat/pojmenovat po session, nikoli po technických segmentech.
- Ověření: skutečné Swift obálky ze starší fronty → izolované API, dvojí
  replay a reopen/Viewer PASS. Přejmenování přidá jen metadata, verified média
  zůstanou verified. Fyzická přejímka této nové verze zůstává samostatná.

### 2026-10-04 — Přejmenování cesty nesmí přepsat přijatý create_trip

- Kontext: přechod existující Zkoušky na pojmenovanou cestu Camino se
  zachováním Momentů a stejného Vieweru.
- Problém: změna původního create_trip by porušila neměnnou identitu při
  replay. Nový Trip by oddělil další záznamy od již existujících.
- Řešení: původní Trip a přesné obálky zachovat; nový název poslat jako
  samostatnou revizi set_trip_title s capability trip_title_v1. iOS ukládá
  historii do SettingRecord, server čte přijaté názvy z accepted_operations;
  žádná migrace schématu ani nový upload médií. Nejdřív nasadit server.
- Ověření: reopen a exact retry skutečných Swift obálek na izolovaném API
  PASS, původní Trip/Moment/Asset i Viewer mapa a auth zachovány. Fyzické
  přejmenování na iPhonu zůstává samostatný krok.

### 2026-10-04 — Upgrade Camino může zachovat další prázdné cesty

- Kontext: řízený upgrade archivu s jednou naplněnou cestou a staršími
  prázdnými Trip záznamy.
- Problém: historické `trip_count == 1` zastavilo upgrade i s jednoznačným
  platným `trip_id` v konfiguraci. Prázdné cesty se kvůli nasazení nemažou.
- Řešení: ověřit existenci explicitně zvolené cesty a nepřítomnost Momentů
  v jiných cestách. Zachovat všechny Trip řádky a jejich přesný otisk
  porovnat před/po. Bez výběru zůstává požadavek jediné cesty.
- Ověření: sada služby 25/25 PASS; prázdné cesty zůstaly, neznámý výběr
  nebo jiná naplněná cesta byly odmítnuty, změna otisku byla rozpoznána.


### 2026-10-23 — Vybraný Viewer projekt není celý owner archiv

- Kontext: zobecnění Camina na souběžné cesty a dovolené.
- Problém: původní kontrola upgradu odmítala další naplněné cesty, i když
  jednoznačné trip_id pouze vybíralo dosavadní Viewer. Přepnutí telefonu
  přitom nesmí přesměrovat již připravené přenosy.
- Řešení: zachovat identity a přesné fronty; metadata projektu vést samostatně
  v revizích. Explicitní výběr Vieweru kontrolovat jako existující cestu,
  celý owner archiv včetně dalších projektů kontrolovat a hashovat společně.
  Bez explicitního výběru se při více cestách dál nehádá.
- Ověření: skutečný Swift dvouprojektový fixture → API/MediaStore, dokončení
  rozpracovaného uploadu po přepnutí a restartu, původní bajty/identity i
  oddělené Viewer granty PASS. Čtecí kontrola archivu zachovala oba projekty.

### 2026-10-23 22:44 CEST — Status nesmí blokovat start vlastního workeru

- Problém: čtecí status získal a hned uvolnil worker lock během startu;
  současný worker používající LOCK_NB náhodně skončil BlockingIOError.
  Selhal tak nativní integrační test p+n i celá publikační brána před pushem.
- Typ: souběh při startu, potvrzený regresním testem.
- Řešení: během existující 30s startovací lhůty worker lease nezkoušet.
  Poté ponechat kontrolu opuštěného workeru, druhé čtení účtenky i zákaz
  souběžného workeru; neopakovat přerušené p+n automaticky.
- Ověření: 57 cílených testů, 10/10 souběžných integračních opakování
  a plná brána 2186/2186 PASS. app/communication/luna_release.py;
  tests/test_luna_release.py. Původní účtenka zůstává attention.

### 2026-10-24 09:52 CEST — Projekt filmu patří manifestu, nikoli globální volbě

- Kontext: více cest se stejnými názvy a dny, souběžně otevřené karty.
- Řešení: konfigurační cestu ponechat jen jako legacy výchozí volbu.
  Nový výběr nese trip_id a datum; uložený project_id znovu svázat s trip_id
  neměnného manifestu při čtení, renderu i výdeji. Neměnit sdílený objekt
  podle posledního UI výběru. Viewer katalog i URL jsou projektově omezené
  a povolení se ověřuje z aktuální projekce.
- Ověření: stejné názvy/dny, oddělené manifesty a syntetické exporty,
  odmítnuté cizí asset/job, Node late response/tab/reload a skutečné PNG HTTP.

- Závěrečná přejímka kroku: plná brána 2193 PASS, iOS Release PASS a
  explicitní odmítnutí chybného tvaru požadavku před otevřením archivu.


### LL-080 — Ovládání textu fotografie potřebuje skutečný DOM scénář

- Problém: dlouhý text odmítly limity titulku/karty, chyba byla daleko od tlačítka; původní DOM test vůbec nevytvářel kontejnery textů a karet.
- Typ: opakující se
- Řešení nalezeno: 24102026
- Řešení: testovat skutečnou sekci s dlouhým textem, místní chybou a následným kliknutím, uložením, reloadem a přesunem fotografie. Textová karta mezi obrazy není vrstva přes fotografii. Čtení musí zachovat celý zvolený text a mít změřenou délku; chatový TTS helper s krácením pro film nepoužívat. Ověřeno syntetickým 3022znakovým vstupem, skutečnými MP4 a místním TTS.

- Doplnění LL-080 (24. 10.): Node test spouštěný z Pythonu musí použít společný `scripts.cockpit_quality_gate.node_binary()`, ne mediální `binary("node")`. Regrese sama vynucuje `/usr/bin:/bin:/usr/sbin:/sbin`; terminálový PATH přítomnost Node ve službě neprokazuje.
- Doplnění LL-080 (11. 11., Přátelé): také nová MMTX JS regrese používá tento resolver a systémový PATH. Samotné shutil.which("node") v nové povinné kontrole zastavilo servisní bránu3487; opravovat dohledání, ne skipovat test ani měnit službu.


- Doplnění LL-080 (27. 10., Orus): cloudový limit ověřuj v UTF-8 bajtech, cenu v Unicode znacích; celý text a mezery musí po spojení částí souhlasit. Souhlas navazuj na přesný uložený text, hlas, tempo a cenu, při editaci jej zruš a před každým přenosem znovu ověř povolení. Nejasný placený požadavek nikdy automaticky neopakuj; zvolených 90 % tempa ověř místním atempo a skutečnou délkou. Ověřeno 6000 emoji, full decode, HTTP/DOM regresí; camino_orus_integration_20261027.md.

- Doplnění LL-080 (27. 10., publikační PATH): i závěrečný kontrolní probe v testu musí předat executable=media_binary("ffprobe"). Nestačí, že produkční adaptér cestu rozšiřuje. Regrese musí sama vynutit PATH služby; Orus modul 13 PASS.

- Doplnění LL-080 (2. 11., MMTX rozpočet): test odmítnutí placeného požadavku nemá vyžadovat instalované FFmpeg. Mockovat dohledání nástroje, vynutit PATH služby a ověřit skutečnou rozpočtovou chybu i nulové dekódování/odeslání. Reprodukce FAIL→PASS, Azure/builder 11 PASS v obou prostředích; skutečné mediální kontroly zůstávají samostatné.

- Doplnění LL-080 (4. 11., GitHub CI): mockovaný stdin test musí mockovat i `media_binary`, jinak selže dřív než ověří předání celého textu. U Orusu samostatně testovat celý text/concat/90% tempo bez binárek a zachovat skutečnou integraci s konkrétním preflightem ffmpeg i ffprobe. Terra doložila 2 původní chyby bez nástrojů → 2 PASS + přeskočenou skutečnou integraci s důvodem; běžné moduly 37 PASS bez skip. Zelený místní běh s Homebrew není důkaz dostupnosti nástrojů na GitHub runneru.

### LL-081 — Pracovní text a historie hlasových pokusů se nesmějí přepisovat navzájem

- Problém: samotné přepsání textu a nahrazení aktuálního audio odkazu neumožní porovnat pokusy ani obnovit jejich znění; skrytí záznamu navíc nesmí poškodit starší film.
- Typ: opakující se
- Řešení nalezeno: 24102026
- Řešení: uchovat neměnný zdrojový text a samostatnou pracovní kopii, každý pokus svázat s vlastním textem a původem. Smazání pokusu řešit obnovitelným košem s odpojením aktuálního odkazu; historické exporty dál čtou zachované odvozeniny s kontrolou soukromí. Staré účtenky doplnit pouze čtecím rozřešením zdrojové revize. Ověřeno editací/reloadem, více pokusy, košem/obnovou a neměnným hotovým filmem.


### LL-082 — Opožděný poll nesmí vrátit pracovní text před potvrzené uložení

- Problém: průběžný GET zahájený před psaním nebo během autosave mohl dorazit po potvrzení nové revize a nahradit ji starší odpovědí; editace pak působila jako nefunkční.
- Typ: opakující se
- Řešení nalezeno: 24102026
- Řešení: lokální změna a úspěšné potvrzení save zvýší generaci čtecích požadavků. Odpověď s původní generací se nesmí aplikovat ani skrýt rozpracovaný formulář. Ověřit oba souběhy s řízenými odpověďmi, nejen běžné uložení/reload. Nový DOM scénář FAIL před opravou → PASS po ní; žádná migrace uložených dat.

### LL-083 — Po uzavřeném kroku dlouhého vlákna doporuč nový chat s bodem navázání

- Problém: dlouhý rozhovor zatěžuje pracovní kontext; přechod bez uloženého stavu ztěžuje navázání a záměna `/new` za obnovu může odvést od existujícího návrhu.
- Typ: opakující se
- Řešení nalezeno: 24102026
- Řešení: po uzavřeném kroku dlouhého vlákna doporuč Mílovi `/new` pro nový chat ve stejném CLI a projektu. Nejprve zachovej stav, necommitovanou práci a připrav stručný startovní pokyn s kanonickým handoffem, posledním relevantním commitem/publikační účtenkou a otevřenými kroky; navazující relace nejdřív jen obnoví kontext a ověří stav. Pro návrat k existujícímu uloženému rozhovoru použij `/resume`. Příkaz nespouštěj automaticky, původní chat nemaž a nevymýšlej limit délky ani zbývající kapacitu. Význam příkazů ověřen v oficiální dokumentaci Codex CLI; samotný přechod do nového chatu zde nebyl prakticky testován. Kanonický postup: [Nový chat po dlouhé práci](technical/session_recovery_rules.md#nový-chat-po-dlouhé-práci).

### LL-084 — Po skrytí aktivní cesty musí zůstat správa projektů a přenosy

- Problém: žádost o smazání správně skryla aktivní cestu, ale kořenový přechod na přípravu projektu odstranil jedinou nabídku ostatních cest, koše i přenosů. Testy datového koše tuto UI chybu nezachytily.
- Typ: opakující se
- Řešení nalezeno: 24102026
- Řešení: i větev bez aktivního projektu musí zpřístupnit správu existujících projektů/koše a přenosy; skrytý projekt se neobnovuje automaticky.
- Ověření: skutečný izolovaný UI scénář nejdřív reprodukoval chybu na původní binárce, po opravě prošel přes dvě cesty, zachovaný Moment, poslední cestu, restart, koš a přenosy. Podepsaná IPA 22 připravená; fyzický telefon se přejímá zvlášť.

### LL-085 — Prázdný video intent zruš při odmítnutém startu, zbytky nabídni ke kontrole

- Problém: dva staré video intenty bez souborů, Assetů a Momentů trvale zvyšovaly hlášku média ke kontrole. Start kamery mohl po uložení intentu odmítnout práci bez návratového výsledku.
- Typ: opakující se
- Řešení nalezeno: 24102026
- Řešení: znovu ověř stav po GPS čekání, vrať výsledek startu a ruš pouze známý neúspěšný intent bez souborů. Staré/neprázdné pokusy nabídni k výslovnému úklidu; zmraz metadata/souborový inventář, revaliduj před unlinkem, chraň přijaté Assety a projektový koš. Při pádu zachovej intent pro čerstvou kontrolu. Pro výslovné Zrušit použij ověřený alert; lazy seznam neověřuj počtem pouze renderovaných řádků.
- Ověření: Swift 95 PASS (8 nových), nový skutečný UI scénář PASS včetně zrušení a restartu, plná brána 2232 PASS. Telefonní audit četl jen nutná technická metadata/inventář; živý SQLite soubor se zvenčí nepřepisoval. IPA 23 připravená, fyzický úklid se potvrzuje samostatně.


### 2026-10-26 — Výběr v editoru je pohled, ne nový střih
- Kontext: Camino, seznam záběrů/náhled/nastavení a přehrání hotového filmu.
- Problém: index se po přesunu vztahuje k jinému záběru; přestavba miniatur při každém vstupu může opakovat drahé soukromé GET. Pozdní odmítnutí play() může patřit již zavřenému filmu.
- Řešení: výběr držet odděleně podle Asset ID bez změny draftu a bez renderu/proxy. Při psaní měnit jen popisky, obrázky zachovat. Hotový výsledek vybírat podle aktuální revize a celé délky; chybu přehrávání vázat na epochu/generaci.
- Ověření: Node regrese výběru bez zápisů, zachování textu/identity/miniatur, vyloučení staršího a částečného filmu a pozdní play rejection PASS. Vizuální browserová přejímka samostatně; reports/camino_film_workspace_20261026.md.

### LL-086 — Miniatura nesmí znovu hashovat celý film

- Problém: editor s 29 fotografiemi posílal pro každou miniaturu až 16MB PNG a dvakrát hashoval všechny zdroje filmu; čekání na stránku narůstalo na minuty.
- Typ: opakující se
- Řešení nalezeno: 26102026
- Řešení: samostatné malé metadata-free PNG (256px seznam, 1600px pracovní náhled), bez skrytého duplicitního obrázku. Čtecí kontrola může krátce využít ověřené hashy v omezené RAM pouze při shodě device/inode/size/mtime_ns/ctime_ns a kontrole změn při čtení. Aktuální soukromí/manifest/koš se znovu ověřují vždy, vlastní obrázek se vždy hashově ověří. Uložení a render používají úplné ověření bajtů; bez persistentního cache nebo cache oprávnění.
- Ověření: stejné místní vstupy, miniatura 5,287 → 0,192 s a 16,2 MB → 100 KB, stav editoru 1,324 → 0,039 s při již ověřených souborech. Plná brána 2243 PASS; regrese změny soukromí, stejné velikosti/obnoveného mtime, symlinku, souběhu a expirace PASS. Čas celé stránky po nasazení se přijímá samostatně. Report camino_film_loading_20261026.md.

### LL-087 — Výška navigátoru závisí na skutečné hlavičce a viewportu

- Problém: miniatury končily na max-height:60vh a při scrollu dlouhého pravého editoru mizely z dohledu.
- Typ: opakující se
- Řešení nalezeno: 28102026
- Řešení: sticky panel pod měřenou hlavičkou, flex seznam s min-height:0 a vlastním overflow. Výšku odvozovat od aktuální polohy a viditelného spodního okraje; resize a změny hlavičky/obsahu spojit přes RAF, posluchače odpojit při zavření či skrytí. Výpočet nesmí přestavovat miniatury, měnit draft nebo spouštět další requesty.
- Ověření: syntetický DOM scénář geometrie/lifecycle a 102 cílených kontrol PASS. Skutečný browserový wheel/resize a Safari zůstávají samostatná přejímka; camino_film_navigation_height_20261028.md.

### LL-088 — Poslední rozpracovaný film není nejnovější den fotografií

- Problém: střižna otevírala starou volbu karty nebo konfigurační cestu; katalog řadil podle data zdrojů místo posledního uložení střihu.
- Typ: opakující se
- Řešení nalezeno: 28102026
- Řešení: číst čas existující poslední editovací revize (u nového filmu project-r1), ověřit kandidáta proti současným oprávněním a nabídnout jej napříč cestami pouze při novém otevření. Při refreshi zachovat ruční/dirty výběr. Nejprve porovnat metadata; kvůli výběru nečíst exportní úlohy všech filmů. Čtení/render nesmí měnit hodiny uloženého střihu.
- Ověření: 86 cílených kontrol PASS včetně dvou cest, staršího dne uloženého později, změny soukromí, read-only bajtů/mtime a Node stale/refresh/reopen. Místní čtení 0,771 s / 0,027 s; browserová přejímka zůstává samostatná. Report camino_film_resume_latest_20261028.md.

### 2026-11-01 — Azure ukázky před pokračováním přerušovaného Edge TTS

- Kontext: MMTX scéna 6, opakované HTTP 429 zastavily Edge na 16/144 stopách.
- Typ: opakující se
- Řešení: výslovný Azure provider, původní hlasová ID a -10 %, přesné escapované SSML bez krácení textu. Nejprve oddělený poslech chybějících hlasů, potom teprve věcné přijetí a doplnění scény. Hotové MP3 a účtenky vždy ověřit a zachovat.
- Náklady a tajemství: celý plán zkontrolovat před sítí; rezervovat účtované znaky před každým POST. Limit 10 000 znaků na běh, žádný automatický retry/refund při nejisté odpovědi. Klíč pouze v místním .env a stdin konfiguraci curl, nikdy v argv nebo chybovém výpisu.
- Ověření: šest skutečných Azure MP3, 274 účtovaných znaků, 22,488s spojený poslech a přesně shodné SHA-256 všech původních souborů obou kopií scény. 44 cílených testů PASS. Lidské přijetí celého zvuku je samostatný krok; viz mmtx_scene06_azure_preview_20261101.md.

- Doplnění 2026-11-01 po přijetí ukázek: zbývajících 128 stop dokončeno 128 unikátními Azure požadavky, 5 870 znaků; plná sada 144/144 a staré MP3 beze změny. Testy výběru ukázek a překročení rozpočtu mají používat syntetická data, aby po dokončení scény nezávisely na skutečně chybějících stopách.

### LL-097 — Modernizace App Serveru nesmí obejít důkaz doručení

- Problém: resume zbytečně načítal historii, commentary se mohlo stát odpovědí a obecná chyba zahazovala strukturu. Lokální verze CLI sama nedokládá verzi sdíleného listeneru.
- Typ: opakující se
- Řešení nalezeno: 04112026
- Řešení: před operací s vláknem ověřit metadata připojeného serveru; potom posílat excludeTurns. Volit explicitní final_answer, phase-less ponechat jako legacy; zachovat started, přesný client ID a completed. Strukturované chyby uchovat v atributech, nikoli v běžném textu výjimky. willRetry je činnost serveru uvnitř tahu, ne pokyn k druhému odeslání.
- Ověření: 100 cílených testů PASS včetně skutečného klienta nad syntetickým transportem, session hubu a obnovy stavu bez opakování. Report codex_appserver_p1b_20261104.md. Živá přejímka je samostatná.

### LL-099 — Editor nemaž před dokončením přípravy požadavku

- Problém: mobilní dotaz zmizel bez viditelné práce či chyby. Syntetická výjimka při přípravě ID reprodukovala vymazání textu a blokaci před prvním POST; přesná chyba telefonu nebyla prokázaná.
- Typ: opakující se
- Řešení nalezeno: 05112026
- Řešení: ID, serializaci a optimistický stav připravit před vymazáním editoru. Při selhání přípravy text zachovat a ukázat chybu u editoru. U nejistého výsledku zachovat needitovatelnou kopii a blokovat nový send do korelovaného potvrzení; obecné serverové selhání není důkazem nulového účinku. Model ani akci automaticky neopakovat.
- Ověření: FAIL→PASS Node VM nad skutečnou obsluhou, 150 cílených testů PASS; fyzický retest je samostatný. Report human_adam_iphone_send_failure_20261105.md.

### LL-105 — EventKit oprávnění ověřovat ve skutečném kontextu helperu

- Problém: přímé spuštění z Codexu hlásilo write_only, přestože uživatel povolil plný přístup samostatné kalendářové aplikaci.
- Typ: zobecnitelné
- Řešení nalezeno: 07112026
- Řešení: samostatný podepsaný read-only .app helper ve vlastní aplikační složce, GUI žádost přes LaunchServices a skutečný krátký launchd probe s ověřeným rodičem PID 1. Tento kontext potvrdil full_access a omezené čtení. Kalendářové zápisy nejsou v pilotu vůbec implementované. Přímé CLI oprávnění není důkaz servisního oprávnění; po změně binárního podpisu provést novou přejímku. Do logů/Gitu jen agregované důkazy, názvy kalendářů a ID soukromě. Ověřeno znovu v bodě 2: nové ad-hoc sestavení má jiný cdhash a launchd kontext not_determined. Žádost evidovat samostatně pro přesný binární otisk, starou uchovat; GUI grant se automaticky nepřenáší ani neopakuje. Přehled má zůstat authorization_required do nové uživatelské přejímky.
- Doplnění 07112026, bod 4: pro kontrolu návrhu stačí přesné omezené start/end v již podporovaném native overview požadavku. Pythonová změna období nevyžaduje nové Swift sestavení ani OS souhlas. Skutečný launchd read čtyř vybraných kalendářů PASS při nezměněném binárním otisku a nastavení; logy pouze agregované.

- Doplnění 07112026: novou schopnost zápisu lze sestavit jako samostatný podepsaný helper a ponechat čtecí Swift/bundle/OS grant beze změny. Sdílet jen parametrizovanou stavební infrastrukturu. Ověřeno shodou původního zdrojového/binárního otisku a sestavením nového create-only writeru; jeho vlastní OS grant a živý zápis tím nejsou přejaté. Report calendar_simple_20261107.md.

- Doplnění 07112026, živý writer: první read-back měl přesně uložené údaje, marker i alarmy, ale prázdné eventIdentifier. Python jej správně nepřijal jako konečné ověření. Jediné následné read-only recover původní identity už mělo neprázdné ID; native log prokázal právě jeden create, obnovu bez save a Cockpit jednu odpovídající událost. Příčinu dočasně chybějícího ID neodhadovat a nezaměňovat neúplnou účtenku za svolení vytvořit druhou událost. Důkaz logs/calendar_writer_macos_acceptance_20261107.log.

- Doplnění 08112026: rychlé zadání úkolu může znovu použít stejný create-only writer bez rebuildu/grantu. Trvalá identita před native voláním; po write_unknown pouze jeden bounded read-only recover původní operation_id, pak uchovaný nejistý stav. Po ověření spouštět obnovu přehledu až mimo výběrový zámek a jen při nové verified účtence. Ověřeno syntetickým souběhem/restartem/timeoutem a živým pouze čtecím build/context auditem; skutečný zápis nové karty není touto zkouškou přejatý. Report calendar_task_entry_20261108.md.

### LL-106 — Metadata iCloud aliasu ověřuj na připnutém skutečném cíli

- Problém: NSURL na systémovém aliasu CloudDocs/Documents hlásí neubiquitous,
  přestože skutečná složka Dokumenty synchronizovaná je. Nepřemostěné JS pole
  klíčů navíc může přes Foundation vrátit prázdný slovník.
- Typ: opakující se
- Řešení nalezeno: 07112026
- Řešení: nejprve ověřit připnutou identitu a povolený alias, pro NSURL audit
  použít resolve cíle. Pole klíčů v JXA přemostit na NSArray, NSNumber 0/1 na
  bool a chybějící metadata nikdy nezaměnit za upload. Ověřeno čtecím auditem
  skutečného iCloudu a syntetickým testem; dostupnost složky není upload TXT.

### LL-107 — Přejímka návodu musí vázat přesný důkaz, ne jen správný JSON

- Problém: platná citace někde v dlouhém souboru nebo zachované nadpisy
  neprokazují nové nastavení, zachování kroků ani ověření telefonu.
- Typ: opakující se
- Řešení nalezeno: 07112026
- Řešení: oddělit core validaci od obsahové přejímky. Kontrolovat každou
  kapitolu, přesné technické literály v citaci, schválený seznam aplikací,
  autoritu/stáří a kotvu ručního důkazu. Účtenku svázat s kandidátem,
  kontextem i checklistem. Strojový výsledek review není publikace.
  Ověřeno synteticky v REC-03; lidskou přejímku a skutečnou obnovu nepředstírat.

### LL-108 — Původní hash nestačí jako povolení k opakování již dokončené kopie

- Problém: stejný starý obsah může být očekávaná nedokončená kopie, ale také
  pozdější ruční vrácení již dokončené verze. Samotná dvojice old/new hashů
  tyto případy nerozliší a může přepsat lidský zásah.
- Typ: opakující se
- Řešení nalezeno: 07112026
- Řešení: spojit schválený obsah a cíle s neměnným přijetím; v žurnálu
  uchovat dokončení každé kopie i záměr rollbacku. Dokončená kopie smí při
  obnovení zůstat pouze ve schváleném stavu. Aktivní marker dále odmítne
  starou žádost po novějším vydání. Ověřeno syntetickým REC-04 přenosem.

### LL-109 — Test návrhu služby nesmí vyžadovat skutečnou lokální .venv

- Problém: REC plist test prošel v hlavním checkoutu, ale publikační profil bez .venv skončil chybou ještě před push.
- Typ: zobecnitelné
- Řešení nalezeno: 07112026
- Řešení: metadata planneru ověřit na vlastním dočasném projektu s fixture interpretu a skriptu; nic nespouštět ani neinstalovat. Produkční is_file validaci ponechat a přidat negativní kontrolu chybějících souborů. 125 cílených REC testů PASS; plnou izolovanou bránu ověří nové přesné vydání.

### LL-110 — Po výpadku nejdřív dokonči doručení, nevytvářej další analýzu

- Problém: nový týden nebo ruční spuštění může obejít rozpracovanou úlohu,
  zopakovat placenou analýzu či začít novou před dokončením známých kopií.
- Typ: opakující se
- Řešení nalezeno: 07112026
- Řešení: jeden trvalý ISO slot pro ruční/timer vstup, marker před analýzou
  a přednost nedokončeného přenosu. Nejistá analýza zůstane attention přes
  další týdny; obnovuje se známá účtenka, nikoli model. No-change větev
  znovu ověří kopie na konci revize. Ověřeno synteticky i s REC-04 writerem;
  nejedná se o živou modelovou/launchd přejímku.

### LL-111 — Pod vlastním souborovým zámkem neopakuj zamykající writer

- Problém: atomický JSON writer uvnitř již drženého exclusive_file_lock čekal na vlastní druhý flock a skončil timeoutem.
- Typ: opakující se
- Řešení nalezeno: 07112026
- Řešení: pod existujícím stabilním zámkem použít atomic_replace_text_under_external_lock; celý read/modify/write dál patří pod původní zámek. Neoslabovat transakci oddělenými nezamčenými zápisy. Ověřeno agendou kalendáře: jediný background claim napříč instancemi, revizní kontrola soukromých typů a zachování po restartu; tests.test_calendar_agenda, report calendar_agenda_20261107.md.

### LL-112 — Browserová identita požadavku nesmí záviset jen na HTTPS-only API

- Problém: randomUUID nebylo na HTTP dostupné; obecný catch to označil jako chybu úložiště a trvale zašedil dosud neodeslaný formulář.
- Typ: opakující se
- Řešení nalezeno: 08112026
- Řešení: používat pro serverový 32hex ID silné getRandomValues (dostupné i mimo secure context), nikdy slabé Math.random. Oddělit známé selhání před POST od nejistého zápisu: prázdné úložiště dovolí editaci a nový explicitní pokus; částečně uložený payload musí zachovat původní ID a pouze status/recover. Testovat HTTP profil bez randomUUID i skutečné chyby setItem/read-back; nemockovat všechny kryptografické funkce jako vždy dostupné. Red→green regrese a 26 cílených PASS, report calendar_task_storage_fix_20261108.md.

### LL-113 — Nový zdrojový manifest není opakování placeného pokusu

- Problém: souběžný nový main zneplatnil už přijatou kartu před prvním modelem;
  přepsání packetu by skrylo změnu zdrojů a nový adresář by obešel deduplikaci.
- Typ: zobecnitelné
- Řešení nalezeno: 07112026
- Řešení: neplacený refresh povolit jen bez attempt/controller/turns, původní
  kartu zachovat a nový manifest přijmout pod vlastním digestem. Starý limit
  se nenavyšuje a všechny verze drží stejný job/marker. Po rezervaci nebo
  nejistotě refresh odmítnout, nikoli resetovat. Ověřeno šesti regresními
  případy a skutečným zastavením před placeným tahem. Původní Datova čísla LL-111 až LL-113 jsou při integraci
  posunuta na LL-113 až LL-115, aby zůstaly zachované kalendářové LL-111/112.

### LL-114 — Správný význam není doslovná citace

- Problém: skutečný Sol/medium při přesných zdrojích změnil v citaci jen
  první písmeno na velké; JSON i seznam dokumentů byly správné, exact match ne.
- Typ: zobecnitelné
- Řešení nalezeno: 07112026
- Řešení: doslovný kontrakt ponechat fail-closed, zachovat raw odpověď,
  určit skutečnou spotřebu z jedinečných turn účtenek a další SDK kroky
  neodeslat. Dvě konkrétní kapitalizace doložené v REC-06, 2 SDK tahy,
  21,013 Standard kreditu bez retry. Návrh serverových source/anchor ID je
  další neplacený vývoj, nikoli už ověřené řešení nebo přijatý modelový výstup.

### LL-115 — Přesný text může dodat resolver, model jen vybrat odkaz

- Problém: model věcně správnou citaci při přepisu kapitalizuje; přesný kontrakt selže.
- Typ: zobecnitelné
- Řešení nalezeno: 07112026
- Řešení: v novém protokolu nabídnout ID neměnného zdroje a úseku, vázat je
  SHA katalogu/requestu a doslovnou citaci načíst programem. Scope, úplnost
  a původní obsahový gate zachovat i v syntéze. Ověřeno 24 offline testy,
  úplným historickým korpusem a 101 fixture; není ověřena živá modelová volba
  ID ani věcná správnost. Starý neúspěšný běh zůstává uzavřený; nový formát
  vyžaduje nové nacenění a zvláštní přijetí placené zkoušky.

Doplnění 07112026 k LL-115: skutečná malá dvoufázová zkouška potvrdila oba
source/anchor kontrakty, přesné citace i doslovně zachovaný celý original.
Cena 8,50485 Standard kreditu pod mezí 15; syntéza 400,240 s ale překročila
schválených 300 s. Vyhodnocuj obsah, cenu a čas odděleně z raw účtenek:
obsahová revalidace bez modelu není zpětné přijetí celého jobu. Zachovat
attention a známé doručení, neopakovat SDK jen kvůli času ani zpětně neměnit
limit. Nový fázový časový plán je další samostatná karta, ne oprava účtenky.

Doplnění 08112026 k LL-115: v prvním velkém anchor tahu model vrátil
l131111 pro AGENTS.md s 26 řádky. Formát l+číslo prošel output schematem,
přesný resolver správně zastavil celý job; 38 ostatních referencí platných,
9,58995 Standard kreditu a žádný retry. ID protokol vyžaduje nejen runtime
ověření, ale i další zpřesnění přípustných hodnot v output schema. Takové
zpřesnění je zatím návrh k offline ověření, nikoli ověřené řešení či souhlas
s dalším modelem. Raw/cenu/uzavřený slot zachovat, ID nehádat ani nenormalizovat.

Doplnění 08112026 k LL-115 (offline ověřeno): samostatný nový formát může
vydávat pro každý zdroj hustý číselný index 1…N; integer minimum/maximum a
source-specific anyOf pak reprezentují přesně vydané povolené dvojice bez
desítek tisíc enum values či regex aproximace. Immutable mapa/request hash
a nezávislý resolver zůstávají. Protipříklad 131111 při max21 odmítl nezávislý
JSON Schema validator; 21 schémat, 8683 probes a 99874 mapování. Je to lokální
důkaz, nikoli modelově ověřený formát, souhlas s dalším pokusem nebo oprava
starého jobu. Platná reference sama neprokazuje správnost tvrzení.

Doplnění 08112026 k LL-115 (integrace): nový přesný wire formát patří do
samostatného pevného jobu s novou konkrétní kartou, nikoli do resetovaného
uzavřeného slotu. Worker reprodukuje wire/schema/map SHA a všechny raw dávky
před syntézou; runtime decode nesmí měnit raw ani mít legacy fallback.
Ověřeno 46 kontraktními testy a skutečným čerstvým korpusem 532 dokumentů
přes celý executor/worker (20+1, syntetický wire, izolovaný skutečný tokenizer).
Status/replay bez připojení; provider a věcná správnost zůstávají neověřené.

Doplnění 08112026 k LL-115 (celý skutečný běh):21 číselných odpovědí splnilo
odeslané schema,20 inspections přijato,532 dokumentů/116 findings. To nestačí
pro aplikační přejímku: syntéza34115/32000 output a poslední unverified odstavec
bez evidence. Zdrojová main větev navíc během syntézy postoupila. Job zachovat
attention/174,8297 bez retry. Bez dalšího modelu lze udělat výslovně oddělený,
auditovaný redakční derivát; raw/limit/job se nemění. Ověřeno25 operací,
všech216 citací zachovaných, celý původní obsah a původní quality gate passed.
Běžná lomítka v próze nejsou cesty a nezaškrtnutý přejímací bod není live claim;
rozdíl doložit a redakčně vyjasnit, ne vypnout gate. Nové odvozené cesty bez
přesné citace nepřijímat. Sémantická/provozní přejímka tím není automatická.

### LL-116 — Nejistou mutaci zamykej podle cíle, nikoli jen požadavku

- Problém: nová karta nebo změna provider metadat by vytvořila nové ID/hash
  a mohla zopakovat nejasné smazání stejného výskytu.
- Typ: zobecnitelné
- Řešení nalezeno: 08112026
- Řešení: před mutací fsync serverového claimu i nativního žurnálu pod
  stabilním kalendářem/nativní identitou/výskytem; proměnlivý fingerprint
  kontroluje shodu obsahu, neslouží jako nový retry slot. Recovery jen čte
  původní účtenku, prázdný seznam sám není důkaz dokončení. Ověřeno skutečnou
  Swift transakční logikou s in-memory EventKit (15 scénářů), včetně změny
  poznámek po nejasném remove a nového UI requestu bez další mutace.
  Není to skutečné smazání z osobního kalendáře ani přejímka iCloud sync.


### LL-117 — Volitelný doplněk modelu nesmí zahodit původní platný výsledek

- Problém: přidání kalendářového návrhu přímo do e-mailového kontraktu by
  měnilo editaci/digest starých konceptů; chybná citace by zahodila i platnou odpověď.
- Řešení: samostatná opt-in obálka, validace původního návrhu oddělená od doplňku,
  uložený doplněk vedle původních dat a převzetí do existujícího editoru pod
  stejnou zdrojovou identitou. Existující rozepsaný/nejistý návrh má vždy přednost.
- Ověření: 214 cílených testů, včetně chybné volitelné citace, zachování konceptu,
  restartu, souběžného importu a HTTP průchodu ke stejnému potvrzenému zápisu.
  Zdroj: reports/calendar_hourly_suggestions_20261108.md.
- Hranice: syntetické ověření kontraktu neprokazuje modelovou kvalitu ani
  úsporu tokenů; zapnutí v samostatné službě až po kompatibilním upgradu.

Doplnění 08112026 k LL-115 (čtenářská forma): Míla požaduje jeden průběžně
sjednocovaný návod s jediným datem aktualizace, bez řetězení dodatků. Historii,
zdroje a staré verze uchovat mimo čtenářský text. Neměnná raw účtenka neznamená,
že se v uživatelském návodu mají navždy kopírovat neplatná ID a postupy.
Nový text ověřit pokrytím potřebných témat, zdrojovou mapou a kontrolou
příkazů; netvrdit průchod starým objemovým gate, pokud odstraňuje historii.
Vložený shellový heredoc musí mít neodsazený ukončovací delimiter a správné
odsazení Pythonu; kontrolovat AST a shell -n bez vykonání obnovy.

Doplnění 08112026 k LL-115 (opakované týdenní revize, offline ověřeno):
sjednocení musí být kontrakt generátoru, ne jen pokyn k jednorázové redakci.
Model vydává dispozice bloků a doložené změny, server zachované bloky kopíruje
přesně a vkládá jediné trusted datum. Historie dispozic/citací je mimo TXT.
Dvě navazující revize musí začínat posledním přijatým textem; ověřit, že se
nehromadí data, dodatky ani značky Neověřeno. Nový formát vyžaduje nový gate
pokrytí, nepřepsání starého objemového pravidla. Zmrazené jednorázové adaptéry
musejí původní wire formát zvolit výslovně, bez automatického fallbacku.
Na17 kapitolách/340 blocích keep zachoval obsah přesně; to neprokazuje
sémantickou správnost budoucích modelových rewrite a nenahrazuje přejímku.

Doplnění 08112026 k LL-115 (běhová integrace): změna formátu musí projít
přejímkou i její čerstvou kontrolou těsně před zápisem, nikoli pouze prvním
renderem. Další přijatý týden nesmí být zaměněný za superseded jen proto,
že active marker patří předchozímu dokončenému přenosu; pokračování dovolí
jen shodné připnuté baselines obou kopií. Druhý vstup musí mít SHA prvního
přijatého výstupu. Ověřeno přes skutečný plánovač/generátor/přejímku/writer
s fake modelem a dočasnými soubory, včetně pádu mezi kopiemi bez dalšího tahu.
Run/tick po integraci už nejsou principiálně read-only workflow; registr musí
uvádět model/privátní zápisy a ruční potvrzení, i když je aktivace zatím vypnutá.

Doplnění 08112026 k LL-115 (před aktivací): propojení callbacků není samo
plně automatický provoz. Ověřit také pohyblivý zdroj dokumentace (Git main,
ne dlouhodobě zaostávající HEAD vývojového worktree), přijatou automatickou
přejímací politiku a každý přechod po pádu mezi přijetím a přenosem.
Standard per-turn se nemusí shodovat s globálním Fast; nezapisovat globální
preference, ale vynutit podporovaný override. Účet API-key nesmí projít
cenovým plánem ChatGPT kreditů. Deklarovaná konfigurace a datum čtení
nejsou live/device proof. Nejistý launchctl bootstrap se neposílá podruhé.

Doplnění 08112026 k LL-115 (skutečná aktivace): pokrytí tématu data mimo
Git nesmí být závislé jen na doslovném řetězci mimo Git. Explicitní varování,
že GitHub clone nezíská .env a ignorovaná soukromá data, vyjadřuje stejnou
podmínku. Úzkou opravu omezit na nový integrovaný gate; legacy neoslabovat.
Při odmítnutí před publikací/launch zachovat původní balíček, doložit nulové
odeslání a pouze auditovaně přepnout otisk opraveného validatoru; neměnit
přijaté bajty/role/rozpočet/cíle a nepožadovat znovu už udělený souhlas.
Ověřeno:166 cílených testů, dvě skutečné kopie/upload, jeden bootstrap,
launchd exit0/not_due/0 modelů. Není to důkaz prvního placeného týdenního tahu.


Doplnění 08112026 k LL-115 (integrační test): test neaktivní role nesmí
předpokládat její trvalou nepřítomnost v reálném schváleném configu. Po
pozdější přijaté aktivaci by tak blokoval jinak platnou integraci. Ověřit
fail-closed chybějící binding na vlastní dočasné konfiguraci, její nezměněné
bajty i platnost aktuálních schválených rolí bez jejich přepisování.


Doplnění 09112026 k LL-070: main617f3e0d přidal recovery roli do sdíleného
JSON, ale skutečná hodinová kopie f2d6ef79 ji odmítala. Test hlavního parseru
neodhalí selhání jiného runtime přes symlink stejného configu. Reprodukce
musí proběhnout skutečným instalovaným parserem, bez IMAP/modelu. Po přesné
globální brzdě registrovaný pause/prepare/upgrade na617f3e0d zachoval při
přepnutí celý business stav/nastavení/politiky; první reálný slot11:00
completed,7 zpráv a všechny původní položky beze změny. Novou roli ověřit
ve všech skutečných čtenářích před zpřístupněním sdílené konfigurace.


### LL-118 — Úspěšné uložení ještě nedokazuje viditelnost ve společném Archivu

- Kontext: potvrzená archivace hodinového agenta uchovala originál a PDF, ale stránka Archiv četla pouze staré úložiště.
- Příčina: writer a reader používaly jiné kořeny; účtenka dokazovala uložení, nikoli dostupnost přes uživatelský přehled.
- Řešení: společný read-only reader nad oběma pevnými kořeny, stabilní původní odkazy, oddělené identity nového zdroje a odmítnutí nejednoznačných ID. UID není globální identita mezi schránkami.
- Ověření: hledání → detail → originál/PDF přes skutečné HTTP routy, symlink/path úniky odmítnuté; skutečný uložený dokument dostupný a otisky souborů před/po shodné. Report `reports/email_archive_bridge_20261109.md`.


### LL-119 — Uvolnění formuláře nesmí záviset pouze na dialog.close

- Kontext: po Zrušit nebyla editace v reálném prohlížeči ihned znovu dostupná, ačkoli synchronní testovací close prošlo.
- Příčina: nativní close event je asynchronní; odstranění dialogu a další klik mohou předběhnout jeho doručení.
- Řešení: uvolnit sdílený busy stav výslovně při zavření před odstraněním DOM. Během odesílání formulář dál nelze znovu odeslat ani zavřít.
- Ověření: regresní JS test nezávislý na synchronním close callbacku a headless Edge na skutečném DOM: Zrušit → znovu Editovat → úprava → Splněno PASS; `reports/calendar_complete_edit_20261109.md`.


### LL-120 — Otevření staršího Cockpitu nesmí restartem přerušit p+n

- Kontext: schválený ScienceNews balíček prošel lokální branou; během publikační brány hotkey launcher rozpoznal starší otisk a ukončil server, který bránu obsluhoval.
- Důkaz: job bd828212 push_requested→attention ve 22:00:13, hotkey.out.log ukončil PID 48189 a ve 22:00:26 hlásí nový server; supervisor spustil PID 64718 ve 22:00:20. GitHub zůstal 5ea9af40, dítě quality gate pokračovalo osiřelé; nový HTML odpovídal lokálnímu 1395956d bez řízené účtenky.
- Řešení: před automatickým launcher restartem ověřit veřejný status p+n. Aktivní vydání dovolí otevřít dosavadní server bez restartu; neověřený/malformed/timeout stav restart nepovolí. Vlastní autorizovaný restart publisheru se nemění. Zelená lokální brána není potvrzený push/deploy.
- Ověření: mockovaná hranice restartu a skutečné veřejné status schema, active/idle/unknown/malformed/timeout i zachování současné cesty restartu; 77 cílených testů PASS; plná brána 3370 testů OK / 31 SKIP. Původní nejisté vydání se neopakuje automaticky. `reports/science_news_release_interruption_20261109.md`.


### LL-121 — Neaktivní placenou schopnost vysvětli před kliknutím

- Problém: ScienceNews zobrazoval aktivní tlačítko překladu, přestože role a
  provozní aktivace chyběly; pilotní abstrakt navíc nebyl celý zdrojový text.
- Typ: zobecnitelné
- Řešení nalezeno: 09112026
- Řešení: použít stav serveru pro vypnutí tlačítka a viditelné vysvětlení.
  Hotový uložený výsledek má zůstat dostupný i bez aktivního modelu. Ověřit,
  že neaktivní kliknutí neotevře okno/nepošle POST, čtení hotového výsledku
  nevolá model ani aktivační bránu a nevyřizuje zprávu. HTTP 403 není důkaz
  zákazu překladu; práva, úplnost zdroje a aktivace jsou samostatné podmínky.
  Ověřeno 73 cílenými testy včetně 12 Node případů, fyzická přejímka ještě chybí.


Doplnění 09112026 k LL-121 (skutečný překladový pilot): jedinečný Sol/medium
Standard tah vrátil celý zkontrolovaný překlad za 0,5995 kreditu (usage
6980 input / 1002 output). Vstupní UTF-8 byte proxy 3507 nezahrnovala celou režii
runtime a není horní mez účtovaných vstupních tokenů; cenu odvozovat od jedinečné
usage účtenky. Raw receipt a schválenou přípravnou kartu nepřepisovat dodatečnou
kontrolou. Samostatně rozlišit programovou přejímku, Datovo porovnání významu,
Mílovu četbu a pozdější připojení výsledku do UI. Pro opětovné zobrazení nebo
přenos již hotového překladu nepouštět další modelový tah.


Doplnění 10112026 k LL-121 (uložení a aktivace): domluvené ukládání celého českého
článku musí chránit UI i server, nestačí možnost uložit abstrakt a překlad někdy
později. Čerstvá validace bez zahájení akce smí uvolnit UUID, ztracená odpověď nebo
attention ne. Hotový hashovaný překlad přenášet bez dalšího modelu; starý zmrazený
pilot po adopci kódu nepřipínat znovu. Měsíční rozpočet má u dokončených započítat
vykázané náklady a držet plné rezervy jen neukončených/nejistých. Installer má
ověřit skutečně servírovaný kód i roli a zapsat launch intent před bootstrap.
Pro společnou operaci použít odlišný vnější zámek od atomic_write_json účtenky,
aby se write uvnitř nezablokoval vlastním sidecarem. Ověřeno 112 cílenými a
2964 plnými testy (5 SKIP); jeden živý cached save, nula modelů či spuštěných služeb.


Doplnění 10112026 k LL-070 (ScienceNews): skutečný instalovaný617f3e0d
prokazatelně odmítá science_news_editor v dočasném kandidátním JSON. Jeho role
jsou symlinkem na main. Proto nový config připravit a testovat izolovaně,
nejdřív registrovaně upgradovat kompatibilní runtime a až potom zveřejnit binding.
Test main parseru ani úspěšná lokální brána nezastupují tento čtecí audit.
Zdroj reports/science_news_aad367c7_integration_20261110.md.


Doplnění 10112026 k LL-070 (izolovaná přejímka): celý `.venv` nesdílet
přes symlink, pokud read-only runtime status ověřuje i rodiče stavového rootu.
Guard správně vrací state_alias_refused. Izolovaná kopie má vlastní skutečný
`.venv` adresář a sdílí jen interpret/knihovny; recovery stav ani jeho aktivační
konfiguraci nepřenášet a guard neoslabovat. Čtyři bootstrap testy po úpravě
prostředí PASS, produkční kód beze změny.


### LL-122 — Ověřování zachovaných upozornění nesmí záviset na pořadí pole

- Kontext: jediný skutečný save proběhl za 0,32 s, ale stejné dva alarmy se z EventKit vrátily obráceně. Pořadový JSON comparison vrátil edit_unknown a bezpečnostní zámek správně blokoval další úpravy.
- Řešení: porovnávat multimnožinu přesných časových hodnot alarmů, zachovat počet/duplicity a přesnou rovnost všech ostatních polí i obou nativních ID. Historický žurnál normalizovat při read-backu; nikdy znovu save.
- Důkaz: Swift FAIL→PASS pro alarm reorder, skutečně změněný alarm dál unknown. Reálný read-only recover potvrdil jediný match obou ID, žádné odlišné pole, alarm_order_normalized=true a calendar_writes=false.
- Při novém podpisu helperu může macOS vyžádat nový grant. Nezapomenout původní request_id; UI musí nabídnout povolení a následné read-only ověření. Viditelná lišta zůstává ve viewportu. Report reports/calendar_edit_alarm_order_recovery_20261110.md.


### 2026-11-10 — Tichý příběhový obraz není audio replika

- Kontext: nová šestá scéna MMTX, část 9 má podle schváleného scénáře jen mlčení.
- Řešení: explicitní tichý krok v katalogu/dialogu, nulové repliky, žádné vytvoření Audio ani placené syntézy; schovat a vyprázdnit předchozí bublinu, vypnout Repeat a ponechat ruční Next picture. Vizuální přechod oddělit od počtu vyslovených vět.
- Ověření: Node VM prošel 67 mluvených replik i tichý krok, pozdní callback a Back/Forward v tichu nevytvořily Audio; syntetický builder ticha nezaložil účtenku, MP3 ani požadavek. Safari ověřilo viditelný obraz bez bubliny. Celkem 52 cílených kontrol PASS; fyzická přejímka je samostatná.


### 2026-11-10 — Návaznost MMTX není důkaz viditelného Next

- Problém: od čtvrtého obrazu nové šestky tvořily široký obrázek a dialog vyšší obsah než okno; Next byl pod viditelnou plochou. Testovaný stavový automat byl funkční, skutečný uživatel přesto nemohl běžně pokračovat.
- Řešení: pro dialog pod obrazem vyhradit viewport grid 100svh se zmenšitelným řádkem obrázku (minmax(0,1fr), object-fit:contain) a samostatnými auto řádky dialogu a ovládání. Kontrolovat celý Next ve skutečném okně, nejen v AX stromu, HTTP či mocku Audio.
- Ověření: screenshot skutečného přehrávače 4 / 1/7 ukázal obraz, text a celé Next v okně; následné živé pozorování dosáhlo 5 / 5/7. 53 cílených testů PASS. Přímý odkaz #picture=4 umožňuje opakovat ruční přejímku bez přeskakování zvukové brány.


### 2026-11-10 — Český text a české čtení mají odlišný režim i frontu

- Kontext: MMTX potřebuje postupně zapnout překlad jako text a pak i čtení, bez změn schválené angličtiny.
- Řešení: explicitní tři režimy, samostatný překlad svázaný s anglickou větou a MP3, sekvence EN→CS s jedním aktivním Audio a tokenem. Čistě textový režim nepřehrává český zvuk; vypnutí za běhu češtinu zastaví a zneplatní callbacky. Chybu angličtiny nelze obejít přepínačem. Optional localStorage nesmí blokovat přehrávač.
- Ověření: 58 cílených testů, všech 67 dvojic a ticho, změny režimu během řeči i v klidu, chyby a Repeat, historie, uložená volba i zablokované úložiště. Původních 98 podkladů a 9 účtenek beze změny; nové CZ MP3 oddělené a jednorázové.


### 2026-11-10 — Rozhovor a obrazové zadání potřebují jedno potvrzované shrnutí

- Problém: samostatná pole změnit/zachovat a historie rozhovoru mohou současně instruovat obrazový model a vzájemně si odporovat.
- Řešení: architekt navrhuje jeden strukturovaný souhrn; nerozhodnuté úvahy drží zvlášť. Člověk potvrdí právě zobrazenou verzi i podklady, server ověří jejich token a do obrazu neposílá staré volné poznámky/historii. Pozdní odpověď nesmí přepsat novější uloženou práci. Společný půdorys a míry patří celé místnosti, automaticky se přikládají a jejich revize váže souhrn i obrazové potvrzení; trvalé mazání musí zohlednit i automatické reference mimo variantový výběr. Název nového výsledku je samostatná metadata ze schválených změn; ruční přejmenování nemá vyžadovat placenou obnovu souhrnu. Číslování shod musí být transakční a obnova zachovat původně schválený název.
- Ověření: syntetické serverové/UI testy změněných podkladů, revize, poznámek, nerozhodnutých otázek, nejistého výsledku a idempotence; Safari potvrdilo celý tok bez placeného modelu. Report `reports/interior_conversation_brief_20261110.md`.

### 2026-11-10 — Novost slovníčku se ověřuje proti skutečně použitým větám

- Kontext: MMTX šestka potřebuje jen hesla nepoužitá v předchozích pěti scénách.
- Řešení: číst audio manifesty i deklarované EN dialogy/pokyny/slovníčky; u sdíleného skriptu omezit správnou scénu. Mapovat tvary explicitně a evidovat výskyt nové položky v novém příběhu. Trees není nové po tree, nová významová spojení se porovnávají jako celek. Existující audio převzít jen při shodě textu, hlasu, tempa a otisku.
- Ověření: deset zdrojů shodných s vydaným f7a4ab58, 450 úseků / 191 lemmat; 77 nových doložených hesel. Test vloženého starého hesla zablokoval generování před transportem. 20 přesných CS nahrávek převzatých, 74 cílených testů PASS. Viz mmtx_scene06_dictionary_audit_20261110.json.

### 2026-11-11 — Číslované kapitoly MMTX musí spouštět stav, ne pouze obrázek

- Kontext: Přátelé obsahují několik ilustrací jedné hry a samostatný rozhovor uvnitř owlGarden.
- Řešení: čísla mapovat na skutečné kapitoly a jejich vstupní fáze; při přímém vstupu do rozhovoru zachovat cleanup, nový sequenceId, reset a původní dialog/pokračování. Samotné přepsání src nespustí odpovídající dialog ani interakci. Více animačních fází terče nečíslovat jako samostatné hry bez výslovné dohody.
- Ověření: skutečné místní Safari prokliklo všech pět vstupů, odpovídající obrazy, návraty a Escape; 20 cílených testů a statická brána OK. Původní pracovní předpoklad pětky Míla následně opravil: Přátelé jsou čtyři části, Lesní škola má vlastní ikonu. Nabídka 1–4 / 2×2 a samostatná ikona ověřené v Safari, 20 cílených testů a statická brána OK.

### 2026-11-11 — Zrušená replika nesmí uvolnit čekající Next jako úspěch

- Kontext: ruční krokování čtyř částí Přátel používá async dialogy i interaktivní hry.
- Řešení: oddělit dokončení zvuku od potvrzení Next, tokenovat všechny Audio/TTS callbacky a při návratu vyřešit pending čekání jako false. Pokračující dialog/herní handler musí kontrolovat také sequenceId, nejen stejné jméno scény. Vypnutí českého čtení dokončí pouze již úspěšně vyslovenou angličtinu; EN chyba zůstává chybou.
- Ověření: Node test prošel návrat za řeči, stale callback, přepínání jazyků, chyby a Repeat i celý příběh s herními úkoly. 40 cílených testů a statická brána OK.


### LL-123 — Trvalá idempotence domény nesmí záviset na krátké obecné cache

- Problém: obecná repository cache posledních operation_id se ořezává; dlouhodobá záležitost nesmí po jejím vyřazení přijmout stejný požadavek jako novou akci ani vrátit starší stav.
- Typ: opakující se
- Řešení nalezeno: 11112026
- Řešení: v doménové transakci držet malé trvalé operation_id + otisk celého normalizovaného příkazu + identitu/revizi výsledku. Před opakováním ověřit otisk; vrátit aktuální projekci a revizi původní operace. Nová změna dál kontroluje expected_revision. Uzavření/obnovení mění generaci pro pozdní výsledky; úložiště ani nejistý požadavek neopravovat založením druhé identity.
- Ověření: syntetické hlídání přestálo restart, dvojklik, dvě souběžné instance, konflikt revizí, chybu atomického zápisu i vyřazení 258 obecných idempotentních operací; žádný živý model nebo e-mailový úkon.

- Doplnění12.11.: UI musí před POST uchovat pouze malé ID původního pokusu. Po ztracené odpovědi nebo503 čte původní stav/historii, nevytváří nové operation_id ani druhý POST. Chyba tab storage zabrání odeslání;409 uchová draft a vyžaduje vědomé otevření čerstvé revize. Ověřeno Node regresí a skutečným syntetickým UI průchodem.

### LL-124 — Plánovaná služba musí zajistit svou runtime závislost i bez otevřeného chatu

- Problém: po restartu Macu běžel e-mailový LaunchAgent, ale sdílený App Server
  startoval až připojením Human–Adama. Chybějící socket blokoval i ranní běhy
  po probuzení; loaded/enabled samo nedokládá dokončené kontroly pošty.
- Typ: opakující se
- Řešení nalezeno: 12112026
- Řešení: po ověření role zajistit sdílený server před katalogem a běžným
  modelovým posouzením. Start napříč Cockpitem a službou serializovat stabilním
  souborovým zámkem; zdravý server převzít. Existující nedostupný socket není
  oprávnění ke kill/unlink ani k opakování nejistého modelového tahu. Status,
  readiness a hotový/noční/zakázaný běh zůstávají bez startovacího účinku.
- Ověření: 166 cílených testů a plná brána3520 testů OK /31 SKIP,
  včetně zámku drženého jiným procesem.
  Skutečný izolovaný CLI při souběhu provedl jeden start a jedno převzetí;
  katalog10 bez thread/start a turn/start. Dnešní registrovaný resume obnovil
  sdílený server se stejným business otiskem, nastavením a rolí. Trvalý fix
  vyžaduje i upgrade vlastní instalované kopie; reboot/wake po nasazení je
  samostatná přejímka. Důkaz `reports/email_runtime_boot_20261112.md`.


Doplnění12112026 k LL-124 po aktivaci: přesný registrovaný upgrade zachoval
celý business otisk, nastavení i JSON rolí. Nová instalace7f47a41f má311
souborů přesně podle manifestu a readiness bez blokátorů. Její vlastní
approved_selection na izolovaném socketu skutečně spustil nový server
a při druhém volání převzal stejné PID, Terra/high,0 thread/start a turn/start.
První produkční check již dokončený slot správně přeskočil (already_completed,0).
Tento důkaz nenahrazuje skutečný reboot/wake po upgradu.

### 2026-11-12 — Čtecí projekce nesmí zavolat obnovu stavu jako vedlejší účinek

- Kontext: HA-01 skládá modelový tah, dokončování a publikování pro budoucí UI.
- Řešení: mapovat jen povolená pole zdrojových snímků. LunaReleaseStore.status() může při opuštěném workeru změnit účtenku; v čisté projekci použít pouze load/public_job. Původní doklad nepřepisovat ani při pozdějším přesném důkazu deploymentu. Při změně scope/session během sběru vrátit neověřený snímek.
- Ověření: integrační kontrola odmítá volání status recovery, před/po má shodné soubory i mtime; testy staré/cizí účtenky, nového požadavku, rotace a dodatečné verifikace procházejí.

### 2026-11-12 — Otevřený panel není důkaz dokončeného vykreslení

- Kontext: HA-02 procházel základními DOM aserty, ale vizuální snímek výsledků odhalil přerušení renderWork kvůli chybějící legacy projektové kontinuitě.
- Řešení: tolerovat null v nepovinném kontinuitním zdroji a ověřovat výsledný obsah workMeta i dostupné akce podle jejich skutečných bran. Kombinovat vykonávané DOM scénáře, geometrii a vizuální kontrolu; přesná šířka viewportu musí být změřená, ne odhadnutá z velikosti okna.
- Ověření: regresní Node VM null scénář, 271 cílených testů OK a 200 skutečných browser kontrol PASS včetně vykreslených výsledků, tabů, souhlasů a nula POST požadavků.

### 2026-11-12 — Rozdělení front nesmí obejít stávající bezpečnostní guard

- Kontext: HA-03 odděluje RPC, typované odběry a legacy důkazy tahu; ScienceNews guard kontroluje také item/started a neznámé události s item payloadem.
- Řešení: kompatibilní receive cesta musí zachovat všechny položky, které původní guard vyhodnocuje, nejen dokončené nebo známé typy. Neplatný kritický payload zneplatní spojení, nezmizí jako nepovinná telemetrie. Vadné novější usage naopak musí označit měření jako nedostupné, aby nezůstalo staré číslo aktuální; nesmí samo zrušit jinak potvrzené doručení.
- Ověření: regresní testy volají skutečný ScienceNews one-turn guard přes produkční dispatcher a klienta; odmítnuté item/started i neznámé item payloady. Neplatný poslední total odstraní předchozí platnou hodnotu, ale jeden user item/start/final dál potvrdí doručení. Bez modelového volání.


### LL-125 — Přijetí požadavku musí přežít jeho čekající HTTP spojení

- Typ: opakující se. Řešení nalezeno: 12112026.
- Problém: ztracená HTTP odpověď ani chybějící browserový stav neprokazují, že se modelový požadavek neprovedl. Nové ID při obnově by vytvořilo druhý tah; pozdější job stejného projektu nesmí nahradit původní child-job vazbu.
- Řešení: trvalé přijetí a otisk přesného zadání/oprávnění, serverově vlastněný worker s původním profile lockem a file lease, durable dispatch bariéra před RPC. Reload čte stejné ID. Restart obnovuje jen původní canonical/completion důkaz; bez něj neověřeno. Identitní doklady se nevyřazují s krátkou historií. Child job ID je po prvním navázání pevné. HTTP wait není vlastník provedení.
- Ověření: HA-04 fixture se skutečným pádem vlastního Python procesu po dispatch, legacy HTTP disconnectem, dvěma klienty, selháním persist/startu, retencí/cursorem a odmítnutou náhradou dokončovacího jobu; bez modelu. Report human_adam_ha04_server_work_20261112.md.


### LL-126 — Hotový mailový slot není důkaz kontroly hlídané záležitosti

- Typ: opakující se. Řešení nalezeno: 12112026.
- Problém: completed_slot nebo nulová dávka přeskočí nově splatnou kontrolu. Zdraví poslední dávky není důkaz úplnosti zdroje; pozdní model nesmí posunout starý zdrojový snapshot za slíbený termín.
- Řešení: samostatný deterministický průchod ve finish původní služby, bez opakování mailového posouzení. Oddělit as_of od dokončení scanu; při každém novém scanu zneplatnit starou úplnost. Negativní podnět jen pro úplný čerstvý zdroj ve stejné epoše a snapshot od termínu dál. Pauza, backlog, chyba, nejasná vazba či starý worker znamenají neověřenost. Jedna identita aktuálního podnětu na věc/generaci/termín/novou zprávu.
- Ověření: syntetické dva monitory a restart, prázdný i dokončený mailový slot bez nového modelu, pomalé posouzení přes deadline, chyba/epocha/backlog a starý heartbeat bez falešného Běží. Report email_followups_monitor_20261112.md.


### LL-127 — Návrh drží uživatelský základ, nikoli každou technickou revizi

- Typ: opakující se. Řešení nalezeno: 12112026.
- Problém: background kontrola zvyšuje revizi během modelového posouzení. Nemá zahodit návrh nad nezměněným cílem; naopak ruční změna, vyřízení nebo jiné podklady nesmějí přijmout starý výsledek.
- Řešení: před jediným běžným tahem atomicky zmrazit konkrétní source_digest, ID pokusu, generaci a otisk uživatelských polí včetně poslední ruční revize. Technické kontroly otisk nemění; ruční úpravy, nová generace, zdrojový drift či vypnutí dovolí jen neaktuální původní účtenku. Přijetí do UI navíc kontroluje aktuální celkovou revizi a původní citovaný podklad. Mění jen navržený další krok a kdo je na řadě; Vyřízeno je zvláštní uživatelský úkon. Ruční přiřazení po posouzení nikdy nespouští nový placený průchod.
- Ověření: simulované posouzení souběžně s technickou kontrolou zůstane přijatelné; ruční editace/uzavření/znovuotevření/vypnutí/výměna zdroje výsledek zneplatní. Node/HTTP a vlastní headless browser ověřily původní účtenku, žádné dvojí přijetí/tah a zachovaný cíl/lifecycle. Report email_followups_assessment_20261112.md.
### 2026-11-12 — Ztracené přijetí dlouhé práce řeší dohledání identity, ne druhé odeslání

- Kontext: HA-05 převádí browser z čekajícího send na HA-04 přijetí a samostatné čtení práce; HTTP odpověď může přijít pozdě nebo se ztratit.
- Řešení: před jediným POST držet stejnou klientskou referenci, po nejistotě pouze GET podle původní identity. Cursor/revision nesmí jít zpět, staré scope/generation se neuplatní a finální stav se neoživí opožděným snímkem. Čtecí obnova nesmí kopírovat původní text do nového send. Oddělit poslední změnu od času úspěšného čtení.
- Ověření: vykonávané Node scénáře skutečné cesty odeslání prošly dvojklik, ztrátu ACK, opožděné ACK po novějším čtení a přípravnou chybu bez druhého POST. Browserový polling zachová draft/selection/starší chat/řeč a po finálním dokladu skončí. Žádný skutečný modelový tah.

### LL-128 — Zapnutý příznak není důkaz nové kontroly služby

- Typ: opakující se. Řešení nalezeno: 12112026.
- Problém: kompatibilní kód v main není instalovaná hodinová kopie; starý heartbeat po zapnutí nebo stejný slot po reaktivaci nesmějí dokazovat nový běh. Chybějící úplný scan není důkaz absence odpovědi.
- Řešení: registrované pause/prepare/upgrade, přesný manifest a readiness skutečné kopie, potvrzený opt-in s kontrolou vlastní instalace/commitu a zámkem workeru. Aktivace zneplatní technický čas/slot, ne kurzory či obchodní evidenci. Čekat na skutečný nový launchd heartbeat; source_unverified ponechat do přirozeného dalšího scanu.
- Ověření:67 cílených a3730 plná sada PASS; upgrade322 souborů zachoval162 položek i ruční údaje/kurzory/nastavení/role. Nový heartbeat1 věc/0 proposals a živé API true; source_verified přesný původní zdroj, bez historického scanu či modelu. Report email_followups_activation_20261112.md.

Doplnění13112026 k LL-128: samostatný dohlížitel odděluje vlastní čerstvost,
heartbeat sledované služby, skutečnou úplnost všech zdrojů a ověřeně běžící
delší práci. Současné výpadky sdružuje; před POST rezervuje doručení a
nejistotu po pádu neopakuje. Souběh, restart a disková chyba po send ověřené
izolovanými testy. Ostré zapnutí a externí watchdog jsou zvlášť.


### LL-129 — Schránka Macu neprokazuje obsah schránky iPhonu

- Typ: opakující se. Řešení nalezeno: 13112026.
- Problém: uživatel vidí zkopírovanou Pushcut URL na telefonu, ale pbpaste na Macu čte jiný text. Z toho nelze vyvozovat nesprávné kopírování; příčina přenosu nebyla doložená.
- Řešení: obsah nevypsat, bezpečně validovat a oddělit schránky obou zařízení. Po soukromém získání prvního webhooku lze další oznámení v témže známém účtu adresovat přesným zadaným názvem podle dokumentovaného Pushcut formátu; není třeba další přenos secretu. Nesestavovat jiný účet ani neznámý název. Skutečné HTTP přijetí a fyzické doručení ověřit odděleně, nejistý POST neopakovat.
- Ověření: první clipboard URL soukromě uložená, název SamanthaDohledProblem ověřený bez secret výpisu; automatický skutečný SSD incident accepted1. Obnova nakonfigurovaná, její přijetí/doručení zůstává otevřené. Report agent_supervisor_20261113.md; https://www.pushcut.io/support/notifications .


### LL-130 — Rychlá knižní karta musí projít celým starým čtecím a editačním řetězcem

- Typ: opakující se. Řešení nalezeno:13112026.
- Problém: odstranění povinného umístění/anotace pouze ve formuláři nestačí; původní backend a editor vyžadují úplnou knihu. Ztracená HTTP odpověď po zápisu navíc může vést k duplicitě.
- Řešení: explicitní základní typ karty v témže archivu, skutečně chybějící údaje bez falešných zástupných textů, kompatibilní přehled/editor/search. Rezervovat stabilní identitu před zápisem a po výpadku číst původní výsledek; další exemplář je samostatné výslovné rozhodnutí. Při doplňování umístění kontrolovat revize všech zvolených knih a zachovat cizí změny i po částečném selhání.
- Ověření: skutečný process crash, chyba disku po publikaci a uprostřed batch, souběh dvou zápisů, editace/replay/vyřazení, Node a headless HTTP disconnect+reload bez druhého záznamu. Viz book_quick_inventory_20261113.md; fyzická iPhone kamera samostatně.

Doplnění13112026 k LL-130: kamerový/WASM pilot ověřit i s produkčními HTTP
hlavičkami a celou stránkou. Izolovaná komponenta bez Permissions-Policy/CSP
může projít, zatímco skutečný dokument kameru nebo WASM zakazuje. Povolení
omezit na potřebný hlavní dokument a pevný katalogový host, ostatní trasy
ponechat v původní politice. Ověřeno skutečnou HTTP odpovědí a prohlížečem
s mock video-only kamerou, stop tracků a dekódováním WASM.

### 2026-11-12 — Append do tahu nesmí zrušit ani rozvolnit důkaz původního zadání

- Kontext: turn/steer může přidat další userMessage do stejného tahu; dosavadní kontrola všech user items jako jediné by po platném doplnění zneplatnila výsledek, obecné povolení více vstupů by zase obešlo guard.
- Řešení: opt-in ledger odděluje právě jeden původní client ID od přesných command IDs rezervovaných před RPC. Původní started/final/completed důkazy zůstávají; cizí/duplicitní vstup neprojde. Samostatná trvalá command účtenka rozliší přijetí, odmítnutí a nejistotu. Ztráta ACK, journalu nebo volajícího nikdy neznamená nový start; rodičovská journal bariéra a doménový otisk přežijí kompakci.
- Ověření: produkční client/dispatcher/Hub a HTTP fixture provedly série deseti doplnění do jediného turnu se stejným oprávněním. Selhání ukládání/HTTP/calleru, cizí ACK/generace, změna kontextu a dokončení během doplnění nevyvolaly druhý RPC ani nepřepsaly rodičovský výsledek. Žádný skutečný modelový pokus.


### 2026-11-13 — Nový learner nesmí rozbít druhou aplikaci se sdílenými zdroji

- Kontext: Vocabulary EN83 načítá původní `vocabulary-en/app.js` a `styles.css`.
  Nová galerie EN potřebuje katalog, který data EN83 nemají.
- Řešení: před přepsáním vstupního JS/CSS vyhledat ostatní konzumenty. Novou
  galerii oddělit do `gallery.js`, `model.js`, `gallery.css`, původní sdílené
  soubory zachovat. Metadata patří do autorského katalogu a překládají se podle
  přesného významu na neměnné UID/audio ID, nikoli podle aktuálního řádku.
- Ověření: EN83 i původní app.js/styles.css mají nulový diff; cílená přejímka
  potvrzuje obě vstupní HTML, stabilní audio po přesunu/vložení řádku a oba
  významy orange. Všechna starší pole 425 karet zůstala obsahově shodná.


### 2026-11-13 — Terminálový projekt nepatří automaticky do tabulky proudů

- Kontext: tabulku ACTIVE_PROJECTS spotřebovává katalog Human–Adam. Nový aktivní
  řádek Vocabulary EN bez záznamu v WORKSTREAMS způsobil testový nesoulad.
- Řešení: samostatný terminálový projekt evidovat v určené netabulkové sekci
  s pamětí a handoffem; pouhé místní zadání nezakládá nový proud v Cockpitu.
- Ověření: po přesunu zápisu všechny testy WorkstreamCatalog prošly; další
  0,5s SDK startup timeout je samostatný výsledek, nikoli zelená celá brána.


### 2026-11-13 — Negativní RPC deadline patří až za inicializaci testovacího klienta

- Kontext: syntetické SDK testy měly 0,5–0,6 s pro úmyslně mlčící RPC, stejná
  hodnota se omylem používala už při konstrukci CLI/SDK proxy. První handshake
  naměřený 1,1645 s pak selhal dřív, než test vůbec poslal testovanou operaci.
- Řešení: nejdřív dokončit inicializaci se stávajícím standardním limitem,
  potom nastavit původní krátkou operační mez. Nezvyšovat testovanou RPC mez,
  nepřidávat retry a neměnit produkční transport. Skutečný test selhání
  inicializace si ponechá vlastní původní deadline.
- Ověření: 71 cílených PASS s ResourceWarning jako chybou; zůstává jediný
  turn/start, decline approvals, ukončení pouze vlastní proxy a původní
  delivery_unknown. Měření/proxy byly jen proti vlastním syntetickým socketům.

- Finální ověření: plná kanonická brána 3685 testů / 566,387 s, 5 SKIP, OK;
  zmrazené SDK zdroje jsou po běhu shodné.


### 2026-11-13 — Nový Pages projekt musí projít až skutečným publisherem

- Kontext: Vocabulary EN potřebuje vlastní publikační identitu a HTTP cestu.
  Samotná registrace v katalogu a PAGES_PROJECT_PATHS nestačí: publisher má
  samostatný seznam povolených smoke cest. Mock celé serverové odpovědi by
  chybějící vnitřní povolení neodhalil.
- Řešení: zkontrolovat katalog, mapu i vnitřní whitelist; cíleně projít skutečnou
  funkci publisheru s injektovaným runnerem a HTTP fetcherem. Ověřit přesnou
  URL se zmrazeným SHA pro nové i již hotové nasazení. Zachovat odmítnutí
  neregistrovaných cest před jakýmkoli příkazem.
- Ověření: 67 cílených publikačních kontrol PASS / 6,026 s, bez GitHubu/modelu.
  Celková brána: PASS — 3688 testů / 631,512 s, 5 SKIP, 0 failures/errors. Registrace musí být před ostrým
  předáním načtená v serverovém runtime; místní test není veřejné vydání.


### 2026-11-13 — Integrační worktree potřebuje skutečný kořen .venv

- Kontext: celý .venv byl vlastní pomocnou symlink zkratkou na již existující
  závislosti. Čtecí recovery status správně odmítl alias mezi rodiči sandboxu;
  v plné bráně selhala jediná CLI kontrola ještě před jakoukoli akcí.
- Řešení: opravit pouze prostředí integračního worktree. Vlastní zkratku
  uchovat privátně, vytvořit skutečný místní kořen .venv a referencovat stejné
  existující dependency bin/lib. Neměnit scheduler guard, produkční kód ani
  jeho testová očekávání, nic neinstalovat a nespouštět službu.
- Ověření: celý recovery scheduler 42 PASS / 0,746 s s ResourceWarning jako
  chybou; zdroje zůstaly shodné. Nová plná brána: PASS: 3823 testů / 580,485 s, 8 SKIP; 3 SDK schema kontroly následně PASS / 0,376 s, zbývá 5 původních SKIP.


### 2026-11-13 — Node test musí používat stejné nalezení runtime jako servisní brána

- Kontext: galerie spouštěla Node pod jménem `node`. Terminálové testy prošly,
  ale servisní PATH bez /usr/local/bin způsobil FileNotFoundError a zastavil
  plnou bránu před pushem (3823 testů,1 error).
- Řešení: použít stávající scripts.cockpit_quality_gate.node_binary, který
  respektuje NODE_BINARY a ověřené instalační cesty. Neměnit systémové
  prostředí a nezaměnit chybějící runtime za přeskočený test.
- Ověření:29 testů PASS v minimálním launchd PATH, včetně skutečných
  Node scénářů; rychlá statická brána PASS. Původní účtenka zůstává
  attention; nový opravený head vyžaduje novou přesnou release účtenku.


### 2026-11-13 — Start kamery nesmí čekat potichu na čtečku

- Kontext: první iPhone přejímka hlásila tlačítko bez reakce. JS před žádostí
  o kameru čekal na dynamický script; onload výjimka mohla ponechat promise
  neukončenou. Stav byl až za formulářem a chyby dekodéru se při čtení snímků
  ztrácely jako běžný nečitelný kód. Přesná příčina konkrétního iPhonu
  tím ještě není doložená.
- Řešení: vyžádat video přímo v click cestě, připravit reader/WASM až nad
  zapnutou kamerou, zobrazit stav vedle tlačítka, ohraničit načítání a chybu
  inicializace zachytit před smyčkou snímků. Zachovat generační rušení,
  aby pozdní dokončení starého skenu neukončilo nově otevřený stream.
- Ověření: FAIL→PASS pro žádost před downloadem; odmítnutí/timeout/API/WASM/
  zavření/restart PASS,60 cílených testů a statická brána PASS. Headless
  mobilní celé HTML se skutečnými hlavičkami: kamera před pozdrženým JS,
  reálný WASM a jeho blokovaná varianta s ukončením stop PASS. Fyzický iPhone
  je samostatná přejímka po vlastním p+n.


### 2026-11-13 — Větné audio má vlastní textovou identitu a normalizaci

- Kontext: slovíčkový generátor převádí čárky a středníky na tečky a má
  výjimku hlasu pro izolované cat. Přímé převzetí těchto pravidel do celých
  vět by měnilo interpunkci a mohlo přehrát jiný text po redakční úpravě.
- Řešení: samostatný větný manifest/namespace, přesný text obou vět a UID
  vedle EN/CZ. Zachovat interpunkci, soubor určit hlasem/tempem/textem.
  Před syntézou uložit privátní požadavek; při nejistotě bez uloženého MP3
  nic automaticky neopakovat. Manifest publikovat do výstupu až při úplné
  sadě. Cílový překlad přehrát pouze po odhalení odpovědi.
- Ověření: 850 skutečných MP3 dekódovaných; všech845 slovíčkových MP3
  a původní obsah beze změny. 29 cílených Python testů včetně27Node PASS,
  obě jazykové verze ověřené v nativním Safari.


### 2026-11-13 — Datové atributy dlaždic nesmí kolidovat s ovládacími prvky

- Kontext: Poslech galerie potřeboval původní text popisku. Použití
  data-label na dlaždici ji přidalo mezi globálně vybírané jazykové
  ovladače [data-label], včetně nesprávného aria-pressed.
- Řešení: Pro popisek dlaždice data-caption, pro ovládací prvky ponechat
  jejich vyhrazený atribut. Změnu poslechu provést nad existujícími uzly,
  ne přerenderem; aktualizaci galerijních ARIA nespouštět při každé další
  velké kartě.
- Ověření: Původní FAIL→PASS pro CZ popisky a EN poslech; finálně30
  cílených Python včetně34Node PASS /14,959s, Safari desktop.
