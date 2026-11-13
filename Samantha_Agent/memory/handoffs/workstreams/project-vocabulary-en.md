# Handoff pracovního proudu: Vocabulary EN

Nazev: Vocabulary EN
Pracovni proud: project-vocabulary-en
Typ: Project
Priorita: 2
Stav: ceka na retest
Pripomenout pri startu: ne
Datum: 2026-11-13 18:56 CET

Co se resilo:
Míla zadal nahrávky všech vět stejnými hlasy jako slovíčka.

Co je hotove:
- Produkční galerie a textové věty z9c6cc825 byly vydané samostatně.
- Nově850 kompletních MP3 vět, přehrávač v obou směrech a soukromý náhled.
- Všech845 slovíčkových MP3, CSV i obsah425 karet beze změny.
- 29 cílených Python včetně27Node PASS; plná brána3831 /646,379s, 5 SKIP, OK.
- Finální zdroje13/13 i850 MP3 shodné s důkazy; handoff, projektová paměť
  a autorský postup jsou součástí stejného místního checkpointu.

Co neni hotove:
- Mílův lidský poslech a fyzická iPhone přejímka.
- Samostatně schválené Pages p+n nových větných nahrávek.

Dalsi krok:
Mílův poslech v již vydaném soukromém náhledu.

Navrhovane dalsi kroky:
- Fyzická iPhone přejímka.
- Samostatné Pages p+n nového audia po přijetí.

Zmenene nebo relevantni soubory:
build_vocabulary_en_sentence_audio.py; vocabulary-en-sentence-audio.json;
gallery.js; model.js; test_vocabularyen_audio_library.py;
test_vocabularyen_selection.js; GALLERY_AUTHORING.txt; nové MP3.

Bezpecnost / neukladat:
Jen veřejné věty do registrovaného Edge TTS. Bez nového placeného provideru,
bez nového TVBCP, bez PythonMF push či nasazení. Cizí main/Will se nemění.
Soukromý Sites náhled zachová původní publikum.

## Historie

### 2026-11-13 13:22 CET — Schválená integrace čtyř Datových commitů

Hotovo: Připravený integrační kandidát nad main9857d2e6 spojuje HA-06,
galerii Vocabulary EN, testovou SDK opravu a přesnou Pages registraci.
77 souborů změněných pouze na main zůstává bajtově shodných; konfliktní
registry zachovávají Willovy záznamy a doplňují Datovy. Původní worktree
Data zůstává čistý na 9f113231; integrační výsledek je připravený k převzetí
na main. Skutečné převzetí potvrzuje závěrečná účtenka v Downloads.

Rozhodnutí: Míla schválil všechny Datovy commity a určil nechat Willovy
stranou. Integrace zachová historii main i schválené f95734f5, 9b584b95,
2f16cf66 a 9f113231. Žádný push, nasazení nebo služba tím nejsou povolené.

Další krok: Samostatně rozhodnout o případném publikačním rozsahu.
Závěrečná účtenka uvádí merge SHA a skutečné fast-forward převzetí na main;
Willovy čekající commity se tímto souhlasem nepublikují.

Navrhované další kroky: Samostatné publikování Vocabulary EN vyžaduje vlastní
schválené p+n a serverově načtenou novou vazbu. Fyzický iPhone a případné
nahrávky vět zůstávají otevřené. Žádný nový Vocabulary EN TVBCP nevznikl.

Technický důkaz: 105 cílených kontrol PASS / 22,338 s; plná integrační brána
PASS: 3823 testů / 580,485 s, 8 SKIP; 3 SDK schema kontroly následně PASS / 0,376 s, zbývá 5 původních SKIP. Zachovaný originální main i Datovy soubory,
žádný reset/rebase/force push. Privátní source manifest a porovnání 77 souborů
jsou v data/private/vocabulary_en_integration_20261113/ integračního worktree.

Rozsah souhlasu k další fázi: Míla schválil čtyři Datovy commity a požádal
nechat Willovy stranou. Toto není souhlas s celým čekajícím GitHub balíčkem.
Běžné p+n audituje celý rozsah origin/main..main, takže se v této etapě
nespouští. Před zveřejněním je potřeba samostatně určit a schválit jeho rozsah.


## 2026-11-13 15:04 CET — Oprava servisního nalezení Node před společným p+n

