"""FR client contract: synthetic tests only, never reads Jana's private data."""
from pathlib import Path
import subprocess
import unittest
from scripts.cockpit_quality_gate import node_binary

ROOT=Path(__file__).resolve().parents[2]
CLIENT=ROOT/'docs/vocabulary-fr'


class VocabularyFrenchWebGalleryTests(unittest.TestCase):
    def test_real_frontend_against_synthetic_data_including_partial_audio(self):
        result=subprocess.run([node_binary(),'--test',str(Path(__file__).with_name('test_vocabularyfr_selection.js'))],cwd=ROOT/'Samantha_Agent',capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
        self.assertIn('fail 0',result.stdout)

    def test_client_is_self_contained_and_keeps_language_and_storage_separate(self):
        html=(CLIENT/'index.html').read_text()
        for name in ('model.js','learners.js','learner-ui.js','practice.js','personal.js','personal-ui.js','memory.js','gallery.js','gallery.css'):
            self.assertIn(name,html)
            self.assertTrue((CLIENT/name).is_file())
        self.assertIn('lang="fr"',html)
        self.assertIn('speakCzechButton',html)
        css=(CLIENT/'gallery.css').read_text()
        self.assertIn('repeat(2,minmax(0,1fr))',css)
        for name in ('index.html','model.js','gallery.js','learners.js','learner-ui.js','practice.js','memory.js'):
            content=(CLIENT/name).read_text()
            for foreign in ('vocabulary-it','vocabulary-en','VocabularyIT','vit-','speechSynthesis'):
                self.assertNotIn(foreign,content,name)
        self.assertIn('vocabulary-fr.navigation.v1',(CLIENT/'gallery.js').read_text())
        self.assertIn('vocabulary-fr.learner-backup',(CLIENT/'learners.js').read_text())

    def test_private_payload_does_not_advertise_unavailable_public_app(self):
        from app import cockpit
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        with TemporaryDirectory() as directory, patch.object(cockpit, 'GIT_ROOT', Path(directory)):
            ids=lambda: {item['id'] for item in cockpit.web_apps_catalog()['apps']}
            self.assertNotIn('vocabulary-fr', ids())
            self.assertIn('vocabulary-fr-trainer', ids())
            public=Path(directory)/'docs/data/vocabulary-fr-v2.json'
            public.parent.mkdir(parents=True)
            public.write_text('{"items": []}')
            self.assertIn('vocabulary-fr', ids())
            apps=cockpit.web_apps_catalog()['apps']
            self.assertEqual(apps[0]['id'],'vocabulary-fr')
            self.assertEqual(apps[0]['title'],'Francouzština Jana')
            self.assertEqual([app['id'] for app in apps[-2:]],['lekarna','lekarna-admin'])
            self.assertIn('Francouzština Jana',(CLIENT/'index.html').read_text())

    def test_registered_web_target_is_distinct_and_desktop_launch_is_preserved(self):
        from app import cockpit
        from app.communication.luna_release import PAGES_PROJECT_PATHS,release_target
        from app.communication.human_adam_workstream_catalog import WORKSTREAM_CATALOG
        web={item['id']:item for item in cockpit.WEB_APP_CATALOG}
        desktop={item['id']:item for item in cockpit.DESKTOP_APP_CATALOG}
        self.assertTrue(desktop['vocabulary-fr-trainer']['script'].name=='vocab_trainer_fr.py')
        self.assertEqual(web['vocabulary-fr-trainer']['launch_type'],'desktop')
        self.assertEqual(web['vocabulary-fr']['url'],'https://belisarius-mila.github.io/PythonMF/vocabulary-fr/')
        self.assertEqual(release_target('project-vocabulary-fr'),'github_pages')
        self.assertEqual(PAGES_PROJECT_PATHS['project-vocabulary-fr'],'vocabulary-fr/')
        self.assertEqual(sum(r.workstream_id=='project-vocabulary-fr' for r in WORKSTREAM_CATALOG),1)

    def test_cockpit_integrates_game_entry_without_changing_other_apps_or_the_base_catalog(self):
        from app import cockpit
        from app.vocabulary_fr_hosting import Pilot
        from unittest.mock import patch
        from urllib.parse import parse_qs,urlsplit
        base={item['id']:dict(item) for item in cockpit.WEB_APP_CATALOG}
        origin='https://fixture-friendly-family-game.trycloudflare.com'
        with patch.object(Pilot,'status',return_value={'running':True,'origin':origin}):
            apps={item['id']:item for item in cockpit.web_apps_catalog()['apps']}
        self.assertEqual(parse_qs(urlsplit(apps['vocabulary-fr']['url']).fragment),{'onlineOrigin':[origin]})
        self.assertEqual(urlsplit(apps['vocabulary-fr']['url']).netloc,'belisarius-mila.github.io')
        self.assertEqual(base,{item['id']:item for item in cockpit.WEB_APP_CATALOG})
        for key,item in apps.items():
            if key!='vocabulary-fr':self.assertEqual(item,base[key])


if __name__=='__main__':unittest.main()
