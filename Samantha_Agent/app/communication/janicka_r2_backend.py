"""Narrow private backend binding for Janička R2-Adam documents."""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from pathlib import Path

from app.communication.janicka_r2_compiler import (
    DocumentInspector,
    JanickaR2DocumentCompiler,
    inspect_registered_document,
)
from app.communication.janicka_r2_document_selection import (
    DocumentPageSearchProvider,
    DocumentSearchProvider,
    JanickaR2DocumentSelectionFlow,
    search_registered_document_page,
    search_registered_documents,
)
from app.communication.janicka_r2_documents import (
    R2_DOCUMENTS_RELATIVE_ROOT,
    JanickaR2DocumentStore,
)


JANICKA_R2_WORKSTREAM_ID = "project-r2-adam-janicka"


@dataclass(frozen=True)
class JanickaR2Backend:
    """Bind one canonical private root to the guarded R2 document store."""

    canonical_private_root: Path
    document_root: Path

    @classmethod
    def bind(
        cls,
        *,
        canonical_private_root: Path,
        document_root: Path,
    ) -> "JanickaR2Backend":
        private_root = Path(canonical_private_root).resolve()
        owned_root = Path(document_root).resolve()
        expected_root = (private_root / R2_DOCUMENTS_RELATIVE_ROOT).resolve()
        if owned_root != expected_root or private_root not in owned_root.parents:
            raise ValueError(
                "Dokumentový backend R2-Adama míří mimo svůj vlastněný private kořen."
            )
        return cls(
            canonical_private_root=private_root,
            document_root=owned_root,
        )

    def document_store(self) -> JanickaR2DocumentStore:
        """Return the guarded store without creating or reading private documents."""

        return JanickaR2DocumentStore(
            canonical_private_root=self.canonical_private_root,
        )

    def document_compiler(
        self,
        *,
        document_inspector: DocumentInspector | None = None,
    ) -> JanickaR2DocumentCompiler:
        """Return the R2 compiler bound to this backend's guarded store."""

        return JanickaR2DocumentCompiler(
            store=self.document_store(),
            document_inspector=(
                document_inspector
                or partial(
                    inspect_registered_document,
                    vault_dir=self.canonical_private_root / "documents",
                )
            ),
        )

    def document_selection_flow(
        self,
        *,
        document_search: DocumentSearchProvider | None = None,
        document_page_search: DocumentPageSearchProvider | None = None,
        document_inspector: DocumentInspector | None = None,
    ) -> JanickaR2DocumentSelectionFlow:
        """Return the two-step read-only search and human-selection flow."""

        return JanickaR2DocumentSelectionFlow(
            compiler=self.document_compiler(
                document_inspector=document_inspector,
            ),
            document_search=(
                document_search
                or partial(
                    search_registered_documents,
                    vault_dir=self.canonical_private_root / "documents",
                )
            ),
            document_page_search=(
                document_page_search
                or partial(
                    search_registered_document_page,
                    vault_dir=self.canonical_private_root / "documents",
                )
            ),
        )

    def developer_instructions(self) -> str:
        return (
            " R2-Adam ma jedinou zapisovatelnou vyjimku pro vlastni TXT dokumenty: "
            f"{self.document_root}. Vsechna ostatni zdrojova data pod "
            f"{self.canonical_private_root} zustavaji read-only. Dokumenty spravuj "
            "vyhradne pres app.communication.janicka_r2_documents."
            "JanickaR2DocumentStore; nepouzivej obecny filesystemovy zapis ani shellovy "
            "bypass. Bez dalsiho potvrzeni lze jeden dokument vytvorit, precist, vypsat "
            "nebo zmenit. Odebrani je pouze obnovitelny move_to_trash a vyzaduje presnou "
            "potvrzovaci vetu konkretniho dokumentu. Nikdy trvale nemaz obsah kose, "
            "nevypisuj soukromy fulltext do logu a nepouzivej sit. Kompilace z "
            "dokumentoveho vaultu smi pouzit jen jeden explicitni document_id pres "
            "registrovanou read-only schopnost inspect_document_text a "
            "JanickaR2DocumentCompiler; vystup je vzdy novy TXT bez prepisu. Pred "
            "kompilaci pouzij registrovanou read-only schopnost "
            "search_private_documents pres JanickaR2DocumentSelectionFlow, ukaz jen "
            "redigovane volby a pockej na lidsky vybranou selection_ref; ani jedinou "
            "shodu nevybirej automaticky. Pro prehled z vice dokumentu nejdrive ukaz "
            "redigovane volby a pockej na vyslovny lidsky vyber dvou az peti "
            "selection_ref. Pak pres prepare_selected_sources nacti pouze tyto zdroje, "
            "nevypisuj jejich text do chatu a sestav pozadovany strukturovany prehled. "
            "Novy TXT vytvor vyhradne pres compile_selected_overview se stejnym dotazem, "
            "volbami a source_set_ref; zmena zdroju musi vynutit novy vyber. Kdyz "
            "zadani pozaduje vsechny shody, pouzij search_complete_document_set. Ukaz "
            "pocet a vsechny redigovane nazvy, pockej na vyslovne potvrzeni celeho "
            "result_set_ref a nikdy nevydavej oriznuty vysledek za uplny. Pro pouhy "
            "soupis nazvu pouzij compile_complete_title_list bez fulltextove inspekce. "
            "Pro obsahovy prehled nacti potvrzenou sadu pres "
            "prepare_complete_source_batch po davkach a zapis ji jen pres "
            "compile_complete_overview se vsemi batch_refs."
        )

    def development_control_lines(self) -> tuple[str, ...]:
        return (
            "r2_document_access=manage_owned_txt_documents",
            f"r2_document_root={self.document_root}",
            "r2_document_confirmation_required=delete",
            "rule=The only private write exception is r2_document_root through "
            "JanickaR2DocumentStore. All other source user data under "
            "canonical_private_root remains read-only.",
            "rule=Create, read, list and replace are allowed only for one requested TXT "
            "document. Removal must use confirmed recoverable move_to_trash; never "
            "permanently delete private documents.",
            "rule=Compilation may use one explicit document_id through the registered "
            "read-only inspect_document_text capability and JanickaR2DocumentCompiler. "
            "The source remains unchanged and the TXT output is create-only.",
            "rule=Before compilation, use the registered read-only "
            "search_private_documents capability through JanickaR2DocumentSelectionFlow. "
            "Show only redacted candidates and require one human-selected selection_ref; "
            "never auto-select even a single match.",
            "rule=A multi-source overview may use two to five explicit human-selected "
            "selection_refs through JanickaR2DocumentSelectionFlow. Prepare only the "
            "confirmed sources, never paste their text or the generated TXT into chat, "
            "and create the output only through compile_selected_overview with the "
            "matching source_set_ref. Source changes require a new human selection.",
            "rule=A request for all matches must use search_complete_document_set and "
            "human confirmation of the displayed complete result_set_ref. Never present "
            "a truncated search as complete. A title-only list must use "
            "compile_complete_title_list without fulltext inspection. A content overview "
            "must prepare every confirmed five-source batch and pass every batch_ref to "
            "compile_complete_overview. Overly broad searches must fail closed.",
        )
