from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

from app.shared_chat_runtime import make_hub


class RuntimeTests(unittest.TestCase):
    def test_operating_hub_keeps_existing_human_model_but_no_development_tools_or_state(self):
        client=Mock();client.__enter__=Mock(return_value=client);client.__exit__=Mock(return_value=False)
        client.read_effective_config.return_value={'mcp_servers':{'private-provider':{'token':'PRIVATE'}}}
        base=SimpleNamespace(workspace=SimpleNamespace(project_root=Path('/existing/human/workspace')),
            codex_binary='codex',_new_client=Mock(return_value=client),_local_delivery_receipt=Mock(),
            profile_getter=Mock(return_value={'model':'already-selected-model','reasoning_effort':'high'}))
        manager=SimpleNamespace(default_profile_id='human_adam',profiles={'human_adam':{'service':base}})
        with tempfile.TemporaryDirectory() as directory,patch('app.communication.human_adam_profiles.HUMAN_ADAM',manager):
            root=Path(directory);hub=make_hub(root)
            self.assertEqual(hub.model,'already-selected-model')
            self.assertEqual(hub.state_path,root/'session.json')
            self.assertEqual(hub.sandbox_policy,{'type':'readOnly','networkAccess':False})
            self.assertEqual(hub.config_overrides['mcp_servers'],{'private-provider':{'enabled':False}})
            self.assertFalse(any(hub.config_overrides['features'].values()))
            self.assertFalse((root/'session.json').exists())
            base._new_client.assert_called_once_with()


if __name__=='__main__':unittest.main()