Hotovo: Regresní test galerie používá stejné nalezení Node jako kanonická
brána. Funguje také při minimálním launchd PATH, bez změny systémového PATH,
instalace či přeskočení testu. Galerie a její produkční data se nemění.

Rozhodnutí: Míla výslovně schválil p+n všech čekajících commitů; tím je
překonané předchozí omezení publikace pouze na Datovy commity. Nejprve
společný runtime, následně vlastní registrovaný Pages cíl Vocabulary EN.
Nový TVBCP se nezakládá.

Další krok: Commit opravy, zarovnání čistých profilů a nové registrované
p+n opraveného headu. Původní nejisté vydání se neopakuje.
Navrhované další kroky: Po potvrzeném nasazení fyzická iPhone přejímka.

Technický důkaz: Původní účtenka a843815b941d7872bcc6e69bea341829 skončila
attention; 3823 testů / 53 skip / 1 error: FileNotFoundError node v novém
galerijním testu. Brána skončila před _push_exact_head; živý GitHub dál
fb062e34, main498ba91a o12 commitů napřed, žádné nasazení. Oprava:29 testů
PASS/13,193s s PATH=/usr/bin:/bin:/usr/sbin:/sbin, včetně skutečných Node
scénářů; rychlá statická brána PASS. Původní důkaz zachovaný v
logs/all_commits_failed_gate_20261113.log a all_commits_runtime_release_20261113.log.


## 2026-11-13 15:55 CET — Procvičování vět a potvrzené vydání galerie

Hotovo: Na velké kartě je přepínač Slovíčko / Věta. Celé věty jdou
procvičovat CZ → EN i EN → CZ, odhalení ukáže obě jazykové verze. Další
sleduje galerii a návrat zvýrazní poslední miniaturu. Volba přežije historii,
obnovu i pokračování; výchozí režim a staré odkazy zůstávají slovíčkové.

Rozhodnutí: Pokračování navazuje na Mílův dřívější požadavek na věty; nové
placené audio se nevytváří. Zvuk v režimu Věta má jasný popisek Slovíčko;
aplikace nehodnotí správnost ani výslovnost. Nový TVBCP nebyl dohodnutý.

Další krok: Mílova přejímka vět na telefonu v aktualizovaném soukromém náhledu.
Místní checkpoint odděluje novou funkci od již vydané produkční galerie.
Navrhované další kroky: Mílova přejímka vět na telefonu; poté samostatné
rozhodnutí o integraci a Pages vydání této nové funkce. Nahrávky celých vět
zůstávají možným odděleným krokem.

Technický důkaz: 25 Node scénářů PASS / 16,511 s; 22 cílených Python testů
PASS / 17,653 s (včetně Node a původních exportních kontrol). Nativní Safari
potvrdilo odhalení obou vět, oba směry, skrytou odpověď na další kartě, úzké
zobrazení a návrat na cow se zvýrazněním Tady jsme skončili. Fyzický iPhone
není tímto doložený. Plná brána PASS: 3823 testů / 927,757 s, 5 SKIP,
0 failures/errors. Všech pět zmrazených zdrojů/testů po bráně bajtově shodných;
source_manifest.json a final_verification.json jsou v
data/private/vocabulary_en_sentences_20261113/.

Dnešní živá kontrola navíc potvrzuje už hotové Pages vydání původní galerie:
účtenka 63ea606335ef4e37fe02905091edfcd3, completed/done, deployed=true,
cíl project-vocabulary-en / github_pages, zdroj 0ec447e7949e343991ed9dc5ae99152c8aab9384.
Veřejné index.html/gallery.js/gallery.css/model.js odpovídaly tomuto main
bajtově (HTTP i SHA-256). Starší zápisy o čekající publikaci jsou historické.
Tento nový režim vět zatím součástí Pages není.

Nezávislý soukromý náhled galerie je již vydaný na
https://vocabulary-en-layout-20261113.fairfly9.chatgpt.site
Site appgprj_6af70efd30b081919af279ac1930a3a6; pouze vlastník, žádné rozšíření
přístupu. Původní verze zdroje cf9063615487740bf320739ea376eb246a51d754,
deployment appgdep_6af7101f75a48191ab43e28c7e545deb. Aktualizace vět: zdroj
3b9c65861001db8cff8ec739a0ae2466d507564b, deployment
appgdep_6af72635871c8191931e5289107d6820 succeeded. Nativní Safari ověřilo
na vydaném webu cat a přepnutí Slovíčko → Věta s celým českým zadáním.
Přístup zůstává pouze vlastník; archiv má shodné čtyři soubory rozhraní,
média i data jsou beze změny. Main a běžící Cockpit se tímto krokem nemění.

