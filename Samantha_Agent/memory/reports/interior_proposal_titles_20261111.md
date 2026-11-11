# Ateliér — popisné názvy nových návrhů

Stav: místní vývoj, 2026-11-11 12:25 CET; bez p+n. Proud project-neuberk-kacenka, větev adam/interior-proposal-titles-20261111, podklad a40b65cd. Starší uložené varianty ani obrazové podklady se nepřejmenovávají a soubory se nemažou.

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
