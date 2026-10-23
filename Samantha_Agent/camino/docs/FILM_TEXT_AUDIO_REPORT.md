# Texty a komentáře ve střižně — 23. 10. 2026

## Rozsah a stav

Míla schválil vývoj nabídnutého panelu Texty a komentáře. Implementace je
lokální, nenasazená. Telefon, Camino služba a archiv se neupravují.
Neproběhl produkční render ani zápis do existujícího filmového projektu.

Read-only audit dne 6. října: uložená revize 5, 25 obrazových záběrů,
pět povolených zvukových částí, žádná zapnutá. Pro tento den nejsou na Macu
přijaté textové revize. Archiv celkem obsahuje osm operací append_text
a osm textových revizí; povolené texty jsou v pěti dnech. To neprokazuje
aktuální frontu telefonu ani příčinu chybějícího konkrétního textu.

## Uživatelské ovládání

- Panel nabízí aktuální přijatý text deníku, jeho čas a název Momentu.
  Upřednostňuje lidskou úpravu podle dosavadního TextHistory kontraktu.
- Text lze pro film upravit a výslovně nahradit titulek vybraného záběru
  (nejvýše 140 znaků na jednom řádku). Deník se nemění.
- Textová karta je samostatný obraz na tmavém podkladu, výchozí délka 5 s.
  Lze měnit text, délku 0,1–300 s, umístění na začátek nebo za záběr
  a zařazení. Nejvýše 32 karet, každá do 1000 znaků. Příliš dlouhý text
  se nekrátí automaticky; nečitelná karta zablokuje export s vysvětlením.
- Každý hlas má Poslechnout / vybrat úsek a Vložit komentář k záběru.
  Výběr nabídne celý původní úsek, zkrácení je ruční. Vložení odmítne
  překrytí jiného hlasu nebo přesah za obraz a ukáže potřebné prodloužení.
- Umístění hlasu je uložený absolutní čas. Po pozdější změně pořadí či délek
  obrazu je nutné jej zkontrolovat nebo zopakovat vložení k záběru.
- Chybějící text se vysvětlí jako chybějící přijatý podklad. Automatický
  přepis hlasu, generovaná řeč ani externí AI nejsou součástí změny.

## Data, soukromí a kompatibilita

Původní manifesty, revize a výstupy se nepřepisují ani nemigrují. Nabídka
textů je čtecí doplněk původní uzavřené sady. Až vědomé vložení uloží do
nové revize střihu referenci moment_id/revision_id/SHA-256 přijatého textu.
Pozdější textová úprava se do dřívějšího filmu sama nepromítne.

Povolenost vychází z aktuálního ověření celého dne. Jen pro mě, skryté
a nejasné zdroje se nevydávají. Původ textu včetně předků revizí se ověřuje
iterativně; cizí, soukromé či cyklické vazby se odmítnou. Vazby použitého
textu se ověřují při uložení, zadání exportu, v renderu a při výdeji MP4.

Zvukový poslech vzniká až na výslovný klik jako odvozená AAC kopie bez
zdrojových metadat v dosavadní soukromé sériové frontě. Výdej audio/mp4
znovu ověřuje původní manifest a aktuální povolenost. Originál není novou
HTTP cestou vydávaný. Opakované otevření používá stejnou ověřenou kopii.

Staré střihy bez karet a textových referencí zachovávají původní strukturu
i otisk. Samostatné karty se do časové osy vkládají při výpočtu, takže
dílčí náhled i finále používají shodné pořadí a délky.

## Provedené ověření a otevřené kroky

- Python py_compile, Node --check a git diff --check PASS.
- cockpit_quality_gate.py --skip-unit-tests PASS (statická brána).
- Read-only nové view nad revizí 5: stále 25 obrazových a 5 zvukových nabídek,
  žádný zapnutý hlas, 0 textů; původní Xcode nastavení má shodný SHA-256.
- Čtecí zachycení jednoho existujícího dne s textem bez uložení: jedna
  povolená textová nabídka a rozřešení její přesné reference PASS.
- Automatické testy nebyly přidávané ani spouštěné. Plná publikační brána,
  syntetický render karty i poslechové kopie a proklik Safari zůstávají
  NEOVĚŘENO. Statická brána není jejich náhradou.

Další krok: funkční ověření persistence, soukromí, renderu a ovládání;
případné samostatně schválené p+n přes registrovanou Lunu, potom fyzická
přejímka titulku, karty a vlastního hlasu v krátkém náhledu.

Redigované čtecí účtenky jsou v data/private/camino_texts_20261023/;
žádný osobní text ani nahrávka nejsou v tomto reportu nebo Gitu.

## Kontrolní oprava po první publikační bráně

První Luna úloha a3d0c4730ea1ef7a0e9f3b5f7a2336b7 se zastavila před
pushem: 2174 testů, jediný FAIL v očekávané délce složené stránky. Fixture
neobsahoval rozšíření nového panelu. Po kontrole diffu aktualizovaná délka,
počet řádků a SHA-256; stejný cílený kontrakt 1/1 PASS. Kontroly se
nepřeskakují. Živý GitHub nadále 07109721, nasazení nezačalo, Xcode
nastavení obnovené. Důkaz nejistotu push_state řeší externím ověřením,
původní účtenku nepřepisuje. Opravený checkpoint vyžaduje nové přesné
předání celého čekajícího balíčku registrované Luně.
