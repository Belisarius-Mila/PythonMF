"""Reviewed test ownership and cross-domain contracts, never caller-selected."""
from __future__ import annotations

import hashlib
from fnmatch import fnmatchcase
from functools import lru_cache
from pathlib import Path

LOADED_SOURCE_HASH = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

CORE_TESTS = ("tests.test_cockpit_http_security", "tests.test_cockpit_server",
              "tests.test_file_persistence", "tests.test_capability_runtime_policy",
              "tests.test_cockpit_frontend")

# Full regression is a separate nightly/manual operation. Runtime selection
# expands domain/consumer contracts; it never selects the whole registry.
SOURCES = {
    "vocabulary_fr_content": ("VocabularyFR/vocabulary_fr_*.py", "VocabularyFR/build_sentence_pictures.py"),
    "validation": ("app/communication/validation_*.py", "app/communication/checkpoint_quality_gate.py",
                   "scripts/*quality_gate*.py", "scripts/validation_*.py", "AGENTS.md",
                   "scripts/cockpit_fast_feedback.py", "memory/technical/validation_policy.md", ".github/workflows/*"),
    "release": ("app/communication/github_batch.py", "app/communication/luna_release*.py",
                "app/communication/simple_main_*.py", "app/communication/human_adam_workspace.py",
                "app/communication/main_remote_sync.py", "app/communication/agent_roles.py",
                "app/communication/git_runtime.py",
                "config/agent_roles.json"),
    "persistence": ("app/file_persistence.py", "app/work_repository.py", "app/document_tools.py",
                    "app/documents/transactions.py"),
    "backup": ("app/backup/*.py", "scripts/backup*.py"),
    "housekeeping": ("app/worktree_cleanup.py", "scripts/workspace_housekeeping.py",
                     "app/autosave_service.py", "scripts/autosave_*.py", "scripts/cleanup_session_autosave.py"),
    "vocabulary_content": ("VocabularyEN/VocabularyEN.csv", "VocabularyEN/vocabulary_en_catalog.json",
                           "VocabularyEN/Pict/*.png", "VocabularyEN/Pict/*.webp", "VocabularyEN/Pict/*.jpg",
                           "docs/assets/vocabulary-en/*.png", "docs/assets/vocabulary-en/*.webp",
                           "docs/assets/vocabulary-en/*.jpg", "docs/assets/vocabulary-en-thumbs/*.webp",
                           "docs/assets/vocabulary-en-audio/*/*.mp3", "docs/assets/vocabulary-en-sentences/*/*.mp3",
                           "docs/data/vocabulary-en*.json", "tests/test_vocabularyen_selection.js",
                           "tests/test_vocabularyen_learners.js"),
    "vocabulary_it": ("VocabularyIT/vocabulary_it_*.py", "VocabularyIT/vocabulary_it_*.json",
                      "PictNew/generated/*_it_web_review/*", "docs/data/vocabulary-it-v2.json",
                      "Pict/it_web_vit_*.webp", "docs/vocabulary-it/*",
                      "docs/data/vocabulary-it-audio.json", "docs/data/vocabulary-it-sentence-audio.json",
                      "docs/data/vocabulary-it-quiz.json",
                      "docs/assets/vocabulary-it-audio/*/*.mp3", "docs/assets/vocabulary-it-sentences/*/*.mp3",
                      "tests/test_vocabularyit_selection.js",
                      "docs/assets/vocabulary-it-v2/*/*.webp",
                      "VocabularyIT/VocabularyIT.csv", "VocabularyIT/VerbeIT.csv", "VocabularyIT/IT_Pict.csv"),
    "vocabulary_fr": ("app/vocabulary_fr_multiplayer.py", "app/vocabulary_fr_hosting.py", "app/vocabulary_fr_cloud.py", "deploy/vocabulary-fr/*", "docs/vocabulary-fr/*", "tests/test_vocabularyfr_hosting.py", "tests/test_vocabularyfr_cloud.py", "tests/test_vocabularyfr_online.js", "tests/test_vocabularyfr_multiplayer.py", "tests/test_vocabularyfr_selection.js",
                      "tests/fixtures/vocabulary_fr_*.js"),
    "calendar": ("app/calendar_*.py", "app/cockpit_calendar*.py", "app/cockpit_email_calendar.py",
                 "app/email/calendar_*.py", "scripts/calendar_*.py", "scripts/calendar_*.swift",
                 "app/frontend/calendar_overview/*", "app/frontend/calendar_task/*",
                 "app/frontend/shared/calendar_actions.js",
                 "app/frontend/email_agent/calendar_*.js", "tests/calendar_*.swift",
                 "tests/*calendar*frontend.test.cjs", "tests/calendar_actions_frontend.test.cjs",
                 "memory/technical/calendar_all_day_boundaries.md"),
    "library": ("app/book_*.py", "app/library_*.py", "app/cockpit_book_*.py", "app/article_archive.py",
                "app/frontend/cockpit/library_*.js", "tests/book_*.test.cjs"),
    "shared_chat": ("app/shared_chat.py", "app/shared_chat_runtime.py", "app/shared_chat_library.py", "app/cockpit_shared_chat.py",
                    "app/frontend/samantha_chat/*", "tests/shared_chat_*.test.cjs"),
    "frontend": ("app/frontend/cockpit/styles.css", "app/frontend/cockpit/service-worker.js"),
    "email_followups": ("app/email/followup*.py", "app/cockpit_email_followups.py",
                        "app/frontend/email_agent/followups*.js", "tests/email_followups_frontend.test.cjs"),
    "email_agent": ("app/email/continuous_*.py", "app/email/proposal_policy.py",
                    "app/cockpit_email_agent.py",
                    "app/frontend/email_agent/app.js", "tests/email_agent_frontend.test.cjs"),
    "interior": ("app/interior_*.py", "app/cockpit_interior.py", "app/frontend/interior/*",
                 "tests/interior_*.test.cjs"),
    "science": ("app/science_news*.py", "app/cockpit_science_news.py", "scripts/science_news*.py",
                "tests/science_news*.test.cjs"),
    "vocabulary": ("app/vocabulary*.py", "VocabularyEN/*.py", "tests/vocabulary*.test.cjs", "docs/vocabulary-en/*"),
    "camino_film": ("app/camino_film*.py", "app/camino_mac_film*.py", "scripts/camino_film*.py",
                    "scripts/camino_mac_film*.py", "tests/camino_film*.test.cjs"),
    "documents": ("app/documents/*.py", "app/email/archive_browser.py", "app/cockpit_document*.py",
                  "app/cockpit_email_archive_routes.py"),
    "human_adam_ui": ("app/communication/human_adam_ui.py", "tests/human_adam*frontend.test.cjs",
                      "tests/human_adam_send_frontend.test.cjs", "tests/luna_release_frontend.test.cjs"),
    "mmtx": ("app/mmtx*.py", "tests/mmtx*.test.cjs", "docs/mmtx/*"),
}

