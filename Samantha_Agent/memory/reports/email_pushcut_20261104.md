# Pushcut — upozornění na důležitou poštu

## Stav 2026-11-04 23:24 CET

Míla zvolil dokončit zvukové upozornění s odkazem před spuštěním hodinové
služby a výslovně schválil variantu Pushcut. Nový kód je lokální;
předchozí provozní příprava již byla vydaná po 77f7e12f (Terra p+n
742135a3ba9990edc0afe6734d125166, 2368 PASS, smoke 5/5, GitHub CI
41922126605 success, živý stamp a přesný obsah stránky ověřené).

## Uživatelský průchod

1. Na iPhonu nainstalovat Pushcut a povolit oznámení/zvuk.
2. Vytvořit oznámení `SamanthaEmail`, text „Zkontroluj e-maily v Cockpitu.“,
   vybrat rozpoznatelný zvuk a jako Default Action nastavit URL na HTTPS
   stránku E-maily k řešení. Zvuk a odkaz lze zkusit místním Test Notification.
3. Po vydání otevřít E-maily k řešení → Upozornění na iPhone. Vložit Copy URL
   z Pushcutu a ověřený odkaz Cockpitu, zvolit upozorňování a uložit.
4. Použít Poslat test na iPhone. Tato výslovná akce funguje i bez běžící
   hodinové služby; API přijetí nenahrazuje poslech a klepnutí na telefonu.

Text, zvuk a odkaz se nastavují přímo v Pushcutu. Backend posílá prázdný
POST na konkrétní webhook, bez dynamických JSON přepisů. Podle
[dokumentace](https://www.pushcut.io/support/notifications) a
[nabídky](https://www.pushcut.io/) tím využíváme předdefinovanou notifikaci
bez placeného dynamického obsahu. Samovolné otevření Cockpitu se neslibuje;
stránka se otevírá klepnutím na notifikaci.

## Chování cyklu a uložení

- Nová úspěšně posouzená důležitá karta a její záznam do fronty vznikají
  v jedné transakci stávajícího private JSON repository.
- Jeden hodinový klíč sdružuje nové důležité položky do jednoho upozornění.
  Další položky v už upozorněné hodině nezvoní znovu; nová hodina má vlastní
  záznam. Staré karty se při zapnutí nepřidávají zpětně do fronty.
- Nízká důležitost, chyba modelu a už vyřízené karty upozornění nevyvolají.
  Vypnutí či změna cíle přeskočí dosud neodeslanou starou frontu.
- Před POST se trvale zapíše `sending`. HTTP 200 znamená `accepted` API,
  výslovné 4xx `rejected`; jiné/neověřitelné výsledky `delivery_unknown`.
  Pád po rezervaci pokusu se po restartu označí jako nejistý. Žádný
  automatický retry, včetně testu se stejným request ID.
- Testy jsou svázané s revizí nastavení; změna webhooku nebo odkazu
  nezobrazuje starý úspěšný test jako ověření nového nastavení.
- Síťové volání drží pouze vlastní dispatch zámek. Vyřizování jiných karet
  mezitím zůstává dostupné. Souběžný dispatcher neposílá druhý požadavek.
- Hodinový registrovaný vstup odesílá čekající frontu i při opakovaném
  ticku už dokončené hodiny, bez nového IMAP/modelového průchodu.

Webhook je uložený pouze v existujícím ignorovaném private stavu; přehled
a odpovědi nastavení vracejí jen příznak připojení. Chybové texty nevracejí
transportní URL/tělo. Příjemce a skutečný webhook nejsou součástí Git zápisu.
Přesměrování požadavku se nenásledují. Nová závislost ani služba nevznikla.

## Ověření a otevřené kroky

- 147 cílených testů PASS: 17 Pushcut scénářů, HTTP nastavení/test,
  JS formulář/dvojklik/polling, dosavadní cyklus/editor/SMTP a registry.
- Výběr posledního výsledku používá čas testu, nikoli pořadí klíčů, které
  repository při zápisu řadí abecedně. Samostatná regrese FAIL→PASS.
- Živý čtecí HTTPS audit ověřil správný Cockpit. Do jeho private nastavení
  byl připraven pouze odkaz s vypnutými upozorněními; skutečný webhook
  chybí. Čtyři původní vyřazené/ignorované položky a kurzory zachované.
- Důkazy: `logs/email_pushcut_targeted_20261104.log`,
  `logs/email_pushcut_gate_20261104.log`,
  `logs/email_pushcut_local_status_20261104.log`.
- Prohlížečový ovládací host při čerstvém pokusu nedostupný; funkční JS/HTTP
  testy nejsou vizuální přejímkou na Macu či fyzickým iPhone testem.
- První plná brána: 2385 scénářů, jediný FAIL byl starý pevný otisk
  rozšířené e-mailové stránky (14832 → 18957 znaků, 223 → 290 řádků).
  Fixture aktualizován na skutečnou složenou stránku, kontrola ponechaná;
  následných 147 cílených testů včetně celého frontend kontraktu PASS.
  Čtecí oprava posledního testu má navíc vlastní regresi FAIL→PASS.
  Plnou bránu znovu provede registrované p+n podle LL-079 před publikací.
- Míla během dokončování výslovně schválil p+n; po lokálním commitu se
  předá Terře bez další žádosti. Živý POST do Pushcutu, fyzický zvuk,
  klepnutí na iPhonu ani hodinový provoz zatím nejsou potvrzené.
- Další krok: samostatné vydání a propojení skutečné notifikace, následně
  fyzická přejímka. Potom řízený instalátor/provozní profil a aktivace.
  Kalendář/CalDAV a potvrzená archivace/metadatová přejímka dál čekají.
