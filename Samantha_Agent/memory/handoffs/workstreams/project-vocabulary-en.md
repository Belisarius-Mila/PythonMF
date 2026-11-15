# Handoff pracovního proudu: Vocabulary EN

Nazev: Vocabulary EN
Pracovni proud: project-vocabulary-en
Typ: Project
Priorita: 2
Stav: mistne hotove dve davky10+20, overeno, ceka na samostatne Pages p+n
Pripomenout pri startu: ne
Datum: 2026-11-15 11:43 CET

Co se resilo:
První desítka a dalších20 schválených slovíček z TXT návrhu MMTX Cesta
k jezeru podle kanonického autorského postupu.

Co je hotove:
- První desítka ven-0453–0462 a druhá dvacítka ven-0463–0482;
  celkem482 záznamů/472 aktivních,453 Slovíček a19 Interakcí,18 témat.
- Druhá dávka:20 EN/CZ vět,20 explicitních obrazů/náhledů a80 nových MP3;
  13 nových ilustrací,1 upravený závod a6 převzatých.
-52 cílených Python testů včetně56 Node scénářů a statická brána PASS.
-462 starších položek/identit a2688 médií přesně shodných;80 dekódovaných
  MP3,123 místních HTTP souborů shodných,148 zdrojů zmrazených po ověření.
- Obě místní dávky zatím nebyly publikované; poslední vlastní potvrzené
  Pages vydání2779af14 obsahovalo452/442. Nové p+n nezadané.

Co neni hotove:
Publikování obou dávek10+20 a fyzická přejímka telefonu.

Dalsi krok:
Na samostatný pokyn Terra Pages p+n s čerstvým auditem celého balíčku.

Navrhovane dalsi kroky:
Přejímka nových30 karet a A–D na telefonu; dalších35 hesel ze zásobníku MMTX.

Zmenene nebo relevantni soubory:
CSV/katalog;3 webové manifesty;20 zdrojových obrazů,20 webových kopií,
20 náhledů a80MP3;3 inventární testy; reports/vocabulary_en_lake_batch2_20261115.md.

Bezpecnost / neukladat:
Vlastní větev data/vocabulary-lake-batch1-20261115 navazuje druhou dávkou
na58e30135 (první desítka), základ d141d030. Souběžný main se nemění.
Dávky first10 i next20 jsou applied; žádné opakování médií/přípravy.
Soukromé doklady v data/private/vocabulary_lake_batch2_20261115/ a původním
autorském store. Nové karty nepřebírají A–D ani Benji. Nový TVBCP není sjednaný.

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


## 2026-11-13 20:54 CET — Poslech anglických slovíček přímo z galerie

Hotovo: Galerie má přepínač Učení / Poslech dostupný i při posouvání.
V Učení klik otevře kartu, v Poslechu přehraje existující anglickou MP3
a zůstane v galerii. Opakovaný klik zvuk zopakuje, jiná dlaždice zastaví
předchozí zvuk. České popisky ani režim vět jazyk poslechu neovlivní.

Rozhodnutí: Míla odsouhlasil návrh jedním klikem v explicitním režimu;
dvojklik se nepoužívá. Výchozí Učení, Poslech platí pro otevřenou stránku
a nepřepisuje uložený učební kontext. Mód se přepíná bez překreslení
dlaždic, posunu, změny filtrů nebo poslední učené karty.

Další krok: Aktualizovat stejný soukromý náhled a dokončit vlastní checkpoint.
Navrhované další kroky: Mílova iPhone přejímka; potom samostatné Pages p+n
obou vlastních kroků, větného audia a poslechu dlaždic.

Technický důkaz: 30 cílených Python testů včetně 34 Node scénářů PASS
/ 14,959 s. Pokrytý EN poslech s CZ popisky a režimem vět, opakování,
zastavení, neměnná historie/scroll/storage/bookmark, chybějící či neshodné
audio, pozdní chyba a návrat k učení. Safari desktop potvrdilo cat/cow
bez otevření karty, CZ popisky a stále dostupný přepínač ve středu galerie.
Pokus o úzké okno skončil noWindowsAvailable; fyzický iPhone není doložený.
Původní CSV, data karet a oba audio manifesty jsou shodné; nové TTS volání
nevzniklo. Nový krok mění pouze UI, bez nové persistence nebo workflow;
ověřuje se cílenou sadou a statickou branou. Předchozí plná brána 3831
patří checkpointu větného audia 3ca7bf0d, nikoli tomuto novému UI.


## 2026-11-13 20:58 CET — Poslech dlaždic dokončený v soukromém náhledu

Hotovo: Přepínač Učení / Poslech je dostupný i uprostřed dlouhé galerie.
Kliknutí v Poslechu přehraje existující EN slovíčko, v Učení otevře kartu.
Opakování, vystřídání zvuku a neměnný učební bookmark jsou ověřené.
Soukromý náhled obsahuje i předchozí větné audio; původní publikum zachované.

Rozhodnutí: Hotový vlastní terminálový krok, bez nových MP3, modelových
volání, persistence, TVBCP a PythonMF p+n. Cizí main/Will beze změny.

Další krok: Mílova iPhone přejímka přepínače a poslechu v soukromém náhledu.
Navrhované další kroky: Samostatné schválené Pages p+n obou vlastních kroků.

Technický důkaz: 30 cílených Python testů včetně 34 Node scénářů PASS
/14,959s. Safari desktop: cat/cow, opakování, CZ popisky a přepínač při
posunu; žádné otevření velké karty. Úzké okno nebylo dokončené po
noWindowsAvailable, fyzický iPhone čeká. Všechny čtyři zmrazené zdroje/testy
jsou shodné; CSV, data425 karet a oba audio manifesty jsou beze změny.
Log vocabulary_en_gallery_listen_targeted_final_20261113.log
SHA-256:d0f373de623d554609758e7533f62664e4c49fb7c48a1af12ec9e41e63d58b1f

Sites zdroj6592f7771f0f0004163cafd508e20843e63879ca, deployment
appgdep_6af76cd6193081918923335752327ec6 succeeded. Přesně tři změněné
frontend soubory, archiv bajtově shodný, audio se neměnilo.
https://vocabulary-en-layout-20261113.fairfly9.chatgpt.site
Scénář v Downloads: Vocabulary_EN_poslech_dlazdic_2026-11-13.txt.

Závěrečné doladění: hláška v přepínači má min-width:0 a zalamování dlouhých
slov, aby na úzkém displeji nevynucovala vodorovný posuv. Finální Node retest:
34/34 PASS /14,441s. Finální statická brána PASS, soukromá verze obsahuje
tuto stejnou CSS.


