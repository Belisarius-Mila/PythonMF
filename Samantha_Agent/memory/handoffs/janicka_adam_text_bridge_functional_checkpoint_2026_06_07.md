# Janička Adam text bridge functional checkpoint

Nazev: Janička Cockpit / textový chat s Adamem
Priorita: 1
Stav: hotovo
Pripomenout pri startu: ne
Datum: 2026-06-07

## Co se resilo

Janička v Cockpitu má umět položit textový dotaz Adamovi tak, aby Jana nemusela
ovládat Codex ani VS Code. Cílem bylo, aby odpovídal běžící Adam/Codex relace se
znalostí projektu, ne separátní obecná AI bez kontextu.

## Co je hotove

- `Jana Adam` textový modal v Cockpitu předává dotazy do běžící Codex relace.
- Každý dotaz dostane `request_id` a odpověď se zapisuje zpět přes
  `scripts/adam_voice_reply.py --request-id ... --route janicka_text_bridge`.
- Byly otestované reálné dotazy:
  - `Jak funguje Najít dokument?`
  - `Co mi můžeš říct o projektu Pozůstalost?`
- Odpovědi se zobrazily zpět v Cockpitu.
- Poslední pozorovaná rychlost odpovědi byla přibližně 44 sekund. To je
  realistické pro cestu přes plnohodnotnou běžící Codex relaci.
- Od této vlny je výchozí doručení textového dotazu přes terminálový bridge,
  ne přes VS Code GUI fallback.

## Dulezite technicke rozhodnuti

Krátce se zkoušela skrytá `screen` relace `samantha_adam`, aby se nepřepínal
fokus z Cockpitu. Ukázalo se, že tato cesta uměla požadavek uložit jako
`delivered`, ale Codex v ní dotaz reálně nepřevzal a odpověď nedorazila.

Funkční stav je proto jiný:

- Janička bridge cíleně používá terminálový bridge a doručuje do označené nebo
  nalezené Codex relace.
- AppleScript GUI helper zůstává jako explicitní fallback.
- VS Code helper se může krátce aktivovat, ale není výchozí cesta.

## Co neni hotove

- Neřešit teď rychlost za každou cenu. Pokud má odpovídat skutečný Adam/Codex,
  desítky sekund jsou přijatelné.
- Skrytá `screen` varianta není spolehlivá jako hlavní cesta pro odpovědi.
- `Rodinné projekty` v Janičce zůstávají další samostatný krok.

## Dalsi krok

Nechat aktuální textový kanál bežet jako funkční prošlapanou variantu. Při
dalším testování se soustředit spíš na obsah odpovědí pro Janu než na technickou
architekturu.

## Navrhovane dalsi kroky

- Krátkodobě: ručně s Janou/Mílou testovat další jednoduché otázky v Cockpitu.
- Pokud bude čekání působit matoucí, přidat do UI stav typu `Adam čte` /
  `Adam odpovídá`.
- Později: pro úplně jednoduché kuchařkové dotazy zvážit rychlou lokální odpověď,
  ale jen pokud nebude porušen princip, že klíčové odpovědi dává Adam/Codex.

## Zmenene nebo relevantni soubory

- `app/adam_service.py`
- `app/speech/terminal_bridge.py`
- `app/cockpit.py`
- `scripts/adam_voice_reply.py`
- `tests/test_adam_service.py`
- `tests/test_terminal_bridge.py`
- `tests/test_cockpit.py`
- `tests/test_adam_voice_mode.py`
- `memory/projects/janicka_cockpit_takeover.md`

## Commity

- `61af5f2 Add managed Adam service for Janicka chat`
- `8cc754f Use managed screen delivery for Janicka Adam`
- `0a6bb4f Route Janicka Adam prompts to visible VS Code`

## Bezpecnost / neukladat

- Do git-safe handoffu neukládat hesla, tokeny, recovery klíče, plné e-maily,
  rodná čísla ani jiné citlivé konkrétní údaje.
- U projektu Pozůstalost odpovídat Janě jen obecně; citlivé údaje patří pouze
  do private/šifrovaného balíku mimo git a mimo běžné Cockpit rozhraní.
