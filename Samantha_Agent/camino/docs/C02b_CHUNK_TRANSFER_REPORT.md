# C02b — report experimentu částí a iOS fronty

Datum: 2026-09-17

## Výsledek

C02b je zahájené a má dva lokální checkpointy. Syntetický receiver přijímá
výchozí 8MiB části, trvale eviduje manifest a bezpečně uložené části, po
přerušení vrací přesný seznam chybějících indexů a teprve po sestavení a
serverové kontrole celkové délky a SHA-256 vytvoří jediný objekt a účtenku.

Stejná relace, část i finalizace jsou idempotentní. Jiná identita nebo jiné
bajty jsou konflikt bez přepsání. Chybný hash části, chybějící část a chybný
celkový hash nedostanou potvrzení. Ztracenou odpověď finalizace lze nahradit
dotazem na stav existujícího Assetu.

Čistý Swift model fronty odděluje lokální byte progress od serverového důkazu.
Po relaunchi bere serverový snapshot jako autoritu, při nedostupné síti říká
čekání a stav `Ověřeno na Macu` dovolí jen serverové `verified`. Jednorázové
mobilní povolení se váže na konkrétní dávku a neplatí pro nové médium.

Druhý checkpoint přidal oddělenou aplikaci `Camino Transfer Test` 0.4.0 (1).
Vytváří pouze syntetický soubor 96 MiB + 257 B, vede trvalý journal a pro jednu
background `URLSession` připravuje nejvýše dvě 8MiB části. Token ukládá do
Keychain, vyžaduje HTTPS a nemá oprávnění k Fotkám, mikrofonu ani datům Camino
Audio. Po návratu porovnává frontu se serverem a nepoužívá veřejný fallback.

## Automatické ověření

- Python C02b receiver: 10/10 PASS.
- Swift transfer core: 18/18 PASS.
- iOS simulátor UI: 1/1 PASS; vytvoření 96MiB syntetické dávky, viditelný
  journal/progress a výchozí zákaz mobilních dat.
- Nepodepsaný Debug build pro `generic/platform=iOS` arm64: PASS.
- C02a regrese: 10/10 PASS; plná projektová brána: 1705/1705 PASS.
- Pokrytý syntetický velký soubor má dvě plné 8MiB části a krátký konec. Test
  nejprve odešle části 0 a 2, po dotazu doplní jen část 1 a ověří jediný
  výsledný objekt se shodným hashem.
- Samostatně jsou pokryté konflikty, chybné hashe, chybějící část, stav
  `verifying`, idempotentní retry, ztracená odpověď, zákaz veřejného bindu,
  relaunchová reconciliace, scope mobilní dávky, trvalý journal, strop dvou
  připravených částí a odmítnutí neplatného serverového snapshotu.

Plná projektová brána je samostatný povinný důkaz tohoto změnového kroku.

## Vazba na akceptační testy

- T043: lokálně doloženo doplnění chybějící části, konečný hash a jediný objekt;
  skutečné přerušení iPhone sítě NEPROVEDENO.
- T047: aplikace má background souborové úlohy a po relaunchi znovu porovnává
  server; zámek a nucené ukončení na skutečném iPhonu NEPROVEDENO.
- T048: UI má pravdivé čekání bez veřejného fallbacku; cizí Wi-Fi, captive
  portal, přechod sítě a nedostupný tailnet NEPROVEDENO.
- T049: trvalý grant je omezený na jednu dávku a nová dávka vzniká bez něj;
  skutečný mobilní přenos NEPROVEDENO.
- T050: server i UI drží `Ověřuji` po dosažení 100 % bytů; řízené zadržení
  serverového ověření na fyzickém iPhonu NEPROVEDENO.

Žádný z T043/T047–T050 proto zatím není označen PASS.

## Rizika a hranice

- Background `URLSession` je zkompilovaná a UI ověřené jen v simulátoru;
  skutečné plánování iOS, zámek, force quit a síťové přechody jsou neověřené.
- Receiver je izolovaný standard-library experiment, ne produkční FastAPI,
  databáze, launchd služba ani záloha.
- Prototyp při každém stavovém dotazu znovu hashově kontroluje přijaté části;
  je záměrně jednoduchý, ne výkonově hotový.
- Výchozí experimentální maximum je 512 MiB a neříká nic o budoucím
  produkčním limitu videa.
- Nebyla změněna Tailscale Serve konfigurace, nic nebylo vystaveno veřejně,
  aplikace nebyla instalována a nebyla použita reálná média.

## Další krok

Připojit a odemknout iPhone, lokálně podepsat a nainstalovat oddělenou aplikaci
bez odinstalace Camino Audio. Potom otevřít privátní HTTPS cestu pouze po dobu
řízeného testu a postupně provést T043 a T047–T050. Žádný scénář není PASS,
dokud není doložen na fyzickém telefonu.
