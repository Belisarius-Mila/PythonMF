# Interiérový architekt — zachování dat a návrh migrace

Stav 25. 11. 2026: **návrh, migrace neprovedena**. Rozhodnutí: jeden projekt,
dvě rozpracované místnosti a zachování veškeré dostupné dosavadní práce.

## Identita a názvy

- Jeden proud Human–Adam: Interiérový architekt, ID `project-neuberk-kacenka`.
- Cílová hierarchie: projekt → místnosti → podklady, model, drafty a varianty.
- Starší Kačenka a místnost současného Ateliéru patří do tohoto jednoho
  projektu. Aktuální data Ateliéru používají název Koupelna dolní; případné
  přejmenování této místnosti čeká na upřesnění, neblokuje dokumentaci.
- ID proudu, cesty k handoffu/TVBCP ani původní soukromé cesty se nyní nemění.
  Staré názvy jsou aliasy, nevzniká duplicitní proud nebo druhá aplikace.

## Co zachovat

- Původní soubory, fotografie, plánky, náčrty, starší obrazové koncepty a
  dostupné původní indexy Kačenky.
- Originály i odvozené soubory současného Ateliéru, všechny záznamy variant,
  rodičovské vazby, kresby, názvy, poznámky a rozpracovaná zadání s revizemi.
- Historii rozhovorů a původních požadavků, jejich identity a stavy, přijaté
  výsledky a dostupné údaje o původu. Žádný nový modelový tah při převodu.
- Evidenci dřívějšího smazání a její význam. Import ani obnova nesmějí vrátit
  záměrně odstraněný obrázek nebo vykreslit prázdný záznam jako platný obraz.

Požadavek zachovat návrhy platí pro to, co je skutečně dostupné. Neznámé
nebo již odstraněné soubory se nevymýšlejí ani automaticky neregenerují.

## Pořadí budoucího převodu

1. **Inventura a mapa vazeb.** Soukromý manifest s cestami, velikostmi,
   otisky, stávajícími ID a vazbou zdroj → cílová místnost. Rozlišit soubory,
   obrazové varianty, textové/historické záznamy a neznámé vazby.
2. **Kontrakt verze 2.** Definovat skutečné verzované schéma projektu,
   místnosti, varianty, masek a scény. Ilustrační SCENE_MODEL.json není schéma.
   Historický obraz bez ověřených měr nedostane domyšlenou přesnou geometrii.
3. **Suchý převod na oddělené kopii.** Zachovat původní identitu nebo
   jednoznačnou původovou mapu, historii a kontrolní otisky. Opakované spuštění
   stejného převodu nesmí násobit místnosti ani varianty. Neúplný převod se
   nesmí vydávat za dokončený a nesmí přepsat zdrojová data.
4. **Ověření úplnosti a návratu.** Porovnat všechny položky a vazby před/po,
   otevřít zachované obrazy, texty a historii obou místností. Ověřit zotavení
   z přerušení, chybějící soubor, konflikt revize i zachování markerů smazání.
5. **Kontrolované přepnutí.** Až po vyhodnoceném suchém převodu, přejímce
   a odpovídajícím oprávnění. Původní úložiště ponechat zachované a dostupné
   pro návrat. Bez automatického smazání staré aplikace nebo rodinných dat.

## Přejímací kritéria

- Obě místnosti a všechny dostupné historické návrhy jsou dohledatelné
  v novém UI; počet databázových záznamů se nevydává za počet obrázků.
- Neměnné originály i původní metadata mají stejné otisky; nové odvozeniny
  mají vlastní identitu a nemění význam historického výsledku.
- Převod nesmí odesílat soukromé podklady poskytovateli, instalovat modely,
  zakládat nové AI požadavky ani měnit rozpočty a role.
- Spuštění a ověření proběhne nejprve na testovací kopii, nikoli na živých datech.
- Nové UI a geometrický model se přejímají samostatně; zachovaná historie není
  důkazem implementace masek, správné geometrie nebo dokončení verze 2.0.
