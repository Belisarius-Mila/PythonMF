# Scene 2 — Sunny's Lost Nuts

Produkční webový modul druhé scény lesní cesty MMTX. Sunny ztratí oříšky, Fiona pomáhá s otázkami a Matýsek postupně kliká na Benjiho, Bunny a Brunovu brašnu.

Navazuje na Scene 1 — Clearing Meeting.

Aktuální tok: rozcestí v lese → Scene 1 → Scene 2. Další scény budou později navazovat za scénu 2; návrat na rozcestí je zatím přes tlačítko `↩`.

## Co scéna dělá

1. Zobrazí nový obrázek scény a velké tlačítko Start.
2. **Úvod:** Sunny zjistí, že nemá oříšky. Fiona se ptá Benjiho.
3. **Krok 1:** *Tap Benji. Does he have nuts?* → Benji: *No. I have a map.*
4. Fiona se ptá Bunny → **Krok 2:** *Tap Bunny. Does he have nuts?* → Bunny: *No. I have a carrot.*
5. Bruno nabídne brašnu → **Krok 3:** *Tap the bag.* → oříšky vyskočí jako overlay.
6. Sunny: *My nuts! I am so happy!* → Fiona: *Good. Now we are ready.* → mapa se rozsvítí.
7. Dokončovací bublina `Next: Journey to the Lake` otevře Scene 3.
8. Špatný klik = jen jemná nápověda (*Try again.* / *Not yet. Tap Benji.* / *Look at the bag.*), bez spoilerů.
9. Ikona knihy otevře malý slovníček. Klik na položku přečte anglické slovo a potom český význam.

Výukové fráze: *I don't have*, *Do you have?*, *I have a map*, *I have a carrot*, *I have a bag*, *Look inside!*

## Jak spustit lokálně

```bash
cd web_mmtx_scene02_cursor_prototype
python3 -m http.server 8877
```

Otevři v prohlížeči: `http://localhost:8877/`

## Hlavní obrázek

| Soubor | Popis |
|--------|--------|
| `scene_02_sunnys_lost_nuts_before.png` | **Aktivní** produkční scéna (1672×941) |
| `scene_placeholder.svg` | Nouzový fallback při chybě načtení PNG |

## Audio — soubory k doplnění

MP3 zatím nejsou v repozitáři. Kód je na ně připravený; pokud soubor chybí, použije se fallback přes `speechSynthesis`.

Viz `audio/README.md` pro kompletní manifest včetně instrukčních vět a slovníčku.

## Slovníček

Ikona `📖` otevře malý slovníček. Položky:

| English | Česky |
|---------|-------|
| nuts | oříšky |
| map | mapa |
| carrot | mrkev |
| bag | brašna |
| I have | mám |
| I don't have | nemám |
| Do you have? | máš? |
| Does he have? | má on? |
| Look inside | podívej se dovnitř |

## Interakční kroky

| Krok | UI nápověda | Správný klik | Odpověď / efekt |
|------|-------------|--------------|-----------------|
| úvod | — | — | Sunny + Fiona otázka na Benjiho |
| 1 | Tap Benji. Does he have nuts? | Benji | *No. I have a map.* |
| 2 | Tap Bunny. Does he have nuts? | Bunny | *No. I have a carrot.* |
| 3 | Tap the bag. | brašna / širší zóna | overlay oříšků |
| závěr | — | — | Sunny + Fiona + mapa |

## Hotspoty (1672×941, %)

| Cíl | x | y | w | h |
|-----|---|---|---|---|
| Benji | 3.0 | 40.0 | 23.0 | 40.0 |
| Bunny (na pařezu) | 25.0 | 17.0 | 13.0 | 37.0 |
| Bruno | 44.0 | 28.0 | 14.0 | 47.0 |
| Fiona | 62.0 | 29.0 | 17.0 | 48.0 |
| Sunny | 81.0 | 47.0 | 15.0 | 41.0 |
| **Brašna (přesná)** | 50.5 | 44.0 | 10.5 | 22.0 |
| **Brašna (odpustivá zóna)** | 46.0 | 38.0 | 20.0 | 32.0 |

Oříšky po nálezu: overlay na pozici **53 % / 52 %** (emoji, později nahraditelné PNG `nuts_reveal.png`).

## Stavy scény

`idle` → `playing` → `waitingTap` ↔ `resolvingTap` → `complete`

## Integrace do MMTX

- Hlavní web: `../index.html`
- Vstup: dveře po dokončení Scene 1 (`clearingMeeting`)
- Výstup po dokončení: `../scene03_journey_to_the_lake/index.html`

## Ruční test checklist

- [ ] Stránka se otevře bez JS chyb v konzoli
- [ ] Načte se `scene_02_sunnys_lost_nuts_before.png` (ne starý mossy stump)
- [ ] Start spustí Sunnyin úvod
- [ ] Matýsek postupně klikne Benji → Bunny → brašnu
- [ ] Špatný klik jen jemně poradí, neprozradí budoucí odpovědi
- [ ] Klik na brašnu odhalí oříšky (overlay)
- [ ] Sunny se zaraduje, Fiona řekne *Good. Now we are ready.*
- [ ] Mapa a complete banner se zobrazí
- [ ] ↺ a 🎤 fungují během úkolu
- [ ] 📖 otevře slovníček a položky se dají přehrát
- [ ] Chybějící MP3 nerozbije scénu (TTS fallback)
