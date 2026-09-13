# ToBeToHave — lokální webový prototyp

Stav 2026-09-13: připravený lokální prototyp, bez publikování a bez změny
desktopové aplikace nebo Cockpitu. VocabularyFR, VocabularyIT a sdílený Pict
se v tomto kroku neupravují.

## Spuštění

Ze složky `Samantha_Agent`:

```sh
.venv/bin/python -m http.server 8791 --bind 127.0.0.1 --directory ../ToBeTraining/web
```

Na stejném Macu otevřít `http://127.0.0.1:8791/`. Adresa s `127.0.0.1`
nefunguje z jiného zařízení. Soubor `index.html` se neotevírá přes `file://`.
Server servíruje pouze složku `web`, nikoli dokumenty v rodičovském projektu.

## Ovládání

- **Otázky a odpovědi:** be / have / go, 107 otázek, samostatné odkrytí
  kladné a záporné odpovědi. Opětovné klepnutí přehraje odpověď znovu.
- **Hraj si se slovy:** 24 příkladů rozdělených podle slovesa. Barevné
  dílky se postupně objevují a MP3 přečte celou větu.
- **Vytvořit otázku:** be přeskočí před zájmeno; u have/go přijde Do/Does
  a has/goes se změní na have/go. Pohyb doplní krátké barevné konfety.
- **Pauza / Pokračovat** pozastaví zvuk, čekání i slovní animaci.
- **Pokračovat automaticky** zapne opakovaný průchod oznamovacími větami.
  Výchozí režim dává uživateli čas a čeká na další pokyn.
- Český překlad je volitelný, pouze textový a patří k oznamovací větě.
  Při tvorbě otázky se schová, aby nesliboval překlad jiného významu.
- Náhodné pořadí projde všechny položky bez opakování uvnitř jednoho cyklu.
  Přechod mezi náhodnými cykly neopakuje bezprostředně poslední položku.
- Tempo mění rychlost MP3. Změna režimu či věty zruší předchozí přehrávání.
  Odchod do pozadí pozastaví aktivní skládání; jednorázový poslech zastaví.
- Rozložení je responzivní. Systémová volba omezeného pohybu potlačí animace.

Obrázky jsou kontextová nápověda, nikoli zadání testu s jednou správnou
odpovědí. Procvičují se obě možné odpovědi. U míst může být zobrazeno samotné
místo; u věku je na obrázku doplněná informace z otázky.

## Data, obrázky a hlas

Původní `tobevety.csv` a `verb_conjugation.csv` zůstávají pouze ke čtení.
`scripts/build_web_data.py` exportuje jejich obsah a zkontrolované přiřazení
obrázků do `web/data.json`. Změna zdrojového CSV vyžaduje novou kontrolu
přiřazení; nejde o obecné automatické hledání podle klíčových slov.

V `web/assets/images` je 47 WebP: 36 adaptací z Pict a 11 nových ilustrací.
Každý obrázek má nejvýše 262 144 B (0,25 MiB), nejdelší stranu nejvýše
1200 px. Původní soubory Pict zůstávají zachované. Nové originály a kontaktní
náhledy jsou v místním ignorovaném `qa/`; všechny webové odkazy vedou na
samostatné kopie uvnitř `web`. Podrobnosti a zadání v `IMAGE_PLAN.md`.

Veškerá angličtina používá **184 hotových MP3**, včetně otázek, obou odpovědí,
oznamovacích vět a vytvořených otázek. Stejný text sdílí nahrávku.
Hlas je `en-US-JennyNeural`, při generování tempo `-10%`.
Aplikace nepoužívá `speechSynthesis`, mikrofon ani online generování za běhu.

Příprava MP3 používá registrovanou schopnost `generate_project_audio_asset`
a implementaci `app.speech.edge_tts_mp3`. Pouze při přípravě odchází veřejný
výukový text ke službě TTS. Již hotová aplikace čte místní soubory.

```sh
# Ze Samantha_Agent, při vědomé aktualizaci obsahu:
.venv/bin/python ../ToBeTraining/scripts/build_web_data.py
.venv/bin/python ../ToBeTraining/scripts/build_audio.py
```

## Ověření

```sh
node --test ../ToBeTraining/scripts/test_web.mjs ../ToBeTraining/scripts/test_app_flow.mjs
.venv/bin/python ../ToBeTraining/scripts/check_web.py --url http://127.0.0.1:8791
```

Ověřeno 14 automatických testů včetně skutečného UI modulu s náhradním DOM
a audiem: odkrývání odpovědí, výběr vět, otázky, překlad, pauza, pozdní
callback po změně lekce, MP3 chyby a pořadí. Ověřeno 184 MP3 přes ffprobe,
47 dekódovatelných WebP v rozpočtu a 236 místních HTTP odpovědí shodných
s obsahem souborů. Prošla rychlá projektová statická brána.

**Otevřené ověření:** skutečné vykreslení, ovládání a poslech v prohlížeči
na Macu a iPhonu. Vestavěný Browser se v této relaci nepřipojil kvůli
nedostupnému nativnímu propojení. Testovací DOM neověřuje layout ani
politiku přehrávání Safari. Není ověřen offline režim/PWA ani vzdálený provoz.
Před případným nasazením ověřit zejména první tap, automatické další MP3,
pauzu během přesunu slov, návrat z pozadí a zobrazení při šířce 375 px.
