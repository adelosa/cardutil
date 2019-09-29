import io
import unittest

from cardutil.mciipm import VbsWriter, VbsReader, IpmReader, IpmWriter, Block1014, Unblock1014, block_1014, unblock_1014

from tests import message_ascii_raw, message_ebcdic_raw


class MciIpmTestCase(unittest.TestCase):

    def test_real_message_example_ascii(self):
        # create the input ipm file bytes -- test_file
        message_list = [message_ascii_raw for _ in range(15)]
        with io.BytesIO() as in_data:

            # write vbs test file
            writer = VbsWriter(in_data, blocked=True)
            for message in message_list:
                writer.write(message)
            else:
                writer.close()
            print_stream(in_data, "VBS in data")

            # read vbs test file
            reader = IpmReader(in_data, blocked=True)
            results = list(reader)
        self.assertEqual(len(results), len(message_list))

    def test_real_message_example_ebcdic(self):
        message_list = [message_ebcdic_raw for _ in range(15)]
        with io.BytesIO() as in_data:
            # write 1014 blocked test file
            writer = VbsWriter(in_data, blocked=True)
            for message in message_list:
                writer.write(message)
            else:
                writer.close()
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

    def test_ipmwriter_blocked_file(self):
        record = {'MTI': '1111', 'DE2': '8888999988889999'}
        records = [record for _ in range(5)]

        with io.BytesIO() as out_data:
            writer = IpmWriter(out_data, blocked=True)
            for record in records:
                writer.write(record)
            writer.close()

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
        with self.assertRaises(ValueError):
            unblock_1014(out_blocked_missing_data, out)

        # bad pad chars
        out_blocked_bad_fill = io.BytesIO(blocked[:-2] + b'$$')
        out_blocked_bad_fill.seek(0)
        out = io.BytesIO()
        with self.assertRaises(ValueError):
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


def print_stream(stream, description):
    stream.seek(0)
    data = stream.read()
    print(description)
    print(data)
    stream.seek(0)


if __name__ == '__main__':
    unittest.main()
