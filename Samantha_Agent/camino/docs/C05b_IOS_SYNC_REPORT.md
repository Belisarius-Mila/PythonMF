# C05b — report trvalé iOS fronty

Datum lokální implementace: 2026-09-23

## Výsledek implementace

Integrovaná iOS aplikace má trvalý C05b journal, privátní HTTPS klient C03b/C05a
a obrazovku **Uložení a přenosy**. Fronta dává přednost manifestům a metadatům,
potom audiu, fotografiím a videu. Přesné bajty již vytvořené operace se ukládají
pro byte-identical retry; médium se po přerušení znovu porovná se serverem a
stav `verified` vznikne jen po serverové finalizaci délky a celkového SHA-256.

Místní pořizování ani čtení na serveru nezávisí. Token je uložený v Keychain,
URL musí být HTTPS a neexistuje veřejný fallback. Jednorázové mobilní povolení
se při potvrzení zmrazí na právě zobrazenou dávku a okamžitě se otevře nové ID
dávky, takže pozdější záznamy oprávnění nezdědí. Pozastavení je trvalé.

Změna serverové identity nebo epochy je fail-closed. Telefon pošle pouze
inventář Momentů, nic nemaže a nadále zobrazuje nutnou servisní kontrolu;
serverové exporty sám neodblokuje.

## Provozní obal

Registrovaný lifecycle `camino_c05b_private_start/copy_token/status/stop`
spouští samostatný C05a proces pouze na `127.0.0.1:8766`, drží databáze a média
mimo Git a přidává jen privátní Serve cestu `/camino-api`. Start se zablokuje,
pokud je Funnel aktivní, cesta už existuje, port je obsazený, tailnet není
online nebo neprojde C05a HTTPS health a zdraví kořene Cockpitu. Stop odebere
jen vlastněnou cestu, zastaví jen vlastněný proces, odvolá token, porovná přesný
původní Serve stav a zachová data i důkaz.

Nejde ještě o C06a: služba není `launchd` managed, nemá párovací UI ani
produkční zálohu/obnovu.

## Automatický důkaz

- Swift Core: 29/29 PASS, z toho 7 C05b testů pro priority, pause, jednu mobilní
  dávku, serverovou finalizaci, změnu epochy, byte-identical retry, mapování
  textové revize a zákaz nového uploadu média po změně metadat.
- C05b provozní obal + registr workflow: 13/13 cílených testů PASS.
- iOS simulátorový build bez podpisu: PASS.
- UI test obrazovky fronty, trvalého pozastavení a místního záznamu po relaunchi:
  1/1 PASS.
- Plná projektová brána: 1768/1768 PASS.

## Fyzické přijetí

Instalace, privátní služba a fyzické scénáře T047–T053/T058 zatím nejsou tímto
lokálním důkazem prohlášeny za PASS. Výsledky se zapisují výhradně podle
`C05b_IPHONE_TEST_PLAN.md`; nedostupný captive portal zůstane viditelně
`NEOVĚŘENO`.
