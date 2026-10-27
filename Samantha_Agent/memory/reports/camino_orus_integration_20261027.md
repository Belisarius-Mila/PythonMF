# Camino — Orus ve střižně, tempo −10 %

Stav: 2026-10-27, místní vývoj, bez nového p+n. Proud: project-camino.

## Výsledek

Míla přijal výslovnost a příjemnost českého cs-CZ-Chirp3-HD-Orus. Původní
tempo bylo rychlé; z místního porovnání 1,00 / 0,90 / 0,85 vybral 0,90.
Nové čtení fotografie používá Orus a stejné místní FFmpeg atempo=0.9 se
zachováním výšky hlasu. Rychlost nezávisí na cloudové podpoře speakingRate.

Před vytvořením UI ukazuje cenu a checkbox pro konkrétní text. Souhlas se
spotřebuje jedním pokusem a editace jej ruší. Cena vychází z Unicode znaků
včetně mezer a sazby 30 mikroUSD/znak, bez předpokladu zbývající bezplatné
kvóty. Pro 6000 znaků je to 0,18 USD. Zobrazení se zaokrouhluje nahoru na
tři desetinná místa; server ověřuje přesnou částku v celých mikroUSD,
hlas, tempo a celý text proti uložené revizi.

## Bezpečnost a úplnost

- Celý komentář do 6000 znaků se beze ztráty dělí do částí nejvýše 5000
  UTF-8 B. Čeština, emoji, mezery a nové řádky zůstávají ve stejném pořadí.
  Google dostává jen potvrzený text; fotografie/GPS ani další deník neodesílá.
- Povolení a současný přesný text se kontrolují před každým přenosem,
  po čekání na autentizaci a před připojením hotového zvuku. Změna nebo zámek
  zastaví další část či připojení. Již odeslaný text nelze odvolat.
- Oficiální google-auth obsluhuje servisní účet. Token je jen v paměti,
  TLS ověřené, endpointy pevné. Readiness čte pouze metadata místního klíče
  a nezahajuje síťové spojení. Chyby neobsahují klíč, token, cloudovou
  odpověď ani text. Přístupový soubor musí mít bezpečný vlastnický režim
  a žádný symlink v cestě.
- Každá část má jediný POST. HTTP chyba, timeout ani nejistý výsledek se
  neopakují. Před přenosem existuje místní záznam; stejné ID nedokončeného
  pokusu je blokované, hotové ID vrací ověřený výsledek. UI blokuje dvojklik
  již před čekáním na uložení. Nový pokus vyžaduje nový výslovný souhlas.
- Části se spojí, zpomalí a převedou na soukromé AAC/M4A; celý zvuk se
  dekóduje a změří. PCM části jsou dočasné a po zpracování nezůstávají jako
  další trvalé kopie. Účtenka uchová hlas, tempo, text/hash a potvrzenou cenu.
- Historie, koš, import MP3/WAV a starší filmy zůstávají funkční. Starší
  čtyřpoložkový protokol zůstává místní Zuzana pro starší klienty. Nové UI
  vždy předává cloud_consent; při chybě Orusu nevolá náhradní hlas.
  Nová řeč se do filmu nezařadí automaticky.

## Skutečné ověření přístupu a poslech

Projekt camino-orus vytvořil Míla, TTS API Enabled doložené snímkem.
Ověřený klíč je jen v ignorované projektové credentials složce, soubor 0600
a adresář 0700. Žádná osobní e-mailová adresa, klíč ani token nejsou v tomto
zápisu. Fakturační konfigurace se vývojem neměnila. Trial kredit byl vidět
v konzoli; skutečné vyúčtování a zbývající kvóta NEOVĚŘENO.

Jediná schválená zkouška: 166 smyšlených znaků, při doložené sazbě
0,00498 USD před případnou kvótou, schválený strop 0,01 USD. HTTP 200,
MP3 44 736 B / 11,184 s, mono 24 kHz, full decode PASS, SHA-256
9368a96277fb5ec257e5ce0af466bd58fbf4c84840db7f9cfa4632dfcb7b6cc1.
Míla poslech potvrdil; zvolený místní derivát 0,90 má 12,414 s.
Tento souhlas nepovolil skutečné soukromé texty ani další neomezené náklady.

