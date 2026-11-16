# Vocabulary IT — volitelné Psaní

Stav: 2026-11-16 12:55 CET; nový krok místní, samostatné p+n dosud nezadané.
Proud: project-vocabulary-it. Základ ee6d904d, vlastní stálý worktree Data.

## Chování

Přepínač Psaní je součástí Slovo a obrázek, výchozí vypnuto. Po správném
obrázku zůstane velká karta do dokončení jejího italského přehrání. Potom
italský nadpis zmizí a fokus přejde do velkého psacího pole. Český význam
zůstává. Psaní se vyhodnocuje automaticky až při úplné správné shodě:
zelené600ms potvrzení, zavření pole, obnovení zápisu a povolení Další.
Uživatel pokračuje sám. Nápověda ukáže přesný zápis500ms, zachová draft
a znovustiskem obnoví interval. Místo pro nadpis je rezervované i při skrytí,
takže nápověda neposouvá pole. Samostatná živá zpráva s lang=it se vizuálně
nezobrazuje; vydrží pro čtečku déle než500ms a vyčistí se psaním/odchodem.

Porovnání zachová přízvuky, dvojité souhlásky i interpunkci. NFC normalizuje
různé Unicode zápisy; velikost písmen, krajní/vícenásobné mezery a běžné
telefonní apostrofy se tolerují. Vyžaduje se celý text karty, včetně výrazů
s alternativami či vykřičníkem; žádné nejasné přijímání synonym. Enter při
neshodě vysvětlí kontrolu písmen/přízvuků/znamének, rozpracovaný text
se nepočítá jako obrázková chyba.

Zopakovat slovo během psaní zachová draft a skrytý zápis. Vypnutí Psaní
umožní přeskočit obtížný zápis. Při selhání či20s timeoutu zpětného audia
se zápis neschová, Další zůstane použitelný a replay dovolí opravu.
Přepnutí, odchod, změna filtru, bfcache i opakované stisky ruší staré časovače.
Při správném zeleném potvrzení replay/hint fázi nepřeruší. Volba žije pouze
v paměti návštěvy, reload vypne Psaní. Žádný nový zápis do localStorage,
žádná změna osobních A–D/obtížných; souhrn jen počítá úspěšné zápisy/nápovědy.

## Ověření a omezení

-38 Node scénářů skutečné galerie/profilů/procvičování PASS (původních29+9).
- Zkoušené diakritické caffè/lunedì/perché/città, NFC/IME, dvojité souhlásky,
  apostrofy, úplná/částečná shoda, chybné Enter, hint499/500ms a opakování,
 600ms uzavření, replay, failed/stalled audio, vypnutí, návrat/bfcache a profily.
- Read-only nezávislá kontrola našla chybějící živé oznámení hintu, doplněno;
  jiná reprodukovatelná závada nebyla nalezena.
- Skutečné Safari na Macu: zapnutí, start, chybný a správný obrázek, přechod
  po poslechu do prázdného pole, rozepsané ma, hint mai, návrat skrytí,
  dopsání i, správné potvrzení, zavření pole, fokus Další a další paese.
  Originální produkční okno nebylo měněno; vlastní testovací okno zavřené.
- Automatická doménová brána a shoda finálních zdrojů jsou v gate.json,
  gate_sources.json a completion.json soukromého vocabulary_it_writing_20261116.
- Skutečný iPhone/Android/VoiceOver nebyl převzat. Mobilní Safari může po
  asynchronním poslechu vyžadovat klepnutí do pole pro otevření klávesnice.
- Žádná nová hlasová výroba ani nové assety; stávající hlasy a filtry zachované.

## Oddělení předchozího vydání

Původní hra dd0ceade byla mezitím začleněná ee6d904d, zveřejněná a uživatelem
přijatá. Minulá jednorázová chyba načítání neprokazuje vadný obrázek:
všech1282 veřejných herních assetů (814 obrázků/miniatur a468 IT word MP3)
bylo dnes staženo HTTP200, přesně porovnáno a plně dekódováno bez závady.
Příčinu konkrétní události nelze bez jejího času a karty zpětně určit.
Staré vydání neopakovat. Nové Psaní vyžaduje samostatný pokyn p+n; Willův
současný main se při tomto vývoji nemění.
