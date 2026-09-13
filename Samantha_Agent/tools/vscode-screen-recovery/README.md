# Samantha Screen Recovery

Místní doplněk pro tlačítko **Servis → Běžící relace → Screeny → Obnovit
ve VS Code na Macu**. Otevře terminál se stejným běžícím screenem. Nevytváří
nový screen ani Codex, neodesílá text do rozpracovaného terminálu.

Cockpit před otevřením i před převzetím ověří vlastníka, projekt a identitu
screenu. Screen s terminálovým Codexem lze připojit, chráněné služby nikoli.
Převzetí připojeného screenu vyžaduje potvrzení v Cockpitu; původní terminál
se odpojí. Požadavek funguje i při kliknutí z iPhonu, cíl je vždy Mac
s Cockpitem. Obnova samostatných terminálů bez screenu není součástí.

## Příprava místního doplňku

Ze složky Samantha_Agent, s novou zvolenou cestou výstupu:

```sh
.venv/bin/python scripts/build_screen_recovery_extension.py /tmp/samantha-screen-recovery-0.1.0.vsix
"/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" --install-extension /tmp/samantha-screen-recovery-0.1.0.vsix
```

Bez npm závislostí, marketplace a publikování. Doplněk se aktivuje přijetím
URI ve VS Code; okno musí být důvěryhodné. macOS/VS Code může při prvním
otevření vyžádat systémové potvrzení. Pokud je doplněk zakázaný, povol ho
v přehledu rozšíření VS Code. Instalace doplňku sama nenasazuje změnu Cockpitu.

## Hranice a ověření

- URI obsahuje jen port místního serveru a jednorázový náhodný ticket (90 s).
  Ticket se neukládá na disk a nelze ho znovu použít. Odpovědi API neobsahují
  příkazy procesů, historii rozhovorů ani pracovní cesty.
- Doplněk kontaktuje pouze `127.0.0.1`, odmítá přesměrování a spouští pevný
  `/usr/bin/screen -d -r <ověřený socket>` přímo, bez shellového řetězce.
- Identita obnovy obsahuje PID, start, vlastníka, příkaz, adresář, executable
  a stav připojení. Běžná změna podřízené úlohy Codexu neblokuje obnovu;
  ochrany aktuálních potomků se vždy znovu kontrolují.
- Duplicitní žádost během 90 s neotevírá další terminál. Při nejistém doručení
  nejprve zkontroluj VS Code; požadavek se automaticky neopakuje.
- Hláška Cockpitu dokládá předání požadavku. Úspěšné připojení ověř v terminálu.
  Při zániku screenu mezi ověřením a připojením `screen -r` skončí; nový
  screen se nevytváří. Terminál je transientní, VS Code ho při restartu
  automaticky znovu nespouští.

Testy: `.venv/bin/python -m unittest tests.test_screen_recovery`.
Ruční test: na vlastním testovacím screenu ověř odpojený i připojený stav,
zrušení potvrzení, kontinuitu PID uvnitř, nové okno terminálu a opakovaný klik.

Použitá API: [VS Code terminal a URI handler](https://code.visualstudio.com/api/references/vscode-api).
