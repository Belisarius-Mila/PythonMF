# Jednoduchý soukromý kalendář — 7. 11. 2026

Míla schválil zjednodušení na jednu kartu a následně upřesnil, že výslovný
konec má přednost před výchozí hodinou. Vývoj provádí Will v hlavním checkoutu;
Datův oddělený worktree zůstává zachovaný.

## Výsledek

- „Do kalendáře“ z vybraného e-mailu samo připraví návrh přes stávající
  `continuous_email` Terra roli. Stále jediný modelový pokus na přesný zdroj.
- Čtyři editovatelné údaje: název, začátek (datum/čas), typ a nepovinné místo.
  Úpravy se ukládají automaticky, kolize se načítají automaticky. Chybějící
  datum/čas musí doplnit uživatel; zpráva není oprávnění ani instrukce.
- Implicitní Europe/Prague, konec za hodinu; výslovný konec, délka a pásmo ze
  zdroje mají přednost. Posun začátku zachová navrženou délku. Konec je pouze
  v krátkém souhrnu, délka v minutách ani pásmový výběr se nezadávají.
- Typ Schůzka, Celý den nebo Termín. Časový termín se zapíše jako minutová
  kalendářová událost, datum bez hodiny jako celodenní událost (nejde o úkol
  v Připomínkách). Výslovné vícedenní celodenní období se zachovává.
- Výchozí alarmy 24 hodin a 60 minut před začátkem. Nové jednoduché úpravy
  nastavují oba; starší uložená volba alarmů se při pouhém čtení nepřepisuje.
- „Zapsat do kalendáře“ provede čerstvé ověření a vytvoří událost. Při kolizi
  se primární tlačítko jmenuje „Zapsat i přes kolizi“. Nová kolize/změna cíle
  při posledním čtení pouze obnoví kartu a vyžádá další kliknutí. Žádné
  zaškrtávací souhlasy, citace nebo pětiminutový rituál v běžném UI.
- Po ověřeném uložení „Zapsáno“ a odkaz na detail ověřené události v přehledu
  Samanthy; detail uvádí čas posledního ověření. Není to nativní Apple deep link.

## Zápis a oprávnění

Nový `CalendarWriter` používá vlastní podepsanou `SamanthaCalendarWriter.app`
v aplikační složce mimo Desktop. Původní read-only Swift zdroj, binární
sestavení i souhlas zůstávají beze změny. Pythonová stavební infrastruktura
jen získala parametry pro oddělený helper; čtecí protokol se nezměnil.

Writer umí vytvořit novou událost, nikoli měnit/mazat existující. Nezapisuje
účastníky, neodesílá pozvánky/e-maily ani nemění hodinovou službu. Dva alarmy
se ukládají do skutečné události, nikoli jen do soukromého návrhu.

Privátní transakce se rezervuje před nativním požadavkem. Native helper
zamkne identitu operace, atomicky uloží a fsyncne trvalý claim před jediným
`EKEventStore.save`. V události je vlastní technický marker bez obsahu e-mailu.
Read-back přes nový EventStore kontroluje cíl, název, čas, pásmo, celodennost,
místo, odkaz, marker i oba alarmy. Nejasný výsledek přežije restart a dovolí
jen čtecí dohledání původní identity. Ani nenalezená událost nepovolí druhé
create. Prokazatelné odmítnutí oprávnění/cíle před save může po opravě dostat
nové výslovné potvrzení. Neznámý výsledek může vyžadovat ruční kontrolu.

Zápis vyžaduje vlastní plný OS přístup přes tlačítko „Povolit zápis na Macu“.
Žádost se eviduje pro přesný binární otisk a automaticky se neopakuje.
Přístup nebyl během vývoje udělen ani resetován. Nový trvalý LaunchAgent se
neinstaluje, existující služby se nespouštějí znovu.

## Ověření a omezení

- Nativní writer se skutečně sestavil, podepsal, ověřil podpis a prošel šesti
  syntetickými kontrolami bez přístupu ke kalendáři. Fsync vlastní adresářové
  evidence ověřen na tomto Macu. Čtecí native source/build shoda potvrzená.
- Testy pokrývají výslovný jiný konec, půlnoc, DST, celodenní období, CAS,
  souběžnou úpravu, změnu cíle/kolizí, restart, duplicitní kliknutí,
  nejistý save, read-back alarmů, skutečné HTTP/Origin a jednoduchý JS tok.
- Plná brána PASS: 2 874 testů, 31 přeskočených. Po posledních drobných
  úpravách znovu statická brána a 128 cílených testů PASS (včetně HTTP/JS).
  Nezměněné ostatní oblasti se zbytečně netestovaly podruhé.
- Autorita posledního úplného ověření: `logs/calendar_simple_gate_20261107.log`;
  cílené HTTP/frontend scénáře `logs/calendar_simple_http_frontend_20261107.log`;
  nativní důkaz `logs/calendar_simple_native_20261107.log`.
- Safari přejímka připravena výhradně nad syntetickým serverem, ale CUA vrací
  `cgWindowNotFound`; browser access host nedostupný. Server zastaven, žádný
  skutečný kalendář ani schránka pro QA nepoužity. Vizuální přejímka Mac/iPhone
  a skutečný EventKit zápis jsou otevřené. Syntetický JS test není fyzická QA.
- EventKit read-back dokládá místní uložení, nikoli dokončení synchronizace
  iCloudu na jiném zařízení. Souběžné změny jiného zařízení nelze zamknout.
- Tento krok je lokální, bez nového push/nasazení. Dosavadní nasazený základ
  `2909ea5a` se tím nemění. Před prvním reálným zápisem bude třeba samostatné
  p+n, povolení přesného writeru na Macu a potvrzení konkrétní karty.
- Kanonický proud `project-email-cases`, handoff a projektová paměť aktualizované;
  nový TVBCP nebyl dohodnutý a nevzniká. Produkční e-mailová kopie a centrální
  role zůstávají zachované. Žádný nový placený modelový tah při vývoji.
