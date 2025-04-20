import unittest

from cardutil.vendor import hexdump


class VendorHexdumpTestCase(unittest.TestCase):
    def test_dump_binary_data(self):
        data = b"\x00\x01\x02\x03\x04\x05\x06\x07"
        output = hexdump.hexdump(data, result='return')
        expected_output = "00000000: 00 01 02 03 04 05 06 07                           ........"
        self.assertEqual(expected_output, output)

    def test_dump_text_default_latin1_encoding(self):
        data = b"\x30\x31\x32\x33\x34\x35\x36\x37"
        output = hexdump.hexdump(data, result='return')
        expected_output = "00000000: 30 31 32 33 34 35 36 37                           01234567"
        self.assertEqual(expected_output, output)

    def test_dump_text_cp500_encoding(self):
        data = b"\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7"
        output = hexdump.hexdump(data, result='return', encoding='cp500')
        expected_output = "00000000: F0 F1 F2 F3 F4 F5 F6 F7                           01234567"
        self.assertEqual(expected_output, output)
