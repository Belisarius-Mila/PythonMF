# MMTX: příběhová hotspot aplikace pro Matýska

## Stav

Nový směr anglické hry pro Matýska byl oddělen od `anglictina_matysek_V3.py`.

Bylo rozhodnuto:

- V3 nechat beze změny,
- novou aplikaci stavět jako samostatný soubor:

```text
MatysekANJ/MMTX.py
```

## Cíl

Cílem `MMTX.py` je vytvořit příběhovou scénu, kde dítě nevybírá položky z menu, ale kliká na objekty přímo v obrázku.

Stejné objekty mohou mít různé chování podle režimu:

- v režimu barev houba řekne barvu,
- v režimu čísel houba dostane číslici a přehraje se číslo,
- později v příběhovém režimu může objekt spustit část příběhu nebo úkol.

## Důležité poznatky

Pygame na tento typ aplikace stačí.

Není potřeba nový framework.

Technický princip:

- jeden hlavní obrázek jako pozadí,
- nad ním seznam klikacích zón,
- každá zóna má ID, barvu, souřadnice a případná data,
- aktuální režim určuje, co kliknutí udělá.

Příklad hotspotu:

```python
{
    "id": "orange_mushroom_big",
    "rect": (760, 210, 170, 120),
    "color_word": "orange",
    "number_value": 3,
}
```

Později bylo rozhodnuto, že pro přesnější klikání v režimu čísel mají být místo hrubých obdélníků použity menší elipsy.

## Rozhodnutí

### Režim Barvy

V `MMTX.py` vznikl režim barev.

Používá obrázek:

```text
MatysekANJ/NumCol1.JPG
```

Klikací skupiny hub:

- Red
- Blue
- Green
- Orange

Po kliknutí:

- přehraje se anglické slovo,
- kliknutá oblast se zvýrazní,
- na chvíli se zobrazí anglický název barvy.

### Režim Čísla

Byl doplněn druhý režim `Cisla`.

Původní logika:

- každá konkrétní houba měla pevně přiřazené číslo.

To bylo změněno, protože Míla chtěl přirozenější chování:

- první kliknutá houba dané barvy dostane 1,
- další nová houba stejné barvy dostane 2,
- další dostane 3,
- pokud se klikne znovu na už očíslovanou houbu, zopakuje se její existující číslo.

Příklad:

- klik na libovolnou zelenou houbu jako první: zobrazí 1, přehraje `one`,
- klik na další zelenou houbu: zobrazí 2, přehraje `two`,
- klik na další: zobrazí 3.

Toto chování je důležité zachovat.

### Geometrie hotspotů

Geometrie byla opakovaně laděna.

Problém:

- obdélníkové nebo velké kruhové plochy byly nepřesné,
- číslice se kreslily na nevhodná místa,
- klikací zóny neodpovídaly kloboukům hub.

Úpravy:

- hotspot umí zvlášť klikací oblast a `label_center`,
- číslice se kreslí na vlastní kotevní body,
- v režimu čísel se používají menší elipsy,
- klikací oblasti jsou menší a přesnější.

Geometrie může stále vyžadovat ruční doladění podle reálného klikání v okně.

## Otevřené otázky

- Doladit hotspoty skoro po pixelu podle skutečného obrázku.
- Rozhodnout, jak odstranit nebo schovat horní přepínače a nahradit je příběhovým ovládáním.
- Přidat třetí režim typu úkol:
  - `Find blue`
  - `Find three`
- Přidat další příběhové scény nebo objekty.
- Rozhodnout, zda sova, pes, batoh nebo jiný objekt bude sloužit jako příběhový průvodce.
- Připravit další obrázky ve stejném stylu.

## Další kroky pro Codex

Před prací číst:

- `MatysekANJ/MMTX.py`
- `MatysekANJ/PROJECT_HANDOFF_MMTX.md`, pokud existuje
- `MatysekANJ/MMTX_STRUCTURE_PLAN.md`, pokud existuje
- tento memory soubor

Pravidla:

- Neplést si `MMTX.py` s `anglictina_matysek_V3.py`.
- V3 neupravovat, pokud Míla výslovně neřekne.
- Hlavní nová aplikace je `MMTX.py`.
- Udržet technickou jednoduchost.
- Preferovat jeden obraz, hotspoty a režimy před mnoha obrazovkami.
- Při úpravě čísel zachovat dynamickou logiku číslování podle pořadí kliknutí v rámci barvy.
- Při práci s hotspoty dávat pozor na přesnost a oddělit klikací oblast od pozice labelu.

Po změnách ověřit alespoň:

```bash
python3 -m py_compile MatysekANJ/MMTX.py
```

A headless pygame start, pokud je to možné.

## Zdroj

Souhrn ChatGPT/Codex konverzace k nové aplikaci `MMTX.py`, příběhové scéně s houbami, režimu barev, režimu čísel, hotspotům, geometrii klikacích oblastí a dynamickému číslování hub.

