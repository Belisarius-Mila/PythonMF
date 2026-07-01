# Scene 3 - Journey to the Lake

Samostatny webovy modul treti sceny lesni cesty MMTX.

Navazuje na Scene 2 - Sunny's Lost Nuts.

## Co scena dela

1. Zviratka dojdou k rozcesti pod dubem.
2. Matysek klepne na havrana, ktery poradi jit vlevo.
3. Matysek klepne na levou cestu; klik na pravou cestu jen jemne vrati zpatky.
4. Zviratka dojdou ke statku, kde potkaji velkeho pratelkeho kone.
5. Kun varuje pred psem a pozve zviratka na vodu.
6. U pumpy Matysek hleda, kdo vi, jak dostat vodu.
7. Spatne kliky daji neutralni odpovedi `I don't know`; spravny klik na Fionu spusti reseni.
8. Sunny skace na paku, Bruno tlaci, voda tece a scena se dokonci.

## Obrazove faze

| Soubor | Popis |
| --- | --- |
| `journey_lake_3a.png` | rozcesti pod dubem |
| `journey_lake_3b.png` | havran radi z vetve |
| `journey_lake_3c.png` | kun na ceste pred statkem |
| `journey_lake_3d.png` | Benji mluvi s konem |
| `journey_lake_3e.png` | prazdne vedro u pumpy |
| `journey_lake_3f.png` | Sunny a Bruno pumpuji vodu |

Vsechny obrazky maji rozmer 1672 x 941.

## Slovnicek

look, left, right, way, path, crow, bad, deep, valley, maybe, bears, but,
horse, scared, me too, friendly, careful, dog, live, warning, farm, door,
stranger, come, drink, water, pump, get, bucket, empty, I don't know, forest,
handle, jump, push.

## Interakce

| Beat | UI napoveda | Spravny klik | Chovani |
| --- | --- | --- | --- |
| Havran | Tap the crow. | crow | havran zacne radit |
| Rozcesti | Tap the left path. | left path | pokracovani ke statku |
| Pumpa | Who knows how to get water? | Fiona | spusti pumpovani |

## Audio

Anglicke MP3 pro dialogy, instrukce, napovedy a slovnicek jsou v
`audio/english/`. Scena je pouzije prednostne a pri chybejicim souboru spadne
zpet na `speechSynthesis` fallback.

Aktualni voice lock:

| Postava | Hlas |
| --- | --- |
| Bunny | `en-US-AnaNeural` |
| Sunny | `en-US-MichelleNeural` |
| Benji | `en-US-AndrewNeural` |
| Fiona | `en-US-JennyNeural` |
| Bruno | local macOS `Daniel` |
| Crow | `en-US-EricNeural` |
| Horse | `en-US-ChristopherNeural` |
| UI / slovnicek / All | `en-US-JennyNeural` |

Ceske napovedy a preklady zustavaji zatim pres fallback.

Poznamka 2026-07-01: Benjiho Edge MP3 byly preobsazene z `en-US-BrianNeural`
na `en-US-AndrewNeural`, protoze Brian pusobil moc brucive / podobne Brunovi.
Bunnyho repliky jsou znovu vygenerovane jako `en-US-AnaNeural`. Brunovy
repliky jsou po retestu prepnute z Edge `Guy` na lokalni hlubsi hlas `Daniel`,
ktery odpovida puvodni brucivejsi reference.

Poznamka 2026-07-01 vecer: havrani ceske citoslovce je upravene na `Krá krá`,
hotspot havrana je mensi a slovnicek je rozsiren na 35 polozek vcetne novych
MP3 pro vsechny klikatelne vyrazy. Audio pro `live` je vynucene na vyslovnost
`liv`, aby neznel jako pridavne jmeno `live`.

## Spusteni lokalne

```bash
cd docs
python3 -m http.server 8011
```

Otevrit:

```text
http://127.0.0.1:8011/scene03_journey_to_the_lake/
```

## Rucni test checklist

- [ ] Stranka se otevre bez JS chyb.
- [ ] Klepnuti do sceny spusti ceskou napovedu a anglicky dialog.
- [ ] Havran je klikatelny.
- [ ] Leva cesta pusti dal; prava cesta vrati jemnou napovedu.
- [ ] U pumpy Bunny/Benji/Bruno/Sunny daji neutralni odpoved.
- [ ] Klik na Fionu prepne na pumpovani.
- [ ] Po finalni vete se ukaze mapa a complete banner.
- [ ] Slovnicek se otevre a umi precist anglicke slovo + cesky vyznam.
