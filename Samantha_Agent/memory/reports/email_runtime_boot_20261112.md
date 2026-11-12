# Hodinová pošta: start sdíleného App Serveru po restartu

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
