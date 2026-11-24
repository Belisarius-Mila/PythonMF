# Francouzština Jana — příprava trvalého hostingu

Render: Hobby workspace, jedna placená instance `0.5c-512mb`, Frankfurt,
1 GB persistent disk `/var/data`. Návrh základu **7,25 USD/měsíc** před daněmi
(7 USD compute + 0,25 USD disk), 5 GB přenosu v Hobby, potom 0,15 USD/GB.
Ceník ověřen 24.11.2026: https://render.com/pricing . Cena není provozní strop.

**Příprava není souhlas s placenou aktivací ani publikováním.** Účet a
konkrétní URL ještě nejsou určené. Applying Blueprint vytváří placenou službu.

## Nasazení po souhlasu

1. Vydat přesný přípravný commit registrovaným FR p+n přes Terru.
2. V účtu Render použít Blueprint path
   `Samantha_Agent/deploy/vocabulary-fr/render.yaml`. Repo root ponechat
   jako build root. Blueprint používá JSON syntaxi (podmnožina YAML).
3. Zkontrolovat workspace Hobby, plán, region, disk a jednu instanci.
   Automatická nasazení z Gitu jsou vypnutá. Schválit počáteční placenou aktivaci.
4. Render sám dodá `RENDER_EXTERNAL_URL`, `RENDER_GIT_COMMIT` a `PORT`.
   Build vyexportuje veřejné FR vstupy z přesného HEAD do
   `.fr-cloud/releases/$RENDER_GIT_COMMIT`. Start spouští jediný exportovaný
   modul v izolovaném Pythonu, bez importů Samanthy/Cockpitu.
5. Ověřit release SHA u poskytovatele, veřejné bajty a API health, obrázky,
   MP3 Range/206, dvě nezávislé session a další kolo s novými slovy.
6. Ověřit restart se stejným diskem a místností. Až potom zapsat skutečný
   vlastněný HTTPS původ do `docs/vocabulary-fr/online-hosting.json` a vydat
   propojení FR Pages/Cockpitu registrovaným postupem. Konfigurace je nyní `null`.
7. První nová adresa vyžaduje novou místnost/pozvánku. Další kola zůstávají
   ve stejné místnosti. Osobní data původního webu zůstávají na Pages.

## Provozní hranice

- Cloud entrypoint přijme jen Render HTTPS původ, platný port a existující
  absolutní data directory. Lokální loopback-only CLI se nemění.
- Health ověří databázovou tabulku; cizí Host/Origin a soukromé routy se odmítnou.
- `SIGTERM` zastaví přijímání požadavků a nechá dokončit časově omezené requesty.
- Jedna instance se stejným diskem. Aktualizace s diskem má krátký výpadek;
  nemá zero-downtime ani SLA základního plánu. Žádné paralelní repliky SQLite.
- Platnost místností zůstává 24h / 2h bez aktivity. Prošlé záznamy se tímto
  přípravným krokem automaticky nemažou.
- Před aktualizací lze v běžící Render shell session spustit exportovaný modul
  s příkazem `backup` místo `serve`. Vytvoří novou 0600 SQLite zálohu v
  `/var/data/backups`, bez mazání/přepisování a bez off-site uploadu.
- Záloha na stejném disku není nezávislá kopie. Snapshoty poskytovatele
  nepovažovat za náhradu konzistentní SQL zálohy. Vlastní doména není v této etapě.
- Nevkládat klíče poskytovatele do Gitu nebo Blueprintu. Soukromá lokální
  databáze, Samantha, Camino a další aplikace nejsou součástí exportu.

Testy: `tests.test_vocabularyfr_cloud`, existující FR hosting/multiplayer/galerie.
Skutečný rozsah určuje `scripts/validation_gate.py`. Živý Linux/Render build a
fyzická přejímka vyžadují aktivovaný účet; místní test není důkaz nasazení.

Podklady: [web service](https://render.com/docs/web-services),
[disky](https://render.com/docs/disks), [Blueprint](https://render.com/docs/blueprint-spec),
[environment](https://render.com/docs/environment-variables),
[health](https://render.com/docs/health-checks), [Python](https://render.com/docs/python-version).
