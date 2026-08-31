from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .vault import (
    DEFAULT_DOCUMENTS_DIR,
    PROJECT_ROOT,
    apply_document_import_file,
    extract_text,
    find_duplicate_by_sha,
    is_relative_to,
    normalize_confirmation_text,
    safe_slug,
    safe_text,
    sha256_file,
    tesseract_languages,
    TextExtractionResult,
    validate_source_file,
)


LOCAL_SEND_ROOT = Path.home() / "Desktop" / "LocalSend"
BANKING_DOMAIN = "banking"
BANKING_DOCUMENT_TYPE = "bank-account-parameters"


@dataclass(frozen=True)
class BankDocumentMetadata:
    bank_name: str
    product_name: str
    currency: str
    account_number: str
    iban: str
    bic_swift: str
    document_date: str
    account_opened_on: str

    @property
    def complete(self) -> bool:
        return bool(
            self.bank_name
            and self.currency
            and self.account_number
            and self.iban
            and self.bic_swift
            and self.document_date
        )

    def restricted_record(self) -> dict[str, str]:
        return {
            "bank_name": self.bank_name,
            "product_name": self.product_name,
            "currency": self.currency,
            "account_number": self.account_number,
            "iban": self.iban,
            "bic_swift": self.bic_swift,
            "document_date": self.document_date,
            "account_opened_on": self.account_opened_on,
            "snapshot_as_of": self.document_date,
        }


