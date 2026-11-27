# Vocabulary FR — vydání523 karet a zachování místností, 27. 11. 2026

Míla výslovně zadal p+n a aktualizaci soukromé herní služby. Výroba médií je
uzavřená v daabc486; žádná nová syntéza ani obrazová výroba není součástí kroku.

První registrované předání 567563befb2a764de1ac85ed35ea9597 skončilo attention
před potvrzením push. Původní worker skončil a jeho lease je volná. Čerstvý
audit i ls-remote potvrzují původní GitHub0068a369, cílový daabc486 není odeslaný;
žádný původní Git transport neběží. Účtenka se nemaže ani nepřepisuje a stejný
pokus se automaticky neopakuje. Původní odpověď nedokládá přesný důvod odmítnutí.
Chyba vykonavatele nyní předá i stručnou původní serverovou zprávu, aby další
odmítnutí nebylo zaměněno za neurčité selhání přenosu.

Kontroly lokálních médií jsou nově součástí existující registrované sady
vocabularyfr_content. Nepotřebují samostatnou desktopovou validační doménu
ani změnu registru běžícího Cockpitu. Původních6 testů Jana bundle zůstává
v původním souboru;6 mediálních testů je zachovaných v kanonické FR sadě.
Validační pravidla se neobcházejí, žádný test ani podpis se nevypíná.

Nutná kompatibilita místností

Dosavadní Rooms váže partii na přesný otisk katalogu; pouhá výměna481→523 by
při pokračování vrátila409, i když jsou původní slovíčka nezměněná. Proto
PrivateGame.prepare připíná kompatibilní přechod do neměnného plánu jen tehdy,
když jsou všechny původní hratelné položky i jejich quiz metadata přesně stejné.
Skutečný obsah:481/481 původních významů beze změny, nových42.

Activate znovu porovná plán. Po zastavení původního procesu a před startem
nového vytvoří registrovanou konzistentní SQLite zálohu a v jedné transakci
změní pouze body.catalog u místností odpovídajících původní verzi. Nezmění
ID, request ID, heslové otisky, pozvánku, hráče, skóre, balíček, kolo ani expiraci.
Neznámé významy odmítne bez změny kterékoli místnosti; jiné verze nepřeznačuje.
Dokončený request se podle stávajícího lifecycle už znovu neprovádí.

Ověření

-4 nové regresní případy migrace: oba režimy, zachování všech ostatních polí,
  rollback při neznámém UID, jiné katalogy a přesná kontrola starých významů.
-63 cílených tailnet/content testů a60 release/submission testů PASS.
- Ověřená kopie skutečné databáze se17 původními místnostmi a2 novými
  kontrolovanými rozehranými partiemi. Přesný rozdíl je jen catalog; oba hráči
  pokračují stejnými tokeny i pozvánkou v Pexesu i duelu. Živá DB nezměněná.
- Programová brána476 testů PASS, účtenka ff3cd252f0388dbb64408896df82cec25b0b991f42c0ecd2ebede9fcf9edf806.
- Finální SHA a výsledky publikace/aktivace určuje
  data/private/vocabulary_fr_content_release_20261127/completion.json.

Rozsah aktivace a souhlas

Služba používá stávající LaunchAgent a Tailscale8443; zachová stejnou adresu,
Cockpit443 i ostatní Serve trasy a vypnutý Funnel. Před systémovou aktivací
musí být aktuální přesný plán a Mílova přesná globální potvrzovací věta podle
global_safety_brake.md; výslovné p+n nepřeskakuje tuto technickou bránu.
Plán v1 pro daabc486 nebyl aktivovaný. Po integračním commitu je nutný nový
plán zahrnující ověřený převod katalogu; stará identita se nepoužije na jiný SHA.

Další postup

Zkontrolovat a commitnout úzkou opravu, zarovnat čisté profily, poté nové
registrované submit_release(wait=True) pro celý opravený balíček. Aktivovat
službu až po potvrzené publikační účtence a přesné globální větě. Ověřit523
položek, všechny změněné klientské bajty, audio Range206, SQLite integrity
a zachování původních identit ze skutečné zálohy po zastavení služby.
Po změně verze oba hráči obnoví stránku; pozvánku nemění. Fyzická přejímka
na dvou Macích zůstává samostatná. Konečné účtenky zůstávají soukromé.
