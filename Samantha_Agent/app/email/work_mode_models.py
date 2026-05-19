from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WorkMode:
    case_id: str
    case_record: dict[str, Any]
    vault_directory: Path


@dataclass(frozen=True)
class WorkModeActionPlan:
    available_actions: tuple[str, ...]
    requires_confirmation: tuple[str, ...]
