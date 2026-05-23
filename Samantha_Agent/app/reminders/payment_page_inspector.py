from __future__ import annotations

import html
import json
import re
import ssl
import subprocess
from dataclasses import dataclass
from datetime import date
from typing import Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from agents import function_tool

from .payment_sms_tools import AMOUNT_PATTERN, POLICY_PATTERN


MAX_PAGE_BYTES = 300_000
DEFAULT_TIMEOUT_SECONDS = 12

DATE_VALUE_PATTERN = re.compile(
    r"\b(?P<date>"
    r"\d{4}-\d{1,2}-\d{1,2}"
    r"|\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
    r")\b"
)
DUE_CONTEXT_PATTERN = re.compile(
    r"(?P<context>"
    r"(?:splatnost|splatne|splatné|uhrad(?:it|te)?\s+do|zaplat(?:it|te)?\s+do|"
    r"platba\s+do|do\s+dne|nejpozdeji|nejpozději)"
    r"[^.\n\r]{0,80}?"
    r"(?P<date>\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{2,4})"
    r")",
    re.IGNORECASE,
)
START_CONTEXT_PATTERN = re.compile(
    r"(?P<context>"
    r"(?:(?:pocatek|počátek)\s+(?:pojisteni|pojištění|smlouvy)|"
    r"(?:pojisteni|pojištění|smlouva|sluzba|služba)\s+(?:plati|platí)\s+od|"
    r"(?:platnost|ucinnost|účinnost)\s+od)"
    r"[^.\n\r]{0,80}?"
    r"(?P<date>\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[./-]\d{1,2}[./-]\d{2,4})"
    r")",
    re.IGNORECASE,
)

CONFIRMATION_WORDS = (
    "potvrzuji",
    "souhlasim",
    "souhlasím",
    "ano",
    "prozkoumej",
    "zkontroluj",
    "over",
    "ověř",
    "overit",
    "ověřit",
    "precti",
    "přečti",
)
INSPECTION_WORDS = (
    "platebni",
    "platební",
    "platba",
    "faktura",
    "pojistka",
    "pojisteni",
    "pojištění",
    "splatnost",
    "odkaz",
    "stranka",
    "stránka",
    "url",
)


@dataclass(frozen=True)
class PaymentPageInspection:
    domain: str
    source_label: str
    due_date: str
    due_date_raw: str
    due_confidence: str
    start_date: str
    start_date_raw: str
    amount: str
    policy_number: str
    fetched_chars: int
    bank_transfer_due_date: str = ""
    payment_gateway_due_date: str = ""
    provider_name: str = ""
    product_name: str = ""
    payment_gateway_domain: str = ""


@function_tool
def inspect_payment_page_for_reminder(
    payment_url: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    max_bytes: int = MAX_PAGE_BYTES,
) -> str:
    """Read-only inspect a payment page and extract safe reminder fields."""
    return inspect_payment_page_for_reminder_text(
        payment_url=payment_url,
        user_confirmed=user_confirmed,
        confirmation_text=confirmation_text,
        max_bytes=max_bytes,
    )


def inspect_payment_page_for_reminder_text(
    payment_url: str,
    user_confirmed: bool = False,
    confirmation_text: str = "",
    max_bytes: int = MAX_PAGE_BYTES,
    fetcher: Callable[[str, int], str] | None = None,
) -> str:
    """Plain implementation behind the function tool, testable without network."""
    try:
        parsed = _parse_https_url(payment_url)
    except ValueError as exc:
        return f"Read-only kontrola platebni stranky byla odmitnuta: {exc}"
    domain = parsed.netloc.casefold()

    if not user_confirmed or not has_explicit_payment_page_inspection_confirmation(
        domain=domain,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji vyslovne potvrzeni od Mily v aktualni zprave. "
            f"Potvrzeni musi obsahovat domenu {domain} a jasny souhlas s read-only "
            "kontrolou platebni stranky/faktury. Bez toho odkaz neoteviram."
        )

    safe_max_bytes = min(max(10_000, max_bytes), MAX_PAGE_BYTES)
    try:
        page_text = _fetch_payment_inspection_source(
            parsed_url=payment_url,
            fetcher=fetcher or _fetch_https_text,
            max_bytes=safe_max_bytes,
        )
    except PaymentPageInspectionError as exc:
        return (
            f"Read-only kontrola platebni stranky na domene {domain} selhala: {exc}. "
            "Nic nebylo ulozeno, zaplaceno ani odeslano."
        )

    inspection = inspect_payment_page_text(
        page_text=page_text,
        domain=domain,
        source_label="platebni stranka",
    )
    return format_payment_page_inspection(inspection)


