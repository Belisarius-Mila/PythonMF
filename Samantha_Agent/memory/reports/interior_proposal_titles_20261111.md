# Ateliér — popisné názvy nových návrhů

Stav: implementace c7efd566 ověřená místně; Míla 2026-11-11 15:25 CET autorizoval úklid repa a Terra p+n všech připravených commitů. Konečný provozní výsledek je v soukromé účtence 7c39e3b6bc3779200de7a3355028d00f a release/verification.json, nikoli v tomto předávacím zápisu.

## Výsledek

Architekt připravuje title v téže odpovědi jako souhrn. Pokyn je typ místnosti + hlavní schválená změna, například „Koupelna – vana v rohu u okna“, krátce a bez nevyřešených úvah. Názvem se neslibuje stavební proveditelnost. Osobní název místnosti nemusí být její funkční typ. Před vytvořením je viditelný návrh jména, ručně upravitelný a uložitelný; pod ním je přesný plánovaný název včetně případného číslování. Žádný samostatný modelový tah kvůli názvu.

Při absenci pojmenovaného souhrnu zůstává současný uložený název; je-li prázdný, je před potvrzením viditelná místní záložní kombinace názvu místnosti a začátku schválených změn. Lze ji ručně upravit bez placeného chatu. Nové obrazové podklady dostávají stejný popisný název jako varianta. Při obsahové deduplikaci obrazu se existující jméno původního podkladu nepřepíše.

## Kontrakt a zachování starých výsledků

- Nové protokolové joby mají interní title_protocol=interior-title-v1. Named chat schema má ve všech objektech další vlastnosti zakázané a všechny vlastnosti povinné včetně title. Původní schéma je zachované pro staré joby a deníky. [OpenAI Docs — strict schema](https://developers.openai.com/api/docs/guides/function-calling#strict-mode).
- Historická JSON odpověď bez názvu zůstane čitelná; starý obrazový job při obnově ponechá staré pojmenování. Nový named job bez platného názvu je odmítnutý jako vadný souhrn, bez automatického nového modelu. Modelová role, účet a transport zůstávají beze změny; nový zdroj je součástí otisků případného budoucího pilotu.
- Název se ukládá do stávajícího draft.title, mění revizi a potvrzovací token. Obsahový základ nového souhrnu název odděluje, takže přejmenování nezneplatní changes/preserve/unresolved. Staré aplikované souhrny porovnají původní titul z deníku při ověření ostatního obsahu. Změna skutečného obsahu/podkladů/poznámek/měr souhrn dál zneplatní.
- Pozdní named odpověď smí při změně samotného názvu aktualizovat nezměněný obsahový základ, ale zachová novější ruční název. Novější obsah nesmí přepsat. Neuložené browserové úpravy a konflikty revizí zůstávají chráněné.
- Obrazový job zmrazí proposal_title ze zkontrolovaného stavu. Obsah approved_brief zůstává beze změny, historie/poznámky prázdné. Název je pouze metadata, nikoli text pro obraz.
- Číslování „· 2“, „· 3“ počítá všechny existující varianty místnosti a normalizuje mezery/Unicode/velikost písmen při porovnání. Finální volba se opakuje uvnitř dokončovací transakce, takže i dva souběžné joby získají různá jména. Při pozdější kolizi se může zvýšit číslo; věcný název zůstává stejný. Výsledek respektuje limit120 znaků. Replay/recover již dokončeného jobu nedělá další variantu ani číslo.

## Ověření

143 cílených Python/HTTP/frontend kontrol PASS (včetně30 Node scénářů); po sjednocení nadpisu po ručním uložení dalších38 frontend/HTTP kontrol PASS. Nově12 serverových kontraktů +1 HTTP +2 Node scénáře. Pokrývají přijetí názvu v jednom chatu, ruční změnu bez nového modelu, neplatnost starého image tokenu, novější ruční název při pozdní odpovědi, dvě stejné generace, více výstupů, dvě souběžné úlohy, obnovu ze zmrazeného jména, historická data, striktní schéma a délku/Unicode.

Safari/CUA: syntetický model navrhl „Koupelna – vana v rohu u okna“, člověk upravil na „Koupelna – rohová vana u okna“. Bez dalšího chatu byly vytvořeny dva fake obrázky a v galerii ověřeny názvy bez čísla a s „· 2“. Další preview ukázalo „· 3“. Snapshoty obsahují přesné schválené názvy a stejný approved_brief. Fake counts chat1/image2/paid0; skutečný model ani reálná soukromá místnost nebyly použity. Testovací panel a vlastní HTTP server ukončené. Toto není skutečný sémantický/placený test kvality názvu od architekta ani nasazení.

Plná brána PASS: 3482 testů, 0 chyb, 31 SKIP, 496,6 s.

Důkazy: data/private/interior_proposal_titles_20261111/ (qa.json, full_gate.log, image_snapshot_1.json, image_snapshot_2.json, browser_counts.json, preservation_before.json a následné ověření). Kanonický handoff, projektová paměť i katalog aktualizované. Nový TVBCP nebyl domluvený a nezakládá se; jeho vazba pro budoucí Human–Adam zůstává výslovně otevřená.

## Další krok

Samostatné p+n; po vydání lidská přejímka jména v běžném rozhovoru. Skutečná data, Data a MMTX se nemění.


## 2026-11-11 15:25 CET — Závěrečné předání názvů Terře na p+n

Hotovo: Popisné názvy nových AI návrhů jsou implementované v c7efd566 a ověřené místně: brána3482 PASS/31 SKIP, cílené143/30Node a syntetické Safari. Existující názvy/podklady zůstaly zachované.

Rozhodnutí: Míla výslovně zadal „ukliď repo, všechny commity p+n Terra“. Celý připravený balíček včetně tohoto zápisu převezme jediný registrovaný submit_release pro project-neuberk-kacenka. Vykonavatel musí odpovídat centrální roli gpt-6.1-terra/high; role se nemění a jiný model se tiše nepoužije. Rozpracované větve, Data ani média se nemažou. Tento zápis vzniká před zmrazením balíčku; konečný provozní výsledek je mimo Git v přesné účtence. Po vydání kvůli výsledkovému zápisu nevznikne další čekající commit.

Další krok: Po potvrzeném vydání obnovit Ateliér a při příštím běžném rozhovoru ověřit navržený název. Žádný skutečný placený test architekta není součástí p+n.

Navrhované další kroky: Žádné nové; TVBCP bez nové dohody nevzniká.

Technický důkaz: Stabilní request_id=interior-proposal-titles-final-pn-c7efd566-20261111-v1, job_id=7c39e3b6bc3779200de7a3355028d00f. Autorita skutečného push/nasazení: registrovaná soukromá účtenka tohoto job ID a data/private/interior_proposal_titles_20261111/release/receipt.json. Jednorázové závěrečné ověření je verification.json; čistota a zarovnání repa/profilů alignment.json. Při navázání načíst tuto konkrétní účtenku a použít registrovaný živý audit. Samotný tento předávací zápis nasazení nepotvrzuje. TVBCP vazba pro budoucí Human–Adam zůstává otevřená.
