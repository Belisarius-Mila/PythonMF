# Samantha — ověření a rychlost vydání

Proud `project-samantha-infrastructure`; kanonická pravidla
`../technical/validation_policy.md`, rozhodnutí v existujícím TVBCP téhož proudu.

15.11.2026 Míla schválil nejprve společný runner a podepsané účtenky, následně
snížení běžného běhu pomocí domén/závislostí, denní úplné CI regrese a Git fixture.

Aktuální místní politika validation-v2 má pevnou mapu12 oblastí a malý společný
bezpečnostní základ. Reverzní importy přidávají potřebné konzumenty; neznámá
závislost, dynamický import měněného modulu, nový spustitelný soubor či společná
kritická změna znamená plnou sadu. Bezpečnost zápisu/obnovy kalendáře se ověřuje
vždy při kalendářové změně. Počet300 je cíl, nikoli možnost testy oříznout.

Změna existujícího calendar_writer:282 testů/39,283s, celý diagnostický běh
56,874s. Předchozí plná kalendářová brána3972/621,309s unit,645,4s celkem.
Aktuální změna samotné politiky vyžaduje závěrečnou plnou bránu; její skutečná
účtenka, počty a neměnné finální otisky jsou v
`data/private/validation_domains_20261115/completion.json`. Podrobný report
`../reports/validation_domains_20261115.md`. Bez PASS účtenky nejde o dokončení.

Cílená místní publikace dále vyžaduje podepsaný plný základ stejného prostředí
nejvýše24h starý. Převzetí stejných bajtů/režimů a kontrola před/po zůstávají.
CI nad úplným event diffem používá stejnou mapu; denně02:17 UTC a ručně plná
sada, bez místní publikační účtenky. Rozvrh je až v budoucím schváleném pushi.
Git fixture jsou úplné samostatné kopie procesového seedu, bez hardlinků.
Jeden křehký celostránkový hash test nahrazen funkční kompoziční kontrolou.

Historický stav v1: vydáno38a33532 registrovaným Terra p+n,
job0203d0fbaf6cae4b993c7fa4670a9bb6. Bootstrap byl plný798,9s, celé vydání871,1s;
starý backend ještě nemohl převzít nový důkaz. Místní v1 full3966/623,6s
oproti následnému převzetí25,9s. Stav v1 nenahrazuje aktuální živý audit.

Tento v2 vývoj ani předchozí kalendářový f2b56fa3 nejsou vydané.
Žádné nové p+n, restart, helper/grant, kalendářový create ani záloha.
Média, Git historie a aktivní Data zachované; fyzická/provozní přejímka zvlášť.
