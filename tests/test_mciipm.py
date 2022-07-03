import io
import unittest

from cardutil import CardutilError
from cardutil.mciipm import (
    VbsWriter, VbsReader, IpmReader, IpmWriter, Block1014, Unblock1014, block_1014, unblock_1014, vbs_list_to_bytes,
    vbs_bytes_to_list, IpmParamReader, MciIpmDataError)

from tests import message_ascii_raw, message_ebcdic_raw, print_stream


class MciIpmTestCase(unittest.TestCase):

    def test_mciipm_data_error_exception(self):
        err = MciIpmDataError("Message", record_number=1, binary_context_data=b'1234')
        assert str(err) == 'Message'
        assert err.record_number == 1
        assert err.binary_context_data == b'1234'

    def test_real_message_example_ascii(self):
        # create the input ipm file bytes -- test_file
        message_list = [message_ascii_raw for _ in range(15)]
        with io.BytesIO() as in_data:
            with VbsWriter(in_data, blocked=True) as writer:
                writer.write_many(message_list)

            print_stream(in_data, "VBS in data")

            # read vbs test file
            reader = IpmReader(in_data, blocked=True)
            results = list(reader)
        self.assertEqual(len(results), len(message_list))

    def test_ipm_reader_iso8583_exception(self):
        """
        Test what happens when the iso8583 rec raises an exemption
        """
        # create the input ipm file bytes -- test_file
        with io.BytesIO() as in_data:
            with VbsWriter(in_data, blocked=True) as writer:
                writer.write(b'bad ipm message')
            reader = IpmReader(in_data, blocked=True)
            with self.assertRaises(CardutilError):
                list(reader)

    def test_real_message_example_ebcdic(self):
        # write 1014 blocked test file
        message_list = [message_ebcdic_raw for _ in range(15)]
        with io.BytesIO() as in_data:
            with VbsWriter(in_data, blocked=True) as writer:
                writer.write_many(message_list)

            print_stream(in_data, "1014 blocked in data")

            # read blocked test file
            reader = IpmReader(in_data, encoding='cp500', blocked=True)
            results = list(reader)
            print(results)

        self.assertEqual(len(results), len(message_list))

    def test_ipmwriter_vbs_file(self):
        record = {'MTI': '1111', 'DE2': '8888999988889999'}
        records = [record for _ in range(5)]

        with io.BytesIO() as out_data:
            writer = IpmWriter(out_data)
            for record in records:
                writer.write(record)
            writer.close()

            print_stream(out_data, 'VBS output file')

            reader = IpmReader(out_data)
            results = list(reader)
            print(results)

        self.assertEqual(results, records)

    def test_ipm_reader_with_config(self):
        record = {'MTI': '1111', 'DE2': '8888999988889999'}
        # the following config applies the PAN masking formatter
        bit_config = {"2": {"field_name": "PAN", "field_type": "LLVAR", "field_length": 0, "field_processor": "PAN"}}
        records = [record]

        with io.BytesIO() as out_data:
            with IpmWriter(out_data) as writer:
                writer.write_many(records)

            print_stream(out_data, 'VBS output file')
            reader = IpmReader(out_data, iso_config=bit_config)

            results = list(reader)

        print(results)
        self.assertEqual(results, [{'MTI': '1111', 'DE2': '888899******9999'}])

    def test_ipmwriter_blocked_file(self):
        record = {'MTI': '1111', 'DE2': '8888999988889999'}
        records = [record for _ in range(5)]

        with io.BytesIO() as out_data:
            with IpmWriter(out_data, blocked=True) as writer:
                writer.write_many(records)

            print_stream(out_data, 'VBS output file')

            reader = IpmReader(out_data, blocked=True)
            results = list(reader)
            print(results)

        self.assertEqual(results, records)

    def test_vbsreader_vbs_file(self):
        # create the input file bytes -- test_file
        records = [b'12345678901234567890' for _ in range(5)]
        with io.BytesIO() as in_data:

            # write vbs test file
            writer = VbsWriter(in_data)
            for record in records:
                writer.write(record)
            else:
                writer.close()
            print_stream(in_data, "VBS in data")

            reader = VbsReader(in_data)
            results = list(reader)
            print(results)

        self.assertEqual(results, records)

    def test_vbsreader_vbs_file_missing_0_len(self):
        """
        The reader can handle VBS files that don't have final 0 length record
        """
        # create the input file bytes -- test_file
        records = [b'12345678901234567890' for _ in range(5)]
        with io.BytesIO() as in_data:

            # write vbs test file
            writer = VbsWriter(in_data)
            # don't call close method which writes the zero length record
            for record in records:
                writer.write(record)

            print_stream(in_data, "VBS in data")

            reader = VbsReader(in_data)
            results = list(reader)
            print(results)

        self.assertEqual(results, records)

    def test_vbsreader_blocked_file(self):
        # create the input file bytes -- test_file
        records = [b'12345678901234567890' for _ in range(5)]
        with io.BytesIO() as in_data:

            # write vbs test file
            writer = VbsWriter(in_data, blocked=True)
            for record in records:
                writer.write(record)
            else:
                writer.close()
            print_stream(in_data, "Blocked vbs data")

            reader = VbsReader(in_data, blocked=True)
            results = list(reader)
            print(results)
            self.assertEqual(results, records)

    def test_vbsreader_exceptions(self):
        # create the input file bytes -- test_file
        with io.BytesIO() as in_data:
            in_data.write(b'\xFF\xFF\x00\x00')  # negative length
            print_stream(in_data, "VBS in data")
            reader = VbsReader(in_data)
            with self.assertRaises(MciIpmDataError):
                list(reader)

        with io.BytesIO() as in_data:
            in_data.write(b'\x00\x00\x00\x05abcd')  # one byte short of record length (5)
            print_stream(in_data, "VBS in data")
            reader = VbsReader(in_data)
            with self.assertRaises(MciIpmDataError) as context:
                list(reader)
            assert str(context.exception) == "Unable to read complete record - record length: 5, data read: 4"
            assert context.exception.record_number == 1
            assert context.exception.binary_context_data == b"\x00\x00\x00\x05abcd"

    def test_file_blocker_compare(self):
        """
        Checks that the Block1014 class works the same as the
        :return:
        """
        out_unblocked = io.BytesIO()

        message_list = [message_ascii_raw for _ in range(10)]
        writer = VbsWriter(out_unblocked)
        for message in message_list:
            writer.write(message)
        writer.close()

        out_blocked = io.BytesIO()
        block_1014(out_unblocked, out_blocked)
        out_blocked.seek(0)
        blocked1 = out_blocked.read()
        print(blocked1)

        out_blocked2 = io.BytesIO()
        writer = VbsWriter(out_blocked2, blocked=True)
        for message in message_list:
            writer.write(message)
        writer.close()
        out_blocked2.seek(0)
        blocked2 = out_blocked2.read()
        print(blocked2)

        self.assertEqual(blocked1, blocked2)

        out_blocked.seek(0)
        out = io.BytesIO()
        unblock_1014(out_blocked, out)

        print_stream(out, "unblocked data")

    def test_unblock1014_exceptions(self):
        # create correct blocked
        message_list = [message_ascii_raw for _ in range(10)]
        out_blocked = io.BytesIO()
        writer = VbsWriter(out_blocked, blocked=True)
        for message in message_list:
            writer.write(message)
        writer.close()
        out_blocked.seek(0)
        blocked = out_blocked.read()
        print(blocked)

        # remove byte from end of file -- invalid file size
        out_blocked_missing_data = io.BytesIO(blocked[:-2])

        out_blocked_missing_data.seek(0)
        out = io.BytesIO()
        with self.assertRaises(CardutilError):
            unblock_1014(out_blocked_missing_data, out)

        # bad pad chars
        out_blocked_bad_fill = io.BytesIO(blocked[:-2] + b'$$')
        out_blocked_bad_fill.seek(0)
        out = io.BytesIO()
        with self.assertRaises(CardutilError):
            unblock_1014(out_blocked_bad_fill, out)

    def test_write_read_large_records(self):
        """
        Checks that the Block1014 class handles large records (greater than 1014 bytes per record)
        """
        blocked = io.BytesIO()

        message_list = [b'*' * 2000 for _ in range(5)]
        writer = VbsWriter(blocked, blocked=True)
        for message in message_list:
            writer.write(message)
        writer.close()
        print_stream(blocked, 'blocked')

        reader = VbsReader(blocked, blocked=True)
        for count, rec in enumerate(reader):
            self.assertLess(count, 5)
            self.assertEqual(rec, b'*' * 2000)

    def test_block1014_file_obj(self):
        """
        check that can access the underlying file object
        :return:
        """
        my_file = io.BytesIO()
        my_file_block = Block1014(my_file)
        self.assertEqual(my_file_block.tell(), 0)
        self.assertEqual(my_file_block.undefined_func, None)
        my_file_block.close()

    def test_vbsreader_file_obj(self):
        """
        check that can access the underlying file object
        :return:
        """
        my_file = io.BytesIO()
        vbs = VbsReader(my_file)
        self.assertEqual(vbs.tell(), 0)
        self.assertEqual(vbs.undefined_func, None)

    def test_vbswriter_file_obj(self):
        """
        check that can access the underlying file object
        :return:
        """
        my_file = io.BytesIO()
        vbs = VbsWriter(my_file)
        self.assertEqual(vbs.tell(), 0)
        self.assertEqual(vbs.undefined_func, None)

    def test_unblock1014_file_obj(self):
        """
        check that can access the underlying file object
        :return:
        """
        my_file = io.BytesIO()
        my_file_block = Unblock1014(my_file)
        self.assertEqual(my_file_block.tell(), 0)
        self.assertEqual(my_file_block.undefined_func, None)
        my_file_block.read()

    def test_vbs_list_to_bytes_to_list(self):
        test_bytes_list = [b'aaa', b'bbb', b'ccc']
        vbs_data = vbs_list_to_bytes(test_bytes_list)
        print(vbs_data)
        self.assertEqual(vbs_data, b'\x00\x00\x00\x03aaa\x00\x00\x00\x03bbb\x00\x00\x00\x03ccc\x00\x00\x00\x00')
        vbs_list = vbs_bytes_to_list(vbs_data)
        print(vbs_list)
        self.assertEqual(vbs_list, test_bytes_list)

    def test_ipm_param_reader(self):
        param_file_data = [
            b'2011101414AIP0000T1IP0000T1 TABLE LIST                 ' + 188 * b'.' + b'001',
            b'2014101414AIP0000T1IP0040T1 ACCOUNT RANGE TABLE        ' + 188 * b'.' + b'036',
            b'TRAILER RECORD IP0000T1  00000218                                               ',
            b'........xxx....',  # dummy record
            b'1711114A0365116545113000000000MCC5116545113999999999MCC020000000152710084563AUS036CMCC NNYMCC N0000000362'
            b'0000000000000000000000000000 000000NN   000000NNNN0NUNN0N N     ',
        ]

        with io.BytesIO() as test_param_stream:
            with VbsWriter(test_param_stream, blocked=True) as test_param_vbs:
                test_param_vbs.write_many(param_file_data)

            test_param_stream.seek(0)
            reader = IpmParamReader(test_param_stream, table_id='IP0040T1')

            for record in reader:
                print(record)


if __name__ == '__main__':
    unittest.main()
