# Camino — návrh kompaktního panelu textu a hlasu

Datum: 2026-10-28. Pracovní proud: project-camino.
Stav: návrh publikovaný přes Lunu do 643c93ec; bez implementace nového UI.

## Podnět a cíl

Míla prakticky potvrdil, že zpracování textu a převod na hlas ve střižně
fungují skvěle. Rozhraní ale obsahuje příliš mnoho textu a dlouhých ovladačů
pod sebou. Požaduje užší výběrová pole, případně dvě vedle sebe, a přehlednější
uspořádání. Nejprve zadal pouze analýzu a návrh, následně jeho uložení commitem.

Cíl prvního kroku: zpřehlednit pouze panel Text a komentář fotografie.
Hlavní pracovní cesta je text → hlas → poslech → použití ve filmu.

## Zjištění ze současného kódu

- Obecné pravidlo pro select nastavuje šířku 100 %. Výběry zdrojového textu,
  použití textu a původní nahrávky se skládají do dlouhého svislého panelu.
- Základní práce s textem a Orusem sdílí prostor s obnovou originálu,
  původními nahrávkami, importem, správou pokusů a opakovanou nápovědou.
- Cena a souhlas jsou oddělené od tlačítka pro vytvoření hlasu dalšími
  ovladači. Míla již narazil na neaktivní tlačítko, jehož podmínka nebyla
  na první pohled zřejmá.
- U každého uloženého pokusu se opakují přehrávač a dlouhá sada tlačítek.

Podklady: app/frontend/cockpit/film_editor.js, styles.css a page.html.
Jde o rozbor zdrojového rozložení a Mílův popis; nebylo provedeno nové
nezávislé vizuální měření ani proklik návrhu v prohlížeči.

## Navržené uspořádání

1. Dva kompaktní výběry v jednom řádku: Text z deníku a Použití textu.
   Na úzké ploše se složí pod sebe. Dlouhé názvy musí zůstat zjistitelné,
   i když uzavřené výběrové pole zabere méně místa.
2. Hlavní upravitelný text zachovat přes celou šířku panelu. Pod ním jen
   stručný stav uložení a počet znaků. Originál otevřít na vyžádání přes
   Zobrazit originál; ruční převzetí vybraného textu zůstane výslovná akce.
3. Jeden souvislý blok vytvoření řeči: Orus, tempo −10 %, cena, souhlas
   s odesláním konkrétního textu Googlu a hlavní tlačítko bez mezilehlých
   nesouvisejících polí. Důvod blokace musí být přímo u tlačítka viditelný
   i bez možnosti na něj kliknout.
4. Po vytvoření nabídnout přehrávač a Použít ve filmu. Pokud nahrávka
   přesahuje fotografii, ukázat rovnou odpovídající volbu prodloužení;
   potřebná nápravná akce nesmí zmizet pouze do skryté nápovědy.
5. Uložené nahrávky, Import MP3/WAV a Další možnosti sbalit do samostatných
   rozbalovacích částí. Do dalších možností patří méně častá obnova textu
   a práce s původními nahrávkami. Historie a koš musí zůstat snadno dohledatelné.
6. Kratší popisky a tlačítka, delší vysvětlení pod Nápověda. Základní stav
   uložení či vytváření řeči uvádět stručně; zásadní chyby ponechat viditelné
   v kontextu operace i při posunu panelu.

## Orientační náčrt

```text
Text z deníku [výběr ▾]   Použití [výběr ▾]
[Převzít text]

┌──────────────────────────────────────┐
│ Upravitelný text komentáře            │
└──────────────────────────────────────┘
Uloženo · počet znaků        Zobrazit originál

Orus · tempo −10 %           Cena: …
☐ Souhlasím s odesláním textu Googlu
  za uvedenou cenu.
[Vytvořit čtení]

▶ Poslech                   [Použít ve filmu]

▸ Uložené nahrávky
▸ Import MP3/WAV
▸ Další možnosti
```

## Funkční hranice pro případnou realizaci

- Zachovat celý text, oddělení originálu a pracovní kopie, automatické
  ukládání, historii, obnovitelný koš a import MP3/WAV.
- Zachovat přesný Orus a přijaté tempo 0,90. Nevytvářet jiný hlas ani
  nepřepínat poskytovatele kvůli změně rozložení.
- Cena a souhlas zůstávají viditelné před odesláním. Souhlas je pro konkrétní
  text a pokus; editace jej ruší. Změna rozložení nesmí sama spustit generování.
- Převzetí textu nepřepisuje rozepsanou práci samotnou změnou výběru.
  Zařazení řeči do filmu zůstává samostatná vědomá akce.
- Zachovat pozici, rozepsaný text a ochranu před opožděným načtením.
  Sbalení doplňkových částí nesmí skrýt probíhající operaci nebo její chybu.

## Ověření při budoucím vývoji

- Skutečný DOM scénář: výběr zdroje, převzetí, editace, uložení, souhlas,
  vytvoření, poslech, prodloužení fotografie a použití ve filmu.
- Souhlas se editací zruší a důvod neaktivního tlačítka je čitelný bez hoveru.
- Dva výběry vedle sebe při dostatečné šířce, jeden sloupec na úzké ploše;
  žádný vodorovný posuv, ovládání klávesnicí a čitelné dlouhé názvy.
- Uložené pokusy, koš, import a původní text zůstanou dostupné po rozbalení.
- Regrese opožděného pollu, zachování rozepsaného textu a pozice.
- Nakonec fyzická přejímka Mílou v Safari; samotný automatický test ji nenahrazuje.

## Rozsah návrhového commitu

Pouze tento návrh a související projektové záznamy. Uživatelské potvrzení
funkce textu a hlasu platí pro popsanou vyzkoušenou práci; nepotvrzuje
automaticky všechny scénáře koše, importu a celé filmové časové osy.
Kód, skutečné projekty a média se nemění. Implementace návrhu, případná
delegace a vydání jeho realizace potřebují navazující zadání.

## 2026-10-28 09:41 CET — Publikace návrhu

Míla výslovně zadal „Luna cc = p+n“. Jediný registrovaný submit_release s wait=True vydal oba čekající dokumentační commity. Účtenka 4b73bdbe1a6d9377f6e084dd26f20eb6: completed, head 643c93ecc88365e1d8016b06df362a11a2ac5d1d, push/deployment confirmed, project-camino → Cockpit, plná brána 2256 testů / 513,5 s, smoke 5/5, protected_services_unchanged=true.

Jedna Adamova kontrola: živý GitHub přesně na vydaném headu, rozsah oproti dcb89967 pouze memory. Živé HTML HTTP 200 přesně shodné se zdrojem a SHA-256 768f4c4f47414927c3a1974f63b30b0d0199bba8daacb31224bc26cded16ce0a, health HTTP 200, code_stamp 296a14675318a23b. Publikovaný je návrh, nové rozložení zatím není v aplikaci.

return_channel=caller převzal Adam zde v terminálu; automatické returned_to_adam=false není důvodem retry. Následný výsledkový zápis je místní pro příští balíček. Další krok zůstává realizace až na navazující zadání, pak fyzická přejímka přehlednosti.
