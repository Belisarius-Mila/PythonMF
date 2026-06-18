Nazev: Samantha screen scrollback fix
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ne
Datum: 2026-06-18

Co se resilo:
Start pres `samantha` chrani Codex relaci pomoci `screen`, ale v praxi se v nem
scrollovani chovalo hur nez pri prostem spusteni `codex`. Mila potreboval po
restartu relace normalne dohledat predchozi vystup a rozlisit, jestli je problem
ve startu Samanthy, nebo jen ve scrollbacku uvnitr `screen`.

Co je hotove:
- `scripts/samantha_codex.sh` pouziva projektovy screen config
  `scripts/samantha_screenrc`.
- Pri pripojeni k existujici i nove `screen` relaci vypise kratky tip:
  `Ctrl+A` potom `Esc` otevira screen scrollback a `Esc` ho zavira.
- `scripts/samantha_screenrc` nastavuje vetsi scrollback a vypina alternate
  screen, aby scrollback zustaval pouzitelnejsi v terminalu.
- Syntakticka kontrola `zsh -n scripts/samantha_codex.sh` prosla.
- Stara `screen` relace `samantha_codex` byla po Milove potvrzenem pokynu
  ukoncena, aby mohl zkusit cisty start.

Co neni hotove:
- Neni jeste rucne potvrzeno, ze novy start `samantha` ma scrollovani v praxi
  dostatecne pohodlne.
- Chovani muze zalezet na terminalu, SSH klientovi a tom, zda se pouziva
  trackpad/kolecko, klavesy PageUp/PageDown nebo screen copy mode.

Dalsi krok:
Spustit ciste:

```bash
source ~/.zshrc
samantha
```

Pak v delsim vystupu overit scrollovani. Pokud bezne kolecko stale nestaci,
pouzit screen copy mode: `Ctrl+A`, potom `Esc`; ven opet `Esc`.

Navrhovane dalsi kroky:
Okamzity:
- Mila rucne otestuje novy start Samanthy a scrollback.

Volitelne:
- Pokud `screen` zustane nepohodlny, zvazit samostatny rezim startu bez `screen`
  pro lokalni Mac praci, ale ponechat `screen` jako vychozi pro SSH/iPhone
  recovery.
- Pokud nektery terminal ignoruje `altscreen off`, pridat do handoffu presny
  terminal a chovani.

Zmenene nebo relevantni soubory:
- `scripts/samantha_codex.sh`
- `scripts/samantha_screenrc`
- `memory/ACTIVE_PROJECTS.md`
- `memory/MEMORY_INDEX.md`

Bezpecnost / neukladat:
- Handoff neobsahuje tajemstvi, e-maily, tokeny ani soukroma data.
- `data/session_autosave/` zustava jen nouzovy zdroj obnovy a nesmi se commitovat.
