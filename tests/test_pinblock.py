import unittest

from cardutil import pinblock


class PinblockTestCase(unittest.TestCase):
    def test_pin_block_Iso0(self):
        self.assertEqual(
            b'\x04\x12\x26\xcb\xa9\x87\x6f\xed',
            pinblock.Iso0PinBlock(pin='1234', card_number='4441234567890123').to_bytes())

    def test_visa_pvv(self):
        test_key = '5CA64B3C22BEC347CA7E6609904BAAED'
        self.assertEqual(
            '3856', pinblock.calculate_pvv(pin='2205', card_number='4564320000980369', pvv_key=test_key, key_index=1))

    def test_visa_pvv_more_values_required(self):
        """
        check when additional digits for pvv required
        """
        test_key = '5CA64B3C22BEC347CA7E6609904BAAED'
        self.assertEqual(
            '0885', pinblock.calculate_pvv(pin='0654', card_number='4564320000980369', pvv_key=test_key, key_index=1))

    def test_visa_pvv_mixin(self):
        # use pin block without card_number property
        MyPinBlock = type('MyPinBlock', (pinblock.Iso4PinBlock, pinblock.VisaPVVPinBlockMixin), {})
        pb = MyPinBlock(pin='6666')
        with self.assertRaises(ValueError):
            pb.to_pvv(pvv_key='00' * 8)
        self.assertEqual(pb.to_pvv(pvv_key='00' * 8, card_number='1111222233334444'), '1703')

    def test_pin_block_Iso0TDESPinBlockWithVisaPVV(self):
        pb1 = pinblock.Iso0TDESPinBlockWithVisaPVV(pin='1234', card_number='1111222233334444')
        self.assertEqual(pb1.pin, '1234')
        self.assertEqual(pb1.card_number, '1111222233334444')
        self.assertEqual(pb1.to_bytes(), b'\x04\x12&\xdd\xdc\xcc\xcb\xbb')
        self.assertEqual(pb1.to_enc_bytes(key='00' * 16), b'L\t\x06\xd1\x03\x08\x87\x1a')
        self.assertEqual(pb1.to_pvv(pvv_key='00' * 16), '6264')

        pb2 = pinblock.Iso0TDESPinBlockWithVisaPVV.from_bytes(
            pin_block=pb1.to_bytes(), card_number='1111222233334444')
        self.assertEqual(pb2.pin, '1234')

        pb3 = pinblock.Iso0TDESPinBlockWithVisaPVV.from_enc_bytes(
            enc_pin_block=pb1.to_enc_bytes('00' * 16), card_number='1111222233334444', key='00' * 16)
        self.assertEqual(pb3.pin, '1234')

    def test_pin_block_Iso4AESPinBlockWithVisaPVV(self):
        pb1 = pinblock.Iso4AESPinBlockWithVisaPVV(pin='1234', random_value=14932500169729639426)
        self.assertEqual(pb1.pin, '1234')
        self.assertEqual(pb1.to_bytes()[0:8], b'\x44\x12\x34\xaa\xaa\xaa\xaa\xaa')
        self.assertEqual(pb1.to_enc_bytes(key='00' * 16), b',4yaY\xbf\x10j\xf6\xf5\xd2;Y\xfd\xe2\xfe')
        self.assertEqual(pb1.to_pvv(pvv_key='00' * 16, card_number='1111222233334444'), '6264')

        pb2 = pinblock.Iso4AESPinBlockWithVisaPVV.from_bytes(pin_block=pb1.to_bytes())
        self.assertEqual(pb2.pin, '1234')

        pb3 = pinblock.Iso4AESPinBlockWithVisaPVV.from_enc_bytes(
            enc_pin_block=pb1.to_enc_bytes('00' * 16), key='00' * 16)
        self.assertEqual(pb3.pin, '1234')

    def test_pinblock_operations(self):
        tdes_key = '2222111122221111'
        aes_key = tdes_key * 2
        key = aes_key

        pin_blocks = [
            type(
                'TDESPinBlock',
                (pinblock.Iso0PinBlock, pinblock.TdesEncryptedPinBlockMixin, pinblock.VisaPVVPinBlockMixin), {}),
            type(
                'AESPinBlock',
                (pinblock.Iso4PinBlock, pinblock.AESEncryptedPinBlockMixin, pinblock.VisaPVVPinBlockMixin), {}),
            pinblock.Iso0TDESPinBlockWithVisaPVV,
            pinblock.Iso4AESPinBlockWithVisaPVV
        ]
        for pb in pin_blocks:
            print(pb)
            pb = pb(pin='1234', card_number='1111222233334444')
            self.assertEqual(pb.pin, '1234')
            self.assertEqual(pb.to_pvv(pvv_key='1111222211112222', key_index=1, card_number='1111222233334444'), '9595')
            pb2 = pb.from_bytes(pb.to_bytes(), card_number='1111222233334444')
            self.assertEqual(pb2.pin, '1234')
            pb2 = pb.from_enc_bytes(pb.to_enc_bytes(key=key), key=key, card_number='1111222233334444')
            self.assertEqual(pb2.pin, '1234')


if __name__ == '__main__':
    unittest.main()
