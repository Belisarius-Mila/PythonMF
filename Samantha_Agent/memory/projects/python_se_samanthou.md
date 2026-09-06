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

Míla potvrdil, že rozbalená verze 1.1 se chová stejně jako původní aplikace;
v této zprávě výslovně neurčil platformu. Nová 1.2 čeká na uživatelský retest
přepínání balíčků na Linuxu. Přenos postupu mezi
počítači zatím není hotový. Původní a nová aplikace používají oddělené postupy.
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
