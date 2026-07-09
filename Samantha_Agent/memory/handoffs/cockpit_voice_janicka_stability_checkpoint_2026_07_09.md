Nazev: Cockpit / VoiceBridge / Janicka stabilita po testech
Priorita: 1
Stav: ceka na retest
Pripomenout pri startu: ano
Datum: 2026-07-09

Co se resilo:
- Stabilita Cockpitu, VoiceBridge a okna Janicka po upravach kolem health checku, managed Codex relaci a hlasoveho dorucovani.
- Rozliseni skutecneho prevzeti hlasove zpravy v Codex chatu od automaticke odpovedi watcheru.
- Uklid a diagnostika starych Janicka Codex relaci mimo spravu.

Co je hotove:
- Hlavni VoiceBridge diagnostika rozlisuje beznou Adam relaci, managed relace a orphaned Janicka relace.
- Okno Janicka umi zobrazit a nabidnout uklid starych Janicka relaci mimo spravu.
- Managed Janicka light relace se nepocita jako problem hlavniho Adam VoiceBridge.
- Recoverable frontend network chyby typu kratky `Load failed` se po uspesnem health checku vycisti.
- Automaticka odpoved watcheru je explicitne oznacena jako automaticka a ne jako prevzeti v Codex chatu.
- Pri selhani automaticke direct odpovedi se ulozi bezpecny technicky detail do pending zaznamu pro Adama.
- Testy pro Adam voice mode a Cockpit byly rozsireny o tyto pripady.

Co neni hotove:
- Neni jeste overeno, ze Janicka chat funguje i po ukonceni teto dlouhe relace a zavreni VS Code.
- Neni jeste provedena navazujici recovery zaloha po tomto checkpointu.

Dalsi krok:
- Po commitu a pushi ukoncit dlouhou relaci, zavrit VS Code, spustit Cockpit bez VS Code a rucne otestovat `Janicka` -> `Zeptat se Adama`.

Navrhovane dalsi kroky:
- Okamzity retest: bez VS Code poslat v Janicce alespon dva navazujici textove dotazy a overit, ze odpoved dorazi z managed Janicka cesty.
- Pokud Janicka bez VS Code selze, nerozbijet hlavni VoiceBridge naslepo; nejdriv cist stav light relace, managed TTY, screen delivery a fallback.
- Po uspesnem retestu udelat externi recovery zalohu.

Zmenene nebo relevantni soubory:
- `app/cockpit.py`
- `app/speech/adam_voice_mode.py`
- `tests/test_cockpit.py`
- `tests/test_adam_voice_mode.py`
- `memory/handoffs/cockpit_voice_janicka_stability_checkpoint_2026_07_09.md`

Bezpecnost / neukladat:
- Neukladat ani neopisovat plne texty hlasovych pokynu, osobni udaje, tokeny, API klice ani obsahy soukromych dokumentu.
- Pri ukoncovani relaci chranit aktualni Adam voice marker a managed Janicka relaci; neukoncovat bez potvrzeneho duvodu.
