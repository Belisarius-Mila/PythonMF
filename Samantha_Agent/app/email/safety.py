from __future__ import annotations


CONFIRMATION_WORDS = (
    "potvrzuji",
    "souhlasim",
    "ano",
    "precti",
    "precist",
    "přečti",
    "přečíst",
    "vypis",
    "vypsat",
    "vypiš",
)

LINK_REQUEST_WORDS = (
    "url",
    "urls",
    "odkaz",
    "odkazy",
    "link",
    "linky",
)


def has_explicit_read_confirmation(uid: str, confirmation_text: str) -> bool:
    normalized_text = confirmation_text.casefold()
    normalized_uid = uid.strip()
    return normalized_uid in normalized_text and any(
        word in normalized_text for word in CONFIRMATION_WORDS
    )


def has_explicit_link_confirmation(uid: str, confirmation_text: str) -> bool:
    normalized_text = confirmation_text.casefold()
    return has_explicit_read_confirmation(
        uid=uid,
        confirmation_text=confirmation_text,
    ) and any(word in normalized_text for word in LINK_REQUEST_WORDS)


def has_explicit_multi_uid_read_confirmation(
    uids: list[str] | tuple[str, ...],
    confirmation_text: str,
) -> bool:
    normalized_text = confirmation_text.casefold()
    normalized_uids = [uid.strip() for uid in uids if uid.strip()]
    if len(normalized_uids) < 2:
        return False
    if len(set(normalized_uids)) != len(normalized_uids):
        return False
    return all(uid in normalized_text for uid in normalized_uids) and any(
        word in normalized_text for word in CONFIRMATION_WORDS
    )
