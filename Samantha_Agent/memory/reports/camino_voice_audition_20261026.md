# Camino — české hlasy k poslechovému výběru

Stav: 2026-10-26 16:33 CET, čtyři místní katalogové ukázky připravené; hlas D — Orus vybraný,
žádná změna kódu střižny, generátoru, služby či iPhonu a žádné nové p+n.

## Hotový poslech

Míla odmítá kvalitu Zuzany a žádá připravit lepší hlasy. K dispozici jsou
čtyři skutečné české referenční ukázky z oficiálního katalogu Google Cloud:

| Volba | Hlas | Typ | Délka | MP3 bajtů |
| --- | --- | --- | ---: | ---: |
| A | Kore | ženský | 6.48 s | 47301 |
| B | Aoede | ženský | 6.04 s | 46821 |
| C | Charon | mužský | 5.68 s | 49917 |
| D | Orus | mužský | 6.32 s | 50757 |

Celkem 194 796 B (190,2 KiB), Google Chirp 3 HD, locale cs-CZ. Nejde o vlastní
novou syntézu ani o posouzení kvality Adamem. Ukázky jsou ze současného
oficiálního katalogu: https://docs.cloud.google.com/text-to-speech/docs/list-voices-and-types
Podpora češtiny a rodina hlasů: https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd

Vše je v ignorované projektové složce
`data/private/camino/voice-audition-20261026/`: čtyři MP3, index.html a manifest.json.
Původní WAV se stahovaly pouze do paměti; MP3 mají zdrojovou URL i oba SHA-256
v manifestu. Složka 0700, soubory 0600. Poslechová stránka má běžné/pomalejší/
rychlejší přehrání, pauzuje předchozí hlas při spuštění jiného a nabízí stažení.
Příkaz k otevření index.html výslovně v Safari skončil úspěšně; nepoužil se
Apple Music ani obecné otevření audio souboru. Skutečný poslech Míly a vizuální
kontrola stránky zatím NEOVĚŘENO.

## Generování a hranice

- Registrované externí generování necitlivého obsahu má živě ověřený aktivní
  odvolatelný souhlas trusted_external_generation_v1. Připraven byl pouze
  smyšlený český text, žádné soukromé deníky, média, GPS či tajemství.
- První pokus přes registrovaný Edge TTS helper na známém funkčním endpointu
  Microsoftu skončil HTTP 429. Vlastní vzorky nevznikly; žádná série retry.
  Staré PlayHT audio odkazy nebyly dostupné, proto konečný výběr používá
  aktuální oficiální katalog Google. Microsoft Vlasta/Antonín nejsou součástí
  výsledných souborů. V manifestu zůstává pravdivý záznam nulových generací.
- Stahování z Googlu ověřovalo TLS přes certifi; ověřování nebylo vypnuté,
  systémová konfigurace ani knihovny se neměnily. Nevznikl nový placený API
  požadavek, účet ani instalace hlasu. Katalogová ukázka není důkaz připravené
  API integrace pro vlastní texty.
- Střižna nadále používá dosavadní Zuzanu. Zvolený cloudový hlas teprve
  vyžaduje ověření API přístupu, ceny/rozpočtu a oprávnění ke konkrétním textům.
  Do deníku je stále soukromé; globální souhlas necitlivé tvorby neopravňuje
  odeslat deníkový text externě. Žádné automatické online nahrazení Zuzany.
- Chatový Edge helper text nad 1500 znaků zkracuje. Pro případné budoucí
  filmové zapojení jej nelze přímo připojit na komentář do 6000 znaků; musí
  zachovat celý zvolený text a prokázat skutečnou délku. Platí LL-080/081.

## Ověření a další krok

Všechny čtyři MP3 prošly úplným FFmpeg dekódováním; délka změřená ffprobe,
SHA-256 i lokální odkazy v poslechové stránce ověřené. JavaScript porovnávací
stránky prošel node --check. Produkční kód se neměnil, jeho plná brána se
neopakovala. Předchozí vydání 004ec7e1/Luna 05b42458 zůstává doložené zvlášť.

Míla vybral D — Orus. Konkrétní připojení je popsané níže; stále chybí
přístup ke Google Cloud a schválení aktivace/rozpočtu.
Vícedenní film P2-F zůstává pozdější etapa po přijetí střihu skutečného dne.