## 2026-11-13 23:33 CET — Kandidát pro schválené p+n obou vlastních kroků

Hotovo: V izolovaném integračním worktree jsou spojené vlastní commity
3ca7bf0d (850 větných MP3) a581fbed3 (Poslech/Učení dlaždic) nad main908a6aee.
Všechny vlastní zdroje a média zůstávají bajtově shodné, nezávislé Willovy
soubory také. Jediný konflikt v dodatcích Lessons Learned vyřešen zachováním
celých obou bloků; index zachovává oba proudy. Původní Data zůstává čistý.

Rozhodnutí: Míla zadal „OK, prosím p+n...“ pro navazující dva vlastní kroky.
Předchozí hranice ponechat Willovy commity stranou zůstává platná. Živý
GitHub audit našel originbb05bf8f a jeden cizí nepublikovaný commit908a6aee
(Knihovna: místní miniatury a katalogové žánry). Registrované p+n odesílá
celý origin/main..main; tento cizí commit nelze přeskočit.

Další krok: Po ověření kandidáta samostatně potvrdit, zda lze k odeslání
na GitHub zahrnout i908a6aee, nebo zachovat vlastní rozsah a počkat na jeho
vydání. Do té doby žádný main fast-forward, push, modelové předání ani deploy.
Navrhované další kroky: Schválené Pages vydání Vocabulary EN, potom fyzická
iPhone přejímka; publikace Knihovny do Cockpitu je jiný cíl.

Technický důkaz: Živý audit ready,1 pending cizí commit, poslední runtime
releasebb05bf8f completed/pushed/deployed. Po případném schválení širšího
GitHub rozsahu použít jediný submit_release(wait=True), projekt
project-vocabulary-en, centrálního release_executor a cíl github_pages.
Nový TVBCP nevzniká, běžící Cockpit ani Camino se tímto Pages krokem nenasazují.

Integrační přejímka: 30 cílených Python testů včetně34Node scénářů
PASS /23,001s; statická brána PASS. Kandidát je připravený k rozhodnutí
o přesném GitHub rozsahu, produkce ani main zatím nezměněné.


## 2026-11-13 23:45 CET — Schválený celý čekající GitHub balíček

Hotovo: Integrační kandidát b5a2383a je ověřený, vlastní větné audio
a poslech dlaždic i nezávislé Willovy zdroje jsou zachované.

Rozhodnutí: Na přesný dotaz k cizímu pending908a6aee Míla odpověděl
„Vezmi všechny commity prosím...“. Tím výslovně rozšířil GitHub rozsah
a překonal předchozí omezení ponechat Willův commit stranou. Schválené
jsou vlastní3ca7bf0d+581fbed3, integrační mergeb5a2383a a čekající908a6aee
včetně nutného dokumentačního potvrzení tohoto rozhodnutí. Nasazovaný
cíl zůstává project-vocabulary-en / github_pages. Nejde o nový runtime
deploy Knihovny/Cockpitu ani změnu služby Camino.

Další krok: Převzít ověřenou integraci na čistý main, zarovnat čisté profily
a předat přesný head registrovanému submit_release(wait=True). Role
release_executor se bere z centrálního JSON; očekávaná Terra/high.
Navrhované další kroky: Po potvrzeném Pages vydání fyzická iPhone přejímka.

Technický důkaz: Integrační30 Python testů včetně34Node PASS /23,001s,
statická brána PASS. Předpoklad před převzetím: main908a6aee, originbb05bf8f,
profily zarovnané a žádná aktivní release úloha. Konečný výsledek autoritativně
v privátní release účtence a závěrečném TXT v Downloads; tento zápis
sám budoucí push ani nasazení nepotvrzuje. Nový TVBCP nevzniká.


### 2026-11-14 00:03 CET — Oprava testovacího přípravku před vydáním

Hotovo: Příčina zastaveného vydání je dohledaná. Sedm testů následných
změn e-mailové služby selhalo při pomocném Git commitu, kterému chyběla
syntetická identita. Doplněny stejné lokální parametry -c jako u ostatních
commitů přípravku; produkční kód ani konfigurace Gitu se nemění.

Rozhodnutí: Platí Mílův výslovný souhlas se všemi čekajícími commity včetně
Willova908a6aee; cílem nasazení zůstává pouze Vocabulary EN GitHub Pages.
Předchozí job d8a4ccdf718ec01252b852bf3bb7d1d7 je zachován jako attention.

Další krok: Po cílených testech a statické bráně předat opravený přesný
main registrovanému vykonavateli s novou identitou vydání.

Navrhované další kroky: Dokončit Pages ověření a Mílův poslech na iPhonu.
Bez nového TVBCP; jeho založení nebylo dohodnuté.

Technický důkaz: Původní plná brána3858 testů /731,197s skončila právě
7 chybami ve followup_install, před push. Čerstvý ls-remote potvrdil původní
origin bb05bf8f; publikace nezačala. Původní log zachovaný v soukromém
vocabulary_en_audio_listen_release_20261114_fixture_fix/failed_gate_20261113.log.
Cílená sada30 testů PASS /19,618s a statická brána PASS; vlastní
logs/vocabulary_en_release_fixture_* protokoly. Konečný provozní výsledek patří do privátní účtenky a Downloads.


## 2026-11-14 10:33 CET — Sekundová česká nápověda při poslechu

Hotovo: Kliknutí na dlaždici v Poslechu přehraje původní EN slovíčko
a na1000ms ukáže český popisek. Potom se vrátí původní popisek.
Míla upřesnil zachovat anglický název i v českém směru procvičování;
CZ→EN ani EN→CZ proto jazyk běžného popisku nemění. Stávající samostatný
přepínač popisků EN/CZ zůstává zachovaný. Míla předchozí produkční
slovník i nalezené věty přijal; nejde o novou syntézu nebo úpravu obsahu.

Rozhodnutí: Nový klik obnoví celou sekundu. Jiná dlaždice vrátí předchozí
popisek hned. Změna režimu, filtrů, jazyka popisků, otevření učení
a opuštění stránky krátkou nápovědu ukončí. Poslech nemění bookmark,
historii, filtry ani uložený učební kontext.

Další krok: Samostatné Pages p+n nové české nápovědy. Předchozí souhlas se všemi commity patřil dokončenému
vydání9ab2c87b a nepředstírá publikaci tohoto nového kroku.

Navrhované další kroky: Po schváleném vydání ověřit délku nápovědy na iPhonu.
Nový TVBCP není dohodnutý, proto nevzniká.

