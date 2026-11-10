# MMTX — český text a volitelné české čtení nové šestky

Míla požádal o český překlad každé věty, nejprve zapínaný jako text a při dalším
zapnutí i čtený. V kontextu dosavadní práce jde o všech deset obrazů nové šestky.
Následující pokyn výslovně propojuje právě šestku z posledního obrazu pětky a
předává celý tento balíček Terře k p+n. Český přepínač tohoto checkpointu řeší šestku.

## Ovládání

Přepínač postupně nabízí `CZ: vypnuto` → `CZ: text` → `CZ: text + hlas`.
První stav přehrává dosavadní angličtinu. Druhý navíc zobrazí český překlad pod
anglickou větou, bez českého zvuku. Třetí po anglické větě přehraje českou MP3;
Next se odemkne až po dočtení. Repeat opakuje celý zvolený jazykový režim.

- Zapnutí čtení u již dokončené věty přečte její překlad, bez zbytečného
  opakování anglického zvuku. Zapnutí během angličtiny přidá češtinu po jejím
  doznění. Vypnutí během češtiny ji ihned zastaví a zneplatní staré callbacky.
- Anglickou chybu přepínač nepřeskočí. Chyba českého zvuku nabídne Repeat;
  vypnutí českého čtení umožní pokračovat po již vyslechnuté angličtině.
- Ticho v obrazu 9 zůstává bez textové bubliny a bez Audio ve všech režimech.
- Volba se ukládá do volitelného localStorage jen pro šestku. Bez úložiště,
  při jeho odmítnutí nebo neplatném stavu funguje bezpečný výchozí režim EN.
- Při viditelné češtině se všechny obrazy zobrazují v opraveném třířádkovém
  rozložení ve výšce okna: celý obrázek, oba texty, ovládání. V EN se u obrazů
  1–3 zachová původní rozložení. Český odstavec má lang=cs, tlačítko vysvětluje
  aktuální stav i další akci a při více ovladačích se může zalomit řádek HUD.

## Překlady a nové audio

Všech 67 českých překladů je samostatně v translations_cs.json, svázaných s
původním anglickým textem, jeho MP3, mluvčím, obrazem a číslem repliky. Devátý
obraz nemá umělý překlad ticha. Anglické JSON i audio manifesty se nepřepisují.

67 nových unikátních Azure požadavků, hlas cs-CZ-VlastaNeural, −10 %, 3977 SSML
znaků z předem zmrazeného limitu 4000, 1540368 B nových MP3. Odpovídající
anglické požadavky se neopakovaly. Celkem šestka obsahuje 67 EN + 67 CS MP3.
Soukromá účtenka zaznamenala před každým transportem rezervaci a nakonec 67
complete položek. Žádný retry ani fallback poskytovatele.

- Otisk vstupu translations_cs.json: `896fe055ce99243e8ed7d275054d4cf36a4cf44530d51b1833c891fa7a7050bb`.
- Otisk veřejného audio_manifest_cs.json: `fc40df532f3b11597fd21d040e440e1d8baf78b28e7908df86813f3ae4ce12fb`.
- 98 původních podkladů a devět původních raw EN účtenek zůstalo SHA-256
  beze změny. Nové soubory mají samostatnou audio/cs větev a český manifest.
- Nový builder sdílí dosavadní prověřenou jednorázovou výrobu s anglickým
  builderem přes build_assets. Anglický vstup, podpis účtenek, cesty a pravidla
  se nemění. Český builder před transportem kontroluje úplnost i přesnou vazbu
  každého překladu na angličtinu a shodu obou vstupních mirrorů.
- Tajemství zůstala v místní konfiguraci; raw účtenky a zmrazený plán nejsou v Gitu.

## Ověření

- 58 cílených kontrol PASS. Dekódování a otisky 67 EN + 67 CS MP3, shoda
  veřejných dat a mirroru. Lokální HTTP 170/170 skutečných souborů přesné.
- Node VM prošel všech 67 EN→CS dvojic, ticho a závěrečné Repeat/Again.
  Ověřil přepínání během řeči i v klidu, zastavení češtiny, chyby obou jazyků,
  pozdní callbacky, historii, uloženou volbu, zakázané úložiště a neplatnou
  vazbu překladu. Tichý obraz nespustil Audio ani při změně režimu.
- Syntetické kontroly builderu potvrdily celý rozpočet před transportem,
  zachování anglických podkladů, hotový opakovaný běh bez nových požadavků,
  durable attempted při ztracené odpovědi a zastavení bez retry. Skutečná
  generace se kvůli testu neopakovala.
- Skutečné Safari v běžném přehrávači ukázalo část 4 / 1/7 se čitelnou
  anglickou větou i překladem a celým Next uvnitř okna. Následně byl vidět
  režim CZ: text + hlas; HTTP protokol doložil nové české MP3 Fiony a Sunnyho
  v probíhajícím průchodu. Toto není Mílovo výslovné hodnocení celého hlasu.
- Plná místní brána českého rozšíření: 2984 testů OK (5 SKIP), 570,813 s unit.
  Po přidání rohu poslední cílená sada 70 PASS; nad integrovaným main poběží
  samostatná povinná publikační brána. Rychlá statická brána a git diff --check PASS.
- Fyzická přejímka na iPhonu, kvalita českých hlasů a Mílovo jazykové hodnocení
  zůstávají otevřené.

## Vydání

Vše je lokální vývoj v Datově worktree, bez změn Willova main a jeho WIP.
České rozšíření má vlastní navazující checkpoint po fe01d527. Při případné
integraci je potřeba předchozí vývoj částí 2, 3, 4–10 a oprava viewportu.
Servisní 06c34051 se do main nepřebírá podruhé. Míla následně výslovně autorizoval nové p+n celého hotového balíčku Terrou.
Nový běh bude mít vlastní stabilní request ID a nový přesný main head; nejde
o automatické opakování původního neúspěšného jobu. Další krok je dokončit
checkpoint, integrovat jen MMTX a jednou zavolat registrované submit_release(wait=True).


## Navazující pokyn — skrytý přechod z pětky a p+n

Na posledním rozlučkovém obrazu páté scény je nové průhledné klikací pole v
levém dolním rohu, 24 % šířky × 28 % výšky, minimálně 44 × 44 px. Nemá viditelný
text ani hover zvýraznění, ale má srozumitelný aria-label a klávesnicový focus.
Směřuje na skutečný index nové šestky. Běžný dokončovací odkaz zůstává.

Roh se zpřístupní jen při stage=complete a data-scene-state=friends-farewell,
pokud neběží řeč/animace a je zavřený slovníček. Před závěrem není viditelný
ani klikatelný. Otevřený slovníček ho skryje, zavření obnoví. Cache verze
pětky je 20261110lakecorner1; HTML, JS a interaction.css jsou shodné v mirroru.

14 kontrol pětky a přechodu PASS; celková cílená sada s češtinou 70 PASS.
Node VM ověřil nedokončený závěr, dokončený poslední obraz, slovníček,
přehrávání, animaci a jiný obraz. Skutečné fyzické proklikání tajného rohu
na Mílově zařízení zůstává součástí přejímky. Publikační worker znovu provede
povinnou bránu nad přesným integrovaným main před push/nasazením.
