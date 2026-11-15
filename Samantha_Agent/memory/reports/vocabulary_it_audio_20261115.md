# Vocabulary IT — italský hlas a zvuková knihovna


### 2026-11-15 23:08 CET — Italský hlas a úplná knihovna slov i vět

Hotovo: Všech497 aktivních karet má hotové nahrávky slovíčka i příkladové
věty v italštině a češtině.1988 vazeb používá1907 unikátních MP3 (26920656 B).
Italský hlas Elsa, český Vlasta, rychlost-10 %. Poslech v galerii přehraje
italské slovo a krátce ukáže češtinu; větší karta přehrává slovo nebo celou
větu v právě zvoleném směru. Hotová knihovna přežije nový export dat.

Rozhodnutí: Míla schválil pokračování „italský hlas a zvuková knihovna…“
a potvrdil, že nemá jinou hlasovou preferenci. Použit stávající registrovaný
Edge generátor; žádné nové placené Azure volání. Původní EN ani CSV/mapping
se nemění. Souhlas s vývojem není p+n.

Další krok: Italská obrázková hra podle bodu7 schváleného plánu.

Navrhované další kroky: Přesná revize italských obrazových kolizí pro hru;
telefonní poslech/přejímka; samostatně registrovaný publikační cíl a vydání.

Technický důkaz:1907/1907 souborů má přesnou SHA, kladnou délku, MP3 codec,
plné dekódování a netichý signál. 1801 nových nahrávek, 106 přesně
shodných českých převzatých z EN do vlastní IT knihovny. Manifesty mají
status=complete,497 UID každý, přesné zdrojové texty a oddělené word/sentence
cesty.10 audio testů bez online syntézy a16 JS scénářů v doménové bráně:
nejistá žádost blokuje opakování, souběh drží zámek, před každým novým
voláním se kontrolují zdroje a veřejný index vzniká až po úplné kontrole.
Fyzický Safari na Macu: galerie,2/4/6 sloupců při100 %,8 při zmenšení,
věta/odhalení/Další/návrat, posledních20 a reload; reálné MP3 přehrávání
slova IT a věty IT/CZ s modrou ikonou přehrávání Safari, CZ nápověda a návrat
italského popisku. Veškeré audio nebylo ručně poslechnuto; jazyková korektura
všech vět/metadat a skutečný iPhone/Android zůstávají otevřené.
Původní browser bridge je nedostupný, nativní Safari CUA funguje. Vlastní QA
okno a lokální server po testu uzavřené. Fyzický profil/PIN se neměnil.
Finální programová brána a shoda zdrojů: private/vocabulary_it_audio_20261115.
Lokální checkpoint proti společnému77b5f652; žádný push, nasazení ani zásah
do divergentního main/Willovy práce.

Provozní příkazy (z kořene PythonMF)
- Plán bez volání: python3 VocabularyIT/vocabulary_it_audio.py --root Samantha_Agent/data/private/vocabulary_it_gallery_20261115/inputs
- Nová výroba jen po kontrole plánu a autorizaci; --apply vyžaduje privátní --receipt.
- Při ztraceném dokončeném souboru obnovit přesné bajty; negenerovat automaticky znovu.
- Stav requested/uncertain zakazuje opakování; prohlédnout stejnou účtenku.
- Výchozí endpoint registrované knihovny15.11. fungoval. Starší workaround
  LL-076 se nemá zapínat automaticky a přepínat uvnitř paralelních požadavků.
- Generátor hlídá katalog/CSV/data před každou novou žádostí i publikací;
  export během výroby neměnit. Reexport až po dokončení.
- Veřejné manifesty obsahují pouze slovníkový text, nikoli privátní ledger.
