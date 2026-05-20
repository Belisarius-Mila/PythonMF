from __future__ import annotations

from agents import function_tool

from .photo_import import (
    format_apply_lekarna_photo_import_manifest,
    format_prepare_lekarna_photo_import_manifest,
    format_validate_lekarna_photo_sources,
)
from .service import (
    format_domaci_lekarna_audit,
    format_domaci_lek_retire_preview,
    format_domaci_leky_search,
    format_retire_domaci_lek,
)


@function_tool
def search_domaci_leky(query: str, limit: int = 10) -> str:
    """Read-only search in local home medicine inventory by symptom or category."""
    return format_domaci_leky_search(query=query, limit=limit)


@function_tool
def audit_domaci_lekarna() -> str:
    """Read-only audit checklist for local home medicine inventory."""
    return format_domaci_lekarna_audit()


@function_tool
def preview_vyrazeni_leku(query: str, reason: str = "") -> str:
    """Read-only preview for retiring one medicine inventory item."""
    return format_domaci_lek_retire_preview(query=query, reason=reason)


@function_tool
def apply_vyrazeni_leku(
    query: str,
    reason: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Soft-retire one medicine inventory item after explicit confirmation."""
    return format_retire_domaci_lek(
        query=query,
        reason=reason,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


@function_tool
def prepare_lekarna_photo_import() -> str:
    """Prepare a CSV manifest template for newly added medicine-box photos."""
    return format_prepare_lekarna_photo_import_manifest()


@function_tool
def apply_lekarna_photo_import(
    manifest_path: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Apply a reviewed medicine photo import manifest after explicit confirmation."""
    return format_apply_lekarna_photo_import_manifest(
        manifest_path=manifest_path,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


@function_tool
def validate_lekarna_photo_sources() -> str:
    """Validate that medicine photo source paths referenced from CSV exist."""
    return format_validate_lekarna_photo_sources()
