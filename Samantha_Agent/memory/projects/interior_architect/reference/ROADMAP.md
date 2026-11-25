# Vývojový plán

| Etapa | Orientační hodiny | Výstup a akceptační kritérium |
|---|---:|---|
| 0 Audit | 1–2 | Mapa kódu, rizika, baseline testů, plán migrace |
| 1 Maskování | 3–6 | Editor, uložení, kompozice, nulová změna chráněných pixelů |
| 2 Scene model | 2–4 | Verzované schéma, validace, neznámé údaje a zámky |
| 3 Půdorys | 4–8 | Editace, kóty, kolize, správný směr dveří |
| 4 Analýza | 4–8 | Hrany a validace, volitelné ML po benchmarku |
| 5 3D | 6–12 | Konzistentní kamery, otvory, materiály, export |
| 6 Adaptéry | 3–6 | Capability flags, zákaz neautorizovaných nákladů |
| 7 UX a stabilizace | 6–12 | Varianty, porovnání, reporty a regresní testy |

Celkem 29–58 hodin orientačně pro prototyp, bez auditu nelze garantovat; produkční verze může být výrazně náročnější.

## První implementační sprint
1. Zkontroluj AGENTS.md, git status, závislosti a testy. Zapiš baseline a audit.
2. Definuj datový kontrakt masek, identifikátor originálu a souřadnice.
3. Napiš čistou funkci rasterizace a řešení překryvů; testy před integrací.
4. Implementuj kompozici a kontrolu integrity včetně PNG round-trip.
5. Přidej editor do existujícího Cockpitu, undo/redo, uložení a obnovení.
6. Připoj lokální testovací kandidát (bez AI), zobraz before/after a report.
7. Připoj existující adaptér jen pokud jeho schopnosti a náklady dovolují bezpečné použití; jinak ponech explicitně nedostupný.
8. Spusť unit, integrační a UI testy; manuálně ověř na cílovém Macu, je-li dostupný. Reportuj výsledky a další krok.

Další sprint: scene model a 2D editor. Automatickou segmentaci a lokální generování odlož, dokud základ nefunguje.
