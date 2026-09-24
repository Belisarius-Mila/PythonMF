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

Registrovaný lifecycle `camino_c05b_private_start/copy_url/copy_token/status/stop`
spouští samostatný C05a proces pouze na `127.0.0.1:8767`, drží databáze a média
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

Podepsané Camino 0.1.0 (3) bylo nainstalováno jako aktualizace stejného bundle
ID bez odinstalace. Starší Momenty a média zůstaly dostupné. Na iPhonu 14 Plus
prošly T051, T047-A/B, dostupná část T048, T049, T050, T052, T053, T058 a
trvalé pozastavení. Captive portal T048 zůstává viditelně `NEOVĚŘENO`, protože
nebyl bezpečně dostupný.

Závěrečný serverový důkaz po fyzickém průchodu obsahuje 104 přijatých operací,
41 Momentů, 45 Assetů a 45/45 ověřených médií o 214 555 219 B. T050 má
souběžný mezistav `43 verified + 1 uploading` před finálním 44/44. T052 při
řízeném `insufficient_storage` zachoval 45. relaci neověřenou a po obnovení
stejnou relaci dokončil. T053 zvýšil jen počet operací; mediální počty i bajty
se nezměnily. T058 ponechal `reconciliation_required=1` a `exports_blocked=1`.

Registrovaný stop odebral pouze `/camino-api`, zastavil vlastněný proces,
odvolal token a přesně obnovil původní Serve konfiguraci. Konečný stav je
`phase=stopped`, server ani cesta nejsou aktivní, Funnel zůstává vypnutý a
aktivních tokenů je nula. Podrobná hranice každého výsledku je v
`C05b_IPHONE_TEST_PLAN.md`.

Při prvním reálném startu byly opraveny dvě vady provozního obalu: přímý Python
vstup nyní přidá kořen projektu do importní cesty a vyhrazený C05b port 8767
nekoliduje se ScanDocu na 8766. Opětovné vložení aktuální URL je samostatný
potvrzovaný workflow `copy_url`.
