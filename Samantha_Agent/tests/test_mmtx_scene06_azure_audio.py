import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from app.speech.azure_tts_mp3 import CharacterBudget, ssml_parts


class Scene06AzureTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        spec = importlib.util.spec_from_file_location('scene06_azure_builder', root/'MatysekANJ/build_scene06_audio.py')
        self.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.builder)

    def test_remaining_plan_and_preview_cover_six_original_voices(self):
        b = self.builder
        story = [[speaker, 'Hello!', 'Ahoj!'] for speaker in ('logan','fiona','benji','bunny','sunny','bruno')]
        with tempfile.TemporaryDirectory() as tmp, patch.object(b,'ROOT',Path(tmp)):
            for lang in ('en','cs'):
                p=b.ROOT/'audio'/lang/'000.mp3';p.parent.mkdir(parents=True);p.write_bytes(b'existing')
            selection = b.preview_selection(story)
            self.assertEqual(len(selection), 6)
            voices = {b.VOICES[row[0]] if lang == 'en' else 'cs-CZ-VlastaNeural' for _,lang,row in selection}
            self.assertEqual(len(voices), 6)
            for i,lang,_ in selection:self.assertFalse((b.ROOT/'audio'/lang/f'{i:03}.mp3').exists())

    def test_existing_valid_clip_is_preserved_without_network(self):
        b = self.builder
        row = ['benji', 'Hello!', 'Ahoj!']
        data = b'existing valid content'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);path = root/'audio/en/000.mp3';path.parent.mkdir(parents=True);path.write_bytes(data)
            synth = AsyncMock()
            with patch.object(b, 'ROOT', root), patch.object(b, 'decode'):
                asyncio.run(b.generate_one(0, 'en', row, {'en/000':b.expected(row,'en',data)}, 'ffmpeg', synth=synth))
            self.assertEqual(path.read_bytes(), data)
            synth.assert_not_awaited()

    def test_preview_failure_retains_first_clip_and_never_changes_scene(self):
        b = self.builder
        story = [['benji', 'Hello!', 'Ahoj!']]
        budget = CharacterBudget()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp);scene = repo/'scene';scene.mkdir();(scene/'story.json').write_text(json.dumps(story))
            before = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in scene.iterdir()}
            calls = []
            async def synth(text, *, voice, rate):
                calls.append(voice);budget.reserve(ssml_parts(text,voice,rate)[1])
                if len(calls)==2:raise RuntimeError('test service failure')
                return b'ID3'+b'a'*1100
            with patch.object(b,'REPO',repo),patch.object(b,'ROOT',scene),patch.object(b,'decode'),patch.object(b.asyncio,'sleep',new=AsyncMock()):
                with self.assertRaisesRegex(RuntimeError,'test service failure'):
                    asyncio.run(b.generate_preview(story,'ffmpeg',synth,budget))
            self.assertEqual(len(calls),2)
            receipt_path = next(repo.glob('Samantha_Agent/data/private/mmtx/scene06_azure_preview/*/preview.json'))
            receipt = json.loads(receipt_path.read_text())
            self.assertEqual(receipt['status'],'failed')
            self.assertEqual(len(receipt['clips']),1)
            self.assertTrue((receipt_path.parent/receipt['clips'][0]['file']).is_file())
            self.assertEqual(receipt['reserved_characters'],budget.reserved)
            self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in scene.iterdir()})

    def test_whole_plan_over_limit_sends_nothing(self):
        b=self.builder
        with tempfile.TemporaryDirectory() as tmp, patch.object(b,'ROOT',Path(tmp)), patch.object(b,'synthesize_azure_tts_mp3_sync') as synth:
            (b.ROOT/'story.json').write_text(json.dumps([['benji','Hello!','Ahoj!']]))
            (b.ROOT/'audio_bindings.json').write_text('{}')
            with self.assertRaisesRegex(RuntimeError,'žádný požadavek'):
                asyncio.run(b.main(['--apply','--provider','azure','--max-characters','1']))
            synth.assert_not_called()


if __name__ == '__main__':unittest.main()
