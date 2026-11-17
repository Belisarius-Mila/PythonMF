## Integrační doplnění Willa17.11.2026

Klientský osobní režim je hotový v1e7c8bd7,464/203 ověřeno. Datovy
obsahový a předávací commity a5f11f68/c07df87b jsou společně začleněné;
nový pokyn Míly autorizuje p+n celého balíčku. Soukromý seznam se nepublikuje.
Doklad vydání: private vocabulary_fr_personal_hard_release_20261117/completion.json.
Fyzický import u Jany zůstává samostatný. Níže je Datův uzavřený doklad.

# Vocabulary FR — Janina obtížná slovíčka bez profilů A–D

Stav: obsahový převod a soukromé předání do sdíleného iCloudu hotové.
Míla potvrdil uložení označení v prohlížeči bez A–D a PIN. Klientské vydání
a fyzický import u Jany tento zápis nepotvrzuje.

Hotovo: nový čistý obsahový převod používá trvalé UID a původní HT.
Schválené vynechané duplicity slučuje pomocí OR, stejně jako katalog.
Výstup má samostatný kontrakt personal-hard-backup, bez A–D, PIN, naučených
slov, textů nebo pevného seznamu vybrané slovní zásoby. Všechna slovíčka tak
mohou zůstat implicitním základem i po pozdějším rozšíření katalogu.

Soukromý převod skutečného zdroje je uložený v Downloads i ve sdílené
podsložce Web_Jana vedle původních Janiných dat. Nezávislé porovnání
každého původního zaškrtnutí s katalogovými identitami a aktuálním obsahem
main prošlo. Zdrojový CSV je hashově nezměněný; žádná osobní označení nejsou
v Git ani docs. Podrobný doklad: private vocabulary_fr_jana_hard_20261117.

Rozhodnutí: Míla chce obtížná slova Jany nad celým slovníkem bez nutnosti
profilů A–D a PIN. Osobní stav zůstává soukromě v prohlížeči, nikoli ve
veřejném payloadu. Výslovně zadal definovat a provést předání souboru přes
stávající sdílený adresář. Úvodní soubor slouží k jednorázovému importu;
pozdější úpravy se do něj automaticky nezapisují. Přenos na jiné zařízení
použije nejnovější export, který Jana uloží do podsložky Zalohy.

Další krok: Will jako vlastník klienta převezme nový kontrakt a doplní
Všechna / Jen obtížná i editor nad celým slovníkem. Stávající data A–D se
zachovají. Předání v Downloads popisuje import s náhledem a potvrzením,
lokální uložení, průnik s 18 okruhy a všechny učící režimy. Nové krátké TXT
doplňuje konkrétní sdílené umístění a potvrzené rozhodnutí, aby nebylo třeba
Míly znovu žádat o stejnou volbu.

Technický důkaz: šest nových syntetických obsahových testů PASS; úplnou
registrovanou bránu původního převodu dokládá podepsaná účtenka se 147 PASS.
Skutečný sdílený JSON je bajtově shodný s ověřeným importem. Willův aktuální
parser přijímá všechna označení, nezná žádné cizí UID a rozlišuje celý slovník
od obtížných. Kontrola parseru neměnila prohlížeč. Návod používá názvy ovládání
z aktuálních klientských zdrojů. Foundation u JSON i návodu potvrdilo
ubiquitous=true, uploaded=true, uploading=false, bez chyby. Janino zařízení
ani fyzický import zatím ověřené nejsou. Původní CSV zůstal SHA shodný.
Kanonický handoff, existující TVBCP a projektovou paměť nadále zapisuje Will;
jejich doplnění je součástí tohoto předání. Žádný Git push ani webové nasazení;
provedený přenos soukromého souboru do sdíleného iCloudu byl výslovně zadaný.
