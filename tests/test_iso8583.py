import binascii
import datetime
import decimal
import unittest

from cardutil import CardutilError
from cardutil.config import config
from cardutil.iso8583 import (
    BitArray, _iso8583_to_field, _field_to_iso8583, _iso8583_to_dict, _dict_to_iso8583, loads, dumps,
    _pds_to_de, _pds_to_dict, _pytype_to_string, _icc_to_dict, _get_de43_fields, _get_date_from_string,
    Iso8583DataError)

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
        print(outs, flush=True)
        self.assertEqual(outs.pop(), '00010031239999006ABCDEF')

    def test_pds_to_de_multiple_fields(self):
        vals = {'PDS0001': '*' * 900, 'PDS9999': '!' * 900}
        outs = _pds_to_de(vals)
        print(outs)
        self.assertEqual(_pds_to_dict(outs.pop(), {}), {'PDS9999': '!' * 900})
        self.assertEqual(_pds_to_dict(outs.pop(), {}), {'PDS0001': '*' * 900})

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

    def test_icc_to_dict_error_handling_incomplete_de55(self):
        """Test DE55 with incomplete data (missing length byte)"""
        # DE55 with tag 9F02 but missing length byte
        incomplete_data = binascii.a2b_hex("9f02")

        # Should raise exception
        with self.assertRaises(CardutilError):
            _icc_to_dict(incomplete_data, "on_error=ERROR")

        # Should work with WARN mode
        result = _icc_to_dict(incomplete_data, "on_error=WARN")
        self.assertIn("ICC_DATA", result)
        self.assertNotIn("TAG9F02", result)
        self.assertEqual(result["ICC_DATA"], "9f02")

    def test_icc_to_dict_error_handling_truncated_de55(self):
        """Test DE55 with truncated data (length says more data than available)"""
        # DE55 with tag 9F02, length=06 but only 2 bytes of data
        truncated_data = binascii.a2b_hex("9f02060000")

        # Should raise exception
        with self.assertRaises(CardutilError):
            _icc_to_dict(truncated_data, "on_error=ERROR")

        # Should work with WARN mode
        result = _icc_to_dict(truncated_data, "on_error=WARN")
        self.assertIn("ICC_DATA", result)
        self.assertNotIn("TAG9F02", result)
        self.assertEqual(result["ICC_DATA"], "9f02060000")

    def test_icc_to_dict_error_handling_empty_de55(self):
        """Test with empty DE55 data"""
        empty_data = b""
        result = _icc_to_dict(empty_data)

        # Should only have ICC_DATA (empty)
        self.assertIn("ICC_DATA", result)
        self.assertEqual(result["ICC_DATA"], "")

    def test_icc_to_dict_error_handling_partial_valid_de55(self):
        """Test DE55 with partially valid data"""
        # Valid tag 9F02, then invalid data (9F03 without length)
        partial_data = binascii.a2b_hex("9f02060000000010009f03")

        # Should raise exception
        with self.assertRaises(CardutilError):
            _icc_to_dict(partial_data, "on_error=ERROR")

        # Should work with WARN mode
        result = _icc_to_dict(partial_data, "on_error=WARN")
        self.assertIn("ICC_DATA", result)
        self.assertIn("TAG9F02", result)
        self.assertNotIn("TAG9F03", result)
        self.assertEqual(result["TAG9F02"], "000000001000")

    def test_icc_to_dict_error_handling_zero_tag(self):
        """Test that zero tag (0x00) stops processing"""
        # Data with tag 9F02, then 00 tag, then more data (which should be ignored)
        zero_tag_data = binascii.a2b_hex("9f020600000000100000009f030600000000000000")
        result = _icc_to_dict(zero_tag_data)

        # Should have only TAG9F02, processing stops at 00
        self.assertIn("TAG9F02", result)
        self.assertNotIn("TAG9F03", result)
        self.assertEqual(result["TAG9F02"], "000000001000")

    def test_icc_to_dict_error_handling_invalid_de55_no_exception(self):
        """Test that various invalid DE55 formats don't raise exceptions with WARN mode"""
        invalid_cases = [
            b"",  # Empty (valid case, no exception)
            binascii.a2b_hex("9f"),  # Incomplete 2-byte tag
            binascii.a2b_hex("9f02"),  # Missing length
            binascii.a2b_hex("9f0210"),  # Length says 16 bytes but no data
            binascii.a2b_hex("ff"),  # Single invalid byte
            binascii.a2b_hex("9f02060000000010009f"),  # 9F tag at end, no length
            binascii.a2b_hex("9f0206000000001000c1"),  # C1 tag at end, no length
        ]

        for i, invalid_data in enumerate(invalid_cases):
            with self.subTest(case=i):
                # Should not raise any exception with WARN mode
                try:
                    result = _icc_to_dict(invalid_data, "on_error=WARN")
                    self.assertIsInstance(result, dict)
                    self.assertIn("ICC_DATA", result)
                except Exception as e:
                    self.fail(f"Case {i} raised unexpected exception: {e}")

                # Test ERROR mode behavior
                if i == 0:  # Empty data case - should not raise exception
                    result = _icc_to_dict(invalid_data, "on_error=ERROR")
                    self.assertIsInstance(result, dict)
                    self.assertIn("ICC_DATA", result)
                    self.assertEqual(result["ICC_DATA"], "")
                else:  # All other cases should raise exception
                    with self.assertRaises(CardutilError):
                        _icc_to_dict(invalid_data, "on_error=ERROR")

    def test_icc_to_dict_error_handling_multiple_valid_tags(self):
        """Test extraction of multiple valid EMV tags even with errors"""
        # Multiple valid tags followed by invalid data
        data = binascii.a2b_hex(
            "9f02060000000010009f03060000000000009f1a0208409f2608"
            "1234567890abcdef82021800950500800000009a03201231"
            "9c01005f2a0208409f3704aabbccdd9f"  # Ends with incomplete tag
        )

        # Should raise exception
        with self.assertRaises(CardutilError):
            _icc_to_dict(data, "on_error=ERROR")

        # Should work with WARN mode
        result = _icc_to_dict(data, "on_error=WARN")

        # Verify valid tags are extracted despite the error at the end
        expected_tags = [
            "TAG9F02",
            "TAG9F03",
            "TAG9F1A",
            "TAG9F26",
            "TAG82",
            "TAG95",
            "TAG9A",
            "TAG9C",
            "TAG5F2A",
            "TAG9F37",
        ]
        for tag in expected_tags:
            self.assertIn(tag, result, f"Missing {tag}")

        # Verify some values
        self.assertEqual(result["TAG9F02"], "000000001000")
        self.assertEqual(result["TAG9F26"], "1234567890abcdef")

    def test_icc_to_dict_error_handling_configurable_behavior(self):
        """Test that error handling behavior can be configured"""
        # Test data with incomplete tag at end
        incomplete_data = binascii.a2b_hex("9f02060000000010009f")

        # Test ERROR behavior
        with self.assertRaises(CardutilError):
            _icc_to_dict(incomplete_data, "on_error=ERROR")

        # Test WARN behavior
        result_warn = _icc_to_dict(incomplete_data, "on_error=WARN")
        self.assertIn("ICC_DATA", result_warn)
        self.assertIn("TAG9F02", result_warn)
        self.assertEqual(result_warn["TAG9F02"], "000000001000")

    def test_icc_to_dict_error_handling_error_mode(self):
        """Test ERROR mode - should raise exceptions for any error (default behavior)"""
        # Test with various malformed data
        malformed_cases = [
            (binascii.a2b_hex("9f"), "Incomplete 2-byte tag"),
            (binascii.a2b_hex("9f02"), "Missing length"),
            (binascii.a2b_hex("9f02060000"), "Length says 6 but only 2 bytes"),
            (binascii.a2b_hex("ff"), "Single invalid byte"),
        ]

        for i, (malformed_data, description) in enumerate(malformed_cases):
            with self.subTest(case=i, description=description):
                # Should raise exception
                with self.assertRaises(CardutilError):
                    _icc_to_dict(malformed_data, "on_error=ERROR")

    def test_icc_to_dict_error_handling_integration_with_iso8583(self):
        """Verify DE55 error handling toggles via field_processor_config through dumps/loads."""
        # Use repo default bit_config (expected WARN by default)
        base_bit_cfg = config["bit_config"]
        malformed_de55 = binascii.a2b_hex("9F")  # incomplete 2-byte tag

        # Default (WARN): should NOT raise
        msg_warn = dumps(
            {"MTI": "0100", "DE2": "4444555566667777", "DE55": malformed_de55},
            iso_config=base_bit_cfg,
        )
        out = loads(msg_warn, iso_config=base_bit_cfg)
        self.assertIn("DE2", out)
        self.assertEqual(out["DE2"], "4444555566667777")
        self.assertIn("ICC_DATA", out)
        self.assertTrue(all(not k.startswith("TAG") for k in out.keys()))

        # Force ERROR without importing copy: shallow copy + copy only "55" sub-dict
        cfg_error = dict(config["bit_config"])
        if isinstance(cfg_error["55"], dict):
            cfg_error["55"] = dict(cfg_error["55"])
            cfg_error["55"]["field_processor_config"] = "on_error=ERROR"
        else:
            self.skipTest("cfg_error['55'] is not a dict, cannot set field_processor_config")

        msg_error = dumps(
            {"MTI": "0100", "DE2": "4444555566667777", "DE55": malformed_de55},
            iso_config=cfg_error,
        )
        with self.assertRaises(CardutilError):
            loads(msg_error, iso_config=cfg_error)

        # Force ERROR without importing copy: shallow copy + copy only "55" sub-dict
        cfg_error2 = dict(config["bit_config"])
        if isinstance(cfg_error2["55"], dict):
            cfg_error2["55"] = dict(cfg_error2["55"])
            cfg_error2["55"]["field_processor_config"] = "on_error=ERROR"
        else:
            self.skipTest("cfg_error2['55'] is not a dict, cannot set field_processor_config")

        msg_error2 = dumps(
            {"MTI": "0100", "DE2": "4444555566667777", "DE55": malformed_de55},
            iso_config=cfg_error2,
        )
        with self.assertRaises(CardutilError):
            loads(msg_error2, iso_config=cfg_error2)

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

    def test_pds_subfield_parsing(self):
        """Test PDS subfield parsing with the example from the requirements"""
        # Test data from the requirements document
        # PDS0105 with value: '0012312040000003206201101'
        # Expected subfields:
        # - File Type (pos 0-3): '001'
        # - File Reference Date (pos 3-9): '231204'
        # - Processor ID (pos 9-20): '00000032062'
        # - File Sequence Number (pos 20-25): '01101'

        pds_field_data = "010502500123120400000032062011010122001T"

        # Parse the PDS field
        result = _pds_to_dict(pds_field_data)

        # Verify basic PDS field parsing still works
        self.assertIn('PDS0105', result)
        self.assertEqual(result['PDS0105'], '0012312040000003206201101')
        self.assertIn('PDS0122', result)
        self.assertEqual(result['PDS0122'], 'T')

        # Verify subfield parsing for PDS0105
        self.assertIn('PDS0105_SF1', result)  # File Type
        self.assertIn('PDS0105_SF2', result)  # File Reference Date
        self.assertIn('PDS0105_SF3', result)  # Processor ID
        self.assertIn('PDS0105_SF4', result)  # File Sequence Number

        # Verify subfield values
        self.assertEqual(result['PDS0105_SF1'], '001')          # File Type
        self.assertEqual(result['PDS0105_SF2'], '231204')       # File Reference Date
        self.assertEqual(result['PDS0105_SF3'], '00000032062')  # Processor ID
        self.assertEqual(result['PDS0105_SF4'], '01101')        # File Sequence Number

    def test_iso8583_message_with_pds_subfields(self):
        """Test parsing a complete ISO8583 message with PDS subfields"""
        # Create a test message similar to the example in requirements
        # MTI=1644, DE24=697, DE48 contains PDS fields
        test_message_dict = {
            'MTI': '1644',
            'DE24': '697',
            'DE48': '010502500123120400000032062011010122001T',
            'DE71': 1
        }

        # Convert to ISO8583 bytes and back to test round-trip
        message_bytes = dumps(test_message_dict)

        # Parse the message back
        parsed_dict = loads(message_bytes)

        # Verify the expected structure from requirements
        expected_keys = ['MTI', 'DE24', 'DE48', 'PDS0105', 'PDS0122', 'DE71']
        for key in expected_keys:
            self.assertIn(key, parsed_dict, f"Missing key: {key}")

        # Verify PDS subfields are present
        subfield_keys = ['PDS0105_SF1', 'PDS0105_SF2', 'PDS0105_SF3', 'PDS0105_SF4']
        for key in subfield_keys:
            self.assertIn(key, parsed_dict, f"Missing subfield: {key}")

    def test_pds_custom_config(self):
        """Test PDS parsing with custom configuration"""
        # Create custom PDS config for testing
        custom_pds_config = {
            "0999": {
                "subfields": {
                    "1": {"field_start": 0, "field_name": "Custom Field 1", "field_length": 5,
                          "field_python_type": "string"},
                    "2": {"field_start": 5, "field_name": "Custom Field 2", "field_length": 3,
                          "field_python_type": "int"}
                }
            }
        }

        # Test data with PDS0999
        test_data = "099900812345678"  # PDS0999, length 008, data "12345678"

        result = _pds_to_dict(test_data, custom_pds_config)

        # Verify parsing
        self.assertIn('PDS0999', result)
        self.assertEqual(result['PDS0999'], '12345678')
        self.assertIn('PDS0999_SF1', result)
        self.assertEqual(result['PDS0999_SF1'], '12345')
        self.assertIn('PDS0999_SF2', result)
        self.assertEqual(result['PDS0999_SF2'], 678)  # Should be converted to int

    def test_pds_multiple_fields_with_subfields(self):
        """Test parsing multiple PDS fields with subfields"""
        # Test data with multiple PDS fields
        test_data = "010502500123120400000032062011010122001T009900512345"

        result = _pds_to_dict(test_data)

        # Should have both PDS0105 and PDS0099
        self.assertIn('PDS0105', result)
        self.assertIn('PDS0122', result)
        self.assertIn('PDS0099', result)

        # PDS0105 should have subfields
        self.assertIn('PDS0105_SF1', result)
        self.assertIn('PDS0105_SF2', result)
        self.assertIn('PDS0105_SF3', result)
        self.assertIn('PDS0105_SF4', result)

        # PDS0099 should not have subfields (no config)
        subfield_keys_0099 = [k for k in result.keys() if k.startswith('PDS0099_SF')]
        self.assertEqual(len(subfield_keys_0099), 0, "PDS0099 should not have subfields")

    def test_pds_subfield_int_conversion_error(self):
        """Test PDS subfield parsing when integer conversion fails"""
        # Create custom PDS config with an integer field that will fail conversion
        custom_pds_config = {
            "0888": {
                "subfields": {
                    "1": {"field_start": 0, "field_name": "Valid String", "field_length": 3,
                          "field_python_type": "string"},
                    "2": {"field_start": 3, "field_name": "Invalid Int", "field_length": 3,
                          "field_python_type": "int"},
                    "3": {"field_start": 6, "field_name": "Valid Int", "field_length": 3,
                          "field_python_type": "int"}
                }
            }
        }

        # Test data with PDS0888: "ABC" (string), "XYZ" (invalid int), "123" (valid int)
        test_data = "0888009ABCXYZ123"  # PDS0888, length 009, data "ABCXYZ123"

        result = _pds_to_dict(test_data, custom_pds_config)

        # Verify parsing
        self.assertIn('PDS0888', result)
        self.assertEqual(result['PDS0888'], 'ABCXYZ123')

        # Verify subfields
        self.assertIn('PDS0888_SF1', result)
        self.assertEqual(result['PDS0888_SF1'], 'ABC')  # String field works normally

        self.assertIn('PDS0888_SF2', result)
        self.assertEqual(result['PDS0888_SF2'], 'XYZ')  # Should remain as string due to ValueError

        self.assertIn('PDS0888_SF3', result)
        self.assertEqual(result['PDS0888_SF3'], 123)    # Should be converted to int successfully

    def test_pds_subfield_decimal_conversion_error(self):
        """Test PDS subfield parsing when decimal conversion fails"""
        # Create custom PDS config with a decimal field that will fail conversion
        custom_pds_config = {
            "0777": {
                "subfields": {
                    "1": {"field_start": 0, "field_name": "Valid Decimal", "field_length": 5,
                          "field_python_type": "decimal"},
                    "2": {"field_start": 5, "field_name": "Invalid Decimal", "field_length": 5,
                          "field_python_type": "decimal"},
                    "3": {"field_start": 10, "field_name": "Valid String", "field_length": 3,
                          "field_python_type": "string"}
                }
            }
        }

        # Test data with PDS0777: "12.34" (valid decimal), "ABC.X" (invalid decimal), "DEF" (string)
        test_data = "077701312.34ABC.XDEF"  # PDS0777, length 013, data "12.34ABC.XDEF"

        result = _pds_to_dict(test_data, custom_pds_config)

        # Verify parsing
        self.assertIn('PDS0777', result)
        self.assertEqual(result['PDS0777'], '12.34ABC.XDEF')

        # Verify subfields
        self.assertIn('PDS0777_SF1', result)
        self.assertEqual(result['PDS0777_SF1'], decimal.Decimal('12.34'))  # Should be converted to decimal

        self.assertIn('PDS0777_SF2', result)
        self.assertEqual(result['PDS0777_SF2'], 'ABC.X')  # Should remain as string due to conversion error

        self.assertIn('PDS0777_SF3', result)
        self.assertEqual(result['PDS0777_SF3'], 'DEF')    # String field works normally

    def test_icc_to_dict_empty_length_byte(self):
        """Test that _icc_to_dict raises or warns on empty length byte for a tag"""
        from cardutil.iso8583 import _icc_to_dict, Iso8583DataError
        import binascii

        # Tag 9F02, but no length byte follows
        data = binascii.a2b_hex("9f02")
        # ERROR mode: should raise
        with self.assertRaises(Iso8583DataError):
            _icc_to_dict(data, "on_error=ERROR")
        # WARN mode: should not raise, ICC_DATA should be present, no TAG9F02
        result = _icc_to_dict(data, "on_error=WARN")
        self.assertIn("ICC_DATA", result)
        self.assertNotIn("TAG9F02", result)
        self.assertEqual(result["ICC_DATA"], "9f02")

    def test_icc_to_dict_invalid_processor_config(self):
        """Test _icc_to_dict with various invalid processor configurations"""
        # Use simpler valid test data that won't cause insufficient data errors
        test_data = binascii.a2b_hex("9f02060000000010009f03060000000000")

        # Test with malformed config strings
        invalid_configs = [
            "invalid_config_string",
            "key_without_equals",
            "key=value;malformed",
            "=empty_key",
            "key=",
            ";semicolon_start",
            "key=value;",
            None,
            "",
            123,  # Non-string type
            {"dict": "not_string"},  # Dict instead of string
        ]

        for invalid_config in invalid_configs:
            with self.subTest(config=invalid_config):
                # Should not raise exception, should use default WARN behavior
                result = _icc_to_dict(test_data, invalid_config)
                self.assertIsInstance(result, dict)
                self.assertIn("ICC_DATA", result)
                # Should parse the first valid tag at least
                self.assertIn("TAG9F02", result)
                # Second tag might not parse due to insufficient data, which is expected

    def test_icc_to_dict_processor_config_parsing(self):
        """Test that processor config is parsed correctly"""
        # Use simpler valid test data
        test_data = binascii.a2b_hex("9f02060000000010000000")  # Extended to avoid insufficient data

        # Test valid config parsing
        valid_configs = [
            "on_error=ERROR",
            "on_error=WARN",
            "on_error=error",  # Test case insensitive
            "on_error=warn",
            "on_error=ERROR;other_key=value",
            "other_key=value;on_error=WARN",
            "key1=val1;on_error=ERROR;key2=val2",
        ]

        for valid_config in valid_configs:
            with self.subTest(config=valid_config):
                # Should not raise for valid data
                result = _icc_to_dict(test_data, valid_config)
                self.assertIn("TAG9F02", result)

    def test_icc_to_dict_no_field_tag_scenarios(self):
        """Test scenarios where field_tag is empty or missing"""

        # Test 1: Data ends abruptly, no tag available
        truncated_data = b""

        # ERROR mode
        result_error = _icc_to_dict(truncated_data, "on_error=ERROR")
        self.assertIn("ICC_DATA", result_error)
        self.assertEqual(result_error["ICC_DATA"], "")

        # WARN mode
        result_warn = _icc_to_dict(truncated_data, "on_error=WARN")
        self.assertIn("ICC_DATA", result_warn)
        self.assertEqual(result_warn["ICC_DATA"], "")

    def test_icc_to_dict_empty_field_length_raw(self):
        """Test scenarios where field_length_raw is empty"""

        # This is a tricky case - the field_length_raw check happens after we've
        # already read the tag, so we need data that gets to that point
        # but somehow has empty length data

        # Test with a single byte tag followed by end of data
        single_byte_tag_no_length = binascii.a2b_hex("01")  # Tag 01, but no length follows

        # ERROR mode
        with self.assertRaises(Iso8583DataError):
            _icc_to_dict(single_byte_tag_no_length, "on_error=ERROR")

        # WARN mode
        result = _icc_to_dict(single_byte_tag_no_length, "on_error=WARN")
        self.assertIn("ICC_DATA", result)
        self.assertNotIn("TAG01", result)
        self.assertEqual(result["ICC_DATA"], "01")

    def test_icc_to_dict_struct_unpack_error(self):
        """Test handling of struct.unpack errors in length processing"""
        # This tests the struct.unpack(">B", field_length_raw) call
        # Since we're reading exactly 1 byte, struct.unpack should not normally fail
        # unless there's truly no data, which is covered by the empty length check

        # Test with tag but no length byte (different from previous test)
        tag_no_length = binascii.a2b_hex("82")  # Single byte tag, no length

        # ERROR mode
        with self.assertRaises(Iso8583DataError):
            _icc_to_dict(tag_no_length, "on_error=ERROR")

        # WARN mode
        result = _icc_to_dict(tag_no_length, "on_error=WARN")
        self.assertIn("ICC_DATA", result)
        self.assertEqual(result["ICC_DATA"], "82")

    def test_icc_to_dict_comprehensive_error_coverage(self):
        """Comprehensive test covering all error conditions with both WARN and ERROR modes"""

        error_cases = [
            # Case 1: Incomplete 2-byte tag (9F without second byte)
            {
                "data": binascii.a2b_hex("9f"),
                "description": "Incomplete 2-byte tag",
                "error_msg_contains": "Incomplete 2-byte tag"
            },
            # Case 2: 2-byte tag with no length
            {
                "data": binascii.a2b_hex("9f02"),
                "description": "2-byte tag with no length",
                "error_msg_contains": "No length byte available"
            },
            # Case 3: Tag with insufficient data for declared length
            {
                "data": binascii.a2b_hex("01050000"),  # Tag 01, length 05, but only 2 bytes of data
                "description": "Insufficient data for declared length",
                "error_msg_contains": "Insufficient data"
            },
            # Case 4: Single byte tag at end of data
            {
                "data": binascii.a2b_hex("82"),
                "description": "Single byte tag at end",
                "error_msg_contains": "No length byte available"
            }
        ]

        for i, case in enumerate(error_cases):
            with self.subTest(case=i, description=case["description"]):
                # Test ERROR mode - should raise exception
                with self.assertRaises(Iso8583DataError) as cm:
                    _icc_to_dict(case["data"], "on_error=ERROR")
                self.assertIn(case["error_msg_contains"], str(cm.exception))

                # Test WARN mode - should not raise exception
                result = _icc_to_dict(case["data"], "on_error=WARN")
                self.assertIsInstance(result, dict)
                self.assertIn("ICC_DATA", result)
                # Should not have any TAG entries due to errors
                tag_keys = [k for k in result.keys() if k.startswith("TAG")]
                self.assertEqual(len(tag_keys), 0)
                # Some cases might have partial success, so we just verify ICC_DATA exists
                self.assertTrue(len(result) >= 1)  # At least ICC_DATA

    def test_icc_to_dict_default_error_handling(self):
        """Test default error handling when no config is provided"""
        # Test with malformed data and no processor config
        malformed_data = binascii.a2b_hex("9f")

        # Default should be WARN mode
        result = _icc_to_dict(malformed_data)
        self.assertIn("ICC_DATA", result)
        self.assertEqual(result["ICC_DATA"], "9f")

        # Explicit None config
        result2 = _icc_to_dict(malformed_data, None)
        self.assertIn("ICC_DATA", result2)
        self.assertEqual(result2["ICC_DATA"], "9f")

    def test_icc_to_dict_exception_in_try_block(self):
        """Test generic exception handling in the try block"""
        # Use valid data that has sufficient bytes for the declared length
        valid_start = binascii.a2b_hex("9f02060000000010000000")  # Valid tag with enough data

        # This should process successfully
        result = _icc_to_dict(valid_start, "on_error=ERROR")
        self.assertIn("TAG9F02", result)

        # Test with data that might cause other types of exceptions
        # (though most are already covered by specific error checks)
        edge_case_data = binascii.a2b_hex("9f0200")  # Tag with zero length

        result_warn = _icc_to_dict(edge_case_data, "on_error=WARN")
        self.assertIn("ICC_DATA", result_warn)
        self.assertIn("TAG9F02", result_warn)
        self.assertEqual(result_warn["TAG9F02"], "")

    def test_icc_to_dict_processor_config_exception_handling(self):
        """Test exception handling in processor config parsing"""
        # Use valid data that will parse successfully
        test_data = binascii.a2b_hex("01024142")  # Tag 01, length 02, data "AB"

        # Create a config that will cause an exception during parsing
        # We'll use a config that causes str().split() to fail
        class BadConfigObject:
            def __str__(self):
                raise ValueError("Intentional error in str() method")

            def split(self, sep):
                raise AttributeError("split method not available")

        bad_config = BadConfigObject()

        # This should handle the exception gracefully and use default config
        result = _icc_to_dict(test_data, bad_config)
        self.assertIsInstance(result, dict)
        self.assertIn("ICC_DATA", result)
        self.assertIn("TAG01", result)
        self.assertEqual(result["TAG01"], "4142")

    def test_icc_to_dict_empty_length_byte_error_specific(self):
        """Test 'Empty length byte' error when field_length_raw is falsy"""
        # This tests the condition where we have a tag but field_pointer >= len(field_data)
        # when trying to read the length byte

        test_data = binascii.a2b_hex("01")  # Just a tag, no length

        # This triggers "No length byte available" error
        with self.assertRaises(Iso8583DataError) as cm:
            _icc_to_dict(test_data, "on_error=ERROR")
        self.assertIn("No length byte available", str(cm.exception))

        # WARN mode should handle gracefully
        result_warn = _icc_to_dict(test_data, "on_error=WARN")
        self.assertIn("ICC_DATA", result_warn)
        self.assertEqual(result_warn["ICC_DATA"], "01")
        self.assertNotIn("TAG01", result_warn)
