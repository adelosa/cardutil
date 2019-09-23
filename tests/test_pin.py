import unittest
from binascii import unhexlify

from cardutil.pin import pin_block_0, tsp, visa_pvv


class PinTestCase(unittest.TestCase):
    def test_pin_block_0(self):
        self.assertEqual('041226cba9876fed', pin_block_0(pin='1234', card_number='4441234567890123'))

    def test_tsp(self):
        self.assertEqual('2345678901211234', tsp(pin='1234', card_number='4441234567890123'))

    def test_visa_pvv(self):
        test_key = '5CA64B3C22BEC347CA7E6609904BAAED'
        self.assertEqual('3856', visa_pvv(tsp('2205', '4564320000980369'), unhexlify(test_key)))

    def test_visa_pvv_more_values_required(self):
        """
        check when additional digits for pvv required
        """
        test_key = '5CA64B3C22BEC347CA7E6609904BAAED'
        self.assertEqual('0885', visa_pvv(tsp('0654', '4564320000980369'), unhexlify(test_key)))


if __name__ == '__main__':
    unittest.main()
