"""Exercise playback cancellation, corpus selection and native speech contracts."""

import heapq
import random
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2] / "VocabularyFR"
sys.path.insert(0, str(ROOT))
from verb_training import LessonPlayer, LocalSpeech, TrainingCorpus, phrase


class Scheduler:
    def __init__(self):
        self.queue, self.cancelled = [], set()
        self.clock = self.counter = 0

    def after(self, delay, callback):
        self.counter += 1
        heapq.heappush(self.queue, (self.clock + delay, self.counter, callback))
        return self.counter

    def after_cancel(self, job):
        self.cancelled.add(job)

    def step(self):
        while self.queue:
            self.clock, job, callback = heapq.heappop(self.queue)
            if job not in self.cancelled:
                callback()
                return True
        return False

    def drain(self):
        for _ in range(2000):
            if not self.step():
                return
        raise AssertionError("Unbounded timer loop")


class Speech:
    command = ["fake"]

    def __init__(self):
        self.spoken = []
        self.running = False
        self.code = 0

    def start(self, text):
        self.spoken.append(text)
        self.running = True

    def stop(self):
        self.running = False

    def poll(self):
        return self.code


class TrainingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = TrainingCorpus(ROOT)

    def setUp(self):
        self.scheduler, self.speech = Scheduler(), Speech()
        self.shown, self.finished, self.errors = [], Mock(), Mock()
        self.player = LessonPlayer(self.scheduler, self.speech, self.shown.append, self.finished, self.errors)

    def lesson(self, verb="aller", **kwargs):
        return self.corpus.lesson(verb, "S", "1", rng=random.Random(1), **kwargs)

    def test_all_groups_produce_three_distinct_matching_sentences(self):
        for verb, number, person in self.corpus.groups:
            events = self.corpus.lesson(verb, number, person)
            sentences = [e for e in events if e["kind"] == "sentence"]
            self.assertEqual(len({e["text"] for e in sentences}), 3)
            expected = {r["Sentence"]: r["SentenceT"] for r in self.corpus.groups[verb, number, person]}
            for event in sentences:
                self.assertEqual(event["translation"], expected[event["text"]])

    def test_cycle_stays_within_number_and_falloir_is_impersonal(self):
        for number in ("S", "P"):
            person = "1"
            result = []
            for _ in range(4):
                result.append(person)
                person = self.corpus.next_person("aller", number, person)
            self.assertEqual(result, ["1", "2", "3", "1"])
        self.assertEqual(self.corpus.persons("falloir", "P"), [])
        self.assertEqual(self.corpus.next_person("falloir", "S", "3"), "3")
        with self.assertRaises(KeyError):
            self.corpus.lesson("falloir", "P", "1")

    def test_elision_and_recall_reveal_sequence(self):
        self.assertEqual(phrase("j'", "achète"), "j'achète")
        events = self.lesson("acheter", recall=True)
        recall = next(i for i, e in enumerate(events) if e["kind"] == "recall")
        self.assertEqual(events[recall]["text"], "J'")
        self.assertEqual([e["text"] for e in events if e["kind"] == "reveal"],
                         ["J'", "J'A", "J'AC", "J'ACH", "J'ACHÈ", "J'ACHÈT", "J'ACHÈTE"])
        self.assertEqual(events[-1]["speech"], "j'achète")
        self.assertFalse(any(e["speech"] for e in events if e["kind"] == "reveal"))

    def test_audio_finishes_before_next_sentence_and_no_czech_speech(self):
        self.speech.code = None
        self.player.start(self.lesson(introduction=True))
        for _ in range(6):
            self.scheduler.step()
        self.assertEqual(len(self.shown), 1)
        self.speech.code = 0
        self.scheduler.drain()
        self.assertEqual(len(self.speech.spoken), 6)  # infinitive, form, 3 sentences, answer
        self.finished.assert_called_once()
        self.errors.assert_not_called()

    def test_pause_stops_process_and_resume_repeats_interrupted_utterance(self):
        self.player.start(self.lesson())
        first = self.speech.spoken[-1]
        self.player.pause()
        self.assertFalse(self.speech.running)
        self.scheduler.drain()
        self.assertEqual(len(self.shown), 1)
        self.player.resume()
        self.assertEqual(self.speech.spoken[-1], first)
        self.scheduler.drain()
        self.finished.assert_called_once()

    def test_switch_invalidates_old_callbacks(self):
        self.player.start(self.lesson())
        stale = self.scheduler.queue[0][2]
        self.player.start(self.lesson("acheter"))
        count = len(self.shown)
        stale()  # Even a callback already dispatched by Tk cannot advance the new lesson.
        self.assertEqual(len(self.shown), count)
        self.scheduler.drain()
        self.assertEqual(self.shown[-1]["text"], "J'ACHÈTE")
        self.finished.assert_called_once()

    def test_repeat_after_completion_speaks_answer_and_finishes(self):
        self.player.start(self.lesson())
        self.scheduler.drain()
        before = len(self.speech.spoken)
        self.player.repeat()
        self.scheduler.drain()
        self.assertEqual(len(self.speech.spoken), before + 1)
        self.assertEqual(self.speech.spoken[-1], "je vais")

    def test_stop_and_silent_mode(self):
        self.player.start(self.lesson(), sound=False)
        self.scheduler.drain()
        self.assertEqual(self.speech.spoken, [])
        self.player.start(self.lesson())
        self.player.stop()
        count = len(self.shown)
        self.scheduler.drain()
        self.assertEqual(len(self.shown), count)
        self.assertFalse(self.speech.running)

    def test_speech_error_pauses_without_advancing_or_claiming_completion(self):
        self.speech.code = 1
        self.player.start(self.lesson())
        self.scheduler.drain()
        self.assertTrue(self.player.paused)
        self.assertEqual(len(self.shown), 1)
        self.finished.assert_not_called()
        self.errors.assert_called_once()

    def test_linux_french_voice_and_no_shell(self):
        which = lambda name: "/usr/bin/espeak-ng" if name == "espeak-ng" else None
        speech = LocalSpeech("linux", which)
        with patch("verb_training.subprocess.Popen") as launch:
            speech.start("J'achète du pain.")
        self.assertEqual(launch.call_args.args[0], ["/usr/bin/espeak-ng", "-v", "fr", "-s", "145", "J'achète du pain."])
        self.assertNotIn("shell", launch.call_args.kwargs)
        self.assertIsNone(LocalSpeech("linux", lambda _: None).command)


if __name__ == "__main__":
    unittest.main()
