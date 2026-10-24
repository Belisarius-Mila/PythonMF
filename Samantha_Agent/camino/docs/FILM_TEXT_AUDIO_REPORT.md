# Texty a komentáře ve střižně — 23. 10. 2026

Tento report popisuje historické vydání. Novější místní přepracování
textu a hlasu přímo u fotografie je v [reportu z 24. 10.](PHOTO_TEXT_COMMENT_REPORT.md).

## Rozsah a stav

Panel Texty a komentáře je pushnutý a nasazený do Cockpitu z `d8d16f1b`.
Registrovaná Luna: účtenka `4b1ed8c23af048f133e00971d0ad1038`, stav completed,
push_state a deployment_state confirmed; plná brána PASS (2 174 testů
v účtence, 380,4 s), kontroly po restartu 5/5. Nový panel byl po nasazení
a při této dokumentační aktualizaci znovu ověřený přes HTTP; runtime odpovídá
účtence. Terminál převzal účtenku, samostatný portálový callback se netvrdí.

Telefon, Camino služba a archiv zůstaly při vydání zachované podle ochranné
kontroly. Nevznikl produkční render ani zápis do existujícího filmového
projektu. Praktický postup je v [návodu střižny](../film/README.md).
Fyzická přejímka nového panelu a samostatné nové render větve jsou otevřené.

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
- Po prvním lokálním kroku byla dokončená plná publikační brána Luny:
  PASS, 2 174 testů v účtence. Opravený frontendový kontrakt také samostatně
  1/1 PASS. Nové testy pro kartu a poslechovou kopii nebyly přidané.
- Syntetický render nových větví karty i poslechové kopie a fyzický proklik
  Safari zůstávají NEOVĚŘENO. Regresní brána ani HTTP nejsou jejich náhradou.

Další krok: na krátkém náhledu fyzicky ověřit titulek, kartu a vlastní hlas,
uložení/reload a souběh zvuku. Nová publikace této dokumentace má vlastní
účtenku a nepředstavuje takovou funkční přejímku.

Redigované čtecí účtenky jsou v data/private/camino_texts_20261023/;
žádný osobní text ani nahrávka nejsou v tomto reportu nebo Gitu.

## Historie první publikační brány a opravy

První Luna úloha a3d0c4730ea1ef7a0e9f3b5f7a2336b7 se zastavila před
pushem: 2174 testů, jediný FAIL v očekávané délce složené stránky. Fixture
neobsahoval rozšíření nového panelu. Po kontrole diffu aktualizovaná délka,
počet řádků a SHA-256; stejný cílený kontrakt 1/1 PASS. Kontroly se
nepřeskakují. V okamžiku této neúspěšné úlohy zůstal živý GitHub na
07109721 a nasazení nezačalo. Původní účtenka se nepřepisovala; nejistotu
push_state vyřešil přímý důkaz z GitHubu. Opravený balíček se dvěma commity
následně vydala Luna pod úspěšnou účtenkou uvedenou v úvodu. Xcode
nastavení bylo po každé uzavřené úloze obnovené se shodným SHA-256.