TEST_PREFIXES = {
    "vocabulary_fr_content": ("tests.test_vocabularyfr_content",),
    "validation": ("tests.test_validation_", "tests.test_cockpit_quality_gate", "tests.test_cockpit_fast_feedback", "tests.test_github_batch",
                   "tests.test_luna_release_submission", "tests.test_simple_main_deploy",
                   "tests.test_simple_main_checkpoint"),
    "release": ("tests.test_github_batch", "tests.test_luna_release", "tests.test_simple_main_",
                "tests.test_human_adam_workspace", "tests.test_main_remote_sync", "tests.test_agent_roles"),
    "persistence": ("tests.test_file_persistence", "tests.test_work_repository", "tests.test_document_persistence",
                    "tests.test_document_transactions", "tests.test_email_work_repository"),
    "backup": ("tests.test_backup_",),
    "housekeeping": ("tests.test_worktree_cleanup", "tests.test_autosave_continuity", "tests.test_workflow_commands"),
    "vocabulary_content": ("tests.test_vocabularyen_gallery", "tests.test_vocabularyen_audio_library"),
    "vocabulary_it": ("tests.test_vocabularyit_catalog", "tests.test_vocabularyit_export", "tests.test_vocabularyit_gallery", "tests.test_vocabularyit_audio"),
    "vocabulary_fr": ("tests.test_vocabularyfr_web_gallery", "tests.test_vocabularyfr_multiplayer", "tests.test_vocabularyfr_hosting", "tests.test_vocabularyfr_cloud"),
    "calendar": ("tests.test_calendar_", "tests.test_cockpit_calendar", "tests.test_email_calendar_",
                 "tests.test_cockpit_email_calendar"),
    "library": ("tests.test_book_", "tests.test_cockpit_book_", "tests.test_library_", "tests.test_article_archive"),
    "shared_chat": ("tests.test_shared_chat",),
    "frontend": ("tests.test_cockpit_pwa", "tests.test_article_archive", "tests.test_book_cover",
                 "tests.test_library_photos"),
    "email_followups": ("tests.test_email_followup", "tests.test_cockpit_email_followup"),
    "email_agent": ("tests.test_continuous_email_agent", "tests.test_email_proposal_policy",
                    "tests.test_email_visibility_preferences", "tests.test_cockpit_email_agent",
                    "tests.test_hourly_email_agent", "tests.test_email_calendar_assessment"),
    "interior": ("tests.test_interior_", "tests.test_cockpit_interior"),
    "science": ("tests.test_science_news",),
    "vocabulary": ("tests.test_vocabulary_authoring",),
    "camino_film": ("tests.test_camino_film", "tests.test_camino_mac_film"),
    "documents": ("tests.test_document_", "tests.test_email_archive_browser"),
    "human_adam_ui": ("tests.test_human_adam_ui", "tests.test_workstream_live_status"),
    "mmtx": ("tests.test_mmtx_",),
}

