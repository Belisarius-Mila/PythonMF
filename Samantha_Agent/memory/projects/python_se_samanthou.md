# Python se Samanthou

Aktualizováno: 2026-09-06, Europe/Prague.

## Cíl a dohoda

Mílova začátečnická offline učebna Pythonu od Samanthy (ChatGPT), původně
jeden soubor přijatý přes LocalSend. Musí fungovat na Macu i Linux PC.
Míla nejprve požádal pouze o analýzu, následně schválil postup vývoje
a pokynem „OK, jdeme na to! Začni.“ autorizoval první krok.

Pořadí: oddělit sedm lekcí → přenos kurzů a postupu → Moje dílna → vysvětlení
kódu a doplňující otázky → kontextové nápovědy → skutečné krokování → více lekcí.
Další fáze nyní nejsou implementované. AI připojení se bude řešit až v příslušné fázi.

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

Skutečný Linux GUI retest je otevřený; přístup přes SSH nebyl dodaný. Míla má
v ZIPu README se spuštěním a krátkým kontrolním postupem. Přenos postupu mezi
počítači zatím není hotový. Původní a nová aplikace používají oddělené postupy.
Hodnocení záměrně zachovává omezené kontroly původní učebny. Spuštěný kód má
přístup k počítači; časový limit není bezpečnostní sandbox.

Jde o samostatný terminálový projekt. Není založen Human–Adam proud ani TVBCP;
nový TVBCP se případně založí až po výslovné dohodě. Cockpit ani Pages se nenasazují.
Kanonický handoff: `handoffs/python_se_samanthou_course_package_2026_09_06.md`.