Technický důkaz: Nativní Safari v místním náhledu zobrazilo po kliknutí
kočka a následně znovu cat se zvukem, bez otevření karty. Node sada má
37 scénářů PASS /35,520s včetně časování999/1000ms v obou směrech,
opakovaného kliknutí a rušení nápovědy. Statická brána PASS. Finální protokol: vocabulary_en_translation_flash_node_final_20261114.log.
Původní CSV,425 karet, oba audio manifesty, obrázky i MP3 zůstávají beze změny.
Fyzický iPhone a nové produkční vydání tímto krokem nejsou potvrzené.


## 2026-11-14 10:39 CET — Schválené produkční vydání české nápovědy

Hotovo: Izolovaná integrace c372ada6 nad publikovaným main e53dd971.
JS, testy a návod jsou bajtově shodné s37 scénáři PASS. Obě historie
paměťových zápisů jsou zachované, původní média i cizí práce také.

Rozhodnutí: Míla zadal „OK, prosím dej na produkce jestli je to možné...“.
Cíl project-vocabulary-en / github_pages, cesta vocabulary-en/.
Bez runtime nasazení Cockpitu, bez syntézy a bez nového TVBCP.

Další krok: Po bezpečné připravenosti kanonického main a profilů
převzít přesnou integraci a jednou zavolat submit_release(wait=True).

Navrhované další kroky: Fyzická přejímka krátké nápovědy na iPhonu.

Technický důkaz: Při přípravě main e53dd971 odpovídá GitHubu, ale má
cizí rozpracované Vocabulary FR a nezařazený agent_supervisor 2.md.
Živý github-batch-audit: audit_failed; deploy-audit: ready=false.
Cizí obsah se nemění, nezařazuje ani neodkládá. Release nebyl spuštěný.
Konečný výsledek patří do privátní účtenky a Downloads.


## 2026-11-14 10:41 CET — Připravené přesné vydání, čeká rozhodnutí o okolním stavu

Hotovo: Kandidát obsahuje českou nápovědu c372ada6 a aktuální kanonický
main4ad82a7f. Vlastní gallery.js,37scénářový test i návod jsou stále
bajtově shodné s otestovaným checkpointem; cizí FR změny se neupravovaly.

Rozhodnutí: Produkční Vocabulary EN vydání je výslovně schválené.
Nový cizí pending commit4ad82a7f vznikl souběžně a nebyl součástí
předchozího konkrétního publikačního balíčku. Jeho GitHub zahrnutí
vyžaduje potvrdit rozsah. Samotné nasazení zůstává Vocabulary EN Pages.

Další krok: Potvrdit zahrnutí4ad82a7f do GitHub balíčku a zachování
starší nezařazené kopie agent_supervisor 2.md v ignorovaném privátním
archivu. Teprve pak čistý main/profily a registrované p+n.

Navrhované další kroky: Krátká fyzická iPhone přejímka po publikaci.

Technický důkaz: Cizí nezařazený soubor je7777B, SHA-256
08bf3f5c2fa41d235ea9678e978cfe6dce9700863e0dbe8e2bb1b78c17717f12.
Nemá se mazat ani commitovat; navržený archiv zachová přesné bajty.
Živá publikační brána odmítá nečistý main a nezarovnané profily.
Dosud žádný push, modelové předání ani deploy. Konečné provozní důkazy
patří do privátní účtenky a Downloads, nikoli do dalšího pending commitu.


## 2026-11-14 11:07 CET — Společné vydání všech lokálních a Datových commitů

Hotovo: Do společného kandidáta je převzatý celý hotový Datův krok české
sekundové nápovědy při anglickém poslechu. Kód,37Node scénářů a návod jsou
bajtově shodné s Datovým kandidátem9f759706; jeho původní worktree je čistý
a zachovaný. Dnešní již veřejně ověřená sova zůstává bajtově beze změny.

Rozhodnutí: Po dokončení sovy Míla výslovně zadal nasadit všechny lokální
commity včetně Datových. Tím je potvrzený i dříve čekající společný GitHub
rozsah. Cíl zbývajícího vývoje je project-vocabulary-en / github_pages;
statické Pages obsahují také dnešní sovu. Žádný nový TVBCP nebyl sjednaný.

Další krok: Přesný integrační checkpoint předat jednou registrovanému
submit_release(wait=True), po plné bráně ověřit původní Pages běh i veřejné
gallery.js a dnešní soví audio. Konečný výsledek patří do soukromé účtenky
data/private/all_local_data_release_20261114/release_receipt.json a
public_verification.json; tento přípravný zápis sám nasazení nepotvrzuje.

Navrhované další kroky: Fyzická iPhone přejímka sekundové nápovědy.

Technický důkaz: Integračních11 Python testů včetně Node scénářů PASS /23,964s.
Zdroj před integracíb2bfb8b2, vlastní Datův krokc372ada6, integrační historie
e9cb0f9d+9f759706. Převzetí bez konfliktu; ostatní změny zachované.
Statická brána logs/all_local_data_release_20261114_static.log.


## 2026-11-14 12:35 CET — Místní profily A–D a přenos osobních výběrů

Hotovo: Nastavení nabízí vlastní slovní zásobu A–D, místní PIN4–8 číslic,
výběr jednotlivých slov i celého zobrazeného tématu. V galerii přibylo
Všichni/A/B/C/D, Jen obtížná a Výběr obtížných slov. Osobní výběr
se protíná se stávajícími filtry; všech18 definic témat zůstává stejných.
Věty, poslech, náhodné kolo a návrat do galerie pracují s osobním výběrem.

Rozhodnutí: Míla zvolil ukládání zvlášť v každém prohlížeči a schválil
zálohu/načtení. Bez serveru, účtů a automatické synchronizace zařízení.
PIN chrání úpravy jako místní pojistka; ukládá se pouze náhodná sůl
a PBKDF2-SHA256 hash, nikoli číslice PINu. Záloha obsahuje výběry A–D
bez PINů. Obnova načte do návrhu právě otevřeného uživatele; vyžaduje
Uložit a zachová ostatní uživatele i zdejší PIN. Nový TVBCP není dohodnutý.

Další krok: Přejímka na PC/Android/iPhonu podle scénáře v Downloads. Předchozí publikace české sekundové
nápovědy je na Mílův pokyn odložená; FR commit musí zůstat stranou.
Tento vývoj nepovoluje nové p+n a produkci nemění.

Navrhované další kroky: Mac/PC a fyzický Android/iPhone přejímka podle
Vocabulary_EN_profily_A-D_test_2026-11-14.txt v Downloads, potom
samostatné rozhodnutí o produkčním vydání.

