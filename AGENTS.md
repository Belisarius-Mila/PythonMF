# PythonMF — projektové instrukce pro Codex

Platí pro repozitář PythonMF a jeho podprojekty.

## Rozcestník

- Společné pracovní instrukce jsou v `Samantha_Agent/AGENTS.md`; při zahájení
  práce je načti, pokud už nejsou v aktuálním kontextu.
- Při zahájení relace nebo změně tématu vyhledej v
  `Samantha_Agent/memory/MEMORY_INDEX.md` příslušný projekt, jeho handoff a
  relevantní projektovou paměť. Při pokračování stejného úkolu znovu čti jen
  změněné, chybějící nebo rozporné podklady.
- Pro `ulož handoff`, `ulož rozpracováno`, `přeruš práci` či požadavek na
  prioritu/připomenutí použij postup v
  `Samantha_Agent/memory/technical/session_recovery_rules.md`.
- Podrobnější instrukce konkrétního podprojektu se použijí v jeho rozsahu.

## Společné bezpečnostní hranice

- Měň jen soubory potřebné pro aktuální zadání; zachovej nesouvisející změny.
- Nikdy nemaž soubory bez výslovného souhlasu Míly. Pro vysoce rizikové akce
  platí `Samantha_Agent/memory/technical/global_safety_brake.md`.
- Do Gitu nepatří tajemství, soukromý obsah ani
  `Samantha_Agent/data/session_autosave/`. Nepoužívej `git add .`.
- Oprávnění k vývoji samo nepovoluje push, publikování ani nasazení;
  použij pravidla příslušného prostředí v `Samantha_Agent/AGENTS.md`.
