## 2026-11-20 13:08 CET — Pexeso pro děti, 32 číslovaných míst a 1–4 hráči

Hotovo: Místně zapojená samostatná část Pexeso.16 různých významů každý
dvakrát,32 pevných číslovaných rubů, na PC8×4 a na úzkém displeji4×8.
1–4 krátká jména, aktivní hráč, sbírky a skóre po dvojicích. Shoda nechá
hráče pokračovat a dvě šedá prázdná místa; neshoda střídá hráče. EN MP3,
česká nápověda2 s, porovnání po dočtení, zelená shoda, konec/remíza,
rozbalení získaných obrázků a opakování stejné či nové zásoby. Filtry témat,
A–D, obtížných a posledních N. Kontrola záměn v celé šestnáctce včetně
stejných náhledových hashů; zvuk a obrázky zůstávají stávající.

Rozhodnutí: Míla schválil celý Vocabulary_EN_Pexeso_navrh_2026-11-20.txt
slovy „SUPER! Souhlas. Zahaj prosím vývoj.“ Jména a rozehraná partie jsou
pouze v sessionStorage tohoto panelu, bez síťového zápisu a bez změn A–D.
Obnovení zachová dokončené tahy a nabídne ruční pokračování bez autoplay.
Tento nový vývoj nepovoluje nové p+n. Samostatný EN TVBCP není založen;
zachovaná vazba na architektura_komunikace_samantha.txt.

Další krok: Dokončit programovou doménovou bránu a jediný lokální commit.
Přesný konečný head/bránu určuje private/vocabulary_en_memory_20261120/
completion.json. Následně Mílova přejímka a samostatný pokyn k p+n přes Terru.

Navrhované další kroky: Vyzkoušet skutečnou výuku/projektor a fyzický telefon.
Větší plány a zadávání čísla klávesnicí zůstávají případným navazujícím krokem.

Technický důkaz:13 nových herních scénářů skutečného JS modulu PASS; celá
původní a rozšířená Node sada108 PASS před posledním drobným vizuálním
zpřesněním. Finální brána ověří přesné konečné zdroje včetně všech scénářů.
Safari Mac:4 jména,32 míst8×4, EN/krátká CZ, neshoda/střídání a obnova
správného hráče; celý plán i skóre ve skutečném okně.7/7 místních HTTP
souborů přesných.531 aktivních karet a média beze změny.17 předem existujících
nesouvisejících kopií s „2“ zachovaných; do našeho commitu nepatří.
Fyzická iPhone přejímka otevřená. Žádné nové ilustrace/TTS/push/deploy.

Implementace: docs/vocabulary-en/memory.js; úzké zapojení index.html, gallery.js a gallery.css.
Scénáře jsou součástí registrovaného test_vocabularyen_selection.js přes test_vocabularyen_gallery.
