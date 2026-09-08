"""Integrity of the imported present-tense training corpus."""

import csv
import re
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2] / "VocabularyFR"


def read_rows(name):
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class VerbTrainingDataTests(unittest.TestCase):
    def test_training_catalog_and_preserved_library(self):
        training = read_rows("VerbeTraining.csv")
        library = read_rows("VerbeFR.csv")
        self.assertEqual(len(training), 100)
        self.assertEqual(len({r["InfFR"] for r in training}), 100)
        self.assertEqual(len(library), 107)
        self.assertEqual(len({r["InfFR"] for r in library}), 107)
        for order, (selected, entry) in enumerate(zip(training, library), 1):
            self.assertEqual(selected["Order"], str(order))
            self.assertEqual(selected["InfFR"], entry["InfFR"])
            self.assertEqual(selected["InfCZ"], entry["InfCZ"])
        self.assertEqual(
            {r["InfFR"] for r in library[100:]},
            {"acheter", "boire", "laisser", "payer", "rentrer", "travailler", "vendre"},
        )

    def test_every_sentence_has_a_matching_present_form(self):
        rows = read_rows("VerbeSentences.csv")
        library = {r["InfFR"]: r for r in read_rows("VerbeFR.csv")}
        selected = {r["InfFR"] for r in read_rows("VerbeTraining.csv")}
        self.assertEqual(len(rows), 1800)
        self.assertEqual(len({r["Id"] for r in rows}), 1800)
        self.assertEqual(len({(r["Sentence"], r["SentenceT"]) for r in rows}), 1800)
        person_map = {
            "je": ("S", "1"), "j'": ("S", "1"), "tu": ("S", "2"),
            "il": ("S", "3"), "elle": ("S", "3"), "nous": ("P", "1"),
            "vous": ("P", "2"), "ils": ("P", "3"), "elles": ("P", "3"),
        }
        for row in rows:
            with self.subTest(sentence=row["Id"]):
                self.assertIn(row["InfFR"], selected)
                self.assertEqual(row["Tense"], "present")
                self.assertTrue(row["SentenceT"].strip())
                self.assertEqual(person_map[row["Pronoun"]], (row["Number"], row["Person"]))
                prefix = row["Pronoun"] + ("" if row["Pronoun"].endswith("'") else " ")
                self.assertRegex(row["Sentence"].lower(), "^" + re.escape(prefix + row["Form"]) + r"\b")
                key = "Ind" + ("P" if row["Number"] == "P" else "") + row["Person"]
                form = re.sub(
                    r"^(?:j['’]|je |tu |il/elle |il |nous |vous |ils/elles |ils )",
                    "", library[row["InfFR"]][key],
                )
                self.assertEqual(form, row["Form"])

    def test_coverage_and_impersonal_falloir(self):
        rows = read_rows("VerbeSentences.csv")
        counts = Counter((r["InfFR"], r["Number"], r["Person"]) for r in rows)
        for verb in read_rows("VerbeTraining.csv"):
            infinitive = verb["InfFR"]
            for number in ("S", "P"):
                for person in ("1", "2", "3"):
                    expected = 3 if infinitive != "falloir" else (18 if (number, person) == ("S", "3") else 0)
                    self.assertEqual(counts[infinitive, number, person], expected)
        falloir = next(r for r in read_rows("VerbeFR.csv") if r["InfFR"] == "falloir")
        self.assertEqual(falloir["Ind3"], "il faut")
        for key in ("Ind1", "Ind2", "IndP1", "IndP2", "IndP3"):
            self.assertEqual(falloir[key], "")


if __name__ == "__main__":
    unittest.main()
