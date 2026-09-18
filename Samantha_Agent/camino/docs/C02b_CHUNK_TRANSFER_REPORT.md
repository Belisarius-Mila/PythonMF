# C02b — report experimentu částí a iOS fronty

Datum: 2026-09-18

## Výsledek

C02b je zahájené a má ověřené lokální checkpointy. Syntetický receiver přijímá
výchozí 8MiB části, trvale eviduje manifest a bezpečně uložené části, po
přerušení vrací přesný seznam chybějících indexů a teprve po sestavení a
serverové kontrole celkové délky a SHA-256 vytvoří jediný objekt a účtenku.

Stejná relace, část i finalizace jsou idempotentní. Jiná identita nebo jiné
bajty jsou konflikt bez přepsání. Chybný hash části, chybějící část a chybný
celkový hash nedostanou potvrzení. Ztracenou odpověď finalizace lze nahradit
dotazem na stav existujícího Assetu.

Čistý Swift model fronty odděluje lokální byte progress od serverového důkazu.
Po relaunchi bere serverový snapshot jako autoritu, při nedostupné síti říká
čekání a stav `Ověřeno na Macu` dovolí jen serverové `verified`. Jednorázové
mobilní povolení se váže na konkrétní dávku a neplatí pro nové médium.

Druhý checkpoint přidal oddělenou aplikaci `Camino Transfer Test` 0.4.0 (2).
Vytváří pouze syntetický soubor 96 MiB + 257 B, vede trvalý journal a pro jednu
background `URLSession` připravuje nejvýše dvě 8MiB části. Token ukládá do
Keychain, vyžaduje HTTPS a nemá oprávnění k Fotkám, mikrofonu ani datům Camino
Audio. Po návratu porovnává frontu se serverem a nepoužívá veřejný fallback.
Dostupná povolená Wi-Fi může spustit automatickou reconciliaci;
`Synchronizovat nyní` zůstává ruční provozní záloha.

## Automatické ověření

- Python C02b receiver: 10/10 PASS.
- Swift transfer core: 19/19 PASS.
- iOS simulátor UI: 1/1 PASS; vytvoření 96MiB syntetické dávky, viditelný
  journal/progress a výchozí zákaz mobilních dat.
- Nepodepsaný Debug build pro `generic/platform=iOS` arm64: PASS.
- Podepsaný Debug build 0.4.0 (2), strict podpis, instalace a spuštění na
  iPhonu 14 Plus / iOS 26.6.1: PASS. Vývojový profil platí do 24. září 2026;
  Camino Audio nebylo odinstalováno ani změněno.
- T043 ovladač, C02b receiver a C02a regrese: 28/28 PASS.
- Sdílený T043/T047 ovladač a registr workflow: 11/11 PASS.
- Pokrytý syntetický velký soubor má dvě plné 8MiB části a krátký konec. Test
  nejprve odešle části 0 a 2, po dotazu doplní jen část 1 a ověří jediný
  výsledný objekt se shodným hashem.
- Samostatně jsou pokryté konflikty, chybné hashe, chybějící část, stav
  `verifying`, idempotentní retry, ztracená odpověď, zákaz veřejného bindu,
  relaunchová reconciliace, scope mobilní dávky, trvalý journal, strop dvou
  připravených částí, odmítnutí neplatného serverového snapshotu a koaleskování
  žádosti, která přijde během už běžící reconciliace.

- Plná projektová brána po přípravě T047: 1716/1716 PASS.

## Vazba na akceptační testy

- T043: **PASS v rozsahu syntetického C02b experimentu.** Uprostřed skutečného
  uploadu byl zapnut Letový režim. Telefon ukázal 5 % bytů, 0/13 potvrzených
  částí a 2/2 připravené; Mac doložil nedokončenou relaci `uploading`, 0/13
  přijatých a žádný nový finální objekt. Po obnovení sítě bylo přijato 13/13,
  vznikl jediný objekt tohoto Assetu o 100 663 553 B a jeho SHA-256 se shodoval
  s účtenkou.
- T047: **PASS v rozsahu syntetického C02b experimentu.** Při první dávce byl
  telefon uzamčen během přenosu; po odemčení UI pravdivě ukázalo mezistav a
  server dokončil 13/13. Při druhé dávce byl po 1/13 přijatých částí skutečně
  nuceně ukončen proces; audit po 20 s zůstal na 1/13 bez druhého objektu. Po
  ručním relaunchi UI ukázalo 15 %, 1/13, 1/2 a server doplnil pouze chybějící
  části do 13/13. T047 má dva objekty/účtenky, oba 100 663 553 B, hashově
  shodné.