## Vybraný D — Orus, 2026-10-26 17:01 CET

Volba Míly uložená v manifestu a označená na index.html, přesně
`cs-CZ-Chirp3-HD-Orus`. Tempo nebylo zvlášť zvolené. Vlastní texty se tímto
krokem nesyntetizovaly a výchozí hlas aplikace zatím není přepnutý.

Read-only audit konfigurace: žádné související Google/GCP/Gemini/TTS hodnoty
v projektovém .env, odpovídající shellové proměnné nenastavené, běžný místní
ADC soubor chybí a google.auth/google.cloud.texttospeech nejsou instalované.
To neprokazuje neexistenci účtu nebo projektu u Googlu. Míla dostal asynchronní
otázku na existující projekt, bez žádosti o hesla či klíče do chatu.

### Konkrétní postup připojení

1. Určit Mílův Google Cloud projekt a ověřit povolený Cloud Text-to-Speech
   a billing; nevytvářet účet/placenou konfiguraci bez příslušného souhlasu.
2. Bezpečně nastavit místní přístup dle oficiální ADC autentizace, bez
   tajemství v Gitu/chatu. Konkrétní způsob závisí na Mílově projektu;
   nic se zatím neinstalovalo ani nepřihlašovalo.
3. Po schválení rozpočtu provést jedinou první smyšlenou zkoušku do 1000
   znaků; odhad nejvýše 0,03 USD při placené sazbě, bez předpokladu dostupné
   bezplatné kvóty. Při nejistotě či chybě neprovádět automatickou novou syntézu.
4. Integrovat Orus pro celý komentář do 6000 znaků: API má limit 5000 UTF-8
   bajtů na požadavek, proto dělit beze ztráty a spojit v původním pořadí.
   Nepoužít zkracující chatový helper, zachovat historii/koš a starší filmy.
   Vždy předem výslovně potvrdit odeslání daného textu Googlu a cenu;
   běžný globální souhlas necitlivé tvorby nepovoluje soukromý deník.
5. Ověřit skutečný celý zvuk, délku, revizi/text/oprávnění před i po pomalé
   operaci. Žádný automatický fallback na jiný hlas. Publikace/nasazení
   zůstávají samostatné p+n.

Soukromý integration-plan.json zmrazuje hlas, navržený rozsah zkoušky,
cenové podklady a čekající přístup/billing/rozpočet. Není hotovým adaptérem
ani důkazem úspěšné syntézy. Zatím žádný placený API požadavek.

Oficiální ceník ověřený 26. 10. 2026: Chirp 3 HD uvádí 1 milion znaků měsíčně
zdarma, potom 30 USD/milion znaků. Billing je nutný i pro bezplatnou kvótu;
aktuální nárok a vyčerpání konkrétního účtu neověřené. 6000 znaků odpovídá
0,18 USD při zveřejněné placené sazbě; approved_budget_usd v plánu zůstává null.

Zdroje: https://cloud.google.com/text-to-speech/pricing ;
https://docs.cloud.google.com/text-to-speech/docs/get-started ;
https://docs.cloud.google.com/text-to-speech/docs/authentication ;
https://docs.cloud.google.com/text-to-speech/quotas .

## Publikace dokumentace — 2026-10-26 17:16 CET

Účtenka `c418d280bd7f24e0146cf90fabe2e4c6`: completed, 3 commity do
`4dc658324465859f71e8294d880738cd306fd35d`, push/deployment confirmed,
project-camino → Cockpit. Plná publikační brána 2243 PASS /
430.7 s, smoke 5/5, protected_services_unchanged=true.

Adam jednou převzal účtenku a ověřil, že rozsah od funkčního 004ec7e1 obsahuje
pouze memory soubory. Health OK, přesné HTML HTTP 200, SHA-256
`996571f43ceeb225384e0d6173a06421e3d91a057edc985abc91304ae040b0ab`, code stamp `dd0a0d1332d72444`.
Soukromý manifest stále selected_voice=Orus a installed_in_editor=false.
Toto vydání nezprovoznilo Google Cloud přístup ani nový hlas v aplikaci.
Return caller převzatý, returned_to_adam=false není důvodem retry.
Následný výsledkový zápis je místní checkpoint pro příští vývoj; další krok
je chybějící Google Cloud projekt/přístup a schválení aktivace/rozpočtu.
