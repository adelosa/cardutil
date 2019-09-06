import decimal
import unittest

from cardutil.config import config
from cardutil.iso8583 import (
    BitArray, _iso8583_to_field, _field_to_iso8583, _iso8583_to_dict, _dict_to_iso8583, loads, dumps,
    _pds_to_de, _pds_to_dict)

message_ebcdic_raw = (
        '1144'.encode('cp500') +
        b"\xF0\x10\x05\x42\x84\x61\x80\x02\x02\x00\x00\x04\x00\x00\x00\x00" +
        ('164444555544445555111111000000009999201508151715123456789012333123423579957991200000'
         '012306120612345612345657994211111111145BIG BOBS\\70 FERNDALE ST\\ANNERLEY\\4103  QLD'
         'AUS0080001001Y99901600000000000000011234567806999999').encode('cp500'))

message_ascii_raw = (
        b"1144" +
        b"\xF0\x10\x05\x42\x84\x61\x80\x02\x02\x00\x00\x04\x00\x00\x00\x00" +
        (b"164444555544445555111111000000009999201508151715123456789012333123423579957991200000"
         b"012306120612345612345657994211111111145BIG BOBS\\70 FERNDALE ST\\ANNERLEY\\4103  QLD"
         b"AUS0080001001Y99901600000000000000011234567806999999"))


