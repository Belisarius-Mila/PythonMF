# Znalostní databáze / Knihovna článků

## Cíl

Projekt slouží jako širší osobní znalostní databáze. První hotový vstup je
Knihovna článků v Cockpitu; původní vědecké články zůstávají jednou kategorií
uvnitř této oblasti.

Směr potvrzený 2026-06-11:

- `Knihovna článků / web article archive` a `Knowledge inbox / živá znalostní
  databáze` patří k sobě;
- Knihovna článků je první funkční MVP vstup pro URL a webové texty;
- Knowledge inbox je širší bezpečný intake pro velké podklady, chat exporty a
  soubory, které se mají nejdřív read-only zanalyzovat a až po potvrzení
  rozdělit do tematických knowledge karet.

Vědecká část slouží jako lokální knihovna průlomových nebo jinak důležitých
vědeckých článků z různých oborů.

Ukládat se sem mohou:

- PDF článků,
- odkazy na články,
- obrázky, grafy a screenshoty,
- česká shrnutí,
- poznámky Míly,
- důvody, proč je článek důležitý nebo průlomový.

## Umístění dat

Hlavní složka:

```text
data/vedecke_clanky/
```

Praktické webové články, které mohou časem zmizet z internetu, se ukládají jako
soukromý fulltextový archiv mimo git:

```text
data/private/article_archive/
```

Velké podklady a exporty pro budoucí znalostní databázi se ukládají mimo git do:

```text
data/private/knowledge_inbox/
```

Základní soubory a složky:

```text
data/vedecke_clanky/README.md
data/vedecke_clanky/registry.csv
data/vedecke_clanky/inbox/
data/vedecke_clanky/articles/
data/vedecke_clanky/images/
data/vedecke_clanky/links/
data/vedecke_clanky/notes/
data/vedecke_clanky/exports/
```

## Evidence

Hlavní evidence je:

```text
data/vedecke_clanky/registry.csv
```

Každý článek nebo odkaz má mít jeden řádek v `registry.csv`.

Důležité položky:

- ID,
- název,
- obor,
- rok,
- autoři,
- DOI,
- URL,
- lokální soubor,
- obrázky,
- krátké české shrnutí,
- důvod významnosti,
- stav,
- tagy,
- datum přidání,
- informace, zda bylo provedeno internetové doplnění.

## Pravidlo pro internet

Při každém ukládání nových dat se vždy nejdřív zeptat:

```text
Chceš, abych k tomu hledal na internetu doplňující informace?
```

Bez výslovného potvrzení internet nepoužívat.

Pokud Míla hledání povolí, lze doplnit:

- DOI,
- autory,
- rok publikace,
- časopis nebo konferenci,
- oficiální stránku článku,
- abstrakt,
- související práce,
- popularizační vysvětlení,
- praktický význam objevu.

## Doporučený postup

1. Uložit dodaný soubor do `inbox/`, nebo odkaz do `links/`.
2. Zeptat se na internetové doplnění.
3. Přidat řádek do `registry.csv`.
4. Pro důležité články vytvořit poznámku podle `notes/TEMPLATE.md`.
5. Roztřídit PDF/text do `articles/` a obrázky do `images/`.
6. V poznámce držet hlavně české shrnutí a praktický význam článku.

## Stav

Projekt byl založen 2026-05-18.

2026-06-10 byl doplněn lehký soukromý archiv webových článků:

- `scripts/archive_article_url.py` uloží URL, zdrojové HTML, prostý text a metadata.
- `scripts/search_article_archive.py` hledá ve fulltextu uložených článků.
- `scripts/read_article_archive.py` zkusí živou URL a při nedostupnosti použije lokální TXT fallback.
- Cockpit má read-only okno `Knihovna` se záložkami `Recepty`, `Vědecké články`,
  `Samantha / AI nástroje`, `Ostatní`, seznamem od nejnovějších položek a
  fulltextovým hledáním ve vybrané kategorii.
- Vstup přes Cockpit: do okna `Knihovna` lze vložit URL, vybrat kategorii, doplnit
  volitelné tagy a uložit článek automaticky do soukromého archivu.

První uložený praktický článek je návod k lepení spárovky z Nářadí Praha. Plný
text i HTML jsou jen v `data/private/article_archive/` a nepatří do gitu.

2026-06-11 byla doplněna infrastruktura pro ručně vložený text bez URL:

- `app/article_archive.py` umí `archive_text_entry(...)` a ukládá položky se
  `source_type = manual_text`, `source_label`, `source_note`, kategorií a tagy.
