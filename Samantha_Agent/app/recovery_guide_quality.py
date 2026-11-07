"""REC-03: deterministic evidence gates and a separate cold-reader dossier.

Never executes commands, reads devices or grants publication. Context/facts
must come from the trusted controller/operator, never from model output.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import re
from typing import Any

from app.recovery_guide_sources import Snapshot, canonical_json, digest, reject_secrets

VALIDATOR_VERSION = 1  # Bump when acceptance rules change after this release.

HEAD = re.compile(r"(?m)^(\d{1,2})\. ([^\n]+)$")
LITERAL = re.compile(r"https?://[^\s`<>\"']+|(?:~/|/|\$[A-Z_]+/|\.(?:venv|env)/|(?:app|scripts|config|memory)/)[\w./~$:-]+|\bgpt-[\w.:-]+")
SHELL = re.compile(r"(?m)^\s*(?:\$\s+(.+)|```(?:bash|sh|zsh)\s*\n([\s\S]*?)\n```)")
COMMAND = re.compile(r"(?:^\s*|`|\b(?i:spusť|proveď|příkaz:)\s+)((?:sudo|python[\d.]*|\.venv/bin/python|brew|git|launchctl|rm|curl|ssh|tailscale|rsync|chmod|chown|xcodebuild|security|pip[\d.]*|npm|node)\b[^\n`]+)", re.M)
RETIRED = re.compile(r"read_only_voice|readOnlyVoice|voice[_-]bridge|/api/voice", re.I)
LIVE = re.compile(r"\b(?:dnes|právě|čerstvě|aktuálně|živě).{0,40}(?:ověřen|nasazen|otestován)|"
                  r"\b(?:ověřen|nasazen|otestován)[\w ]{0,25}\b(?:dnes|právě)|"
                  r"\b(?:ověřen|otestován)[\w ]{0,25}(?:iPhon|telefon)|"
                  r"(?:iPhon|telefon).{0,25}\b(?:ověřen|otestován)|HTTP\s+200|uploaded\s*=\s*true", re.I)
ASSIGNMENT = re.compile(r"(?im)\b(?:api[_ -]?key|password|passwd|heslo|token|secret)['\"]?\s*[:=]\s*['\"]?([\w+/.=-]{8,})")
PLACEHOLDERS = {"placeholder", "redacted", "neukladat", "neuvádět", "your_api_key", "example_value"}
FIELDS = ("purpose", "requirement", "installation", "version", "configuration", "data", "sign_in",
          "permissions", "start", "verification", "mac_connection", "iphone_installation",
          "iphone_permissions", "iphone_verification")
TOPICS = {
    "python": ("python",), "environment": (".venv", "virtuální prostředí"),
    "codex": ("codex",), "app_server": ("app server", "app-server"),
    "roles": ("agent_roles.json",), "cockpit": ("cockpit",), "launchd": ("launchd",),
    "path": ("path",), "tailscale": ("tailscale",), "https": ("https",),
    "backup": ("záloh",), "outside_git": ("mimo git",), "camino": ("camino",),
    "xcode": ("xcode",), "signing": ("podpis",), "installation": ("instal",),
    "iphone": ("iphone",), "icloud": ("icloud",), "permissions": ("oprávněn",),
    "sign_in": ("přihláš",),
}


class QualityError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)  # Safe code only: never put rejected content in logs.


@dataclass(frozen=True)
class SourceFact:
    path: str
    sha256: str
    authority: str  # documented, historical, proposed, deployed, manual_verified
    observed_on: str
    quote_sha256: str | None = None  # Required for a live/manual proof packet.


@dataclass(frozen=True)
class ReviewContext:
    snapshot_sha256: str
    checked_on: date
    facts: tuple[SourceFact, ...] = ()
    workflows: tuple[tuple[str, str], ...] = ()  # approved command ID -> exact literal
    applications: tuple[str, ...] = ()  # Explicit complete inventory, not guessed defaults.
    application_scope_approved: bool = False
    macos_expected: str | None = None
    macos_observed: str | None = None
    unresolved_conflicts: tuple[str, ...] = ()
    max_age_days: int = 90


def _fail(condition: bool, code: str) -> None:
    if condition:
        raise QualityError(code)


def safe_text(text: str) -> None:
    _fail(not isinstance(text, str), "invalid_text")
    try:
        text.encode("utf-8", errors="strict")
        reject_secrets(text)
    except (UnicodeError, ValueError) as exc:
        raise QualityError("unsafe_text") from exc
    _fail(any(ord(c) < 32 and c not in "\n\r\t" for c in text)
          or any(c in text for c in "\u202a\u202b\u202d\u202e\u2066\u2067\u2068\u2069"), "hidden_control")
    for match in ASSIGNMENT.finditer(text):
        value = match.group(1).casefold()
        _fail(value not in PLACEHOLDERS and not value.startswith(("your_", "example_", "redacted")), "credential_assignment")


def _sources(snapshot: Snapshot) -> dict:
    sources = (snapshot.original, *snapshot.sources)
    _fail(len({s.path for s in sources}) != len(sources), "duplicate_source")
    for source in sources:
        _fail(digest(source.text) != source.sha256, "source_hash_mismatch")
    return {s.path: s for s in sources}


def _headings(text: str) -> list:
    return [m for m in HEAD.finditer(text) if m[2] == m[2].upper() and any(c.isalpha() for c in m[2])]


def anchors(evidence: list, sources: dict) -> list[dict]:
    result = []
    for row in evidence:
        _fail(not isinstance(row, dict) or set(row) != {"source", "quote"}, "invalid_citation")
        name, quote = row["source"], row["quote"]
        _fail(not isinstance(name, str) or name not in sources or not isinstance(quote, str)
              or not quote.strip() or quote not in sources[name].text, "unsupported_citation")
        safe_text(quote)
        source = sources[name]
        start = source.text.index(quote)
        line = source.text[:start].count("\n") + 1
        result.append({"source": name, "source_sha256": source.sha256, "line_start": line,
                       "line_end": line + quote.count("\n"), "quote_sha256": digest(quote),
                       "occurrences": source.text.count(quote), "authority": source.authority})
    return result


def _fact(name: str, context: ReviewContext, sources: dict, quote: str) -> SourceFact:
    matches = [f for f in context.facts if f.path == name]
    _fail(len(matches) != 1, "missing_or_duplicate_source_fact")
    fact = matches[0]
    _fail(fact.sha256 != sources[name].sha256, "fact_hash_mismatch")
    _fail(fact.authority not in {"documented", "historical", "proposed", "deployed", "manual_verified"}, "invalid_authority")
    try:
        observed = date.fromisoformat(fact.observed_on)
    except (ValueError, TypeError) as exc:
        raise QualityError("invalid_evidence_date") from exc
    age = (context.checked_on - observed).days
    _fail(age < 0, "future_evidence")
    _fail(age > context.max_age_days, "stale_evidence")
    _fail(fact.authority in {"manual_verified", "deployed"} and fact.quote_sha256 != digest(quote), "live_evidence_anchor_mismatch")
    return fact


def _literals(text: str) -> set[str]:
    return {m[0].rstrip(".,:;)") for m in LITERAL.finditer(text)}


def _technical(text: str, quotes: str, context: ReviewContext | None) -> None:
    _fail(not _literals(text).issubset(_literals(quotes)), "uncited_technical_literal")
    commands = {m[1].strip() for m in COMMAND.finditer(text)}
    for match in SHELL.finditer(text):
        commands.update(line.strip() for line in (match[1] or match[2]).splitlines()
                        if line.strip() and not line.strip().startswith("#"))
    for command in commands:
        _fail(context is None or command not in dict(context.workflows).values(), "unregistered_command")
        _fail(command not in quotes, "uncited_command")


def validate(answer: dict, snapshot: Snapshot, *, context: ReviewContext | None = None) -> str:
    """Mandatory core gate used by the pilot, including unchanged sections.

    Technical literals must be in the cited quote, not merely somewhere in a
    large document. Full semantic correctness still needs independent review.
    """
    sources = _sources(snapshot)
    if context is not None:
        _fail(context.snapshot_sha256 != snapshot.sha256, "review_snapshot_changed")
    _fail(not isinstance(answer, dict) or set(answer) != {"paragraphs"}, "invalid_answer")
    rows = answer["paragraphs"]
    _fail(not isinstance(rows, list) or not rows, "empty_guide")
    for row in rows:
        _fail(not isinstance(row, dict) or set(row) != {"text", "status", "evidence"}, "invalid_paragraph")
        text, status, evidence = row["text"], row["status"], row["evidence"]
        safe_text(text)
        _fail(not text.strip() or not isinstance(status, str) or status not in {"unchanged", "documented", "unverified"}
              or not isinstance(evidence, list), "invalid_paragraph")
        _fail(status == "unchanged" and text not in snapshot.original.text, "false_unchanged")
        _fail(status != "unchanged" and not evidence, "missing_evidence")
        anchors(evidence, sources)
        if status != "unchanged":
            _fail(bool(RETIRED.search(text)), "retired_voice_reference")
            quotes = "\n".join(e["quote"] for e in evidence)
            _technical(text, quotes, context)
            _fail(status == "documented" and all(sources[e["source"]].authority in
                  {"historical_or_mixed", "previous_version", "historical", "proposed"} for e in evidence), "history_as_current")
            if LIVE.search(text):
                _fail(context is None, "unproven_live_claim")
                proven = False
                for e in evidence:
                    fact = _fact(e["source"], context, sources, e["quote"])
                    proven |= fact.authority in {"manual_verified", "deployed"} and text in e["quote"]
                _fail(not proven, "unproven_live_claim")
    candidate = "\n\n".join(("[Neověřeno]\n" if r["status"] == "unverified" else "") + r["text"] for r in rows) + "\n"
    _fail(bool(RETIRED.search(candidate)) or bool(re.search(r"(?:spusť|zapni|nasaď|povol).{0,40}placen[ýého\s]+hlasov", candidate, re.I)), "retired_voice_reference")
    original_heads, new_heads = _headings(snapshot.original.text), _headings(candidate)
    _fail(not original_heads, "missing_original_structure")
    _fail(len({m[1] for m in new_heads}) != len(new_heads), "duplicate_chapter")
    positions = []
    for i, old in enumerate(original_heads):
        found = [(j, m) for j, m in enumerate(new_heads) if m[0] == old[0]]
        _fail(len(found) != 1, "missing_chapter")
        j, new = found[0]
        positions.append(j)
        before = snapshot.original.text[old.end():original_heads[i+1].start() if i+1 < len(original_heads) else None]
        after = candidate[new.end():new_heads[j+1].start() if j+1 < len(new_heads) else None]
        _fail(len(after.strip()) < len(before.strip()) * .75, "chapter_content_lost")
    _fail(positions != sorted(positions), "reordered_chapters")
    _fail(len(candidate) < len(snapshot.original.text) * .75, "guide_content_lost")
    before = snapshot.original.text[:original_heads[0].start()].strip()
    after = candidate[:new_heads[0].start()].strip()
    _fail(len(after) < len(before) * .75, "preface_lost")
    if all(r["status"] == "unchanged" for r in rows) and candidate.strip("\n") == snapshot.original.text.strip("\n"):
        return snapshot.original.text  # No synthetic newline/version change.
    dates = r"\b(?:20\d{2}-\d{2}-\d{2}|\d{1,2}\.\s*\d{1,2}\.\s*20\d{2})\b"
    _fail(candidate.strip() != snapshot.original.text.strip()
          and re.sub(dates, "<DATE>", candidate).strip() == re.sub(dates, "<DATE>", snapshot.original.text).strip(), "date_only_change")
    return candidate


def review(answer: dict, snapshot: Snapshot, dossier: dict, context: ReviewContext) -> dict:
    """Complete REC-03 checklist; only returns review/blocked, never approval."""
    result: dict[str, Any] = {"schema_version": 1, "validator_version": VALIDATOR_VERSION,
        "state": "blocked", "snapshot_sha256": snapshot.sha256,
        "context_sha256": digest(canonical_json(asdict(context) | {"checked_on": context.checked_on.isoformat()})),
        "publication_authorized": False, "semantic_review_required": True, "issues": [], "anchors": []}
    try:
        _fail(context.snapshot_sha256 != snapshot.sha256, "review_snapshot_changed")
        _fail(type(context.max_age_days) is not int or context.max_age_days <= 0, "invalid_freshness_policy")
        _fail(bool(context.unresolved_conflicts), "unresolved_recovery_conflict")
        candidate = validate(answer, snapshot, context=context)
        result["candidate_sha256"] = digest(candidate)
        _fail(context.application_scope_approved is not True or not context.applications, "application_scope_unapproved")
        for name, alternatives in TOPICS.items():
            if not any(word in candidate.casefold() for word in alternatives):
                result["issues"].append({"code": "missing_topic", "field": name})
        _fail(not context.macos_expected or not context.macos_observed, "macos_baseline_unverified")
        _fail(context.macos_expected != context.macos_observed, "new_macos_requires_review")
        _fail(not isinstance(dossier, dict) or set(dossier) != {"applications"}
              or not isinstance(dossier["applications"], list), "invalid_application_dossier")
        apps = dossier["applications"]
        _fail(any(not isinstance(a, dict) or set(a) != {"name", "fields"} for a in apps), "invalid_application")
        names = [a["name"] for a in apps]
        _fail(any(not isinstance(n, str) for n in names) or len(set(names)) != len(names), "duplicate_application")
        _fail(set(names) != set(context.applications), "application_coverage")
        sources = _sources(snapshot)
        for row in answer["paragraphs"]:
            result["anchors"].extend(anchors(row["evidence"], sources))
            for evidence in row["evidence"]:
                fact = _fact(evidence["source"], context, sources, evidence["quote"])
                _fail(row["status"] == "documented" and fact.authority in {"historical", "proposed"}, "history_as_current")
        for app in apps:
            fields = app["fields"]
            _fail(not isinstance(fields, dict) or set(fields) != set(FIELDS), "application_fields_missing")
            for name, field in fields.items():
                _fail(not isinstance(field, dict) or set(field) != {"value", "status", "source", "quote", "observed_on"}, "invalid_application_field")
                safe_text(field["value"])
                _fail(not field["value"].strip(), "empty_application_field")
                status = field["status"]
                _fail(not isinstance(status, str) or status not in {"documented", "manual_verified", "unverified", "not_applicable"}, "invalid_field_status")
                if status == "unverified":
                    _fail(field["value"] != "neověřeno" or any(field[k] is not None for k in ("source", "quote", "observed_on")), "false_unverified")
                    continue
                evidence = {"source": field["source"], "quote": field["quote"]}
                result["anchors"].extend(anchors([evidence], sources))
                fact = _fact(field["source"], context, sources, field["quote"])
                _fail(field["observed_on"] != fact.observed_on, "evidence_date_mismatch")
                _fail(field["value"] not in field["quote"], "unsupported_application_value")
                _fail(bool(RETIRED.search(field["value"])), "retired_voice_reference")
                _technical(field["value"], field["quote"], context)
                sentences = re.split(r"(?<=[.!?])\s+", field["quote"])
                _fail(not any(re.search(r"(?<!\w)" + re.escape(app["name"]) + r"(?!\w)", sentence, re.I)
                              and field["value"] in sentence for sentence in sentences), "application_not_in_evidence")
                _fail(fact.authority in {"historical", "proposed"}, "history_as_current")
                _fail(bool(LIVE.search(field["value"])) and fact.authority not in {"manual_verified", "deployed"}, "unproven_live_claim")
                _fail(status == "manual_verified" and fact.authority != "manual_verified", "phone_proof_not_manual")
        result["dossier_sha256"] = digest(canonical_json(dossier))
        result["state"] = "blocked" if result["issues"] else "review"
    except QualityError as exc:
        result["issues"].append({"code": exc.code})
    return result


def cold_reader_bundle(answer: dict, snapshot: Snapshot, dossier: dict, context: ReviewContext) -> dict:
    checked = review(answer, snapshot, dossier, context)
    _fail(checked["state"] != "review", "cold_reader_gate_blocked")
    import json
    return {"guide": validate(answer, snapshot, context=context), "application_dossier": json.loads(canonical_json(dossier)),
            "quality_receipt": checked, "private_history_included": False, "reader_test_executed": False,
            "instructions": "Použij pouze tento návod. Nic neinstaluj ani nespouštěj. Označ chybějící kroky, nejasná nastavení a nedoložené přístupy. Ruční neověřené údaje nepovažuj za aktuální měření."}
