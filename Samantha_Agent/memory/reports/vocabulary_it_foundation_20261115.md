# Vocabulary IT — bod1, uzavřené vstupy a významový katalog

Schválení: „doplň podrobný plán vývoje do txt nakonec a rovnou začni prvním bodem“.

Výsledek
- Původní TXT rozšířené o181 řádků osmibodového plánu. Původních25010 bajtů
  včetně uživatelských SOUHLAS zůstalo přesným prefixem; ověřený readback.
-471/471 významů pod vit-0001–0471, všech471 aktivních a fyzicky dohledatelných.
-18 hlavních témat; slovní druh, typ a obtížnost jsou návrhy k redakční kontrole.
-460 navržených Slovíček a11 Interakcí; žádný automaticky přidaný idiom.
-112 prioritních karet, nikoli počet ověřených vad. Úplná fronta v TXT vedle katalogu.
-777 zmrazených souborů, z toho761 obrazů;121703729 bajtů soukromých kopií.
  U všech obrazů ověřeno dekódování a rozměry, u všech kopií přesný SHA/velikost.
- Původní CSV, mapping, rody, příkladové věty,10 naučených a260 obtížných zachované.
- Každá obrazová vazba zatím pending-review; tento krok neodhadoval finální ilustraci.

Ověření
30 cílených kontrol PASS. Reálné čtecí audity kanonického zdroje i uzavřeného
snímku:777/777 a471/471,18 témat. Testy obráceného pořadí a jiných Order,
homografů včetně portafoglio/nipote, neznámé/duplicitní karty, explicitního
aliasu, Unicode NFC bez odstranění diakritiky/case, původních rodů a L/HT,
neplatného katalogu, chybějících/změněných souborů a přesné velikosti písmen.
Nová doména vocabulary_it i testovací modul jsou zaregistrované ve stávající
programové bráně, včetně kontroly jejího výběru. Finální gate.json/gate.log
jsou v private/vocabulary_it_foundation_20261115. Plná sada nezadaná.

Rizika a další krok
Worktree má745 obrazů;16 kanonických obrazů je pouze v úplném soukromém snímku.
Nejde o produkční nedostatek ani důvod doplňovat obrázky náhradou. Před exportem
se použijí konkrétní schválené soubory z úplného zdroje. Krok2 začíná16 původními
resolverovými rozpory, smíchanými významy, konkrétními tvary a gramatickým rodem.
Návrhy nejsou CEFR, jazyková přejímka ani finální klasifikace. Žádné změny starého
CSV/mappingu, mazání, nová syntéza, push či nasazení. Vývoj ve vlastním worktree;
origin mezitím pokročil souběžným Willovým vývojem, lokální základ77b5f652 je
explicitní a neprokazuje integraci do novějšího main.
