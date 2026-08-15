import unittest

from fastapi.testclient import TestClient

from app.main import app


class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # -----------------------------------------------------
    # Health
    # -----------------------------------------------------

    def test_health(self):
        response = self.client.get("/health")

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.json()["status"],
            "healthy"
        )

    # -----------------------------------------------------
    # Person
    # -----------------------------------------------------

    def test_get_person(self):
        response = self.client.get(
            "/persons/P00013"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        data = response.json()

        self.assertEqual(
            data["person_id"],
            "P00013"
        )

        self.assertIn(
            "canonical_name",
            data
        )

    # -----------------------------------------------------
    # Person sources
    # -----------------------------------------------------

    def test_get_person_sources(self):
        response = self.client.get(
            "/persons/P00013/sources"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        data = response.json()

        self.assertGreater(
            len(data),
            0
        )

    # -----------------------------------------------------
    # Person not found
    # -----------------------------------------------------

    def test_person_not_found(self):
        response = self.client.get(
            "/persons/P99999"
        )

        self.assertEqual(
            response.status_code,
            404
        )

    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    def test_search_people(self):
        response = self.client.get(
            "/persons/search",
            params={"q": "Amit"}
        )

        self.assertEqual(
            response.status_code,
            200
        )

        data = response.json()

        self.assertIsInstance(
            data,
            list
        )

    # -----------------------------------------------------
    # Multi-source entities
    # -----------------------------------------------------

    def test_multi_source_entities(self):
        response = self.client.get(
            "/entities/multi-source"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        data = response.json()

        self.assertEqual(
            len(data),
            25
        )

    # -----------------------------------------------------
    # Source statistics
    # -----------------------------------------------------

    def test_source_statistics(self):
        response = self.client.get(
            "/statistics/sources"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        data = response.json()

        self.assertIsInstance(
            data,
            list
        )

    # -----------------------------------------------------
    # City search
    # -----------------------------------------------------

    def test_candidates_by_city(self):
        response = self.client.get(
            "/candidates/city/Noida"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertIsInstance(
            response.json(),
            list
        )

    # -----------------------------------------------------
    # Skill search
    # -----------------------------------------------------

    def test_candidates_by_skill(self):
        response = self.client.get(
            "/candidates/skill/Python"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertIsInstance(
            response.json(),
            list
        )

    # -----------------------------------------------------
    # Naukri
    # -----------------------------------------------------

    def test_naukri_details(self):
        response = self.client.get(
            "/persons/P00013/naukri"
        )

        self.assertEqual(
            response.status_code,
            200
        )

    # -----------------------------------------------------
    # Gig
    # -----------------------------------------------------

    def test_gig_details(self):
        response = self.client.get(
            "/persons/P00013/gig"
        )

        self.assertEqual(
            response.status_code,
            200
        )

    # -----------------------------------------------------
    # CBNexus
    # -----------------------------------------------------

    def test_cbnexus_details(self):
        response = self.client.get(
            "/persons/P00013/cbnexus"
        )

        self.assertEqual(
            response.status_code,
            200
        )

    # -----------------------------------------------------
    # Data quality issues
    # -----------------------------------------------------

    def test_data_quality_issues(self):
        response = self.client.get(
            "/data-quality/issues"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        data = response.json()

        self.assertEqual(
            len(data),
            21
        )

    # -----------------------------------------------------
    # Data quality summary
    # -----------------------------------------------------

    def test_data_quality_summary(self):
        response = self.client.get(
            "/data-quality/summary"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertIsInstance(
            response.json(),
            list
        )

    # -----------------------------------------------------
    # Database summary
    # -----------------------------------------------------

    def test_database_summary(self):
        response = self.client.get(
            "/database/summary"
        )

        self.assertEqual(
            response.status_code,
            200
        )

        data = response.json()

        self.assertEqual(
            data["persons"],
            66
        )

        self.assertEqual(
            data["source_records"],
            105
        )

        self.assertEqual(
            data["naukri_applications"],
            42
        )

        self.assertEqual(
            data["gig_workers"],
            32
        )

        self.assertEqual(
            data["cbnexus_contacts"],
            31
        )

        self.assertEqual(
            data["data_quality_issues"],
            21
        )

        self.assertEqual(
            data["multi_source_entities"],
            25
        )


if __name__ == "__main__":
    unittest.main()