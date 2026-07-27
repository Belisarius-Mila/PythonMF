from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from datetime import date

from agents import function_tool

from .config import EmailConfigError
from .icloud_provider import EmailProviderError, ICloudReadOnlyEmailProvider
from .models import EmailTextSearchHit
from .redaction import redact_email_addresses
from .seznam_provider import SeznamEmailProviderError, SeznamReadOnlyEmailProvider


DENIAL_PHRASES = {
    "open_urls": (
        "neotevirat odkazy",
        "neotevirat url",
        "neotevírat odkazy",
        "neotevírat url",
        "neotevirej odkazy",
        "neotevírej odkazy",
    ),
    "download_attachments": (
        "nestahovat prilohy",
        "nestahovat přílohy",
        "nestahuj prilohy",
        "nestahuj přílohy",
    ),
    "send_email": (
        "nic neodesilat",
        "nic neodesílat",
        "neodesilat",
        "neodesílat",
    ),
    "delete_email": ("nemazat", "nemaz", "nemaž"),
    "move_email": ("nepresouvat", "nepřesouvat", "nepresouvej", "nepřesouvej"),
    "mark_read": (
        "neoznacovat jako prectene",
        "neoznačovat jako přečtené",
        "neoznacuj jako prectene",
        "neoznačuj jako přečtené",
    ),
}


