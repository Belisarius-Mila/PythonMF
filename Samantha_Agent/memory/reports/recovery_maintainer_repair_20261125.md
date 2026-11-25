# Podklady obnovy Samanthy — 25. 11. 2026

Tento dokument je netajný podklad pro sjednocený obnovovací návod. Stav je
časově omezený na níže popsaný čtecí audit; není to důkaz fyzické obnovy Macu.

## Správce návodu a současný způsob práce

Agent Samantha používá Codex App Server, hlavní checkout a oddělené pracovní
kopie. Historické pojmenování Agent SDK není pokyn k migraci architektury.
Role a jejich schválené modely spravuje config/agent_roles.json. Po obnově
nepřebírat model ani rozpočet z paměti; ověřit skutečný aktuální stav repozitáře.

Hlavní provozní návod je OBNOVA_SAMANTHY_NOVY_MAC.txt v kořeni PythonMF,
druhá provozní kopie je v iCloud Dokumentech. Kopie na Ploše a starší soubor
v Downloads nejsou automaticky autoritou. Při auditu byly provozní kopie
shodné a měly datum 8. listopadu. Datum nové redakce není datum externí zálohy.

Týdenní správce má label com.samantha.recovery-guide, interval kontroly900s
s výběrem nejnovějšího splatného nedělního slotu od09:00 Europe/Prague.
Nejde o placené spuštění každých15 minut. Má vlastní privátní aktivaci,
stav a schválenou roli recovery_document_maintainer, Sol/medium Standard,
mez200 kreditů/běh a1000/měsíc. Při auditu neměl dokončený týdenní slot:
čekal na runtime proof pro0.163.0, zatímco sdílený server byl0.169.0.
Revalidace runtime je samostatný přesný syntetický pokus; bez důkazu
nepřepisovat runtime_evidence ani nevypínat ochrannou bránu.

Registrovaný recovery_service_archive_preserve vytváří pouze nový soukromý
archiv v Samantha_Agent/data/private/recovery-service-archives. Obsahuje
konfiguraci a žurnály správce, bootstrap návod, protokolové důkazy pro
Standard, dvě vlastněné definice LaunchAgentů a konzistentní databázi FR.
Dokončený manifest ověřuje SHA všech souborů; změna zdroje, symlink nebo
překročení rozsahu zastaví dokončení. Nejde o instalaci zachycených plistů.
Pro obnovu vybrat dokončený archiv obsažený ve skutečném recovery snapshotu,
ověřit jeho manifest a upravit cesty až podle nového vlastněného zařízení.

Aktivní správce původně běžel ze stálé Data pracovní kopie mimo hlavní
PythonMF. Samotná recovery hlavního checkoutu proto nezaručuje zachování
jeho soukromé aktivace a žurnálů. Po ztrátě Macu určit umístění z ověřeného
servisního doplňku, obnovit stavy a sestavit novou definici pro nové cesty.
Neobnovovat starý plist slepě a nespouštět druhý správce. Bez kompletního
ověřeného runtime proofu, limitů, přijatého návodu a historie nejistých pokusů
musí zůstat nová aktivace vypnutá.

## Francouzština Jana a společné pexeso

Od24.11. je přijatý bezplatný soukromý provoz na zapnutém Macu přes Tailscale
Serve. Samostatná služba com.samantha.vocabulary-fr používá soukromé HTTPS8443
na loopback8792. Soukromý hostname se při obnově odvozuje z nového vlastněného
zařízení a schválené sítě; není správné kopírovat jméno zaniklého Macu.
Funnel se nezapíná, nepřidávat granty ani neměnit Cockpit/Camino trasy.

Kód služby je app/vocabulary_fr_tailnet.py a app/vocabulary_fr_multiplayer.py.
Veřejný klient je docs/vocabulary-fr; hlavní vstup Francouzština Jana
v Cockpitu zachovává původní Pages původ osobního učení a do fragmentu
předává ověřenou adresu živé soukromé herní služby. Samotné Pages nejsou
herní server. Dočasné Cloudflare adresy nejsou trvalou obnovovací adresou.

