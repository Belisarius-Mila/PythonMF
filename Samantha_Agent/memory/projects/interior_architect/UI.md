# Návrh pracovního rozhraní

25. 11. 2026 · návrh obrazovek pro Mac a iPhone · [datový kontrakt](BACKEND.md)

## 1. Otevřít místnost

V Janičce zůstane cesta **Rodinné projekty**. Tlačítko ponese jméno **Otevřít Interiérového architekta**. Na stávající adrese `/interior/` se otevře jeden projekt. První obrazovka má dvě místnosti. Každá ukáže poslední uloženou práci a tlačítko **Pokračovat**. Po návratu z místnosti se zachová výběr. Žádný druhý výběr projektu.

| Místnost | První otevření po převodu | Co je odtud dostupné |
|---|---|---|
| Kačenka | Skupiny „Interiérové koncepty“ (21) a „Studie prázdné místnosti“ (5). Otevřená skupina zachová pořadí a hodnocení z původního indexu. | Fotografie, pracovní překresy, půdorysy a textové míry. Ze starého konceptu lze založit novou větev. |
| Koupelna dolní | Poslední uložený draft podle dostupné evidence. Je-li návratová volba neplatná nebo chybí věrohodné pořadí draftů, otevřít historii a nabídnout výběr. | 7 podkladů, 27 položek historie (4 s obrázkem), 15 uložených draftů. Textová práce zůstává přístupná i po odstranění média. |

Čísla jsou snímek z auditu. Budoucí UI je vždy spočítá ze skutečně otevřené místnosti.

## 2. Pracovat nad fotografií

Rozvržení pro Mac po výběru pracovního pohledu:

```text
Místnosti  ›  Kačenka        [Změnit místnost]        Uloženo · revize 4
[Podklady]   [Fotografie]   [Půdorys]   [3D]   [Historie]

Pohledy místnosti      Pracovní fotografie                 Vrstvy a omezení
  fotografie           [−] [Přizpůsobit] [+]               Oko  Vrstva        Režim
  náčrt                                                     ☑   Okno          Zámek pixelů
  půdorys              plátno fotografie                    ☑   Omítka        Úprava
                       s obrysem zvolené oblasti            [+ Nová oblast]
[Změnit podklad]       Obdélník · Polygon · Štětec · Guma   [Zpět] [Znovu]

[Porovnat]             Stav fotografie a geometrie         [Uložit variantu]
```

Ukázkové vrstvy a revize ilustrují ovládání. Kurzor i dotyk se převádí z polohy na plátně do souřadnic plného obrazu. Přiblížení ani otočení telefonu nemění uložené body. Výběr podkladu, zámky, rozpracovaná změna a uložená varianta jsou stále rozlišitelné. Kreslení do originálu založí draft s odkazem na původní pohled.

1. **Podklady.** Zvolit konkrétní fotografii jako pracovní pohled. Plánek, reference i staré návrhy lze připnout vedle ní. Chybí-li obraz, zobrazí se dostupný text a volba jiného podkladu.
2. **Ochrana a úprava.** Označit např. okno režimem „Zámek pixelů“ a omítku režimem „Upravit“. V inspektoru se nastaví název, režim a viditelnost vrstvy. Další režimy jsou „Zámek geometrie“, „Volný návrh“ a „Pouze kontext“. Barvu doplní popisek a šrafování. V překryvu se ukáže vítězná ochrana a proč. Skrytí vrstvy v náhledu její ochranu nevypne.
3. **Vyzkoušet a porovnat.** V prvním milníku se nabídne „Vyzkoušet místní úpravu“. Posuvník Před/Po, přepnutí Originál/Výsledek a mapa rozdílů sdílejí zoom a polohu. Report ukáže počet změněných chráněných pixelů, zvlášť výsledek geometrie a jeho důvod. Odmítnutý kandidát ponechá rozpracovanou masku k další úpravě.
4. **Uložit.** Uložit pojmenovanou variantu na vybrané větvi a vrátit se do historie. Stav u názvu rozliší „Uloženo“, „Rozepsáno v tomto zařízení“ a „Konflikt revize“. Při konfliktu lze vedle sebe otevřít serverovou a místní verzi a uložit místní práci jako kopii. Uzavření stránky nesmí tiše ztratit tahy nebo text.

