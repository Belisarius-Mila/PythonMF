# TVBCP: Samantha Agent / RAG

Pracovni proud: `project-samantha-agent-rag`
Typ: `Project`
Rezim: `active`

## Cil a hranice

Cilem je, aby Samantha pri hledani v git-safe Markdown pameti rozlisila
soucasny kanonicky stav, agregovany rozcestnik, beznou referenci a historicky
zdroj. Stary snapshot nesmi ridit dnesni praci jen proto, ze obsahuje vice
shodnych slov.

Do tohoto proudu nepatri private data, automaticke prepisovani historie,
hromadne vytvareni prazdnych handoffu/TVBCP ani embeddings bez praktickeho
dukazu, ze textove hledani nestaci.

## Kanonicka rozhodnuti

- Poradi autority je pro rozpoznany pracovni proud:
  kanonicky handoff/TVBCP, agregat, historicky handoff.
- Chybejici kanonicka dvojice se prizna jako `aggregate_unverified`; system
  nesmi predstirat plne overeny stav.
- Autorita se nesmi globalne prenaset mezi nesouvisejicimi proudy.
- P0 datum commitu pouziva jen jako signal ke kontrole, nikdy jako dukaz
  obsahove pravdy.
- Kanonicke dvojice zustavaji lazy a vznikaji jen pri skutecne potrebe nebo po
  vyslovne dohode; P2 nematerializuje dalsich 23 proudu.
- Embeddings se odkladaji, dokud prakticke testy neprokazi nedostatecnost
  soucasneho textoveho hledani.

## Milniky

- P0: read-only audit 30 proudu, formalnich vazeb a dostupnosti kanonicke pameti.
- P1: autorita zdroju v `search_memory`, cilene testy 21/21 a nasazeni se smoke
  testem 5/5.
- P2: jedna kanonicka dvojice pro Samantha Agent / RAG a aktualizovane odkazy
  z agregatu a pametoveho indexu.
- P3: jediny formalni mode drift opraven; Mobile Input je vsude `paused`.
- P4: read-only prakticka akceptace sedmi proudu a zkracenych nazvu.
- P5: nefiltrovane prvni hledani autority a dva jednoznacne query aliasy.
- P6: obsahovy audit sedmi roadmapovych proudu a narovnani pouze prokazatelne
  zastaralych aktivnich souhrnu.

## Otevrene kroky a rizika

- P3 odstranilo jediny strojove prokazany formalni rozpor; obsahova pravdivost
  dalsich volnych textu tim neni automaticky potvrzena.
- `aggregate_unverified` je poctivy fallback, ne potvrzeni obsahove spravnosti.
- Historicky zdroj muze zustat ve vysledcich, ale nesmi predbehnout rozpoznany
  kanonicky zdroj stejneho proudu.
- Obecny `Cockpit` je skutecne nejednoznacny a nesmi dostat tichy alias.
- Proudy bez materializovane kanonicke dvojice zustavaji
  `aggregate_unverified`; P6 je hromadne nematerializuje.

## Chronologicke zaznamy

### 2026-07-29 22:21 CEST - P2 kanonicka pamet proudu

#### Hotovo

- Samantha Agent / RAG ma po Milove vyslovnem souhlasu vlastni kanonicky
  handoff a TVBCP.
- Soucasny stav P0 a P1 je dohledatelny bez zavislosti na kvetnovem handoffu.

#### Rozhodnuti

- Materializuje se pouze tento aktivni proud; chybejici dokumenty ostatnich
  proudu se hromadne nevytvareji.

#### Dalsi krok

- Opravit jediny prokazany formalni rozpor Mobile Input a zopakovat P0 audit.

#### Navrhovane dalsi kroky

- Potom overit nekolik praktickych dotazu pres Samanthu.
- Obsahovy audit omezit nejdrive na proudy, ktere ovlivnuji soucasnou roadmapu.
- Embeddings pridat jen pri dolozene potrebe.

#### Technicky dukaz

- P0 audit je deterministicky a read-only.
- P1 pred nasazenim prosel 21 cilenymi testy a rychlou statickou branou; bezici
  Cockpit potom prosel smoke testem 5/5.
- P0 audit po P2 hlasi 6 kompletnich kanonickych dvojic, 23 lazy
  nematerializovanych proudu a jeden nezmeneny formalni rozpor.
- Dotaz `Samantha Agent RAG` vraci jako prvni handoff a TVBCP tohoto proudu s
  autoritou `canonical`; agregat je az dalsi zdroj.

### 2026-07-29 22:39 CEST - P3 oprava formalniho rozporu

#### Hotovo

- Rezim Mobile Input je v agregovanem registru opraven z `active` na `paused`,
  shodne s kanonickym katalogem a `WORKSTREAMS.md`.
