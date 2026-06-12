Nazev: Autosave status a voice triage false-positive fix
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-12

Co se resilo:
- Mila se vratil k puvodni priorite "auto safe", tedy ochrane rozpracovane
  Codex/Samantha prace proti padu relace.
- Pri kontrole se ukazalo, ze posledni `data/session_autosave/latest_info.txt`
  je stary zhruba 18 hodin a autosave watcher realne nebezi.
- Soucasne se objevila falesna hlasova brzda: veta "bylo treba stisknout
  potvrzeni" byla mylne vyhodnocena jako rizikovy tisk, protoze triage hledala
  `tisk` jako podretezec ve slovu `stisknout`.

Co je hotove:
- Pridan read-only status tool `scripts/autosave_status.py`.
- Tool hlasi stari posledniho autosave snapshotu, zda bezi watcher a pripadne
  doporuci dalsi krok po potvrzeni.
- `scripts/system_quick_check.py` pouziva novy autosave status misto pouhe
  kontroly mtime souboru.
- Opravena triage v `app/speech/voice_inbox.py`: term `tisk` se bere jako
  rizikovy jen jako samostatne slovo, ne uvnitr `stisknout`.
- Regresni testy potvrzuji, ze `stisknout potvrzeni` je read-only diagnostika,
  ale `Vytiskni fakturu` stale vyzaduje potvrzeni.
- Overeno, ze posledni predtim nedorucena hlasova zprava ma po oprave
  `risk=read_only` a `requires_confirmation=false`.

Co neni hotove:
- Autosave watcher nebyl spusten automaticky, protoze by zacal zapisovat
  soukrome session logy do `data/session_autosave/`.
- Dalsi relace ma byt spoustena pres `samantha`, ne pres holy `codex`, aby
  se autosave a screen zapnuly automaticky.

Dalsi krok:
- Po ukonceni teto relace spustit novou praci pres:
  `source ~/.zshrc && samantha`
  pokud shell prikaz `samantha` sam nezna.

Navrhovane dalsi kroky:
- Okamzity: commit a push teto opravy.
- Pri dalsim startu overit `.venv/bin/python scripts/autosave_status.py`; pokud
  watcher stale nebezi, nepokracovat dlouho v praci bez startu pres `samantha`.
- Volitelne: doplnit Cockpit servisni tlacitko/stav pro autosave watcher.

Zmenene nebo relevantni soubory:
- `scripts/autosave_status.py`
- `scripts/system_quick_check.py`
- `tests/test_safety_quick_checks.py`
- `app/speech/voice_inbox.py`
- `tests/test_voice_inbox.py`

Bezpecnost / neukladat:
- `data/session_autosave/` muze obsahovat citlive texty z relace a nikdy se
  nesmi commitovat.
- Spusteni watcheru je zapis do soukromych runtime dat; delat jen vedome nebo
  pres standardni start `samantha`.
