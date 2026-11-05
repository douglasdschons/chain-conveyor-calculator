import unittest

from src.localization import format_number, parse_number


class BrazilianNumberTests(unittest.TestCase):
    def test_decimal_comma_and_thousands(self):
        self.assertEqual(parse_number("25,4"), 25.4)
        self.assertEqual(parse_number("1.000,50"), 1000.5)
        self.assertEqual(parse_number(" 1.700 ", integer=True), 1700)
        self.assertEqual(format_number(25.4), "25,4")
        self.assertEqual(format_number(1000.5, 2), "1.000,50")
        self.assertEqual(format_number(4.15554, 5, grouping=False), "4,15554")

    def test_mixed_or_invalid_notation_is_rejected(self):
        for value in ("25.4", "1,000.50", "NaN", "inf", "", "1;5"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_number(value)
        with self.assertRaises(ValueError):
            parse_number("1,5", integer=True)
