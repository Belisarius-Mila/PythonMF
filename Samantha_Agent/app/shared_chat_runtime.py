"""Lazy operating chat on the existing App Server; no development-profile mutation."""
from app.communication.session_hub import CanonicalSessionHub

INSTRUCTIONS = '''Jsi Samantha, osobní asistentka Míly. Odpovídej česky, tykej,
stručně a věcně. Toto je samostatný provozní rozhovor sdílený telefonem a monitorem.
První balíček podporuje textový rozhovor. Knihovna, kalendář, web a jejich akce
zatím nejsou připojené. Nikdy nepředstírej vyhledání, otevření, uložení ani provedení
akce. Nepoužívej nástroje, soubory, shell, síť ani jiné rozhovory. Řiď se pouze
obsahem tohoto rozhovoru. U nejasného dotazu se krátce doptej.'''


def make_hub(root):
    from app.communication.human_adam_profiles import HUMAN_ADAM
    base = HUMAN_ADAM.profiles[HUMAN_ADAM.default_profile_id]['service']
    # Reuse the user's existing human-chat model selection; no new role or candidate.
    profile = base.profile_getter(cwd=base.workspace.project_root,
        codex_binary=base.codex_binary, client_factory=base._new_client)
    with base._new_client() as client:
        config = client.read_effective_config(cwd=base.workspace.project_root)
    overrides = {'project_doc_max_bytes': 0, 'web_search': 'disabled',
        'features': {name: False for name in ('code_mode', 'code_mode_host', 'shell_tool',
            'unified_exec', 'computer_use', 'browser_use', 'browser_use_external', 'apps',
            'multi_agent', 'multi_agent_v2', 'image_generation', 'view_image', 'skill_search', 'memories')},
        'mcp_servers': {name: {'enabled': False} for name in (config.get('mcp_servers') or {})}}
    workspace = root / 'workspace'
    workspace.mkdir(parents=True, exist_ok=True, mode=0o700)
    return CanonicalSessionHub(state_path=root/'session.json', workspace=workspace,
        client_factory=base._new_client, developer_instructions=INSTRUCTIONS,
        sandbox='read-only', sandbox_policy={'type': 'readOnly', 'networkAccess': False},
        approval_policy='never', model=profile['model'], reasoning_effort=profile['reasoning_effort'],
        config_overrides=overrides, delivery_recovery_reader=base._local_delivery_receipt)
