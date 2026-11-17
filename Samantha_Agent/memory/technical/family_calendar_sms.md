# Rodinný kalendář — soukromé osobní SMS

Samostatná CalendarSMS nad kanonickým data/private/family_calendar/sms.
Výchozí draft je vypnutý, obsahuje jediný E.164 telefon a oslovení. Schema1,
Preferovaná služba SMS/09:00/Europe-Prague jsou pevné; Mac může použít RCS. Osobní údaje a konkrétní náhled nikdy Git.
Povolené osoby/události vlastní existující registr; datum po probuzení je dnešní,
žádný včerejší backlog. Oslovení, šablony a pravidlo jsou svázané otiskem.

- prepare: create-only vypnutý návrh a prázdný ledger,700/600, žádný transport.
- status/preview: jen redigované stavy, počty a fingerprint. Náhled čte dnešní
  rodinné události; žádné SMS DB, model, send nebo zotavovací zápisy.
- test: samostatná přesná aktuální zpráva TEST_CONFIRMATION, fingerprint a
  stabilní request_id. Nejasný původní test blokuje i jinou novou identitu.
- verify: potvrzená kontrola původního request_id/otisku; pouze čtení původního
  Messages výsledku a doplnění účtenky, nikdy nový send.
- enable: samostatná ENABLE_CONFIRMATION + fingerprint. Vyžaduje odpovídající
  sent/delivered test do7 dnů, shodu načteného runtime a hodinový policy.
- disable: potvrzené vypnutí pouze SMS konfigurace; e-maily beze změny.
- tick: pouze již povolený přesný policy. Worker lock, trvalé sending před
  SMS a vlastní per-recipient/event/year klíč. Chybějící/poškozená historie
  je překážka, nikdy nový prázdný ledger. Not_sent pouze před transportem,
  retry nejdřív za hodinu/max24. Po transportu nejistota bez opakování.

MessagesSMS používá dosavadní Messages sender. Před pokusem čte MAX ROWID
přes mode=ro; výsledek musí být novější, odchozí, s přesným textem, celým
příjemcem a službou SMS nebo RCS. Null text se zkouší dekódovat přes macOS
Foundation NSUnarchiver, bez otevření aplikace. Přesná shoda celého
dekódovaného textu zůstává povinná. Sent není totéž co delivered. Více shod,
jen jiné zprávy, iMessage nebo nečitelné attributedBody nejsou důkaz. Skutečný transport je třeba
ověřit v konkrétním běhovém prostředí; testy UI oprávnění samy neprokazují.

Owned family_calendar_delivery_run.scheduled_main volá nezávisle SMS a e-mail,
ale jen bez vlastních argumentů. --today/--config-path ani jiný ruční replay
SMS větev nespouští. Plist, původní SMTP příjemci a jejich ledger se nemění.
Pole `sms` je součást redigovaného `/api/family-calendar/delivery-status`;
Cockpit ukazuje vypnuté/neověřené/aktivní SMS a potřebnou kontrolu samostatně.

Registrované Python schopnosti: family_calendar_sms_prepare/status/preview/control.
Kontrolní agentové tools status/preview nemají odchozí účinek; control test/enable
vyžaduje potvrzení právě aktuální zprávy a navíc rozlišenou přesnou frázi.
Registrované shellové status/preview/tick směřují na scripts/family_calendar_sms.py.
Ruční tick navíc vyžaduje potvrzení workflow a respektuje vypnutý policy.

Soukromý vývojový důkaz: family_calendar/sms_development_20261117/completion.json.
Vývoj, lokální commit ani p+n nepovolují testovací SMS nebo aktivaci.
