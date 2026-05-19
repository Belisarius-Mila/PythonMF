# PictNew: opakovatelné generování obrázků pro slovíčka

## Stav

Míla řeší opakované doplňování obrázků pro slovníkové aplikace:

- `VocabularyFR/VocabularyFR.csv`
- `VocabularyIT/VocabularyIT.csv`
- společný adresář `Pict/`
- společný soubor `Pict/mapping.json`
- pracovní výstupy v `PictNew/`

Původně existují pomocné soubory:

- `VocabularyFR/FR_Pict.csv`
- `VocabularyIT/IT_Pict.csv`

Bylo ale rozhodnuto, že pro budoucí automatizovanou proceduru budou pravděpodobně zbytečné jako zdroj pravdy.

## Cíl

Cílem je vytvořit opakovatelný systém, který po doplnění nových slovíček:

1. zkontroluje, zda už pro ně existuje vhodný obrázek,
2. vygeneruje rozhodovací protokol,
3. po potvrzení připraví nové položky do `mapping.json`,
4. vygeneruje nové obrázky přes image generator,
5. uloží protokol o vytvořených obrázcích.

Systém má zabránit tomu, aby se při každém novém doplnění slovíček celý proces znovu ručně vymýšlel.

## Důležité poznatky

Zdroj pravdy má být pouze:

- `VocabularyFR.csv`
- `VocabularyIT.csv`
- `Pict/mapping.json`
- skutečný obsah adresáře `Pict/`

Soubory `FR_Pict.csv` a `IT_Pict.csv` nemají být pro novou architekturu povinné. Mohou zůstat kvůli starší práci nebo ruční kontrole, ale nová procedura na nich nemá záviset.

FR a IT se mají řešit společně, protože:

- `mapping.json` je společný,
- `Pict/` je společný,
- český význam může být stejný pro FR i IT,
- společný audit snižuje duplicity obrázků.

Tlačítko `PictNew` může být ve francouzské i italské aplikaci, ale má volat stejný sdílený kód.

## Rozhodnutí

### Procedura 1: audit

První procedura má být čistě kontrolní. Nemá měnit `mapping.json`, obrázky ani slovníky.

Po stisku tlačítka `PictNew` má projít:

- `VocabularyFR/VocabularyFR.csv`
- `VocabularyIT/VocabularyIT.csv`
- `Pict/mapping.json`
- adresář `Pict/`

Má zjistit:

- přímé shody v `mapping.json`,
- shody v `mapping.json`, u kterých chybí obrázek,
- pravděpodobné shody podle českého významu,
- pravděpodobné shody podle existujícího anglického názvu obrázku,
- slovíčka bez použitelného obrázku,
- možné duplicity českých významů nebo obrázků.

Výstup má být textový protokol například:

```text
PictNew/NewVocabularyDDMMYYYY.txt
```

Například pro 11. 5. 2026:

```text
PictNew/NewVocabulary11052026.txt
```

Po vytvoření protokolu má aplikace zobrazit hlášku:

```text
Vygenerován protokol o shodě: NewVocabulary11052026.
Prosím o posouzení.
```

Tlačítko `OK` zavře okno.

Tlačítko `AddPictures` později spustí druhou proceduru.

Při dalším stisku `PictNew` se audit spustí znovu a denní protokol se může přepsat aktuálním stavem.

### Doporučená struktura auditního protokolu

Protokol má být rozhodovací, ne jen dlouhý technický výpis.

Doporučené sekce:

```text
Souhrn
------
VocabularyFR rows: ...
VocabularyIT rows: ...
mapping.json entries: ...
Pict images: ...

1. Shody k ručnímu posouzení
----------------------------

2. Mapping existuje, ale obrázek chybí
--------------------------------------

3. Nové položky bez návrhu
--------------------------

4. Pravděpodobné duplicity
--------------------------

5. Kandidáti pro nové obrázky
-----------------------------
```

Protokol by měl ideálně seskupovat položky podle českého významu nebo podle navrženého obrázku, ne slepě po řádcích.

### Procedura 2: AddPictures

Druhá procedura už bude akční. Spouštět se má až po auditu a po posouzení shod.

Má udělat:

1. Najít slovíčka bez obrázků.
2. Navrhnout anglický název obrázku.
3. Vytvořit request JSON, například:

```text
PictNew/NewPicturesRequestDDMMYYYY.json
```

4. Doplnit nové položky do `Pict/mapping.json`.
5. Ideálně řadit `mapping.json` abecedně podle českého klíče.
6. Vygenerovat obrázky.
7. Uložit nové obrázky nejprve do `PictNew/`.
8. Zmenšit nebo optimalizovat obrázky na cílovou velikost cca 250 kB, maximum 300 kB.
9. Vygenerovat protokol:

```text
PictNew/NewPicturesDDMMYYYY.txt
```

10. Zobrazit hlášku:

```text
Obrázky vytvořeny, čti protokol: NewPicturesDDMMYYYY.
```

