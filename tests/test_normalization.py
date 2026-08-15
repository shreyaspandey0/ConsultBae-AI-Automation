import unittest

from src.normalization import (
    normalize_name,
    normalize_email,
    normalize_phone,
    normalize_city,
    normalize_status,
    normalize_verified,
    is_valid_email,
    is_valid_phone,
)


class TestNormalization(unittest.TestCase):

    # -----------------------------------------------------
    # Name
    # -----------------------------------------------------

    def test_name_normalization(self):

        self.assertEqual(
            normalize_name("  ISHA   CHOPRA "),
            "isha chopra"
        )

    # -----------------------------------------------------
    # Email
    # -----------------------------------------------------

    def test_email_normalization(self):

        self.assertEqual(
            normalize_email(
                "  ISHA.CHOPRA95@MAILTEST.EXAMPLE.ORG "
            ),
            "isha.chopra95@mailtest.example.org"
        )

    # -----------------------------------------------------
    # Phone
    # -----------------------------------------------------

    def test_phone_with_country_code(self):

        self.assertEqual(
            normalize_phone(
                "+91-9000000254"
            ),
            "9000000254"
        )

    def test_phone_without_country_code(self):

        self.assertEqual(
            normalize_phone(
                "9000000254"
            ),
            "9000000254"
        )

    def test_phone_scientific_notation(self):

        self.assertEqual(
            normalize_phone(
                "9.19000000254E11"
            ),
            "9000000254"
        )

    def test_phone_float_format(self):

        self.assertEqual(
            normalize_phone(
                "919000000254.0"
            ),
            "9000000254"
        )

    # -----------------------------------------------------
    # City
    # -----------------------------------------------------

    def test_city_normalization(self):

        self.assertEqual(
            normalize_city("Gurugram"),
            "gurgaon"
        )

        self.assertEqual(
            normalize_city("New Delhi"),
            "delhi"
        )

        self.assertEqual(
            normalize_city("Bangalore"),
            "bengaluru"
        )

    # -----------------------------------------------------
    # Status
    # -----------------------------------------------------

    def test_status_normalization(self):

        self.assertEqual(
            normalize_status("ACTIVE"),
            "active"
        )

        self.assertEqual(
            normalize_status("Paused"),
            "paused"
        )

    # -----------------------------------------------------
    # Verified
    # -----------------------------------------------------

    def test_verified_normalization(self):

        self.assertTrue(
            normalize_verified("YES")
        )

        self.assertTrue(
            normalize_verified("Verified")
        )

        self.assertFalse(
            normalize_verified("NO")
        )

        self.assertFalse(
            normalize_verified("N")
        )

    # -----------------------------------------------------
    # Validation
    # -----------------------------------------------------

    def test_valid_email(self):

        self.assertTrue(
            is_valid_email(
                "person@example.com"
            )
        )

    def test_invalid_email(self):

        self.assertFalse(
            is_valid_email(
                "personexample.com"
            )
        )

    def test_valid_phone(self):

        self.assertTrue(
            is_valid_phone(
                "+91-9000000254"
            )
        )

    def test_invalid_phone(self):

        self.assertFalse(
            is_valid_phone(
                "12345"
            )
        )


if __name__ == "__main__":
    unittest.main()