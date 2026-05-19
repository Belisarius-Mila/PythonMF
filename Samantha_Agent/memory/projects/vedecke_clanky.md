# Vědecké články

## Cíl

Projekt slouží jako lokální knihovna průlomových nebo jinak důležitých vědeckých článků z různých oborů.

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

Zatím nejsou uložené konkrétní články.
