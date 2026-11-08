# REC-06 — offline protokol zdrojových odkazů

2026-11-07, Data, vlastní worktree `data/parallel-20261104`.

## Výsledek a hranice

Implementován izolovaný protokol pro inspect i synthesis. Model vybírá ID
zdroje a řádku, program vrací přesný text ze zmrazeného zdroje. Nemění se
produkční klient, runtime, role, služby ani původní validátor kvality.
REC-06 zůstává otevřená; nový formát dosud neprošel skutečným modelovým tahem.

Tento krok neprovedl žádné SDK/modelové volání. Původní uzavřený pilot a jeho
raw účtenky zůstaly beze změny. Dva původní jedinečné tahy mají dříve doložený
odhad 21,013 Standard kreditu; žádná nová cena se k nim nepřičítá. Nevznikl
nový celý návod, zápis TXT/iCloud, týdenní aktivace, push ani nasazení.

## Kontrakt

- `recovery_guide_anchors.py`: neměnný katalog úplných textů. Krátká ID jsou
  lokální pro SHA katalogu; vazba zahrnuje cestu, SHA celého zdroje, znakový
  rozsah a SHA úseku. Řádky mají dvojice `[anchor_id, celý původní řádek]`.
  Prázdné řádky zůstávají ve vstupu s null ID. Žádné zkracování celého textu.
  Citace zachová velikost písmen, odsazení a koncové mezery; odstraní pouze
  koncové CR/LF. Neznámý, prázdný či cizí odkaz se odmítne.
- `recovery_guide_anchor_protocol.py`: immutable request váže celý payload,
  schema, rozsah a katalog. Inspect vyžaduje právě všechny dokumenty v dávce
  v pevných klíčích `covered`; original do coverage nepatří. Model nedodává
  pole quote. Resolver vytvoří starý kontrakt `{source, quote}` a ponechá
  původní doslovnou kontrolu.
- Syntéza vyžaduje každou dokumentaci právě jednou. Dostane celý original,
  zjištění a přesné vybrané úseky. Nedostává celou historii dialogu.
  Odkazy dokumentace musí pocházet z předaného evidence poolu, original lze
  citovat celý. Doručený text/status se nepřepisuje; výsledek znovu prochází
  nezměněným `recovery_guide_quality.validate` včetně příkazů a historických
  tvrzení. Neúplné čtení nesmí vytvořit syntézu.
- `recovery_guide_anchor_audit.py`: čtecí audit konkrétního historického
  packetu a dvou raw účtenek ve vlastní .venv. Vytváří pouze explicitní
  offline fixture ID. Dvě kapitalizace mapuje jen podle již přezkoumaných
  konkrétních návrhů ve full_result JSON; obecná normalizace/fuzzy match není.
  Staré notes nejsou znovu přijaty a žádný controller/attempt se nezapisuje.

ID a hashe dokazují identitu zdrojového textu, nikoli oprávnění ke spuštění
ani věcnou správnost modelového závěru. Živý stav Macu/iPhonu a aplikační
nastavení zůstávají samostatnou doloženou přejímkou.

## Ověření

- 24 nových cílených testů OK: Unicode/CRLF/mezery, neměnnost, podvržení
  payloadu a schématu, neznámé/cizí odkazy, úplnost, duplicitní JSON,
  odmítnutí neschváleného příkazu a vydávání historie za současnost.
- Plná projektová brána OK: 2 642 testů, 5 skipped (620,921 s testů).
  Finální statická brána a `git diff --check` také OK.
- `recovery_guide_anchors_offline_20261107.json`: historický v2 snapshot,
  530 dokumentů + celý original, 6 290 890 zdrojových UTF-8 bytů,
  81 612 neprázdných anchorů. Všech 14 čtecích requestů sestaveno, každý
  dokument právě jednou; zpětné složení textů je přesné.
- Dvě uložené odpovědi poskytly fixture pro 101 dokumentů; všechny vyřešené
  citace přesné včetně obou kapitalizačních regresí. **Fixture není nový
  modelový výstup ani dodatečné přijetí starého běhu.** Syntéza z těchto
  neúplných 101/530 dokumentů byla odmítnuta. Raw účtenky a oba staré stavové
  soubory mají po auditu stejné hashe.

