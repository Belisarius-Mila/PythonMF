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

## Otevrene kroky a rizika

- Jeden formalni rozpor Mobile Input zustava k samostatne oprave v P3.
- `aggregate_unverified` je poctivy fallback, ne potvrzeni obsahove spravnosti.
- Historicky zdroj muze zustat ve vysledcich, ale nesmi predbehnout rozpoznany
  kanonicky zdroj stejneho proudu.

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
