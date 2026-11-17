# Vocabulary FR — současný klient a historický prototyp

## 2026-11-17 15:52 CET — Předání registrace prvního Datova FR testu

Hotovo: Will připravil přesný registrační patch pro již existující Datův
syntetický test_vocabularyfr_content.py.27 jeho testů prošlo přímo z Datovy
větve; patch mění pouze validation_domains.py a cockpit_quality_gate.py,
git apply --check i strukturální výběr domény vocabulary_fr_content PASS.
Rozhodnutí: Míla požádal odblokovat Datův checkpoint. Data převezme Willův
konkrétní patch, pak ověří a checkpointuje svůj hotový obecný kód spolu
s registrací. Vlastnictví centrálního návrhu zůstává Willovi; jeho pracovní
kopie nebyla změněná. Na main se registrace přenese až s testem v uzavřeném
Datově commitu. Soukromý obsah není předmětem této registrace ani commitu.
Další krok: Data aplikuje předání Vocabulary_FR_Data_registrace_testu_predani_2026-11-17.txt
z Downloads, spustí vlastní registrovanou bránu a předá přesný checkpoint.
Navrhované další kroky: Potom Willova integrace a zvláštní přejímka soukromého
obsahového balíčku. Skutečných464 karet tímto testem nebylo potvrzeno.
Technický důkaz: uzavřený patch Vocabulary_FR_Data_registrace_testu_2026-11-17.patch
má SHA256446d70dd1ec7c647f0d3f28dffeb99c84775c308f4d74ac2a5ef86fbfc2cd4ad.
Podklad31c670bb,27 syntetických testů PASS/0,706s. Soukromá účtenka
shared_chat_transfer_fix_20261117/data_registration_receipt.json. Žádný
reset/rebase, další checkout, push, nasazení ani zveřejnění Janina obsahu.

## 2026-11-17 14:55 CET — FR klient pro Janu podle kontraktu v1.1

Hotovo: Samostatný klient Vocabulary FR podle IT31c670bb: galerie18 témat,
slova/věty FR/CZ, vlastní A–D/PIN/zálohy, obrazová hra, psaní s500ms nápovědou,
smyčka Slovíčka / Věta + slovíčko a až5 kontextových obrázků. Testovací obsah
je čistě syntetický; nejde o ověření skutečných464 karet ani hotovou aplikaci
s Janiným obsahem. Český a francouzský zvuk jsou dostupné nezávisle. Chybějící
FR zvuk se přizná, smyčka zůstane pozastavená na stejné kartě, hra takový
hlasový cíl nepoužije. Bez TTS fallbacku nebo automatické výroby.
Rozhodnutí: Míla potvrdil paralelní dělení Data/Will a kontrakt v1.1.
Data vlastní katalog/exporty/média/obsahové testy; Will klient, registry,
společné zápisy a integraci. Skutečný soukromý balíček mimo docs i Git,
nezměněný živý CSV, budoucí publikace a placená výroba samostatně.
Další krok: Převzít uzavřený Datův soukromý balíček s manifestem a SHA spolu
s jeho hotovými obecnými kódovými commity. Teprve při jejich integraci zapojit
existující obsahové testy a ověřit464 skutečných karet mimo publikační strom.
Navrhované další kroky: Mílova/Janina obsahová, akustická a telefonní přejímka
nad skutečným balíčkem; volba FR hlasu a případná výroba až po nové dohodě.
Technický důkaz:24 skutečných JS scénářů a81 cílených Python kontrol PASS.
Nativní Safari nad soukromými syntetickými fixtures ověřilo galerii, odhalení,
kontexty chat/lune, vysvětlení chybějícího FR audia, Stop a návrat/fokus karty.
Vlastní okno i localhost server zavřené, původní okno zachované. Žádná akustická
ani telefonní přejímka. Finální programovou bránu, zmrazené otisky a commit
určuje private vocabulary_fr_client_20261117/completion.json.
Registrace github_pages/vocabulary-fr/ a vlastní validační domény je pouze
místní; desktopový launcher i starý FR prototyp zachované. Běžící Cockpit
se nerestartoval a stále nenačetl tuto změnu registrace/validační mapy.
Před případným budoucím p+n načíst nové registry autorizovaným postupem;
současné zadání není oprávněním k restartu, push ani nasazení. Azure adaptér
beze změny. Nový TVBCP/proud nevzniká, používá se existující FR dvojice.

Starší webový MVP níže je historický samostatný prototyp; tento port jej nemění.

# VocabularyFR Web Trainer pro Janu

Zalozeno: 2026-06-04
Priorita: 2
Stav: webovy MVP prototyp funguje lokalne

## Cil

Preklopit francouzskou slovnikovou aplikaci `VocabularyFR/vocab_trainer_fr.py`
do formy, kterou Jana muze pouzivat bez instalovaneho Pythonu, idealne na Macu
a pozdeji i na iPhonu.

Zakladni datovy zdroj zustava:

```text
VocabularyFR/VocabularyFR.csv
```

CSV schema:

```text
FR,CZ,Order,Sentence,SentenceT,L,HT,gender_fr
```

## Aktualni webovy prototyp

Staticka webova aplikace je v:

```text
VocabularyFR/web/
```

Hlavni soubory:

```text
VocabularyFR/web/index.html
VocabularyFR/web/styles.css
VocabularyFR/web/app.js
VocabularyFR/web/audio/
VocabularyFR/web/pict/
```

Lokalni testovaci server:

