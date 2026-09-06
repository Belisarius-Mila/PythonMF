# Python se Samanthou

Aktualizováno: 2026-09-06, Europe/Prague.

## Cíl a dohoda

Mílova začátečnická offline učebna Pythonu od Samanthy (ChatGPT), původně
jeden soubor přijatý přes LocalSend. Musí fungovat na Macu i Linux PC.
Míla nejprve požádal pouze o analýzu, následně schválil postup vývoje
a pokynem „OK, jdeme na to! Začni.“ autorizoval první krok.

Pořadí: oddělit sedm lekcí → přenos kurzů a postupu → Moje dílna → vysvětlení
kódu a doplňující otázky → kontextové nápovědy → skutečné krokování → více lekcí.
Míla následně upřednostnil připojení dalšího balíčku sedmi lekcí. AI připojení se
bude řešit až v příslušné fázi.

## První krok

Samostatný projekt `PythonSeSamanthou/` vedle `Samantha_Agent/` v repozitáři PythonMF.
Verze 1.1 načítá `kurzy/python_zaklady/kurz.json` a sedm složek s `lekce.json`,
`vyklad.md`, `ukazka.py`, `reseni.py`. Původní texty a kód jsou zachované.
Kontroly jsou deklarativní data, ne spustitelné pluginy. Nová lekce využívající
existující typy kontrol nevyžaduje změnu aplikace; ověřeno osmou testovací lekcí.

Postup používá trvalá ID, nikoli pořadí. Migrace v1 zná pevné původní pořadí sedmi
lekcí, zachovává originál, tvoří přesnou záložní kopii a ukládá do `prubeh_v2.json`.
Vadný formát a konflikt současných aplikací zastaví zápis. Zápis je atomický.
Žádný skutečný osobní postup se při vývoji nečetl ani nepřeváděl.

## Důkazy a předání

- 27 cílených testů: shoda původních textů, běhu a hodnocení; stabilní ID;
  přidání/reordering lekcí; validace balíčku bez spuštění příkladů; migrace,
  záloha, konflikt, vadný formát a simulované selhání zápisu.
- Skutečné Tk GUI na Macu: migrace testovacích dat, sedm běhů a kontrol,
  kreslení, uložení, znovuotevření s obráceným pořadím lekcí. Prošlo i z rozbaleného ZIPu.
- Python 3.9 gramatika ověřena pro všechny Python soubory; běhové testy na Pythonu 3.12.
- ZIP v LocalSendu: `PythonSeSamanthou_1_1_20260906.zip`, 38 souborů, 51 475 B.
  SHA-256 `9eef90640b66e7ee16f508ea5fab1496d0655fc40664ed22e4bc6ba2cf084cd0`.
- Originál v LocalSendu zůstal byte-for-byte zachovaný; SHA-256
  `94583742b6b192e9610c63fd9dca67f735a818ee47235d51fd63a6486f6c6013`.
- Plná projektová brána: 1518 testů prošlo (447,156 s); rychlá statická brána
  i pět testů projektového registru prošly. Místní checkpoint bez push/deploy.

## Otevřené a omezení

Míla potvrdil fungování 1.2 po vyřešení záměny při spuštění na Linuxu a zadal
vývoj Mojí dílny. Verze 1.3 je ověřená na Macu a čeká na jeho Linux retest.
Přenos postupu mezi počítači zatím není hotový. Původní a nová aplikace používají oddělené postupy.
Hodnocení záměrně zachovává omezené kontroly původní učebny. Spuštěný kód má
přístup k počítači; časový limit není bezpečnostní sandbox.

Jde o samostatný terminálový projekt. Není založen Human–Adam proud ani TVBCP;
nový TVBCP se případně založí až po výslovné dohodě. Cockpit ani Pages se nenasazují.
Kanonický handoff: `handoffs/python_se_samanthou_course_package_2026_09_06.md`.


## 2026-09-06 12:40 CEST — Druhý balíček a verze 1.2

Hotovo:
- Původní commit fa329883 byl na Mílův pokyn pushnut; vzdálený main byl ověřen.
- Balíček python-dalsi-kroky obsahuje sedm navazujících lekcí: text/f-string,
  seznam/index, for nad seznamem, return, while, slovník a bodovací panel.
- Verze 1.2 má výběr balíčku v GUI. Kurzy se načítají ze složky kurzy;
  přepnutí zachovává vlastní pokusy, dokončení i poslední lekci každého kurzu.
  Během spuštěného programu nebo při selhání uložení zůstane původní výběr.
- Původní balíček a formát prubeh_v2.json zůstaly beze změny.
- 31 automatických testů, původní i nové Tk GUI smoke na Macu prošly.
  Ověřena rozbalená distribuce i samotný přídavný balíček nad nezměněnou 1.1:
  všech sedm nových řešení prošlo i původním hodnoticím modulem.

Rozhodnuti:
Nový obsah používá stávající formát i typy kontrol. Připojení samo o sobě
nevyžaduje aktualizaci aplikace: 1.1 ho otevře přes --course; 1.2 přidává pohodlí
výběru v okně. Při běžném startu se otevře základní balíček. Původní datum a
historický důkaz první etapy výše popisují verzi 1.1, nikoli dnešní 1.2.