## Režie a nepodporované vlastnosti

První dávka: starý payload 598 940 B, anchor payload 678 005 B + schema
3 283 B. Druhá: 584 211 B proti 687 691 B + schema 5 284 B. Všech 14 nových
inspect payloadů má dohromady 8 742 382 B a schémata 47 756 B. Nejde o počet
tokenů ani cenovou kartu a nezahrnuje budoucí syntézu či transportní obálku.
Původní dělení dávek/limit nelze bez přepočtu převzít.

Podporovaný rozsah: nejvýše 996 zdrojových ID v jednom schématu včetně
original; neprázdné fyzické úseky po řádcích; nejvýše 16 odkazů na zjištění
či odstavec, 100 zjištění/dávku a 1 024 odstavců syntézy. Prázdný nebo čistě
mezerový zdroj není podporován a zastaví katalog. Trusted request má limit
256 MB, raw odpověď 4 MB. Celý velmi dlouhý řádek může vytvořit velkou citaci;
zatím není samostatný cenový/context planner ani limit délky jednotlivé citace.

Živý SDK adapter, nové cenové/context posouzení a modelová kompatibilita
nového schématu zatím nejsou implementované/ověřené. Oficiální dokumentace
uvádí podporu pevných required klíčů, `$defs`/`$ref`, enum, pattern a mezí
array: [Structured Outputs — Supported schemas](https://developers.openai.com/api/docs/guides/structured-outputs#supported-schemas).
To samo nedokazuje přijetí připojeným Codex App Serverem ani správnou volbu
zdrojového úseku modelem. Snapshot je historicky připnutý, není živým auditem
nastavení ani dnešního main. Žádná automatická migrace role či aktivace.

## Přesný další integrační krok pro Willa

1. Přezkoumat tento izolovaný diff a převzít jen pilot/testy/registraci/zápisy;
   zachovat souběžnou kalendářovou práci. Stávající uzavřený v2 job neobnovovat.
2. V novém samostatném `app/recovery_guide_anchor_trial.py` připravit nejprve
   neplacenou kartu: nový trial ID; aktuální schválený manifest; katalog SHA,
   request SHA, přesné schéma/payload, kód/transport/peer a centrální kandidát
   role; přepočet úplných vstupů, výstupní rezervy a syntézy včetně nové režie.
   Izolovaný tokenizer je referenční odhad, nikoli garantované Sol účtování.
3. Teprve konkrétní novou kartu předložit k samostatnému přijetí malé živé
   zkoušky. Adapter zachová existující sdílený socket, Standard per-turn,
   trvalý marker před odesláním, kontrolu čerstvosti a známé účtenky; při
   nejistotě žádný další create/turn. Neměnit produkční klient ani role JSON.
4. Po malé živé přejímce zvlášť nacenit celý korpus. Až přijatý celý kandidát
   otevře Mac/iPhone dossier, dvě cílové TXT kopie a pozdější týdenní aktivaci.

Souhlas s tímto offline vývojem nespouští ani neschvaluje novou placenou kartu.

## Změněné soubory tohoto kroku

- app/recovery_guide_anchors.py
- app/recovery_guide_anchor_protocol.py
- app/recovery_guide_anchor_audit.py
- tests/test_recovery_guide_anchors.py
- tests/test_recovery_guide_anchor_audit.py
- scripts/cockpit_quality_gate.py
- memory/reports/recovery_guide_anchors_20261107.md
- memory/reports/recovery_guide_anchors_offline_20261107.json
- memory/technical/capability_routing_rules.md
- memory/technical/recovery_guide_maintainer.md
- memory/projects/samantha_external_backup.md
- memory/handoffs/workstreams/project-samantha-infrastructure.md
- memory/tvbcp/workstreams/project-samantha-infrastructure.md
- memory/ACTIVE_PROJECTS.md
- memory/MEMORY_INDEX.md
- memory/LESSONS_LEARNED.md
