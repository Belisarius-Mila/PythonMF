# Terra 6.1 — schválená zkouška vykonavatele p+n


## 2026-10-28 12:02 CET — Cenově schválená zkouška Terry 6.1 pro p+n

Míla po zobrazení ceny výslovně schválil Terru pro zkoušku a p+n, protože hlásí vyčerpaný kredit Luny. Do dalšího rozhodnutí je release_executor v centrálním config/agent_roles.json preferovaně gpt-6.1-terra/high. Jde o společnou roli pro registrovaná p+n všech proudů, nikoli o změnu hlavního Adama nebo simple_developer; vývojová role zůstává beze změny. Původní schválený kandidát Luna je zachovaný v politice, aktuální předání musí být výslovně připnuté k auditované Terře, aby nepřešlo na fallback.

Oficiální Standard kredity / milion tokenů: Terra 25 vstup, 1,25 cache, 125 výstup; Luna 2,5 / 0,25 / 12,5. Cena byla Mílovi před schválením ukázána jako 10× za běžný vstup/výstup a orientačně 0,7 kreditu za podobné převzetí, zkouška zvlášť. Není to cenový strop ani doložená faktura. Zdroj https://learn.chatgpt.com/docs/pricing .

Registrovaný probe_release_executor_candidate('gpt-6.1-terra','high') skutečně prošel 2026-10-28T11:01:43+00:00, probe_only=true, published=false. Důkaz data/private/communication/release_candidate_probes/terra_20261028.json obsahuje pouze redigovaný výsledek; žádné tajemství ani historii. Nejde o vývojovou zkoušku simple_developer. Plné vydání čeká na brány a přesný audit celého balíčku v project-camino.

Připravený UI krok: e95b9874 (větší okno a celá obrazovka). Předchozí nasazený základ 205789da. Aktuální krok mění pouze modelovou politiku p+n a projektové zápisy; nezařazuje novou změnu aplikace. Následuje plná brána a jedno předání přes submit_release(wait=True), bez nativního pomocného agenta, retry nebo přepnutí modelu uvnitř úlohy.

Plná místní brána 2258 testů PASS (493,520 s unit část; 502,1 s fáze), 53 cílených testů rolí/předání PASS. Důkaz logs/terra_release_precommit_gate_20261028.log. P+n ještě nebylo spuštěné.


## 2026-10-28 12:21 CET — Výsledek skutečného p+n

Účtenka 6bf0ff7d29efba5a7da3eff147e08d59 completed, push_state=confirmed, deployment_state=confirmed, 2 commity do f336fd47e0b77420baeab25683cbc2bb39441ed3, project-camino → Cockpit. Vykonavatel gpt-6.1-terra/high, policy digest 2658fc0b796051bbbfe1bd957bd1c62c0977bd081fe5f37561bf4ec873c0540d. Plná publikační brána 2258 PASS / 445,5 s, smoke 5/5, protected_services_unchanged=true. Code stamp 296a14675318a23b zachovaný (měnily se frontend, modelová politika a dokumentace).

Adam převzal účtenku v nativní relaci a jednou ověřil GitHub head, health HTTP 200 a přesnou shodu živého HTML se zdrojem; SHA-256 23faa858e96af264b405a3af1b7a5a78255d2e41eda3652d449b9a42393056dc, nové tlačítko přítomné. returned_to_adam=false zůstává portálový příznak, není důvodem retry.

Samotné převzetí: 26516 vstupních, 0 cached, 72 výstupních tokenů (z toho 13 reasoning), celkem 26588. Při schváleném Standard ceníku odhad 0,6719 kreditu; neobsahuje kandidátský probe, Adama ani jiné části práce a nejde o fakturu nebo důkaz úspory celého postupu. Terra zůstává preferovaným release_executor do dalšího rozhodnutí Míly; simple_developer beze změny. Fyzická Safari přejímka fullscreen NEOVĚŘENO. Tento závěrečný zápis je místní pro příští balíček, bez nového zásahu do UI nebo dalšího p+n.
