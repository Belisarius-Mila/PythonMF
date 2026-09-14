# Cockpit: oddělení čtecích dokumentových HTTP cest — 14. 9. 2026

Lokální strukturální krok nad kódem `fc889ed5`. Sedm GET cest a čtyři obsluhy
čteček/souborů přesunuty do `cockpit_document_routes.py` (130 řádků).
`cockpit.py`: 10 892 → 10 801 řádků; `make_handler`: 1 481 → 1 389;
`do_GET`: 326 → 295. `do_POST` zůstává 642 řádků.

## Hranice

- Cesty: `/api/documents/search`, `/api/documents/review-report`,
  `/api/documents/case-detail`, `/documents/read`, `/documents/pdf`,
  `/purchases/read`, `/purchases/pdf`.
- Modul dostává pět backendových funkcí; předání odpovědi používá původní Handler.
  Přístupové kontroly proběhnou před dispatch, bezpečnostní hlavičky a centrální
  převod výjimek zůstávají společné. Původní resolvery hlídají index a úložiště.
- Žádná změna UI, POST, ukládání, parametrů, obsahu odpovědí či autorizace.
  Každý požadavek znovu načítá svou odpověď; nevzniká cache ani obecný router.
- Nový soubor přidán do kompilace, obou GitHub CI filtrů a povinných rizikových
  cest pro plnou bránu. Testová sada přidána do kanonického manifestu.

## Ověření

- Osm nových HTTP testů prošlo před i po přesunu. **61/61 kontraktů shodných**:
  status, SHA256 celého těla a hlavičky kromě `Date`/`Server`.
- Pokryté úspěšné JSON odpovědi, čtečky, PDF/obrazová data, chybějící a opakované
  parametry, kódované reference, neznámé cesty/POST, nepovolený Host (původní 400),
  centrální redigované 500 a skutečné resolvery odmítající vnější cestu i symlink.
- Všechna data syntetická v dočasném úložišti a na izolovaném lokálním serveru.
  Živé soukromé dokumenty se nečetly. Zaznamenané stavy: 200 × 11, 404 × 36,
  400 × 7, 500 × 7. Report neobsahuje těla ani cesty soukromých dat.
- AST porovnání: sedm větví a čtyři těla obsluh shodné po zohlednění předaných
  závislostí a návratového příznaku dispatch. Zbytek AST `cockpit.py` nezměněný.
- Existující kontrola adres frontendu čte také skutečné větve nového dispatch;
  původní kontrola pouze hlavního souboru po přesunu cesty neviděla.
- 35 cílených testů prošlo. **Plná brána 1665/1665**, unit 252.042 s,
  včetně nového testu povinné plné brány při změně odděleného HTTP modulu.

## Stav a další krok

Krok je lokální, bez push/nasazení. Přínosem je samostatná odpovědnost a
ověřitelnost dokumentového HTTP rozhraní; měření nezakládá tvrzení o zrychlení UI.
Následuje samostatné vydání a společná přejímka dokumentových čteček na Macu/iPhonu;
navazující audit/UI zůstává otevřený. Souběžný `OwlSpeech.csv` změnil samostatný
commit, není součástí tohoto dokumentového řezu.
