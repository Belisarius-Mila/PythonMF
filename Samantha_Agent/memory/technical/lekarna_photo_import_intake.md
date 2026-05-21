# Lekarna photo import intake

Datum zalozeni: 2026-05-21

## Cil

Zkratit dalsi import novych fotek do domaci lekarny tak, aby Codex nemusel znovu
promyslet cely postup. Tento soubor popisuje, co ma Mila dodat a co ma Codex
udelat pred zapisujicimi kroky.

## Co ma Mila dodat

Idealni vstup pro kazdou novou fotku:

- fotku ulozit do `data/lekarna/photo_imports/`,
- rict, do ktere fyzicke krabice nebo dozy polozka patri:
  - `U léků - Míla (osobní léky)`,
  - `U léků - Jana (osobní léky)`,
  - `Horní koupelna - Pils Home Store / velká krabice`,
  - `Horní koupelna - dóza vitamíny/minerály/přírodní spánek`,
- rict, jestli jde o osobni lek na predpis, volne prodejny lek, doplnek stravy,
  zdravotnicky prostredek nebo nejistou polozku,
- pokud je to videt nebo znamo: presny nazev, sila, forma, pocet kusu, expirace,
  pro koho je lek urcen a zda se ma zobrazit ve webove aplikaci.

Minimalni vstup muze byt i kratky, napr.:

```text
V photo_imports jsou dve nove fotky.
Tetradin patri do Milovy krabicky.
Cinfamucol patri do velke krabice.
```

## Co ma Codex udelat

1. Precist `memory/MEMORY_INDEX.md`, relevantni Lekarna memory a tento intake.
2. Najit nove fotky v `data/lekarna/photo_imports/`.
3. Zkontrolovat, zda uz nejsou zkopirovane v `data/lekarna/Leky_v_Krabickach/`;
   pokud ne, pripravit je tam jako zdroj pro import.
4. Vizualne precist obal: nazev, ucinnou latku, silu, formu, mnozstvi a nejistoty.
5. U leku a vyssich rizik dohledat aktualni PIL/SPC/produktovy zdroj. Preferovat
   oficialni zdroje:
   - SÚKL/DLP pro ceske registrovane leky,
   - EMA pro centralizovane registrace,
   - zahranicni lekove agentury u zahranicnich pripravku,
   - oficialni web vyrobce/dodavatele u doplnku.
6. Vytvorit manifest v `data/lekarna/photo_imports/` pres `csv.DictWriter`, ne
   rucne skladanym CSV textem.
7. Do `PIL_Short` psat jen kratky prakticky vytah: k cemu obecne je, hlavni
   omezeni, hlavni interakce nebo situace pro lekare/lekarnika. Nepsat vlastni
   davkovani.
8. Spustit preview zmenseni obrazku na cil cca 100 kB.
9. Spustit validaci manifestu/planu importu.
10. Pockat na presna potvrzeni pro zapisujici kroky.
11. Po potvrzeni spustit zmenseni, apply importu, validace zdroju, testy a lokalni
    private-data export.
12. Verejny sifrovany webovy bundle pregenerovat jen pres skryty lokalni prompt
    s heslem, nikdy heslo nepsat do chatu.

## Potvrzovaci vety

Zmenseni obrazku:

```text
Potvrzuji zmenseni obrazku
```

Import fotek do evidence:

```text
Potvrzuji import fotek lekarna
```

## Bezpecnost

- `data/lekarna/` a `docs/lekarna/private-data/` jsou soukrome a nepatri do gitu.
- Pred zapisujicim importem musi vzniknout zaloha hlavniho CSV.
- Nejasne polozky maji zustat `nutno_overit=ano`, `expirace=nezjisteno` a mit
  jasne popsane nejistoty.
- Osobni leky na predpis se oznacuji jako pro konkretni osobu a pouze podle lekare.
