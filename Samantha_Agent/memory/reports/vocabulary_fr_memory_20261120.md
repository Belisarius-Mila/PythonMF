## 2026-11-20 23:44 CET — Janino francouzské pexeso 6 × 4

Hotovo: V Janině francouzštině nová část Pexeso se stejnými pravidly jako
EN:24 číslovaných rubů,12 různých dvojic,1–4 krátká jména, skóre a sbírky.
Po otočení obrázek, francouzská MP3 a čeština2 s; porovnání po dočtení,
zelená shoda, dvě šedá místa a pokračování stejného hráče, při neshodě
střídání. Konec/remíza, rozbalení sbírek, stejná/nová zásoba, projektor
a ruční obnova dokončených tahů bez autoplay. PC6×4, úzký displej4×6.

Rozhodnutí: Míla zadal stejné pexeso v Janině Francouzštině. Francouzský
klient používá svůj společný výběr Všechna/Jen obtížná, témata a další
filtry; hra osobní označení ani A–D nemění. Samostatný sessionStorage
vocabulary-fr.memory-pairs.v1, validace FR UID a existujících FR médií.
Přenos současného EN pravidla, bez nových ilustrací, MP3 nebo změn obsahu.
Nové p+n nezadané. Stávající FR TVBCP zůstává kanonický, žádný nový dokument.

Další krok: Dokončit programem vybranou doménovou bránu a jeden lokální
commit; přesný head/bránu určuje private/vocabulary_fr_memory_20261120/
completion.json. Míla může přezkoušet místní náhled; publikace až na p+n.
Navrhované další kroky: Fyzická přejímka na Janině zařízení po vydání.
Technický důkaz:47 klientských JS scénářů PASS včetně12 nových pro pexeso,
FR bez CZ fallbacku, načasování, skóre, obnova, filtry a neměnnost osobních
záznamů. Finální stav po posledním zpřesnění ověří doménová brána v gate.log.
Skutečný481kartový katalog vytvoří12 kompatibilních dvojic se zvukem.
Safari Mac:24 míst6×4,4 jména a skóre současně, FR/krátká CZ, neshoda
Jana→Eva, reload a ruční pokračování Evy. Fyzický iPhone zůstává otevřený.
Veškeré FR datové JSON a EN zdroje hashově zachované. Původní média ani
osobní soubory se neupravují; bez push, nasazení, TTS nebo restartu služeb.

Implementace: docs/vocabulary-fr/memory.js, gallery.js, index.html a gallery.css.
Používá stávající model.js, practice.js a veřejné FR manifesty. Oddělená
francouzská hra zachovává schéma, jazyky a namespace bez importů EN modulu.
Syntetická testovací data neobsahují skutečný Janin osobní seznam.