- Ostatni text, priorita, odkazy a dalsi krok Mobile Input zustaly beze zmeny.

#### Rozhodnuti

- P3 opravuje pouze strojove prokazany rozpor a nerozsiruje se na obsahove
  prepisovani dalsich projektu.

#### Dalsi krok

- P4 ma read-only overit prakticke dotazy pro Cockpit, Human-Adam, R2-Adam,
  Rodinny kalendar, Dokumenty, E-mail a Automaticke ukoly.

#### Navrhovane dalsi kroky

- U kazdeho dotazu sledovat vybranou autoritu a pripadny `source_type`.
- Otestovat plny i zkraceny nazev proudu a pripadne navrhnout jen jednoznacne
  katalogove aliasy.
- Opravovat jen prokazany drift, ne domnenky.
- Embeddings pridat jen pri dolozene nedostatecnosti textoveho hledani.

#### Technicky dukaz

- P0 audit pred P3 dokazoval prave jeden `mode_mismatch` pro
  `project-mobile-input`; po zmene hlasi nula formalnich rozporu a rezim
  Mobile Input `paused`.
- Cilenych 21 testu pameti proslo. Exploracni dotaz se zkracenym nazvem
  odkryl pouze kandidat k read-only provereni v P4, nikoli dalsi datovy rozpor.

### 2026-07-30 06:46 CEST - P4 akceptace a P5 volba autority

#### Hotovo

- P4 read-only oddelilo zdravy ranking textoveho RAG od chybneho rozhodovani
  agenta: Samantha pro aktualni stav volila `source_type=projects` a tim
  vyrazovala kanonicke handoffy a TVBCP.
- P5a zavedlo prvni hledani bez `source_type`, vyhodnoceni uvedene autority a
  zastaveni po relevantnim `canonical` vysledku.
- P5b zavedlo samostatne query aliasy `R2 Adam` a `Kalendář`; runtime binding
  aliasy zustaly beze zmeny.

#### Rozhodnuti

- `source_type` je explicitni zuzeni nebo druhy krok jen tehdy, kdyz prvni
  vysledky neobsahuji relevantni kanonicky zdroj.
- `R2 Adam` a `Kalendář` jsou v katalogu jednoznacne. Samotny `Cockpit` neni a
  zustava bez aliasu.
- Ranking ani embeddings se v P5 nemeni.

#### Dalsi krok

- Potvrzene nasadit P5 do Cockpitu a provest smoke test.

#### Navrhovane dalsi kroky

- Po nasazeni zvolit maly obsahovy audit nejdulezitejsich aktivnich proudu.
- Embeddings otevirat jen pri novem praktickem dukazu, ze textove hledani
  nestaci.

#### Technicky dukaz

- P5a prosla 24 cilenymi a 1238 uplnymi testy. Finalni live dotazy R2-Adam a
  Rodinny kalendar provedly jedine nefiltrovane volani a vratily `canonical`.
- P5b prosla 47 cilenymi a 1240 uplnymi testy. Live `R2 Adam` a `Kalendář`
  provedly jedine nefiltrovane volani a vratily spravny kanonicky handoff.
- Nebyl cten private obsah a nebyl proveden zapis do private uloziste.

### 2026-07-30 07:25 CEST - P6 obsahove narovnani aktivni pameti

#### Hotovo

- P5 je nasazena na aktualnim Cockpitu a opakovany smoke test prosel 5/5.
- P6a porovnalo sedm roadmapovych proudu se zivymi dukazy a odlisilo formalni
  konzistenci od obsahove pravdivosti.
- P6b opravilo jen aktivni souhrny a dalsi kroky, ktere byly prokazatelne
  prekryte novejsim stavem.

#### Rozhodnuti

- Historicke bloky se neprepisuji ani nemazou.
- Chybejici kanonicke dvojice se kvuli P6 hromadne nezakladaji.
- Neovereny private provozni stav, zejmena zivy rezim Rodinneho kalendare, se
  nesmi domyslet.

#### Dalsi krok

- Prejit k jednomu uplnemu overeni toku e-mail -> private vault -> R2 TXT.

#### Navrhovane dalsi kroky

- Po praktickem toku provest provozni prejimku R2-Adama z pohledu Jany.
- Embeddings otevrit jen pri novem dukazu, ze textove hledani nestaci.

#### Technicky dukaz

- P0 audit nadale hlasi nula formalnich rozporu.
- P5 ranking vraci pro R2-Adam a Kalendar kanonicke zdroje jako prvni a u
  nematerializovanych proudu priznava slabsi autoritu.
- Private obsah nebyl pri P6a ani P6b cten nebo zapisovan.
