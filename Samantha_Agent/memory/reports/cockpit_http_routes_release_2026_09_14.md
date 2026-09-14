# Vydání čtecích HTTP modulů Cockpitu — 14. 9. 2026

Míla schválil push a nasazení; UI audit má proběhnout později samostatně.
Funkční commity: `8ce24999` (dokumenty) a `da9d0bea` (e-mailový archiv).
Nasazený funkční head: `da9d0bea009a467d01fe2c6674a3e06aa0cbcf68`.
Ověřeno `2026-09-14T08:45:07+00:00`: nový proces potvrzen, otisk
`0461867a886fdf42`, provozní smoke **5/5**. Vývojová plná brána
**1675/1675**, dokumentové kontrakty **61/61**, archivační **53/53**.

Tento záznam vzniká po ověřeném nasazení funkčního kódu, před společným
GitHub balíčkem včetně tohoto zápisu. Balíček provede povinnou plnou bránu;
po něm se znovu ověří nasazení finálního headu. Aktuální stav poskytují
registrované `github-batch-audit`, `deploy-audit` a `workstream_live_status`.
Ruční přejímka ještě neproběhla. Snížení počtu řádků není důkaz zrychlení UI.

## Ruční přejímka pro Mílu

Na Macu otevřít obvyklý Cockpit a obnovit stránku Cmd+R. Na iPhonu otevřít
obvyklou adresu/zkratku Cockpitu a obnovit stránku v Safari. Projít na obou:

1. V části **Najít dokument** zadat část názvu známého uloženého PDF a dát
   **Hledat**. Očekává se odpovídající výsledek, bez chyby či nekonečného načítání.
2. U výsledku **Otevřít / číst**: zobrazí se správný dokument; posunout stránku,
   ověřit čitelnost a stisknout **Zpět do Cockpitu**. Očekává se návrat do Cockpitu.
   Je-li k dispozici uložený obrázek, stejně ověřit také jeho čtečku.
3. Vyhledat známý nákup s PDF, **Otevřít PDF**, zkontrolovat fakturu a **Zpět do
   Cockpitu**. Známá starší mezera: nákupní návrat spoléhá na původní okno;
   pokud nereaguje, vrátit se do původní karty a nahlásit zařízení i tento krok.
4. Nahoře **E-maily → Archiv e-mailů → Otevřít**. Vyhledat známou uloženou zprávu
   podle části předmětu/odesílatele, dát **Hledat** a vybrat zprávu. Očekává se text
   a seznam příloh pod hlavičkou.
5. U PDF přílohy **Otevřít celé PDF**; ověřit správný obsah. Je-li obrázek,
   ověřit i jeho náhled/otevření. Z nové karty se vrátit do archivu; na iPhonu
   **← Zpět na seznam**, vybrat jinou zprávu a nakonec **Zpět do Cockpitu**.

Během přejímky stačí čtení, bez tisku, ukládání metadat či přesouvání dokumentů.
Chybějící vhodný testovací dokument označit „neověřeno“. Výsledek vrátit jako
zařízení + číslo kroku + OK/problém, bez soukromého obsahu či názvů dokumentů.
Po přejímce samostatný audit UI; jeho provedení není součást tohoto vydání.
