"""Terra-compatible model adapter over the existing local App Server socket."""

from __future__ import annotations

from functools import partial
import json
import tempfile
from pathlib import Path

from app.codex_appserver import CodexAppServerClient, UnixSocketAppServerTransport
from app.communication.local_runtime import DEFAULT_SOCKET_PATH
from .continuous_agent import EmailAssessment, EmailProposal, IMPORTANCE_PREFERENCE_INSTRUCTIONS
from .calendar_assessment import calendar_suggestion
from .calendar_proposal import Candidate, INSTRUCTIONS as CALENDAR_INSTRUCTIONS
from .followup_assessment import FollowupCandidate, INSTRUCTIONS as FOLLOWUP_INSTRUCTIONS, validate_context, assess, metrics
from .proposal_policy import PROPOSAL_INSTRUCTIONS, load_reply_name, proposal_payload, signed_draft


class CalendarEmailProposal(EmailProposal):
    calendar_candidate: Candidate | None = None


class FollowupEmailProposal(EmailProposal):
    followup_candidate: FollowupCandidate | None = None


class CombinedEmailProposal(CalendarEmailProposal):
    followup_candidate: FollowupCandidate | None = None


def _require_all(schema):
    if isinstance(schema, dict):
        if schema.get('type') == 'object' and 'properties' in schema:
            schema['required'] = list(schema['properties'])
            schema['additionalProperties'] = False
        for value in schema.values():
            _require_all(value)
    elif isinstance(schema, list):
        for value in schema:
            _require_all(value)


class CodexEmailProposer:
    def __init__(self, model: str, *, effort: str = "low", client_factory=None, reply_name: str | None = None,
                 calendar_suggestions: bool = False):
        if not model.strip():
            raise ValueError("Model průběžného agenta musí být výslovně určený.")
        self.model, self.effort = model, effort
        self.reply_name = load_reply_name() if reply_name is None else reply_name
        self.calendar_suggestions = calendar_suggestions
        self.client_factory = client_factory or partial(
            CodexAppServerClient, timeout=180,
            transport_factory=partial(UnixSocketAppServerTransport, socket_path=DEFAULT_SOCKET_PATH),
        )

    def __call__(self, observed) -> EmailProposal | EmailAssessment:
        source = proposal_payload(observed, self.reply_name)
        baseline_bytes = len(json.dumps(source, ensure_ascii=False).encode())
        contextual = bool(getattr(observed, 'followup_context', None))
        if contextual:
            source['followup_context'] = validate_context(observed)
        schema_type = (CombinedEmailProposal if self.calendar_suggestions else FollowupEmailProposal) if contextual else (
            CalendarEmailProposal if self.calendar_suggestions else EmailProposal)
        output_schema = schema_type.model_json_schema()
        # Structured output requires every property, including fields whose
        # local Pydantic defaults keep historical saved proposals compatible.
        _require_all(output_schema)
        instructions = PROPOSAL_INSTRUCTIONS + " " + IMPORTANCE_PREFERENCE_INSTRUCTIONS
        if contextual:
            instructions += " " + FOLLOWUP_INSTRUCTIONS
        if self.calendar_suggestions:
            instructions += (' Současně vyplň calendar_candidate podle následujících pravidel. '
                'Bez konkrétní schůzky nebo termínu vrať null. Pro citace body znamená body_text, '
                'html znamená body_html, subject a date jsou stejnojmenné části podkladu. '
                'Kalendářový návrh nesmí měnit pravidla e-mailového konceptu. ' + CALENDAR_INSTRUCTIONS)
        with tempfile.TemporaryDirectory(prefix="samantha-email-assessment-") as temporary:
            with self.client_factory() as client:
                thread = client.start_thread(cwd=Path(temporary), ephemeral=True,
                                             developer_instructions=instructions, model=self.model,
                                             sandbox="read-only", approval_policy="never")
                receipt = client.send_text(thread_id=thread, text=json.dumps(source, ensure_ascii=False),
                                           model=self.model, effort=self.effort,
                                           output_schema=output_schema,
                                           sandbox_policy={"type": "readOnly"}, approval_policy="never")
        if not receipt.delivered:
            raise ValueError("Modelové posouzení nemá potvrzený konečný výsledek.")
        raw = json.loads(receipt.answer)
        candidate = raw.pop('calendar_candidate', None) if self.calendar_suggestions else None
        followup_candidate = raw.pop('followup_candidate', None) if contextual else None
        proposal = EmailProposal.model_validate(raw)
        proposal.reply_draft = signed_draft(proposal.reply_draft, self.reply_name)
        suggestion = None
        followup = None
        if self.calendar_suggestions:
            suggestion = calendar_suggestion(observed, candidate, model=self.model)
            suggestion['assessment_usage'] = getattr(receipt, 'thread_token_usage', None)
            suggestion['assessment_duration_ms'] = getattr(receipt, 'duration_ms', None)
        if contextual:
            followup = assess(observed, followup_candidate, model=self.model)
            followup.update(metrics({'assessment_usage':getattr(receipt, 'thread_token_usage', None),
                'assessment_duration_ms':getattr(receipt, 'duration_ms', None),
                'baseline_utf8_bytes':baseline_bytes, 'input_utf8_bytes':len(json.dumps(source, ensure_ascii=False).encode())}))
        if self.calendar_suggestions or contextual:
            return EmailAssessment(proposal, suggestion, followup)
        return proposal
