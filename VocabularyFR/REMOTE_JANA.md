# VocabularyFR pro Janin samostatný účet

Tento postup připraví desktopovou VocabularyFR na Mílově Macu tak, aby se Jana
přihlašovala vzdálenou plochou do vlastního macOS účtu. Program a obrázky jsou
společné a pouze ke čtení; Janiny tři pracovní CSV soubory jsou oddělené v jejím
uživatelském účtu.

Instalátor je záměrně dvoukrokový a create-only. Nikdy nepřepisuje existující
instalaci. První příkaz pouze zkontroluje účet, Python, zdrojový CSV soubor,
úplnost `Sentence`/`SentenceT`, obrázky a cílové cesty. Ve výstupu nezobrazuje
Janino uživatelské jméno ani soukromé cesty.

## 1. Náhled bez zápisu

V Terminálu z kořene PythonMF spusť:

```bash
python3 VocabularyFR/install_jana_remote.py \
  --jana-user JANINO_KRATKE_JMENO \
  --source-csv "SEM_PRETAHNI_JANIN_AKTUALNI_VocabularyFR.csv"
```

Úspěšný náhled vrátí JSON se stavem `preview` a hodnotou
`plan_fingerprint`. Pokud vrátí `failed`, nic se nevytvořilo. Nejčastější
příčinou je nedownloadovaný iCloudový soubor, chybějící příkladová věta nebo už
existující cílová instalace. Pole `picture_mapping_missing_images` je redigované
varování o starším mapování a samo o sobě instalaci neblokuje.

## 2. Potvrzená instalace

Stejný příkaz spusť přes `sudo`, přidej `--apply`, přesnou potvrzovací větu a
fingerprint z bezprostředně předcházejícího náhledu:

```bash
sudo python3 VocabularyFR/install_jana_remote.py \
  --jana-user JANINO_KRATKE_JMENO \
  --source-csv "SEM_PRETAHNI_JANIN_AKTUALNI_VocabularyFR.csv" \
  --apply \
  --confirmation INSTALL_VOCABULARYFR_FOR_JANA \
  --expected-fingerprint FINGERPRINT_Z_NAHLEDU
```

Instalace vytvoří:

- společný program v `/Users/Shared/VocabularyFR/app`,
- společné obrázky a `mapping.json` v `/Users/Shared/VocabularyFR/Pict`,
- Janina pracovní CSV v `~/Library/Application Support/VocabularyFR`,
- Janin spouštěč `VocabularyFR.command` na její ploše.

Janin aktuální slovník se bere pouze ze zadaného iCloudového CSV. `VerbeFR.csv`
a `FR_Pict.csv` se při první instalaci založí z aktuálních projektových verzí a
potom jsou už Janinými samostatnými pracovními soubory.

## 3. První živé ověření

1. Jana se přes Sdílení obrazovky přihlásí do svého účtu.
2. Na své ploše otevře `VocabularyFR.command`.
3. Ověří načtení slovíček, obrázek, francouzskou výslovnost a jedno uložení
   příznaku `L` nebo `HT`.
4. Zvuk je nutné ověřit v reálné vzdálené relaci; instalátor přenos zvuku
   netestuje.

Spuštění bez `--data-dir` a `--pict-dir` zůstává kompatibilní s dosavadním
Mílovým lokálním používáním aplikace.