Technický důkaz: Samostatné learners.js a learner-ui.js, známé UID místo
pořadí řádků, záloha validovaná před použitím, žádné cizí HTML.
Ověření read-back zápisu a kontrola původního místního snímku brání
přepsání změn z druhého okna. Poškozené/zakázané úložiště neblokuje
společný slovník a nepřepisuje se prázdnými daty. Pozdní import nesmí
přepsat dalšího uživatele nebo novější ruční úpravy. Safari ukázalo
Přehled/Nastavení/PIN formulář; úplná ruční přejímka byla přerušená
souběžným používáním Safari. Žádná fyzická mobilní přejímka není doložená.
Finální testy a otisky budou v privátním vocabulary_en_learners_20261114/.


Ověření a checkpoint: Plná brána PASS,3831 testů /670,998s unit část,
683,815s celý běh,5 SKIP, bez failures/errors. 48 cílených Node scénářů
PASS /20,384s. Po bráně13/13 zmrazených souborů shodných; následné
změny jen v zápisu výsledků a poučení,8/8 zdrojů aplikace a testů zůstává
shodných s testovaným stavem. Před commitem ještě rychlá statická brána.
Log vocabulary_en_learners_full_gate_20261114.log, SHA-256:
fc8368436ebff87cb506120f46ddfda8b4f246dca1cba9378b92cb4e18be2fa1
Skutečná Git identita se neměnila; syntetická identita byla pouze v env
testovacího procesu kvůli již známému pomocnému Git commitu přípravku.
Privátní verification.json/source_manifest/checkpoint zůstávají autoritou
konkrétního checkpointu. Žádný nový push, deploy ani TVBCP.


## 2026-11-14 13:30 CET — Schválené p+n místních profilů A–D

Hotovo: Přesný vlastní24d26fa5 integrovaný nad publikovaný main5b9dda8e.
Všech8 zdrojů aplikace a testů shodných s checkpointem48 Node PASS
a plnou branou3831 PASS; paměťové konflikty zachovaly oba celé záznamy.

Rozhodnutí: Míla výslovně zadal „Nejprve p+n prosím.“ pro profily A–D.
Cíl project-vocabulary-en / github_pages / vocabulary-en/.
Živý ls-remote potvrdil5b9dda8e; dříve vyloučený FR commit4ad82a7f už
je v GitHub main. Do nového rozsahu se tedy FR ani sova nově nepřidávají.

Další krok: Po kontrole integrace převzít čistý main/profily a předat
přesný nový head jedinému submit_release(wait=True). Nový TVBCP nevzniká.

Navrhované další kroky: Produkční přejímka PC/Android/iPhone podle TXT
v Downloads po potvrzeném Pages vydání.

Technický důkaz: Pouze Vocabulary EN runtime/testy/návod a paměť;
ostatní5b9dda8e soubory zachované. Konečný push, deploy, plná publikační
brána a veřejné otisky patří do privátní účtenky a Downloads.
Běžící Cockpit, Camino a autosave se tímto Pages krokem nenasazují.

Integrační přejímka:30 cílených Python testů včetně48 Node scénářů PASS
/16,834s. Rychlá statická brána PASS.8/8 zdrojů a testů shodných s24d26fa5.
Připravený rozsah proti GitHub5b9dda8e tvoří pouze vlastní checkpoint
a integrační merge. Profily při přípravě čisté a zarovnané s main5b9dda8e.


## 2026-11-14 19:24 CET — Typ učiva, interakce a bezpečné vyřazení

Hotovo: Místně nový filtr Vše / Slovíčka / Interakce / Fráze. Aktivní
nabídka má415 karet:396 slovíček a19 Interakcí. Kategorie Fráze je připravená
pro budoucí celé idiomatické výpovědi, současné schválené položky ji nenaplňují.
Všech18 témat, původních425 identit, obrázky i osobní výběry zůstávají zachované.

Rozhodnutí: Míla schválil rozdělení36 dosavadních výrazů, vyřazení samostatných
větných vzorů a ponechání would like jako slovesného výrazu. Dále zadal vyřadit
běžné pravidelné plurály při existenci jednotného čísla, nepravidelné zachovat.
Dovolil úplné smazání jen pokud nenaruší vazby; jinak skrytí. Kvůli uloženým UID
v jednotlivých prohlížečích zvolené active=false, bez výmazu nebo recyklace ID.

Další krok: Po místním checkpointu
samostatně integrovat do aktuálního main se zachováním Willových změn a po
odpovídajícím pokynu provést registrované Pages p+n. Žádné p+n ani runtime restart
se tímto vývojem nespouští; Cockpit HTTPS změna je v jiné zachované větvi.

Navrhované další kroky: Fyzická přejímka filtru a uloženého A na telefonu;
obsahová revize dalších nejednoznačných slovních druhů. Oxford pouze čeká na
uživatelem odeslaný licenční dotaz, žádná Oxford data nejsou přebírána. Budoucí
nové idiomy vybírat jako samostatný obsahový krok, nevytvářet je tímto vydáním.

Technický důkaz:29 cílených Python testů PASS /27,329s včetně53 Node scénářů;
18 kontrol brány PASS /6,974s. Ověřený skutečný controller: filtr s tématy,
osobním A a historií/reloadem; žádná vyřazená karta v učení, poslechu, náhodném
kole, přímém odkazu nebo Nastavení. Všechny čtyři profily zachovají vyřazená
UID při změně obtížnosti, hromadné úpravě viditelného tématu, Uložit a záloze.
Import skryté karty zachová a vysvětlí. Finální plná brána PASS:3880 testů /871,256s,31 SKIP. Všech19/19 finálních
souborů kódu, dat a nových MP3 shodných se zmrazeným manifestem tohoto běhu.
2473 původních mediálních souborů má stejné bajty;6 nových MP3 dekódovaných.

Vyřazené vzory:ven-0199 we can;ven-0203 we are;ven-0257 I have;
ven-0258 I don't have;ven-0259 Do you have?;ven-0260 Does he have?.
Vyřazené pravidelné plurály:ven-0195 apples→ven-0117 apple;
ven-0197 pigs→ven-0182 pig;ven-0200 friends→ven-0045 friend;
ven-0271 bears→ven-0173 bear. Vazba singularUid zůstává v autorském katalogu.
Plurály bez samostatné jednotné karty (eyes, parents, potatoes, boots, nuts)
a samostatné pojmy jako pants zůstávají; žádné strojové odřezávání koncovek.

