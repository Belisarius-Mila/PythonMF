# Pracovní text, hlasové pokusy a import komentáře — 24. 10. 2026

## Rozsah a hranice

Míla při praktické zkoušce požádal o ruční úpravy textu před čtením,
zachování původního textu z iPhonu a jednoduché mazání pokusů. Změna doplňuje
práci s komentářem přímo u fotografie a import již připraveného MP3/WAV.

Jde o nový místní vývoj. Předchozí balíček 5cd323ef byl prokazatelně pushnutý
a nasazený registrovanou Lunou 4f7f51ee421b4fd20b71e09b454c509f: plná brána
2206, smoke 5/5; živý čtecí audit při tomto vývoji potvrzuje stejný Cockpit.
Starší neúspěšná účtenka 570b4fc7 je historie. Tento nový krok není nasazený.
Osobní střih, zdrojové texty a skutečné nahrávky se během vývoje neupravovaly.

## Postup u fotografie

1. Otevři **Text a komentář** a převezmi text deníku. V poli **Text pro čtení
   a zobrazení — zde můžeš ručně upravovat** vznikne pracovní kopie.
2. **Původní načtený text z iPhonu** je zvlášť, pouze pro čtení. Pracovní
   kopii uprav libovolně do 6000 znaků; průběžně se ukládá do filmové revize.
   Před zavřením počkej na potvrzené uložení; otevřený neodeslaný koncept
   není trvalou zálohou po násilném zavření karty.
3. **Upravit text pro čtení** zaměří pracovní pole. **Uložit pracovní text**
   umožní uložit hned. **Obnovit pracovní text z originálu** vrátí výchozí
   znění po běžném potvrzení; vytvořené hlasové pokusy se tím neztrácejí.
4. Vytvoř místní čtení nebo vyber soubor a zvol **Importovat MP3/WAV
   k fotografii**. Vytvoření/import uloží pokus pro poslech, nikoli automaticky
   do zvuku filmu. Potom jej výslovně použij a podle potřeby prodluž fotografii.
5. Sekce **Uložené pokusy a nahrávky** uchovává předchozí verze se skutečnou
   délkou a vlastním přehrávačem. **Upravit text tohoto pokusu** vrátí přesný
   pracovní text dané nahrávky k dalším ručním úpravám. **Použít tento pokus
   ve filmu** vybere jeho uložené znění a zvuk; rozdílný pracovní text vyžaduje
   běžné potvrzení. Původní text z odpovídající revize deníku zůstane zachovaný.
6. **Smazat pokus do koše** funguje jedním kliknutím. Je-li vybraný u fotografie,
   nejprve se uloží jeho odpojení; pracovní text ani originál se nemažou.
   V **Koši pokusů** je **Obnovit pokus**. Koš je obnovitelný a neuvolňuje místo
   na disku. Nejde o trvalý výmaz souborů a starší hotové filmy zůstávají platné.

Po další editaci pracovní verze se předchozí nahrávka odpojí od nového textu,
ale zůstane mezi uloženými pokusy. Předchozí uložené filmové revize i exporty
se nepřepisují. Tím lze opakovat úpravu, čtení, poslech a odstranění pokusu.

## Implementační kontrakt

- Volitelné `photo_text.original_text` nese původní načtený text. Server jej
  porovnává s přesnou přijatou textovou revizí a odmítne jeho přepsání.
  `photo_text.text` je pracovní verze. Deník na iPhonu a archivní revize
  zůstávají neměnné. Starším filmovým revizím se originál doplní pouze do
  čtecí projekce; uložené JSON soubory se nemigrují ani nepřepisují.
- Každý úspěšný hlasový pokus má vlastní neměnný text, původ, SHA-256 zvuku
  a změřenou délku. U starších účtenek se text rozřeší z jejich uložené
  filmové revize bez přepsání účtenky. Přehled odděluje pracovní text od historie.
- Automatické načítání nesmí přepsat ručně editovaný ani právě uložený text.
  Úprava a potvrzené uložení zneplatní starší odpovědi. Regrese pokrývá i
  načítání zahájené během probíhajícího uložení.
- Koš je atomický, vratný příznak v soukromém adresáři pokusu. Nové připojení
  pokusu v koši server odmítne. Poslechový GET/HEAD/Range po smazání nevrací
  audio. Historický export stále ověřuje původní soubory a oprávnění a může
  používat stejnou zachovanou odvozeninu; bin nesmí poškodit hotový film.
- Import přijímá MP3/WAV do 64 MiB a nejvýše 300 s. Vstup se dekóduje
  vynuceným MP3/WAV dekodérem, nikoli autodetekcí playlistu nebo cizích cest.
  Vznikne metadata-free AAC kopie, ověří se délka i úplné dekódování. Původní
  import se zachová soukromě. Import není nový archivní Asset ani změna
  neměnného Mac manifestu. Stejný požadavek nesmí přepsat jiný obsah.
- Import i generování dohledají FFmpeg/FFprobe pod omezeným PATH bez změny
  prostředí Cockpitu. Node test dál používá projektový helper a vynucuje PATH
  služby. Existující soukromí, zdrojové vazby a ochrana originálů zůstávají.
- Přehled obsahuje nejvýše 256 uchovaných pokusů projektu včetně koše;
  trvalá správa úložiště je samostatná operace. Přerušené importy/generace
  bez ověřené účtenky se nenabízejí jako hotové nahrávky. Není automatický retry.

## Ověření

- 45 cílených kontrol PASS: 23 testů komentářů, 20 frontendových kontraktů
  a 2 kontroly registru POST rout.
- Rozšířený DOM scénář ověřuje originál pouze pro čtení, ruční editaci,
  uložení a reload, více pokusů, návrat jejich textu, koš/obnovení, odpojení
  použitého pokusu, import MP3 a zachování původního textu v celém cyklu.
- Skutečný import WAV i MP3 pod PATH služby PASS, soukromé AAC má celou
  délku. HTTP upload, limity a původ požadavku, koš/obnovení PASS.
- Ochrana před přepsáním originálu, soukromí, cizí fotografií, zastaralou
  revizí, symlinkem a playlistem PASS. Starší účtenka i hotový film po
  smazání pokusu zůstaly beze změny.
- Dodatečně nalezený souběh autosave/načítání: nový DOM scénář nejprve FAIL,
  po opravě PASS. Pokrývá starou odpověď před psaním i během ukládání;
  pracovní text ani potvrzená revize se nesmějí vrátit zpět. Oba DOM skripty PASS.
- Plná společná brána 2216 testů PASS (458,188 s unit část), závěrečná statická brána PASS.
- Skutečný proklik této nové verze na Safari/iPhonu NEOVĚŘENO. Inventura
  dostupných ploch nevrátila žádný připojený prohlížeč.

## Další krok

Samostatné p+n Lunou a potom praktické přijetí u fotografie. Výběr
přirozenějšího hlasu zůstává samostatnou poslechovou zkouškou; v tomto kroku
se žádný osobní text neposílal externímu generátoru, žádné placené čtení
neproběhlo. Místní čtení stále používá Zuzanu. Import umožní dodat kvalitnější
hotovou MP3 nebo vlastní nahrávku. Nový cloudový hlas tím není vybraný ani zapojený.
