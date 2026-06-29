# Global safety brake

Tento soubor definuje uzkou globalni brzdu pro Samanthu/Codex. Cilem neni
omezovat beznou praci ani hlasovou komunikaci. Vychozi rezim ma byt prakticky:
bezne cteni, hledani, shrnovani, diagnostika, priprava navrhu, otevreni Cockpitu,
prace s read-only reporty a nizkorizikove kroky maji projit hladce.

Globalni brzda se pouziva jen pro akce, kde by chyba mohla znicit data, rozbit
prostredi, zverejnit tajemstvi nebo udelat tezko vratnou zmenu.

## Zasada

- Co neni vysoce rizikove, nema byt zbytecne blokovane.
- Běžné potvrzení typu `ano` staci pro bezne zmeny s jasnym rozsahem.
- Pro globalni brzdu nestaci obycejne `ano`; je potreba presna potvrzovaci veta.
- Zadna hesla ani tajne fraze se do projektu neukladaji. Potvrzovaci veta neni
  kryptograficke heslo, ale zamerna pauza pred nebezpecnym krokem.

## Presna potvrzovaci veta

Pro akce pod globalni brzdou si vyzadej presne:

```text
Potvrzuji globální brzdu: rozumím riziku a chci pokračovat.
```

Bez teto vety akci neprovadej. Pokud je pozadavek hlasovy nebo nepresny, nejdrive
ho preved na konkretni plan a nech Milu potvrdit textove.

## Akce pod globalni brzdou

Vyžaduj presnou potvrzovaci vetu pro:

- mazani nebo hromadne prepisovani cehokoli v `~/Desktop/PythonMF/`,
- mazani adresaru nebo mazani vice nez 5 souboru najednou,
- prikazy typu `rm -rf`, `find ... -delete`, hromadne `mv`/presuny mimo projekt,
- mazani nebo hromadne upravy v `Samantha_Agent/memory/` mimo bezne handoff/index
  aktualizace,
- mazani, hromadne upravy nebo presuny v `data/private/`, document vaultu,
  backup slozkach, rodinnych mediich a soukromych pracovnich datech,
- `git reset --hard`, force push, mazani vetvi nebo tagu, prepis historie,
- zveřejnění, výpis nebo commit tajemstvi: `.env`, API klice, tokeny, hesla,
  recovery klice, app-specific passwords,
- zmeny systemove konfigurace mimo projekt: shell profily, LaunchAgents,
  SSH konfigurace, Tailscale/VPN, sitova konfigurace, opravneni systemu,
- platby, odesilani SMS/e-mailu jmenem Mily/Jany nebo jine externi akce s dopadem
  mimo lokalni projekt, pokud nejde o predem potvrzeny nizkorizikovy workflow.

## Dalsi ochranna sit

I kdyz Mila napise rizikovy pokyn prirozene nebo hlasem, Codex ma porad pouzit
vlastni usudek. Napriklad pokyn `smaz dulezity soubor` nebo `pushni vsechno`
nesmi byt proveden automaticky. Nejdrive je potreba zkontrolovat rozsah, vysvetlit
dopad a vyzadat odpovidajici potvrzeni.

## Technicky guard ve full-access rezimu

Od 2026-06-29 existuje doplnkova technicka brzda pro nove relace spoustene pres
`samantha`:

```text
scripts/destructive_command_guard.py
scripts/safe_bin/rm
scripts/safe_bin/git
scripts/safe_bin/find
scripts/safe_bin/mv
```

`scripts/samantha_screen_entry.sh` pridava `scripts/safe_bin/` na zacatek `PATH`,
takze bezne prikazy `rm`, `git`, `find` a `mv` jdou nejdrive pres guard.
Guard blokuje hlavne:

- mazani v `PythonMF`,
- `rm -rf` a hromadne mazani,
- `find ... -delete` a `find ... -exec rm`,
- `git reset --hard`, `git clean`, force push a mazani git vetvi/tagu,
- hromadne presuny a presuny private/memory/autosave dat.

Pro vedome obejiti vyzaduje stejnou presnou vetu v promenne prostredi:

```bash
SAMANTHA_DESTRUCTIVE_CONFIRMATION="Potvrzuji globální brzdu: rozumím riziku a chci pokračovat."
```

Limit: absolutni cesty jako `/bin/rm` nebo `/usr/bin/git` wrapper obejdou. To ma
byt brano jako vedome rizikove obejiti a porad podlega pravidlum globalni brzdy.
Stavajici uz bezici Codex relace nemusi mit novy `PATH`; plne zapojeni plati po
novem startu pres `samantha`.

## Poznamka pro hlasovy rezim

Hlasovy rezim ma zustat pouzitelny. Hledani, cteni, shrnovani, diagnostika,
otevreni aplikaci, priprava odpovedi, read-only dotazy a bezpecne reporty se
nemaji zasekavat na teto brzde. Brzda patri jen na skutecne rizikove operace.