Obsahové opravy schváleného návrhu:ven-0062 I (am) / já (jsem)→I / já,
stejné UID ven-0062, audio ID62 a přesný původní iam.png/náhled; původní EN/CZ match rezervovaný.
Příklad I am ready now—let’s start. U sure věta Sure, I can help you. /
Jistě, mohu ti pomoci. U please odstraněná zatoulaná uvozovka. Výslovně
schválené doplnění2 slovních a4 větných MP3 stejnými hlasy/tempy přes registrovaný
syntetizér; žádné automatické opakování nebo přepis starých souborů.

Typ učiva je nezávislý na expressionType (počet slov), partOfSpeech i18 tématech.
Celé věty nemají předstíraný slovní druh Fráze; krátké komunikační projevy mají
kontextově určený druh nebo prázdné partOfSpeech s obvyklou skupinou Další výrazy.
How much zůstává slovíčkem, ale gramatická funkce je označena k revizi.
CSV má pouze3 opravené řádky, zachované CRLF a všech425 záznamů. Oba audio
manifesty pořád pokrývají425 identit. Žádný osobní PIN/výběr není v Gitu.

Předání: vlastní větev data/vocabulary-types-20261114 nad68d2b720, oddělená
od Cockpit větve data/cockpit-web-navigation-20261114 s50f113f5+a356e51d.
Původní Data/Will/main se tímto krokem nemění. Vocabulary EN nemá dohodnutý
samostatný TVBCP; v terminálovém vývoji aktualizovaný tento kanonický handoff,
projektová paměť, report a registry. Nový TVBCP nebyl založen.
Důkazy mimo Git:data/private/vocabulary_types_20261114/ (baseline, audio_plan,
word_generation, sentence_generation, preservation_verification, gate_sources,
test_timings). Logy: logs/vocabulary_types_targeted_final_20261114.log,
logs/vocabulary_types_gate_tests_20261114.log a logs/vocabulary_types_full_gate_20261114.log.
Živé Mac/iPhone přijetí a nový veřejný obsah nejsou těmito testy doložené.

Technická mez: skrytí je implementované ve webové galerii EN. Starší desktopový
trainer čte kompatibilní CSV včetně425 historických položek; jeho samostatné
ovládání se tímto krokem nemění. EN83 a sdílené app.js/styles.css beze změny.

Integrační hranice: tato větev vychází z68d2b720. Při pozdějším převzetí
nepřepisovat celé aktuální CSV z main. Zkontrolovat diff tří opravovaných
řádků a zachovat případné novější L/HT/WS i nesouvisející doplnění. Stejně
zachovat Willovy změny knihovny a FR mapování; žádná změna Pict/mapping.json
v tomto kroku nevznikla. Publikační balíček se audituje až po integraci.


## 2026-11-14 — Schválené Terra p+n typů učiva

Míla výslovně požádal „OK. prosím Terra p+n.“ Vlastní checkpoint c551b348
je integrovaný nad aktuální main24096145, jehož knihovna a Cockpit už jsou
na origin/main. Všech18 samostatných zdrojů/dat/nových MP3 odpovídá původní
zelené bráně;41 nezávislých souborů novějšího main zůstává bajtově shodných.
Sdílené registry zachovávají oba proudy a brána současně zahrnuje aktuální
knihovní moduly i exportér Vocabulary EN. Integrační47 testů PASS /33,497s.

Další krok: po rychlé statické kontrole vlastní integrační checkpoint,
fast-forward čistého main, bezpečné zarovnání profilů a jediný registrovaný
submit_release(wait=True). Cíl project-vocabulary-en / github_pages,
centrální release_executor Terra/high; žádný další runtime deploy Cockpitu.
Request data-vocab-types-20261114-v1, deterministická účtenka 4e5e18a70db086fa6eac083f0f9e2984.
Plnou publikační bránu provede worker nad přesným finálním headem. Tento
přípravný zápis nepotvrzuje budoucí push ani nasazení; autoritou výsledku
je data/private/vocabulary_types_release_20261114/result.json a závěrečné
public_verification.json/final_receipt.json na kanonickém main, též TXT
v Downloads. Fyzická přejímka telefonu zůstává následná. Bez nového TVBCP.


## 2026-11-14 20:59 CET — Významové karty a obsahová revize

Hotovo: Zkontrolovaných19 položek,17 nových významových/slovnědruhových karet
ven-0426 ažven-0442. Celkem442 záznamů,432 aktivních:413 Slovíček a19 Interakcí.
Všech18 témat a425 původních UID/audio ID/proveniencí/L/HT/aktivit zachovaných.
Běžné další významy second/help/free/right/open/smile atd. mají vlastní věty
a vlastní identitu; opatrně je správně carefully. Osm nových ilustrací,
31 nových slovních a42 větných MP3 stejnými hlasy/tempy.

Rozhodnutí: Míla schválil opravu chyb i doplnění významových karet, vět
a podle potřeby obrázků. Jedna karta procvičuje jasný význam; stejné anglické
heslo může mít více karet. Správné další významy se nezahazují. Nové karty
nevstupují automaticky do osobních výběrů A–D ani do zdrojového Benji.
Samostatný TVBCP nebyl dohodnutý a nevzniká. Vývoj probíhá ve vlastní větvi
data/vocabulary-meanings-20261114 nad64e9897a, zachovává současnou knihovnu.

Další krok: Po plné bráně vlastní místní checkpoint; nové Pages p+n je
samostatný navazující krok. Poslední potvrzené Pages p+n je2b17cbb4, účtenka
4e5e18a70db086fa6eac083f0f9e2984 completed/confirmed,3912 testů a17 veřejných
souborů shodných. Tento nový obsah ještě není nasazený.

Navrhované další kroky: Přejímka nových významů a výběrů na telefonu;
samostatné Pages vydání; autorský vstup a budoucí idiomy. Oxford stále čeká
na Mílův dotaz, žádná Oxford data nejsou přebíraná.

Technický důkaz:36 cílených Python testů PASS /19,288s včetně55 Node scénářů,
nových kontrol obou second a samostatných osobních výběrů. Všech2479 původních
médií bajtově shodných; všech73 nových MP3 dekódovaných ffmpeg. Benji autorství
rozlišuje původní Order i heslo, aby další významy nezdědily nesprávný zdroj.
Historický desetiheslový casting včetně40MP3 zůstává původní; testuje se proti
jeho historickému vstupu a současné CSV přísně odmítne jako změněný zdroj.
Plná brána PASS:3920 testů /706,416s unit část,31 SKIP. Všech107 finálních zdrojů/testů/dat/médií je shodných s finální branou.
Dva nepoužité nové náhledy others/proverbs z předběžných exportů jsou zachované v soukromém
archivu mimo publikační balíček. Finální výsledek a otisky jsou v soukromém
data/private/vocabulary_meanings_20261114/verification.json a checkpoint.json.
Browser host při pokusu o místní proklik nebyl dostupný; aktuální vizuální
přejímka celé stránky ani fyzického telefonu tím není doložená.


