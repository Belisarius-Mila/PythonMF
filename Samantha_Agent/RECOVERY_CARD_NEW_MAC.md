# Recovery karta: nový Mac + externí záloha

Aktualizováno 2026-10-19. Hlavní podrobný návod je nyní v prostém textu:

[OBNOVA_SAMANTHY_NOVY_MAC.txt](OBNOVA_SAMANTHY_NOVY_MAC.txt)

Obsahuje instalace, Python a knihovny, VS Code, Codex, Xcode, iLoader,
Tailscale, obnovu dat, služby, iPhone a závěrečné ověření.

## Kde začít

1. Získej tento TXT z kořene SSD Falta nebo z repozitáře, pokud už byl
   publikován. Ve šifrovaném kontejneru je také doplněk kódu pro starší
   projektový snapshot; viz kapitola 6.4 TXT.
2. Připrav přístupy a heslo šifrovaného recovery disku mimo ztracený Mac.
3. Podle TXT připrav nový macOS, zvol správnou architekturu a Python 3.12.
4. Vyber dokončený snapshot podle manifestu; nepoužívej slepě poslední
   adresář. Poslední doložený běh je `20261018_210658`, profil recovery.
5. Obnov do prázdného cíle a nejdřív ověř místní Cockpit. Teprve potom
   obnovuj trvalé služby a soukromou vzdálenou cestu.

## Důležitá hranice úplnosti

Projektová záloha není obraz celého Macu. Neobsahuje instalované aplikace,
Klíčenku, kompletní konfiguraci systému ani celý `~/.codex`.
Nouzové `data/session_autosave` se vylučuje i z recovery profilu;
vybrané originální Codex sessions jsou samostatně zahrnuté.

**Živý archiv Camina má samostatný šifrovaný doplněk**
`20261019_212828-78238a8a` v `SamanthaBackups/camino_snapshots/`:
čtyři databáze, média, filmové projekty, konfigurace a přesný serverový release.
Obnovuj jej podle kapitol 1.4 a 12 TXT spolu s projektovým snapshotem.
Aktualizované recovery zálohování tento doplněk pořizuje automaticky;
starší projektový snapshot z 18. 10. tím změněn nebyl.

## Co nedělat

- Nic nemazat ani nepřepisovat přes existující cílovou složku.
- Nekopírovat starý Codex `auth.json`; přihlásit se znovu. Čerstvé nové
  přihlášení není potřeba mazat.
- Neposílat `.env`, historii, tokeny ani hesla do chatu nebo Gitu.
- Nepřenášet Intel virtuální prostředí na Apple Silicon.
- Neopakovat staré odchozí úlohy, push/nasazení nebo potvrzení automaticky.
- Nemazat ani neresetovat původní Camino na iPhonu.

## Pokyn novému Adamovi

> Jsem Míla a obnovuji Samanthu na novém Macu. Pracuj česky.
> Přečti OBNOVA_SAMANTHY_NOVY_MAC.txt, AGENTS.md, memory/MEMORY_INDEX.md
> a handoff infrastruktury. Nic nemaž, nepřepisuj existující data,
> nevypisuj tajemství. Ověř skutečný rozsah zálohy včetně mezery živého Camina.
> Nejdřív obnovme Python a místní Cockpit, potom jednotlivé služby.

Staré postupy s automatickým `git pull`, hromadným přepsáním `~/.codex`
a mazáním jeho přihlášení byly touto kartou nahrazené.
