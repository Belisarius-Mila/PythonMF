# Ateliér — čistý pracovní obrázek a samostatné kreslené pokyny

## 2026-11-24 12:46 CET — Bod 2 schválený včetně p+n

Hotovo: Čistý pracovní obrázek se předává beze změny jeho dosavadních preview bajtů. Kresba vzniká až na samostatné kopii připojené na konec vstupů. Půdorys i všechny další vybrané reference zachovávají bajty, pořadí a čísla. V potvrzovaném souhrnu jsou oba náhledy s popisky a skutečný počet obrázků. Ovládání kresby a výběru podkladů zůstává stejné.

Rozhodnutí: Míla schválil vývoj bodu 2 následovaný p+n. Šest vybraných zdrojů včetně společného půdorysu zůstává limitem výběru; při kresbě vzniká nejvýše sedm modelových vstupů, což se vejde do dosavadní osmiobrazové hranice klienta. Žádná reference se nevyřazuje. Terra/high Standard, obrazový engine i exekuční oprávnění se nemění. Kresba je vodítko, nikoli skutečná maska. Neproběhl žádný placený obrazový pokus.

Další krok: Jediné již schválené p+n přes registrovaný submit_release, poté nezávisle ověřit živý protokol a celé sestavené HTML/CSS/JS. Stabilní request_id `interior-separate-drawing-20261124-v1`, job_id `53e1c9f217b1dea04c7ce1f72fd25e2a`. Tento zápis předchází zmrazení commitu, není důkazem publikace. Autoritou výsledku jsou přesná účtenka tohoto jobu a `data/private/interior_separate_drawing_20261124/release/receipt.json`, `verification.json`, konečný `completion.json`. Po vydání se kvůli výsledkovému zápisu netvoří další čekající commit.

Navrhované další kroky: Při příští běžné práci s vlastní fotografií porovnat praktičnost obou podkladů. Skutečný výběr oblasti maskou z původního bodu 3 není součástí této změny ani novým vývojovým zadáním.

Technický důkaz: Registrovaná validation-v3 brána targeted,12 modulů,182 testů PASS bez přeskočených,109,4s včetně statických kontrol; součástí21 Node scénářů. Samostatná backendová sada101 PASS a po doplnění otisků18 aktivačních PASS. Nativní Safari nad oddělenou syntetickou HTTP místností ověřilo dva náhledy vedle sebe, čistý obrázek vlevo, označenou kopii vpravo, počet2 a zachované potvrzení. Model ani generování se v browseru nevolaly; testovací panel byl zavřen a původní panel obnoven. iPhone a kvalita skutečného generativního výstupu touto zkouškou ověřené nejsou.

## Technické hranice

- Nové požadavky mají `image_input_protocol=interior-images-v2`. Manifest rozlišuje working_clean, room_plan, reference a drawing_guide. Pouze kreslená kopie odkazuje na clean_image_number; neoznačuje se jako další pracovní obrázek ani půdorys. Stejné oddělení dostává chat i tvorba obrazu.
- Kreslená kopie je poslední vstup. Číslo společného půdorysu se nezmění, ani když je pracovní obrázek zároveň půdorysem. Bez kresby nevzniká žádný vstup navíc.
- Protokol je v potvrzovacím tokenu, takže starý předdeployový token nepovolí nový formát bez obnovení náhledu. Stávající souhrn kvůli tomu nevyžaduje nový placený chat. Příprava vstupů i instrukce jsou v exekučním otisku pilotu; jejich změna se nesmí vydávat za opravu pouhého zpracování artefaktů.
- Všechny čisté i kreslené kopie mají vlastní neměnné snapshoty a SHA před předáním. Stejný request_id nic znovu neposílá a obnova původního výsledku nekreslí z dnešního draftu. Starší požadavky bez nového protokolu se nepřevádějí.
- Existující potvrzované mazání zahrne i input_7.png pouze u zaznamenané sedmivstupové žádosti s odděleným drawing_guide. Neznámá sedmá kopie nadále blokuje mazání. Skutečné soukromé podklady se během vývoje nemazaly.
- Data/MMTX a modelové role zůstaly nedotčené. Nový TVBCP nebyl dohodnutý; terminálový krok má kanonický handoff, projektovou paměť a tento report.

Předchozí bod1 je již vydaný: commit77f71125, potvrzené p+n přes Terru bf5124129a4a4fd9f5a618744136d34c, smoke5/5 a nezávislá shoda živých capabilities i sestavené stránky. Důkaz je `data/private/interior_image_provenance_20261124/completion.json`; původní neúspěšný DNS pokus f2ae15e2ce433e3744c1a124c644c0c8 se neopakuje.
