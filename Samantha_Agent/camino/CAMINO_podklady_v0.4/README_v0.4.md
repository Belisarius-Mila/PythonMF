# Camino — podklady v0.4

**14. září 2026 · funkční specifikace, nikoli hotová aplikace.**

## Kde začít

Pro pohodlné čtení otevři [funkční specifikaci v HTML](CAMINO_funkcni_specifikace_v0.4.html). Je samostatná, nepotřebuje internet a obsahuje navigaci po kapitolách. Autoritativním podkladem pro úpravy a vývoj je [stejná specifikace v Markdownu](CAMINO_funkcni_specifikace_v0.4.md).

Návrh obsahuje 15 obrazovek, 73 funkčních pravidel a 80 akceptačních scénářů. Potvrzená rozhodnutí Míly U01–U11 jsou oddělená od nových návrhových rozhodnutí D01–D10. Nejde o nové kolo uživatelského dotazníku.

## Soubory

| Soubor | Účel |
|---|---|
| [Funkční specifikace](CAMINO_funkcni_specifikace_v0.4.md) · [HTML](CAMINO_funkcni_specifikace_v0.4.html) | Obrazovky, akce, chyby, data, soukromí, server, AI, deník a pozdější film. |
| [Akceptační scénáře](CAMINO_akceptacni_testy_v0.4.md) · [HTML](CAMINO_akceptacni_testy_v0.4.html) | T001–T080; všechny NEPROVEDENO. Definice testů, ne potvrzení funkčnosti. |
| [Plán pro Codex](CAMINO_Codex_v0.4.md) · [HTML](CAMINO_Codex_v0.4.html) | Malé postupné úlohy; první zadání C00 je rozepsané k vložení. |
| [AGENTS.md](AGENTS.md) | Krátká pravidla projektu pro Codex. Při založení projektu umístit do kořene repozitáře. |
| [Změnový list](CAMINO_zmeny_v0.4.md) · [HTML](CAMINO_zmeny_v0.4.html) | Co se konkretizovalo proti v0.3 a co ještě vyžaduje technickou zkoušku. |
| [Kontrola dokumentů](KONTROLA_PODKLADU_v0.4.json) | Počty, návaznost identifikátorů a kontrolní součty historických souborů; nejde o testy aplikace. |
| [Manifest souborů](MANIFEST_SHA256.json) | Kontrolní součty obsahu balíčku; manifest sám není součástí svého seznamu. |
| `historie/` | Nezměněné dřívější návrhy v0.2 a v0.3. |

## Předání Codexu

Předat aktuální dokumenty, začít souborem `AGENTS.md` a úkolem C00 v plánu. Žádný pokyn vyvinout celý systém najednou. První krok je read-only audit prostředí; první kódový experiment potom samostatné bezpečné audio na skutečném telefonu. Kontrakty API a migrace přijdou po úvodních experimentech, nejsou v tomto balíčku předstírané jako hotové.

Historie slouží pro porovnání. V případě rozporu je aktuální v0.4. Cílový domácí Mac není automaticky totožný s dříve zmiňovaným Intel MacBookem. Konkrétní verze systémů, instalace na iPhone, mikrofon a zálohovací úložiště zatím nebyly v této práci prakticky ověřeny.

## Co znamená hotový podklad

Dokumenty byly vytvořeny a jejich vnitřní identifikátory a soubory zkontrolovány. Aplikace tím nevznikla, na Mílově telefonu ani Macu neběžely uvedené testy a nebyla provedena žádná platba ani externí zpracování jeho médií. Číselný AI rozpočet zbývá stanovit před zapnutím placeného pilotu, nikoli před přípravou kódu.
