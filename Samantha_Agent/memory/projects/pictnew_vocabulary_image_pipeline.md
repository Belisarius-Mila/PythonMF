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

## Povinný aktualizační kontrakt od 2026-07-31

Toto pravidlo se spouští při každém přidání nebo úpravě slovíček v některé z
oblastí `FR - Míla`, `FR - Jana` nebo `IT - Míla`. Nestačí zkontrolovat jen
slovník, který se právě měnil.

Povinně auditovat všechny aktuální zdroje:

- `FR - Míla`: `VocabularyFR/VocabularyFR.csv` a současnou kořenovou/iPhone
  sadu `VocabularyFR.csv`, dokud nebudou datově sjednocené,
- `FR - Jana`: připojený iCloud zdroj
  `PythonMF/VocabularyFR/VocabularyFR.csv`,
- `IT - Míla`: `VocabularyIT/VocabularyIT.csv`.

Pro všechny tyto zdroje existuje jediný společný obsah mapování:

- kanonický zdroj v repozitáři je `Pict/mapping.json`,
- Janina distribuční kopie je `iCloud/PythonMF/Pict/mapping.json`,
- obě kopie musí být po každé změně bajtově shodné,
- jiný aktivní `mapping.json` vedle aplikace, v upload balíčku nebo v pracovním
  adresáři není dovolený,
- aplikace na iPhonech čtou mapování pouze z vlastního `Pict/mapping.json`.

Každá příští aktualizace slovíček musí v jednom souvislém kroku:

1. Projít všechny čtyři výše uvedené CSV.
2. Porovnat jejich české významy s kanonickým `Pict/mapping.json`.
3. Ověřit skutečné obrázky v Mílově i Janině adresáři `Pict`.
4. Nejprve znovu použít vhodný existující obrázek; chybějící obrázek připravit
   nebo generovat jen podle potvrzovacího workflow.
5. Před změnou mappingu vytvořit zálohu a ukázat preview.
6. Po potvrzení upravit pouze kanonický mapping, zachovat jen české klíče a
   abecední řazení.
7. Stejný výsledný mapping a potřebné obrázky dorovnat do Janina `Pict`.
8. Ověřit celý řetězec `CSV -> mapping -> skutečný obrázek` pro všechny čtyři
   CSV a porovnat kontrolní součty obou distribučních mappingů.
9. Na závěr přesně vypsat, které soubory se mají nahrát na iPhony; mapping patří
   pouze do `Pict`.

Úkol nelze označit za hotový, dokud audit neprokáže všechny tři oblasti
`FR - Míla`, `FR - Jana`, `IT - Míla`. Pokud nové slovíčko už správné mapování
a obrázek má, má se i tento nulový výsledek výslovně uvést.

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

## Aktualni stav 2026-05-20

- Pro `VocabularyIT/IT_Pict.csv` je pripraven `PictNew/NewPicturesRequest20052026.json` s 125 unikatnimi cilovymi obrazky v 13 davkach po 10.
- `image_generator.py` generuje bezpecne po davkach do `PictNew/generated/YYYYMMDD_it_batchNNN/`, defaultne dry-run, skutecne API volani jen s `--execute` a potvrzenim `Potvrzuji generovani obrazku`.
- Batch 001 byl po uprave promptu znovu vygenerovan a Mila ho vizualne pochvalil jako povedeny.
- Batch 002 je technicky hotovy: 10/10 `generated`, vystup `PictNew/generated/20260520_it_batch002/`, nejvetsi soubor cca 185.2 kB, vznikly `generation_report.json` a `review.html`.
- Batch 003 je technicky hotovy: 10/10 `generated`, vystup `PictNew/generated/20260520_it_batch003/`, nejvetsi soubor cca 240.1 kB, vznikly `generation_report.json` a `review.html`.
- Batch 004 je technicky hotovy: 10/10 `generated`, vystup `PictNew/generated/20260520_it_batch004/`, nejvetsi soubor cca 210.0 kB, vznikly `generation_report.json` a `review.html`.
- Dalsi prakticky krok je vizualne zkontrolovat `PictNew/generated/20260520_it_batch002/review.html`, `PictNew/generated/20260520_it_batch003/review.html` a `PictNew/generated/20260520_it_batch004/review.html`.
- Batch 005 ani presun obrazku do `Pict/` nespoustet bez dalsiho Milova potvrzeni.

Dne 2026-05-20 vznikl také přípravný skript bez generování:

