from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from agents import function_tool

from .store import DEFAULT_REMINDERS_PATH, save_reminder_draft
from .tools import has_explicit_reminder_save_confirmation


AMOUNT_PATTERN = re.compile(
    r"(?P<amount>\d+(?:[ .,]\d{3})*(?:[,.]\d{1,2})?)\s*(?:kc|kč|czk)",
    re.IGNORECASE,
)
POLICY_PATTERN = re.compile(
    r"(?:pojist(?:ky|ka|ku|eni|ění)|smlouv(?:y|a|u)|faktur(?:y|a|u)|cislo|číslo)"
    r"\s*(?:c\.?|č\.?|cislo|číslo)?\s*(?P<number>\d{6,})",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r"https?://[^\s<>)]+", re.IGNORECASE)


@function_tool
def save_payment_sms_reminder(
    sms_text: str,
    source_sender: str = "SMS",
    source_date: str = "",
    verified_due_date: str = "",
    verified_start_date: str = "",
    review_due_date: str = "",
    priority: str = "high",
    user_confirmed: bool = False,
    confirmation_text: str = "",
) -> str:
    """Save a safe reminder from a payment/insurance SMS after confirmation."""
    return save_payment_sms_reminder_text(
        sms_text=sms_text,
        source_sender=source_sender,
        source_date=source_date,
        verified_due_date=verified_due_date,
        verified_start_date=verified_start_date,
        review_due_date=review_due_date,
        priority=priority,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
    )


def save_payment_sms_reminder_text(
    sms_text: str,
    source_sender: str = "SMS",
    source_date: str = "",
    verified_due_date: str = "",
    verified_start_date: str = "",
    review_due_date: str = "",
    priority: str = "high",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    path: Path = DEFAULT_REMINDERS_PATH,
    today: date | str | None = None,
) -> str:
    """Plain implementation behind the function tool, testable with a temp path."""
    parsed_today = _parse_date_or_today(today)
    source_date = _safe_source_date(source_date=source_date, today=parsed_today)
    review_due_date = review_due_date.strip() or source_date
    verified_due_date = verified_due_date.strip()
    verified_start_date = verified_start_date.strip()

    if verified_due_date:
        _require_iso_date(verified_due_date, "verified_due_date")
    _require_iso_date(review_due_date, "review_due_date")
    if verified_start_date:
        _require_iso_date(verified_start_date, "verified_start_date")

    payment = _parse_payment_sms(sms_text)
    reminder = _build_payment_reminder(
        payment=payment,
        source_sender=source_sender,
        source_date=source_date,
        verified_due_date=verified_due_date,
        verified_start_date=verified_start_date,
        review_due_date=review_due_date,
        priority=priority,
    )

    reminder_id = reminder["id"]
    if not user_confirmed or not has_explicit_reminder_save_confirmation(
        reminder_id=reminder_id,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji druhe samostatne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat id pripominky {reminder_id} a jasny souhlas "
            "s ulozenim pripominky. Bez toho na disk nic nezapisuji."
        )

    try:
        result = save_reminder_draft(reminder, path=path)
    except ValueError as exc:
        return f"Ulozeni platebni pripominky bylo odmitnuto: {exc}"

    if result.created:
        if verified_due_date:
            return (
                f"Ulozeno: {result.reminder_id}. "
                "Byla ulozena bezpecna platebni pripominka s overenou splatnosti. "
                "Plna URL ani token z SMS nebyly ulozeny."
            )
        return (
            f"Ulozeno: {result.reminder_id}. "
            "Nebyla ulozena platba jako hotovy fakt, ale ukol overit splatnost. "
            "Plna URL ani token z SMS nebyly ulozeny."
        )

    return (
        f"Neulozeno: {result.reminder_id}. {result.message} "
        "Na disk nebyla pridana duplicita."
    )


def _parse_payment_sms(sms_text: str) -> dict[str, object]:
    policy_number = _first_group(POLICY_PATTERN, sms_text, "number")
    amount = _first_group(AMOUNT_PATTERN, sms_text, "amount")
    domains = _extract_domains(sms_text)
    return {
        "policy_number": policy_number,
        "amount": _normalize_amount(amount),
        "domains": domains,
    }


