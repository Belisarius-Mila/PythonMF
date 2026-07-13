Nazev: ColorsAndNumbers - navrh soukrome fotogalerie
Priorita: 2
Stav: ceka na rozhodnuti
Pripomenout pri startu: ne
Datum: 2026-07-13

Co se resilo:
- Mila navrhl v obrazovce `Numbers` pridat pobliz tlacitka `Back` male tlacitko
  `Foto` s ikonou fotoaparatu.
- Pod tlacitkem ma byt jednoducha galerie nejvyse tri fotografii.
- Po navrhu bylo rozhodnuto galerii zatim neimplementovat a vratit se k ni
  pozdeji.

Co je navrzene:
- Tlacitko `Foto` ma byt jen v obrazovce `Numbers`, dobre citelne jako
  `Foto` + ikona fotoaparatu, ne pouze nepojmenovana ikona.
- Galerie se ma otevrit jako prekryvny panel podobny sovimu oknu: velka aktualni
  fotografie, tri nahledy, poradi `1 / 3`, sipky i swipe a tlacitko `Zavrit`.
- Prazdna galerie ma nabidnout `Pridat fotku`; systemovy file input na iPhonu
  umozni vyber z Fotek nebo porizeni nove fotografie.
- Samostatny rezim `Spravovat` ma umoznit fotografii nahradit nebo po potvrzeni
  odstranit. Ctvrta fotografie se nesmi pridat bez nahrazeni jedne ze tri.
- Otevreni galerie ma zastavit vyslovnost a casovanou sekvenci `Numbers`;
  galerie a sova se nemaji prekryvat ani prehravat soucasne.

Doporuceny soukromy model:
- Repozitar `PythonMF` a publikovane GitHub Pages jsou verejne, proto rodinne
  fotografie nepatri do Gitu ani do `docs/colors-numbers/`.
- Prvni verze ma fotografie ukladat pouze do `IndexedDB` konkretniho prohlizece.
- Pred ulozenim je prohlizec zmensi zhruba na 1600 px, prevede na usporny JPEG
  a novym vykreslenim odstrani EXIF metadata vcetne pripadne GPS polohy.
- Fotografie tak neopusti zarizeni a preziji bezny reload i novou verzi webu.
- Omezeni: galerie se nesynchronizuje mezi zarizenimi a muze zmizet po vymazani
  dat Safari; originaly zustavaji v aplikaci Fotky a lze je vlozit znovu.
- Synchronizovana galerie by vyzadovala private backend a prihlaseni; pro tri
  fotografie se zatim nedoporucuje.

Navrhovane technicke provedeni:
- Samostatny `photo-gallery.js`, aby se galerie nemichala s denni upravou
  sovího audio radku v `app.js`.
- HTML panel a styly zrcadlit v pracovní i publikovane kopii aplikace.
- Do repozitare neukladat zadne skutecne fotografie ani jejich base64 kopie.

Nutny budouci test:
- Automaticky: syntaxe, limit tri fotografii, odmítnutí jineho typu souboru,
  shoda pracovní/publikovane kopie a pojistka, ze Git neobsahuje fotografie.
- Rucne na iPhonu: Fotky i fotoaparat, orientace na vysku/sirku, 1-3 fotografie,
  odmitnuti ctvrte, swipe, nahrazeni, potvrzene odstraneni, reload, offline
  provoz, male rozliseni a souziti se sovou, zvukem a tlacitkem `Back`.

Dalsi krok:
- Nic neimplementovat bez noveho vyslovneho rozhodnuti Mily.
- Pri navratu nejdrive znovu potvrdit, zda staci galerie lokalni pro jedno
  zarizeni, nebo je opravdu nutna synchronizace mezi vice zarizenimi.

Zmenene nebo relevantni soubory pro budouci praci:
- `ColorsAndNumbers/web_colors_numbers/index.html`
- `ColorsAndNumbers/web_colors_numbers/app.js`
- `ColorsAndNumbers/web_colors_numbers/styles.css`
- `docs/colors-numbers/`

Bezpecnost / neukladat:
- Necommitovat rodinne fotografie, EXIF/GPS metadata ani soukrome obrazove
  nahledy do verejneho repozitare nebo GitHub Pages.
