# Terra 6.1 — schválená zkouška vykonavatele p+n


## 2026-10-28 12:02 CET — Cenově schválená zkouška Terry 6.1 pro p+n

Míla po zobrazení ceny výslovně schválil Terru pro zkoušku a p+n, protože hlásí vyčerpaný kredit Luny. Do dalšího rozhodnutí je release_executor v centrálním config/agent_roles.json preferovaně gpt-6.1-terra/high. Jde o společnou roli pro registrovaná p+n všech proudů, nikoli o změnu hlavního Adama nebo simple_developer; vývojová role zůstává beze změny. Původní schválený kandidát Luna je zachovaný v politice, aktuální předání musí být výslovně připnuté k auditované Terře, aby nepřešlo na fallback.

Oficiální Standard kredity / milion tokenů: Terra 25 vstup, 1,25 cache, 125 výstup; Luna 2,5 / 0,25 / 12,5. Cena byla Mílovi před schválením ukázána jako 10× za běžný vstup/výstup a orientačně 0,7 kreditu za podobné převzetí, zkouška zvlášť. Není to cenový strop ani doložená faktura. Zdroj https://learn.chatgpt.com/docs/pricing .

Registrovaný probe_release_executor_candidate('gpt-6.1-terra','high') skutečně prošel 2026-10-28T11:01:43+00:00, probe_only=true, published=false. Důkaz data/private/communication/release_candidate_probes/terra_20261028.json obsahuje pouze redigovaný výsledek; žádné tajemství ani historii. Nejde o vývojovou zkoušku simple_developer. Plné vydání čeká na brány a přesný audit celého balíčku v project-camino.

Připravený UI krok: e95b9874 (větší okno a celá obrazovka). Předchozí nasazený základ 205789da. Aktuální krok mění pouze modelovou politiku p+n a projektové zápisy; nezařazuje novou změnu aplikace. Následuje plná brána a jedno předání přes submit_release(wait=True), bez nativního pomocného agenta, retry nebo přepnutí modelu uvnitř úlohy.

Plná místní brána 2258 testů PASS (493,520 s unit část; 502,1 s fáze), 53 cílených testů rolí/předání PASS. Důkaz logs/terra_release_precommit_gate_20261028.log. P+n ještě nebylo spuštěné.
