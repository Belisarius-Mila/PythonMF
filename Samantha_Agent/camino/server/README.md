# Camino server — C05a

Tento modul je lokální produkčně orientovaný základ soukromého owner API.
Spojuje síťový adaptér C03b s trvalým příjmem médií C05a. Nespouští se
automaticky, nemění Tailscale Serve a neposkytuje Viewer.

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
