# Kompatibilní upgrade pošty před ScienceNews rolí

Stav 2026-11-10 10:58 CET. Míla poskytl přesnou globální větu pro připravený upgrade a pokračování nasazení.

- Registrované pause/prepare/upgrade vlastněného hodinového LaunchAgentu: 617f3e0d8669255238d2dd56c93cfbf037dc1a4a → již publikovaný 8c83e93bd6fada51fa4dc24e8fcb57338f90b8fe. Původní release i servisní záloha jsou zachované. Nikde nebyl ručně přepsán instalovaný parser nebo TCC.
- Stav installed/owned/loaded/enabled PASS, první health already_completed. Business digest před/po je totožný, všech 95 položek identických, nastavení i celé původní role byte-identické. Žádný nový modelový pokus nebyl tímto již dokončeným slotem zahájen.
- Nový skutečně instalovaný parser nejprve přijal izolovaný kandidátní config se science_news_editor. Teprve pak main fast-forward na31a59e0c zpřístupnil nový binding; následná samostatná kontrola instalovaného parseru přijala již skutečný sdílený live config. Email policy digest zachovaný, ScienceNews digest odpovídá Datovu schválenému kandidátu.
- Doklady: `logs/science_calendar_email_upgrade_20261110.log`, `logs/science_calendar_post_adoption_audit_20261110.log`; podrobnější privátní audit je pod service_audits ve vlastním úložišti poštovní služby. Texty, adresy, položky ani tajemství se do Gitu nekopírují.
- ScienceNews páteční LaunchAgent se neinstaluje a nový rozpočet není schválený. Datův commit a prioritní kalendářová oprava pokračují společným runtime p+n; report `calendar_edit_alarm_order_recovery_20261110.md`.