- Cockpit `Knihovna` má vedle `Uložit URL` také vstup `Uložit text`.
- Ručně vložený recept nebo výstřižek se ukládá do stejného soukromého archivu
  a je dohledatelný stejným fulltextovým hledáním jako URL články.
- CLI fallback je `scripts/archive_text_entry.py`, použitelný pro TXT soubor od
  historické Samanthy/ChatGPT.
- Recepty bez URL mají být označené zdrojem typu například `ChatGPT historický
  chat` a poznámkou, že jde o vložený nebo syntetizovaný text bez původní URL.

2026-06-11 byl doplněn datový model pro přílohy znalostních karet:

- Každá položka v `data/private/article_archive/articles/<id>/metadata.json`
  může mít volitelné pole `attachments`.
- Příloha je relativní cesta pod soukromým archivem, typicky:
  `attachments/original/`, `attachments/readable/`, `attachments/thumbs/`.
- API Knihovny vrací u položek `attachment_count`, `attachment_types` a
  `attachment_roles`; detail položky vrací i seznam příloh.
- Cockpit umí přílohy v detailu zobrazit a servíruje je přes bezpečný lokální
  endpoint `/api/library/attachment`, ne přes absolutní cestu na disku.
- První cílové použití: ručně psané rodinné recepty, kde textová karta drží
  přepis a příloha drží čitelný scan/fotku rukopisu.
- Doporučené tagy pro tyto položky: `rodinny-recept`, `rucne-psany`, `scan`,
  `ma-obrazek`, případně `prepis-overit`.
- Doporučený `source_label`: `Rodinný ručně psaný recept`.

2026-06-11 byl doplněn i první zápisový průchod pro obrázkové přílohy:

- Backend funkce `attach_article_image(...)` připojí obrázek k existující kartě,
  uloží originál, vytvoří čitelnou JPEG kopii a thumbnail.
- CLI fallback je `scripts/attach_article_image.py`.
- Cockpit `Knihovna` má akci `Připojit obrázek`: nejdřív vybrat kartu v seznamu,
  potom vybrat lokální obrázek, případně doplnit popisek/tagy/poznámku a uložit.
- Při připojení přes Cockpit se automaticky přidávají tagy
  `rodinny-recept`, `rucne-psany`, `scan`, `ma-obrazek`, `prepis-overit`.
- Endpoint pro zápis je `/api/library/attachment/add`; pro čtení příloh zůstává
  `/api/library/attachment`.

2026-06-20 byla doplněna kategorie `Samantha / AI nástroje`:

- Interní klíč kategorie je `ai_tools`.
- Kategorie slouží pro čitelné články o Codexu, Agents SDK, OpenAI novinkách,
  Realtime/voice směru a budoucích schopnostech Samanthy.
- Nové funkcionality OpenAI se mají ukládat jako samostatné články s datem,
  praktickým významem pro Samanthu a poznámkou, že před implementací je nutné
  ověřit aktuální oficiální dokumentaci.
- První soukromé položky jsou `Codex Cookbook: praktická kuchařka pro práci s kódem`
  a `Agents SDK jako budoucí schopnosti Samanthy`.

2026-07-01 byla opravena archivace webových článků se starším českým kódováním:

- `app/article_archive.py` nově respektuje deklarované HTML kódování a fallbacky
  `utf-8`, `windows-1250`, `iso-8859-2`.
- Extrakce preferuje hlavní obsah v blocích jako `div#clanek`, `article` a
  `main`, aby se do textu nedostávaly navigace, reklamy a související bloky.
- Cockpit po uložení URL jasně otevře uloženou položku a ukáže status
  `Otevřeno: ...`, aby opakované uložení stejné URL nevypadalo jako nečinnost.
- Rozbité soukromé položky z testu GVT článku byly podle Milova pokynu
  odstraněny natvrdo mimo git; čistý záznam byl znovu uložen do soukromého
  archivu se správnou češtinou.
- Položka `Špagety ala carbonara` byla v soukromé knihovně přesunuta z
  `Ostatní` do `Recepty`.

Další krok:

1. Až Míla se Samanthou připraví první přepis ručně psaného receptu a fotku,
   uložit nejdřív jednu testovací kartu.
2. Připojit první reálnou fotku/skener přes Cockpit a ručně zkontrolovat
   čitelnost čitelné kopie i thumbnailu.
3. Podle výsledku doladit cílovou velikost/rozměr čitelné kopie pro rukopisy.
4. U většího balíku receptů udělat read-only rozbor: počet receptů, navržené
   názvy, kategorie, tagy a stav `prepis-overit`.
5. Až po potvrzení rozdělit balík na jednotlivé receptové karty.
