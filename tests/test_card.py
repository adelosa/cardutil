import unittest

from cardutil import card


class CardTestCase(unittest.TestCase):
    def test_check_digit(self):
        acct = '7992739871'
        self.assertEqual('3', card.calculate_check_digit(acct))
        self.assertIsNone(card.validate_check_digit(card.add_check_digit(acct)))
        with self.assertRaises(AssertionError):
            card.validate_check_digit("111")

    def test_mask(self):
        self.assertEqual('123456**9012', card.mask('123456789012'))
        self.assertEqual('123456..9012', card.mask('123456789012', mask_char='.'))


if __name__ == '__main__':
    unittest.main()
