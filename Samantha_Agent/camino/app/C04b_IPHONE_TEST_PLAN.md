# C04b — cílený test na iPhonu

Stav 2026-09-20 12:12 CEST: `cz.pythonmf.camino.app` 0.1.0 (1) je podepsaná,
nainstalovaná a spuštěná na iPhonu 14 Plus. Fyzický průchod čeká na pozorování
obrazovek, médií a zvuku.
Syntetické testy a simulátor nenahrazují níže uvedený fyzický průchod. Použij
novou zkušební cestu a neosobní záběry; do chatu stačí ID testu a PASS/FAIL,
bez fotografií, hlasu a soukromých textů. Zkouška nevyžaduje letový režim.

## Před startem

1. Podepsat a nainstalovat nové Camino s vlastním bundle ID. Neodinstalovat
   prototypy ani nemaž jejich data.
2. Spustit Camino, založit **Zkoušku**. Potvrdit, že hlavní obrazovka nabízí
   Foto/Video/Komentář a že Mac synchronizace se netváří jako hotová.
3. Povolit kameru a mikrofon až při prvním použití příslušné funkce.

## Průchod

| Test | Úkon a pozorování pro PASS |
|---|---|
| T007 | Vyfotit neosobní předmět. Hláška o uložení se objeví až po záznamu a snímek zůstane v detailu i po opětovném spuštění. Chybu zápisu ověřuje syntetická část; na telefonu ji nevynucuj zaplněním úložiště. |
| T008 | Rychle udělat dva snímky. V detailu prvního nahrát komentář a přidat další foto. Zůstanou dva samostatné Momenty; první má obě fotografie a komentář, druhý jen svůj snímek. Po restartu se vazby nemění. |
| T009 | Při odmítnuté kameře otevřít Foto: zobrazí se vysvětlení a Zpět; Komentář a místní deník fungují dál. Změnu oprávnění proveď až po prvních snímcích. |
| T011 | Natočit krátký klip se zvukem, dát Stop, přejít domů a aplikaci znovu otevřít. Klip je jednou v detailu, přehrává obraz i skutečný zvuk a uvádí správnou délku. |
| T012 | Jeden krátký klip na výšku a jeden na šířku; po restartu se oba přehrávají bez chybného otočení. |
| T013 | Vědomě zapnout **Natočit bez zvuku**, pořídit klip a ověřit trvalý štítek. Při odepřeném mikrofonu se běžné video samo nepřepne na tiché. |
| T014 | U krátkého rozběhnutého videa odejít z aplikace nebo zamknout telefon. Po návratu zkontrolovat, zda je použitelný klip dokončen, nebo pravdivě označen jako částečný; nesmí se tvářit, že pokračuje v záznamu. |
| T060 | Zkontrolovat běžné hlášky o místě a přerušení. Vynucené zaplnění úložiště a tepelný stres nejsou součástí této bezpečné zkoušky; tato část zůstává neověřená. |

T010 (textové revize) patří k C04d. Automatické přenesení skutečného videa na Mac
a úplné T049 patří až k produkčnímu propojení C05a. Po testu zapiš výsledky
jednotlivých ID, model/iOS, datum, zjištěná selhání a zda šlo o fyzický iPhone.

## Průběžný fyzický výsledek 2026-09-21

- T007, úspěšný zápis a restart: Míla potvrdil hlášku o uložení a fotografii
  v detailu po úplném zavření a opětovném otevření aplikace. Na Macu byl po
  znovuotevření pozorován nový proces aplikace. Chyba dokončení zápisu nebyla
  na zařízení vyvolána; celý T007 zůstává částečně ověřený.
- T008, fyzický PASS podle Mílova pozorování na iPhonu 14 Plus: dvě rychlé
  fotografie vytvořily dva samostatné Momenty. U prvního zůstal komentář a
  výslovně přidaná druhá fotografie; druhý má jen svou fotografii. Míla
  potvrdil správné vazby také po úplném zavření a opětovném otevření aplikace.
- T009, fyzický PASS podle Mílova potvrzení: při odepřené kameře otevření
  `Foto` zobrazilo vysvětlení a `Zpět`; `Komentář` i místní deník dál
  fungovaly.
- T011, fyzický PASS podle Mílova pozorování: krátké video se po opětovném
  otevření přehrává s obrazem a zvukem a bez duplicit. Délka je vidět až v
  ovládání přehrávače během přehrávání, ne trvale v detailu; jde o poznámku
  k UI, nikoli o blokátor požadovaného správného času klipu.
- T012, fyzický PASS podle Mílova potvrzení: krátké klipy na výšku i na šířku
  se po úplném zavření a opětovném otevření přehrávají se správnou orientací
  a bez chybného ořezu.
- T013, fyzický PASS podle Mílova potvrzení: vědomě zvolené video bez zvuku má
  viditelný štítek před Start, během záznamu i v detailu po restartu. Při
  odepřeném mikrofonu se běžné video samo nepřepnulo na tiché; výslovně tichý
  klip zůstal dostupný jen po vědomé volbě.
- T014, fyzický PASS podle Mílova potvrzení: zámek telefonu, odchod z aplikace
  i přijatý krátký hovor ukončily rozběhnuté video bez samovolného pokračování.
  Zachované klipy byly přehratelné a pravdivě označené jako částečné; hovor se
  do videa nezaznamenal.
