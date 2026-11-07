# Kalendář 4 — časy, upozornění, kolize a potvrzení

## 2026-11-07 13:40 CET — bod 4, upozornění a odvozené časy

Hotovo: Editor doplňuje datum konce a počítá délku z časů v uvedeném pásmu,
včetně DST. Přes půlnoc se konec neposouvá bez pozdějšího data. Ručně zadaná
délka bez koncového času zachovává správné skutečné datum konce. Vícedenní
uživatelské datum se nepřepisuje. Původ výpočtu se odlišuje od citace modelu.
Upozornění jsou standardně 24 hodin a 60 minut před začátkem/termínem;
každé lze vypnout, volba se uchová. U celodenní schůzky se počítají od půlnoci
a koncové datum je výlučné. Celodenní termín bez hodiny vyžaduje pro náhled
upozornění upřesnit čas. Upozornění se zatím neplánují do OS: skutečný zápis
události a alarmů patří bodu 5.

Hotovo: Zkontrolovat kolize a zobrazit náhled načítá výhradně vybrané kalendáře
v přesném omezeném období návrhu, i mimo výchozích 30 dní přehledu. Konečný
náhled obsahuje celý interval, místo/odkaz, přesný cíl, čtené kalendáře, kolize
a konkrétní časy upozornění. Potvrzení vyžaduje kontrolu údajů/citací a zvlášť
přijetí kolizí, jsou-li přítomné. Znovu čte kalendáře; změněný obsah nebo
vypršení ukáže nový náhled bez přeneseného souhlasu. Revize, source digest,
výběr/cíl, upozornění, kolize a pětiminutová platnost brání použití starého
potvrzení. Chybějící oprávnění/cíl, neúplný výsledek či chyba čtení potvrzení
neumožní. Souběžné změny na jiném zařízení zamknout nelze. Potvrzení neprovádí
zápis kalendáře a není povolením obejít čerstvou kontrolu v budoucím bodu 5.

Rozhodnutí: Míla výslovně požádal o automatické datum/délku, obě výchozí
upozornění a pokračování vývoje. Pokračování znamená bod 4 podle přijatého
plánu, vykonavatel Will. Nové p+n tím nebylo zadáno.


Další krok: místní checkpoint po plné bráně; samostatně schválené p+n a fyzická
přejímka nového editoru. Navrhované další kroky: bod 5 — jediný skutečný zápis,
uložení obou alarmů do EventKitu a ověření výsledku; bod 6 — přejímka iPhonu.

Technický důkaz: 112 cílených testů PASS a dalších 45 finálních regresních
kontrol PASS včetně nových závodů/vypršení. Plná brána a finální checkpoint dle
logs/calendar_review_full_gate_20261107.log a calendar_review_verified_20261107.log.
Skutečné omezené čtení čtyř vybraných kalendářů PASS, cíl zapisovatelný,
build i uložený přehled beze změny; pouze agregáty v
logs/calendar_review_native_live_20261107.log. Žádný skutečný e-mail, nový
modelový tah, kalendářový zápis ani restart/službový upgrade. Hodinový agent,
role a Datův samostatný worktree beze změn. Nový e-mailový TVBCP nedohodnutý.

Doplnění ověření: skutečné Safari nad oddělenou syntetickou zprávou a kalendářem
prošlo změnou koncového času 11:00 → 11:01 (délka ihned 61), uložením, náhledem
obou konkrétních upozornění, kolizí a odděleným souhlasem k potvrzení. Screenshot
zkontrolovaný; původní panel obnovený a vlastněný QA server zastavený. Nejde o
přejímku skutečného e-mailu/iPhonu. Důkaz logs/calendar_review_safari_20261107.log.
Plná vývojová brána PASS: 2656 testů, skipped=31, 496,185 s unit část.
Poslední drobná CSS oprava skrytých souhlasových řádků ověřená následně
28 frontend/HTTP testy a znovu ve skutečném Safari; oba výchozí alarmy zaškrtnuté,
souhlasy před náhledem skryté. Změna persistence a potvrzování byla ověřená
plnou bránou; finální CSS pokrývají doplňkové kontroly a rychlá statická brána.
