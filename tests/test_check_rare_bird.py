import unittest
from datetime import date

from scripts.check_rare_bird import ebird_week, lookup_frequency


class EbirdWeekTests(unittest.TestCase):
    def test_four_period_month(self) -> None:
        self.assertEqual(ebird_week(date(2026, 1, 1)), 0)
        self.assertEqual(ebird_week(date(2026, 1, 8)), 1)
        self.assertEqual(ebird_week(date(2026, 1, 15)), 2)
        self.assertEqual(ebird_week(date(2026, 1, 22)), 3)
        self.assertEqual(ebird_week(date(2026, 1, 31)), 3)
        self.assertEqual(ebird_week(date(2026, 12, 31)), 47)


class LookupFrequencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.values = [index / 100 for index in range(48)]
        self.frequencies = {"sample": self.values}

    def test_current_period_lookup(self) -> None:
        self.assertEqual(
            lookup_frequency(self.frequencies, "SAMPLE", date(2026, 2, 8)),
            self.values[5],
        )

    def test_unknown_species_fails_closed(self) -> None:
        self.assertEqual(
            lookup_frequency(self.frequencies, "unknown", date(2026, 2, 8)),
            1.0,
        )

    def test_malformed_species_data_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            lookup_frequency({"sample": [0.1]}, "sample", date(2026, 2, 8))

    def test_out_of_range_frequency_is_an_error(self) -> None:
        invalid = {"sample": [1.1] * 48}
        with self.assertRaises(ValueError):
            lookup_frequency(invalid, "sample", date(2026, 2, 8))


if __name__ == "__main__":
    unittest.main()