## 2026-11-14 21:29 CET — Finální místní uzavření revize

Hotovo:442 záznamů/432 aktivních,17 nových významových karet. Všech19
zrevidovaných karet má pevnou vazbu na schválený obrázek;424 původních
obrázkových vazeb zachovaných, pouze free má záměrně nový obraz volného času.

Rozhodnutí: Rozsah Mílova schválení je stejný; žádné nové rozhodnutí ani TVBCP.
Další krok: Samostatně schválené Pages p+n.
Navrhované další kroky: Přejímka významů a osobních výběrů na telefonu.

Technický důkaz: Finální plná brána3920 PASS /706,416s unit část,
31 SKIP,0 failures/errors;36 cílených Python včetně55 Node PASS /36,142s.
Všech107/107 finálních zdrojů/testů/dat/médií shodných s touto branou;
2479 původních médií zachovaných,73 nových MP3 dekódovaných.
První zelená brána byla doplněná závěrečnou kontrolou původních obrazových
vazeb: změna CZ careful způsobila obecný fallback; nyní jsou obrázky
19 karet připnuté a tuto chybu hlídá regresní test. Dva nepoužité nové
náhledy jsou zachované v privátním archivu, nikoli v publikačním balíčku.
Konečný checkpoint a shodu commitovaných bajtů potvrzuje privátní
checkpoint.json; vlastní worktree je zachovaný, main/knihovna se nemění.
Vizuální browser host nebyl dostupný, fyzický telefon neověřený.


## 2026-11-14 22:03 CET — Schválená integrace a Pages vydání významových karet

Hotovo: Datův checkpoint97d34aef je převzatý nad současný main2ed8f750.
442 záznamů/432 aktivních,17 nových významových karet,8 ilustrací a73 MP3;
poštovní UI i knihovna zůstávají zachované. Závěrečné Datovy obrázkové vazby
jsou převzaté beze změny.
Rozhodnutí: Míla výslovně schválil doplnit dokumentaci a nasadit Datovu práci.
Jediný cílový proud project-vocabulary-en / github_pages / vocabulary-en/.
Další krok: Dokončit statické ověření a lokální integrační
checkpoint a jediný submit_release(wait=True).
Navrhované další kroky: Po potvrzeném vydání přejímka významů a A–D na iPhonu.
Technický důkaz:108/108 Datových souborů mimo memory a16/16 nezávislých
souborů main bajtově shodných s rodiči; konflikt jen v LESSONS_LEARNED vyřešen
zachováním obou záznamů. Datova plná brána3920 PASS/31 SKIP nad107 zmrazenými
zdroji zůstává historickým důkazem, novou plnou publikační bránu provede worker.
Request adam-vocab-meanings-20261114-v1, deterministický job 203708b8edeb3bdcfd8080e03aa16bc1.
Autoritou výsledku bude data/private/vocabulary_meanings_release_20261114/
release_receipt.json a public_verification.json. Tento přípravný zápis
nepotvrzuje budoucí publikaci; při nejistotě ověřit stejný job bez resubmit.
Původní2b17cbb4/4e5e18a7 neopakovat. Žádný Cockpit restart, nový model
obsahu, přepis osobních výběrů, výmaz médií či nový TVBCP. Fyzický telefon
a aktuální vizuální přejímka nových významů zůstávají otevřené.

Integrační přejímka na současném main:36 cílených Python testů včetně55 Node
scénářů PASS /19,725s;108 Datových a16 nezávislých main souborů shodných.

Po doplnění vlastního předání:108 Datových a11 nezávislých produkčních/main
souborů bajtově shodných;5 dalších nezávislých dokumentů main zachovává celý
původní obsah a přidává pouze autorizované závěrečné předání poštovního UI.


## 2026-11-14 22:23 CET — Významové karty veřejně vydané a ověřené

Hotovo: Vocabulary EN na Pages obsahuje442 záznamů/432 aktivních karet,
všech17 nových významů,8 nových ilustrací a73 MP3. Veřejný obsah přesně
odpovídá schválenému integračnímu vydání. Dokumentace poštovního UI je
dorovnaná; původní poštovní vydání se neopakovalo.
Rozhodnutí: Dokončené Mílou schválené Pages p+n; žádné nové rozhodnutí.
Další krok: Fyzická přejímka nových významů a osobních výběrů A–D na iPhonu.
Navrhované další kroky: Potom návrat k poštovnímu A+C; autorský vstup
a budoucí idiomy zůstávají volitelné navazující kroky.
Technický důkaz:e780fe98, job203708b8edeb3bdcfd8080e03aa16bc1 completed,
Terra/high,push/deploy confirmed, plná brána3920 PASS/763,3s, Pages
workflow43642325042/deployment7794063099, HTTP200. Čtecí kontrola všech
100 veřejných souborů (92 změněných) ověřila velikosti/SHA,17 nových UID,
442/432 a přesný aktuální GitHub head. Chráněné služby beze změny; Cockpit
health je zdravý se stejným procesem/kódem. Datův worktree zůstává zachovaný.
Účtenka a public_verification.json jsou v privátním
vocabulary_meanings_release_20261114/. Původní caller účtenka převzatá;
portálový returned_to_adam není potvrzený. Fyzický iPhone ani aktuální
vizuální přejímka nejsou doložené. Žádné p+n ani generování neopakovat.
Závěrečný dokumentační checkpoint vzniká po vydání místně; nemění nasazené
produkční soubory a není důvodem pro další nasazení. Bez nového TVBCP.


## 2026-11-15 08:27 CET — Autorský vstup a první dávka částí těla

Hotovo: Jeden interní autorský postup přijímá jednotlivou položku, seznam
i CSV. Připraví obsah a média v odděleném prostoru, rezervuje stabilní UID
a zařadí přesný ověřený balíček. Stav dávky je dohledatelný; opakované
zařazení vrací původní účtenku. Přirozené zadání interpretuje Data v chatu.
První skutečná dávka má10 částí těla ven-0443 ažven-0452,9 nových ilustrací,
1 převzatý obraz ruky a40MP3. Celkem452 záznamů/442 aktivních,423 Slovíček
a19 Interakcí;18 témat a všechny původní osobní identity zachované.

