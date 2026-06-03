from .activity_state import (
    BACKUP_WARNING_DAYS,
    DEFAULT_BACKUP_ACTIVITY_STATE_PATH,
    BackupActivityState,
    format_backup_activity_reminder,
    load_backup_activity_state,
    record_backup_completed,
    save_backup_activity_state,
)

_LAZY_EXPORTS = {
    "list_backup_snapshots": ("app.backup.restore_tools", "list_backup_snapshots"),
    "preview_backup_restore": ("app.backup.restore_tools", "preview_backup_restore"),
    "restore_path_from_backup": ("app.backup.restore_tools", "restore_path_from_backup"),
    "run_project_backup": ("app.backup.run_tools", "run_project_backup"),
    "run_project_backup_text": ("app.backup.run_tools", "run_project_backup_text"),
}


def __getattr__(name: str):
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _LAZY_EXPORTS[name]
    from importlib import import_module

    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value

__all__ = [
    "BACKUP_WARNING_DAYS",
    "DEFAULT_BACKUP_ACTIVITY_STATE_PATH",
    "BackupActivityState",
    "format_backup_activity_reminder",
    "load_backup_activity_state",
    "record_backup_completed",
    "save_backup_activity_state",
    "list_backup_snapshots",
    "preview_backup_restore",
    "restore_path_from_backup",
    "run_project_backup",
    "run_project_backup_text",
]
