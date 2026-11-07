"""Pure frozen-source anchor catalogue. No model, disk writes or approval.

Short IDs are local to one catalogue hash. Their bindings include path, full
UTF-8 SHA-256 and character span. Quotes always come from the frozen source,
never from a model string or a case/whitespace-normalized approximation.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from app.recovery_guide_sources import Snapshot, Source, canonical_json, digest, reject_secrets

VERSION = 1


class AnchorError(ValueError):
    """Safe diagnostic code only, without source or response contents."""


@dataclass(frozen=True)
class Anchor:
    source_id: str
    anchor_id: str
    start: int
    end: int
    line: int
    quote_sha256: str
    binding_sha256: str


@dataclass(frozen=True, init=False, eq=False)
class Catalogue:
    snapshot_sha256: str
    original_id: str
    document_ids: tuple[str, ...]
    sha256: str
    _sources: Mapping[str, Source]
    _anchors: Mapping[tuple[str, str], Anchor]
    _models: Mapping[str, str]
    _paths: Mapping[str, str]

    def __init__(self, snapshot: Snapshot):
        rows = (snapshot.original, *sorted(snapshot.sources, key=lambda r: r.path))
        if len({r.path for r in rows}) != len(rows):
            raise AnchorError('duplicate_source_path')
        sources, anchors, models = {}, {}, {}
        for index, row in enumerate(rows):
            if (not all(isinstance(v, str) for v in (row.path, row.sha256, row.text, row.authority))
                    or not row.path or digest(row.text) != row.sha256):
                raise AnchorError('invalid_source_binding')
            reject_secrets(row.text)
            # Copy immutable values; a caller's mutable containers are not held.
            source = Source(row.path, row.sha256, row.text, row.authority)
            source_id = f'd{index:04d}'
            sources[source_id] = source
            lines, cursor, count, physical_line = [], 0, 0, 1
            for number, raw in enumerate(source.text.splitlines(keepends=True), 1):
                end = cursor + len(raw.rstrip('\r\n'))
                quote = source.text[cursor:end]
                anchor_id = f'l{number}' if quote.strip() else None
                if anchor_id:
                    sha = digest(quote)
                    binding = digest(canonical_json({'path': source.path, 'source_sha256': source.sha256,
                        'start': cursor, 'end': end, 'quote_sha256': sha}))
                    anchors[(source_id, anchor_id)] = Anchor(source_id, anchor_id, cursor, end,
                        physical_line, sha, binding)
                    count += 1
                lines.append([anchor_id, raw])  # Compact input; full line bytes stay unchanged.
                cursor += len(raw)
                physical_line += raw.count('\n')
            if cursor != len(source.text) or ''.join(r[1] for r in lines) != source.text:
                raise AnchorError('incomplete_source_lines')
            if not count:
                raise AnchorError('empty_source_has_no_citation_anchor')
            models[source_id] = canonical_json({'source_id': source_id, 'path': source.path,
                'sha256': source.sha256, 'authority': source.authority, 'lines': lines})
        object.__setattr__(self, 'snapshot_sha256', snapshot.sha256)
        object.__setattr__(self, 'original_id', 'd0000')
        object.__setattr__(self, '_sources', MappingProxyType(sources))
        object.__setattr__(self, '_anchors', MappingProxyType(anchors))
        object.__setattr__(self, '_models', MappingProxyType(models))
        object.__setattr__(self, '_paths', MappingProxyType({r.path: key for key, r in sources.items()}))
        object.__setattr__(self, 'document_ids', tuple(key for key in sources if key != self.original_id))
        object.__setattr__(self, 'sha256', digest(canonical_json({'version': VERSION, 'snapshot_sha256': self.snapshot_sha256,
            'sources': [{'id': key, 'path': row.path, 'sha256': row.sha256, 'authority': row.authority}
                        for key, row in sources.items()],
            'anchors': [{'source_id': a.source_id, 'anchor_id': a.anchor_id, 'binding_sha256': a.binding_sha256}
                        for a in anchors.values()]})))

    def assert_snapshot(self, current: Snapshot):
        if current.sha256 != self.snapshot_sha256:
            raise AnchorError('snapshot_changed')

    def source_id(self, path: str) -> str:
        try:
            return self._paths[path]
        except (KeyError, TypeError):
            raise AnchorError('unknown_source') from None

    def source(self, source_id: str) -> Source:
        try:
            return self._sources[source_id]
        except (KeyError, TypeError):
            raise AnchorError('unknown_source') from None

    def model_source(self, source_id: str) -> dict:
        import json
        self.source(source_id)
        return json.loads(self._models[source_id])

    def resolve(self, source_id: str, anchor_id: str, *, catalogue_sha256: str) -> dict:
        if catalogue_sha256 != self.sha256:
            raise AnchorError('catalogue_changed')
        if not isinstance(source_id, str) or not isinstance(anchor_id, str):
            raise AnchorError('invalid_reference_type')
        try:
            anchor = self._anchors[(source_id, anchor_id)]
        except KeyError:
            raise AnchorError('unknown_or_blank_anchor') from None
        source = self.source(source_id)
        if not 0 <= anchor.start < anchor.end <= len(source.text) or digest(source.text) != source.sha256:
            raise AnchorError('source_or_range_changed')
        quote = source.text[anchor.start:anchor.end]
        binding = digest(canonical_json({'path': source.path, 'source_sha256': source.sha256,
            'start': anchor.start, 'end': anchor.end, 'quote_sha256': digest(quote)}))
        if digest(quote) != anchor.quote_sha256 or binding != anchor.binding_sha256 or not quote.strip():
            raise AnchorError('anchor_binding_changed')
        return {'source': source.path, 'quote': quote}

    def reference_at(self, source_id: str, offset: int) -> dict:
        """Trusted fixture/catalogue utility, never a model-provided offset."""
        if type(offset) is not int or offset < 0:
            raise AnchorError('invalid_character_offset')
        self.source(source_id)
        for pair, anchor in self._anchors.items():
            if pair[0] == source_id and anchor.start <= offset < anchor.end:
                return {'source_id': source_id, 'anchor_id': anchor.anchor_id}
        raise AnchorError('character_not_in_nonblank_anchor')

    def stats(self):
        return {'catalogue_sha256': self.sha256, 'snapshot_sha256': self.snapshot_sha256,
                'document_count': len(self.document_ids), 'anchor_count': len(self._anchors),
                'source_text_bytes': sum(len(r.text.encode()) for r in self._sources.values()),
                'model_calls': 0, 'semantic_correctness_proven': False}
