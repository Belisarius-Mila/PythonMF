# Python se Samanthou

Aktualizováno: 2026-09-06, Europe/Prague.

## Cíl a dohoda

Mílova začátečnická offline učebna Pythonu od Samanthy (ChatGPT), původně
jeden soubor přijatý přes LocalSend. Musí fungovat na Macu i Linux PC.
Míla nejprve požádal pouze o analýzu, následně schválil postup vývoje
a pokynem „OK, jdeme na to! Začni.“ autorizoval první krok.

Pořadí: oddělit sedm lekcí → přenos kurzů a postupu → Moje dílna → vysvětlení
kódu a doplňující otázky → kontextové nápovědy → skutečné krokování → více lekcí.
Míla následně upřednostnil připojení dalšího balíčku sedmi lekcí. AI připojení přes Codex/ChatGPT je nyní součástí verze 1.5; viz nejnovější záznam dole.

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
vývoj Mojí dílny. Verzi 1.3 otevřel, ale hlásil nemožnost upravovat text.
Verze 1.5 zachovává aktivaci editoru a nahrazuje API přihlášeným Codexem;
čeká na Linux retest a instalaci/přihlášení Codexu.
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


## 2026-09-06 15:17 CEST — AI průvodce a zadávání textu, verze 1.4

Hotovo:
- Míla zadal opravu údajně read-only dílny a připojení AI vysvětlování/vedení.
  Na Linuxu nemá API klíč ani přihlášený Codex („Ani jedno“).
- Editor a poznámky už v 1.3 měly state=normal; skutečné stisky kláves na Macu
  fungovaly. Příčina konkrétního linuxového hlášení není potvrzená. Verze 1.4
  výslovně aktivuje editor, označuje pole MŮJ KÓD, přidává Upravit kód,
  zaměření při kliknutí/otevření, nabídku Vložit/Vybrat vše a Ctrl+A.
- AI průvodce: vysvětlení po krocích, pomoc s chybou, malý další úkol a doptávání.
  Vlastní otázka má přednost před zvoleným režimem. Kód AI nemění ani nespouští.
- Oddělené rozhovory podle identity pokusu, asynchronní odpovědi, upozornění na
  změněný kód během čekání. Přikládá výpis/chybu jen pro přesně shodný kód.
- Nastavení zakrytého API klíče a modelu; bez klíče dílna dál funguje offline.
  Klíč z UI pouze v paměti otevřené dílny, případně načtení OPENAI_API_KEY.
  Žádný klíč se nekopíroval na Linux ani do souborů/ZIPu. Worker nedědí dvě
  jmenované API proměnné; stále není bezpečnostním sandboxem.
- Běh učebního kódu, oba balíčky, postup a formát dilna.json zachovány.

Rozhodnuti:
OpenAI Responses API, výchozí gpt-5.4-mini, HTTPS přes standardní knihovnu,
bez pip závislostí, bez automatických retry a bez spouštění AI návrhů.
Explicitní tlačítko odesílá kód/poznámky/výpis a rozhovor; store=false není
slib nulové retence služby. Historie jen v paměti, šest dvojic na pokus,
při dotazu pět předchozích dvojic. Důležité odpovědi lze kopírovat do poznámek.
Na tomto Macu chybí Python CA bundle; TLS context přidává systémový cert.pem
výhradně na macOS, ověřování certifikátů zůstává zapnuté. Linux používá default CA.

Dalsi krok:
Míla rozbalí jediný PythonSeSamanthou_1_4_20260906.zip a spustí aplikaci
z nové složky. Ověřit skutečné psaní/vložení na Linuxu. Pro AI si vytvoří
vlastní OpenAI API klíč, nastaví API účet a klíč vloží do Nastavení AI.

Navrhovane dalsi kroky:
Po retestu případně trvalé lokální nastavení přihlášení podle Mílova přání,
přenos pokusů mezi stroji nebo skutečné krokování. Bez nového TVBCP/Cockpit proudu.
Předchozí 1.3 byla na Mílův pokyn pushnuta jako 6fb2c215; nový krok 1.4 se nyní
ukládá pouze lokálně a potřebuje nový výslovný pokyn pro push.

Technicky dukaz:
- 51 cílených testů; čtyři skutečné Tk GUI smoke na Macu. Nový GUI test zadává
  klávesy, BackSpace, Return, Ctrl+A a náhradu výběru; ověřuje 900 × 640,
  bezklíčový režim, historii, odloženou odpověď jinému pokusu, změnu kódu a
  chybu API bez ztráty otázky. Testy používají pouze dočasná data.
- Živé OpenAI API na syntetickém kódu cislo=3/print(cislo+2) vysvětlilo výsledek
  5 a v navazující otázce změnu cislo=8 na výsledek 10. Žádná osobní data.
- Python 3.9 gramatika ověřena pro všech 47 Python souborů; běh na Pythonu 3.12.
- LocalSend: PythonSeSamanthou_1_4_20260906.zip, 79 souborů, 95 608 B,
  SHA-256 6e3c509d67377de4b43a9a2b7cec61f4310056283301c89639149654bd787fac.
