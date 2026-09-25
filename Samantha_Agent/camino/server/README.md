# Camino server — C05a

Tento modul je lokální produkčně orientovaný základ soukromého owner API.
Spojuje síťový adaptér C03b s trvalým příjmem médií C05a. Nespouští se
automaticky a nemění Tailscale Serve. Viewer je explicitně volitelný.

M1 přidává volitelný lokální Viewer přes `create_app(viewer=...)`. M2a přidává
explicitní konfiguraci spouštěče, periodickou přípravu médií a konfigurovaný
přímý odkaz z Cockpitu. Výchozí spouštěč dál Viewer nezapíná. Nastavení a
hranice jsou v `../docs/M2_RUNTIME_REPORT.md`; služba není tímto nasazená.

## Oddělené prostředí

FastAPI nepatří do sdíleného prostředí Samanthy. Vytvoř samostatné prostředí
mimo zdrojový repozitář a instaluj připnuté přímé závislosti:

```sh
python3 -m venv /soukroma/cesta/camino-server-venv
/soukroma/cesta/camino-server-venv/bin/python -m pip install -r camino/server/requirements.txt
```

Databáze metadat, médií a tokenů i kořen mediálních souborů musí být mimo
zdrojový repozitář, nesmí být symlink a musí být přístupné pouze vlastníkovi.
Skutečný token nikdy nepatří do příkazu, dokumentace ani Gitu. První token lze
místně vložit přes skrytý vstup shellu a potom proměnnou odstranit:

```sh
read -s CAMINO_C05A_TOKEN
export CAMINO_C05A_TOKEN
/soukroma/cesta/camino-server-venv/bin/python -m camino.server.admin \
  --auth-db /soukroma/cesta/auth.sqlite add-token --label "Hlavní iPhone"
unset CAMINO_C05A_TOKEN
```

Odvolání používá pouze vypsané necitlivé ID tokenu:

```sh
/soukroma/cesta/camino-server-venv/bin/python -m camino.server.admin \
  --auth-db /soukroma/cesta/auth.sqlite revoke-token --token-id UUID
```

## Start bez síťového vystavení

Po nastavení `CAMINO_C05A_METADATA_DB`, `CAMINO_C05A_MEDIA_DB`,
`CAMINO_C05A_MEDIA_ROOT` a `CAMINO_C05A_AUTH_DB` lze službu spustit jen na
loopbacku. HTTPS má později ukončit výhradně soukromý Tailscale Serve; Funnel a
veřejný bind jsou zakázané.

```sh
/soukroma/cesta/camino-server-venv/bin/python -m camino.server.main \
  --host 127.0.0.1 --port 8766
```

Tento návod není oprávnění službu nasadit nebo změnit Serve. C05a checkpoint
ověřuje kód synteticky; skutečná služba, iPhone klient a vzdálený přenos jsou
samostatné kroky.

## Jednorázový loopback smoke

Bezpečný integrační mezikrok je vedený v registru workflow pod ID
`camino_c05a_loopback_smoke`. Náhled nejdřív ukáže pevný příkaz, přesný rozsah
zápisů a vyžádá samostatné potvrzení; ruční improvizované spuštění se
nepoužívá. Smoke pracuje jen se syntetickými daty, dynamickým loopback portem a
dočasnými odvolatelnými tokeny. Zachovává privátní redigovaný důkaz, ale
nemění Serve/Funnel, nepřipojuje iPhone a není nasazením trvalé služby.

## C05b fyzické přijetí

Session-owned službu pro C05b řídí pouze registrované workflow
`camino_c05b_private_start`, `copy_url`, `copy_token`, `status` a `stop`. Data jsou mimo
repozitář, proces binduje jen loopback a Tailscale Serve přidá jen
`/camino-api`; vyhrazený acceptance port je `127.0.0.1:8767`, aby nekolidoval
se ScanDocu na portu 8766. Start ověřuje vypnutý Funnel, privátní HTTPS i zdraví kořene
Cockpitu; stop odvolá token a porovná přesný původní Serve stav.

Pro T050 používá tento oddělený acceptance běh pětisekundové zdržení finalizace.
Pro T052 existují potvrzované režimy `storage_full_on/off`, které restartují
jen vlastněný proces nad stejnými daty a vyvolají `insufficient_storage` bez
plnění skutečného disku. T058 používá potvrzované `rotate_epoch`; nic nemaže,
ale záměrně ponechá inventární kontrolu a exporty blokované. Tyto testovací
volby nejsou C06a provozní konfigurace.
