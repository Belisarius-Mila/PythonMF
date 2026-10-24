# Návrat k projektům a přenosům po žádosti o smazání

## Příčina a oprava

Mílův snímek z 24. 10. 2026 ukázal v buildu 21 po žádosti o smazání
aktivní cesty pouze obrazovku **Připravit projekt**. Koš správně skryl
aktivní cestu; kořen aplikace pak přešel z hlavní obrazovky do přípravy
projektu. Ta dosud nabízela jen založení nové cesty a neměla navigaci
k ostatním cestám, žádostem o smazání ani přenosům.

Oprava mění pouze UI:

- Bez aktivní cesty zůstává při existujícím projektu či koši dostupné
  **Projekty a koš**. Lze zvolit jinou cestu a vidět stav žádostí.
- **Uložení a přenosy** je dostupné i bez aktivní cesty, včetně stavu
  spojení a doručení žádosti Macu. Zavádějící pevné tvrzení, že Mac není
  připojený, je odstraněné.
- Příprava nového projektu zůstává dostupná. Žádosti se neruší,
  skryté projekty se samy neobnovují a mazací/přenosový kontrakt se nemění.

## Ověření a balíček

- Původní binárka: skutečný regresní UI scénář FAIL přesně na chybějícím tlačítku projectList po žádosti (129,859 s).
- Oprava: stejný scénář PASS (89,366 s). Dvě cesty, označený Moment v první, žádost o smazání druhé, návrat k první se zachovaným Momentem, žádost o poslední, restart, koš a otevření/zavření přenosů. Syntetická data izolovaná od telefonu i služby.
- Statická brána a git diff --check PASS; model/persistence nezměněné, dřívější plná brána 2232 se bez změny těchto částí neopakovala.
- Podepsaný Release archive/export, strict codesign čisté extrakce a ZIP/CRC PASS. Nové delší texty navigace ověřené přímo v Release binárce; krátké Swift řetězce mohou být inline a prosté hledání jejich bajtů není spolehlivá kontrola.
- IPA `Camino-Projects-Trash-22-20261024.ipa`, verze 0.1.0 (22), bundle `cz.pythonmf.camino.app`, 1074899 B, SHA-256 `cb00915a10f2e3e97852f18b656c965d1adeea98abe8a41ac5b5e3342296c14b`. Profil do 2026-10-29T19:01:14Z.
- Shodné create-only kopie v Downloads a iCloud Dokumentech; upload potvrzený. Starší IPA zachované. Zdrojový rodič 3cd6308a, přesné SHA obou změněných Swift souborů v privátní účtence; odpovídající vývojový commit je dohledatelný podle Fix Camino navigation after project trash request.
- Soukromé důkazy: ipa-receipt.json, archive/export/codesign logy a exportovaná příloha UI testu. Testové logy/xcresult jsou v dočasném lokálním úložišti, ne v Gitu.

## Předání

Nový klient je připravený build 22; samostatnou službu ani Cockpit tato UI oprava
neaktualizuje. Telefon nyní používá build 21, jehož spuštění a žádost
Míla potvrdil. Skutečný výmaz/obnova a fyzická přejímka nového UI zůstávají
samostatné; místní ani serverová uživatelská data se při této opravě nemění.