- Plná projektová brána 1.4: všech 1518 testů prošlo (319,288 s).
- Rozbalený finální ZIP: všech 79 souborů přesně odpovídá zdrojům; všech
  51 testů, nové GUI AI a původní GUI dílny z distribuce prošly. Oba balíčky
  kurzů jsou byte-for-byte shodné s předchozím commitem.
- Po finální úpravě registru prošlo dalších 28 testů katalogu/registru a rychlá
  statická brána. Kontrola ZIPu nepotvrdila přítomnost používaného API klíče.


## 2026-09-06 15:37 CEST — Codex přes účet ChatGPT, verze 1.5

Hotovo:
- Míla odmítl potřebu samostatného účtování AI otázek přes API a výslovně zadal
  změnu na automatizované použití Codexu přihlášeného přes ChatGPT.
- Dílna volá codex exec na pozadí; vysvětlení, vedení i doptání zůstávají v okně.
  Původní HTTP API backend a pole pro klíč/model byly nahrazeny, žádný API fallback.
- Připojení AI má oficiální instalační návod, tlačítko Přihlásit přes ChatGPT
  (otevře browser flow) a Ověřit připojení. Přihlašování/kontrola neblokují editor.
- Vyžaduje Codex 0.153.0+ a ověřený ChatGPT login před každou otázkou. API/unknown
  login odmítne ještě před vynucením metody, takže kontrola neodhlásí API relaci.
  Proměnné API klíčů/provider override a rodičovské identity procesu nepřebírá.
- Tlačítko Zastavit a zavření dílny ukončí vlastní čekající procesovou skupinu.
  Chyba nezapíše částečnou odpověď jako úspěch, zachová otázku. Limity/přihlášení
  hlásí česky bez surových diagnostik, klíčů a tokenů.
- Historie je nadále samostatná pro každý pokus, omezená a do zavření dílny.
  Kód lze upravovat během čekání, pozdní odpověď je přiřazena původnímu pokusu.

Rozhodnuti:
Codex používá vlastní uložené přihlášení, dílna auth.json nečte ani nekopíruje.
Přihlášení je společné s Codexem na daném počítači. Využití podléhá limitům a
oprávnění účtu ChatGPT, není to slib neomezeného provozu zdarma.
Každá otázka startuje izolovaný dočasný pracovní adresář a předává zadání přes
stdin. Režim read-only; vypnuté shell/unified exec/code mode, multi-agent,
pluginy/apps/hooks, paměti a web. Bez osobní konfigurace modelu a historie
uživatele. --ephemeral a history.persistence=none; interní logy Codexu a
retence služby nejsou tímto prohlášeny za nulové. Výstup zpracovávají dočasné
soubory. Dílna neopakuje celé dotazy, Codex může interně obnovovat spojení.
Zastavení nevrací již spotřebovaný limit. Běžný dotaz nemění globální nastavení.

Dalsi krok:
Na Linuxu rozbalit jediný PythonSeSamanthou_1_5_20260906.zip. Nainstalovat
Codex podle Připojení AI a přihlásit se přes ChatGPT; poté ověřit připojení,
vysvětlení a doptání přímo v dílně. Nadále ověřit místní problém s editací,
který se na Macu nereprodukoval. Skrytou složku osobních dat zachovat.

Navrhovane dalsi kroky:
Po Linux retestu podle Míly přenos pokusů nebo skutečné krokování. Žádný nový
TVBCP, Cockpit proud či nasazení. Commit 1.4 00c16689 zůstal pouze lokální;
1.5 rovněž místní checkpoint, push vyžaduje nový pokyn.

Technicky dukaz:
- 56 cílených testů: transport přes stdin, absence API/provider proměnných,
  kontrola verze/loginu, odmítnutí API bez logoutu/spuštění, parsování JSONL,
  neúplný výsledek, limit/auth chyby, skutečné procesy a zastavení potomků.
- Čtyři Mac Tk GUI smoke; nový průvodce ověřuje připojení, psaní, doptání,
  oddělení historie, pozdní odpověď, chybu, zastavení a zachování otázky.
- Živé ChatGPT přihlášení na Macu: Codex vysvětlil syntetický příklad s výsledkem
  5 a doptání na výsledek 10. Skutečný Tk panel následně získal vysvětlení 4×2=8,
  kód se nezměnil. Bez osobních pokusů nebo přenosu autentizačních souborů.
- Python 3.9 gramatika ověřena, běh na 3.12; Linux zde přímo nespouštěn.
- LocalSend: PythonSeSamanthou_1_5_20260906.zip, 79 souborů, 98 949 B,
  SHA-256 d0a7d2b39d58e3fc97d5ccabbb4cf43146f308f28869ae60739519f08ee04f41.
- Plná projektová brána: všech 1518 testů prošlo (308,715 s). Rozbalená
  distribuce: 56 testů a GUI dílny/průvodce prošly; persistence a oba kurzy
  jsou byte-for-byte zachované. Finální README doplnilo sdílené přihlášení
  s místním Codexem; závěrečná kontrola všech 79 ZIP souborů porovnává aktuální zdroje.
- Po finálních úpravách prošla rychlá statická brána i všech 28 testů katalogu
  a registru. SHA-256 finálního ZIPu i shoda všech distribuovaných souborů ověřeny.