@function_tool
def search_email_text_year(
    terms: list[str],
    year: int = 2026,
    limit: int = 50,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Search iCloud Mail message text for terms in one year; returns headers only."""
    return search_email_text_year_text(
        terms=terms,
        year=year,
        limit=limit,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


@function_tool
def search_seznam_email_text_year(
    terms: list[str],
    year: int = 2026,
    limit: int = 50,
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Search Seznam Mail message text for terms in one year; returns headers only."""
    return search_seznam_email_text_year_text(
        terms=terms,
        year=year,
        limit=limit,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


def search_email_text_year_text(
    terms: list[str] | tuple[str, ...],
    year: int = 2026,
    limit: int = 50,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    provider_factory: Callable[[], object] = ICloudReadOnlyEmailProvider,
) -> str:
    return _search_email_text_year_text(
        terms=terms,
        year=year,
        limit=limit,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        provider_factory=provider_factory,
        provider_error=EmailProviderError,
        provider_label="iCloud",
    )


def search_seznam_email_text_year_text(
    terms: list[str] | tuple[str, ...],
    year: int = 2026,
    limit: int = 50,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    provider_factory: Callable[[], object] = SeznamReadOnlyEmailProvider,
) -> str:
    return _search_email_text_year_text(
        terms=terms,
        year=year,
        limit=limit,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        provider_factory=provider_factory,
        provider_error=SeznamEmailProviderError,
        provider_label="Seznam",
        required_confirmation_provider="Seznam",
    )


def _search_email_text_year_text(
    *,
    terms: list[str] | tuple[str, ...],
    year: int,
    limit: int,
    user_confirmed: bool,
    confirmation_text: str,
    provider_factory: Callable[[], object],
    provider_error: type[Exception],
    provider_label: str,
    required_confirmation_provider: str = "",
) -> str:
    safe_year = _validate_year(year)
    safe_terms = _normalize_terms(terms)
    safe_limit = min(max(1, limit), 200)

    if not user_confirmed or not has_explicit_text_search_confirmation(
        terms=safe_terms,
        year=safe_year,
        confirmation_text=confirmation_text,
        required_provider=required_confirmation_provider,
    ):
        terms_text = ", ".join(safe_terms)
        return (
            "Nejdrive potrebuji jasne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat rok {safe_year}, hledane vyrazy ({terms_text}), "
            f"{'provider ' + required_confirmation_provider + ', ' if required_confirmation_provider else ''}"
            "souhlas s read-only hledanim v textech/tělech e-mailu a zakazy: "
            "neotevirat odkazy, nestahovat prilohy, nic neodesilat, nemazat, "
            "nepresouvat a neoznacovat jako prectene. Bez toho provider nevolam."
        )

    try:
        provider = provider_factory()
        search_text_headers = getattr(provider, "search_text_headers")
        hits = search_text_headers(
            terms=safe_terms,
            since=date(safe_year, 1, 1),
            before=date(safe_year + 1, 1, 1),
            limit=safe_limit,
        )
    except EmailConfigError:
        return (
            f"Chybi lokalni konfigurace pro {provider_label} Mail. "
            "Zkontroluj lokalni .env; neposilej heslo do chatu."
        )
    except provider_error as exc:
        return f"Fulltextove vyhledani v {provider_label} Mailu selhalo: {exc}"

    return format_email_text_search_result(
        hits=hits,
        terms=safe_terms,
        year=safe_year,
        provider_label=provider_label,
    )


def has_explicit_text_search_confirmation(
    terms: list[str] | tuple[str, ...],
    year: int,
    confirmation_text: str,
    required_provider: str = "",
) -> bool:
    normalized = _strip_accents(confirmation_text.casefold())
    provider_confirmed = (
        not required_provider
        or _strip_accents(required_provider.casefold()) in normalized
    )
    return (
        provider_confirmed
        and
        str(year) in normalized
        and any(word in normalized for word in ("potvrzuji", "souhlasim", "ano"))
        and any(word in normalized for word in ("read-only", "readonly", "jen cteni", "ctenim"))
        and any(word in normalized for word in ("text", "textech", "telech", "telo", "tělech", "tělo"))
        and all(_strip_accents(term.casefold()) in normalized for term in terms)
        and all(
            any(_strip_accents(phrase.casefold()) in normalized for phrase in phrases)
            for phrases in DENIAL_PHRASES.values()
        )
    )


def format_email_text_search_result(
    hits: list[EmailTextSearchHit],
    terms: list[str] | tuple[str, ...],
    year: int,
    provider_label: str = "iCloud",
) -> str:
    lines = [
        f"Fulltext {provider_label} e-mailu za rok {year}",
        f"Hledane vyrazy: {', '.join(terms)}",
        "",
    ]
    if not hits:
        lines.append("Nenalezeny zadne odpovidajici e-maily.")
    else:
        lines.append("Nalezene e-maily:")
        for index, hit in enumerate(hits, start=1):
            header = hit.header
            subject = header.subject or "(bez predmetu)"
            lines.extend(
                [
                    f"{index}. UID: {_safe_text(header.internal_id)}",
                    f"   Datum: {_safe_text(header.date)}",
                    f"   Od: {_safe_text(redact_email_addresses(header.sender))}",
                    f"   Predmet: {_safe_text(subject)}",
                    f"   Nalezene vyrazy: {', '.join(hit.matched_terms)}",
                ]
            )

    lines.extend(
        [
            "",
            "Bezpecnost: hledani probehlo read-only; vystup obsahuje jen UID a "
            "hlavicky. Tela e-mailu, plne URL ani prilohy nebyly vypsany, odkazy "
            "nebyly otevreny, nic nebylo odeslano, smazano, presunuto ani oznaceno "
            "jako prectene.",
        ]
    )
    return "\n".join(lines)


def _validate_year(year: int) -> int:
    safe_year = int(year)
    if safe_year < 2000 or safe_year > 2100:
        raise ValueError("Rok je mimo povoleny rozsah.")
    return safe_year


def _normalize_terms(terms: list[str] | tuple[str, ...]) -> list[str]:
    safe_terms: list[str] = []
    seen: set[str] = set()
    for term in terms:
        normalized = " ".join(str(term).split())
        folded = normalized.casefold()
        if not normalized or folded in seen:
            continue
        if len(normalized) > 80:
            raise ValueError("Hledany vyraz je prilis dlouhy.")
        safe_terms.append(normalized)
        seen.add(folded)
    if not safe_terms:
        raise ValueError("Chybi hledany vyraz.")
    if len(safe_terms) > 10:
        raise ValueError("Prilis mnoho hledanych vyrazu.")
    return safe_terms


def _strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _safe_text(value: object) -> str:
    text = str(value)
    text = re.sub(r"https?://\S+", "[url skryto]", text, flags=re.IGNORECASE)
    return redact_email_addresses(text)
