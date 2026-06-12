Nazev: Adam Voice Bridge freeze and return to e-mail workflow
Priorita: 1
Stav: rozpracovane / zmrazeno
Pripomenout pri startu: ano
Datum: 2026-06-12

Co se resilo:
- Mila rozhodl, ze voice bridge se ted zmrazi v aktualnim funkcne pouzitelnem stavu.
- Duvod: dalsi ladeni voice bridge zacina prinaset vic rezijniho zmatku nez prakticke hodnoty pro bezny vzdaleny provoz.
- Navazujici smer je vratit se k e-mailum a otestovat implementaci nacitani metadat na bezpecnem testovacim e-mailu s prilohou, ktery si Mila posle sam.

Co je hotove:
- iPhone/Tailscale Cockpit umi poslat hlasovy nebo textovy pokyn do aktualni Codex relace.
- Posledni Adamova odpoved se zapisuje zpet do Cockpitu pres `scripts/adam_voice_reply.py --latest-command`.
- Hlasove cteni vysledku funguje pres `scripts/speak_edge_open.py`.
- Cockpit zobrazuje runtime kartu `Codex ceka na potvrzeni`.
- Karta byla upravena do lidske struktury: `Co chci udelat`, `Proc`, `Riziko`, `Co ma Mila udelat`.
- Helper `scripts/codex_approval_notice.py set` umi nove volitelne `--risk`.
- Lokalni i Tailscale Cockpit byly po uprave restartovane a live API test karty prosel.
- Testy `tests.test_cockpit`, `tests.test_adam_voice_mode` a `tests.test_terminal_bridge` prosly: 185 testu OK.

Co neni hotove:
- Cockpit stale neumi zmacknout interni Codex approval tlacitko; umi jen vysvetlit, proc Codex stoji a co ma Mila udelat.
- Dev runner a read-only kontrolni tlacitka nejsou vhodne jako hlavni uzivatelske workflow pro Milu; jsou servisni fallback.
- SSH/triage cesta muze porad narazit na rucni potvrzeni, pokud pokyn vyhodnoti riziko nejednoznacne.
- Neni hotova nova e-mailova metadata implementace ani realny test s prilohou.

Dalsi krok:
- Zmrazit dalsi vyvoj voice bridge a prejit na e-mailovy workflow.
- Mila si muze poslat bezpecny testovaci e-mail sam sobe s jednoduchou prilohou bez citlivych dat.
- Pak navazat read-only kontrolou v e-mailovem workflow: nacist hlavicky/metadata a overit, ze se metadata a priloha objevi spravne, bez mazani, bez odesilani a bez ukladani citliveho obsahu do gitu nebo memory.

Navrhovane dalsi kroky:
- Okamzity krok: po H+C+P otevrit e-mailovou cast Cockpitu nebo spustit existujici read-only e-mailovy tooling jen nad testovacim e-mailem.
- Volitelne: zapsat drobne pravidlo do triage/voice inboxu, aby veta typu `H+C+P` nebo `handoff commit push` neuvizla jen kvuli tomu, ze obsahuje commit/push, pokud je zamer jasny a jde o explicitni pokyn od Mily.
- Nevracet se k dalsimu ladeni voice bridge, dokud se neobjevi konkretni blok v realnem e-mailovem nebo dokumentovem provozu.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/speech/adam_voice_mode.py`
- `scripts/codex_approval_notice.py`
- `tests/test_cockpit.py`
- `tests/test_adam_voice_mode.py`
- `memory/technical/codex_remote_approval_notice.md`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Do gitu ani memory neukladat obsah realnych e-mailu, UID se soukromym kontextem, cele e-mailove adresy, prilohy, tokeny, hesla, app-specific passwords ani plne URL.
- Testovaci e-mail ma byt bez citlivych dat.
- Mazani, odesilani, presun do kose, trvale mazani a ukladani obsahu e-mailu zustavaji potvrzovane kroky.
