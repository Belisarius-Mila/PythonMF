# Připravená aktivace týdenního správce obnovy

2026-11-08 16:45 CET, Data, vlastní větev data/parallel-20261104. Žádná instalace služby,
změna skutečné role/aktivace nebo provozních TXT a žádný placený tah.

## Konkrétní balíček k potvrzení

- SHA návrhu `770a11bf39d5880eeda4f3db12708d706518b9e74048b604c58a297bf8832cb6`. Soukromý neměnný návrh je ve vlastní
  .venv/recovery_guide_activation; není to skutečná activation.json.
- Dva pevné cíle: PythonMF/OBNOVA_SAMANTHY_NOVY_MAC.txt a stejné jméno v
  iCloud Drive → Dokumenty. Oba cílové TXT zatím neexistují; složky existují,
  iCloud alias je připnutý a Foundation potvrzuje ubiquitous parent.
- Počáteční kandidát75 448B/SHA`f8c2972994f34dc9dd904162667eae6c147980941e1178e7735759281a605c4e` má17 kapitol,
  všech340 obsahových bloků přijatého čtenářského podkladu zachovaných;
  proti75415B návrhu jde jen o programové formátování záhlaví/oddělovačů.
  Publikuje se bez modelu, obě SHA a skutečný upload se ověří před službou.
- Model gpt-6.1-sol, medium, Standard v každém tahu. Role má doložený skutečný
  REC-06 trial_passed z7.11.,0,3094 odhadovaného kreditu. Ostatní role se nemění.
- Návrh neděle od09:00 Europe/Prague, první slot15.11.2026. Plist kontroluje
  splatnost po15 minutách; neznamená placený tah po15 minutách ani dohnání všech týdnů.
- Navržené meze200 kreditů/běh a1000/měsíc, max20 tahů,2400s, vstup240000,
  finální výstup32000, inspection8000. Jde o přijímací/rezervační limity,
  nikoli tvrdý poskytovatelský billing/output/time cap. Při růstu korpusu
  za schválenou rezervu se nový běh před modelem zastaví.

Profil přejímky zahrnuje Python, Codex, Cockpit, Tailscale, Camino, Xcode,
iCloud, VS Code, Homebrew, Git a Zkratky. Je to navržený rozsah kontrol;
neprohlašuje se za živý inventář všech aplikací na Macu/iPhonu. Neznámá pole
zůstávají neověřená. Čtený korpus nadále zahrnuje celou schválenou dokumentaci.

## Aktuální neplacený plán

547 zdrojů včetně úzké projekce deklarované konfigurace tohoto agenta,
14 inspect +1 synth, rezerva193,42345 kreditu bez předpokládané cache.
Tokenizer o200k_base/tiktoken0.14.0 s20% marží je pouze reference;
přesné modelové mapování/plný skrytý prompt tím prokázané nejsou.
Sazby50/2,5/250 kreditů za milion input/cache/output byly aktuálně ověřené
v [OpenAI Docs — Pricing](https://learn.chatgpt.com/docs/pricing).
[OpenAI Docs — Models](https://learn.chatgpt.com/docs/models) uvádí pro Sol
výchozí500000 kontext; zde zůstává konzervativní reference admission240000
na stejném živě ověřeném peeru0.163.0. Není to měření aktuálního skrytého promptu.

## Co bylo nutné opravit před zapnutím

1. Samotný vývojový worktree by nečetl Willovy nové commity. Nyní bere
   aktuální refs/heads/main přes Git objects, bez checkoutu a cizího WIP.
2. Původní integrace po každém týdnu čekala na ruční přejímku. Výslovně
   přijatá politika validated_auto_v1 může po gate převzít přesné bajty
   a předat je writeru; manual zůstává alternativou. Nejistý návrh se nepublikuje.
3. Globální Fast už falešně neblokuje explicitní per-turn Standard. Globální
   konfigurace se nemění; API-key účet neprojde kreditovým plánem.
4. Aktivační hranice má před přepisem kontrolu cizích změn, stejné kopie a
   pending-cloud pokračování bez modelu. Po nejistém bootstrap už neposílá další.

Automatická politika neprokazuje pravdivost libovolného textu. Nadále drží
citace, pokrytí původních bloků, procedur a bezpečnostních kontrol, aplikace,
macOS baseline, zákaz nedoložených příkazů/tajemství a nerozlišování historie
od live stavu není povoleno. Aplikační/telefonní pole bez skutečného důkazu
zůstávají unverified. Datum čtení dokumentu je pouze datum čtení; žádné fake
ruční přejímky iPhonu se nevytvářejí. Historie/citace zůstávají mimo čtenářský TXT.

## Stav oprávnění a další akce

Míla řekl Aktivuj a určil obě místa. Místní global_safety_brake.md však
výslovně zahrnuje „zmeny systemove konfigurace mimo projekt: shell profily,
LaunchAgents“. Proto dosud není provedena systémová instalace ani skutečná
aktivace; staré fráze k mazání/cache nejsou souhlasem pro tuto jinou akci.
Finální fráze bude současně přijímat právě tento rozpočet/čas/publikační návrh.

Po potvrzení zavolat jednou `app.recovery_guide_activation.activate` s přesným
SHA a skutečným potvrzením. Program ověří kód/podklad/cíle a ostatní role,
provede počáteční publikaci bez modelu, skutečný upload a jediný bootstrap.
Žádné push/deploy/main integrace, restart Codexu/Cockpitu, role jiných agentů
nebo nové modelové volání dnes. Běhový kód/tokenizer zůstává v Data worktree;
zdroje jsou aktuální main a úzká konfigurace. Při přesunu této pracovní kopie
bude nutné vlastní službu vědomě převzít včetně privátního stavu a proběhlých slotů.

## Ověření

206 cílených testů PASS; plná brána 2 882 testů OK (5 skipped); závěrečná statická brána a git diff --check OK.
Osm aktivačních testů používá pouze fake launchctl a dočasné cíle; neinstaluje
skutečný LaunchAgent. Automatické dva týdny, crash po přijetí před připojením,
změna macOS/dossier/source, odmítnutí API-key, aktuální main bez přepnutí větve
jsou pokryté v runtime sadě. Skutečná přejímka nového kontraktu providerem
zůstává otevřená do prvního schváleného běhu. Fyzický iPhone se ověří zvlášť.

Čtecí status v navrženém minimálním launchd PATH prošel; skutečná launchd
session, autentizace v ní a fyzický iPhone tím nejsou prokázané.
