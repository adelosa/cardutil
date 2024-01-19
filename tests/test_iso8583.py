import binascii
import datetime
import decimal
import unittest

from cardutil import CardutilError
from cardutil.config import config
from cardutil.iso8583 import (
    BitArray, _iso8583_to_field, _field_to_iso8583, _iso8583_to_dict, _dict_to_iso8583, loads, dumps,
    _pds_to_de, _pds_to_dict, _pytype_to_string, _icc_to_dict, _get_de43_fields, _get_date_from_string)

from tests import message_ebcdic_raw, message_ascii_raw, message_ascii_raw_hex, message_ebcdic_raw_hex


class Iso8583TestCase(unittest.TestCase):
    def test_dumps(self):
        # use config from package
        out_data = dumps({'MTI': '1234', 'DE2': '123'})
        self.assertEqual(b'1234\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0003123', out_data)

        # explicitly pass the config
        out_data = dumps({'MTI': '1234', 'DE2': '123'}, iso_config=config["bit_config"])
        self.assertEqual(b'1234\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0003123', out_data)

    def test_dumps_with_no_values(self):
        # check that empty fields are not added as elements to ISO output
        in_data_empty = {'MTI': '1234', 'DE2': '', 'DE3': None, 'DE4': 0}
        out_data_empty = loads(dumps(in_data_empty))
        print(out_data_empty)
        self.assertEqual({'MTI': '1234', 'DE4': 0}, out_data_empty)

    def test_dumps_hex_bitmap(self):
        out_data = dumps({'MTI': '1234', 'DE2': '123'}, hex_bitmap=True)
        self.assertEqual(b'1234c000000000000000000000000000000003123', out_data)

    def test_loads(self):
        self.assertEqual(
            {'MTI': '1234', 'DE2': '123'}, loads(dumps({'MTI': '1234', 'DE2': '123'}), iso_config=config['bit_config']))
        self.assertEqual({'MTI': '1234', 'DE2': '123'}, loads(dumps({'MTI': '1234', 'DE2': '123'})))

    def test_dump_load_ascii(self):
        self.assertEqual(message_ascii_raw, dumps(loads(message_ascii_raw)))
        self.assertEqual(message_ascii_raw_hex, dumps(loads(message_ascii_raw), hex_bitmap=True))

    def test_dump_load_ebcdic(self):
        self.assertEqual(message_ebcdic_raw, dumps(loads(message_ebcdic_raw, encoding='cp500'), encoding='cp500'))
        self.assertEqual(
            message_ebcdic_raw_hex,
            dumps(loads(message_ebcdic_raw_hex, encoding='cp500', hex_bitmap=True), encoding='cp500', hex_bitmap=True))

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
            ({'DE1': '456432******1122'}, 18),
            _iso8583_to_field(
                '1', {'field_type': 'LLVAR', 'field_length': 0, 'field_processor': 'PAN'}, b'164564320012321122'))
        self.assertEqual(
            ({'DE1': '456432001'}, 18),
            _iso8583_to_field(
                '1', {'field_type': 'LLVAR', 'field_length': 0, 'field_processor': 'PAN-PREFIX'},
                b'164564320012321122'))
        self.assertEqual(
            ({'DE1': b'\x01\x01\xff', 'ICC_DATA': '0101ff', 'TAG01': 'ff'}, 5),
            _iso8583_to_field(
                '1', {'field_type': 'LLVAR', 'field_length': 0, 'field_processor': 'ICC'}, b'03\x01\x01\xFF'))
        self.assertEqual(
            ({'DE1': '4564320012321122'}, 19),
            _iso8583_to_field('1', {'field_type': 'LLLVAR', 'field_length': 0}, b'0164564320012321122'))
        self.assertEqual(
            ({'DE1': '4564320012321122    '}, 20),
            _iso8583_to_field('1', {'field_type': 'FIXED', 'field_length': 20}, b'4564320012321122    '))
        self.assertEqual(
            ({'DE1': 1234}, 20),
            _iso8583_to_field(
                '1', {'field_type': 'FIXED', 'field_python_type': 'int', 'field_length': 20}, b'00000000000000001234'))
        self.assertEqual(
            ({'DE1': 1234}, 6),
            _iso8583_to_field('1', {'field_type': 'LLVAR', 'field_python_type': 'int', 'field_length': 0}, b'041234'))
        self.assertEqual(
            ({'DE1': decimal.Decimal('123.432')}, 20),
            _iso8583_to_field('1', {'field_type': 'FIXED', 'field_python_type': 'decimal', 'field_length': 20},
                              b'0000000000000123.432'))
        # trigger decode error field length
        with self.assertRaises(CardutilError):
            _iso8583_to_field('1', {'field_type': 'LLVAR', 'field_length': 0}, b'\x00\x004564320012321122')
        # unable to decode field length
        with self.assertRaises(CardutilError):
            _iso8583_to_field('01', {"field_type": "LLLVAR", "field_length": 255}, b'01\xff', encoding='ascii')
        # invalid field length
        with self.assertRaises(CardutilError):
            _iso8583_to_field('01', {"field_type": "LLLVAR", "field_length": 255}, b'01X.', encoding='ascii')
        # unable to decode field value
        with self.assertRaises(CardutilError):
            _iso8583_to_field('01', {"field_type": "LLLVAR", "field_length": 255}, b'001\xff', encoding='ascii')
        # unable to convert to python value

        with self.assertRaises(CardutilError):
            _iso8583_to_field('1', {'field_type': 'LLVAR', 'field_python_type': 'int', 'field_length': 0}, b'04XXXX')

    def test_field_to_iso8583(self):
        self.assertEqual(b'164564320012321122', _field_to_iso8583({'field_type': 'LLVAR'}, "4564320012321122"))
        self.assertEqual(
            b'164564320012321122', _field_to_iso8583({'field_type': 'LLVAR', 'field_length': 0}, "4564320012321122"))
        self.assertEqual(b'0164564320012321122', _field_to_iso8583({'field_type': 'LLLVAR'}, "4564320012321122"))
        self.assertEqual(
            b'0164564320012321122', _field_to_iso8583({'field_type': 'LLLVAR', 'field_length': 0}, "4564320012321122"))
        self.assertEqual(
            b'4564320012321122    ', _field_to_iso8583({'field_type': 'FIXED', 'field_length': 20}, "4564320012321122"))
        self.assertEqual(
            b'00000000000000001234', _field_to_iso8583(
                {'field_type': 'FIXED', 'field_python_type': 'int', 'field_length': 20}, 1234))
        self.assertEqual(
            b'041234', _field_to_iso8583({'field_type': 'LLVAR', 'field_python_type': 'int'}, 1234))
        self.assertEqual(
            b'041234', _field_to_iso8583({'field_type': 'LLVAR', 'field_python_type': 'int'}, '1234'))
        # TODO Exception if field overflow
        self.assertEqual(
            b'123', _field_to_iso8583({'field_type': 'FIXED', 'field_python_type': 'int', 'field_length': 3}, 1234))
        self.assertEqual(
            b'01234', _field_to_iso8583({'field_type': 'FIXED', 'field_python_type': 'int', 'field_length': 5}, 1234))

        self.assertEqual(
            b'041234', _field_to_iso8583({'field_type': 'LLVAR', 'field_python_type': 'int', 'field_length': 0}, 1234))

        self.assertEqual(
            b'0000000000000123.432', _field_to_iso8583(
                {'field_type': 'FIXED', 'field_python_type': 'decimal', 'field_length': 20},
                decimal.Decimal("123.432")))
        self.assertEqual(
            b'140102151610', _field_to_iso8583(
                {'field_type': 'FIXED', 'field_python_type': 'datetime',
                 'field_length': 12, "field_date_format": "%y%m%d%H%M%S"},
                datetime.datetime(2014, 1, 2, 15, 16, 10)))

    def test_field_to_iso8583_binary_field(self):
        """
        https://github.com/adelosa/cardutil/issues/15
        Ensure function can support processing of byte values representing binary fields like DE55
        """
        bit_config = {
            'field_name': 'binary field', 'field_type': 'LLLVAR', 'field_length': 255}
        field_value = b'\x01\x01\x41\x9f\x01\x02\x12\x34'
        encoding = 'latin_1'
        field_output = _field_to_iso8583(bit_config, field_value, encoding)
        self.assertEqual(b'008\x01\x01A\x9f\x01\x02\x124', field_output)

    def test_iso8583_to_dict(self):
        expected_dict = {'MTI': '1144', 'DE2': '4444555544445555', 'DE3': '111111', 'DE4': 9999,
                         'DE12': datetime.datetime(2015, 8, 15, 17, 15, 0),
                         'DE22': '123456789012', 'DE24': '333', 'DE26': 1234,
                         'DE31': '57995799120000001230612', 'DE33': '123456', 'DE38': '123456',
                         'DE42': '579942111111111', 'DE43': 'BIG BOBS\\80 KERNDALE ST\\DANERLEY\\3103      VICAUS',
                         'DE43_NAME': 'BIG BOBS', 'DE43_ADDRESS': '80 KERNDALE ST', 'DE43_SUBURB': 'DANERLEY',
                         'DE43_POSTCODE': '3103', 'DE43_STATE': 'VIC', 'DE43_COUNTRY': 'AUS',
                         'DE48': '0001001Y', 'PDS0001': 'Y', 'DE49': '999', 'DE63': '0000000000000001',
                         'DE71': 12345678, 'DE94': '999999'}

        ascii_dict = _iso8583_to_dict(message_ascii_raw, config["bit_config"], "ascii")
        self.assertEqual(ascii_dict, expected_dict)
        ebcdic_dict = _iso8583_to_dict(message_ebcdic_raw, config["bit_config"], "cp500")
        self.assertEqual(ebcdic_dict, expected_dict)

        # check exception when full message not processed
        with self.assertRaises(CardutilError):
            _iso8583_to_dict(message_ascii_raw + b' ', config["bit_config"], "ascii")

        # check exception when cannot unpack mti and bitmap (struct error)
        with self.assertRaises(CardutilError):
            _iso8583_to_dict(b'\x00TI0', config["bit_config"], "ascii")

        # check exception when cannot decode MTI
        with self.assertRaises(CardutilError):
            _iso8583_to_dict(b'\xFFBCDFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF.....', config["bit_config"],
                             encoding="ascii", hex_bitmap=True)

        # check exception when bit config not found
        with self.assertRaises(CardutilError):
            _iso8583_to_dict(message_ascii_raw, {}, "ascii")

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

    def test_pytype_to_string(self):
        self.assertEqual('ABC', _pytype_to_string('ABC', {'field_python_type': 'string', 'field_length': 5}))
        self.assertEqual('ABC', _pytype_to_string('ABC', {'field_length': 5}))
        self.assertEqual('00001', _pytype_to_string('1', {'field_python_type': 'int', 'field_length': 5}))
        self.assertEqual('00001', _pytype_to_string('1', {'field_python_type': 'long', 'field_length': 5}))
        self.assertEqual(
            '180101171500', _pytype_to_string(datetime.datetime(2018, 1, 1, 17, 15), {
                'field_python_type': 'datetime', 'field_date_format': '%y%m%d%H%M%S'}))

    def test_icc_to_dict(self):
        self.assertEqual(
            _icc_to_dict(b'\x01\x01\x41\x9f\x01\x02\x12\x34'),
            {'ICC_DATA': '0101419f01021234', 'TAG01': '41', 'TAG9F01': '1234'})

    def test_icc_to_dict_null_eof(self):
        # issue and test data provided by Diego Felipe Maia (diegofmaia28@hotmail.com)
        test_de55 = binascii.unhexlify(
            '9f26081c89a48c0c4c3a309f2701809f10120110a04001240000000000000000000000ff9f370401'
            'bd0f6d9f36020011950500000480009a031909069c01009f02060000000289985f2a020032820239'
            '009f1a0200329f03060000000000009f1e0837383636343738349f3303e0f0c89f3501009f090200'
            '009f34034203008407a0000000041010910aaf6f5977b4ca29250012000000000000000000000000'
            '00000000000000000000000000000000000000000000000000000000000000000000000000000000'
            '00000000000000000000000000000000000000000000000000000000000000000000000000000000'
            '000000000000000000000000000000')
        print(_icc_to_dict(test_de55))

    def test_get_de43_fields(self):
        default_processor_config = config['bit_config']['43'].get('field_processor_config')
        # does not match
        self.assertEqual(_get_de43_fields('THIS DOES NOT MATCH REGEX', default_processor_config), {})
        # matches regex
        expected_dict = {'DE43_ADDRESS': '100 MAIN ST',
                         'DE43_COUNTRY': 'AUS',
                         'DE43_NAME': 'BOBS BURGERS',
                         'DE43_POSTCODE': '4102',
                         'DE43_STATE': 'QLD',
                         'DE43_SUBURB': 'WOOLLOONGABBA'}
        self.assertEqual(
            _get_de43_fields(
                'BOBS BURGERS\\100 MAIN ST\\WOOLLOONGABBA\\4102      QLDAUS', default_processor_config), expected_dict)
        custom_processor_config = r'(?P<DE43_ALL>.*)'
        self.assertEqual(
            _get_de43_fields('ALL FIELD', processor_config=custom_processor_config), {'DE43_ALL': 'ALL FIELD'})

        self.assertEqual(
            _get_de43_fields('SOME DATA', None), {})

    def test_get_de43_fields_international_addresses(self):
        default_processor_config = config['bit_config']['43'].get('field_processor_config')
        # United Kingdom
        de43_gbr = _get_de43_fields('The king\\Buckingham Palace\\LONDON\\SW1A 1AA     GBR', default_processor_config)
        self.assertEqual(de43_gbr['DE43_POSTCODE'], 'SW1A 1AA')
        self.assertEqual(de43_gbr['DE43_STATE'], '   ')
        self.assertEqual(de43_gbr['DE43_COUNTRY'], 'GBR')

        # Ireland
        de43_irl = _get_de43_fields('Guinness\\St James Gate\\DUBLIN\\D08 VF8H     IRL', default_processor_config)
        self.assertEqual(de43_irl['DE43_POSTCODE'], 'D08 VF8H')
        self.assertEqual(de43_irl['DE43_STATE'], '   ')
        self.assertEqual(de43_irl['DE43_COUNTRY'], 'IRL')

    def test_get_date_from_string_use_fromisodate(self):
        import builtins
        import sys

        # skip test if being run on py36 or less
        if sys.version_info < (3, 7):
            self.skipTest('Needs py37 or greater to run')

        real_import = builtins.__import__

        def mock_import(name, *vars):
            if name == 'dateutil.parser':
                raise ImportError
            else:
                return real_import(name, *vars)

        builtins.__import__ = mock_import
        self.get_date_from_string()
        builtins.__import__ = real_import

    def test_get_date_from_string_use_builtin(self):
        import sys
        import builtins

        real_version = sys.version_info
        sys.version_info = (3, 6)
        real_import = builtins.__import__

        def mock_import(name, *vars):
            if name == 'dateutil.parser':
                raise ImportError
            else:
                return real_import(name, *vars)

        builtins.__import__ = mock_import
        self.get_date_from_string()
        with self.assertRaises(ValueError):
            _get_date_from_string("11221-11-22")
        builtins.__import__ = real_import
        sys.version_info = real_version

    def test_get_date_from_string_use_dateutil(self):
        try:
            import dateutil
        except ImportError:
            self.skipTest('requires that python-dateutil is installed')
            return
        print(dateutil)
        self.get_date_from_string()

    def get_date_from_string(self):
        self.assertEqual(_get_date_from_string("2002-01-01"), datetime.datetime(2002, 1, 1))
        self.assertEqual(_get_date_from_string("2002-01-01 10:01"), datetime.datetime(2002, 1, 1, 10, 1))
        self.assertEqual(_get_date_from_string("2002-01-01 10:01:02"), datetime.datetime(2002, 1, 1, 10, 1, 2))


if __name__ == '__main__':
    unittest.main()
