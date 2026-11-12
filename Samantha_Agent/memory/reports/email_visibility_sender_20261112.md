# Příště nezobrazovat: čárka ve jménu odesílatele

Datum vývojového snapshotu: 2026-11-12 09:33 CET

## Příčina

U konkrétní uložené nedůležité zprávy dekódované jméno obsahuje čárku.
getaddresses z něj udělá dvě položky, přestože skutečná mailbox adresa je
jediná. Uložení pravidla se atomicky odmítne; přehled ji neskryje. Globální
notice se při této chybě nachází nad aktuálním mobilním výřezem. Soukromý
obsah a hlavičky se do Git-safe reportu nekopírují.

## Oprava

Úzká obnova pouze jedné koncové adresy v <...>, pokud prefix představuje
zobrazované jméno s čárkou a neobsahuje další adresu, závorkové mailboxy nebo
skupinovou/nejasnou syntaxi. Primární platné parsování se nemění. Kanonická
adresa a identity pravidel zůstávají stejné, existující data se nemigrují.
Stejný helper používá i preference důležitosti; její regresní test zajišťuje
zachování položek/kurzorů a shodu korektně uvozeného budoucího jména.

U volby Příště nezobrazovat má každá akce vlastní textový role=status řádek.
Chyba serveru i sítě se zobrazí u tlačítka i v dosavadním notice; tlačítko se
odemkne. Úspěšné uložení nadále obnoví přehled a skryje odpovídající řádky.

## Ověření

Nové domain a Node regrese před opravou selhaly na stejných dvou příčinách.
Po opravě121 cílených testů PASS včetně HTTP kontraktu. Pokryté: odmítnutí
skutečných více adres i skupiny a injekce další hlavičky, zachování všech
položek a kurzorů, skrytí jen správné nedůležité zprávy, zrušení a obnovení,
stávající důležitá karta, dvojklik, síťová/serverová chyba přímo u akce a
textový bezpečný výstup i s řetězcem <script>.

Čtecí náhled jediné odpovídající uložené karty: správná kanonická adresa,
hidden_low_importance=True při čistě paměťovém návrhu pravidla, business
stav před/po shodný; saved_any_rule=False. Důkaz mimo Git v
data/private/email_visibility_sender_20261112/readonly_source_check.json.
Plný lokální běh3524 testů (31 SKIP) našel jedinou neaktualizovanou
referenci velikosti/otisku stránky email_agent. Očekávaný kontrakt byl
aktualizovaný na38496 znaků /562 řádků /SHA-256
cf1a32144c99d77c0859bbd6689b6a45e075cce4cab7f1fd727280791b991712.
Poté celý frontend modul spolu s e-mailovými regresemi121 PASS. Ostatní
nezměněné moduly v plném běhu neměly chybu; znovu je ověří povinná plná
publikační brána před pushem. Log původního běhu
logs/email_visibility_sender_full_gate_20261112.log se nepřepisuje.

## Publikace a hranice

Míla výslovně zadal vývoj a rovnou p+n. Request `email-visibility-sender-20261112-v1`,
job `f3f981a426a7ec06eae6efb6e879bdc4`, project-email-cases→Cockpit. Po commitu jedno
submit_release(wait=True), výsledek se ověří z původní účtenky a soukromého
release_receipt.json ve jmenované složce. Tento předávací snapshot sám
netvrdí dokončený push ani nasazení.

Žádné nové e-mailové posouzení, IMAP/SMTP operace, skutečné uložení pravidla
nebo systémový upgrade hodinové kopie7f47a41f. Pro tento bug běží UI i filtr
přehledu v Cockpitu. Již nasazený provozní fix startu App Serveru zachovaný.
Fyzický klik na iPhonu po vydání zůstává oddělený. Samostatný e-mailový TVBCP
není dohodnutý, nový nevzniká; UI změna zapsaná do existujícího proudu Cockpit.
