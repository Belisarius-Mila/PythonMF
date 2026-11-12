# Codex Reconnect Recovery

Priorita: 1
Pripomenout pri startu: ano
Datum: 2026-05-20

## Ucel

Postup pro navazani prace po vypadku SSH, reconnect loopu, padu Codexu nebo
zaseknuti streamu.

Detailni pravidla jsou v:

```text
memory/technical/session_recovery_rules.md
```

## Zakladni pravidlo

Nejdriv zjistit, co je realne rozpracovane:

```bash
git status --short --branch
git --no-pager log -3 --oneline --decorate
```

Pak cist relevantni memory:

```text
memory/MEMORY_INDEX.md
memory/ACTIVE_PROJECTS.md
memory/handoffs/
```

## Po vypadku SSH

Pouzit:

```bash
samantha
```

Pokud prikaz neni znamy:

```bash
source ~/.zshrc
samantha
```

Rucne:

```bash
screen -ls
screen -r samantha_codex
```

## Network preflight pri startu

`scripts/samantha_codex.sh` spousti `scripts/network_preflight.sh` pred pripojenim
ke `screen` relaci. Preflight kontroluje:

- bezici zname VPN/Tailscale procesy,
- pocet `utun` tunelovych rozhrani,
- IPv4 adresu na Wi-Fi rozhrani,
- zakladni ping na IP a DNS jmeno.

Vychozi rezim jen diagnostikuje a nic nevypina.

Pro pokus o ukonceni znamych VPN procesu pred startem lze pouzit:

```bash
source ~/.zshrc
SAMANTHA_DISABLE_VPN=1 samantha
```

nebo primo:

```bash
~/Desktop/PythonMF/Samantha_Agent/scripts/samantha_clean.sh
```

Preflight lze nouzove preskocit:

```bash
SAMANTHA_PREFLIGHT=0 samantha
```

## Po padu Codexu

Pouzit:

```bash
codex resume --last
```

nebo konkretni session ID:

```bash
codex resume <SESSION_ID>
```

## Pri zaseknutem nastroji

- Zkontrolovat, zda stale bezi proces, ktery Codex spustil.
- Ukoncit jen vlastni diagnosticky proces, ne uzivatelske aplikace.
- Nepouzivat destruktivni git prikazy.
- Pred dalsi praci shrnout, co je rozpracovane a co bylo overeno.

## [PRIPOMENOUT] Cockpit Recovery centrum

Priorita 1 pro pristi praci na Cockpitu: pridat read-only Recovery centrum pro
navazani po padu Samanthy/Codexu. Cilem je, aby Mila nemusel lovit terminalovy
postup v pameti.

Minimalni obsah:

- posledni autosave timestamp z `data/session_autosave/` bez vypisu citliveho
  obsahu logu,
- kratke git status summary,
- posledni relevantni handoff nebo odkaz na `MEMORY_INDEX.md`,
- doporuceny dalsi prikaz: `samantha`, pripadne `codex resume --last`,
- jasne upozorneni, ze recovery panel je read-only a nic neprepisuje.

Kanonicky handoff:

```text
memory/handoffs/cockpit_recovery_center_priority_2026_06_03.md
```

## Pravidlo pro dlouhe ukoly pri nestabilnim spojeni

Pri opakovanych reconnectech nepokracovat dlouhymi interaktivnimi tool cally.
Dlouhe prace spoustet jako samostatne skripty s logem a stavovym vystupem.

Konkretne:

- pred dlouhym ukolem spustit `samantha` nebo pri problemech `SAMANTHA_DISABLE_VPN=1 samantha`,
- dlouhe davky psat do skriptu v `scripts/` nebo projektove lokalni slozce,
- prubeh zapisovat do `logs/` nebo soukrome pracovni slozky,
- vystupy delat navazovatelne a opakovatelne,
- po reconnectu nejdriv precist vystupni soubor/log a az potom pokracovat.

To plati hlavne pro videa, media importy, exporty, sifrovani balicku a hromadne
operace nad soubory.

## Bezpecnost

Autosave v `data/session_autosave/` je nouzovy log a nesmi se commitovat.

## 2026-11-11 19:19 CET — příkazy selhávají ještě před čtením souboru

Chyba `failed to decode code-mode IPC frame: unknown field result_buffered_for_ns`
není doklad chybějících souborových práv. Nejprve ověřit konkrétní poslední
nástrojový výsledek, živý serverInfo.version (nejen codex --version) a neplacené
čtení přes command/exec. Na serveru 0.163.0 při CLI 0.167.0 přímé čtení prošlo.

HumanAdamService předává jen svým hubům config_overrides s vypnutým code_mode
a code_mode_host. Hub je kopíruje při startu, resume i výslovné rotaci; jiné
klienty ani globální config nemění. Tyto přepínače nepovolují přístup, zápis,
síť, nový modelový tah ani retry. Při živé opravě nečinného vlákna se přesná
nastavení před/po porovnají; historie a soukromá session zůstávají zachované.

2026-11-11: lokální kód a živá mitigace původního vlákna jsou oddělené.
Míla navazující Terra p+n samostatně schválil; konečný výsledek určuje přesná
soukromá účtenka jobu 444fe9352557c64a4082aed426d9dd0c. Skutečné použití
nástroje modelem musí potvrdit další uživatelský tah. Důkazy: kanonický handoff Human–Adam a
`data/private/human_adam_tool_compat_20261111/`.

Protokol per-thread config: [oficiální OpenAI dokumentace App Serveru](https://learn.chatgpt.com/docs/app-server).

### 2026-11-12 08:37 CET — HA-01: společná čtecí projekce stavu

Hotovo: Human–Adam má místní přídavný stavový kontrakt pro budoucí přehledné UI. Spojení, probíhající model, navazující kontrola, publikace a starší incidenty mají vlastní význam a rozsah. Starý nebo cizí doklad se nevydává za aktuální tah.

Rozhodnutí: Míla zadal HA-01 podle plánu z 11.11. Používá se nová čistá Python projekce nad existujícími zdroji, bez jejich nahrazení a bez nových mutací. ID jsou stabilní čtecí reference, revision je obsahový otisk, nikoli pořadový event cursor. Vlastníci provedení a doménové účtenky zůstávají autoritou.

Další krok: Po dokončení HA-01 navázat HA-02 — přehlednější rozhraní nad společnou projekcí.

Navrhované další kroky: HA-03 ažHA-05 pro skutečné události, serverově vlastněnou práci a živou kartu; poté doplnění/zastavení. Žádné p+n nebylo zadáno.

Technický důkaz: 29 nových HA-01 testů OK / 2,411 s. Závěrečná plná brána 3543 testů OK / 620,369 s, 5 SKIP; statické a syntaktické kontroly OK. Ověřené nezměněné bajty/mtime zdrojů, korelace a pozdní snímky, přesný head/target/smoke při dodatečném důkazu. Main a služby nedotčené. Report human_adam_ha01_work_state_20261112.txt.
