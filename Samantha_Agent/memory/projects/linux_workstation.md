# Linux / instalace a konfigurace

## Cíl

Bezpečně využít starší stolní počítač s Linux Mintem pro běžnou práci,
výukové aplikace a starší hry. Současně může fungovat jako soukromý klient
Macového Cockpitu přes Tailscale. Není zatím druhým produkčním serverem
Samanthy ani náhradou Macu.

## Výchozí hardware

- Intel Pentium G4560, Kaby Lake, 2 jádra / 4 vlákna, 64 bitů
- 8 GB RAM
- původní 1TB klasický HDD
- integrovaná Intel HD Graphics
- samostatná AMD Radeon R5 435
- zapnutá hardwarová virtualizace
- Kingston A400 480 GB SATA SSD byl zvažovaný, ale pro současnou instalaci
  nebyl potřeba; o upgradu se rozhodne až podle reálné rychlosti

## Aktuální stav k 2026-08-27

- Potřebná data z původních Windows byla před instalací ručně zazálohována.
- Návrat k Windows se neplánuje; Linux Mint je nainstalovaný a běží na původním
  HDD, který byl připraven ke smazání.
- Základní práce v Linuxu funguje. LibreOffice je dostupný a byl otevřený.
- Tailscale je na Linuxu nainstalovaný a PC je připojeno do stejného soukromého
  tailnetu jako Mac.
- Jediný Cockpit nadále běží na Macu na `127.0.0.1:8770`. Tailscale Serve jej
  zpřístupňuje přes soukromé HTTPS pouze uvnitř tailnetu; Mílův výpis potvrdil
  označení `tailnet only` a proxy na lokální Cockpit.
- Cockpit se na Linuxu úspěšně otevřel. Linux je nyní jeho vzdálený klient;
  app-server se na Linuxu nespouští ani se přímo nevystavuje do sítě.

## Kanonická rozhodnutí

- Mac zůstává hlavní autoritou Samanthy, Apple integrací a soukromých dat.
- Staré PC nebude nyní hlavním vývojovým strojem Samanthy. Jeho praktická role
  je běžné používání, dětské výukové aplikace, starší hry a soukromý přístup
  k Macovému Cockpitu.
- Samostatný linuxový server nebo testovací uzel Samanthy je pouze budoucí
  možnost. Neinstalovat na něj v první fázi API klíče, e-mailové či kalendářové
  automatiky ani privátní datové úložiště.
- Cockpit zůstává jedinou Macovou instancí. Přístup z Linuxu používá HTTPS
  adresu Tailscale Serve bez veřejného Funnelu.
- Vývoj na Macu a Linuxu by musel používat Git pro kód a jednoznačnou autoritu
  dat. Dvě nezávisle zapisované kopie CSV se nesmějí tiše obousměrně slučovat.
- Linuxová varianta `vocab_trainer_fr.py`, její přenos dat a automatická
  synchronizace zatím nejsou implementované ani provozně ověřené.
- Herní Windows ve virtuálním stroji nejsou na 2jádrovém procesoru a 8 GB RAM
  vhodný základ. Rozšíření na 16 GB by pomohlo souběhu programů, ale neodstraní
  omezení procesoru a grafiky. Nové PC má smysl až pro konkrétní moderní hry;
  pro výuku a starší hry je rozumné nejprve využít současný Linux.

## Vhodné současné využití

- Firefox a běžné webové nebo výukové aplikace
- webmail nebo později Thunderbird; konkrétní účet se nastavuje jen přes
  podporované IMAP/OAuth přihlášení
- WhatsApp Web v prohlížeči nebo jako webová aplikace, nikoli neověřený klient
- LibreOffice pro dokumenty a tabulky včetně běžné práce se soubory XLSX
- GCompris jako první sada dětských vzdělávacích aktivit
- SuperTux jako lehká hra a jednoduchý test herního výkonu
- podle výsledku později SuperTuxKart, Kanagram, KHangMan nebo KLettres
- Macový Cockpit jako samostatná webová aplikace vytvořená nástrojem Web Apps

U náročnějších her zůstává hlavním omezením procesor a slabá grafika. SSD by
výrazně zrychlil start systému a načítání programů, nikoli však samotný počet
snímků ve hrách. Upgrade se proto nemá kupovat naslepo před praktickým testem.

## Bezpečnostní hranice

- Funnel musí zůstat vypnutý; správný výstup Tailscale uvádí `tailnet only`.
- Na Linuxu se neotevírá `127.0.0.1:8770`; používá se soukromá HTTPS adresa
  Macu. Mac musí být zapnutý, vzhůru a musí na něm běžet Tailscale i Cockpit.
- Tlačítka Cockpitu otevřeného na Linuxu provádějí skutečné operace na Macu;
  nejde o neškodnou kopii nebo demonstrační prostředí.
- Před používáním PC vnoučaty vytvořit oddělený dětský linuxový účet bez
  ikony Cockpitu a bez přístupu k soukromému profilu Míly.
- Do gitové paměti neukládat Tailscale hostname, IP adresy, přihlašovací údaje,
  tokeny ani soukromý obsah.

## Co zatím není hotové

- samostatný linuxový server nebo testovací instance Samanthy
- linuxová verze VocabularyFR a bezpečný Mac/Linux datový handoff
- automatická synchronizace dat mezi Macem a Linuxem
- ověřený přenos VocabularyFR přes LocalSend nebo jiný ruční handoff; LocalSend
  byl pouze doporučený jako jednoduchý lokální přenos a instalace není potvrzená
- praktické ověření doporučených her na tomto hardwaru
- oddělený dětský uživatelský účet

## Nejbližší krok

Vytvořit v Linux Mint nástrojem Web Apps ikonu `Samantha Cockpit`, z Linuxu
provést neškodný test zprávy, znovuotevření historie, zvuku a mikrofonu a
ověřit, že se stále používá soukromá HTTPS adresa označená `tailnet only`.

## Navrhované další kroky

1. Vytvořit oddělený dětský účet bez Cockpitu a citlivých přístupů.
2. Nainstalovat a prakticky vyzkoušet GCompris a SuperTux.
3. Podle skutečné odezvy rozhodnout, zda má smysl SSD nebo rozšíření RAM.
4. Teprve na samostatný pokyn navrhnout a otestovat přenosnou Linux verzi
   VocabularyFR s jedním aktivním zapisujícím zařízením.
5. O linuxovém uzlu Samanthy rozhodovat až podle konkrétní služby, kterou by
   měl převzít, a nejprve ji ověřit bez soukromých dat.