class Iso8583TestCase(unittest.TestCase):
    def test_dumps(self):
        out_data = dumps({'MTI': '1234', 'DE2': '123'})
        self.assertEqual(b'1234\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0003123', out_data)

    def test_loads(self):
        self.assertEqual({'MTI': '1234', 'DE2': '123'}, loads(dumps({'MTI': '1234', 'DE2': '123'})))

    def test_dump_load_ascii(self):
        self.assertEqual(message_ascii_raw, dumps(loads(message_ascii_raw)))

    def test_dump_load_ebcdic(self):
        self.assertEqual(message_ebcdic_raw, dumps(loads(message_ebcdic_raw, encoding='cp500'), encoding='cp500'))

    def test_bitarray(self):
        """
        feed in binary bitmap, convert to array then back to bitmap. Make sure its the same
        """
        start_bitmap = b'\xF0\x10\x05\x42\x84\x61\x80\x02\x02\x00\x00\x04\x00\x00\x00\x00'
        test_bitarray = BitArray()
        test_bitarray.frombytes(start_bitmap)
        bit_list = test_bitarray.tolist()
        for index, value in enumerate(bit_list):
            if value:
                print(f'{index+1}={value}')
        expected_true_bits = (1, 2, 3, 4, 12, 22, 24, 26, 31, 33, 38, 42, 43, 48, 49, 63, 71, 94)
        expected_bits = [True if bit+1 in expected_true_bits else False for bit in range(128)]
        self.assertEqual(expected_bits, bit_list)
        test_bitarray.fromlist(expected_bits)
        end_bitmap = test_bitarray.tobytes()
        self.assertEqual(start_bitmap, end_bitmap)

    def test_iso8583_to_field(self):
        self.assertEqual(
            ({'DE1': '4564320012321122'}, 18),
            _iso8583_to_field('1', {'field_type': 'LLVAR', 'field_length': 0}, b'164564320012321122'))
        self.assertEqual(
            ({'DE1': '4564320012321122'}, 19),
            _iso8583_to_field('1', {'field_type': 'LLLVAR', 'field_length': 0}, b'0164564320012321122'))
        self.assertEqual(
            ({'DE1': '4564320012321122    '}, 20),
            _iso8583_to_field('1', {'field_type': 'FIXED', 'field_length': 20}, b'4564320012321122    '))
        self.assertEqual(
            ({'DE1': 1234}, 20),
            _iso8583_to_field(
                '1', {'field_type': 'FIXED', 'python_field_type': 'int', 'field_length': 20}, b'00000000000000001234'))
        self.assertEqual(
            ({'DE1': 1234}, 6),
            _iso8583_to_field('1', {'field_type': 'LLVAR', 'python_field_type': 'int', 'field_length': 0}, b'041234'))
        self.assertEqual(
            ({'DE1': decimal.Decimal('123.432')}, 20),
            _iso8583_to_field('1', {'field_type': 'FIXED', 'python_field_type': 'decimal', 'field_length': 20},
                              b'0000000000000123.432'))

    def test_field_to_iso8583(self):
        self.assertEqual(
            b'164564320012321122', _field_to_iso8583({'field_type': 'LLVAR', 'field_length': 0}, "4564320012321122"))
        self.assertEqual(
            b'0164564320012321122', _field_to_iso8583({'field_type': 'LLLVAR', 'field_length': 0}, "4564320012321122"))
        self.assertEqual(
            b'4564320012321122    ', _field_to_iso8583({'field_type': 'FIXED', 'field_length': 20}, "4564320012321122"))
        self.assertEqual(
            b'00000000000000001234', _field_to_iso8583(
                {'field_type': 'FIXED', 'python_field_type': 'int', 'field_length': 20}, 1234))
        self.assertEqual(
            b'041234', _field_to_iso8583({'field_type': 'LLVAR', 'python_field_type': 'int', 'field_length': 0}, 1234))
        self.assertEqual(
            b'0000000000000123.432',
            _field_to_iso8583(
                {'field_type': 'FIXED', 'python_field_type': 'decimal', 'field_length': 20},
                decimal.Decimal("123.432")))

    def test_iso8583_to_dict(self):
        expected_dict = {'MTI': '1144', 'DE2': '4444555544445555', 'DE3': '111111', 'DE4': '000000009999',
                         'DE12': '201508151715', 'DE22': '123456789012', 'DE24': '333', 'DE26': '1234',
                         'DE31': '57995799120000001230612', 'DE33': '123456', 'DE38': '123456',
                         'DE42': '579942111111111', 'DE43': 'BIG BOBS\\70 FERNDALE ST\\ANNERLEY\\4103  QLDAUS',
                         'DE43_NAME': 'BIG BOBS', 'DE43_ADDRESS': '70 FERNDALE ST', 'DE43_SUBURB': 'ANNERLEY',
                         'DE43_POSTCODE': '4103', 'DE43_STATE': 'QLD', 'DE43_COUNTRY': 'AUS',
                         'DE48': '0001001Y', 'PDS0001': 'Y', 'DE49': '999', 'DE63': '0000000000000001',
                         'DE71': '12345678', 'DE94': '999999'}

        ascii_dict = _iso8583_to_dict(message_ascii_raw, config["bit_config"], "latin-1")
        self.assertEqual(ascii_dict, expected_dict)
        ebcdic_dict = _iso8583_to_dict(message_ebcdic_raw, config["bit_config"], "cp500")
        self.assertEqual(ebcdic_dict, expected_dict)

    def test_dict_to_iso8583(self):
        source_dict = {'MTI': '1144', 'DE2': '4444555544445555', 'DE3': '111111', 'PDS0001': '1', 'PDS9999': 'Z'}
        actual_iso = _dict_to_iso8583(source_dict, config['bit_config'])
        expected_iso = (b'1144\xe0\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00164444555544445555111111'
                        b'016000100119999001Z')
        print(actual_iso)
        self.assertEqual(expected_iso, actual_iso)

    def test_dict_to_pds_to_de(self):
        vals = {'PDS0001': '123', 'PDS9999': 'ABCDEF'}
        outs = _pds_to_de(vals)
        print(outs)
        self.assertEqual(_pds_to_dict(outs.pop()), vals)

    def test_pds_to_de_multiple_fields(self):
        vals = {'PDS0001': '*' * 900, 'PDS9999': '!' * 900}
        outs = _pds_to_de(vals)
        print(outs)
        self.assertEqual(_pds_to_dict(outs.pop()), {'PDS9999': '!' * 900})
        self.assertEqual(_pds_to_dict(outs.pop()), {'PDS0001': '*' * 900})

    def test_pds_to_de_no_pds_fields(self):
        vals = {'DE1': '*', 'DE2': '*'}
        outs = _pds_to_de(vals)
        print(outs)
        self.assertListEqual(outs, [])


if __name__ == '__main__':
    unittest.main()
