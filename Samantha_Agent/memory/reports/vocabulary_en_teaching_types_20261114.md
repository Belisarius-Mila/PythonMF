# Vocabulary EN — typy učiva a vyřazené karty


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
