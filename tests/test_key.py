import unittest

from cardutil.key import get_zone_master_key, get_enc_zone_master_key


class KeyTestCase(unittest.TestCase):
    def test_get_zone_master_key(self):
        hex_key, kcv = get_zone_master_key('6d6be51f04f76167491554fe25f7abef', '67499b2cf137dfcb9ea28ff757cd10a7')
        self.assertEqual('0a227e33f5c0beacd7b7db09723abb48', hex_key)
        self.assertEqual('05ee1d', kcv)

    def test_get_enc_zone_master_key(self):
        enc_key, kvc = get_enc_zone_master_key(
            '00' * 16,
            '6d6be51f04f76167491554fe25f7abef', '67499b2cf137dfcb9ea28ff757cd10a7')
        print(enc_key)
        print(kvc)


if __name__ == '__main__':
    unittest.main()