Soukromé herní stavy, rooms.sqlite3, konzistentní SQLite zálohy, neměnné
exporty a účtenky plánů jsou v Samantha_Agent/data/private/vocabulary-fr-tailnet.
Zdrojový GitHub nenahrazuje tuto databázi ani ostatní ignorovaná data.
Pro recovery zvolit dokončenou konzistentní zálohu databáze a ověřit její
integritu. Nemíchat soubory živé SQLite z různých okamžiků. Místnosti mají
běžnou expiraci24h /2h bez aktivity; kopie databáze tuto platnost neprodlužuje.

Po obnově zdrojů a Python prostředí použít registrovaný PrivateGame.prepare
pro přesný čistý commit a nové schválené soukromé zařízení. Před zapnutím
zkontrolovat plán, existující služby, porty a původní síť. Aktivace je
samostatná systémová akce s přesnou globální potvrzovací větou. Nevytvářet
obecnou veřejnou proxy, nepřebírat cizí PID/label a nic automaticky nemazat.

Aktualizace25.11. zachovává při změně filtru místnost a hráčské přístupy:
zakladatel rozehrané i dokončené hry mění filtr uvnitř místnosti. Zrušení
vrátí původní hru, potvrzení vymění24 karet a vynuluje skóre. Server zvýší
kolo a odmítá opožděné kliky/poslechy. Vydání klienta nestačí; samostatný
server musí odpovídat schválenému exportu. Po obnově oba hráči odemknou zvuk
ve svých prohlížečích. HTTP test není důkaz slyšitelného zvuku u Jany.

## Záloha a hranice obnovitelnosti

Poslední doložená recovery v auditované evidenci byla15.11.2026. Nová záloha
je úkol této opravy, nikoli hotový výsledek tohoto dokumentu. Výběr snapshotu
vždy řídit dokončeným manifestem a skutečným doplňkem Camina; žádné pevné
historické ID ani datum tohoto dokumentu nenahrazuje manifest.

Recovery provádět jen na připojený a ověřený šifrovaný svazek
/Volumes/SamanthaSecureBackup/SamanthaBackups. Samotný připojený Falta nestačí.
Před kopírováním preflight/dry-run a ověření místa; po něm0 skipped, manifest,
reprezentativní SHA shody, zkušební obnova a evidence poslední dokončené zálohy.
Auth.json a data/session_autosave jsou vyloučené; přihlášení se provádí znovu.
Obnovený konfigurační soubor není důkaz platného přihlášení nebo systémového
oprávnění. Hesla, Keychain, SSH, externí data a chybějící soukromé runtime
kopie je nutné určit zvlášť; kompletní novou instalaci Macu prokáže až
samostatná fyzická zkouška. Žádné tvrzení o úplné obnově všech osobních dat.

## Druhý blokátor a připravený návrh limitů

Neplacený inventář zmrazil682 podkladů, celkem3331261 referenčních tokenů
s přijatou bezpečnostní přirážkou; jde o plánování, nikoli účetní spotřebu.
Původní konfigurace nemá oddělenou inspection_output_tokens, a proto
rezervuje celých32000 výstupních tokenů i pro každou kontrolní dávku.
Takový plán překročí20 kroků a po samotném přepnutí runtime nezačne.

Návrh zachová úplný korpus a limit20 kroků, finální návod32000 tokenů,
čas, roli, Standard i měsíční mez1000 kreditů. Pro poznámky z kontrolní
dávky zavede samostatnou rezervu3000 tokenů a navrhuje přijímací mez250
kreditů za celý běh. Naměřená celková rezervace před konečným commitem
byla232,02615 kreditu,20 kroků. Není to uskutečněná spotřeba ani tvrdý
upstream billing cap. Nový limit250 není dosud schválený ani zapnutý.

Volitelný refresh_budget v přesném revalidačním plánu obsahuje celý otisk
korpusu, jeho Git head, skutečný rozpad rezervace a konkrétní dvě změny
limitů. Převzetí bez této položky rozpočty vůbec nemění. Při změně zdrojů
se před placeným tahem i před změnou aktivace odmítne původní plán.
Přesné přijetí rozpočtového plánu musí navíc předcházet aktivaci.

Standard sazby programu pro Sol50/2,5/250 kreditů za1M input/cache/output
byly při přípravě25.11. potvrzené proti oficiálnímu ceníku:
https://learn.chatgpt.com/docs/pricing#token-rates
Ceny a limity zkontrolovat znovu při budoucí změně; nerozšiřovat rozpočet
jen podle ceny nástupnického modelu. Model role se zde nemění.