## 3. Půdorys, materiály a 3D

**Půdorys** nabízí plátno se stěnami a otvory, přidání objektu, kóty a číselný inspektor. Kliknutí na kótu otevře hodnotu, jednotku, původ a stav potvrzení. U neznámé hodnoty se zobrazí „Doplnit míru“. Odhad se vykreslí odlišně a uživatel uvidí podklad před potvrzením. Nástroj **Dispozice** umožní posun a otočení vybavení a ukáže konkrétní kolizi. Zamčené okno nebo dveře nelze tažením přemístit.

**3D** používá stejné verze stěn, otvorů a objektů. Změna kamery nebo materiálu je samostatná operace. U neúplné geometrie se zobrazí chybějící údaj pro požadovaný pohled. **Analýza** navrhne měření nebo oblast ke kontrole přímo u příslušného podkladu. **Materiály** se otevírají u vybraného povrchu. V prvním řezu se v menu nabízejí jen již přístupné režimy. Nové karty se přidají s funkčním milníkem.

## 4. Historie a návrhy od architekta

Historie je seznam větví s rodičem, titulkem, rozpracovanou revizí, původem a dostupností média. Lze filtrovat „Vše“, „S obrázkem“ a „Rozpracované“. U doloženého odstranění je uvedeno „Obrázek odstraněn“, u neznámého důvodu pouze „Bez připojeného obrázku“. U původních konceptů zůstane viditelný původní posudek. Porovnání dvou obrázků má posuvník jen při shodném pohledu. U různých pohledů zvolit dvě samostatná okna a zobrazit jejich původ.

**Konzultace** je spojena s konkrétní místností a větví. Uživatel vidí otázku, odpověď a schválené zadání. Budoucí **Vytvořit vizualizaci** nejprve ukáže přesné podklady, podporu masky, očekávanou cenu nebo limit a schopnosti adaptéru. Volby, které adaptér nesplní, vysvětlí před startem. Při nejistém výsledku je k dispozici „Ověřit původní požadavek“. Při provozu bez připojení k poskytovateli zůstávají místní nástroje dostupné přes Cockpit. Při výpadku spojení s Cockpitem UI ponechá místní rozepsanou práci a obnoví ji po návratu spojení.

## iPhone a lidská přejímka

Na telefonu jsou místnosti pod sebou. Ve fotografii patří plocha obrázku a spodní lišta aktivnímu nástroji. Tlačítko „Vrstvy“ otevře spodní panel, po výběru se vrátí celé plátno. Jeden prst kreslí ve vybraném nástroji, dva posunují a přibližují. Zpět a Porovnat zůstanou dostupné u plátna. Porovnání lze ovládat i tlačítky Před/Po. Na Macu mají stejné akce klávesnicové ovládání a popsané ovládací prvky.

První přejímka na obou zařízeních projde stejný úkol: vybrat fotografii, zamknout oblast, přiblížit, opravit tah, uložit draft, znovu otevřít, vytvořit místní variantu a přečíst oba výsledky kontroly. Druhá přejímka po zkušebním importu ověří dohledání konkrétního konceptu Kačenky a návrat k rozepsané variantě Koupelny. Tento dokument je návrh obrazovek. Fyzické ovládání bude možné převzít až na implementovaném řezu.

[Otevřít klikací návrh obrazovek](UI_PREVIEW.html). Přepínání místností, obrysy ochrany, posuvník porovnání a filtry historie běží místně. Obsah ukázky je schematický.
