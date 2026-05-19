from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ICLOUD_IMAP_HOST = "imap.mail.me.com"
ICLOUD_IMAP_PORT = 993


class EmailConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class ICloudMailConfig:
    address: str
    app_password: str
    host: str = ICLOUD_IMAP_HOST
    port: int = ICLOUD_IMAP_PORT


def load_icloud_mail_config(env_path: Path | None = None) -> ICloudMailConfig:
    load_dotenv(env_path or PROJECT_ROOT / ".env")

    address = os.getenv("ICLOUD_MAIL_ADDRESS", "").strip()
    app_password = os.getenv("ICLOUD_MAIL_APP_PASSWORD", "").strip()

    if not address or not app_password:
        raise EmailConfigError(
            "Chybi lokalni iCloud Mail konfigurace v .env."
        )

    return ICloudMailConfig(address=address, app_password=app_password)