```text
pict_new_prepare.py
```

Aktuální použití pro italský pracovní CSV:

```bash
python3 pict_new_prepare.py --language it --date 2026-05-20 --batch-size 10 --batch-index 1
```

Výstupy:

```text
PictNew/NewPicturesRequest20052026.json
PictNew/NewPicturesReview20052026_batch001.html
```

Stav po přípravě:

- `IT_Pict.csv` má 128 řádků, kde `PD` obsahuje `add`.
- Ty odpovídají 125 unikátním cílovým obrázkům, protože některé řádky sdílí stejné `ENP`.
- Přípravný skript dávkuje podle unikátních cílových obrázků, ne slepě podle řádků CSV.
- Skript zatím nic negeneruje, nemění `Pict/`, nemění `mapping.json` a nemění CSV.

Dne 2026-05-20 vznikl také první bezpečný generovací skript:

```text
image_generator.py
image_generator_config.json
```

Výchozí nastavení:

- `model`: `gpt-image-2`
- `size`: `1024x1024`
- `quality`: `low`
- `output_format`: `webp`
- `target_size_kb`: `250`
- `max_size_kb`: `300`
- `output_root`: `PictNew/generated`

Bezpečnostní chování:

- Bez `--execute` skript jen vypíše plán a nedělá API volání.
- Skutečné generování vyžaduje potvrzení:

```text
Potvrzuji generovani obrazku
```

- Skript čte `OPENAI_API_KEY` jen z prostředí.
- Skript ukládá nové obrázky jen do `PictNew/generated/...`, ne do `Pict/`.
- Po dávce vytváří `generation_report.json` a `review.html`.

Dry-run pro první dávku prošel:

```bash
python3 image_generator.py --request-json PictNew/NewPicturesRequest20052026.json --batch-index 1
```

Naplánováno bylo 10 obrázků do:

```text
PictNew/generated/20260520_it_batch001/
```

Po potvrzeni 2026-05-20 byl batch 001 skutecne vygenerovan:

- 10/10 obrazku vzniklo.
- Vsechny obrazky jsou `webp`.
- Nejvetsi soubor mel cca `74.6 kB`, tedy hluboko pod limitem `300 kB`.
- Vystupy jsou v:

```text
PictNew/generated/20260520_it_batch001/
```

- Kontrolni soubory:

```text
PictNew/generated/20260520_it_batch001/generation_report.json
PictNew/generated/20260520_it_batch001/review.html
```

Pred dalsi davkou ma Mila vizualne zkontrolovat `review.html`.

Po vizualni kontrole batch 001 Mila rozhodl, ze styl je moc detsky/sterilni a obrazek
`a.webp` je spatne, protoze vysel jako jablko misto metafory neurciteho clenu.
Stary batch 001 byl smazan a prompt byl upraven:

- vice sceny, pozadi, detailu a stinu,
- mene baby styl,
- stridat postavy a nepouzivat porad stejneho kluka/holku,
- ceske napisy jsou povolene, pokud pomahaji pochopeni obrazku,
- zakazat nahodne texty, cizi slova, dekorativni pismena a nesmyslne popisky,
- pro `a` explicitne zakazat pismeno A i jablko a pouzit metaforu jedne neurcite veci.

`PictNew/NewPicturesRequest20052026.json` byl znovu vytvoren s novym promptem a batch
001 je pripraveny k opakovane generaci.

Po Milove potvrzeni byl batch 001 znovu vygenerovan s novym promptem:

- 10/10 obrazku vzniklo.
- Vystupy jsou ve `PictNew/generated/20260520_it_batch001/`.
- Vsechny vystupy jsou `webp`.
- Nejvetsi soubor je `go.webp` cca `237 kB`, tedy pod limitem `300 kB`.
- Vznikly nove kontrolni soubory:

```text
PictNew/generated/20260520_it_batch001/generation_report.json
PictNew/generated/20260520_it_batch001/review.html
```

Pred dalsim batchem nebo presunem do `Pict/` ma Mila vizualne zkontrolovat
`review.html`.

### Stav po dogenerovani batchu 012 a 013

Po Milove potvrzeni 2026-05-20 byly dogenerovany posledni batche requestu
`PictNew/NewPicturesRequest20052026.json`:

- Batch 012: 10/10 obrazku, vsechny status `generated`, nejvetsi soubor cca `230.2 kB`.
- Batch 013: 5/5 obrazku, vsechny status `generated`, nejvetsi soubor cca `246.6 kB`.
- Batch 013 byl posledni batch, protoze request ma celkem 125 unikatnich obrazku.
- Vystupy jsou v:

