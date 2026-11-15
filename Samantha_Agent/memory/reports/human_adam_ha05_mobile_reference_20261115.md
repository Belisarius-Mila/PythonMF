# HA-05 — Starý odkaz na práci po reconnect


## 2026-11-15 22:03 CET — HA-05: obnova starého odkazu v mobilním panelu

Hotovo: Monitor po znovupřipojení umí čtením ověřit konečný stav staré
uložené reference a poté načíst aktuální práci. Zastaralá generace připojení
už sama nevytvoří trvalé Průběh práce není ověřen a neuzamkne ovládání.
Rozhodnutí: Oprava řeší hlášku z iPhonu po obnovení spojení. Běžící aktivace
z Macu se neopakuje; začlenění zdrojů počkalo na konec její dokončovací úlohy.
Samostatné p+n je nadále potřebné pro změnu běžícího UI.
Další krok: Po cílené bráně uložit lokální commit a požádat o vydání opravy.
Navrhované další kroky: Ověřit iPhone po nasazení; HA-09 zůstává samostatný.
Technický důkaz: Reprodukce nad skutečnou ukončenou úlohou generace215
při spojení216 vytvořila blocked/error. Kandidát ověřil přesný starý konec,
pouze GET načetl současný průběh a správně ukázal awaiting_completion.
Node sada má24 scénářů: původní18 a6 regresních skupin pro historické konce,
client-only reference, aktivní/unknown práci, cizí scope/budoucí generaci,
nové admission a již pozorovanou aktuální práci. Žádný automatický POST,
nový tah, zvuk či opakované převzetí neproběhne. Ovládání čeká na čerstvý GET.
Finální důkaz: data/private/ha05_mobile_reference_fix_20261115/completion.json.
Rizika: Fyzická iPhone přejímka není nahrazena Node testem. Starý běžící nebo
nejistý záznam zůstává zablokovaný; konec se nesmí předpokládat ani zahodit.
