# C05c — čtyři stavové osy a pravdivé chyby

Datum zahájení: 2026-09-24

## Cíl

Rozdělit obrazovku **Uložení a přenosy** na čtyři samostatné pravdy:
**Telefon**, **Mac**, **Další záloha** a **AI**. Uživatel nesmí zaměnit ověřenou
kopii na Macu za další zálohu ani hotový přepis za ochranu originálu.

## Rozsah

- Telefon počítá místně uložené Momenty.
- Mac počítá úplné a čekající Momenty odděleně od počtu operací, souborů a
  bajtů ve frontě.
- Další záloha je zelená pouze po ověření konkrétních hashů médií a snapshotu
  metadat; bez C06b zůstává v produkční aplikaci neověřená.
- AI je nezávislá na uložení, Macu i záloze; bez C07 zůstává vypnutá.
- Síťové a serverové chyby mají uživatelské texty bez tvrzení o příčině, kterou
  aplikace nemůže prokázat.
- T054 a T055 mají syntetické modelové scénáře. Ladicí UI fixture je dostupná
  pouze v simulátoru a nemůže změnit produkční stav na zařízení.

## Mimo rozsah

- C06a spravovaný běh služby a párování.
- C06b vytvoření, ověření a obnova druhé zálohy.
- C07 produkční přepis a jiné AI úlohy.
- Nový serverový přenos, Serve, Funnel, token, push, nasazení a instalace.

## Akceptace

| Test | Požadovaný důkaz |
|---|---|
| T050 | `Ověřuji` zůstává čekající stav Macu; zelený stav vznikne až po serverovém potvrzení. |
| T051 | Nedostupný Mac nezablokuje místní uložení a text nevymyslí příčinu. |
| T054 | Hotová AI bez zálohy i záloha bez hotové AI vytvoří čtyři nezávislé stavy bez univerzálního zeleného výsledku. |
| T055 | Po změně textu nebo soukromí zůstávají ověřená média, ale novější metadata čekají na další snapshot zálohy. |

## Hranice důkazu

Automatické testy dokazují výpočet a prezentaci stavů nad syntetickými daty.
Nezakládají skutečnou další zálohu ani AI výsledek. Fyzický iPhone může potvrdit
rozložení, čitelnost a pravdivý aktuální produkční stav; skutečné konce T054 a
T055 vyžadují C06b a C07.
