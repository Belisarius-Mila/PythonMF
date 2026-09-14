# Camino — plán postupného vývoje pro Codex v0.3

**Navazuje na:** `CAMINO_navrh_v0.3.md`  
**Stav:** plán práce, nikoli implementované funkce. Uživatelské volby U01–U11 jsou převzaté z návrhu. První proveditelný úkol C00 je rozepsaný níže; další etapy se mají před provedením rozdělit na jednotlivé malé úkoly podle zjištěného prostředí.

## 1. Pravidla společná pro všechny úkoly

Pracuj vždy pouze na aktuálně zadaném úkolu. Neimplementuj veřejný web, více autorů, hodinkovou aplikaci, průběžné GPS nebo videoeditor jako nevyžádané rozšíření.

Originály jsou neměnné. Žádné automatické mazání. Každá uživatelská a AI úprava má vlastní revizi. Výpadek sítě, AI či serveru neblokuje lokální zachytávání.

„Jen pro mě“ zakazuje sdílené výstupy a film, ale nezakazuje přepis a korekturu externí AI. Běžný záznam není zveřejněný. Rodinný výstup a film smějí používat jen povolené zdroje, nikoli kompletní soukromý souhrn. Výběr zdrojů vynucuje program, nikoli pouze prompt modelu.

Vývoj a automatické testy používají syntetická data a mock AI. Žádný test nesmí bez výslovného provozního nastavení vyvolat placené API. Klíče a osobní média nepatří do repozitáře, screenshotů ani logů. Souhlas s AI obsahem není rozpočet bez omezení.

Nedestruktivní technické detaily zjisti ze skutečného prostředí. Nevyžaduj od Míly volbu frameworku, databáze nebo přenosového protokolu. Nedostupné údaje označ NEOVĚŘENO. Nevydávej test na simulátoru za zkoušku skutečného mikrofonu, zámku nebo mobilní sítě.

Výstup každého úkolu: co se změnilo, změněné soubory, příkazy skutečně spuštěných testů, jejich výsledky, zbývající manuální testy a omezení. Samotný úspěšný build neprokazuje funkčnost na cestě.

## 2. Doporučené uspořádání budoucího repozitáře

```text
camino/
  AGENTS.md
  README.md
  docs/
    PRODUCT_SPEC.md
    DECISIONS.md
    ENVIRONMENT_AUDIT.md
    ARCHITECTURE.md
    DATA_MODEL.md
    ACCEPTANCE_TESTS.md
    OPERATIONS.md
    PRIVACY.md
  contracts/
  ios/
  server/
  tests/
  tasks/
```

Nezakládej hned prázdné modulární systémy pro vše, co bude až později. Výše je organizační cíl, ne povinnost napsat všechno v první iteraci. Při založení repozitáře se tato v0.3 převede na produktovou specifikaci a oddělí se uživatelská rozhodnutí od technických.

Projektový `AGENTS.md` má být krátký a obsahovat společná pravidla, orientaci v dokumentech a způsob testování. Úplnou dlouhou specifikaci do něj nekopírovat. Podporu a způsob načítání tohoto souboru popisuje OpenAI: `https://developers.openai.com/codex/guides/agents-md/`.

## 3. Etapy a menší pracovní úkoly

| Etapa | Samostatné pracovní části | Kdy je hotová |
|---|---|---|
| C00 — audit | Inventář prostředí; kompatibilita a podpis; server a zálohy | Existuje doložená nebo výslovně neověřená cesta ke každé potřebné schopnosti. |
| C01 — audio experiment | Minimální lokální nahrávka; zámek a mikrofon; segmenty a přerušení | A02–A05 na skutečném telefonu; nepředstírat ověření bez hardware. |
| C02 — přenosový experiment | Lokální přijímač testovacího souboru; Tailscale HTTPS; cizí síť | Stejný testovací soubor a kontrolní součet na obou stranách, žádná veřejná služba. |
| C03 — kontrakty | Objekty a revize; soukromí; API příklady; lokální evidence | Testovatelné příklady a žádné nejasné vlastnictví data. |
| C04 — offline klient | Obrazovka a Moment; audio; foto; video; import; nouzový export | Každá část má vlastní test obnovy; řádně uložený záznam přežije restart. |
| C05 — synchronizace | Serverové uploady; iOS fronta; části a finalizace; obnova; stav UI | A07–A10, nesprávná data neprojdou a opakování je bezpečné. |
| C06 — provoz | Spuštění služeb; zálohovací snapshot; ověření kopií; obnova; stavová stránka | A20 a reálný restart v zabezpečené konfiguraci. |
| C07 — AI | Rozhraní a mock; skutečný pilot po rozpočtu; přepis; korektura; revize; omezení nákladů | A11–A14 a A19, žádný zásah do archivace. |
| C08 — deník | HTML/Markdown šablona; souhrn a verze; pozdní vstupy; nenáročná oprava | A12–A13 a automatické sestavení bez „uzavření dne“. |
| C09 — terénní validace | Realistický den; slabá síť; baterie/objem; chyby; release checklist | Všechna nutná zařízení a problematické scénáře mají výsledek, ne jen odhad. |
| C10 — volitelné sdílení | Povolené zdroje; nezávislý souhrn; vyčištěné kopie; náhled; systémové sdílení | A15–A18, A21 a A24. Bez těchto zkoušek funkci nezpřístupnit. |
| C11 — po návratu | Hodinkový export; filmový datový model; výběr a vlastní hlas; titulky; render | A15, A23 a A25; zdroje ověřené, soukromé položky vyloučené. |