Nové obrázky se mají nejdřív kontrolovat v `PictNew/`, teprve potom přesunout do `Pict/`.

### Image generator

Image generator nemá být natvrdo zabudovaný do `vocab_trainer_fr.py` ani `vocab_trainer_it.py`.

Doporučená struktura:

```text
PythonMF/
  pict_new_audit.py
  pict_new_prepare.py
  image_generator.py
  image_generator_config.json
  Pict/
  PictNew/
  VocabularyFR/
  VocabularyIT/
```

Role souborů:

- `pict_new_audit.py`: audit slovníků proti `mapping.json` a `Pict/`
- `pict_new_prepare.py`: příprava request JSONu a návrhů pro `mapping.json`
- `image_generator.py`: dávkové generování obrázků
- `image_generator_config.json`: bezpečná konfigurace bez API klíče

### API klíč

OpenAI API klíč nesmí být uložený v repozitáři.

Nesmí být v Python souboru:

```python
OPENAI_API_KEY = "REDACTED_API_KEY"
```

Nesmí být ani v JSON konfiguraci.

Správně má být pouze v proměnné prostředí:

```bash
export OPENAI_API_KEY="..."
```

Skript ho má číst takto:

```python
import os

api_key = os.environ.get("OPENAI_API_KEY")
```

Pokud klíč není nastavený, skript má skončit s jasnou hláškou a nic negenerovat.

### Konfigurace image generatoru

Příklad bezpečné konfigurace bez klíče:

```json
{
  "backend": "openai",
  "output_dir": "PictNew",
  "max_size_kb": 300,
  "target_size_kb": 250,
  "batch_size": 5,
  "style_prompt": "Clean child-friendly vocabulary-card illustration, isolated main subject, white or transparent background, no text, no letters, no watermark.",
  "image_size": "1024x1024"
}
```

Doporučená dávka na začátek je 5 obrázků. Až se stabilizuje styl, lze zvýšit na 10.

### OpenAI image modely

Pro implementaci má Codex před prací ověřit aktuální oficiální OpenAI dokumentaci k image generation.

V chatu bylo řešeno, že pro tento systém dávají smysl nové GPT Image modely a OpenAI Images API.

Codex nesmí spoléhat na zastaralé názvy modelů bez ověření v oficiálních docs.

## Existující práce

Už existuje první verze skriptu:

```text
pict_new_audit.py
```

Byl spuštěn test:

```bash
python3 pict_new_audit.py --language all --date 2026-05-11
```

Vznikl protokol:

```text
PictNew/NewVocabulary11052026.txt
```

Výsledek testu:

- `VocabularyFR`: 11 nových řádků k doplnění do `FR_Pict.csv`, 112 shod/návrhů k posouzení, 0 bez návrhu
- `VocabularyIT`: 0 nových řádků k doplnění do `IT_Pict.csv`, 85 shod/návrhů k posouzení, 143 bez návrhu

Tento stav byl ještě podle starší logiky s `_Pict.csv`.

Nová architektura má být upravena tak, aby `_Pict.csv` nebyly povinné.

## Otevřené otázky

- Přesně doladit strukturu protokolu `NewVocabularyDDMMYYYY.txt`.
- Rozhodnout, zda `mapping.json` doplňovat automaticky hned, nebo až po ručním potvrzení.
- Rozhodnout, zda se obrázky po kontrole přesouvají ručně z `PictNew/` do `Pict/`, nebo na to vznikne další potvrzovací procedura.
- Ověřit aktuální OpenAI image generation API a doporučený model.
- Rozhodnout, zda `pict_new_prepare.py` bude používat AI pro návrhy anglických názvů, nebo nejdřív čistě pravidlový postup.
- Vyjasnit přesné názvy souborů a datumový formát, pravděpodobně `DDMMYYYY`.

## Další kroky pro Codex

1. Nejprve nic neměnit bez výslovného zadání.
2. Před prací přečíst:
   - tento memory soubor,
   - `pict_new_audit.py`,
   - `Pict/mapping.json`,
   - strukturu `VocabularyFR/`,
   - strukturu `VocabularyIT/`,
   - obsah `PictNew/`.
3. Upravit `pict_new_audit.py` tak, aby nová logika nevyžadovala `FR_Pict.csv` ani `IT_Pict.csv`.
4. Zachovat jeden sdílený kód pro FR i IT.
5. Tlačítka ve `vocab_trainer_fr.py` a `vocab_trainer_it.py` mají později jen volat sdílenou proceduru.
6. Nepřidávat API klíče do žádného souboru.
7. Obrázky nejdříve ukládat do `PictNew/`, ne rovnou do `Pict/`.
8. Před změnou `mapping.json` vždy vytvořit zálohu.
9. Při git operacích nepoužívat slepě `git add .`.

## Zdroj

Souhrn ChatGPT konverzace k budoucí funkcionalitě `PictNew`, automatickému auditu slovníků, sdílenému obrazovému mappingu pro FR/IT, image generatoru přes OpenAI API a opakovatelnému workflow pro generování obrázků k novým slovíčkům.
