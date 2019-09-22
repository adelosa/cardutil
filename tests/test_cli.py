import csv
import io
import unittest

from cardutil.mciipm import VbsWriter
from cardutil.cli import mci_ipm_encode, mci_ipm_param_encode, mci_csv_to_ipm, mci_ipm_to_csv

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
        b'AUS0080001001Y999016000000'
        b''
        b'00000000011234567806999999')


class ChangeEncodingTestCase(unittest.TestCase):
    def test_change_encoding(self):
        # add 5 records to a list
        message_list = [message_ascii_raw for _ in range(5)]

        # create test file
        vbs_in = io.BytesIO()
        writer = VbsWriter(vbs_in, blocked=True)
        for message in message_list:
            writer.write(message)
        writer.close()

        # print it
        print_stream(vbs_in, "Blocked in data")

        # process the param encoding
        param_out = io.BytesIO()
        mci_ipm_param_encode(vbs_in, param_out, in_encoding='latin1', out_encoding='latin1')
        print_stream(param_out, "Change param encoding")

        # process the ipm encode
        vbs_in.seek(0)
        ipm_out = io.BytesIO()
        mci_ipm_encode(vbs_in, ipm_out, in_encoding='latin1', out_encoding='latin1')
        print_stream(ipm_out, "Change encoding")

        vbs_in.seek(0)
        vbs_in_value = vbs_in.read()

        param_out.seek(0)
        param_out_value = param_out.read()
        self.assertEqual(vbs_in_value, param_out_value)

        ipm_out.seek(0)
        ipm_out_value = ipm_out.read()
        self.assertEqual(vbs_in_value, ipm_out_value)

    def test_mci_csv_to_ipm_to_csv(self):
        """
        create an ipm file from csv, then create csv from ipm. Check that input csv == output csv
        """
        def do_test(no_blocking):
            csv_data = 'MTI,DE2,DE4\n0100,1111222233334444,100'
            in_csv = io.StringIO(csv_data)
            print_stream(in_csv, 'in_csv')
            in_csv.seek(0)
            out_ipm = io.BytesIO()

            mci_csv_to_ipm(in_csv=in_csv, out_ipm=out_ipm, no1014blocking=no_blocking)
            out_ipm.seek(0)
            print_stream(out_ipm, 'out_ipm')
            out_ipm.seek(0)

            out_csv = io.StringIO()
            mci_ipm_to_csv(in_ipm=out_ipm, out_csv=out_csv, no1014blocking=no_blocking)
            print_stream(out_csv, 'out_csv')
            out_csv.seek(0)

            reader = csv.DictReader(out_csv)
            record = dict(list(reader).pop())
            print(record)
            self.assertEqual(record['MTI'], '0100')
            self.assertEqual(record['DE2'], '1111222233334444')
            self.assertEqual(record['DE4'], '100')
        do_test(no_blocking=False)
        do_test(no_blocking=True)


def print_stream(stream, description):
    stream.seek(0)
    data = stream.read()
    print(description)
    print(data)
    stream.seek(0)


if __name__ == '__main__':
    unittest.main()