Identifikátory Axx odkazují do hlavního návrhu v0.3. Jednotlivé pracovní části tabulky jsou zamýšleny jako samostatná zadání, nikoli jeden obří požadavek na celou etapu.

## 4. První zadání C00 — technický audit a proveditelnost instalace

### Cíl

Zjistit, jak na dostupném vybavení bezpečně vyvíjet a nainstalovat nativní iPhone aplikaci a provozovat soukromý Mac backend. Nevytvářet ještě plnou aplikaci ani neprovádět nákupy.

### Známé skutečnosti

Cílový uživatel má podle dosavadního kontextu iPhone 14 a Intel MacBook Pro s macOS Sequoia 15.7.7. Aktuální verze na stroji se může lišit a musí se zjistit přímo. Tento notebook není automaticky domácí server. Server v ČR má být Mac, přístup z telefonu přes Tailscale. Rodinný web není potřeba. Míla akceptoval případný roční poplatek Apple; nepožádal o nákup. AI rozpočet není určen a tento úkol API vůbec nepoužívá.

### Povolený rozsah

Prostuduj hlavní návrh v0.3 a stav případného existujícího repozitáře. V dostupném prostředí proveď jen bezpečný read-only inventář. Zapiš, na jakém stroji se audit skutečně provádí a zda je to vývojový Mac nebo jiné prostředí. V Linuxovém či vzdáleném prostředí nevyvozuj stav Mílova Macu.

Zjisti verzi systému, architekturu, dostupnost Xcode, SDK a podpory připojeného zařízení. Příklady vhodných příkazů na Macu jsou `sw_vers`, `uname -m`, `xcodebuild -version` a `xcrun --sdk iphoneos --show-sdk-version`; spouštěj je pouze tam, kde dávají smysl. Nepřepisuj osobní identifikátory, sériová čísla, tokeny nebo celý síťový profil do veřejného dokumentu.

Ověř aktuální oficiální požadavky Apple. Vyber nejjednodušší podporovanou cestu instalace vlastní aplikace na registrovaný iPhone s platností přes cestu. Zjisti, co je doložené a co vyžaduje pozdější připojení zařízení nebo dokončení vývojářského účtu. Nepovažuj App Store či TestFlight za povinnost.

Pokud je autorizovaný přístup k domácímu serveru skutečně dostupný, zkontroluj jeho systém, napájení/uspávání, dostupnost cílových disků a existenci zálohy. Bez takového přístupu zapiš server jako NEOVĚŘENO, nevymýšlej hostnames ani přihlašovací údaje. Zvaž Tailscale Serve jako privátní reverse proxy, ale v tomto úkolu nic veřejně nezpřístupňuj.

### Neprovádět

Žádné aktualizace systému, instalace velkých nástrojů, mazání, migrace úložiště, nákup členství, změny FileVault, trvalé vypínání zabezpečení, veřejné porty nebo Funnel. Žádné tajné klíče a reálná média. Žádné prohlášení o hotové iOS kompatibilitě jen podle tabulky, pokud nebyl sestaven a spuštěn ani malý test.

### Výstupy

`docs/ENVIRONMENT_AUDIT.md`: každá položka má stav OVĚŘENO / NEOVĚŘENO / BLOKUJE, důkaz nebo způsob zjištění a dopad. Odděl vývojový Mac, iPhone a domácí server.

`docs/DECISIONS.md`: doporučená kombinace nástrojů, cesta podpisu a instalace, předběžný provoz serveru. Vysvětli důvody stručně; nerozšiřuj rozsah aplikace.

`tasks/C01_AUDIO_PROTOTYPE.md`: konkrétní malé zadání prvního audio prototypu na základě výsledku auditu. Obsahuje zámek obrazovky, skutečný mikrofon, přerušení, přehrání a obnovu. Pokud hardware zatím není dostupný, explicitně odděl proveditelné přípravné kroky od budoucích manuálních zkoušek.

### Podmínka předání

Míla dostane srozumitelný výsledek: co je připravené, zda existuje konkrétní skutečný blok a jaký je následující malý krok. Nevypisuj mu nový dotazník o již rozhodnutých produktových variantách. Chybějící přístup k zařízení není důvod označit celý projekt za nemožný; znamená pouze neověřenou část auditu.

## 5. Šablona každého dalšího zadání

```text
ID a název:
Cíl:
Předpoklady a vstupní dokumenty:
Co implementovat:
Co v tomto úkolu nedělat:
Chování při chybě:
Ochrana originálů a soukromí:
Automatické testy:
Manuální testy na zařízení:
Výstupní soubory a dokumentace:
Podmínka dokončení:
```

V dalších kolech se nejprve uzavře C00 a audio/síťové experimenty. Kompletní API kontrakt a produkční struktura se připraví na základě těchto výsledků. Tím se zabrání tomu, aby se před hlavními platformními zkouškami napsal velký objem kódu postavený na neověřeném předpokladu.
