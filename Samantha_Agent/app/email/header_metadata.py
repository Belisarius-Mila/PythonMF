from __future__ import annotations

from email.header import decode_header
import re
from typing import Any
from urllib.parse import unquote_to_bytes

from .models import EmailAttachmentMeta


def extract_attachment_metadata_from_bodystructure(message_data: list[object]) -> tuple[EmailAttachmentMeta, ...]:
    bodystructure = _extract_bodystructure_bytes(message_data)
    if not bodystructure:
        return ()
    try:
        parsed = _BodyStructureParser(bodystructure).parse()
    except ValueError:
        return ()
    attachments: list[EmailAttachmentMeta] = []
    _collect_attachments(parsed, "1", attachments)
    return tuple(attachments)


def _extract_bodystructure_bytes(message_data: list[object]) -> bytes:
    chunks: list[bytes] = []
    collecting = False
    for item in message_data:
        if not (isinstance(item, tuple) and item):
            continue
        metadata = item[0]
        if not isinstance(metadata, bytes):
            continue
        payload = item[1] if len(item) >= 2 and isinstance(item[1], bytes) else b""
        if not collecting:
            marker_index = metadata.upper().find(b"BODYSTRUCTURE")
            if marker_index < 0:
                continue
            start = metadata.find(b"(", marker_index)
            if start < 0:
                continue
            metadata = metadata[start:]
            collecting = True
        chunks.append(_replace_terminal_literal(metadata, payload))
        balanced = _balanced_bodystructure_prefix(b"".join(chunks))
        if balanced:
            return balanced
    return b""


def _replace_terminal_literal(metadata: bytes, payload: bytes) -> bytes:
    match = re.search(rb"\{(\d+)\}\s*$", metadata)
    if not match:
        return metadata
    try:
        expected_length = int(match.group(1))
    except ValueError:
        return metadata
    if len(payload) != expected_length:
        return metadata
    return metadata[: match.start()] + _quote_bodystructure_literal(payload)


def _quote_bodystructure_literal(value: bytes) -> bytes:
    return b'"' + value.replace(b"\\", b"\\\\").replace(b'"', b'\\"') + b'"'


def _balanced_bodystructure_prefix(raw: bytes) -> bytes:
    if not raw:
        return b""
    depth = 0
    in_quote = False
    escaped = False
    for index, char in enumerate(raw):
        if in_quote:
            if escaped:
                escaped = False
            elif char == 92:
                escaped = True
            elif char == 34:
                in_quote = False
            continue
        if char == 34:
            in_quote = True
        elif char == 40:
            depth += 1
        elif char == 41:
            depth -= 1
            if depth == 0:
                return raw[: index + 1]
    return b""


class _BodyStructureParser:
    def __init__(self, raw: bytes) -> None:
        self._raw = raw
        self._index = 0

    def parse(self) -> Any:
        value = self._parse_value()
        self._skip_ws()
        return value

    def _parse_value(self) -> Any:
        self._skip_ws()
        if self._index >= len(self._raw):
            raise ValueError("Unexpected end of BODYSTRUCTURE.")
        char = self._raw[self._index]
        if char == 40:
            return self._parse_list()
        if char == 34:
            return self._parse_quoted()
        return self._parse_atom()

    def _parse_list(self) -> list[Any]:
        self._index += 1
        values: list[Any] = []
        while True:
            self._skip_ws()
            if self._index >= len(self._raw):
                raise ValueError("Unclosed BODYSTRUCTURE list.")
            if self._raw[self._index] == 41:
                self._index += 1
                return values
            values.append(self._parse_value())

    def _parse_quoted(self) -> str:
        self._index += 1
        output = bytearray()
        escaped = False
        while self._index < len(self._raw):
            char = self._raw[self._index]
            self._index += 1
            if escaped:
                output.append(char)
                escaped = False
            elif char == 92:
                escaped = True
            elif char == 34:
                return output.decode("utf-8", errors="replace")
            else:
                output.append(char)
        raise ValueError("Unclosed BODYSTRUCTURE quote.")

    def _parse_atom(self) -> Any:
        start = self._index
        while self._index < len(self._raw) and self._raw[self._index] not in b" ()\r\n\t":
            self._index += 1
        atom = self._raw[start : self._index].decode("ascii", errors="replace")
        if atom.upper() == "NIL":
            return None
        if atom.isdigit():
            return int(atom)
        return atom

    def _skip_ws(self) -> None:
        while self._index < len(self._raw) and self._raw[self._index] in b" \r\n\t":
            self._index += 1


def _collect_attachments(node: Any, path: str, attachments: list[EmailAttachmentMeta]) -> None:
    if not isinstance(node, list) or not node:
        return
    if isinstance(node[0], list):
        part_index = 1
        for child in node:
            if not isinstance(child, list):
                break
            _collect_attachments(child, f"{path}.{part_index}" if path else str(part_index), attachments)
            part_index += 1
        return
    if len(node) < 7:
        return

    major = _text(node[0]).lower()
    subtype = _text(node[1]).lower()
    params = _params(node[2])
    content_id = _decode_header_value(_text(node[3]))
    size_bytes = node[6] if isinstance(node[6], int) else None
    disposition_name = ""
    disposition_params: dict[str, str] = {}
    if len(node) > 8 and isinstance(node[8], list) and node[8]:
        disposition_name = _text(node[8][0]).lower()
        if len(node[8]) > 1:
            disposition_params = _params(node[8][1])

    filename = (
        disposition_params.get("filename")
        or disposition_params.get("name")
        or params.get("filename")
        or params.get("name")
    )
    if disposition_name != "attachment" and not filename:
        return

    attachments.append(
        EmailAttachmentMeta(
            filename=_decode_header_value(filename) or "(bez nazvu)",
            content_type=f"{major}/{subtype}" if major and subtype else "",
            size_bytes=size_bytes,
            part_id=path,
            content_id=content_id,
            disposition=disposition_name or "inline",
        )
    )


def _params(value: Any) -> dict[str, str]:
    if not isinstance(value, list):
        return {}
    params: dict[str, str] = {}
    for index in range(0, len(value) - 1, 2):
        key = _text(value[index]).lower()
        if not key:
            continue
        decoded_value = _decode_header_value(_text(value[index + 1]))
        if key.endswith("*"):
            key = key.rstrip("*")
            decoded_value = _decode_rfc2231_value(decoded_value)
        params[key] = decoded_value
    return params


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    decoded_parts: list[str] = []
    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            for candidate in (encoding, "utf-8", "latin-1"):
                if not candidate:
                    continue
                try:
                    decoded_parts.append(part.decode(candidate, errors="replace"))
                    break
                except LookupError:
                    continue
        else:
            decoded_parts.append(part)
    return " ".join(" ".join(decoded_parts).split())


def _decode_rfc2231_value(value: str) -> str:
    if not value:
        return ""
    if "''" in value:
        charset, encoded = value.split("''", 1)
    else:
        charset, encoded = "utf-8", value
    try:
        return unquote_to_bytes(encoded).decode(charset or "utf-8", errors="replace")
    except (LookupError, ValueError):
        return value
