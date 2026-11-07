# Kalendářový agent — bod 3, návrhy z vybraných e-mailů

2026-11-07, Will na main; project-email-cases. Míla po dokončení vývoje výslovně
autorizoval společné Terra p+n včetně Datova rušícího b4b72ab0.

## Výsledek a hranice

V lokální verzi E-maily k řešení přibývá Navrhnout událost. Otevření pouze čte
existující koncept. Teprve samostatné Připravit návrh modelem po vysvětlení
rozsahu odešle vybranou zprávu schválené roli continuous_email. Neprochází historii,
neposílá modelu kalendářový obsah, neodesílá zprávy a nevytváří kalendářové události.
Konec nebo délka, datum, pásmo a místo se nedoplňují mlčky výchozími hodnotami.

Časovaný termín úkolu je bodový deadline bez konce/délky, nikoli schůzka.
Model vrací schůzku, termín úkolu, ruční zpracování nebo zprávu bez konkrétní
události. Položky: název, datum a čas začátku/konce nebo délka, pásmo, místo,
odkaz a celodenní příznak. Citace jsou kontrolované jako přesné podřetězce zdroje;
samy nedokazují správnost modelové interpretace. UI to říká výslovně. Uživatel
vidí citaci, původ, nejistoty a vlastní změny. Neúplný koncept lze uložit s
upozorněními; nikdy se tím nepotvrdí čas, kolize ani zápis.

Program ověřuje formát a existenci data/času, IANA pásmo, chybějící délku,
rozpor konce a délky, půlnoc, neexistující i dvojznačný DST čas a nesoulad s
výslovným ISO/CZ datem či HH:MM v citaci. Relativní datum zůstává označené pro
kontrolu; model dostává datum původní zprávy. ICS a pravidlem rozpoznané opakování
jsou ruční zpracování bez modelu. Jiné nejasnosti rozpoznává model a přejímá člověk;
nejde o obecný deterministický parser přirozeného jazyka.

## Soukromí a jediný pokus

Vybraný zdroj se znovu čte přes existující read-only IMAPAgentSource/BODY.PEEK[]
a porovná se item_id i SHA-256 celého EML. Limit je 8 MiB EML a 256000 UTF-8 B
textového kontextu; překročení je odmítnuté před modelem, žádné tiché krácení.
Koncepty a evidence jsou v samostatném private calendar_drafts, mimo business
stav a formát původních e-mailových karet. UID pozice, odpovědi a hodinová kopie
se nepřevádějí. Modelové role zůstávají v nezměněném agent_roles.json.

Před voláním je trvalý záznam jednoho pokusu na přesný zdroj. Jiný request_id,
dvojklik, znovuotevření ani restart nevytvoří další modelový tah. Nejistý stav se
zobrazuje bez tlačítka nového pokusu. Výsledek se uchovává v private účtence;
případná ruční diagnostika není oprávnění k opakování. Úpravy mají revizi, starší
koncept nepřepíše novější. Browser zachovává rozepsané hodnoty při konfliktu,
blokuje starý GET po novém Save, při nejistém POST nepřipravuje znovu a po zavření
zastaví pouze čtecí polling. Modelový běh se zavřením editoru neopakuje.

Model pracuje v prázdném kontextu, bez skills a projektových instrukcí. MCP,
apps, pluginy, browser/computer use, image generation, shell a další nástroje
jsou vypnuté per-thread. Pojmenovaný profil má minimální čtení, vlastní prázdný
adresář a zakázanou síť; klient vyžaduje serverové potvrzení profilu. Modelový
tah výslovně žádá serviceTierForTurn=default a nepřebírá globální Fast. Není měněná
globální konfigurace. Kompatibilní mechanismus již používá Ateliér.

## Ověření

Luna připravila vymezený JS modul přes app.luna_development; 23 regresních testů
před/po PASS. Převzetí a3c0837f1ef36d4b6a4eed6c1037327f s přesným digestem
6ca8ab922a1cb6a0bed8a986b294dde53f2e83cff7ad290a8d11cdd48d764e42.
Will doplnil integraci a ochrany nejistého pokusu a opožděného čtení. Účtenky
jsou pouze private. První preflight zastavil HTTP bind v izolovaném prostředí
ještě před modelovým tahem; upravené zadání použilo frontendové kontroly.

Cílené testy: logs/calendar_draft_targeted_20261107.log; plná brána:
calendar_draft_full_gate_20261107.log. Finální checkpoint a stav jsou v
calendar_draft_verified_20261107.log, neodvozovat nasazení z lokálního testu.
Jeden skutečný modelový tah nad umělou zprávou prošel: gpt-6.1-terra,
správné datum 2026-11-11, 10:00–11:00, Europe/Prague, místo i odkaz; 7171
vstupních a 214 výstupních tokenů, žádný retry, skutečná pošta se nečetla.
Soukromý zdroj a výsledek zůstávají ve vymezeném syntetickém pilotu.
Cenový helper pro Terru nevrací odhad; nevymýšlí se cena ani nová role.

Živý nulový preflight pojmenovaného profilu PASS, žádný turn/start ani modelový
tah. Legacy readOnly.access zde server odmítá, proto se nepoužívá. Obecná
[OpenAI Docs — App Server](https://learn.chatgpt.com/docs/app-server) zmiňuje obě
cesty, ale autoritou kompatibility je tento živý výsledek. Vypínané vlastnosti
ověřené v živém experimentalFeature/list a [oficiální konfiguraci](https://learn.chatgpt.com/docs/config-file/config-reference).

Safari UI host je nedostupný (cgWindowNotFound při dvou pokusech); browserový
kontrakt PASS není fyzická Mac/iPhone přejímka. Skutečný e-mail nebyl zvolený.
Nový macOS souhlas kalendářového helperu z bodu 2 a výběr kalendářů jsou stále
otevřené a návrhovou část neblokují. Společné Terra p+n s Datovým rušícím commitem je nyní autorizované.
Další krok: přesná integrace a registrované vydání, potom uživatelem vybraný
e-mail; bod 4 kolizí až samostatně. Nový TVBCP
nebyl dohodnutý a nevzniká.

Finální vývojová brána: 2726 testů / 31 SKIP, bez selhání PASS, 441,869 s unit část.
Společné vydání a provozní důkaz: logs/calendar_draft_retirement_release_20261107.log
a calendar_draft_retirement_verified_20261107.log. Starší placené hlasové opravy
se samostatně nevydávají.