Dalsi krok:
Míla rozbalí kompletní 1.2 a vlevo zvolí Python — další kroky. Na Linuxu ověřit
přepínání, poslední lekci a původní pokusy; novou verzi tam Adam přímo nespouštěl.

Navrhovane dalsi kroky:
Po uživatelském retestu Moje dílna nebo samostatný přenos postupu mezi počítači.
AI ani synchronizace nejsou součástí této etapy. Nový push zatím nebyl autorizován.

Technicky dukaz:
- LocalSend: PythonSeSamanthou_1_2_20260906.zip, 70 souborů, 71 076 B,
  SHA-256 d8900676fb9c246c857114bb4b812696cac909ae2d69383340ad108fa5323f3d.
- LocalSend: PythonDalsiKroky_7lekci_20260906.zip, 30 souborů, 14 264 B,
  SHA-256 570a1e246ad24d66f866a1a951f858295cf6f6d952e4cb223d52c7d9acfb7766.
- Testy pracují výhradně s dočasnými daty; osobní postup se nečetl ani neměnil.
- Plná projektová brána: 1518 testů za 442,615 s, jediná chyba byla vazba nového
  řádku ACTIVE_PROJECTS na katalog Cockpitu. Opravena přesunutím samostatného
  terminálového projektu do výslovné textové části registru; bez zakládání
  neobjednaného pracovního proudu/TVBCP. Všech 28 testů katalogu a registru po
  opravě prošlo. Ostatních 1517 testů prošlo v plném běhu; celý běh se po této
  čistě dokumentační opravě neopakoval. Rychlá statická brána prošla.
- GUI při rozměru 900 × 640: přepínač a všechna tlačítka postranního panelu
  jsou zobrazená a vejdou se do panelu na Macu.


## 2026-09-06 14:08 CEST — Moje dílna, verze 1.3

Hotovo:
- Míla potvrdil, že 1.2 funguje; předchozí problém se zobrazením vyřešil sám.
  Následně výslovně zadal vývoj dílny podle dohodnutého pořadí.
- Samostatné okno Moje dílna: pojmenované pokusy, nový pokus, přejmenování,
  kopie, poznámky, automatické i ruční uložení, obnovení posledního pokusu.
- Tlačítko Do dílny kopíruje aktuální kód lekce; originál i dokončení zůstávají.
- Stejný worker a sdílené kreslení, výpis, konečné jednoduché proměnné,
  vysvětlení chyb a třísekundový limit. Dílna nemá školní hodnocení.
- Import UTF-8 .py vytvoří kopii bez spuštění či přepsání zdroje; export kódu
  vytváří výhradně nový soubor. Poznámky se ukládají jen v dílně.
- Soukromý dilna.json je oddělený od prubeh_v2.json ve stejné datové složce;
  platí i vlastní --state-dir. Atomický zápis, ochrana konfliktu, vadný formát
  se nepřepíše. Když nelze uložit, přechod na jiný pokus se zastaví a zavření
  se musí v UI výslovně potvrdit. Osobní data Míly se při vývoji nečetla.

Rozhodnuti:
První dílna funguje offline. AI vysvětlování a doplňující otázky jsou příští
samostatný krok; nyní se nic externě neodesílá. Seznamy a slovníky se zatím
prohlížejí přes print(), ne v přehledu jednoduchých konečných proměnných.
Aplikace i titul dílny zobrazují 1.3. ZIP má vlastní kořenovou složku
PythonSeSamanthou_1_3, aby se omezila záměna s dříve rozbalenou učebnou.

Dalsi krok:
Míla na Linuxu rozbalí jediný kompletní ZIP 1.3, spustí program z nové složky,
zkusí Moji dílnu, kopii z lekce, běh a obnovení kódu/poznámek po zavření.

Navrhovane dalsi kroky:
Po retestu vybrat AI vysvětlování s doptáváním nebo přenos pokusů mezi počítači.
Žádný nový push/deploy zatím nebyl autorizovaný.

Technicky dukaz:
- 42 automatických testů prošlo. Tři skutečné Tk GUI smoke na Macu prošly:
  původní sedm lekcí, oba balíčky a dílna. Dílna ověřuje kopii z lekce, pojmenování,
  poznámky, kresbu, SyntaxError, timeout, import/export, konflikt, close/reopen
  a nezměněný soubor postupu lekcí. Ověřeno také okno 900 × 640.
- Stejné testy a dílna prošly z rozbalené distribuce. Python 3.9 gramatika
  ověřena; běh na Pythonu 3.12. Oba balíčky lekcí jsou byte-for-byte zachované.
- LocalSend: PythonSeSamanthou_1_3_20260906.zip, 75 souborů, 84 039 B,
  SHA-256 7f33b4894fed9b593f5998f958116780cb9e368b4a06f271c036225f78953aad.
- Plná brána 1.3: všech 1518 testů prošlo (284,622 s), rychlá statická brána
  a všech 28 testů katalogu/registru po finální úpravě paměti prošly. Finální
  ZIP je porovnán se všemi 75 distribuovanými soubory.
