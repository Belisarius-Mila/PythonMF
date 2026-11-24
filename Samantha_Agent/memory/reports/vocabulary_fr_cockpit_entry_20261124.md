## 2026-11-24 14:49 CET — Přímý vstup do společného pexesa z Francouzštiny v Cockpitu

Hotovo: Místně připravené propojení stávajícího vstupu „Francouzština Jana“
v Cockpitu s tlačítkem „Hrát spolu na dálku“ uvnitř jejího pexesa. Jana
nemusí ručně kopírovat adresu herní služby. Společná hra se otevře v nové
kartě se 12 právě vybranými slovíčky; původní Francouzština zůstane otevřená
na své adrese se stejnými osobními označeními a filtry. Kopíruje se už jen
pozvánka pro spoluhráče. Běžící dočasný pilot zůstává beze změny.

Rozhodnutí: Míla požádal o integraci přímo do Francouzštiny otevírané
z Cockpitu. Zachovat její dosavadní Pages původ a osobní data. Cockpit
předá aktuální adresu pouze ověřené běžící hry ve fragmentu vstupního
odkazu; konkrétní dočasná adresa se neukládá do Gitu. Katalog nic nespouští.
Nové vydání webu ani restart Cockpitu tímto vývojem ještě neproběhly.

Další krok: Samostatně schválit p+n FR Pages a Cockpitu přes registrované
předání Terře; potom ověřit skutečný katalog, publikovaný klient a vstup
Jany do nové partie. Stávající HTTPS pilot mezitím zůstává použitelný.
Navrhované další kroky: Fyzicky ověřit jeden vstup z Cockpitu a poslání
pozvánky druhému Macu/Linuxu. Trvalou adresu řešit až po večerní přejímce.

Technický důkaz: 39 cílených Python kontrol PASS včetně 60 FR JS scénářů
(5 nových pro vstup z Cockpitu) a 16 online JS scénářů. Výběr a osobní
stav zůstávají zachované, adresu lze obnovit po změně filtrů/reloadu,
nové spuštění z Cockpitu nahradí starou dočasnou adresu. Neplatné adresy,
cizí původ, credentials, port, cesta, query či fragment se nepoužijí jako
cíl. Při chybě či zastavené službě zůstane běžná Francouzština dostupná.
Lokální katalog poskytuje propojený odkaz, živý Cockpit má ještě původní
odkaz: vydání je nutné. Stávající hra přes HTTPS odpovídá200 a její procesy
nebyly restartovány. Kontrola totožnosti procesů je nezávislá na LC_ALL/TZ
volající služby a rozpozná starší české i nové anglické datum startu.
První doménová brána1377 PASS; finální brána, SHA a počet čekajících commitů:
private vocabulary_fr_cockpit_entry_20261124/completion.json.
