from __future__ import annotations

from agents import function_tool

from .image_resize import format_apply_image_resize, format_preview_image_resize


@function_tool
def preview_zmenseni_obrazku(
    path: str = "",
    project: str = "",
    target_kb: int = 0,
    recursive: bool = False,
) -> str:
    """Read-only preview for shrinking image files by target file size in kB."""
    return format_preview_image_resize(
        path=path,
        project=project,
        target_kb=target_kb,
        recursive=recursive,
    )


@function_tool
def apply_zmenseni_obrazku(
    path: str = "",
    project: str = "",
    target_kb: int = 0,
    recursive: bool = False,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Shrink image files after explicit confirmation, keeping backups."""
    return format_apply_image_resize(
        path=path,
        project=project,
        target_kb=target_kb,
        recursive=recursive,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )
