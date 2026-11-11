from __future__ import annotations

from pathlib import Path


FRONTEND_ROOT = Path(__file__).resolve().with_name("frontend")
CSS_MARKER = "{{SAMANTHA_CSS}}"
JAVASCRIPT_MARKER = "{{SAMANTHA_JAVASCRIPT}}"
FRONTEND_PAGE_IDS = (
    "calendar_task",
    "calendar_overview",
    "interior",
    "email_agent",
    "email_archive",
    "email_processing",
    "cockpit",
)
FRONTEND_JAVASCRIPT_MODULES = {
    "email_agent": ("../shared/calendar_delete.js", "calendar_draft.js", "followup_time.js", "followups.js"),
    "calendar_task": ("../shared/calendar_delete.js",),
    "calendar_overview": ("../shared/calendar_delete.js", "../shared/calendar_actions.js",),
    "cockpit": ("../shared/calendar_delete.js", "../shared/calendar_actions.js", "calendar_agenda.js", "navigation.js", "health_recovery_autosave.js", "codex_sessions.js", "library_photos.js", "document_review.js", "document_search.js", "film_feedback.js", "film_editor.js", "film_library.js", "science_news.js"),
}


class CockpitFrontendError(RuntimeError):
    """Raised when a required Cockpit frontend asset is missing or malformed."""


def load_frontend_page(
    page_id: str,
    *,
    frontend_root: Path = FRONTEND_ROOT,
) -> str:
    clean_id = str(page_id or "").strip()
    if clean_id not in FRONTEND_PAGE_IDS:
        raise CockpitFrontendError("Neznámá frontendová plocha Cockpitu.")

    page_root = frontend_root / clean_id
    template = _read_asset(page_root / "page.html")
    styles = _read_asset(page_root / "styles.css")
    javascript_assets = [
        _read_asset(page_root / module_name)
        for module_name in FRONTEND_JAVASCRIPT_MODULES.get(clean_id, ())
    ]
    javascript_assets.append(_read_asset(page_root / "app.js"))
    javascript = "\n".join(javascript_assets)

    if template.count(CSS_MARKER) != 1 or template.count(JAVASCRIPT_MARKER) != 1:
        raise CockpitFrontendError(
            f"Frontendová šablona {clean_id} nemá právě jeden CSS a JavaScript marker."
        )
    if CSS_MARKER in styles or JAVASCRIPT_MARKER in styles:
        raise CockpitFrontendError(f"CSS asset {clean_id} obsahuje zakázaný marker.")
    if CSS_MARKER in javascript or JAVASCRIPT_MARKER in javascript:
        raise CockpitFrontendError(f"JavaScript asset {clean_id} obsahuje zakázaný marker.")

    return template.replace(CSS_MARKER, styles).replace(
        JAVASCRIPT_MARKER,
        javascript,
    )


def _read_asset(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CockpitFrontendError(
            f"Frontendový asset Cockpitu nelze načíst: {path.name}."
        ) from exc


INTERIOR_HTML = load_frontend_page("interior")
CALENDAR_OVERVIEW_HTML = load_frontend_page("calendar_overview")
CALENDAR_TASK_HTML = load_frontend_page("calendar_task")
EMAIL_ARCHIVE_HTML = load_frontend_page("email_archive")
EMAIL_AGENT_HTML = load_frontend_page("email_agent")
EMAIL_PROCESSING_HTML = load_frontend_page("email_processing")
COCKPIT_HTML = load_frontend_page("cockpit")
