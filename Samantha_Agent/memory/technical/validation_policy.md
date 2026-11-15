# Jednotná validační politika

Rozhodnutí Míly 2026-11-15: potřebné kontroly musí vynucovat program, opakované
ověření nezměněného kódu nemá brzdit každý commit a následné p+n.

## Jediná autorita a použití

Autoritou je `app/communication/validation_policy.py`. Stejný runner
`checkpoint_quality_gate.run_checkpoint_quality_gate` používají checkpoint,
GitHub batch, nasazení i ověření již zarovnaného vydání Lunou. Terminál používá
registrovaný `validate_project`, přesný příkaz `.venv/bin/python scripts/validation_gate.py`.
Příkaz nic nepushuje, nenasazuje ani nerestartuje. Samostatná GitHub CI dál
spouští úplnou sadu; místní účtenky se na GitHub neposílají.

Model, uživatelský payload ani starý `allow_quick_gate`/`skip_unit_tests` nesmí
zvolit publikační režim. Samotný `cockpit_quality_gate.py --skip-unit-tests`
zůstává diagnostickou statickou kontrolou a nevytváří použitelný důkaz vydání.

## Výběr kontrol

- Porovnává se celý kandidát od auditovaného origin/main včetně staged,
  unstaged a neignorovaných nových souborů, nikoli jen aktuální projekt.
  Přejmenování zahrnuje původní i novou cestu.
- Neznámé změny a rizikový kód (workflow, závislosti, checkpoint, publikace,
  persistence, zálohy, transakce, pošta, kalendář) vyžadují plnou sadu.
  Totéž platí pro změnu pravidel, testů, tohoto návodu nebo AGENTS.md.
- Pevný úzký seznam dokumentačních cest a známých frontendových souborů má
  pevně přiřazené testovací moduly. Autoritativní seznam je pouze v programu.
  Cílený běh vždy ponechává všechny dosavadní statické kontroly.
- Cílený běh vyžaduje místní podepsaný základ po úspěšné plné bráně v témže
  prostředí. Chybějící modul/základ nebo nejistý vstup znamená plnou bránu.
- Po automatickém doplnění handoffu/TVBCP lze využít základ s přesně stejnými
  bajty a režimy všech souborů mimo povolený cílený seznam. Podepsaný manifest
  určí změněné dokumenty/UI a jejich testy; nedává výjimku změněnému kódu.

## Důvěryhodná účtenka

Soukromá metadata společného Gitu obsahují adresář `samantha-validation`,
náhodný lokální podpisový klíč a atomicky zapisované HMAC-SHA256 účtenky.
Adresář má režim700, klíč a účtenky600. Nejsou součástí pracovního stromu,
commitu, zálohované projektové paměti ani payloadu modelu; nejde o ochranu
před správcem Macu nebo nedůvěryhodným procesem pod stejným účtem.

Účtenka váže SHA-256 skutečného obsahu a režimů všech verzovaných i
neignorovaných vstupů, verzi politiky, testovací recept, Python/prostředí,
verze/RECORD instalovaných závislostí a otisky vybraných nástrojů.
Vstupy se ověří před i po testech nebo převzetí. Změna stejné velikosti a
mtime proto účtenku zneplatní. Externí/adresářové symlinky nemají cache.
Ignorovaná soukromá provozní data nejsou vstupem cache syntetických testů;
živý smoke, audit Git heads, oprávnění a chráněné služby se vždy ověřují zvlášť.

Platnost je nejvýše24 hodin od původní plné brány; řetězení cílených kontrol
ji neprodlužuje. Úspěšný běh musí doložit alespoň jeden test. Vadná, podvržená,
prošlá nebo nekompatibilní účtenka se nepoužije. Starý načtený modul po změně
politiky nevydává zrychlené důkazy. Shodný strom lze po lokálním commitu
svázat s jeho přesným SHA; push a deploy tak neopakují totožné testy.

## Provoz a limity

Rezerva samotné plné brány je1500 sekund. Timeout uchová částečný log a nedává
souhlas s opakováním publikace. První vydání této změny musí bezpečně projít
plnou bránou; teprve běžící nový backend umí novou politiku. Čtenáře režimu
`targeted` mění tentýž balíček jako jeho producenta. Staré `quick` účtenky
zůstávají čitelné pro historii, nepovolují novou publikaci bez testů.

Další optimalizace dlouhých syntetických Git fixture a oddělení médií jsou
samostatné návrhy. Přesuny dat ani přepis Git historie nejsou tímto povolené.
