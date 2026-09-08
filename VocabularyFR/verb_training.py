"""Read-only training corpus and cancellable, event-driven lesson playback."""

import csv
import random
import shutil
import subprocess
import sys
from pathlib import Path


def phrase(pronoun, form):
    return pronoun + ("" if pronoun.endswith(("'", "’")) else " ") + form


class TrainingCorpus:
    def __init__(self, directory):
        directory = Path(directory)
        def read(name):
            with (directory / name).open(encoding="utf-8-sig", newline="") as handle:
                return list(csv.DictReader(handle))
        self.verbs = read("VerbeTraining.csv")
        self.groups = {}
        names = {v["InfFR"] for v in self.verbs}
        if not names or len(names) != len(self.verbs):
            raise ValueError("Seznam sloves je prázdný nebo obsahuje duplicity.")
        ids = set()
        for row in read("VerbeSentences.csv"):
            if (row["InfFR"] not in names or row["Tense"] != "present"
                    or row["Number"] not in ("S", "P") or row["Person"] not in ("1", "2", "3")
                    or not all(row[k].strip() for k in ("Id", "Pronoun", "Form", "Sentence", "SentenceT"))
                    or row["Id"] in ids):
                raise ValueError("Neplatná nebo duplicitní tréninková věta.")
            ids.add(row["Id"])
            key = (row["InfFR"], row["Number"], row["Person"])
            self.groups.setdefault(key, []).append(row)
        for verb in names:
            expected = [("S", "3")] if verb == "falloir" else [
                (n, p) for n in ("S", "P") for p in ("1", "2", "3")]
            actual = {(n, p) for v, n, p in self.groups if v == verb}
            if actual != set(expected):
                raise ValueError(f"Neúplné osoby slovesa {verb}.")
            for n, p in expected:
                rows = self.groups[verb, n, p]
                if len(rows) < 3 or len({r["Form"] for r in rows}) != 1:
                    raise ValueError(f"Chybí tři věty nebo jednotný tvar: {verb}, {n}/{p}.")

    def persons(self, verb, number):
        return [p for p in ("1", "2", "3") if (verb, number, p) in self.groups]

    def next_person(self, verb, number, person):
        people = self.persons(verb, number)
        return people[(people.index(person) + 1) % len(people)]

    def lesson(self, verb, number, person, recall=False, interval=2, rng=None, introduction=False):
        rows = (rng or random).sample(self.groups[verb, number, person], 3)
        pronoun, form = rows[0]["Pronoun"], rows[0]["Form"]
        text = phrase(pronoun, form)
        events = []
        def event(kind, text="", speech="", delay=0, **extra):
            events.append(dict(kind=kind, text=text, speech=speech, delay=delay, **extra))
        if introduction:
            event("intro", speech=verb)
        event("form", text, text, interval)
        for index, row in enumerate(rows):
            event("sentence", row["Sentence"], row["Sentence"], interval,
                  translation=row["SentenceT"], slot=index)
        if recall:
            event("recall", pronoun.upper(), delay=max(3, interval))
        event("reveal", phrase(pronoun.upper(), ""), delay=0.3)
        for length in range(1, len(form) + 1):
            event("reveal", phrase(pronoun.upper(), form[:length].upper()), delay=0.22)
        event("answer", text.upper(), text)
        return events


class LocalSpeech:
    """Only owns its own speech process; no shell, global kill or network."""
    def __init__(self, platform=None, which=shutil.which):
        platform = platform or sys.platform
        self.command = None
        if platform == "darwin" and which("say"):
            self.command = [which("say"), "-v", "Thomas", "-r", "155"]
        elif platform.startswith("linux"):
            executable = which("espeak-ng") or which("espeak")
            if executable:
                self.command = [executable, "-v", "fr", "-s", "145"]
        self.process = None

    def start(self, text):
        self.stop()
        if not self.command:
            raise RuntimeError("Francouzský hlas není dostupný.")
        self.process = subprocess.Popen(self.command + [text], stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL)

    def poll(self):
        return self.process.poll() if self.process else 0

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=0.3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=0.3)
        self.process = None


class LessonPlayer:
    """One Tk timer and one process. Resume restarts the interrupted utterance."""
    def __init__(self, scheduler, speech, show, finished, error):
        self.scheduler, self.speech = scheduler, speech
        self.show, self.finished, self.error = show, finished, error
        self.events = []
        self.index = 0
        self.job = None
        self.paused = False
        self.active = False
        self.sound = True
        self.generation = 0

    def _later(self, milliseconds, callback):
        generation = self.generation
        def run():
            if generation == self.generation and self.active and not self.paused:
                self.job = None
                callback()
        self.job = self.scheduler.after(milliseconds, run)

    def _cancel(self):
        self.generation += 1
        if self.job is not None:
            self.scheduler.after_cancel(self.job)
            self.job = None
        self.speech.stop()

    def start(self, events, sound=True):
        self.stop()
        self.events, self.index, self.sound = events, 0, sound
        self.active = True
        self._play()

    def stop(self):
        self._cancel()
        self.active, self.paused = False, False

    def pause(self):
        if self.active:
            self._cancel()
            self.paused = True

    def resume(self):
        if self.active and self.paused:
            self.paused = False
            self._play()

    def repeat(self):
        if not self.events:
            return
        self._cancel()
        # Repeat the currently visible utterance; at the end repeat the answer.
        self.index = min(self.index, len(self.events) - 1)
        while self.index > 0 and not self.events[self.index]["speech"]:
            self.index -= 1
        self.active, self.paused = True, False
        self._play()

    def _play(self):
        if self.index >= len(self.events):
            self.active = False
            self.finished()
            return
        event = self.events[self.index]
        self.show(event)
        if event["speech"] and self.sound:
            try:
                self.speech.start(event["speech"])
            except (OSError, RuntimeError) as exc:
                self.pause()
                self.error(str(exc))
                return
            self._later(80, self._poll)
        else:
            self._delay()

    def _poll(self):
        code = self.speech.poll()
        if code is None:
            self._later(80, self._poll)
        elif code != 0:
            self.pause()
            self.error("Přehrání selhalo. Zopakuj větu nebo vypni zvuk.")
        else:
            self._delay()

    def _delay(self):
        delay = self.events[self.index]["delay"]
        if not self.sound and self.events[self.index]["speech"]:
            delay = max(2, delay)
        self._later(max(1, int(delay * 1000)), self._advance)

    def _advance(self):
        self.index += 1
        self._play()
