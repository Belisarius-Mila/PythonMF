# Ruční obory a odstranění starých knižních kategorií —14.11.2026

Hotovo místně: původní kategorie/štítky knih odstraněné z rychlého přidání,
obou podrobných formulářů, čtečky, filtrů, výchozího slovníku a současných
API voleb. Nové knižní zápisy nepřevádějí staré kategorie do metadat.
Technické značky obrázků zůstávají; obecné členění knihovna/knihy/články
ani štítky ostatních sekcí se nemění.

Obor se vybírá z26 oficiálních hlavních oborů Konspektu. Volitelné
book_subjects_manual drží uživatelskou volbu odděleně od book_classification.
Souhrn vrací výsledné book_subjects a book_subjects_origin. Ruční obor
funguje bez katalogu i bez ISBN; není automatický odhad ani katalogový důkaz.
Běžná editace jej zachová, změna ISBN zneplatní staré ruční i katalogové
zařazení. Původní durable payload bez nového pole má stejný fingerprint.
Dekodér původního categories zůstává pouze kvůli identitě starých požadavků;
rezervovaná historická metadata a transakční historie se nepřepisují.

Členění: hlavní obor → skupina Konspektu; žánr/forma a témata nezávisle.
Zdroj: https://prirucky.ipk.nkp.cz/katalogizace/monografie/072
Aplikace nyní ukládá hlavní obor, nikoli podskupinu.

Příprava živého čištění: registrované book_legacy_cleanup_preview/apply,
žádný veřejný endpoint ani automatická migrace při startu. Preview má SHA256
přesného plánu a stráže registru, všech knižních metadat, slovníku a operací.
Apply vyžaduje NOVOU přesnou globální větu, žádné rozpracované operace a
nezměněný snímek. Před prvním přepisem zazálohuje původní bajty všech
měněných souborů. Přerušení lze dokončit jen podle původního schváleného
plánu; novější změny se nepřepíší. Náhled i zálohy zůstávají jen soukromě.
Živý apply NEPROVEDEN. Nové p+n NEAUTORIZOVÁNO.

Ověření:

- 395 širších cílených testů PASS; po posledním backendovém zpřesnění41
  knihovních/persistence testů PASS včetně skutečných bajtů fotografie
  a nedotčených metadat jiné sekce.
- Reálný izolovaný prohlížeč: ruční obor při novém uložení i změna existující
  základní karty, katalogový snapshot beze změny,26 voleb, bez kategorií,
  OR/AND a závislé počty,390/1280 bez přetékání,0 výjimek a0 produkčních POST.
  Privátní výsledek browser_1794678186219606000/result.json.
- Plná brána PASS: 3908 testů / 765.447s, 31 přeskočených. Log logs/book_subject_edit_full_gate_final_20261114.log.

Míla potvrdil fyzické skenování DOSAVADNÍ vydané verze; nové editory budou
vyžadovat samostatnou přejímku po případném p+n. Žádná aktivace agentů,
placený modelový tah, publikace, přesun ani odstranění souborů neproběhly.

Vizuální kontrola odhalila předchozí CSS chybu: obecné .library-field
přebíjelo .hidden a v knižním editoru zůstávalo pole Tagy. Cílené pravidlo
pro skryté pole uvnitř editoru opravuje jeho skutečné skrytí. Browser ověřil
computed display:none pro knihu a opětovnou dostupnost u článku. Předchozí
neúplný běh brány byl zastaven, jeho log není PASS; rozhoduje nový finální běh.


## 2026-11-14 19:58 CET — Dorovnání soukromého mostu po vydání

Hotovo: Ruční knihovní obory jsou vydané a jednorázové čištění starých
kategorií dokončené. Přesné zálohy, všechny knihy, obrázky a zařazení zachované;
historie operací se neměnila. Kanonický stav nyní odpovídá dokončeným účtenkám.

Rozhodnutí: Míla zadal pořadí knihovna (jemnější skupiny Konspektu), potom
konkrétní iPhone UI a poštovní A+C. Vývoj skupin schválený; nové p+n ani
hromadná migrace tím nejsou povolené. Vnější watchdog zůstává pouze návrh.

Další krok: Zpětně kompatibilně doplnit skupiny z vybraného MARC072 a jejich UI.
Navrhované další kroky: Fyzická přejímka nového zařazení, konkrétní mobilní
průchod a poté poštovní scénář v Downloads. Skutečná noc dohledu čeká na Mílu.

Technický důkaz:24096145 / cc7bb358f72b61b428a8f4fb09fa7c7b,
push/deploy confirmed,3908 PASS/smoke5. cleanup_receipt:done,3 knihy,
11 položek,5 souborů, přesné původní zálohy a0 zbývajících kategorií.
completion_receipt/live_verification v data/private/book_subject_edit_20261114/.
Cizí Vocabulary EN4e5e18a70db086fa6eac083f0f9e2984 ověřené jedním programovým
čekáním:completed,3912 PASS,push+Pages confirmed,HTTP200. Nic se neopakovalo.
Dnešní health potvrzuje0f157594c8dba03b/PID77219; není to důkaz fyzického UI.
