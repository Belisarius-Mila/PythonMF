# Cockpit: společné spouštění Gitu — 14. 9. 2026

Další lokální řez nad `e7723c9a`. Stejných **1656/1656 testů** prošlo před i po:
**307.14 → 261.43 s**, úspora **45.71 s / 14.9 %**
v unittest části celé brány. Předchozí workspace optimalizace je zapnutá v obou bězích.

## Změna

- Stávající výběr Apple Git přes `xcrun --find git` přesunut beze změny do
  `git_runtime.py`; stejnou volbu sdílí workspace, checkpoint, deploy,
  GitHub batch, remote sync a takeover.
- Společný testový helper `git()` používá tutéž binárku. Repozitáře, fixture
  kroky, Git příkazy a testové scénáře zůstávají skutečné a oddělené.
- Nový modul zahrnut do kompilace a povinné plné brány pro rizikové změny.
  Přibyl jeden regresní test této hranice; původních 1655 zůstává.
- AST porovnání pěti produkčních souborů dokládá jen záměnu executable,
  import a nový gate prefix. Workspace logika a přesunuté tělo resolveru shodné.

## Metoda a důkazy

První běh dočasně nastaví `GIT_EXECUTABLE='/usr/bin/git'` pouze v pěti nově
upravených produkčních modulech a společném test helperu. Workspace už používá
přímý Git jako v dosavadním `e7723c9a`. Druhý běh spouští kanonickou plnou bránu
s `--unit-test-timings`. Stejný manifest, pořadí, počty testů po modulech a Git:
`git version 2.50.1 (Apple Git-155)`. Žádné paralelní sady, změny timeoutů ani vyřazení testů.
Časy porovnávají unittest část; importy a statické kontroly jsou mimo ni.

| Skupina | Testů | Před (s) | Po (s) |
| --- | ---: | ---: | ---: |
| simple_main_checkpoint | 29 | 73.80 | 59.84 |
| simple_main_deploy | 18 | 46.79 | 41.03 |
| human_adam_takeover | 13 | 36.98 | 29.58 |
| human_adam_workspace | 35 | 30.74 | 26.03 |
| github_batch | 5 | 10.60 | 7.77 |
| main_remote_sync | 6 | 12.42 | 7.69 |

Úvodní pilot dvou původních deploy testů prošel: 450 přímých workspace volání,
41 zbývajících volání launcheru. Z nich 29 ve společném test helperu, 6 v takeover,
4 v deploy a 2 v samostatné přípravě bare originu. Poslední dvě nejsou součástí
řezu. Agregované počty a časy jsou v doprovodném JSON, bez argumentů či cest
soukromých dat. Plná brána po změně prošla včetně statických kontrol.

## Omezení a další krok

Jeden pár měření na tomto Macu není záruka stejného výsledku jinde. Dnešní procento
se nesčítá se včerejšími 25 %. Výběr toolchainu platí do restartu; při chybě,
nevhodné cestě, timeoutu a mimo Mac zůstává systémový Git. Stav repozitáře se
necachuje. Nová změna je lokální, bez push/nasazení či měření živé odezvy Cockpitu.

Další optimalizaci vybírat podle nových časů nejdražších skupin; zbývající
samostatné testové Git spouštěče jsou jen kandidát. Povinné vydávací kontroly
zachovat; běžné úpravy ověřovat cíleně.