```text
PictNew/generated/20260520_it_batch012/
PictNew/generated/20260520_it_batch013/
```

- Kontrolni soubory:

```text
PictNew/generated/20260520_it_batch012/generation_report.json
PictNew/generated/20260520_it_batch012/review.html
PictNew/generated/20260520_it_batch013/generation_report.json
PictNew/generated/20260520_it_batch013/review.html
```

Obrazky nebyly presunuty do `Pict/` a nebyl upraven `Pict/mapping.json`.
Pred presunem je dalsi krok vizualne zkontrolovat batch review soubory.

Po Milove potvrzeni, ze vsechny obrazky jsou skvele, byly vygenerovane `.webp`
soubory z batchu 001 az 013 zkopirovany do `Pict/`.

- Kontrola potvrdila 125/125 cilovych souboru v `Pict/`.
- Zdrojove soubory v `PictNew/generated/` zustaly zachovane.
- `Pict/mapping.json` zatim nebyl upraven.
- Dalsi krok je aktualizovat `Pict/mapping.json` jen po samostatnem potvrzeni a pred zmenou vytvorit zalohu.

Výsledek testu:

- `VocabularyFR`: 11 nových řádků k doplnění do `FR_Pict.csv`, 112 shod/návrhů k posouzení, 0 bez návrhu
- `VocabularyIT`: 0 nových řádků k doplnění do `IT_Pict.csv`, 85 shod/návrhů k posouzení, 143 bez návrhu

Tento stav byl ještě podle starší logiky s `_Pict.csv`.

Nová architektura má být upravena tak, aby `_Pict.csv` nebyly povinné.

## Aktualni kanonicky stav 2026-05-23

VocabularyIT vlna z 2026-05-20 je uzavrena.

Hotove:

- Batche 001 az 013 byly vygenerovane do `PictNew/generated/20260520_it_batch001/`
  az `PictNew/generated/20260520_it_batch013/`.
- Mila obrazky vizualne schvalil a 125/125 cilovych `.webp` souboru bylo
  zkopirovano do `Pict/`.
- `Pict/mapping.json` byl po samostatnem potvrzenem preview aktualizovan.
- Po aplikaci mappingu audit hlasil:
  - `added_rows=0`,
  - `mapping_without_image=0`,
  - `unresolved=0`.
- Git checkpoint existuje:
  - `851b347 Apply VocabularyIT picture mapping updates`.

Aktualni dalsi krok:

- Nepokracovat ve starych batchich 001 az 013; tato vlna je hotova.
- Pri dalsich obrazcich nejdrive udelat novy read-only audit podle
  `technical/vocabulary_image_generation_workflow.md`.
- Placené image API volat jen po vyslovnem potvrzeni rozsahu.
- `Pict/mapping.json` upravovat jen po samostatnem preview, zaloze a potvrzeni.
- Nepouzivat `git add .`.

## Historicke handoffy

Tyto handoffy ponechat jako auditni historii prubehu, ale nepouzivat je jako
aktivni startovni stav projektu. Aktualni stav je tento projektovy soubor,
kanonicky workflow `technical/vocabulary_image_generation_workflow.md` a finalni
handoff `handoffs/vocabularyit_mapping_applied_2026_05_20.md`.

- `handoffs/dnesni_checkpoint_lekarna_pictnew_git_2026_05_20.md` - michany denni
  checkpoint Lekarna, media resize, PictNew a git; prekryto pozdejsimi projektovymi
  handoffy.
- `handoffs/vocabularyit_pict_csv_audit_2026_05_20.md` - prvni audit
  `IT_Pict.csv`, priprava requestu a generovani batchu 001 az 004.
- `handoffs/vocabularyit_batches_005_011_generated_2026_05_20.md` - technicky
  hotove batche 005 az 011 pred vizualni kontrolou a kopii do `Pict/`.
- `handoffs/vocabularyit_batches_012_013_generated_2026_05_20.md` - posledni
  batche 012 a 013 a kopie vsech 125 obrazku do `Pict/`; prekryto mapping
  handoffem.
- `handoffs/pictnew_next_image_generation_phase_2026_05_20.md` - snapshot pred
  aplikaci mappingu; cast o neaktualizovanem `Pict/mapping.json` je prekryta
  commitnutym stavem `851b347`.

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
