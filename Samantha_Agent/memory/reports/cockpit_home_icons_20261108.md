# Oddělené ikony Cockpitu a rychlého úkolu — lokální metadata

Míla popsal přecházení obou ikon na naposledy otevřený kalendář nebo úkol.
Způsob vytvoření ikon zatím nepotvrdil; pracovní předpoklad je Safari →
Přidat na plochu. Fyzická příčina na jeho iPhonu nebyla reprodukovaná.

Živý audit hlavní stránky i `/calendar/` potvrdil absenci manifestu.
`/calendar/task/` již má vlastní manifest, id/start `/calendar/task/` a úzký
scope. Tato existující identita je zachovaná, stejně jako úložiště rozepsaného
zadání a původní zápis/obnova/mazání.

## Lokální změna

- Čtecí `/cockpit.webmanifest`: id `/`, start `/`, scope `/`, standalone,
  název Samantha Cockpit. Hlavní stránka a kalendář odkazují na tentýž
  manifest; nová hlavní ikona přidaná i z kalendáře má start v Cockpitu.
- Ikona Nový úkol má dál jinou identitu i název a začíná přímo formulářem.
- Doplněná nápověda přidání obou ikon zvlášť a volby Otevřít jako webovou
  aplikaci, pokud je k dispozici.
- Žádné přesměrování na visibilitychange/pageshow, reset polí, migrace nebo
  výmaz localStorage/sessionStorage. Změna metadat nemá opouštět rozepsaný
  formulář, aktivní chat ani nejasnou kalendářovou operaci.

## Meze a přejímka

Apple popisuje `id` jako rozlišení webových aplikací a `start_url` jako
adresu načtenou při prvním otevření. Není to důkaz, že aplikace vždy opustí
již běžící poslední stránku. Metadata existujících ikon a jejich obnovená
okna nemusí změnu převzít. Nepovažovat tuto opravu za prokázané vyřešení
konkrétního iPhonu, dokud Míla nezopakuje svůj scénář.

Po samostatném p+n přidat pro zkoušku nové ikony s odlišnými názvy, hlavní
z `/` a Nový úkol z `/calendar/task/`, v Safari s povoleným Otevřít jako
webovou aplikaci. Stávající ikony ani jejich data se tímto nemažou; případné
odstranění staré aplikace může odnést její místní rozepsané zadání, proto
nejprve ověřit, že není pending/nejasné. Změnu starých ikon musí provést Míla.
Je-li ikona Zkratka, prověřit místo toho její konkrétní cílovou URL.

Přejímka: hlavní → kalendář → opustit → Nový úkol; úkol → opustit → hlavní.
Ověřit také běžný návrat k rozepsanému formuláři, který má zůstat zachovaný.
Bez telefonu nelze potvrdit přidání ikony, iOS úložiště ani app-switch resume.

## Důkaz

- 36 cílených testů PASS (skutečné HTTP, rozlišení efektivních app id/start,
  přidání hlavní ikony z kalendáře, zachování task identity, odmítnuté query,
  čtecí stránky bez kalendářových mutací, dosavadní frontendové kontrakty).
- Statická brána a git diff --check PASS. Změna je pouze čtecí instalační
  metadata a nápověda; dosavadní serverová/klientská persistence beze změny.
- `logs/cockpit_icons_targeted_20261108.log`, `cockpit_icons_static_20261108.log`,
  `cockpit_icons_live_baseline_20261108.log`.
- Předchozí nasazení f51f3412 má potvrzené Terra p+n, CI 42493938340 success
  a uživatelskou přejímku mazání. Tato nová metadata zatím bez p+n.
- Nesouvisející neversionovaný OBNOVA_SAMANTHY_NOVY_MAC.txt v kořeni PythonMF
  je zachovaný, nečtený a nezařazený do tohoto commitu.

Podklady: [Apple WWDC23 — What's new in web apps](https://developer.apple.com/videos/play/wwdc2023/10120/),
[WebKit — Manifest ID](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/).