def inspect_payment_page_text(
    page_text: str,
    domain: str = "manual",
    source_label: str = "text",
) -> PaymentPageInspection:
    if _looks_like_json(page_text):
        parsed = _inspect_payment_json_text(
            page_text=page_text,
            domain=domain,
            source_label=source_label,
        )
        if parsed is not None:
            return parsed

    text = _html_to_text(page_text)
    due_date_raw, due_date = _extract_context_date(text, DUE_CONTEXT_PATTERN)
    start_date_raw, start_date = _extract_context_date(text, START_CONTEXT_PATTERN)

    if not due_date:
        due_date_raw, due_date = _extract_best_fallback_date(text)

    amount = _extract_first(AMOUNT_PATTERN, text, "amount")
    policy_number = _extract_first(POLICY_PATTERN, text, "number")

    return PaymentPageInspection(
        domain=domain,
        source_label=source_label,
        due_date=due_date,
        due_date_raw=_compact(due_date_raw),
        due_confidence="high" if due_date_raw and "splat" in due_date_raw.casefold() else (
            "medium" if due_date else "none"
        ),
        start_date=start_date,
        start_date_raw=_compact(start_date_raw),
        amount=_normalize_amount(amount),
        policy_number=policy_number,
        bank_transfer_due_date="",
        payment_gateway_due_date="",
        provider_name="",
        product_name="",
        payment_gateway_domain="",
        fetched_chars=len(text),
    )


def format_payment_page_inspection(inspection: PaymentPageInspection) -> str:
    lines = [
        "Read-only kontrola platebni stranky/faktury:",
        f"- Zdroj: {inspection.source_label}",
        f"- Domena: {inspection.domain}",
        f"- Cislo pojistky/smlouvy/faktury: {inspection.policy_number or 'nenalezeno'}",
        f"- Castka: {inspection.amount or 'nenalezena'}",
        f"- Produkt: {inspection.product_name or 'nenalezen'}",
        f"- Pojistovna/dodavatel: {inspection.provider_name or 'nenalezena'}",
        (
            "- Overena splatnost: "
            f"{inspection.due_date or 'nenalezena'}"
            f" (confidence: {inspection.due_confidence})"
        ),
        f"- Splatnost pro platbu kartou/branu: {inspection.payment_gateway_due_date or 'nenalezena'}",
        f"- Splatnost pro bankovni prevod: {inspection.bank_transfer_due_date or 'nenalezena'}",
        f"- Surovy kontext splatnosti: {inspection.due_date_raw or 'nenalezen'}",
        f"- Pocatek pojisteni/sluzby: {inspection.start_date or 'nenalezen'}",
        f"- Surovy kontext pocatku: {inspection.start_date_raw or 'nenalezen'}",
        f"- Domena platebni brany: {inspection.payment_gateway_domain or 'nenalezena'}",
        "",
        "Dalsi krok:",
    ]

    if inspection.due_date:
        lines.append(
            "- Pro ulozeni platebni pripominky pouzij "
            f"verified_due_date={inspection.due_date}"
            + (
                f" a verified_start_date={inspection.start_date}."
                if inspection.start_date
                else "."
            )
        )
    else:
        lines.append(
            "- Splatnost se nepodarilo spolehlive najit; uloz jen ukol overit splatnost."
        )

    lines.extend(
        [
            "",
            "Bezpecnost: odkaz byl pouze read-only nacten, nic nebylo zaplaceno,",
            "nic nebylo odeslano, plna URL ani token nejsou ve vystupu ulozeny.",
        ]
    )
    return "\n".join(lines)