Finální uzavření 2026-11-13 16:17 CET: plná brána vocabulary_en_sentences_full_gate_20261113.log
SHA-256 d7fe52a48a1dec3927907612b479cb7cf852f6a348602792f7c0c1c2cc3aa962. Soukromý Sites náhled je
vydaný a prokliknutý v nativním Safari; fyzický iPhone čeká. Všechny nové
zdroje/testy jsou shodné s bránou; původní manifest karet a audia beze změny.
Příští krok je Mílova přejímka, poté samostatné rozhodnutí o integraci/p+n.
Žádný nový TVBCP; checkpoint je místní v Datově větvi, nikoli Cockpit checkpoint.


## 2026-11-13 17:06 CET — Schválené předání vlastních commitů Terře p+n

Hotovo: Režim vět z checkpointu 9ef50b2f je začleněný nad již publikovaný
main4e7007ae. Všechny čtyři webové zdroje jsou shodné s vlastní zelenou
branou 3823 / 927,757 s, 5 SKIP, OK. Willův ISBN krok už je na GitHubu
a má dokončenou vlastní účtenku; do nového publikačního rozsahu nevstupuje
jako čekající cizí práce. Jeho nezávislé soubory zůstávají bajtově shodné,
paměťový index zachovává oba záznamy.

Rozhodnutí: Míla výslovně zadal Terra p+n pro vlastní commity. Předání
použije jediný submit_release(wait=True), projekt project-vocabulary-en,
cíl github_pages a centrální schválenou roli release_executor Terra/high.
Žádné nové TVBCP a žádný restart Cockpitu nebo služby Camino.

Další krok: Po integrační kontrole zarovnat čisté profily a předat přesný
nový main registrovanému vykonavateli. Samostatná soukromá účtenka je
autoritou výsledku; tento zápis není tvrzením o budoucí publikaci.
Navrhované další kroky: Po potvrzeném Pages vydání Mílova přejímka na iPhonu.

Technický důkaz: Živý GitHub audit před integrací byl aligned4e7007ae,
0 čekajících commitů. Willova účtenka d4e292cadfbff224094fd22cb4614ccd
completed/done, pushed=true, deployed=true. Původní Datův worktree
zůstává zachovaný a čistý na 9ef50b2f. Přesný merge SHA a konečnou účtenku
p+n doplní bezpečný TXT výsledek v Downloads a privátní release receipt.


## 2026-11-13 18:39 CET — Schválené větné audio, generování a přehrávač

Hotovo: Prvních šest skutečných MP3 vět je vytvořených a dekódovatelných;
Aria pro EN a Vlasta pro CZ, tempo -10 %. Oddělený generátor navazuje
na původní CSV a 425 párů vět. Rozhraní přehrává celé zadání a po odhalení
pouze cílový překlad, v obou směrech. Původní slovíčkový režim zůstává.

Rozhodnutí: Míla výslovně zadal začít větným audiem a po vysvětlení hlasů
a rozsahu 425 EN + 425 CZ řekl „OK, jdeme na to!“. Jde o pokračování
vlastního vývoje, bez nového souhlasu s Pages p+n. Registrovaný Edge TTS
se používá pro veřejné věty; žádný přechod na placené Azure ani nové modely.
Chybějící edge-tts7.3.1 doplněné jen do privátního generačního prostředí.
První lokální pokus skončil před sítí kvůli chybějící knihovně; nebyla
provedená externí syntéza ani opakovaný nejistý požadavek.

Další krok: Dokončit všech 850 nahrávek, ověřit celou sadu i návrat/obnovu
v aplikaci a uložit vlastní checkpoint. Soukromý Sites náhled se aktualizuje
při zachování publika; nové Pages vydání vyžaduje samostatné p+n.
Navrhované další kroky: Mílův poslech vět a fyzická iPhone přejímka.

Technický důkaz: 13 Python testů generátoru/slovníčkového audia PASS /0,187s;
27 Node scénářů PASS /12,087s, včetně ochrany překladu před odhalením,
neshodných vět a zastavení při navigaci. Šest MP3 dekódovaných ffmpeg,
délka 2,06–3,67s; dvě ukázky přehrané afplay. To nenahrazuje lidskou
přejímku přirozenosti a výslovnosti. Trvalý stav běžící dávky je
data/private/vocabulary_en_sentence_audio_20261113/generation.json.

