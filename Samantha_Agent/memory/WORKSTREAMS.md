# Registr pracovnich proudu

Kanonicky git-safe registr dlouhodobe prace vedene jako `Project`, `Tool`,
`Layer` nebo `Misc`.

Tento registr je v kroku 0 pouze pametova a navigacni vrstva. Neni zdrojem
runtime bran, semaforu, vetvi ani nasazovaci logiky Cockpitu. Existujici zaznamy
v `ACTIVE_PROJECTS.md` zustavaji behem transformace beze zmeny, dokud nebude
jejich migrace samostatne overena.

| ID | Typ | Kanonicky nazev | Rezim | Docasny kompatibilni zdroj | Vlakno | TVBCP | Handoff | Dalsi krok |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `layer-human-adam-development` | `Layer` | Human–Adam / vývojové prostředí | active | `ACTIVE_PROJECTS.md`: App-server rozhrani / novy Adam | Stavajici oddelene vlakno Human–Adam; soukromy identifikator se do Gitu neuklada. | `tvbcp/architektura_komunikace_samantha.txt` | `handoffs/human_adam_layer_workstream_start_2026_07_20.md` | Checkpointnout a pushnout fazi 1.1; potom napojit jednoduchy backend na kanonicka metadata proudu a profilovy manager bez aktivace v UI. |

## Pravidla prvniho zaznamu

- Jde o novou kanonickou identitu existujici oblasti, nikoli o duplicitni
  projekt.
- Typ pracovniho proudu je `Layer`.
- Stary nazev zustava docasne zachovan jen kvuli kompatibilite soucasneho
  Cockpitu.
- Zalozeni zaznamu samo nemeni UI, API, Git workflow, nasazeni ani bezici
  relaci Human–Adam.