- T048: UI má pravdivé čekání bez veřejného fallbacku; cizí Wi-Fi, captive
  portal, přechod sítě a nedostupný tailnet NEPROVEDENO.
- T049: trvalý grant je omezený na jednu dávku a nová dávka vzniká bez něj;
  skutečný mobilní přenos NEPROVEDENO.
- T050: server i UI drží `Ověřuji` po dosažení 100 % bytů; řízené zadržení
  serverového ověření na fyzickém iPhonu NEPROVEDENO.

T048–T050 zatím nejsou označeny PASS.

## Pozorování a oprava z fyzického T043

První obnovovací průchod nakonec bezpečně doběhl, ale vyžadoval několik stisků
`Synchronizovat nyní`: dvě klepnutí během automatické reconciliace neměla
viditelný účinek a později se fronta jednou zastavila mezi dvojicemi částí.
Příčinou byl jediný příznak `reconciling`; callback přijatý během probíhajícího
asynchronního dotazu se zahodil a automatický průchod současně nezablokoval
tlačítko.

Build 2 používá koaleskující bránu. Impuls během aktivního průchodu nastaví
ještě jeden průchod a všechny reconciliace pravdivě označí UI jako zaneprázdněné.
Po instalaci buildu 2 vznikla třetí syntetická dávka a událost dostupné sítě ji
spustila automaticky. Bez dalšího klepnutí sama přijala 13/13 částí a skončila
`verified` se shodnou délkou a hashem. Přesné přerušení sítě se na buildu 2
neopakovalo; fyzický výpadek a bezpečné dokončení jsou z buildu 1, oprava má
samostatný regresní test a nepřerušený fyzický doběh na buildu 2.

## Rizika a hranice

- Background `URLSession`, zámek a force quit s ručním relaunch jsou ověřené na
  iPhonu; cizí Wi-Fi, captive portal, přechod sítě, jednorázová mobilní data a
  zadržené serverové ověření zůstávají neověřené.
- Receiver je izolovaný standard-library experiment, ne produkční FastAPI,
  databáze, launchd služba ani záloha.
- Prototyp při každém stavovém dotazu znovu hashově kontroluje přijaté části;
  je záměrně jednoduchý, ne výkonově hotový.
- Výchozí experimentální maximum je 512 MiB a neříká nic o budoucím
  produkčním limitu videa.
- Byla přidána pouze dočasná privátní Tailscale Serve cesta; Funnel zůstal
  vypnutý a nebyla použita reálná média. Po T043 byl receiver zastaven, cesta
  odebrána a původní Serve konfigurace přesně obnovena. Tři důkazy zůstaly.
- Registrovaný ovladač T043 ukládá token a běhový stav jen do ignorovaného
  `data/private`, přidá pouze `/camino-c02b`, ověřuje Funnel/Cockpit a při
  ukončení porovná Serve se stavem před testem.
- První potvrzený start odhalil kolizi přímého skriptového spuštění s balíčkem
  `app/email`; receiver neotevřel port a workflow trasu bezpečně odebralo.
  Entry point je opraven na `python -m app.camino_chunk_receiver` a chráněn
  regresním testem. Druhý start už receiver otevřel, ale kontrolní Python HTTPS
  skončilo na chybějícím CA řetězci; rollback znovu obnovil původní Serve.
  Kontrola nyní načítá systémový `/etc/ssl/cert.pem` bez vypnutí TLS ověření.
  Skutečný tailnet Cockpit health s tímto kontextem vrátil 200 a plná brána po
  opravě 1711/1711 PASS.
- Samostatný T047 ovladač používá nový soukromý stav. Read-only audit ověřuje
  vlastněný proces a trasu, Funnel, všechny manifesty relací, hash každé přijaté
  části a finální objekty/účtenky. Stav z T043 se s T047 nemíchá.
- Registrovaný stop po fyzickém důkazu T047 odebral pouze `/camino-c02b`, zastavil
  pouze vlastněný receiver a přesně obnovil původní Serve; Funnel zůstal vypnutý.

## Další krok

T047 je registrovaně ukončený s přesnou obnovou Serve. Potom pokračovat
T048–T050 odděleně.
