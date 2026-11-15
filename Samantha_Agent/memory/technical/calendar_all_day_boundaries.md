# Celodenní hranice EventKit

Oprava z15.11.2026, proud `project-cockpit`; poštovní návrhy zachovávají
`handoffs/continuous_personal_agent_2026_11_04.md` a projektovou paměť e-mailu.

Apple [TN3130](https://developer.apple.com/documentation/technotes/tn3130-changes-to-eventkit-in-macos13-ventura)
dokumentuje dva nativní konce stejné celodenní události: půlnoc následujícího
dne a23:59:59 posledního zahrnutého dne. Vstupní návrh dál používá výlučný konec.

Při ověření se jen celodenní23:59:59 bez zlomku sekundy převede na následující
půlnoc v konkrétním pásmu. Nejde o obecnou sekundovou toleranci. Začátek,
kalendář, název, pásmo, marker operace, místo, URL a oba alarmy zůstávají přesné.
V časované události se ani jedna sekunda nepřijímá jako ekvivalent.

`calendar_writer_v2.swift` ověřuje tuto rovnocennost nativně;
`calendar_event_time.py` stejně ověřuje Pythonovou účtenku. Všechny skutečné
nativní údaje včetně původního end zůstávají v ověřené události zachované pro
její identitu a navazující úkony. Přehled upravuje pouze výlučné end_day pro
zobrazení dnů, skutečné end nepřepisuje. Původní čtecí helper se nepřestavuje.

## Přechod a obnova

Původní `calendar_writer.swift` je neměnný zdroj již běžící generace. Nový
Python vybírá v2; místní vývoj proto neruší kontrolu starého živého buildu.
Po samostatně potvrzeném nasazení použít existující tlačítko Povolit zápis
na Macu: sestaví nový produkční helper a požádá jednou pro přesný binární otisk.
Staré buildy/journály se neodstraňují. Zastaralý build se v UI nehlásí jako hotový.

Při nevyřešeném zápisu se původní operation_id a potvrzené údaje nemění.
Povolení helperu nevytváří událost; Ověřit původní zápis volá pouze recover.
Ztráta oprávnění při recover zůstává unknown a nabídne povolení; nesmí se
převést na nový create. Ani chybějící původní událost nepovoluje další save.

## Doklady

Původní nativní logika nad in-memory EventKit reprodukuje selhání; v2 pokrývá
21 scénářů, včetně obou reprezentací, vícedenních období a obou změn DST.
Celý obsah/identity/alarmy a zákaz dalšího zápisu ověřují stejné regrese.
Nový izolovaný podepsaný helper má6 self-test kontrol bez kalendářového přístupu.
Živý pouze čtecí probe nového buildu vrátil authorization_required/not_determined,
calendar_writes=false; původní operace zatím není ověřená novým helperem.
Závěrečný plný výsledek/commit: soukromá účtenka uvedená v reportu.
