# MMTX – odstranění šesté scény u jezera

- 2026-11-10 12:12 CET: šestá scéna u jezera je odstraněná z aktivní produkce i všech pěti známých místních pracovních prostředí. Vývojový commit `359007b95eb1aad652fa0d4b9e50fc371994f29e` je na GitHub main a přesně nasazený na Pages. Z šestky zůstal jen první obrázek `arrival.webp` (380134 B, SHA-256 `038d273ff95d3077fe26d142ad32ca6fc32d0e9b5c6997ea53c161964fedcf65`) na dosavadních veřejných i místních adresách.
- Odstraněná jsou ostatní média a kód šestky, generátor, jeho dva testové moduly, oba Azure workflow příkazy a přechody ze scény s mostem. Dokončení mostu zůstává jako neklikací stavová zpráva. Scény 1–5, Logan, obrázek loučení i sdílené TTS moduly jsou zachované.
- Úklid: 1584 plánovaných souborů / 35524901 logických bajtů plus 11 souborů bytecode šestky / 171605 B; celkem 35696506 B (asi 35,7 MB). Skutečné uvolnění APFS bloků není tímto součtem měřené. Historie Gitu, zálohy a neidentifikované obecné cache se nepromazávaly.
- Ověření: 51 cílených testů PASS; místní plná brána 3402 testů / 0 chyb / 31 přeskočených (700,764 s unit), plná publikační brána 3402 testů PASS (603,5 s). Předchozích 5910 souborů v pěti prostředích odpovídá původním otiskům s výjimkou 20 očekávaných změn HTML/CSS zakončení mostu; předchozí média beze změny.
- Jediné registrované p+n `project-mmtx` / GitHub Pages: Terra 6.1/high, účtenka `27d91d1047e66647a4e71d99a6279ae1`, completed; push_state/deployment_state=confirmed. Pages run `42804962744`, deployment `7680433197`, HTTP smoke 200; chráněné služby beze změny. Caller účtenku převzal; returned_to_adam=false je portálový příznak, žádný další pokus se neposílá.
- Jedna závěrečná veřejná kontrola: 156 odstraněných souborů + URL celé šestky vracejí HTTP 404; zachovaných 55 veřejných souborů má HTTP 200 a přesné SHA-256, včetně prvního obrázku, vstupů scén 1–5 a Loganova audia/obrázků. GitHub main přesně odpovídá nasazenému commitu. Důkazy a úplný seznam jsou soukromě v `data/private/mmtx/scene06_retirement_review_20261110/`.
- Datův vlastní commit `c87f6064967aa21b9a998279c6fa874f908cd4c8` zůstal zachovaný. V jeho stávajícím worktree je úklid šestky jako 321 souvisejících WIP změn; jeho větev se neslučovala, nerebasovala ani nepřepisovala. Čisté profily Human–Adam/Knihovna a pomocný Willův checkout byly srovnané s main servisním fast-forwardem po výslovné globální brzdě; automatický limit hromadného mazání zůstal zachovaný.
- Nesouvisející zdrojové změny a oba nově přidané necommitované scénáře jsou zachované mimo vydaný balíček. Závěrečný paměťový checkpoint je místní a patří do příštího GitHub balíčku; další p+n se pro samotný zápis neopakuje.
- Další krok: při další práci s Datovou větví zohlednit její výše popsaný WIP úklid a vlastní commit. Fyzický proklik na Macu/iPhonu po změně se neprováděl; serverové odstranění a zachované bajty jsou ověřené.

## Publikační důkaz

- [Pages workflow](https://github.com/Belisarius-Mila/PythonMF/actions/runs/42804962744).
- [Zachovaný první obrázek](https://belisarius-mila.github.io/PythonMF/scene06_lake_arrival/arrival.webp).
- [Zachovaná scéna s mostem a Loganem](https://belisarius-mila.github.io/PythonMF/scene05_log_bridge/).
- Úplný kontrolní seznam, původní otisky, doklad schválení servisního FF a výsledky HTTP jsou místní mimo Git; neobsahují zveřejněné přihlašovací údaje ani soukromé scénáře.
- Starší reporty šestky jsou historické podklady, nikoli aktuální pokyn k obnovení odstraněné scény.
