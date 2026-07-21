"""Unified backend registry for canonical Human-Adam workstreams.

The registry gives every catalog workstream one backend contract. Existing
Human-Adam and Knihovna services are preserved by reference through temporary
compatibility adapters; all other streams resolve lazily through the existing
private-thread factory.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Iterable

from app.codex_appserver import AppServerError
from app.communication.human_adam_workstream_catalog import (
    WORKSTREAM_CATALOG,
    CanonicalWorkstream,
    validate_workstream_catalog,
)


COMPATIBILITY_ADAPTER_BACKEND = "compatibility_adapter"
LAZY_PRIVATE_THREAD_BACKEND = "lazy_private_thread"
_PROFILE_ID_RE = re.compile(r"[a-z][a-z0-9_-]{1,31}")


@dataclass(frozen=True)
class CompatibilityWorkstreamAdapter:
    """Reference one existing persistent service without moving its state."""

    workstream_id: str
    profile_id: str
    service: Any


@dataclass(frozen=True)
class WorkstreamBackendBinding:
    record: CanonicalWorkstream
    backend: str
    compatibility_adapter: CompatibilityWorkstreamAdapter | None = None

    @property
    def profile_id(self) -> str:
        adapter = self.compatibility_adapter
        return adapter.profile_id if adapter is not None else ""


LazyServiceFactory = Callable[[str], Any]


class WorkstreamBackendRegistry:
    """Resolve metadata and service ownership from one canonical workstream ID."""

    def __init__(
        self,
        *,
        compatibility_adapters: Iterable[CompatibilityWorkstreamAdapter] = (),
        catalog: Iterable[CanonicalWorkstream] = WORKSTREAM_CATALOG,
    ) -> None:
        records = validate_workstream_catalog(catalog)
        by_id = {record.workstream_id: record for record in records}
        adapters: dict[str, CompatibilityWorkstreamAdapter] = {}
        profile_ids: set[str] = set()
        for adapter in compatibility_adapters:
            if not isinstance(adapter, CompatibilityWorkstreamAdapter):
                raise TypeError("Kompatibilní backend pracovního proudu není platný.")
            workstream_id = str(adapter.workstream_id or "").strip()
            profile_id = str(adapter.profile_id or "").strip()
            if workstream_id not in by_id:
                raise ValueError("Kompatibilní backend odkazuje na proud mimo katalog.")
            if workstream_id in adapters:
                raise ValueError("Pracovní proud má více kompatibilních backendů.")
            if not _PROFILE_ID_RE.fullmatch(profile_id) or profile_id in profile_ids:
                raise ValueError("Kompatibilní backend nemá jedinečný platný profil.")
            if getattr(adapter.service, "work_profile_id", None) != profile_id:
                raise ValueError("Kompatibilní backend neodkazuje na původní službu profilu.")
            adapters[workstream_id] = adapter
            profile_ids.add(profile_id)

        self._records = records
        self._by_id = by_id
        self._adapters = adapters
        self._workstream_by_profile = {
            adapter.profile_id: workstream_id
            for workstream_id, adapter in adapters.items()
        }

    def catalog(self) -> tuple[CanonicalWorkstream, ...]:
        return self._records

    def binding(self, workstream_id: str) -> WorkstreamBackendBinding:
        clean_id = str(workstream_id or "").strip().casefold()
        record = self._by_id.get(clean_id)
        if record is None:
            raise AppServerError("Požadovaný pracovní proud v katalogu neexistuje.")
        adapter = self._adapters.get(clean_id)
        return WorkstreamBackendBinding(
            record=record,
            backend=(
                COMPATIBILITY_ADAPTER_BACKEND
                if adapter is not None
                else LAZY_PRIVATE_THREAD_BACKEND
            ),
            compatibility_adapter=adapter,
        )

    def compatibility_profile_id(self, workstream_id: str) -> str:
        clean_id = str(workstream_id or "").strip().casefold()
        if clean_id not in self._by_id:
            raise AppServerError("Požadovaný pracovní proud není zaregistrovaný.")
        binding = self.binding(workstream_id)
        if binding.compatibility_adapter is None:
            raise AppServerError("Pracovní proud není kompatibilní profilový backend.")
        return binding.compatibility_adapter.profile_id

    def compatibility_workstream_id(self, profile_id: str) -> str:
        clean_id = str(profile_id or "").strip()
        workstream_id = self._workstream_by_profile.get(clean_id)
        if not workstream_id:
            raise AppServerError("Pracovní profil nemá kompatibilní pracovní proud.")
        return workstream_id

    def service(
        self,
        workstream_id: str,
        *,
        lazy_service_factory: LazyServiceFactory,
    ) -> Any:
        binding = self.binding(workstream_id)
        adapter = binding.compatibility_adapter
        if adapter is not None:
            return adapter.service
        service = lazy_service_factory(binding.record.workstream_id)
        if getattr(service, "work_profile_id", None) != binding.record.workstream_id:
            raise AppServerError("Lazy backend nevrátil službu požadovaného pracovního proudu.")
        return service