Předchozí režim vět je už produkčně vydaný z9c6cc825; účtenka
1e2d90febc09702a5538f43a75e50228 completed/done, Terra/high, push i
Pages confirmed, plná brána3823/637,9s a šest HTTP/SHA souborů shodných.
Starší zápisy o čekající integraci/publikaci tohoto režimu jsou historické.
Nové větné MP3 tímto předchozím vydáním zahrnuté nebyly.

Doplnění 2026-11-13 18:47 CET: Všech850 MP3 vytvořených, všech850 dekódovaných ffmpeg,
žádné chybějící. Celkem16 445 376B, délky1,872–5,496s. Původní CSV,
JSON425 karet, slovíčkový manifest a845 slovíčkových MP3 bajtově shodné
s původním manifestem. Safari: obě jazyková zadání, odhalený cílový
překlad, přechod na cow, původní slovíčkový zvuk i návrat na poslední
dlaždici. 29 cílených Python testů (včetně27Node scénářů) PASS /12,853s.
Plná brána běží nad13 zmrazenými zdroji/testy/daty; MP3 mají samostatné
otisky v audio_verification.json. Soukromý náhled se aktualizuje.

Soukromý Sites náhled aktualizovaný, audience pouze vlastník:
https://vocabulary-en-layout-20261113.fairfly9.chatgpt.site
Zdroj4eb3854dff55272de031acba563dbc38908cb3db, deployment
appgdep_6af74d752cac8191a325f8c7e4f74b07 succeeded. Archiv ověřený proti
všem850 MP3 i třem změněným JSON/JS souborům. Lokální Safari přehrávání
ověřené; následné otevření vzdáleného náhledu nemohlo být dokončené,
protože se nativní okno Safari souběžně měnilo. Fyzický iPhone čeká.


## 2026-11-13 18:56 CET — Větné audio dokončené a ověřené

Hotovo:425 anglických a425 českých vět mají vlastní nahrávky Aria/Vlasta
při tempu -10 %. Věta přehraje zadání; po odhalení odpovědi lze přehrát
cílový překlad. Původní slovíčka i845 MP3 jsou zachované. Soukromý náhled
je vydaný na stejné adrese a přístupný pouze vlastníkovi.

Rozhodnutí: Dokončený schválený vývoj s externí syntézou přes původní Edge
TTS. Žádné nové placené Azure/modelové volání, žádný nový TVBCP a žádné
PythonMF p+n nebo změna Willova main.

Další krok: Mílův lidský poslech a fyzická iPhone přejímka soukromého náhledu.
Navrhované další kroky: Po přejímce samostatné schválené Pages p+n audia.

Technický důkaz: Plná brána3831 testů /646,379s, 5 SKIP, OK. Dříve29
cílených Python včetně27Node PASS /12,853s. Všech13 zmrazených vstupů
po bráně shodných;850/850 MP3 dekódovaných a beze změny, původní CSV,
karty, slovíčkový manifest a845 MP3 rovněž shodné. Celkem16 445 376B nového
audia; délky1,872–5,496s. Nativní Safari lokálně potvrdilo obě jazyková
zadání, oba cílové překlady, skrytou odpověď po Další, slovíčkový zvuk
a návrat na poslední miniaturu. To není fyzická iPhone ani lidská přejímka.

Soukromý Sites: zdroj4eb3854dff55272de031acba563dbc38908cb3db, deployment
appgdep_6af74d752cac8191a325f8c7e4f74b07 succeeded,850 MP3 a3 změněné
JSON/JS soubory v archivu bajtově ověřené. Pokus o následné zobrazení
vzdálené verze v Safari zastavený při souběžně se měnícím okně; úspěšný
nativní deployment je ověřený a místní browser přehrávání potvrzené.

Log: vocabulary_en_sentence_audio_full_gate_20261113.log
SHA-256:7a55c1ad64af68f438134840913d5fcc12db6917aa1171dd26679e3754baed42
Privátní důkazy: data/private/vocabulary_en_sentence_audio_20261113/.
Scénář v Downloads: Vocabulary_EN_vetne_audio_2026-11-13.txt.