Rozhodnutí: Míla nejprve schválil zápis návrhu jako pravidla a potom vývoj
a doplnění10 částí těla. Pravidlo technical/vocabulary_en_authoring_rules.md
bylo uložené před vytvořením implementace; původní SHA a čas jsou v soukromé
rule_receipt.json. Jedna karta/jeden význam, bez automatického převzetí
A–D nebo Benji. Nové p+n zadané nebylo. Nový TVBCP není sjednaný.

Další krok: Dokončit plnou bránu, porovnat finální zdroje a vlastní checkpoint.
Navrhované další kroky: Samostatné Terra Pages p+n a přejímka těla na telefonu;
podle potřeby pozdější interní formulář, další tematické dávky a idiomy.
Oxford stále čeká na Mílův odeslaný dotaz.

Technický důkaz:90 cílených Python PASS /46,101s včetně56 Node scénářů.
Ověřený skutečný process exit po prvním zdrojovém zápisu, obnova stejné dávky,
souběh dvou příprav se samostatnými ID, cizí změny, změněný připravený soubor
i jeho změna uprostřed aplikace a zákaz opakování nejistého externího zvuku.
Všech442 původních položek exportu přesně shodných,2568 původních médií
bajtově shodných,40 nových MP3 dekódovaných ffmpeg. Skutečná dávka
body-parts-20261115-v1 je applied;75 změněných souborů a kontrolovaný replay
bez dalšího přidání/generování. Finální plná brána3936 PASS /1017,426s unit část,31 SKIP; soukromá autorita
výsledku je data/private/vocabulary_authoring_body_20261115/verification.json
a checkpoint.json. Vizuální iPhone přejímka není automatickými testy doložená.


## 2026-11-15 08:39 CET — Finální uzavření autorského vstupu a dávky těla

Hotovo: Schválené pravidlo uložené před implementací, jednotný interní
autorský postup a skutečná dávka10 částí těla, kompletní obrázky/věty/audio.
452 záznamů/442 aktivních; všech442 původních karet přesně zachovaných.
Rozhodnutí: Mílovo schválení místního vývoje platí; nové rozhodnutí nevzniklo.
Další krok: Samostatně schválené Terra Pages p+n.
Navrhované další kroky: Přejímka těla a osobních výběrů na telefonu, další
tematické dávky, pozdější interní formulář.
Technický důkaz: Plná brána3936 PASS /1017,426s unit část,
31 SKIP,0 failures/errors;90 cílených Python včetně56 Node PASS.
Všech82/82 finálních zdrojů/testů/dat/médií shodných se zelenou branou;
2568 původních médií zachovaných,40 nových MP3 dekódovaných. Skutečná dávka
body-parts-20261115-v1 applied jednou, replay bez generování nebo zápisu.
Browser host nebyl dostupný; fyzická telefonní přejímka zůstává následná.
Soukromý checkpoint.json potvrzuje výsledný commit a shodu commitovaných
bajtů. Nový TVBCP nebyl sjednaný ani založený.


## 2026-11-15 08:45 CET — Předání před restartem počítače

Hotovo: Vývoj i skutečná dávka10 částí těla jsou v checkpointu e2276615
(e2276615a41738f1378d84f4f7a81f7b2b91cb8c). Pravidlo bylo zapsané před vývojem,
452 záznamů/442 aktivních,40MP3. Plná brána3936 bez chyb,31 SKIP;82 zdrojů
commitovaných přesně podle zeleného běhu.
Rozhodnutí: Míla restartuje počítač. Žádná generace ani publikace neběží.
Další krok: Po restartu nejprve jen obnovit kontext a ověřit vlastní worktree
data/vocabulary-authoring-20261115, kanonický handoff a privátní
data/private/vocabulary_authoring_body_20261115/verification.json a checkpoint.json.
Navrhované další kroky: Teprve na nový pokyn Terra p+n a telefonní přejímka.
Technický důkaz: Dávka body-parts-20261115-v1 je applied. Neopakovat její
generování, přípravu ani zařazování; hotové obrázky/zvuky jsou uložené.
Předrestartový zápis je samostatná dokumentace nad e2276615; kód se nemění.
Souběžný main/knihovna zůstávají stranou. Samostatný TVBCP není dohodnutý.


## 2026-11-15 09:31 CET — Obnovení a příprava předání Terře

Hotovo: Po restartu obnoven hotový autorský vstup a deset částí těla.
V odděleném integračním worktree je zachovaných všech82 zdrojů zelené brány
a12 nezávislých souborů současného main bajtově shodných. Sdílené indexy
zachovávají záznamy Vocabulary EN i Knihovny. Dávka se znovu negenerovala.
Rozhodnutí: Míla výslovně zadal Terra p+n Vocabulary EN. Společný publisher
vydává celý main; čtyři další Willovy commity nejsou touto větou automaticky
schválené. O rozsahu společného push je položena konkrétní otázka.
Další krok: Po potvrzení rozsahu převzít připravenou integraci, zarovnat
jen čisté nedivergentní profily a zavolat jediné submit_release(wait=True).
Navrhované další kroky: Fyzická přejímka částí těla a A–D na telefonu.
Technický důkaz: Zdroj e2276615 + předání acb6e0a8, integrační základ072ab251.
47 cílených Python testů PASS/31,471s a rychlá statická brána PASS.
Předchozí Knihovna jobfff30ae477f38401ae8e582208e9a582 je attention/neaktivní;
živý GitHub audit stálee780fe98 a5 čekajících commitů před integrací.
Pages vydání nesmí restartovat Cockpit. Nový TVBCP není sjednaný.


## 2026-11-15 09:47 CET — Schválený společný balíček

Hotovo: Integrace Vocabulary EN je připravená nad nezměněným main072ab251.
Rozhodnutí: Míla výslovně potvrdil „ANO vše najednou“ k přesné otázce
zahrnout čtyři Willovy commity do společného push a vydat Vocabulary EN
přes Pages bez restartu Cockpitu. Tento rozsah je nyní schválený.
Další krok: Jediné registrované Terra p+n pro project-vocabulary-en/github_pages
s přesným finálním lokálním headem a trvalou identitou požadavku.
Navrhované další kroky: Po vydání ověřit veřejné soubory a fyzický telefon.
Technický důkaz:47 integračních Python testů a statická brána PASS,
82 původních zelených zdrojů a12 nezávislých main souborů přesně zachovaných.
Žádný nový obsah ani média se negenerují; samostatný TVBCP není sjednaný.


## 2026-11-15 10:07 CET — Terra Pages p+n dokončené a veřejně ověřené

