"""Terra-compatible model adapter over the existing local App Server socket."""

from __future__ import annotations

from functools import partial
import json
import tempfile
from pathlib import Path

from app.codex_appserver import CodexAppServerClient, UnixSocketAppServerTransport
from app.communication.local_runtime import DEFAULT_SOCKET_PATH
from .continuous_agent import EmailProposal, IMPORTANCE_PREFERENCE_INSTRUCTIONS
from .proposal_policy import PROPOSAL_INSTRUCTIONS, load_reply_name, proposal_payload, signed_draft


class CodexEmailProposer:
    def __init__(self, model: str, *, effort: str = "low", client_factory=None, reply_name: str | None = None):
        if not model.strip():
            raise ValueError("Model průběžného agenta musí být výslovně určený.")
        self.model, self.effort = model, effort
        self.reply_name = load_reply_name() if reply_name is None else reply_name
        self.client_factory = client_factory or partial(
            CodexAppServerClient, timeout=180,
            transport_factory=partial(UnixSocketAppServerTransport, socket_path=DEFAULT_SOCKET_PATH),
        )

    def __call__(self, observed) -> EmailProposal:
        source = proposal_payload(observed, self.reply_name)
        output_schema = EmailProposal.model_json_schema()
        # Structured output requires every property, including fields whose
        # local Pydantic defaults keep historical saved proposals compatible.
        output_schema["required"] = list(output_schema["properties"])
        instructions = PROPOSAL_INSTRUCTIONS + " " + IMPORTANCE_PREFERENCE_INSTRUCTIONS
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
        proposal = EmailProposal.model_validate_json(receipt.answer)
        proposal.reply_draft = signed_draft(proposal.reply_draft, self.reply_name)
        return proposal
