# Codex remote approval notice

Toto pravidlo resi prakticky problem pri praci z iPhonu nebo pres SSH: Codex muze
cekat na systemove potvrzeni tool callu v Codex UI/terminalu nebo na presnou
textovou potvrzovaci vetu pro rizikovy workflow krok, ale Mila to nemusi videt
v Cockpitu.

## Cil

Kdykoliv Codex predpoklada, ze bude zadat systemove povoleni pro prikaz nebo tool
call, ma pred tim zapsat viditelny runtime stav do Cockpitu. Cockpit pak v
dashboardu a v sekci `Hlas` ukaze kartu `Codex čeká na potvrzení`.

Toto pravidlo neznamena, ze Cockpit umi systemove povoleni zmacknout. Umi ale
spolehlive ukazat, ze prace stoji na potvrzeni, a od 2026-06-28 umi volitelne
zobrazit presnou textovou potvrzovaci vetu, kterou lze z Cockpitu poslat zpet
Adamovi/Codexu pres hlasovy textovy bridge. Karta musi byt psana pro Milu, ne
pro vyvojare: co chce Codex udelat, proc, jake je riziko a co ma Mila ted
udelat.

## Runtime soubor

Soukromy runtime stav je mimo git:

```text
data/private/voice_inbox/codex_approval_request.json
```

Do gitu ani memory se nema ukladat obsah citlivych prikazu, tokeny, hesla nebo
cele soukrome texty. Do karty patri jen kratky bezpecny popis.

## Prikazy

Pred ocekavanym systemovym potvrzenim:

```bash
.venv/bin/python scripts/codex_approval_notice.py set \
  --reason "Codex bude žádat systémové povolení." \
  --command "Stručný bezpečný popis akce." \
  --risk "Read-only kontrola mimo sandbox; nic se nema menit." \
  --next-step "Otevři aktivní Codex relaci a rozhodni systémové potvrzení."
```

Pokud jde o textovou potvrzovaci vetu, kterou ma jit poslat z Cockpitu, iPhonu
nebo SSH, pridej:

```bash
  --confirmation-text "Potvrzuji presne zneni konkretni akce."
```

Policka v Cockpitu:

- `Co chci udelat` vychazi z `--command`.
- `Proc` vychazi z `--reason`.
- `Riziko` vychazi z `--risk`.
- `Co ma Mila udelat` vychazi z `--next-step`.
- `Přesná potvrzovací věta` vychazi z `--confirmation-text`, pokud je vyplnena.

Neposilej do techto poli cele prikazy s tokeny, tajemstvi, cele osobni udaje ani
dlouhe citlive texty. Kdyz je prikaz citlivy, popis jen kategorii akce.

Po dokonceni nebo zruseni:

```bash
.venv/bin/python scripts/codex_approval_notice.py clear \
  --note "Systémové potvrzení je vyřešené."
```

## Kdy pouzit

Pouzij pred:

- prikazem spoustenym s Codex `require_escalated`,
- systemovou diagnostikou mimo sandbox, napriklad `ps`,
- prikazem, ktery typicky vyvola dotaz na povoleni,
- workflow krokem, ktery ceka na presnou textovou potvrzovaci vetu pro
  odeslani, mazani, presun, tisk, cteni citliveho obsahu nebo zapis do
  soukromych dat,
- delsim vzdalenym ukolem, kde Mila nemusi byt u Macu a mohl by cekat bez
  informace, proc prace stoji.

Nepouzivej pro bezne read-only prikazy, ktere necekaji na povoleni ani na
textovou potvrzovaci vetu.

## Minimalni postup Codexu

1. Nejdrive spust `codex_approval_notice.py set` s kratkym duvodem.
2. Teprve potom pozadej o systemove povoleni nebo spust prikaz, ktery ho vyvola.
3. Po vysledku vzdy spust `codex_approval_notice.py clear`.
4. Pokud se prikaz nepovoli nebo selze, kartu take vycisti s poznamkou.

## Stav

MVP je hotove k 2026-06-12, rozsirené k 2026-06-28:

- runtime stav se uklada a cte,
- `/api/status` ho vraci v `voice_mode.codex_approval`,
- Cockpit dashboard a sekce `Hlas` kartu zobrazuji,
- karta umi zobrazit a zkopirovat presnou potvrzovaci vetu,
- karta umi odeslat presnou potvrzovaci vetu Adamovi pres existujici `/api/speech/voice-text`,
- lokalni i Tailscale Cockpit byly live otestovane,
- skutecne vzdalené zmacknuti interniho Codex potvrzeni zatim hotove neni.
