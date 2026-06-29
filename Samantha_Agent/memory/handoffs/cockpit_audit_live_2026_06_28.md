Nazev: Cockpit audit - live handoff 2026-06-28
Priorita: 1
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-28

Co se resilo:
- Navazalo se na systemovy audit Cockpitu po problemech s VoiceBridge, potvrzovacimi kartami a dokumentovym panelem.
- Cilem je prubezne testovat a uklizet Cockpit tak, aby realne denni workflow nebylo matouci a aby nove zmeny nerozbily existujici funkcionality.
- Tento soubor je zivy handoff pro aktualni audit; ma se prubezne aktualizovat po vetsich opravach nebo pri preruseni prace.

Co je hotove:
- Cockpit exact confirmation karta je hotova a pushnuta: karta `Codex ceka na potvrzeni` umi zobrazit presnou potvrzovaci vetu, kopirovat ji a odeslat ji Adamovi pres textovy hlasovy bridge.
- Test potvrzovaci karty pro e-mail probehl bez odeslani e-mailu; potvrzovaci veta dorazila z Cockpitu jako hlasovy/textovy pokyn.
- Dokumenty k revizi:
  - report zobrazuje konkretni dokumenty, akce `Otevrit / cist` a stav cteni;
  - Cockpit ctecka umi zobrazit PDF i obrazkove dokumenty z vaultu;
  - ScanDocu Review umi najit ulozene JPEG prilohy k revizi a zobrazuje obrazkovy nahled inline;
  - po ulozeni revize se rucne potvrzene obrazky bez textove vrstvy uz nevraci do reportu jako `zero_text`;
  - karta `Dokumenty k revizi` pred nactenim ukazuje `?`, ne falesnou `0`, a tlacitko ma text `Nacti report`.
- Dokumentovy panel Cockpitu byl ergonomicky prerazen:
  - levy sloupec: nova PDF, dokumentovy intake, terminy;
  - prostredni sloupec: ulozene dokumenty k revizi, dokumenty k revizi, souvisejici dokumenty;
  - pravy sloupec: problemy, klasifikace.
- Cockpit a ScanDocu byly po opravach restartovane a overene lokalnimi HTTP kontrolami.
- Vsechny souvisejici zmeny byly testovane (`tests.test_cockpit`, podle potreby `tests.test_document_vault_tools`) a pushnute na `main`.
- 2026-06-29 VoiceBridge/Codex session diagnostika:
  - zjisteno, ze dlouho bezici `screen` relace muze byt ziva a pritom ji sandboxovane `ps`/PID overeni neumi potvrdit;
  - `adam_voice_bridge_status` uz v takovem pripade nehlasi zavadejici `Codex relace: 0`, ale pouzije oznaceny marker jako neovereny fallback, pokud bezi `screen` a marker ma ulozeny `parent_pid`;
  - mrtvy marker bez ziveho nebo aspon neoveritelneho screen kontextu zustava nepripraveny.

Co neni hotove:
- Audit Cockpitu jako celek neni uzavreny; zatim probehly hlavne VoiceBridge/potvrzovaci karta a dokumentovy panel.
- Nejsou kompletne projite vsechny Cockpit plochy a tlacitka z pohledu Mac/iPhone/SSH.
- Neni hotovy samostatny finalni auditni report po rucnych testech.
- Neni rozhodnuto, zda `Dokumenty k revizi` ma report nacitat automaticky, nebo zustat rucni kvuli rychlosti hlavniho refreshu.
- Po oprave VoiceBridge fallbacku je potreba restartovat Cockpit a rucne overit Mac/iPhone hlasovy pokyn do teto dlouho bezici `screen` relace.

Dalsi krok:
- Pokracovat rucnim auditem Cockpitu po blocich: nejdrive dokumenty a ScanDocu po realnem provozu, potom VoiceBridge/potvrzovaci karty, potom e-mail/Work Queue a nakonec servis/diagnostika.

Navrhovane dalsi kroky:
- Pri kazdem dalsim bloku drzet rytmus: rucni test -> konkretni nalez -> mala oprava -> test -> commit/push -> aktualizace tohoto handoffu.
- Pro kazdou matoucí kartu nebo tlacitko zapsat, jestli je problem text, vychozi stav, poradi, nebo backendova logika.
- Po dokonceni rucniho kola vytvorit kratky finalni report `memory/reports/cockpit_live_audit_2026_06_28.md` nebo novejsi datum.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/documents/scandocu.py`
- `tests/test_cockpit.py`
- `tests/test_document_vault_tools.py`
- `memory/reports/cockpit_function_inventory_audit_2026_06_27.md`
- `memory/reports/cockpit_post_action_risk_matrix_2026_06_27.md`
- `memory/handoffs/cockpit_remote_exact_confirmation_cards_2026_06_27.md`

Bezpecnost / neukladat:
- Do handoffu neukladat obsah soukromych dokumentu, e-mailu, priloh ani identifikatory, ktere nejsou nutne pro git-safe navazani.
- Pri testech e-mailu, tisku, mazani, odesilani a externich akci vyzadovat potvrzeni podle capability/risk pravidel.
- Soubory v `data/private/` a `data/session_autosave/` necommitovat.
