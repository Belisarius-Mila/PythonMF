# macOS Wi-Fi / VPN / Tailscale Recovery Protocol

Priorita: 1
Pripomenout pri startu: ano
Datum ulozeni: 2026-05-19

## Kontext

Tento protokol vznikl po vaznem vypadku site na macOS po kombinaci:

- instalace Tailscale,
- nastavovani SSH vzdaleneho pristupu,
- aktivnich VPN/tunnel rozhrani,
- prepinani mezi domaci Wi-Fi, iPhone hotspotem a VPN trasami.

## Offline nouzovy pristup

Protoze pri vypadku site nemusi jit otevrit ChatGPT ani pohodlne dohledat memory,
existuje kratka offline karta primo v koreni projektu:

```text
/Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent/NETWORK_RECOVERY_CARD.txt
```

V Terminalu ji lze vypsat i bez internetu:

```bash
/Users/miloslavfalta/Desktop/PythonMF/Samantha_Agent/scripts/network_recovery_card.sh
```

Prakticky doporuceny dalsi krok je mit kopii nebo alias i mimo repozitar, napriklad
na Desktopu, aby byla videt i bez vzpomenu na presnou cestu.

## Symptomy

- Wi-Fi vypada jako pripojena.
- Safari nebo webove stranky zamrznou pri nacitani.
- Hotspot se opakovane nedari pripojit.
- Netecou zadna internetova data.
- `ipconfig getifaddr en0` nevraci zadnou IP adresu.
- `ifconfig` ukazuje vice `utunX` rozhrani.
- DHCP nebo routovani je rozbite.

## Pravdepodobna pricina

Pracovni diagnoza:

- poskozena macOS sitova konfigurace,
- rozbite DHCP/routovani,
- zastarala VPN/Tailscale tunnel rozhrani,
- poskozene nebo nekonzistentni konfiguracni soubory:
  - `NetworkInterfaces.plist`,
  - `preferences.plist`,
  - `com.apple.airport.preferences.plist`.

Tento incident sam o sobe neznamena:

- selhani SSD,
- ztratu dat,
- poskozeni uzivatelskych dat,
- hardwarovou smrt Macu.

## Rychla diagnostika

Zjistit Wi-Fi rozhrani:

```bash
networksetup -listallhardwareports
```

Ocekavany vysledek:

```text
Hardware Port: Wi-Fi
Device: en0
```

Zkontrolovat IP adresu:

```bash
ipconfig getifaddr en0
```

Pokud je vystup prazdny, je pravdepodobne rozbite DHCP nebo routovani.

Zkontrolovat tunnel rozhrani:

```bash
ifconfig | grep utun
```

Vice `utunX` rozhrani muze souviset s VPN, Tailscale nebo jinymi tunely.

## Rychly pokus o opravu

Zastavit VPN/Tailscale procesy:

```bash
sudo killall Tailscale
sudo killall WireGuard
sudo killall NEIKEv2Provider
```

Hlaseni `No matching processes were found` je v poradku a znamena jen to, ze dany
proces prave nebezel.

Resetovat Wi-Fi rozhrani:

```bash
sudo ifconfig en0 down
sudo ifconfig en0 up
```

Obnovit DHCP:

```bash
sudo ipconfig set en0 DHCP
```

Overit:

```bash
ipconfig getifaddr en0
```

## Plna oprava

Pouzit pouze kdyz rychly pokus nepomohl a IP/DHCP je stale rozbite.

Prejit do konfigurace site:

```bash
cd /Library/Preferences/SystemConfiguration
```

Zalohovat problemove konfigurace na Desktop:

```bash
sudo mv com.apple.airport.preferences.plist ~/Desktop/
sudo mv NetworkInterfaces.plist ~/Desktop/
sudo mv preferences.plist ~/Desktop/
```

Restartovat Mac:

```bash
sudo reboot
```

Po restartu macOS automaticky vytvori ciste sitove konfiguracni soubory.

## Po restartu

Dulezite:

- nespoustet hned Tailscale,
- nejdrive overit ciste pripojeni k internetu,
- otestovat domaci Wi-Fi,
- otestovat iPhone hotspot,
- otestovat Safari nebo jiny prohlizec,
- otestovat `ping`.

## Overeni

Zkontrolovat IP:

```bash
ipconfig getifaddr en0
```

Ocekavany typ vysledku:

```text
192.168.x.x
```

nebo:

```text
10.x.x.x
```

Otestovat konektivitu:

```bash
ping 8.8.8.8
ping google.com
```

Interpretace:

- `8.8.8.8` funguje a `google.com` nefunguje: pravdepodobne DNS.
- Oba nefunguji: pravdepodobne sit, DHCP, routovani nebo VPN/tunnel konflikt.
- Oba funguji: zakladni internet je obnoveny.

## Prevence

- Nepoustet soucasne vice VPN/tunnel nastroju, pokud to neni nutne.
- Pred sitovymi experimenty ciste odpojit Tailscale.
- Udrzovat infrastrukturu a recovery poznamky v pameti Samanthy.
- Zasadni AI/dev infrastrukturu pravidelne zalohovat.

## Navrzeny budouci poradek infrastruktury

Mozna cilova struktura mimo tento repozitar:

```text
~/AI/
  SamanthaMemory/
  Agents/
  Infrastructure/
  Recovery/
  Prompts/
  Images/
  Stories/
  Vocabulary/
  MultiLO/
  Backups/
```

## Bezpecnost

Do teto pameti neukladat:

- hesla,
- API klice,
- tokeny,
- privatni VPN konfigurace,
- citlive casti SSH konfigurace,
- verejne IP adresy, pokud nejsou vyslovne potreba.
