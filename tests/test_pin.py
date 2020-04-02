import unittest
from binascii import unhexlify

from cardutil import pin


class PinTestCase(unittest.TestCase):
    def test_pin_block_0(self):
        self.assertEqual(
            b'\x04\x12\x26\xcb\xa9\x87\x6f\xed', pin.pin_block_0(pin='1234', card_number='4441234567890123'))

    def test_tsp(self):
        self.assertEqual('2345678901211234', pin.calculate_tsp(pin='1234', card_number='4441234567890123'))

    def test_visa_pvv(self):
        test_key = '5CA64B3C22BEC347CA7E6609904BAAED'
        self.assertEqual(
            '3856', pin.calculate_visa_pvv(pin.calculate_tsp('2205', '4564320000980369'), unhexlify(test_key)))

    def test_visa_pvv_more_values_required(self):
        """
        check when additional digits for pvv required
        """
        test_key = '5CA64B3C22BEC347CA7E6609904BAAED'
        self.assertEqual(
            '0885', pin.calculate_visa_pvv(pin.calculate_tsp('0654', '4564320000980369'), unhexlify(test_key)))

    def test_pin_block_primitives(self):
        pb = pin.pin_block_0('1234', '1111222233334444')
        print(pb)
        epb = pin._encrypt('00' * 16, pb)
        print(epb)
        pb = pin._decrypt('00' * 16, epb)
        print(pb)
        test_pin = pin.pin_block_0_to_pin(pb, '1111222233334444')
        self.assertEqual(test_pin, '1234')

    def test_pin_block_class(self):
        pb1 = pin.PinBlock(pin='1234', card_number='1111222233334444')
        self.assertEqual(pb1.pin, '1234')
        self.assertEqual(pb1.card_number, '1111222233334444')
        self.assertEqual(pb1.to_bytes(), b'\x04\x12&\xdd\xdc\xcc\xcb\xbb')
        self.assertEqual(pb1.to_enc_bytes(key='00' * 16), b'L\t\x06\xd1\x03\x08\x87\x1a')
        self.assertEqual(pb1.to_pvv(pvv_key='00' * 16), '6264')

        pb2 = pin.PinBlock.from_bytes(
            pin_block=pb1.to_bytes(), card_number='1111222233334444')
        self.assertEqual(pb2.pin, '1234')

        pb3 = pin.PinBlock.from_enc_bytes(
            enc_pin_block=pb1.to_enc_bytes('00' * 16), card_number='1111222233334444', key='00' * 16)
        self.assertEqual(pb3.pin, '1234')


if __name__ == '__main__':
    unittest.main()
