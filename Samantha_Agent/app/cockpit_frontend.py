from __future__ import annotations

from pathlib import Path


FRONTEND_ROOT = Path(__file__).resolve().with_name("frontend")
CSS_MARKER = "{{SAMANTHA_CSS}}"
JAVASCRIPT_MARKER = "{{SAMANTHA_JAVASCRIPT}}"
FRONTEND_PAGE_IDS = (
    "email_archive",
    "email_processing",
    "cockpit",
)


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
    javascript = _read_asset(page_root / "app.js")

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


EMAIL_ARCHIVE_HTML = load_frontend_page("email_archive")
EMAIL_PROCESSING_HTML = load_frontend_page("email_processing")
COCKPIT_HTML = load_frontend_page("cockpit")
