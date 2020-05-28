import csv
import io
import os
import tempfile
import unittest

from cardutil.mciipm import VbsWriter
from cardutil.cli import mci_ipm_encode, mci_ipm_param_encode, mci_ipm_to_csv, mci_csv_to_ipm
from tests import message_ascii_raw


class CliTestCase(unittest.TestCase):
    def test_mci_ipm_encode(self):
        # create test ipm file
        message_list = [message_ascii_raw for _ in range(5)]
        vbs_in = io.BytesIO()
        writer = VbsWriter(vbs_in, blocked=True)
        for message in message_list:
            writer.write(message)
        writer.close()

        # process the ipm encode
        ipm_out = io.BytesIO()
        mci_ipm_encode.mci_ipm_encode(vbs_in, ipm_out, in_encoding='ascii', out_encoding='ascii')

        print_stream(vbs_in, "Input")
        vbs_in_value = vbs_in.read()

        print_stream(ipm_out, "Output")
        ipm_out_value = ipm_out.read()

        self.assertEqual(vbs_in_value, ipm_out_value)

    def test_mci_ipm_encode_cli_parser(self):
        args = vars(mci_ipm_encode.cli_parser().parse_args(['file1.ipm']))
        self.assertEqual(
            args,
            {'in_filename': 'file1.ipm', 'out_filename': None, 'in_encoding': 'ascii',
             'out_encoding': 'cp500', 'no1014blocking': False})

    def test_mci_ipm_param_encode(self):
        # create test param file
        message_list = [b"Parameter message data" for _ in range(5)]
        vbs_in = io.BytesIO()
        writer = VbsWriter(vbs_in, blocked=True)
        for message in message_list:
            writer.write(message)
        writer.close()

        # process the param encoding
        param_out = io.BytesIO()
        mci_ipm_param_encode.mci_ipm_param_encode(vbs_in, param_out, in_encoding='ascii', out_encoding='ascii')

        print_stream(vbs_in, "Input")
        vbs_in_value = vbs_in.read()

        print_stream(param_out, "Output")
        param_out_value = param_out.read()

        self.assertEqual(vbs_in_value, param_out_value)

    def test_mci_ipm_param_encode_parser(self):
        args = vars(mci_ipm_param_encode.cli_parser().parse_args(['file1.ipm']))
        self.assertEqual(
            args,
            {'in_filename': 'file1.ipm', 'out_filename': None, 'in_encoding': 'ascii',
             'out_encoding': 'cp500', 'no1014blocking': False})

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

            mci_csv_to_ipm.mci_csv_to_ipm(in_csv=in_csv, out_ipm=out_ipm, no1014blocking=no_blocking)
            out_ipm.seek(0)
            print_stream(out_ipm, 'out_ipm')
            out_ipm.seek(0)

            out_csv = io.StringIO()
            mci_ipm_to_csv.mci_ipm_to_csv(in_ipm=out_ipm, out_csv=out_csv, no1014blocking=no_blocking)
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

    def test_ipm_to_csv_bad_data_de38(self):
        """
        prod issue - auth code DE38 contains non-ascii characters.
        Added new out-encoding parameter to support this -- changed to latin_1 which supports full 256 bits.
        Also need to set in-encoding to latin_1 for the same reason
        I have only seen this issue on one transaction once after processing 1000's of input files
        """
        in_ipm = io.BytesIO(b'\x00\x00\x00\x1a0100\x80\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                            b'n\x9cm\x9cl\x9c\x00\x00\x00\x00')
        with tempfile.TemporaryFile(mode='w', encoding='latin_1') as out_csv:
            mci_ipm_to_csv.mci_ipm_to_csv(
                in_ipm=in_ipm, out_csv=out_csv, no1014blocking=True, in_encoding='latin_1')

    def test_ipm_to_csv_input_params(self):
        """
        Actually run using real files
        :return:
        """
        in_ipm_data = (b'\x00\x00\x00\x1a0100\x80\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'nXmXlX\x00\x00\x00\x00')

        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as in_ipm:
            in_ipm.write(in_ipm_data)
            in_ipm_name = in_ipm.name
            print(in_ipm_name)
            in_ipm.close()
        mci_ipm_to_csv.cli_run(in_filename=in_ipm_name, out_encoding='ascii')
        mci_ipm_to_csv.cli_run(in_filename=in_ipm_name, out_filename=in_ipm_name + '.csv', out_encoding='ascii')
        os.remove(in_ipm_name)
        os.remove(in_ipm_name + '.csv')

    def test_mci_ipm_to_csv_cli_parser(self):
        args = vars(mci_ipm_to_csv.cli_parser().parse_args(['file1.ipm']))
        self.assertEqual(
            args,
            {'in_encoding': 'ascii', 'out_encoding': 'ascii', 'in_filename': 'file1.ipm', 'no1014blocking': False,
             'out_filename': None})

    def test_mci_csv_to_ipm_cli_parser(self):
        args = vars(mci_csv_to_ipm.cli_parser().parse_args(['file1.ipm']))
        self.assertEqual(
            args,
            {'out_encoding': 'ascii', 'in_filename': 'file1.ipm', 'no1014blocking': False, 'out_filename': None})


def print_stream(stream, description):
    stream.seek(0)
    data = stream.read()
    print('***' + description + '***')
    print(data)
    stream.seek(0)


if __name__ == '__main__':
    unittest.main()