def has_explicit_payment_page_inspection_confirmation(
    domain: str,
    confirmation_text: str,
) -> bool:
    normalized = confirmation_text.casefold()
    return (
        domain.casefold() in normalized
        and any(word in normalized for word in CONFIRMATION_WORDS)
        and any(word in normalized for word in INSPECTION_WORDS)
    )


class PaymentPageInspectionError(RuntimeError):
    pass


def _parse_https_url(payment_url: str):
    parsed = urlparse(payment_url.strip())
    if parsed.scheme.casefold() != "https" or not parsed.netloc:
        raise ValueError("Platebni inspektor smi nacitat jen verejne HTTPS URL.")
    return parsed


def _fetch_https_text(payment_url: str, max_bytes: int) -> str:
    request = Request(
        payment_url,
        headers={
            "User-Agent": "SamanthaAgentPaymentInspector/1.0",
            "Accept": "text/html,text/plain,application/xhtml+xml;q=0.9,*/*;q=0.1",
        },
        method="GET",
    )
    try:
        with urlopen(
            request,
            timeout=DEFAULT_TIMEOUT_SECONDS,
            context=ssl.create_default_context(),
        ) as response:
            content_type = response.headers.get("Content-Type", "")
            raw = response.read(max_bytes + 1)
    except Exception as exc:  # pragma: no cover - network path is integration-only.
        return _fetch_https_text_with_curl(payment_url=payment_url, max_bytes=max_bytes, cause=exc)

    if len(raw) > max_bytes:
        raise PaymentPageInspectionError("stranka je vetsi nez bezpecny limit nacteni")

    if not _is_text_content_type(content_type):
        raise PaymentPageInspectionError(
            f"neocekavany typ obsahu {content_type or 'neznamy'}"
        )

    encoding = _extract_charset(content_type) or "utf-8"
    try:
        return raw.decode(encoding, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def _fetch_https_text_with_curl(payment_url: str, max_bytes: int, cause: Exception) -> str:
    try:
        completed = subprocess.run(
            [
                "curl",
                "-sS",
                "-L",
                "--fail",
                "--max-time",
                str(DEFAULT_TIMEOUT_SECONDS),
                "--max-filesize",
                str(max_bytes),
                payment_url,
            ],
            check=True,
            capture_output=True,
            timeout=DEFAULT_TIMEOUT_SECONDS + 3,
        )
    except Exception as curl_exc:
        raise PaymentPageInspectionError(str(cause)) from curl_exc

    raw = completed.stdout
    if len(raw) > max_bytes:
        raise PaymentPageInspectionError("stranka je vetsi nez bezpecny limit nacteni")
    return raw.decode("utf-8", errors="replace")


def _fetch_payment_inspection_source(
    parsed_url: str,
    fetcher: Callable[[str, int], str],
    max_bytes: int,
) -> str:
    parsed = urlparse(parsed_url)
    api_url = _rixo_payment_api_url(parsed)
    if api_url:
        return fetcher(api_url, max_bytes)
    return fetcher(parsed_url, max_bytes)


def _rixo_payment_api_url(parsed) -> str:
    if parsed.netloc.casefold() != "app.rixo.cz":
        return ""
    match = re.fullmatch(r"/platba/([^/?#]+)", parsed.path)
    if not match:
        return ""
    hash_id = match.group(1)
    return f"https://app.rixo.cz/be/api/public/quick-contracts/{hash_id}/payment"


def _looks_like_json(text: str) -> bool:
    stripped = text.lstrip()
    return stripped.startswith("{") or stripped.startswith("[")


def _inspect_payment_json_text(
    page_text: str,
    domain: str,
    source_label: str,
) -> PaymentPageInspection | None:
    try:
        data = json.loads(page_text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None

    terms = data.get("terms")
    if not isinstance(terms, dict):
        terms = {}
    product = data.get("product")
    if not isinstance(product, dict):
        product = {}
    provider = product.get("provider")
    if not isinstance(provider, dict):
        provider = {}

    gateway_due = _iso_date_from_value(terms.get("dueDatePaymentGateway"))
    bank_due = _iso_date_from_value(terms.get("dueDateBankTransfer"))
    general_due = _iso_date_from_value(data.get("dueDate"))
    start_date = _iso_date_from_value(data.get("contractValidityStartDate"))
    due_date = gateway_due or bank_due or general_due
    due_context = _payment_json_due_context(
        gateway_due=gateway_due,
        bank_due=bank_due,
        general_due=general_due,
    )
    gateway_url = str(data.get("gatewayUrl") or "")

    return PaymentPageInspection(
        domain=domain,
        source_label=source_label,
        due_date=due_date,
        due_date_raw=due_context,
        due_confidence="high" if due_date else "none",
        start_date=start_date,
        start_date_raw=(
            f"contractValidityStartDate={start_date}" if start_date else ""
        ),
        amount=_amount_from_json(data.get("amount")),
        policy_number=str(data.get("variableSymbol") or ""),
        bank_transfer_due_date=bank_due,
        payment_gateway_due_date=gateway_due,
        provider_name=str(provider.get("name") or ""),
        product_name=str(product.get("name") or ""),
        payment_gateway_domain=urlparse(gateway_url).netloc.casefold() if gateway_url else "",
        fetched_chars=len(page_text),
    )


def _payment_json_due_context(
    gateway_due: str,
    bank_due: str,
    general_due: str,
) -> str:
    parts: list[str] = []
    if gateway_due:
        parts.append(f"terms.dueDatePaymentGateway={gateway_due}")
    if bank_due:
        parts.append(f"terms.dueDateBankTransfer={bank_due}")
    if general_due:
        parts.append(f"dueDate={general_due}")
    return "; ".join(parts)


def _iso_date_from_value(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    return _parse_human_date(value)


def _amount_from_json(value: object) -> str:
    if isinstance(value, int | float):
        if float(value).is_integer():
            return f"{int(value)} Kc"
        return f"{value:.2f} Kc"
    if isinstance(value, str):
        return _normalize_amount(value)
    return ""


def _is_text_content_type(content_type: str) -> bool:
    low = content_type.casefold()
    return (
        not low
        or "text/" in low
        or "html" in low
        or "xhtml" in low
        or "json" in low
    )


def _extract_charset(content_type: str) -> str:
    match = re.search(r"charset=([A-Za-z0-9_.-]+)", content_type, re.IGNORECASE)
    return match.group(1) if match else ""


def _html_to_text(raw: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</(p|div|li|tr|h[1-6])>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"[ \t]+", " ", text)


def _extract_context_date(text: str, pattern: re.Pattern[str]) -> tuple[str, str]:
    match = pattern.search(text)
    if not match:
        return "", ""
    raw_date = match.group("date")
    parsed = _parse_human_date(raw_date)
    return match.group("context"), parsed


def _extract_best_fallback_date(text: str) -> tuple[str, str]:
    match = DATE_VALUE_PATTERN.search(text)
    if not match:
        return "", ""
    raw_date = match.group("date")
    return raw_date, _parse_human_date(raw_date)


def _parse_human_date(raw_date: str) -> str:
    value = raw_date.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", value):
            year, month, day = [int(part) for part in value.split("-")]
            return date(year, month, day).isoformat()

        parts = re.split(r"[./-]", value)
        if len(parts) != 3:
            return ""
        day = int(parts[0])
        month = int(parts[1])
        year = int(parts[2])
        if year < 100:
            year += 2000
        return date(year, month, day).isoformat()
    except ValueError:
        return ""


def _extract_first(pattern: re.Pattern[str], text: str, group: str) -> str:
    match = pattern.search(text)
    return match.group(group).strip() if match else ""


def _normalize_amount(amount: str) -> str:
    if not amount:
        return ""
    return f"{amount.replace(' ', '').replace(',', '.')} Kc"


def _compact(text: str, max_chars: int = 180) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[:max_chars].rstrip() + "..."
