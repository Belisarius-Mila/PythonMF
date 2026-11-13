"""Cached, redacted supervisor view. A GET cannot probe or change an agent."""
from app.agent_supervisor import AgentSupervisor


def agent_supervisor_overview(*, service=None):
    try:
        return (service or AgentSupervisor()).status()
    except Exception:
        return {"ok": False, "message": "Stav dohledu nelze ověřit; žádná služba nebyla změněna."}
