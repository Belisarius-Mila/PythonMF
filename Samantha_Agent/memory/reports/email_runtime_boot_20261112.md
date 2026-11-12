# Hodinová pošta: start sdíleného App Serveru po restartu

## Aktuální provoz — 2026-11-12 09:14 CET

Oprava7f47a41f je publikovaná a nasazená v Cockpitu; původní p+n
cfc1c1b1375eb5c46143c98eed93bc38 completed, push/deploy confirmed,
3520 testů PASS, smoke5/5 a protected_services_unchanged=true.
Po Mílově přesné globální větě je vlastní hodinová služba registrovaně
upgradovaná8c83e93b→7f47a41f, installed/owned/loaded/enabled. První
kontrola09:12:45 CET již dokončený slot správně neopakovala: already_completed,
0 nových posouzení. Celý business otisk, nastavení a modelové role shodné,
stará kopie i servisní záloha zachované.

Skutečná instalovaná kopie:311 souborů přesně podle manifestu, readiness bez
blokátorů. Na izolovaném socketu ověřen nový start a převzetí stejného PID
přímo přes instalovaný approved_selection, Terra/high, bez thread/start
a turn/start a bez zásahu do produkčního socketu.
Skutečný reboot/wake po upgradu neprovedený; dál běžný hodinový provoz.
Podrobnosti reports/email_runtime_boot_20261112.md, soukromé bezpečné
účtenky data/private/email_runtime_boot_20261112/.


Datum: 2026-11-12 08:32 CET

## Příčina a rozsah

Mac bootoval12.11.01:16, první ranní clamshell sleep07:05. E-mailový
LaunchAgent je loaded/owned/enabled a opakuje kontrolu po60s. Před opravou
chyběl jeho sdílený app-server socket, readiness instalované8c83e93b hlásila
jen appserver_socket_unavailable; poslední dokončený slot11.11.22:00.
Terminálové CLI používají jiné spojení, jejich start tuto závislost neobnovil.

## Změna

- Modelový výběr služby po schválení role zajistí stejný sdílený server,
  aniž otevírá Human–Adam či vytváří thread/turn.
- Start Cockpitu i e-mailového procesu chrání společný stabilní souborový
  zámek. Nový server zachovává start_new_session=True a privátní Unix socket.
- Živý server se použije; nedostupný existující socket není oprávnění ke
  kill/unlink/retry modelového tahu. Status/readiness se nemění na aktivaci.
- Servisní prepare ověří místní podmínky před novým startovacím vedlejším
  účinkem. Registr workflow tento účinek výslovně uvádí.

## Ověření

166 cílených testů PASS: procesový zámek, souběh samostatných controllerů,
role před startem, závislost před katalogem, bez retry po chybě, noční/zakázaný
a dokončený slot, rezervace a nejistá modelová operace, servisní upgrade
a zachování stavu. Plná brána PASS:3520 testů,31 SKIP,585,445s (unit krok591,4s).
Log logs/email_runtime_boot_full_gate_20261112.log; syntaxe i whitespace PASS.

Skutečné izolované CLI: dva souběžní klienti, jeden start a jedno převzetí,
stejný owner PID, detached procesní skupina, katalog10; žádný thread/start
a turn/start. Testovací server korektně ukončil pouze jeho vlastní controller.
Manuál launchd.plist na tomto Macu potvrzuje ukončování zbývajících procesů
stejné procesní skupiny; start_new_session ponechává server v oddělené skupině.

## Dnešní provozní obnova a publikační hranice

Registrovaný resume obnovil sdílený server a zachoval celý business otisk,
hodnoty nastavení i policy digest. Bez ručního ticku, nového testovacího
modelového tahu, SMTP nebo kalendáře. Původní hodinový runtime8c83e93b
zůstává nainstalovaný; model/list prošel v něm i v nové místní kopii Terra/high.
Přirozený slot08:00 se dokončil v08:32:01 CET:4 nové zprávy,4 běžná posouzení;
health completed bez error_type. Předchozí mezilehlý failed byl ještě z přechodu
před obnovením, další trvalá katalogová chyba se nepotvrdila.

