# Vocabulary FR — Willův klient v1.1, místní vývoj

Schválené rozdělení: Data připravuje jazykový obsah a soukromý balíček;
Will vlastní klienta, registry, společnou dokumentaci a finální integraci.
Základ je ověřená IT verze31c670bb začleněná do main8e03aba2.

Nový docs/vocabulary-fr obsahuje pouze7 obecných klientských souborů.
Žádný skutečný Janin katalog, export, obrázek ani zvuk nebyl vytvořen v docs,
VocabularyFR ani Gitu. Veřejné testovací podklady jsou syntetické ve fixtures.
Privátní místní náhled se stejným klientem používal jen tyto syntetické podklady.
Budoucí skutečný obsah má být nezměnitelný soukromý payload/data a payload/assets
s manifestem cest/velikostí/SHA, private=true/publicPromotionApproved=false.
Do tohoto kroku nebyl předaný a464 skutečných položek nejsou ověřené.

Klient přenáší galerii/filtry18 okruhů, posledních N podle stabilního id,
FR/CZ slova i věty, osobní profily A–D/PIN/zálohy, obrazové procvičování,
psaní a500ms nápovědu, smyčku a kontextové obrázky. UID namespace vfr-,
francouzské řazení, sourceFr/sourceSentenceFr/genderFr, vlastní úložiště.
Psaní zachovává významotvorné akcenty i œ; sjednocuje NFC, velikost a telefonní
apostrofy. Hledání je samostatně tolerantní. Žádný import starého L/HT.

Audio v1.1 přijímá schema1, language=fr, words/sentences a stavy
not-generated/partial/complete. Chybějící fr/cz je null. Shoda celého zdroje
hesla/věty se kontroluje před použitím; relativní cesty se kontrolují zvlášť
pro každý kanál. Neplatný/chybějící FR soubor nezablokuje platnou češtinu
ani galerii. Explicitní tlačítka Francouzsky/Česky ukazují dostupnost zvlášť.
Smyčka při chybějící FR nahrávce zastaví stejnou kartu; hra takový hlasový
cíl vynechá s viditelným počtem chybějících FR nahrávek. Žádný tichý převod
FR akce na českou ani živé TTS. Stejný odemčený prvek smyčky; oddělené fresh
přehrání hry/psaní a ochrana před starými událostmi/Další zůstávají zachované.

Místní registrace existujícího project-vocabulary-fr → github_pages/vocabulary-fr/
a nová samostatná webová položka ponechávají původní desktopový launcher.
FR doména vybírá existující test_vocabularyfr_web_gallery a jeho syntetické
fixtures. Neexistující Datovy obsahové testy se neregistrují; připojí se při
integraci skutečně hotových obecných kódových souborů. Runtime Cockpitu nebyl
restartovaný/nasazený; před budoucím p+n potřebuje autorizovaně načíst nové
registry/validační mapu. Azure adaptér beze změny, žádná placená výroba.

Ověření:24 Node scénářů skutečných FR modulů,81 cílených Python kontrol
včetně registrace/cest publisheru a validačních kontraktů PASS. Nativní Safari
v localhost náhledu ověřilo galerii bez audia, odhalení FR/CZ, dva kontextové
obrázky nad celou větou, vysvětlení pozastavené smyčky při chybějící FR nahrávce,
Stop a návrat/fokus na poslední kartu. Testovací okno i server ukončené;
původní okno zachované. Nejde o poslech skutečného hlasu nebo telefonní QA.

Finální programově vybranou bránu, přesné otisky a lokální commit dokládá
výhradně data/private/vocabulary_fr_client_20261117/completion.json.
Další krok je převzít uzavřený Datův soukromý balíček a samostatně ověřit jeho
otisk i skutečných464 karet vedle klienta. Žádný nový push/publikace/restart.
