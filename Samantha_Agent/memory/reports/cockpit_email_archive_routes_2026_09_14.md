# Cockpit: čtecí HTTP rozhraní e-mailového archivu — 14. 9. 2026

Další lokální strukturální řez nad `8ce24999`. Šest GET cest a tři obsluhy
souborů/příloh přesunuty do `cockpit_email_archive_routes.py` (138 řádků).
`cockpit.py`: 10 801 → 10 705; `make_handler`: 1 389 → 1 292;
`do_GET`: 295 → 260. `do_POST` zůstává 642 řádků.

## Rozsah a zachované hranice

- `/email-archive/`, `/api/email-archive/list`, `/api/email-archive/detail`,
  `/email-archive/file`, `/email-archive/attachment`, `/email-archive/incoming`.
- Modul dostává HTML provider a pět backendových funkcí. Přístupová kontrola,
  centrální převod výjimek, bezpečnostní hlavičky a společná obsluha lokálního
  souboru zůstávají v Handleru. Resolvery a EML dekódování zůstávají v backendu.
- Stejné parametry a výchozí hodnoty, stejné chybové odpovědi a souborová data.
  Vložené přílohy zachovávají inline pro PDF, obrázky mimo SVG a prostý text;
  SVG, HTML, ZIP a ostatní typy zachovávají stažení. Sdílená obsluha lokálních
  souborů zůstává beze změny; krok není přehodnocení obsahové bezpečnostní politiky.
- UI, POST, AI metadata, zápisy a odchozí komunikace beze změny. Žádná nová cache
  ani obecný router. Nový modul v kompilaci, obou CI filtrech a povinné plné bráně.

## Ověření

- Devět nových HTTP testů prošlo před i po. **53/53 kontraktů shodných**:
  status, otisk celého těla a hlavičky kromě `Date`/`Server`.
- Úspěšná stránka, seznam/detail, soubory, MIME/disposition a výchozí hodnoty;
  chybné limity, opakované/kódované parametry, chybějící soubory, neznámé cesty,
  POST, Host odmítnutý před providerem a redigované centrální chyby.
- Skutečné resolvery odmítly traversal/symlink mimo úložiště a chybnou referenci
  přílohy. Platná neprůhledná reference v syntetickém EML vrátila přesné PDF bajty.
  Pouze dočasná syntetická data, žádné čtení živých soukromých e-mailů.
- AST: šest větví, tři těla obsluh a zbytek `cockpit.py` shodné po zohlednění
  explicitních závislostí. Stávající inventura adres frontendu čte nový dispatch.
- **49 cílených testů**, včetně archivačního backendu a dokumentových HTTP cest.
  **Plná brána 1675/1675**, unit 231.324 s. Čas tohoto běhu není benchmark
  dopadu přesunu na výkon.

## Stav a další krok

Tento řez i předchozí dokumentový commit čekají lokálně na společné vydání.
Přínosem je ucelená odpovědnost a ověřitelnost čtecí části archivu. Následuje
samostatný push/nasazení a společná Mac/iPhone přejímka dokumentů i archivu;
navazující audit/UI zůstává otevřený.
