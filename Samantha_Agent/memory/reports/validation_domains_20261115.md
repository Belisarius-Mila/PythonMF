# Menší validační běhy — 15.11.2026

Míla schválil doménové testování po dotazu, proč kalendářová oprava vyvolala
3972 testů. Cílem je řádově méně testů při běžné úpravě, s úplnou regresí
pro společnou infrastrukturu a denně v CI. Nejde o plošné odstranění ochrany.

## Výsledek a měření

Příklad existujícího `app/calendar_writer.py`, analyzovaný nad místním zdrojem:
program vybral22 modulů /282 testů včetně malého bezpečnostního základu,
kalendáře, e-mailového zápisu, obnovy, editace/mazání, úkolů a HTTP/UI.
Skutečný diagnostický běh:282/0 chyb/0 skip,39,283s unit část;56,874s celkem
včetně4,619s výběru, importů a všech dosavadních statických kontrol.
Předchozí kalendářová plná brána:3972/0 chyb/31 skip,621,309s unit část,
645,4s celkem. Počet klesá14,1×, tento celý běh přibližně11,3×.

Jde o měření doménového případu, nikoli publikační důkaz tohoto balíčku.
Aktuální balíček mění samotnou politiku/CI a musí projít plnou branou.
Nový kalendářový v2 helper v předchozím čekajícím commitu navíc vyžaduje
první plné ověření. Nelze pro aktuální společný batch tvrdit pouze282 testů.

Čas56,874s nezahrnuje místní publikační účtenku. Jeden skutečný úplný otisk
obsahu/prostředí trval15,459s; místní runner ověřuje vstupy před i po běhu.
Provozní čas proto může být vyšší než minuta. Po novém plném základu následuje
řízené měření stejného místního runneru nad dočasným komentářem v již známém
kalendářovém zdroji, s přesným vrácením původních bajtů/režimu/mtime; výsledek
bude v soukromé completion.json. Původní plný důkaz platí pouze pro nezměněné
finální vstupy. Toto měření nic nepushuje, nenasazuje ani nezapisuje do kalendáře.

94 cílených regresí prošlo: podpis/cache, doménové závislosti, starý runtime,
CI volba, frontendy a izolace fixture. Poslední úplná brána a přesné otisky
všech finálních souborů jsou pouze v soukromé
`data/private/validation_domains_20261115/completion.json` a místní HMAC účtence.
Tento verzovaný dokument se po ní nemění; bez skutečného PASS není krok uzavřený.
Další cílené Git/checkpoint/release regrese a jejich časování jsou ve stejné
soukromé složce (`git_fixture_timings.json`, `git_fixtures.log`).
Čtyři Git moduly106,396s oproti historickým190,805s; nejde o řízený A/B.
Přímé pomocné měření osmi příprav ve stejném procesu:0,866s opakovaná
inicializace,0,454s procesový seed+kopie. Jde o menší doplňkovou úsporu;
hlavní zrychlení přináší výběr282 potřebných testů.

## Změny a hranice

- Pevná mapa12 domén plus společný základ; reverzní Python importy přidávají
  skutečné konzumenty. Explicitní kompoziční hranice mají smluvní testy.
  Cizojazyčné/runtime vazby zůstávají v revidované mapě.
- Neznámý konzument, dynamický import v měněném modulu, nejistota, nový
  spustitelný soubor nebo společný kritický zásah znamená plnou sadu.
  Výběr se neomezuje pevným počtem; širší změna může překročit300 testů.
- Stejná autorita pro místní runner i CI. GitHub bere celý event diff bez
  path filtrů, denní02:17 UTC a ruční běh jsou plné. CI nevydává místní
  publikační důkaz. Místní podepsaný plný základ stále expiruje po24h;
  samotná noční CI ho neprodlužuje. Žádný nový místní plánovač.
- Git testovací seed se vytváří jednou za proces; každý test dostává úplnou
  nezávislou kopii bez hardlinků. Regrese mění commit/index/soukromý syntetický
  soubor v jedné kopii a ověřuje dvě jiné kopie i nezávislé objekty.
- Odstraněn jeden křehký test SHA/délky/počtu řádků vykresleného HTML.
  Stávající kompoziční kontrola nyní ověřuje vložené CSS/JS/moduly a nevyplněné
  zástupné symboly; funkční Node scénáře zůstávají. Žádné testovací soubory
  ani desítky bezpečnostních scénářů se nemažou. Nové regrese chrání selektor.
- V cílené mapě v1 byly dva již existující moduly mimo plný registr/CLI choices:
  memory_truth_audit a book_cover. Nyní jsou dostupné i v plné sadě a prošly.
  Celkový počet registrovaných testů proto může mírně vzrůst; šetří se potřebný
  běh pro konkrétní změnu, nikoli umělé číslo celé sady.

První v1 politika byla dříve skutečně vydaná v38a33532 (release účtenka
0203d0fbaf6cae4b993c7fa4670a9bb6); současná v2 je nový místní vývoj.
Kalendářový f2b56fa3 zůstává čekající. Tato implementace nemění běžící Cockpit,
EventKit helper, Mac oprávnění, poštu, kalendář ani Data. Žádný push/deploy.
Další krok je samostatně potvrzené p+n; noční CI začne fungovat až po pushi.
