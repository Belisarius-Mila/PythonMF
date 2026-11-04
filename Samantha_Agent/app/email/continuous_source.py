"""Complete, read-only IMAP input for the continuous personal agent."""

from __future__ import annotations

import hashlib
import imaplib
from dataclasses import dataclass, replace

from .archive_models import EmailArchiveSource
from .config import load_icloud_mail_config, load_seznam_mail_config
from .icloud_provider import _message_data_to_archive_source


@dataclass(frozen=True)
class ObservedEmail:
    account: str
    uidvalidity: str
    source: EmailArchiveSource

    @property
    def item_id(self) -> str:
        identity = (self.account, self.source.mailbox, self.uidvalidity, self.source.uid)
        return hashlib.sha256(repr(identity).encode()).hexdigest()

    @property
    def content_digest(self) -> str:
        if self.source.original_eml is None:
            raise ValueError("Úplný e-mail musí obsahovat původní EML.")
        return hashlib.sha256(self.source.original_eml).hexdigest()


@dataclass(frozen=True)
class MailScan:
    uidvalidity: str
    messages: tuple[ObservedEmail, ...]


class IMAPAgentSource:
    """Read whole messages without marking them read; no content classification."""

    def __init__(self, provider: str, folder: str = "INBOX", *, imap_factory=None):
        if provider == "icloud":
            config = load_icloud_mail_config()
            password = config.app_password
        elif provider == "seznam":
            config = load_seznam_mail_config()
            password = config.password
        else:
            raise ValueError("Neznámý e-mailový zdroj.")
        self.provider, self.folder = provider, folder
        self.config, self.password = config, password
        identity = f"{provider}|{config.address.casefold()}|{folder}"
        self.key = hashlib.sha256(identity.encode()).hexdigest()
        self.imap_factory = imap_factory or imaplib.IMAP4_SSL

    def scan(self, cursor: dict, *, limit: int = 10) -> MailScan:
        if not 1 <= limit <= 100:
            raise ValueError("Velikost dávky musí být 1 až 100.")
        with self.imap_factory(self.config.host, self.config.port) as imap:
            imap.login(self.config.address, self.password)
            status, _ = imap.select(self.folder, readonly=True)
            if status != "OK":
                raise RuntimeError("Nelze otevřít sledovanou schránku.")
            _, validity_data = imap.response("UIDVALIDITY")
            if not validity_data or not validity_data[0]:
                raise RuntimeError("Schránka nevrátila UIDVALIDITY.")
            validity = validity_data[0].decode("ascii")
            after = int(cursor.get("after_uid", 0)) if cursor.get("uidvalidity") == validity else 0
            status, data = imap.uid("SEARCH", None, "UID", f"{after + 1}:*")
            if status != "OK" or not data or not isinstance(data[0], bytes):
                raise RuntimeError("Kontrola nových e-mailů selhala.")
            uids = sorted({int(uid) for uid in data[0].split() if int(uid) > after})[:limit]
            messages = []
            for uid in uids:
                status, parts = imap.uid("FETCH", str(uid).encode(), "(RFC822.SIZE BODY.PEEK[])")
                if status != "OK" or not parts:
                    raise RuntimeError("Úplné načtení e-mailu selhalo.")
                raw_parts = [part[1] for part in parts if isinstance(part, tuple) and isinstance(part[1], bytes)]
                if len(raw_parts) != 1:
                    raise RuntimeError("E-mail nemá jedno úplné MIME tělo.")
                source = _message_data_to_archive_source(
                    str(uid), parts, max_chars=None, folder=self.folder,
                    max_message_bytes=len(raw_parts[0]),
                )
                messages.append(ObservedEmail(self.key, validity, replace(source, provider=self.provider)))
            return MailScan(validity, tuple(messages))
