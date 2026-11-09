# Obnova hodinového e-mailového agenta

## 2026-11-09 11:30 CET — Obnovený hodinový e-mailový agent po nekompatibilní roli

### Hotovo
- Vlastní hodinová kopie je registrovaně upgradovaná z f2d6ef79 na již
  publikovaný617f3e0d. Installed/owned/loaded/enabled a skutečný parser PASS.
- První skutečná kontrola dnešního slotu11:00 dokončena v11:28:47 CET:
  7 nových zpráv,3 karty k potvrzení a4 zprávy hodinového přehledu. Živé
  Cockpit overview API ověřilo3 karty a3 přehledové zprávy; poslední nedůležitá
  zpráva je skrytá již existující visibility předvolbou. Všech7 položek je ve
  stavu zachovaných, soukromý obsah se neopisuje.
- Při systémovém přepnutí celý business stav, nastavení a všechny role
  shodné s předchozím snapshotem. Po běžném dočtení jsou všechny původní
  položky beze změny; zdrojové pozice se posunuly až zpracováním nových zpráv.

### Rozhodnutí
- Míla potvrdil přesnou globální brzdu i následné p+n. Použity pouze
  registrované pause/prepare/upgrade; starý release a servisní záloha zachované.
- Příčina: sdílený agent_roles.json již obsahoval recovery_document_maintainer,
  ale parser instalované f2d6ef79 ji neznal. AgentRoleError byl reprodukovaný
  právě v instalované kopii, před IMAP a modelem. Poslední dokončený slot
  před opravou8.11.20:00. Runtime nezačal zpracovávat dnešní poštu až do opravy.
- Terra/high, oba poskytovatelé, bez denního stropu a calendar_suggestions=false
  zachované. Žádná změna přístupů ke schránkám nebo recovery služby.
- Nový kód nebyl potřeba. Dokončovací commit obsahuje pouze Git-safe provozní
  záznam; Python služby se po něm nemění a nevyžaduje druhé přepnutí runtime.

### Další krok
- Dokončit výslovně schválené registrované p+n tohoto záznamu v project-email-cases.
  Autorita výsledku je původní účtenka a logs/email_role_compat_release_20261109.log.

### Navrhované další kroky
- Míla obnoví přehled Cockpitu a převezme3 nové karty.
- Při další nové roli předem ověřit všechny skutečné runtime parsery sdíleného JSON,
  včetně hodinové služby; samotný kompatibilní main nestačí.

### Technický důkaz
- reports/email_hourly_role_compat_20261109.md; logs/email_role_compat_upgrade_20261109.log.
- Soukromé důkazy jen v service_audits/role_compat_upgrade_20261109_1127:
  baseline, připravený plán, switch_checks, verified, první dokončený běh a HTTP projekce.
- Všechny kontroly přepnutí true; aktuální7 modelových posouzení jsou běžný
  již schválený příjem čekající pošty, ne opakování nejistého starého pokusu.
- První health completed, chybové posouzení0, zdrojové pozice posunuté;
  všechny původní položky shodné. Fyzická Mac/iPhone přejímka nepředstíraná.
