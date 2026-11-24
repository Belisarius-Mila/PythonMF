# Ateliér — doložený původ obrazových návrhů

## 2026-11-24 10:26 CET — Bod 1 schváleného návrhu

Hotovo: Nové obrazové návrhy ukládají vlastní přehled původu. Rozbalovací „Jak vznikl obrázek“ je u vybraného AI návrhu i v historii jednotlivých výstupů. Odděluje architekta od obrazového nástroje, uvádí uložený model architekta a jeho přemýšlení, režim Standard, skutečnou připojenou verzi serveru, rozměry výstupu a dostupné ID/průhlednost. Přesný obrazový model, kvalita a složitost mají neznámou hodnotu, nikoli odhad podle Terry. Staré návrhy se čtou bez migrace; historický architekt pochází pouze z původního požadavku, nikdy ze současné role.

Rozhodnutí: Míla schválil vývoj pouze bodu 1. Modelové role, instrukce, oprávnění, potvrzení a počet modelových požadavků zůstávají stejné. Nevznikl Images API adaptér, nové placené generování, maska ani oddělení kresby od fotografie. Nový TVBCP nebyl dohodnutý; tento terminálový krok má kanonický handoff, projektovou paměť a tento report.

Další krok: Samostatně autorizované p+n a poté kontrola zobrazení v běžícím Ateliéru. Při příštím běžném obrazovém požadavku ověřit skutečně vrácená volitelná metadata, bez zvláštního placeného pokusu jen kvůli tomuto přehledu.

Navrhované další kroky: Původní bod 2 — oddělení čistého obrázku od kreslených pokynů — čeká na samostatné zadání. Přímé Images API připadá v úvahu, pokud bude potřeba výslovně volit Sunburst a obrazové parametry; zatím se nezavádí.

Technický důkaz: Registrovaná `scripts/validation_gate.py`, validation-v3, targeted: 139 vybraných modulů, 2459 testů, 31 SKIP, bez chyb; 448,4 s včetně statických kontrol. Součástí je 20 Node scénářů obrazového rozhraní. Nové regrese pokrývají ukládání/obnovu po selhání persistence, původní thread/read bez nového tahu, historické údaje bez zápisů, neodhadování enginu, zachování false u průhlednosti, odmítnutí privátních cest a textové vykreslení metadat. Neproběhla fyzická přejímka Mac/iPhone ani placená obrazová zkouška. P+n a restart Cockpitu nebyly provedené.

## Audit skutečného protokolu

- Živý neplacený initialize přes stávající socket: připojený server `codex-cli 0.169.0`; místní CLI také `0.169.0`. Nevytvořilo se vlákno ani modelový tah.
- Schéma stejného binárního serveru získané `codex app-server generate-json-schema --experimental`: ImageGenerationThreadItem obsahuje mimo jiné `generationId`, `transparentBackground`, `inputImages`, `revisedPrompt`, identitu výsledku a lokální cestu. Neobsahuje model obrazového enginu, quality ani complexity. TurnStartParams tyto obrazové volby také přímo nemají. Opaque config není důkaz podpory nedokumentovaných voleb.
- Tento most obrazový model, quality ani complexity nevolí; nové capabilities to uvádějí výslovně. Hodnota schema_reference je odkazem na prověřenou verzi, nikoli náhradou živé verze uložené u výsledku.
- Do přehledu se přenášejí pouze vybraná pole. Lokální savedPath/inputImages, obrazová data a revidovaný prompt se do veřejného přehledu metadat nekopírují. Schéma podporuje také fileId; tato změna nerozšiřuje dosavadní příjem obrazových dat o stahování příloh.
- Výsledkové JSON i varianty uchovávají údaje pro obnovu. Obnova z původního thread/read nepřipisuje obrázku verzi serveru, která obsluhuje až pozdější čtení. Chybějící historický údaj zůstává neznámý.
- Data worktree s rozpracovanými EN/MMTX změnami zůstal nedotčený. Vývoj proběhl nad čistým aktuálním main; předchozí čekající dokumentační commit byl zachován.

Omezení: audit protokolu nedokládá, který interní obrazový model byl použitý pro konkrétní starší obrázek. Výsledek nelze označit jako Sunburst/Flare ani mu přiřadit high quality bez skutečného důkazu. Doplňující metadata jsou informační a nemění geometrii ani kvalitu obrazového výstupu.
