"""Narrow private backend binding for Janička R2-Adam documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.communication.janicka_r2_compiler import (
    DocumentInspector,
    JanickaR2DocumentCompiler,
    inspect_registered_document,
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
        document_inspector: DocumentInspector = inspect_registered_document,
    ) -> JanickaR2DocumentCompiler:
        """Return the R2 compiler bound to this backend's guarded store."""

        return JanickaR2DocumentCompiler(
            store=self.document_store(),
            document_inspector=document_inspector,
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
            "JanickaR2DocumentCompiler; vystup je vzdy novy TXT bez prepisu."
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
        )
