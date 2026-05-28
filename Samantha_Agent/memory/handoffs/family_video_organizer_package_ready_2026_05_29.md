Nazev: FamilyVideoOrganizer - realny lehky balicek pripraveny k testu
Priorita: 1
Stav: ceka na externi test
Pripomenout pri startu: ano
Datum: 2026-05-29

Co se resilo:
- Navazani na projekt Tomik video / FamilyVideoOrganizer.
- Cilem bylo prejit od UI prototypu k realnemu soukromemu balicku pro dceru:
  aplikace, realny `videos-data.js`, nahledy, bez MP4 v ZIPu.
- Probehlo overeni, ze aplikace ma nacitat 217 realnych zaznamu a prehravat
  puvodni MP4 podle originalnich nazvu souboru.
- Doresily se prakticke drobnosti pred odeslanim: Safari fallback pro vyber
  videi, zelene tlacitko `Slozka s videi` a zamknuti vybraneho radku kliknutim.

Co je hotove:
- Pridan opakovatelny generator:
  `scripts/tomik_family_video_package.py`
- Generator cte:
  - `data/private/tomik_rok_2/03_audit/video_audit_described.csv`
  - `data/private/tomik_rok_2/05_imovie_vyber_short/selection_manifest_short.csv`
  - `data/private/tomik_rok_2/06_imovie_vyber_family/selection_manifest_family.csv`
  - `data/private/tomik_rok_2/02_nahledy/`
- Generator vytvari soukromy balicek mimo git:
  `data/private/tomik_rok_2/family_video_organizer_package_light_20260528/`
- Aktualni ZIP pro odeslani dceri:
  `data/private/tomik_rok_2/family_video_organizer_light_20260528.zip`
- Balicek obsahuje:
  - `index.html`
  - `app.js`
  - `styles.css`
  - `videos-data.js`
  - `thumbs/`
  - `README.md`
- Balicek neobsahuje MP4. Video soubory si dcera pripoji tlacitkem
  `Slozka s videi`.
- Generator podporuje i volitelny tezky lokalni rezim `--include-videos`, kdy
  prida MP4 jako hardlinky nebo kopie do `videos/`.
- `videos-data.js` ma realna data:
  - 217 videi,
  - 35 short,
  - 82 family,
  - 651 nahledu,
  - 0 chybejicich nahledu.
- Safari/nepodporovany prohlizec uz nema koncit hlaskou
  `Vyber slozky tento prohlizec neumi`; misto toho otevira fallback input,
  kde lze vybrat slozku nebo oznacit MP4 soubory.
- Tlacitko `Slozka s videi` je zelene.
- Klik na radek nebo radkove `Play` zamkne aktivni radek, aby hover pri pohybu
  mysi k tlacitku `Play` neprepnul na jine video.

Co neni hotove:
- Neni jeste provedena zpetna realna zkouska u dcery.
- Neni jeste zpracovan dcerin export JSON rozhodnuti.
- Neni implementovan importer dcerina rozhodnuti zpet do short/family manifestu
  nebo do iMovie vyberu; to musi byt samostatny potvrzovany krok.
- Neni finalizovany text doprovodne zpravy pro dceru.

Dalsi krok:
- Poslat dceri `family_video_organizer_light_20260528.zip` a kratky navod:
  rozbalit ZIP, otevrit `index.html`, kliknout `Slozka s videi`, vybrat slozku
  s MP4, projit rozhodnuti/poznamky a nakonec poslat zpet exportovany JSON.

Navrhovane dalsi kroky:
- Okamzite:
  - udelat jeste jeden rucni smoke test aktualniho ZIPu v Chrome/Edge nebo Safari,
  - pripravit kratky lidsky navod pro dceru,
  - poslat ZIP.
- Po dcerine odpovedi:
  - nacist jeji JSON pres `Import draftu`,
  - zkontrolovat diff proti puvodnim short/family vyberum,
  - az po potvrzeni pripravit navazny skript pro aplikaci rozhodnuti do vyberu.
- Volitelne pozdeji:
  - pridat CSV export vedle JSON,
  - pridat stav nalezeno/nenalezeno u prehravani,
  - zvazit kratky help panel primo v aplikaci.

Zmenene nebo relevantni soubory:
- `docs/family-video-organizer/index.html`
- `docs/family-video-organizer/app.js`
- `docs/family-video-organizer/styles.css`
- `scripts/tomik_family_video_package.py`
- `tests/test_tomik_family_video_package.py`
- `data/private/tomik_rok_2/family_video_organizer_light_20260528.zip`
- `data/private/tomik_rok_2/family_video_organizer_package_light_20260528/`

Overeni:
- `node --check docs/family-video-organizer/app.js`
- `.venv/bin/python -m unittest tests/test_tomik_family_video_package.py`
- `unzip -t data/private/tomik_rok_2/family_video_organizer_light_20260528.zip`

Bezpecnost / neukladat:
- Rodinna videa, nahledy, realny `videos-data.js`, ZIP balicek a vystupy z
  dcerina testu patri do `data/private/` a nepatri do gitu.
- Do gitu patri jen generator, UI prototyp, testy a memory/handoff.
- Necommitovat `data/private/`, MP4, nahledy, dceriny export JSON ani cele
  soukrome popisy nad ramec uz existujicich lokalnich private dat.