Nový adaptér s google-auth 2.62.0 v projektovém venv byl živě ověřený
přihlášením a read-only seznamem českých hlasů. Vývojové audio požadavky
používají pouze syntetické mock odpovědi a místní WAV. Od první zkoušky
žádná další cloudová syntéza ani skutečný soukromý text.

## Testy

- 100 cílených kontrol PASS / 62,419 s: adaptér, filmové vrstvy/editor a
  frontend. Nový HTTP test souhlasu/origin/idempotence navíc PASS / 0,770 s.
- 13 nových kontrol pokrývá UTF-8/6000 emoji, souhlas s přesným textem,
  cenou, hlasem a tempem, oprávnění/symlinky klíče, oficiální auth a token
  endpoint, timeout/403 bez retry a úniku, skutečné spojení/zpomalení/full
  decode, zastavení při změně povolení, historii/replay, neplatný souhlas
  bez přenosu, nejasný pokus bez retry, změnu textu během hlasu a HTTP origin.
- DOM scénář ověřuje cenu a souhlas, jeho spotřebování a zrušení editací,
  dvojklik, viditelný chybějící přístup, opožděná čtení, historii a import.
- Plná brána: 2256 PASS / 482,110 s unit část, celkem 496,501 s.
- Složený HTML kontrakt: 627842 znaků, 11816 řádků, SHA-256
  768f4c4f47414927c3a1974f63b30b0d0199bba8daacb31224bc26cded16ce0a.

## Hranice a další krok

Pouze místní vývoj. Bez nového push/nasazení, restartu služby či instalace
iPhonu. Originály, skutečné projekty a staré nahrávky nebyly měněné.
Poslech hlasu/tempa přijatý; fyzické ovládání nového souhlasu a nový komentář
skutečné fotografie ve vydané střižně zůstávají NEOVĚŘENO.

Plná brána a závěrečná statická kontrola prošly; místní checkpoint obsahuje tento zápis. Až na samostatné zadání Luna p+n, potom
přejímka fotografie, souhlasu, celé řeči, historie a umístění ve filmu.

Oficiální podklady ověřené 27. 10. 2026:
https://cloud.google.com/text-to-speech/pricing ;
https://docs.cloud.google.com/text-to-speech/quotas ;
https://docs.cloud.google.com/text-to-speech/docs/reference/rest/v1/text/synthesize ;
https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.service_account.html .

Závěrečná klasifikace endpointu v registru: external_ai; souhlas se váže na konkrétní text a cenu. Po této metadatové úpravě 2 cílené kontroly registru PASS; závěrečná statická brána PASS / 8,406 s.

## 2026-10-27 18:23 CET — První p+n zastavené a oprava

Účtenka 8855740144231119c4ac01e1d8de5657, stav attention, push_state uncertain, deployment not_started. Publikační gate v profilovém workspace: 2256 testů / 1 ERROR / 18 skipped / 438,979 s. Jediná chyba byla v závěrečném probe uvnitř nového testu, který nepředal executable; službový PATH nezahrnuje ffprobe. Produkční adaptér již všude používá media_binary a nemění se. GitHub přímo čtecím dotazem zůstal 4dc65832, tedy žádný publish ani nasazení.

Oprava: test používá explicitní media_binary("ffprobe") a sám vynucuje /usr/bin:/bin:/usr/sbin:/sbin; modul 13 PASS. Předchozí místní plná brána je pravdivý terminálový důkaz, ne náhrada chybějící publikační brány. Po statické kontrole a checkpointu nový běh Lunou dle Mílova dřívějšího výslovného pokynu po opravě opakovat do úspěchu. Původní nejistá účtenka se neopakuje. Žádná další syntéza ani soukromé texty.