Kód je zatím lokální. Míla následně výslovně schválil po dokončení commitu
registrované p+n celého čekajícího balíčku pro project-email-cases → Cockpit.
Přepnutí vlastního LaunchAgentu tím nezískává přesnou systémovou potvrzovací větu. Servisní upgrade použije pause/prepare/upgrade
a vyžaduje přesnou větu z global_safety_brake.md. Žádná nová modelová role,
rozpočet, plánovač ani změna soukromých podkladů. Skutečný reboot/wake po
aktivaci nové kopie nebyl proveden; samotné lokální testy jej nenahrazují.
Samostatný e-mailový TVBCP nebyl dohodnut, nový nevzniká; sdílený runtime
zapsaný do existujícího Human–Adam handoffu a TVBCP.


## Schválené registrované p+n

Request `email-runtime-boot-20261112-v1`, přesné job ID `cfc1c1b1375eb5c46143c98eed93bc38`, project-email-cases → Cockpit.
Po lokálním commitu jediný submit_release(wait=True); centrální role se
nemění. Výsledková autorita je původní strojová účtenka a
`logs/email_runtime_boot_release_20261112.json`. Tento předávací snapshot
sám nepotvrzuje push/deployment; závěr ověří Adam z konečné účtenky.
Během vydání žádná změna main ani vlastní instalované hodinové kopie.

Servisní plán po commitu sváže přesný source_head, manifest a původní
nastavení. Dočasné pause/prepare/resume nepřepisuje systémový plist;
upgrade samotný vyžaduje přesnou globální potvrzovací větu.


## 2026-11-12 09:14 CET — Oprava nasazená i do vlastní hodinové služby

**Hotovo:** Hlídač nové pošty má ve vlastní běžící instalaci opravu automatického startu chybějícího sdíleného serveru. P+n nasadilo7f47a41f do Cockpitu; po přesné globální větě registrovaný upgrade přepnul také vlastní hodinovou kopii8c83e93b→7f47a41f.

**Rozhodnutí:** Míla výslovně schválil p+n a následně dodal přesnou větu pro připravený servisní upgrade. Model, hodinový režim, business stav a nastavení zůstávají stejné. Žádný nový testovací modelový tah, e-mailové odeslání ani kalendářový zápis.

**Další krok:** Běžný hodinový provoz; při příštím skutečném reboot/wake ověřit samostatné obnovení bez otevření chatu.

**Navrhované další kroky:** Pokračovat původní samostatnou etapou UI hlídání záležitostí; její automatický monitor se tímto neaktivoval.

**Technický důkaz:** P+n cfc1c1b1375eb5c46143c98eed93bc38 completed,25 commitů, publikační brána3520 PASS/642,8s, smoke5/5, code stamp bfe18afa86e45de4, chráněné služby při vydání shodné. Následný upgrade installed/owned/loaded/enabled, první check09:12:45 CET already_completed/0. Úplný business digest, všechny dosavadní položky, hodnoty nastavení a celý JSON rolí shodné.311 instalovaných souborů přesně podle manifestu; izolovaný test nové instalace skutečně spustil a znovu použil stejný server bez thread/start nebo turn/start. Report reports/email_runtime_boot_20261112.md; důkazy upgrade_result.json a installed_verification.json jen ve jmenované private složce. Fyzický reboot/wake po aktivaci nebyl proveden.

Doplňující ověření: start a převzetí stejného App Serveru prošly také v přesném
PATH a omezeném prostředí nainstalovaného LaunchAgentu. Instalovaná Terra/high,
0 thread/start a turn/start, produkční socket beze změny; důkaz
service_environment_verification.json ve stejné soukromé složce.
