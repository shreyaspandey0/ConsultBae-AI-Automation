import unittest
import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENTITY_FILE = (
    PROJECT_ROOT
    / "docs"
    / "entity_resolution.csv"
)


class TestEntityResolution(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.df = pd.read_csv(
            ENTITY_FILE,
            dtype=str
        )

    def test_total_source_records(self):

        self.assertEqual(
            len(self.df),
            105
        )

    def test_no_missing_person_ids(self):

        self.assertFalse(
            self.df["person_id"]
            .isna()
            .any()
        )

    def test_record_ids_are_unique(self):

        self.assertEqual(
            self.df["record_id"].nunique(),
            len(self.df)
        )

    def test_expected_source_counts(self):

        counts = (
            self.df["source"]
            .value_counts()
            .to_dict()
        )

        self.assertEqual(
            counts.get("naukri"),
            42
        )

        self.assertEqual(
            counts.get("gig"),
            32
        )

        self.assertEqual(
            counts.get("cbnexus"),
            31
        )

    def test_expected_entity_count(self):

        self.assertEqual(
            self.df["person_id"].nunique(),
            66
        )

    def test_no_entity_has_duplicate_source_record(self):

        duplicates = self.df.duplicated(
            subset=["person_id", "record_id"]
        )

        self.assertFalse(
            duplicates.any()
        )


if __name__ == "__main__":
    unittest.main()