def _build_payment_reminder(
    payment: dict[str, object],
    source_sender: str,
    source_date: str,
    verified_due_date: str,
    verified_start_date: str,
    review_due_date: str,
    priority: str,
) -> dict[str, object]:
    policy_number = str(payment.get("policy_number") or "nezname-cislo")
    amount = str(payment.get("amount") or "nezjistena castka")
    domains = list(payment.get("domains") or [])
    domain_slug = _slugify(str(domains[0]["domain"])) if domains else "bez-domeny"
    number_slug = _slugify(policy_number)

    if verified_due_date:
        reminder_id = f"sms-platba-{number_slug}-{verified_due_date}"
        title = _title_with_number("Zaplatit pojistku/fakturu", policy_number)
        notes_parts = [
            "Platebni SMS byla zpracovana jako bezpecna pripominka.",
            f"Castka: {amount}.",
            f"Overena splatnost: {verified_due_date}.",
            "SMS urgence sama o sobe neurcuje splatnost; rozhodujici je faktura, platebni stranka, smlouva nebo pocatek pojisteni.",
        ]
        if verified_start_date:
            notes_parts.append(f"Overeny pocatek noveho pojisteni/sluzby: {verified_start_date}.")
    else:
        reminder_id = f"sms-overit-splatnost-{number_slug}-{review_due_date}"
        title = _title_with_number("Overit splatnost platby", policy_number)
        notes_parts = [
            "Platebni SMS obsahuje vyzvu k uhrade, ale skutecna splatnost nebyla overena.",
            f"Castka ze SMS: {amount}.",
            "Neukladat jako povinnost zaplatit dnes, dokud neni overena faktura, platebni stranka, smlouva nebo pocatek pojisteni.",
        ]

    if domains:
        notes_parts.append(
            "V SMS byl platebni odkaz; ulozena je jen domena, ne plna URL ani token."
        )
    else:
        notes_parts.append("V SMS nebyla ulozena zadna plna URL.")

    return {
        "id": reminder_id,
        "title": title,
        "notes": " ".join(notes_parts),
        "due_date": verified_due_date or review_due_date,
        "priority": _safe_priority(priority),
        "status": "open",
        "source": {
            "type": "sms",
            "uid": f"manual-payment-sms-{source_date}-{domain_slug}-{number_slug}",
            "date": source_date,
            "sender": _safe_sender(source_sender),
        },
        "links": domains,
        "attachments": [],
    }


def _first_group(pattern: re.Pattern[str], text: str, group: str) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    return match.group(group).strip()


def _extract_domains(text: str) -> list[dict[str, object]]:
    counts: dict[str, int] = {}
    for raw_url in URL_PATTERN.findall(text):
        parsed = urlparse(raw_url)
        domain = parsed.netloc.casefold().strip()
        if not domain:
            continue
        counts[domain] = counts.get(domain, 0) + 1
    return [{"domain": domain, "count": count} for domain, count in sorted(counts.items())]


def _normalize_amount(amount: str) -> str:
    if not amount:
        return ""
    normalized = amount.replace(" ", "").replace(",", ".")
    return f"{normalized} Kc"


def _title_with_number(prefix: str, policy_number: str) -> str:
    if policy_number and policy_number != "nezname-cislo":
        return f"{prefix} {policy_number}"
    return prefix


def _safe_priority(priority: str) -> str:
    normalized = priority.casefold().strip()
    if normalized in {"high", "medium", "low"}:
        return normalized
    return "high"


def _safe_sender(source_sender: str) -> str:
    stripped = " ".join(source_sender.split())
    if not stripped:
        return "SMS"
    return URL_PATTERN.sub("[URL redigovano]", stripped)


def _safe_source_date(source_date: str, today: date) -> str:
    stripped = source_date.strip()
    if not stripped:
        return today.isoformat()
    _require_iso_date(stripped, "source_date")
    return stripped


def _parse_date_or_today(value: date | str | None) -> date:
    if value is None:
        return date.today()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _require_iso_date(value: str, field: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} musi byt datum ve formatu YYYY-MM-DD.") from exc


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.casefold())
    return normalized.strip("-") or "nezname"
