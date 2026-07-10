# Cockpit persistence write map — 2026-07-10

## Rozsah a bezpečnost

Tato git-safe inventura mapuje runtime zápisy v `app/` podle zdrojového kódu.
Nečetla ani neopisuje obsah soukromých dokumentů, e-mailů, hlasových pokynů nebo
private vaultu. Jde o lexikální mapu zápisových míst, ne o migraci dat.

## Hlavní zápisové oblasti

- Cockpit provoz: HTTP event logy, servisní logy, pomocné command/marker soubory.
- VoiceBridge: status, poslední odpověď, pending stav, historie a potvrzovací
  karty v `app/speech/adam_voice_mode.py` a navazujícím Cockpit kódu.
- Dokumenty: JSON/JSONL registry, metadata, auditní rozhodnutí, fulltext a
  lifecycle události v `app/documents/`.
- E-maily: activity state, case indexy, archivní metadata, drafty a outbound
  provozní stav v `app/email/`.
- Připomínky: reminders store, query stav a platební case metadata v
  `app/reminders/`.
- Další runtime registry: článek/knihovna, Quick Notes, urgent reminders,
  backup activity state, Adam service a kvantitativní metriky.

## Potvrzené společné riziko

Přímé `write_text`, `open("w")`, `open("a")` a `json.dump` postupy nemají jeden
společný stabilní mezipo-procesový zámek. Samotné spuštění jedné Cockpit serverové
instance snížilo počet souběžných zapisovatelů, ale pomocné skripty a další
procesy mohou stále zapisovat do stejných runtime souborů.

Rizika jsou:

- částečný JSON při pádu během přepisu,
- ztracený read-modify-write update,
- promíchané nebo neúplné JSONL řádky,
- nesoulad mezi manifestem, indexem a navazujícím stavem.

## První implementovaný řez

Nová sdílená vrstva `app/file_persistence.py` poskytuje:

- stabilní sidecar `.lock` soubor a `fcntl.flock` mezi procesy,
- timeout místo neomezeného čekání,
- atomický text/JSON zápis přes dočasný soubor ve stejné složce,
- flush + `fsync` souboru, `os.replace` a best-effort `fsync` složky,
- zamčenou JSON read-modify-write transakci,
- zamčený JSONL append jednoho kompletního řádku.

První integrace je záměrně nízkoriziková:

1. `app/backup/activity_state.py` používá atomický zamčený JSON zápis.
2. Cockpit HTTP technický event log používá zamčený JSONL append s krátkým
   timeoutem; log zůstává best-effort a nikdy neobsahuje request payloady.

Existující soukromá data se nepřesouvají, nepřepisují dávkově ani nemigrují.

## Ověření

- Dva samostatné Python procesy provedou souběžně zamčené JSON
  read-modify-write operace bez ztracených aktualizací.
- Dva samostatné procesy appendují JSONL a každý očekávaný záznam zůstane právě
  jedním validním řádkem.
- Simulované selhání `os.replace` ponechá původní JSON beze změny a uklidí
  dočasný soubor.
- Integrační testy ověřují použití stabilního locku v backup state a Cockpit
  HTTP event logu.

## Doporučené další pořadí rolloutů

1. VoiceBridge jednotlivé JSON stavové soubory; nejprve čisté přepisy, až potom
   historie a pending read-modify-write operace.
2. Reminders a Quick Notes registry s explicitní zamčenou transakcí.
3. Dokumentové registry a lifecycle JSONL po menších skupinách s consistency
   testem po každé skupině.
4. E-mail activity/case/archive metadata; outbound a mazací workflow až nakonec.

Každý rollout má zachovat formát i cestu existujícího souboru, přidat cílený
regresní/concurrency test a nemigrovat obsah bez samostatného rozhodnutí.
