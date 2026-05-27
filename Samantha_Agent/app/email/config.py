from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ICLOUD_IMAP_HOST = "imap.mail.me.com"
ICLOUD_IMAP_PORT = 993
ICLOUD_SMTP_HOST = "smtp.mail.me.com"
ICLOUD_SMTP_PORT = 587
SEZNAM_IMAP_HOST = "imap.seznam.cz"
SEZNAM_IMAP_PORT = 993
SEZNAM_SMTP_HOST = "smtp.seznam.cz"
SEZNAM_SMTP_PORT = 465


class EmailConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class ICloudMailConfig:
    address: str
    app_password: str
    host: str = ICLOUD_IMAP_HOST
    port: int = ICLOUD_IMAP_PORT


@dataclass(frozen=True)
class SeznamMailConfig:
    address: str
    password: str
    host: str = SEZNAM_IMAP_HOST
    port: int = SEZNAM_IMAP_PORT


@dataclass(frozen=True)
class OutgoingMailConfig:
    address: str
    password: str
    host: str
    port: int
    security: str
    provider: str


def load_icloud_mail_config(env_path: Path | None = None) -> ICloudMailConfig:
    load_dotenv(env_path or PROJECT_ROOT / ".env")

    address = os.getenv("ICLOUD_MAIL_ADDRESS", "").strip()
    app_password = os.getenv("ICLOUD_MAIL_APP_PASSWORD", "").strip()

    if not address or not app_password:
        raise EmailConfigError(
            "Chybi lokalni iCloud Mail konfigurace v .env."
        )

    return ICloudMailConfig(address=address, app_password=app_password)


def load_seznam_mail_config(env_path: Path | None = None) -> SeznamMailConfig:
    load_dotenv(env_path or PROJECT_ROOT / ".env")

    address = os.getenv("SEZNAM_MAIL_ADDRESS", "").strip()
    password = os.getenv("SEZNAM_MAIL_PASSWORD", "").strip()

    if not address or not password:
        raise EmailConfigError(
            "Chybi lokalni Seznam Mail konfigurace v .env."
        )

    return SeznamMailConfig(address=address, password=password)


def load_icloud_smtp_config(env_path: Path | None = None) -> OutgoingMailConfig:
    incoming = load_icloud_mail_config(env_path=env_path)
    return OutgoingMailConfig(
        address=incoming.address,
        password=incoming.app_password,
        host=ICLOUD_SMTP_HOST,
        port=ICLOUD_SMTP_PORT,
        security="starttls",
        provider="icloud",
    )


def load_seznam_smtp_config(env_path: Path | None = None) -> OutgoingMailConfig:
    incoming = load_seznam_mail_config(env_path=env_path)
    return OutgoingMailConfig(
        address=incoming.address,
        password=incoming.password,
        host=SEZNAM_SMTP_HOST,
        port=SEZNAM_SMTP_PORT,
        security="ssl",
        provider="seznam",
    )


def load_smtp_config(provider: str, env_path: Path | None = None) -> OutgoingMailConfig:
    normalized = provider.strip().casefold()
    if normalized == "icloud":
        return load_icloud_smtp_config(env_path=env_path)
    if normalized == "seznam":
        return load_seznam_smtp_config(env_path=env_path)
    raise EmailConfigError("Neznamy SMTP provider. Pouzij `icloud` nebo `seznam`.")