# Composition/read-only adapter boundaries have explicit consumer contracts.
# Stop traversal here; a change TO the adapter itself is not exempted.
BOUNDARY_TESTS = {
    "app.cockpit": (),
    "app.cockpit_frontend": (),
    "app.main": ("tests.test_capability_registry",),
    "app.email.codex_proposer": ("tests.test_agent_reply", "tests.test_hourly_email_agent"),
    "app.agent_supervisor_probes": ("tests.test_agent_supervisor", "tests.test_agent_supervisor_sleep"),
    "app.interior_ai_activation": ("tests.test_interior_ai_activation",),
}

# Shared primitives are checked through their contract suites instead of every
# transitive consumer. Nightly regression checks the remaining combinations.
CONTRACT_SCOPES = frozenset({'validation', 'release', 'persistence', 'backup'})
FALLBACK_TESTS = (*CORE_TESTS, 'tests.test_capability_registry', 'tests.test_cockpit_quality_gate')


def modules_for_scopes(scopes, registry):
    if 'vocabulary' in scopes:
        scopes = set(scopes) | {'vocabulary_content'}
    return {name for scope in scopes for name in registry if name.startswith(TEST_PREFIXES[scope])}


def _matches(path: str, pattern: str) -> bool:
    # A single wildcard never grants ownership of an unknown subdirectory.
    names, patterns = path.split('/'), pattern.split('/')
    return len(names) == len(patterns) and all(fnmatchcase(n, p) for n, p in zip(names, patterns))


@lru_cache(maxsize=16384)
def source_scopes(path: str) -> frozenset[str]:
    return frozenset(name for name, patterns in SOURCES.items()
                     if any(_matches(path, pattern) for pattern in patterns))


def scopes_for_path(path: str, registry) -> frozenset[str]:
    if path.startswith("tests/") and path.endswith(".py"):
        module = path[:-3].replace("/", ".")
        if module not in registry:
            return frozenset()
        return frozenset(scope for scope, prefixes in TEST_PREFIXES.items() if module.startswith(prefixes))
    return source_scopes(path)
