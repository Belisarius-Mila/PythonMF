# Recovery from Samantha backup

Aktualizováno 2026-10-19. Kanonický podrobný postup pro nový Mac je:

[OBNOVA_SAMANTHY_NOVY_MAC.txt](OBNOVA_SAMANTHY_NOVY_MAC.txt)

Krátký vstup: [RECOVERY_CARD_NEW_MAC.md](RECOVERY_CARD_NEW_MAC.md).

## Pokud čteš kopii READ_ME_FIRST_RECOVERY.md ve snapshotu

Podrobný TXT hledej v tomto snapshotu pod:

`PythonMF/Samantha_Agent/OBNOVA_SAMANTHY_NOVY_MAC.txt`

Ve starších snapshotech vzniklých před 2026-10-19 tento TXT ještě není.
Použij jeho samostatně uloženou novější kopii nebo publikovaný repozitář.
Tento soubor se při budoucí standardní záloze kopíruje vedle manifestu;
existující starší snapshoty se změnou dokumentace nemění.

## Bezpečný postup v kostce

1. Připojit a odemknout existující šifrovaný kontejner. Nic neformátovat.
2. Zvolit skutečně dokončený snapshot s manifestem a profilem recovery.
3. Ověřit rozsah. Zdroj standardní zálohy je PythonMF, ne celý domovský
   adresář. Živá služba Camino v Library/Application Support/PythonMF/Camino
   potřebuje samostatnou konzistentní kopii; viz kapitola 1.4 TXT.
4. Obnovit PythonMF jen do prázdného cíle. Existující práci zachovat.
5. Znovu nainstalovat správný Python, vytvořit prostředí, doplnit závislosti
   a znovu přihlásit Codex/GitHub. Nekopírovat starý auth.json.
6. Prověřit soukromá nastavení a nejasné odchozí úlohy, potom spustit
   místní Cockpit. Autostart, Tailscale a iPhone ověřit zvlášť.
7. Po úspěšné obnově provést novou ověřenou zálohu se známým rozsahem.

`data/session_autosave` je záměrně vyloučená i z recovery profilu.
Originální Codex sessions se zálohují samostatně jako vybraný obsah Codexu.
Klíčenka, LaunchAgents, aplikace a externí data se tím automaticky neobnoví.
Recovery profil nemusí obnovit celou živou službu ani všechny historie vláken.

## Cílená obnova na stále fungujícím Macu

Pro jeden rozbitý soubor použij registrovaný postup:

1. `list_backup_snapshots` — výpis dostupných dokončených záloh.
2. `preview_backup_restore` — náhled jedné relativní cesty.
3. Samostatné potvrzení konkrétního snapshotu, cesty a případné citlivosti.
4. `restore_path_from_backup` — před přepsáním zachová `.before_restore` kopii.

Není to oprávnění hromadně přepisovat nový Mac. Hesla a tokeny nepatří do
chatu ani Gitu a žádné snapshoty se kvůli obnově nemažou.

## Co bylo skutečně ověřeno

Běh 2026-10-18: snapshot `20261018_210658`, 90 833 souborů, 0 přeskočených,
exit 0, manifest, recovery návod, shodné SHA-256 čtyř vybraných souborů
plus obnova jednoho souboru do nové dočasné složky. Nový Mac a kompletní
obnova všech služeb zatím testované nebyly. Dne 19. 10. není disk připojený;
údaje o tomto běhu jsou z uloženého ověřovacího logu a evidovaného stavu.
