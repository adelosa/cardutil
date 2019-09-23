import unittest

from cardutil import BitArray


class BitArrayTestCase(unittest.TestCase):
    def test_big_endian(self):
        my_array = BitArray.BitArray()
        my_array.frombytes(b"\x01")
        self.assertEqual([False, False, False, False, False, False, False, True], my_array.tolist())

    def test_liitle_endian(self):
        my_array = BitArray.BitArray(endian='little')
        my_array.frombytes(b"\x01")
        self.assertEqual([True, False, False, False, False, False, False, False], my_array.tolist())


if __name__ == '__main__':
    unittest.main()
