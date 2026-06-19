Nazev: ChatGPT export / Knowledge inbox import checkpoint
Priorita: 2
Stav: rozpracovane
Pripomenout pri startu: ano
Datum: 2026-06-19

Co se resilo:
Mila ma lokalni export vsech ChatGPT chatu za posledni roky. Export je soukromy
podklad a zpracovava se pres `data/private/knowledge_inbox/`. Cilem neni opisovat
chaty do pameti, ale postupne z nich vytahnout bezpecne oblasti pro knihovnu,
recepty, lekarske rady, projekty, tooly a dalsi znalostni karty.

Co je hotove:
- Export byl nalezen v `Downloads` a precten read-only.
- Vznikl samostatny soukromy index:
  `data/private/knowledge_inbox/processed/chatgpt_export_index_2026_06_17.json`
- Index ma 826 konverzaci.
- Index neuklada nazvy chatu, texty zprav, uryvky ani plne obsahy.
- Rizikovy souhrn indexu:
  - low: 641
  - medium: 167
  - high: 18
- Rizikove flagy v indexu:
  - medical: 123
  - family_or_children: 121
  - email_or_outbound: 89
  - private_documents: 55
  - financial_or_legal: 21
  - secrets_or_access: 18
- Pro oblast `recepty_vareni` vznikl read-only rozbor:
  `data/private/knowledge_inbox/processed/chatgpt_export_recepty_vareni_summary_2026_06_19.md`
- Receptovy rozbor nasel 69 kandidatu:
  - `recipe_card_candidate`: 2
  - `cooking_note_candidate`: 40
  - `weak_or_false_positive_review`: 25
  - `manual_review_sensitive`: 2
- Dva prisne receptove kandidaty byly rucne porovnane s knihovnou: jeden byl importovan, jeden byl vynechan jako nereceptovy obsah.
- 25 slabych kandidatu bylo rucne procteno a zhodnoceno:
  `data/private/knowledge_inbox/processed/chatgpt_export_recepty_vareni_weak_review_2026_06_19.json`
- Ze slabych kandidatu bylo importovano 16 receptu a 9 bylo vynechano.
- 40 `cooking_note_candidate` bylo nasledne zpracovano do soukromeho JSON review:
  `data/private/knowledge_inbox/processed/chatgpt_export_recepty_vareni_cooking_notes_review_2026_06_19.json`
- Markdown report z tohoto review byl na Miluv pokyn smazan jako irelevantni:
  `data/private/knowledge_inbox/processed/chatgpt_export_recepty_vareni_cooking_notes_review_2026_06_19.md`
- Z techto 40 kandidatu byly do knihovny ponechany 3 nove recepty:
  - `Řízek z vepřového jazyka`
  - `Záhorský závitek`
  - `Holandský řízek po česku`
- 3 dalsi polozky byly nejdrive importovany, ale hned presunuty do soukromeho kose jako nově vzniklé duplicity existujicich receptu.
- Zbylych 34 polozek je v soukromem JSON auditu jako neimportovane nebo citlive/smesene:
  - `skip_cooking_note`: 18
  - `manual_review_sensitive`: 14
  - `manual_review_possible_recipe`: 2
- Puvodni 2 `manual_review_sensitive` kandidaty byly zpracovane do soukromeho review:
  `data/private/knowledge_inbox/processed/chatgpt_export_recepty_vareni_sensitive_review_2026_06_19.md`
- Z techto 2 citlivych kandidatu byl importovan 1 izolovany samostatny recept:
  - `Zákusek s pečenými jablky a tvarohovým krémem`
- Druhy citlivy kandidat nebyl recept a nebyl importovan.
- Celkem bylo z ChatGPT exportu 2026-06-19 do `Knihovna -> Recepty` pridano a ponechano 21 receptovych polozek.
- Knihovna receptu ma aktualne 44 receptovych polozek.
- Pro bezpecny uklid knihovny je hotove potvrzovane `Vyřadit z knihovny`, ktere polozku netvrde nemaze, ale presouva ji do soukromeho kose.

Co neni hotove:
- V ramci aktualni sady `recepty_vareni_candidates` uz nezbyva nezpracovany receptovy kandidat.
- JSON z cooking-note review eviduje 2 mozne recepty a 14 citlive oznacenych polozek,
  ale markdown souhrn pro rucni cteni byl smazan jako irelevantni a tyto polozky se
  nepovazuji za otevrene receptove kandidaty bez noveho Milova pokynu.
- Neni hotove zpracovani ostatnich oblasti ChatGPT exportu.
- Neni hotovy obecny workflow pro prevod kandidatu do dlouhodobych knowledge karet.
- Neni hotovy UI/report pro systematicky review kandidatu mimo recepty.
- Neni hotovy restore/undo pohled pro soukromy kos knihovny.

Dalsi krok:
Receptovou cast aktualni kandidatni sady povazovat za uzavrenou. Pokud se ma hledat
dalsi receptovy obsah, udelat az novy samostatny relaxed scan celeho ChatGPT exportu
s jinymi pravidly a opet jen read-only preview pred importem.

Navrhovane dalsi kroky:
- Okamzity: zadny dalsi receptovy kandidat z aktualni sady nezbyva.
- Volitelne: spustit novy sirsi scan celeho exportu pro prehlednute recepty, ale az po samostatnem pokynu.
- Navazujici: samostatne oblasti po receptech:
  - lekarske rady a domaci lecba: pouze jako rizikove/overovaci kandidaty, ne jako lekarske pokyny,
  - projekty a tooly: prevadet do memory jen shrnute a po rucnim vyberu,
  - rodinne/citlive/dokumentove veci: zustavaji v private datech, do gitu jen anonymizovane metadata.

Zmenene nebo relevantni soubory:
- `data/private/knowledge_inbox/processed/chatgpt_export_index_2026_06_17.json`
- `data/private/knowledge_inbox/processed/chatgpt_export_recepty_vareni_candidates_2026_06_19.json`
- `data/private/knowledge_inbox/processed/chatgpt_export_recepty_vareni_summary_2026_06_19.md`
- `data/private/knowledge_inbox/processed/chatgpt_export_recepty_vareni_weak_review_2026_06_19.json`
- `data/private/knowledge_inbox/processed/chatgpt_export_recepty_vareni_cooking_notes_review_2026_06_19.json`
- `data/private/knowledge_inbox/processed/chatgpt_export_recepty_vareni_sensitive_review_2026_06_19.md`
- `data/private/knowledge_inbox/processed/chatgpt_export_recepty_vareni_sensitive_review_2026_06_19.json`
- `data/private/article_archive/`
- `memory/handoffs/knowledge_database_library_safe_delete_2026_06_19.md`

Bezpecnost / neukladat:
- Do gitu nepatri ChatGPT export, texty konverzaci, nazvy chatu, uryvky, plne recepty
  z private archivu ani citlive osobni/dokumentove/lekarske obsahy.
- Handoff smi obsahovat jen pocetni souhrny, ID workflow, obecne kategorie a cesty.
- High-risk konverzace s `secrets_or_access` nikdy neimportovat bez samostatneho rucniho
  rozhodnuti a bez opisovani tajemstvi.
- Lekarske vystupy brat jako historicke orientacni poznamky, ne jako aktualni zdravotni radu.
