import io
import unittest

from cardutil.mciipm import VbsWriter, VbsReader, change_encoding, change_param_encoding, IpmReader, IpmWriter

message_ebcdic_raw = (
        '1144'.encode('cp500') +
        b'\xF0\x10\x05\x42\x84\x61\x80\x02\x02\x00\x00\x04\x00\x00\x00\x00' +
        ('164444555544445555111111000000009999201508151715123456789012333123423579957991200000'
         '012306120612345612345657994211111111145BIG BOBS\\70 FERNDALE ST\\ANNERLEY\\4103  QLD'
         'AUS0080001001Y99901600000000000000011234567806999999').encode('cp500'))

message_ascii_raw = (
        b'1144' +
        b'\xF0\x10\x05\x42\x84\x61\x80\x02\x02\x00\x00\x04\x00\x00\x00\x00' +
        b'164444555544445555111111000000009999201508151715123456789012333123423579957991200000'
        b'012306120612345612345657994211111111145BIG BOBS\\70 FERNDALE ST\\ANNERLEY\\4103  QLD'
        b'AUS0080001001Y99901600000000000000011234567806999999')


class MciIpmTestCase(unittest.TestCase):

    def test_real_message_example_ascii(self):
        # create the input ipm file bytes -- test_file
        message_list = [message_ascii_raw for _ in range(5)]
        with io.BytesIO() as in_data:

            # write vbs test file
            writer = VbsWriter(in_data)
            for message in message_list:
                writer.write(message)
            else:
                writer.close()
            print_stream(in_data, "VBS in data")

            # read vbs test file
            reader = IpmReader(in_data)
            results = list(reader)
        self.assertEqual(len(results), len(message_list))

    def test_real_message_example_ebcdic(self):
        message_list = [message_ebcdic_raw for _ in range(5)]
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

    def test_change_encoding(self):
        # add 5 records to a list
        message_list = [message_ascii_raw for _ in range(1)]

        # create test file
        vbs_in = io.BytesIO()
        writer = VbsWriter(vbs_in, blocked=True)
        for message in message_list:
            writer.write(message)
        writer.close()

        # print it
        print_stream(vbs_in, "Blocked in data")

        # process the encoding
        param_out = io.BytesIO()
        change_param_encoding(vbs_in, param_out, in_encoding='latin1', out_encoding='latin1')
        print_stream(param_out, "Change param encoding")

        vbs_in.seek(0)
        ipm_out = io.BytesIO()
        change_encoding(vbs_in, ipm_out, in_encoding='latin1', out_encoding='latin1')
        print_stream(ipm_out, "Change encoding")

        vbs_in.seek(0)
        vbs_in_value = vbs_in.read()

        param_out.seek(0)
        param_out_value = param_out.read()
        self.assertEqual(vbs_in_value, param_out_value)

        ipm_out.seek(0)
        ipm_out_value = ipm_out.read()
        self.assertEqual(vbs_in_value, ipm_out_value)


def print_stream(stream, description):
    stream.seek(0)
    data = stream.read()
    print(description)
    print(data)
    stream.seek(0)


if __name__ == '__main__':
    unittest.main()