def prepare_restricted_bank_document_import_summary(
    source_path: str,
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    source = resolve_restricted_bank_source(source_path)
    if isinstance(source, str):
        return source
    try:
        validate_source_file(source)
        extraction = extract_restricted_bank_text(source)
    except ValueError as exc:
        return f"Priprava bankovniho dokumentu byla odmitnuta: {exc}"

    metadata = extract_bank_document_metadata(extraction.text)
    duplicate = find_duplicate_by_sha(vault_dir=vault_dir, sha256=sha256_file(source))
    missing = missing_required_bank_fields(metadata)
    document_id = suggested_bank_document_id(metadata)
    lines = [
        "Navrh restricted importu bankovniho dokumentu (read-only):",
        f"- Soubor: {safe_text(source.name)}",
        f"- Document ID: {document_id}",
        f"- Banka: {metadata.bank_name or 'nezjisteno'}",
        f"- Produkt: {metadata.product_name or 'nezjisteno'}",
        f"- Mena: {metadata.currency or 'nezjisteno'}",
        f"- Cislo uctu: {mask_account_number(metadata.account_number)}",
        f"- IBAN: {mask_identifier(metadata.iban)}",
        f"- BIC/SWIFT: {metadata.bic_swift or 'nezjisteno'}",
        f"- Datum dokumentu: {metadata.document_date or 'nezjisteno'}",
        f"- Datum zalozeni uctu: {metadata.account_opened_on or 'nezjisteno'}",
        "- Cil: private document vault / banking",
        "- Raw OCR v textovem indexu: ne",
        "- Plne bankovni udaje: pouze restricted_metadata.json",
        "- Rodne cislo, adresa a aktivacni udaj: do metadat se neukladaji",
    ]
    if duplicate:
        lines.append(
            "- Duplicita: stejny obsah uz je ulozen jako "
            f"{safe_text(str(duplicate.get('document_id', '')))}"
        )
    if missing:
        lines.extend(
            [
                f"- BLOKATOR: chybi pole {', '.join(missing)}.",
                "- Finalni import se bez jejich rucni kontroly neprovede.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "Potvrzovaci veta:",
                f"`Potvrzuji, uloz bankovni dokument {source.name} do oblasti banking v restricted rezimu.`",
            ]
        )
    lines.extend(
        [
            "",
            "Bezpecnost: tento nahled nic nekopiruje ani nezapisuje.",
        ]
    )
    return "\n".join(lines)


def apply_restricted_bank_document_import_summary(
    source_path: str,
    document_id: str = "",
    user_confirmed: bool = False,
    confirmation_text: str = "",
    vault_dir: Path = DEFAULT_DOCUMENTS_DIR,
) -> str:
    source = resolve_restricted_bank_source(source_path)
    if isinstance(source, str):
        return source
    if not user_confirmed or not has_explicit_restricted_bank_import_confirmation(
        filename=source.name,
        confirmation_text=confirmation_text,
    ):
        return (
            "Nejdrive potrebuji samostatne potvrzeni od Mily v aktualni zprave. "
            f"Pouzij presne: Potvrzuji, uloz bankovni dokument {source.name} "
            "do oblasti banking v restricted rezimu."
        )

    try:
        validate_source_file(source)
        extraction = extract_restricted_bank_text(source)
    except ValueError as exc:
        return f"Restricted import bankovniho dokumentu byl odmitnut: {exc}"
    metadata = extract_bank_document_metadata(extraction.text)
    missing = missing_required_bank_fields(metadata)
    if missing:
        return (
            "Restricted import bankovniho dokumentu byl odmitnut: "
            f"chybi overena pole {', '.join(missing)}."
        )

    safe_document_id = safe_slug(
        document_id,
        default=suggested_bank_document_id(metadata),
        limit=140,
    )
    try:
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temp_dir:
            staged_source = Path(temp_dir) / source.name
            shutil.copy2(source, staged_source)
            result = apply_document_import_file(
                source_path=str(staged_source),
                target_domain=BANKING_DOMAIN,
                document_type=BANKING_DOCUMENT_TYPE,
                counterparty=metadata.bank_name,
                related_asset=metadata.product_name,
                tags="moneta; bankovni-ucet; eurovy-ucet; smluvni-dokument; restricted",
                document_id=safe_document_id,
                document_title="MONETA - Bezny ucet v EUR - parametry uctu",
                reading_status="ok",
                index_text_override=build_redacted_bank_index_text(metadata),
                restricted_metadata=metadata.restricted_record(),
                restricted_metadata_kind="bank-account",
                vault_dir=vault_dir,
            )
    except ValueError as exc:
        return f"Restricted import bankovniho dokumentu byl odmitnut: {exc}"

    status = "ulozeno" if result.created else "uz existuje"
    return (
        f"Stav: {status}. Document ID: {result.document_id}. "
        "Original je v private vaultu, plne bankovni udaje jsou v restricted metadatech "
        "a raw OCR nebyl vlozen do vyhledavaciho indexu."
    )


def resolve_restricted_bank_source(source_path: str) -> Path | str:
    candidate = Path(source_path).expanduser()
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError:
        return f"Prace s bankovnim dokumentem byla odmitnuta: soubor neexistuje: {source_path}"
    allowed_roots = (
        (PROJECT_ROOT / "data").resolve(),
        Path("/private/tmp").resolve(),
        LOCAL_SEND_ROOT.resolve(),
    )
    if not any(is_relative_to(resolved, root) for root in allowed_roots):
        return (
            "Prace s bankovnim dokumentem byla odmitnuta: zdroj musi byt v LocalSend, "
            "projektove slozce data/ nebo v /private/tmp."
        )
    return resolved


def extract_bank_document_metadata(text: str) -> BankDocumentMetadata:
    folded = fold_ascii(text)
    compact = " ".join(folded.split())
    account_number = first_group(
        compact,
        r"(?:cislo uctu|cislo)\s*:\s*((?:\d{1,10}-)?\d{2,10}/\d{4})",
    )
    iban_match = re.search(r"(?<![A-Z0-9])CZ(?:[\s-]*\d){22}(?!\d)", text, re.IGNORECASE)
    iban = re.sub(r"[^A-Z0-9]", "", iban_match.group(0).upper()) if iban_match else ""
    bic_swift = first_group(compact.upper(), r"(?:SWIFT|BIC).{0,60}?([A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)")
    document_date = extract_iso_date(compact, r"(?:v ramci uctu|smart banku).{0,100}?dne\s*:?\s*")
    account_opened_on = extract_iso_date(compact, r"datum zalozeni uctu.{0,60}?")
    bank_name = "MONETA Money Bank, a.s." if "moneta money bank" in compact else ""
    product_name = "Běžný účet v EUR" if "bezny ucet v eur" in compact else "Eurový účet"
    currency = "EUR" if re.search(r"\bEUR\b", text, re.IGNORECASE) else ""
    return BankDocumentMetadata(
        bank_name=bank_name,
        product_name=product_name,
        currency=currency,
        account_number=account_number,
        iban=iban,
        bic_swift=bic_swift,
        document_date=document_date,
        account_opened_on=account_opened_on,
    )


def extract_restricted_bank_text(source: Path) -> TextExtractionResult:
    extraction = extract_text(source)
    if extraction.text.strip() or source.suffix.casefold() not in {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".tif",
        ".tiff",
    }:
        return extraction
    tesseract = shutil.which("tesseract")
    if not tesseract:
        return TextExtractionResult(
            text="",
            method="restricted-image-ocr-unavailable",
            ocr_needed=True,
            warning="Chybi tesseract pro OCR obrazku.",
        )
    try:
        completed = subprocess.run(
            [tesseract, str(source), "stdout", "-l", tesseract_languages(), "--psm", "3"],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired):
        return TextExtractionResult(
            text="",
            method="restricted-image-ocr-failed",
            ocr_needed=True,
            warning="OCR obrazku se nepodarilo spustit.",
        )
    text = completed.stdout.strip() if completed.returncode == 0 else ""
    return TextExtractionResult(
        text=text,
        method="restricted-image-tesseract-ocr",
        ocr_needed=not bool(text),
        warning="" if text else "Tesseract z obrazku neziskal pouzitelny text.",
    )
def build_redacted_bank_index_text(metadata: BankDocumentMetadata) -> str:
    return " ".join(
        part
        for part in (
            metadata.bank_name,
            metadata.product_name,
            "bankovni dokument parametry uctu smluvni dokument",
            f"mena {metadata.currency}",
            f"ucet konci {account_number_suffix(metadata.account_number)}",
            f"IBAN konci {last_four(metadata.iban)}",
            f"BIC {metadata.bic_swift}",
            f"datum dokumentu {metadata.document_date}",
        )
        if part.strip()
    )


def missing_required_bank_fields(metadata: BankDocumentMetadata) -> list[str]:
    fields = {
        "bank_name": metadata.bank_name,
        "currency": metadata.currency,
        "account_number": metadata.account_number,
        "iban": metadata.iban,
        "bic_swift": metadata.bic_swift,
        "document_date": metadata.document_date,
    }
    return [name for name, value in fields.items() if not value]


def suggested_bank_document_id(metadata: BankDocumentMetadata) -> str:
    suffix = metadata.document_date or "undated"
    return safe_slug(f"moneta-bezny-ucet-eur-{suffix}", default="bank-document", limit=140)


def has_explicit_restricted_bank_import_confirmation(
    filename: str,
    confirmation_text: str,
) -> bool:
    normalized = normalize_confirmation_text(confirmation_text)
    return (
        normalize_confirmation_text(filename) in normalized
        and "banking" in normalized
        and "restricted" in normalized
        and any(word in normalized for word in ("uloz", "ulož", "ulozit", "uložit"))
        and "bankovni dokument" in normalized
    )


def fold_ascii(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).casefold()


def first_group(text: str, pattern: str) -> str:
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def extract_iso_date(text: str, prefix_pattern: str) -> str:
    match = re.search(prefix_pattern + r"(\d{1,2})\s*[.]\s*(\d{1,2})\s*[.]\s*(\d{4})", text)
    if not match:
        return ""
    try:
        return datetime(
            int(match.group(3)),
            int(match.group(2)),
            int(match.group(1)),
        ).date().isoformat()
    except ValueError:
        return ""


def last_four(value: str) -> str:
    compact = re.sub(r"[^A-Za-z0-9]", "", value)
    return compact[-4:] if compact else ""


def mask_identifier(value: str) -> str:
    suffix = last_four(value)
    return f"****{suffix}" if suffix else "nezjisteno"


def account_number_suffix(value: str) -> str:
    account_part = value.split("/", 1)[0].split("-")[-1]
    compact = re.sub(r"\D", "", account_part)
    return compact[-4:] if compact else ""


def mask_account_number(value: str) -> str:
    suffix = account_number_suffix(value)
    bank_code = value.split("/", 1)[1] if "/" in value else ""
    if not suffix:
        return "nezjisteno"
    return f"****{suffix}/{bank_code}" if bank_code else f"****{suffix}"
