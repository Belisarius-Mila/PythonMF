# MMTX — druhý obraz nové šestky: Ollie’s Dinner

Po sedmé replice prvního obrazu nabídne Next picture přechod ke schválenému
obrázku setkání s Olliem. Následuje deset přesných replik Picture 2 z nového
scénáře. Repeat opakuje současnou větu; Again po závěru vrátí začátek šestky.
Čítač ukazuje jednotlivý obraz (1–7, potom 1–10). Chyba MP3 blokuje postup do
další věty až do explicitního Repeat; pozdní callbacky nemění novější stav.

## Zachované první podklady

Všech sedm prvních MP3, `dialogue.json`, `audio_manifest.json` a
`arrival_side_view.webp` má shodné SHA-256 před a po rozšíření. Žádný z prvních
sedmi požadavků se neopakoval; stará privátní raw účtenka se nepřepisuje.

Přehrávač nově načítá katalog `pictures.json` a samostatný `dialogue_02.json`.
První textový paket a první audio manifest zůstávají neměnné. Druhý obraz má
vlastní pojmenované MP3 `audio/en/p02_*.mp3`, veřejný `audio_manifest_02.json`
a soukromou trvalou účtenku `audio_receipt_picture_02.json`.

## Obraz a anglický zvuk

- Přijatý PNG: 1671 × 941, SHA-256 `e934ef302bb2d65449665938779c2ef77b0a841065a83235bc37445afc9c678f`.
- Beze změny rozměrů exportovaný WebP q90: 503 084 B, SHA-256 `0004f9f6eed0ab7b0798c8006f21d1d27b95e257c08c129478d136c0b86404c8`.
- Deset skutečných unikátních Azure požadavků / 635 účtovaných SSML znaků,
  přijímací limit 700, tempo −10 %, 174 528 B hotových MP3.
- Ollie používá `en-US-AndrewNeural`, převzaté původní hlasové ID Ollieho
  z historického builderu. Ostatní postavy zachovávají hlasy prvního obrazu.
- Žádný fallback poskytovatele, žádné opakování nejisté odpovědi, tajemství
  jen v místní konfiguraci a registrovaném transportu.
- Builder `--check --picture 2` ověřuje texty, hlasy, tempo, deset otisků,
  dekódování a mirrory; `--check` nadále samostatně ověřuje první obraz.

## Rozložení a ověření

U druhého obrazu je dialog nahoře nad postavami; ryba a podběrák zůstávají
viditelné. Na úzkém displeji je řeč pod obrázkem, aby nezakrývala postavy.
První obraz ponechává své dosavadní rozložení.

- 57 cílených testů PASS: přesné texty a hlasové vazby obou obrazů, přechod
  7/7 → Ollie 1/10, všech 17 vět, chyby/Repeat na obou obrazech, restart,
  Back/Forward a ochrana původních souborů i raw účtenky při druhém generování.
- Dekódování 7/7 a 10/10; oba mirrory shodné. Lokální HTTP 200 a přesné bajty
  všech 27 skutečných veřejných souborů (pomocné `.lock` nejsou publikované).
- Skutečné Safari zobrazilo druhý obraz, Bunny 10/10, Again a dokončení;
  screenshot ověřil čitelnost a viditelnost postav, ryby i podběráku.
- Fyzická iPhone přejímka a Mílovo výslovné hodnocení hlasu Ollieho zůstávají otevřené.
- Plná místní brána druhého obrazu: 2972 testů OK (5 SKIP), 665,420 s unit.

## Rozsah vydání

Míla zadal nejdříve vydat již hotový první obraz a vyčistit repo, poté připojit
obraz 2. První předání má vlastní přesný head `fee535e5` a Terra účtenku
`4b261f77c13a77e845684bbbd90cc876`: plná brána 3412 PASS, push confirmed,
Pages run `42839271179`: build-pages success, deploy-pages failure / desetiminutový timeout při syncing_files a zrušení deploymentu. Účtenka attention, deployment uncertain.
Tento druhý obraz vzniká odděleně v Datově worktree; není v prvním vydání.
Další p+n pro druhý obraz není tímto záznamem provedené ani automaticky spuštěné.

Willovy tři nesouvisející WIP změny zůstávají v ověřeném stashi
`550024e17da59eb258556f5d3f0979650d5a4d30` a soukromé záloze. Zdrojový main je
čistý. Starší Datův WIP úklid původní šestky se zachovává mimo tento nový commit.

Další krok: dokončit místní bránu a checkpoint druhého obrazu; převzít konečnou
účtenku prvního p+n a ověřit jeho skutečné veřejné soubory. Druhý obraz pak
čeká na samostatnou přejímku a případný pokyn k p+n.


### 2026-11-10 16:12 CET — Druhý obraz ověřený, první nasazení Pages zrušené po timeoutu

Hotovo:
- Lokálně funguje příběhové spojení prvních dvou obrazů a všech 17 anglických MP3. Druhý obraz má schválený obrázek, přesných 10 replik a vlastní neměnné audio podklady.

Rozhodnutí:
- Druhý obraz je oddělený následující vývoj, není součástí prvního zmrazeného p+n. První p+n se neopakuje automaticky; Míla má konkrétní otázku na jediný nový pokus stejného fee535e5. Starý WIP Data je zaznamenaný samostatně v `06c34051` a do main se znovu nepřebírá. Willovo nesouvisející WIP zůstává zachované.

Další krok:
- Uložit konkrétní nový commit druhého obrazu a potvrdit čisté pracovní kopie; poté počkat na Mílovo rozhodnutí o novém pokusu nasazení.

Navrhované další kroky:
- Druhý obraz samostatně projít na Mílově zařízení a případně vydat po jeho pokynu. Produkční Pages po zrušeném nasazení zatím není přejímka nové šestky.

Technický důkaz:
- Plná místní brána 2972 OK (5 SKIP), 665,420 s unit; 57 cílených kontrol PASS, 17/17 MP3 decode, 27 HTTP souborů přesné. Skutečné Safari: obraz Ollie, Bunny 10/10, Again, viditelné postavy a podběrák. První Azure podklady beze změny. První Terra receipt `4b261f77c13a77e845684bbbd90cc876`: gate 3412 PASS, push confirmed, deployment uncertain; GitHub Pages run `42839271179` po 600000 ms syncing_files deployment zrušil. Po zrušení HTML 404. Výsledkový report zachovává první neúspěšný běh bez přepisu.
