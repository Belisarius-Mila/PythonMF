# C02b — první report experimentu částí a fronty

Datum: 2026-09-17

## Výsledek

C02b je zahájené a má první lokální checkpoint. Syntetický receiver přijímá
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

## Automatické ověření

- Python C02b receiver: 9/9 PASS.
- Swift transfer core: 9/9 PASS.
- Společně s nezměněnou C02a regresí: 28/28 cílených testů PASS.
- Pokrytý syntetický velký soubor má dvě plné 8MiB části a krátký konec. Test
  nejprve odešle části 0 a 2, po dotazu doplní jen část 1 a ověří jediný
  výsledný objekt se shodným hashem.
- Samostatně jsou pokryté konflikty, chybné hashe, chybějící část, stav
  `verifying`, idempotentní retry, ztracená odpověď, zákaz veřejného bindu,
  relaunchová reconciliace a scope mobilní dávky.

Údaj 28/28 se potvrdí společným cíleným během před checkpointem; plná
projektová brána je samostatný povinný důkaz tohoto změnového kroku.

## Vazba na akceptační testy

- T043: lokálně doloženo doplnění chybějící části, konečný hash a jediný objekt;
  skutečné přerušení iPhone sítě NEPROVEDENO.
- T047: model po relaunchi nepředpokládá doběhnutí a znovu porovná server;
  zámek a nucené ukončení skutečné aplikace NEPROVEDENO.
- T048: model má pravdivé čekání bez veřejného fallbacku; cizí Wi-Fi, captive
  portal a přechod sítě NEPROVEDENO.
- T049: grant je omezený na jednu dávku; skutečný mobilní přenos NEPROVEDENO.
- T050: server i model drží `verifying` po dosažení 100 % bytů; skutečné iOS UI
  NEPROVEDENO.

Žádný z T043/T047–T050 proto zatím není označen PASS.

## Rizika a hranice

- Swift package je čistá logika, nikoli `URLSession` klient nebo iOS UI.
- Receiver je izolovaný standard-library experiment, ne produkční FastAPI,
  databáze, launchd služba ani záloha.
- Prototyp při každém stavovém dotazu znovu hashově kontroluje přijaté části;
  je záměrně jednoduchý, ne výkonově hotový.
- Výchozí experimentální maximum je 512 MiB a neříká nic o budoucím
  produkčním limitu videa.
- Nebyla změněna Tailscale Serve konfigurace, nic nebylo vystaveno veřejně a
  nebyla použita reálná média.

## Další krok

Navázat druhým checkpointem C02b: připojit k tomuto kontraktu malý nativní iOS
harness se souborovými úlohami `URLSession`, trvalou lokální frontou a nejvýše
dvěma připravenými částmi. Teprve jeho build a instalace mohou otevřít řízenou
fyzickou přejímku T043 a T047–T050 na iPhonu a cizí síti.
