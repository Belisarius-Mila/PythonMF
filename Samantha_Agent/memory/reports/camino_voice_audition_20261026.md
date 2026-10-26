# Camino — české hlasy k poslechovému výběru

Stav: 2026-10-26 16:33 CET, čtyři místní katalogové ukázky připravené; hlas nevybraný,
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

Míla poslechne A–D a vybere hlas/tempo, případně odmítne všechny. Teprve potom
připravit konkrétní proveditelnou integraci pro vlastní filmový komentář.
Vícedenní film P2-F zůstává pozdější etapa po přijetí střihu skutečného dne.
