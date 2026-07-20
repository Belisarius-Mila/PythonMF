# Registr pracovnich proudu

Kanonicky git-safe registr dlouhodobe prace vedene jako `Project`, `Tool`,
`Layer` nebo `Misc`.

V kroku 0 byl tento registr pouze pametova a navigacni vrstva. Od faze 1.3 maji
zde uvedene proudy odpovidajici validovanou strukturovanou vazbu v neveřejnem
backendovem koordinatoru. Markdown se za behu neparsuje a stale neni zdrojem
API, UI, semaforu, vetvi ani nasazovaci logiky. Existujici zaznamy v
`ACTIVE_PROJECTS.md` zustavaji behem transformace kompatibilnim mostem.

| ID | Typ | Kanonicky nazev | Rezim | Docasny kompatibilni zdroj | Vlakno | TVBCP | Handoff | Dalsi krok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `layer-human-adam-development` | `Layer` | Human–Adam / vývojové prostředí | active | `ACTIVE_PROJECTS.md`: App-server rozhrani / novy Adam | Stavajici oddelene vlakno Human–Adam; soukromy identifikator se do Gitu neuklada. | `tvbcp/architektura_komunikace_samantha.txt` | `handoffs/human_adam_layer_workstream_start_2026_07_20.md` | Po checkpointu faze 1.3 pripravit napojeni existujiciho vyberu na koordinator bez zmeny vzhledu. |
| `project-knowledge-library` | `Project` | Knihovna | active | `ACTIVE_PROJECTS.md`: Znalostni databaze / Knihovna clanku / Knowledge inbox | Stavajici oddelene vlakno Knihovny; soukromy identifikator se do Gitu neuklada. | `tvbcp/knihovna_cockpit.txt` | `handoffs/knowledge_library_article_editing_2026_07_16.md` | Spolu s Human–Adam overit neveřejny vyber a automaticky fast-forward; UI zatim neprepinat. |

## Pravidla registru

- Jde o novou kanonickou identitu existujici oblasti, nikoli o duplicitni
  projekt.
- Typ pracovniho proudu je `Project`, `Tool`, `Layer` nebo `Misc`.
- Stary nazev zustava docasne zachovan jen kvuli kompatibilite soucasneho
  Cockpitu.
- Zalozeni zaznamu samo nemeni UI, API, Git workflow, nasazeni ani bezici
  relaci Human–Adam.
