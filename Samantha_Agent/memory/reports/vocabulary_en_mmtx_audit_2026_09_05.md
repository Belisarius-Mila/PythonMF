# Audit MMTX → VocabularyEN

Datum: 2026-09-05 22:40 CEST

## Výsledek

- Doplněno 120 hesel; slovník vzrostl z 305 na 425 položek.
- Každé nové heslo má CZ, Sentence, SentenceT a WS=Benji. Okruh Benji obsahuje 239 položek.
- Všechny původní řádky CSV jsou bajtově zachované. Nové řádky mají Order 306–425.
- Původních 155 slovníčkových hesel již bylo pokryto kromě domluvených výjimek Benji, Bunny a me too. Nové mezery byly v mluvených textech, barvách a školních pokynech.
- Následný audit: 275 sledovaných hesel, 272 obsažených ve slovníku, 3 záměrné výjimky, 0 chybějících hesel.
- Úplný seznam doplnění včetně obou vět je ve `VocabularyEN/mmtx_dialogue_supplement.csv`.
- Zvuky: 239 nových MP3, 845 aktivních unikátních souborů, 850 jazykových odkazů pro 425 karet. Původní audio včetně opraveného cat je zachované.
- Obrázky: 49 nových hesel používá obecnou ilustraci; žádné nové obrázky se negenerovaly.
- Toto je lokální doplnění. Push a publikace Pages ještě nejsou součástí tohoto výsledku.

## Rozsah a pravidla porovnání

Prozkoumány slovníčky a mluvené texty úvodu, Owl Garden, Forest School, scén 1–5 a obou narozeninových scén. Devět zdrojů mluvených textů bylo bajtově porovnáno s veřejným MMTX; kopie původních slovníčků v MatysekANJ odpovídají docs.

Mluvené texty obsahují 321 jedinečných slovních tvarů. Tvary jsou ručně přiřazené k základním heslům (například logs → log, crossed → cross); audit nesčítá každý tvar jako nové heslo.

Jména a citoslovce vyřazené z tokenového auditu: benji, bruno, bunny, caw, fiona, harry, hmm, jane, kate, logan, oh, sunny.

Anglická hesla se porovnávají bez ohledu na velikost písmen a interpunkci. Audit neprohlašuje úplnost všech možných českých významů každého slova. Dřívější překlady a příkladové věty se nepřepisovaly.

Neznámý výraz z budoucího dialogu nyní zablokuje hlášku o úplnosti a vyžádá doplnění kurátorské tabulky; nesmí se tiše ztratit.

## Zdroje

- `docs/forest_school_audio_manifest.js`
- `docs/scene01_audio_manifest.js`
- `docs/scene02_sunnys_lost_nuts/audio_manifest.js`
- `docs/scene03_journey_to_the_lake/audio_manifest.js`
- `docs/scene04_harry_guard_prototype/audio_manifest.js`
- `docs/scene05_log_bridge/audio_manifest.js`
- `docs/scene_jane_birthday/script.js`
- `docs/scene_kate_birthday/script.js`
- `docs/script_intro_v2.js`

## Doplněná hesla

| EN | CZ |
| --- | --- |
| a | neurčitý člen |
| about | o |
| across | přes; na druhou stranu |
| adventure | dobrodružství |
| all | všichni; všechno |
| and | a |
| at | u; v |
| be | být |
| beautiful | krásný |
| birthday | narozeniny |
| brave | statečný |
| bridge | most |
| brown | hnědý |
| cheer | povzbuzovat; jásat |
| color | barva |
| continue | pokračovat |
| cross | přejít; překročit |
| dance | tancovat |
| day | den |
| do | dělat |
| dream | sen |
| eleven | jedenáct |
| else | jiný; další |
| energy | energie |
| excellent | výborný |
| finish | dokončit |
| first | první; nejdříve |
| for | pro |
| from | z; od |
| full | plný |
| give | dát |
| gone | pryč |
| great | skvělý |
| guard | hlídat; strážce |
| happiness | štěstí; radost |
| have | mít |
| he | on |
| health | zdraví |
| heavy | těžký |
| her | ji; jí; její |
| here | tady; sem |
| hi | ahoj |
| him | ho; mu |
| inside | uvnitř; dovnitř |
| it | ono; to |
| job | práce; úkol |
| joy | radost |
| know | vědět; znát |
| laugh | smát se |
| laughter | smích |
| lesson | lekce; vyučovací hodina |
| let | nechat; dovolit |
| listen | poslouchat |
| little | malý |
| log | kláda |
| lots of | hodně |
| lovely | půvabný; krásný |
| many | mnoho |
| me | mě; mně |
| more | více; další |
| my | můj |
| need | potřebovat |
| nice | hezký; milý |
| nine | devět |
| no | ne |
| not | ne; zápor |
| now | teď |
| of | z |
| on | na |
| only | jen; pouze |
| open | otevřený; otevřít |
| or | nebo |
| party | oslava; večírek |
| reason | důvod |
| remember | pamatovat si |
| safe | bezpečný |
| safely | bezpečně |
| save | zachránit |
| school | škola |
| second | sekunda; druhý |
| smile | usmívat se; úsměv |
| so | tak; tak moc |
| some | nějaký; trochu |
| someone | někdo |
| special | zvláštní; výjimečný |
| stay | zůstat |
| step | krok |
| stop | zastavit; přestat |
| stream | potok |
| strong | silný; pevný |
| tap | klepnout |
| ten | deset |
| that | tamten; že |
| the | určitý člen |
| there | tam |
| this | tento; tohle |
| through | skrz; přes |
| to | do; k |
| today | dnes |
| true | pravdivý; skutečný |
| twelve | dvanáct |
| up | nahoru |
| us | nás; nám |
| want | chtít |
| watch | sledovat; dívat se |
| we | my |
| what | co; jaký |
| who | kdo |
| whole | celý |
| why | proč |
| wide | široký |
| will | budu; bude; budoucí čas |
| wish | přát si; přát |
| with | s |
| worry | dělat si starosti |
| year | rok |
| yes | ano |
| yet | ještě; zatím |
| you | ty; vy |
| your | tvůj; váš |

## Ověření

- 15 importních/auditních/mapovacích testů, 11 audio testů a 4 testy JavaScriptu prošly.
- Testována tři celá kola nad 425 kartami včetně přepínání směru.
- Rychlá statická brána prošla.
- Soukromé provozní doklady jsou v data/private/vocabulary_en_mmtx_audit_20260905/.

## Navazující publikace — 2026-09-06 00:24 CEST

Původní lokální výsledek výše je nyní zveřejněný včetně 49 nových,
Mílou schválených ilustrací. Úplná brána prošla 1518 testy. Pages run
33995717491 z d22f25a4 a deployment 6286494824 uspěly. Veřejný manifest
425 karet, app.js a audio manifest jsou bajtově shodné s lokálními;
všech 49 nových obrázků odpovídá schváleným SHA-256. Důkaz je v
vocabulary_en_images_publish_2026_09_06.json. Starší tři vazby na společný
obrázek man pro brother, son a he jsou zachované.