Hotovo: Deset částí těla s obrázky, větami a audiem je veřejně ve Vocabulary EN.
Slovník má452 záznamů/442 aktivních; původní karty a osobní identity zachované.
Rozhodnutí: Dokončený celý Mílou schválený společný push sedmi commitů,
včetně čtyř Willových. Cílem tohoto vydání byl Vocabulary EN/Pages;
Cockpit se nerestartoval a jeho běžící proces/kód jsou shodné s výchozím stavem.
Další krok: Fyzická přejímka částí těla a osobních výběrů A–D na telefonu.
Navrhované další kroky: Další tematické dávky přes hotový autorský postup;
Oxford nadále čeká na odpověď. Nasazení Willova Cockpit UI je samostatný cíl.
Technický důkaz:2779af14, job5cf76b0c85a854c64b04a003c7cf1356 completed,
Terra/high, push+deploy confirmed, plná brána3938 PASS/868,3s. Pages
workflow43697487353/deployment7801188909, vocabulary-en/ HTTP200.
71/71 veřejných souborů má přesnou velikost/SHA-256 předaného headu;
452/442 a všech10 nových UID potvrzených veřejným JSON. Živý GitHub head shodný.
Protected services unchanged; fyzický iPhone tímto není ověřený. Původní
caller účtenka převzatá; portálový returned_to_adam není potvrzený a není
důvodem retry. Dávku ani publikaci neopakovat. Soukromá autorita:
vocabulary_authoring_release_20261115/release_receipt.json a public_verification.json.
Závěrečný dokumentační checkpoint zůstává místně pro další běžný balíček;
produkční soubory nemění a nový deployment nevyžaduje. Bez nového TVBCP.


## 2026-11-15 11:21 CET — První schválená desítka z Cesty k jezeru

Hotovo: Místně zařazených deset karet sky, frog, beaver, woodpecker, net,
hut, shore, fire, sick a healthy. Každá má český význam, vlastní EN/CZ
příklad, explicitní obrázek, náhled a čtyři zvukové reference. Net je
rybářský podběrák; sick/healthy procvičují nemocný/zdravý strom.
Celkem462 záznamů/452 aktivních:433 Slovíček a19 Interakcí,18 témat.
Rozhodnutí: Míla schválil „doplň první desítku dle našich pravidel“
z TXT návrhu MMTX. Zadaný rozsah je místní doplnění, nové p+n nezadané.
Další krok: Samostatně autorizované Terra Pages p+n; potom přejímka telefonu.
Navrhované další kroky: Po výběru další dávka ze zbývajícího návrhu MMTX;
nové významy call/too/turn jsou pouze návrh, nikoli součást této desítky.
Technický důkaz:52 cílených Python testů PASS/42,729s včetně51 výběrových
a5 learner Node scénářů; rychlá statická brána PASS. Všech452 původních
položek i katalogových identit přesně shodných,2628 původních médií
bajtově zachovaných, původní CSV prefix/CRLF zachovaný.40/40 nových MP3
dekódovaných ffmpeg,10 náhledů WebP384×384;63/63 lokálních HTTP odpovědí
byte/SHA exact.78 finálních zdrojů/dat/testů/médií zmrazených po ověření.
Změnil se pouze obsah a očekávané počty v existujících testech; aplikační
a autorský kód beze změny. Plná publikační brána patří do následného p+n.
Autorský request lake-vocabulary-first10-20261115-v1 je applied;
ven-0453 ažven-0462,9 nových ilustrací vestavěným imagegen + převzaté sky.
Dávku ani dokončená média znovu negenerovat. Aria/Vlasta a−10% zachované,
osobní A–D/Benji nové karty automaticky nepřebírají. Fyzický telefon
a aktuální browser přejímka nejsou doložené. Vlastní větev
data/vocabulary-lake-batch1-20261115 nad d141d030; souběžný main s opravou
zálohy zůstává stranou. Doklady: data/private/vocabulary_lake_batch1_20261115/
a authoring job v data/private/vocabulary_authoring/. Bez nového TVBCP.


## 2026-11-15 11:43 CET — Další schválená dvacítka z návrhu MMTX

Hotovo: Místně zařazeno dalších20 karet podle pořadí zbývajícího TXT:
dinner, meeting, morning, splash, race, people, idea, team, plan, place,
side, work, shout, practise, sleep, bring, ask, think, check a leave.
Každá má EN/CZ příklad, explicitní ilustraci, náhled a čtyři zvukové
reference. Celkem482 záznamů/472 aktivních,453 Slovíček a19 Interakcí.
Rozhodnutí: Míla zadal „dávku dalších navržených20 slovíček najednou“.
Zvolený přesný seznam byl oznámen před přípravou. Ask je požádat, leave
je nechat/ponechat; jiné významy se nepřimíchávají. Nové p+n nezadané.
Další krok: Samostatně schválené Terra Pages p+n obou místních dávek (10+20).
Navrhované další kroky: Přejímka telefonu; výběr z35 zbývajících nových
hesel původního návrhu,3 doplňujících významů a2 volitelných rozšíření.
Technický důkaz:52 Python testů PASS/27,378s včetně51 selection +5 learners
Node scénářů, statická brána PASS. Všech462 starších položek/katalogových
identit přesně stejných,2688 původních médií bajtově shodných, CSV prefix
a CRLF zachované.80 nových MP3 dekódovaných,20 náhledů WebP zkontrolovaných,
123/123 místních HTTP odpovědí přesně shodných.148 zdrojů/dat/testů/médií
zmrazených po ověření. Nemění se aplikační ani autorský kód; v existujících
testech se mění jen inventární čísla. Plná publikační brána patří do p+n.
UIDven-0463 ažven-0482; dávka lake-vocabulary-next20-20261115-v1 je applied,
digest5ea1a773d7d59ea7aed3afe9efa189359b635d6143d637644c486d92d70faef5.
Obrázky:13 nově vytvořených vestavěným imagegen,1 úprava závodu bez nápisů,
6 převzatých; žádné původní obrazy se nepřepisují. Aria/Vlasta,−10%,18 témat,
původní UID a osobní výběry zachované. Nové karty nepřebírají A–D/Benji.
Vlastní větev data/vocabulary-lake-batch1-20261115 obsahuje první desítku
a tuto dvacítku; main s Willovou opravou zálohy zůstává stranou.
Doklady: data/private/vocabulary_lake_batch2_20261115/. Dokončené dávky
a média znovu negenerovat. Telefon/browser zatím nepřevzaté. Bez nového TVBCP.