```text
cd /Users/miloslavfalta/Desktop/PythonMF/VocabularyFR/web
python3 -m http.server 8788 --bind 127.0.0.1
```

URL:

```text
http://127.0.0.1:8788
```

## Hotove funkce

- Nacteni `VocabularyFR.csv`.
- Editace, pridani, vlozeni a smazani radku.
- Export aktualizovaneho CSV.
- Primy zapis do vybraneho CSV v prohlizecich s File System Access API
  (prakticky Chrome/Edge); Safari ma fallback export.
- Vyhledavani, razeni a filtry `vse`, `neumim`, `HT`, `nauceno`,
  `s vetou`.
- Treninkova karta FR/CZ s preklapenim.
- Lokalni audio cache pro FR slova a cast vet.
- Obrazky podle logiky puvodni desktopove aplikace: presny stem,
  `Pict/mapping.json`, fallback `man/woman`, `verb`, `preposition`,
  `proverbs`, `others`.
- Auto smycka: Start/Stop, nahodne/postupne, interval 2-30 s,
  cteni slovo nebo slovo + veta.

## Audio

Puvodni prohlizecovy Web Speech hlas byl prakticky nepouzitelny.
Lepsi smer je lokalni audio cache generovana na Milove Macu:

```text
VocabularyFR/generate_web_audio.py
```

Generator pouziva macOS:

```text
say -v Thomas
afconvert
```

Aktualni stav 2026-06-04:

- `web/audio/fr_words/`: 193 souboru, pokryva vsechna aktualni FR slovicka
  v CSV; nizsi pocet nez 206 radku je kvuli duplicitnim FR slovum.
- `web/audio/fr_sentences/`: 127 souboru.
- Web nejdriv hleda `.m4a`; kdyz chybi, spadne na nouzovy prohlizecovy hlas.

Pri novem slovu nebo nove vete audio automaticky nevznikne ve statickem webu.
Je nutne bud obcas spustit generator u Mily, nebo zvolit robustnejsi architekturu
s lokalnim/helper serverem.

## Obrazky

Priprava webovych obrazku:

```text
VocabularyFR/prepare_web_pict_assets.py
```

Generator bere:

```text
Pict/mapping.json
Pict/
VocabularyFR/MaleFox.PNG
VocabularyFR/FemaleFox.PNG
VocabularyFR/VocabularyFR.csv
```

A vytvori:

```text
VocabularyFR/web/pict/manifest.json
VocabularyFR/web/pict/images/
```

Aktualni stav 2026-06-04:

- `web/pict/images/`: 174 souboru.
- `missing_stems`: 0.
- `VocabularyFR/web/` ma celkem cca 39 MB.

Pro Janin Mac je prakticky nutne dodat celou slozku `VocabularyFR/web/`,
protoze obsahuje aplikaci, audio i obrazky.

## Otevrene architektonicke varianty

### Varianta A: staticky web + servis u Mily

Jana pouziva web a CSV. Pri novych slovech/vetach se obcas vezme aktualni CSV
a u Mily se spusti:

```text
python3 VocabularyFR/generate_web_audio.py
python3 VocabularyFR/prepare_web_pict_assets.py
```

Vyhoda: jednoduche.
Nevyhoda: pro denni praci v zahranici je servisni cyklus otravny.

### Varianta B: mala macOS aplikace bez Pythonu

Webove UI zustane, ale pribude lokalni helper nebo zabalena `.app`, ktera umi
volat macOS `say`/`afconvert` a generovat audio primo na Janine Macu.

Vyhoda: Jana muze denne pridavat slova a audio vznikne hned lokalne.
Nevyhoda: slozitejsi prvni build/deploy.

### Varianta C: Samantha server pres Tailscale

Jana by otevrela web pres zabezpeceny pristup k Milovu Macu/serveru.
Server by ukladal CSV, generoval audio a spravoval assets.

Vyhoda: vse se generuje automaticky.
Nevyhoda: Miluv Mac/server musi byt dostupny a musi se resit bezpecny pristup.

### Varianta D: iPhone / Pythonista 3

Pro iPhone je nejrealistictejsi Pythonista verze nad stejnym CSV.
Pythonista umi pracovat se svou iCloud slozkou `Pythonista 3`, ale je nutny
prakticky test s Janou:

1. Vytvorit v Pythonista iCloud maly `samantha_test.txt`.
2. Overit, ze je videt ve Files na iPhonu.
3. Overit, ze je videt na Janine Macu.
4. Pripadne slozku/soubor nasdilet Milovi.

Riziko: jeden CSV editovany z Mac webu i iPhonu muze mit iCloud konflikty.
Pred servisnim zasahem musi byt zaloha CSV.

## Dalsi doporuceny krok

1. Rucne otestovat prototyp na Milove Macu: CSV load, obrazky, audio, auto smycka,
   editace a export.
2. Rozhodnout, zda primarni cil je Janin Mac nebo iPhone.
3. Pokud Janin Mac: navrhnout malou `.app`/helper variantu pro lokalni generovani
   audia bez Pythonu.
4. Pokud iPhone: vikendovy test Pythonista iCloud slozky a konfliktniho chovani
   CSV.

## Bezpecnost

- Skutecne Janino aktualni CSV pred servisem zalohovat.
- Nepouzivat iCloud/Git jako soucasne editovane uloziste bez konfliktni kontroly.
- Pri commitech davat pozor, ze vedle VocabularyFR existuji nesouvisejici
  rozpracovane zmeny v Samantha memory (`Family Memory Films`).
