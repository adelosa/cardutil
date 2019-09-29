import csv
import io
import unittest

from cardutil.mciipm import VbsWriter
from cardutil.cli import (
    mci_ipm_encode, mci_ipm_param_encode, mci_csv_to_ipm, mci_ipm_to_csv,
    mci_ipm_encode_cli_parser, mci_ipm_param_encode_cli_parser, mci_ipm_to_csv_cli_parser, mci_csv_to_ipm_cli_parser
)

from tests import message_ascii_raw


class CliTestCase(unittest.TestCase):
    def test_change_ipm_encoding(self):
        # create test ipm file
        message_list = [message_ascii_raw for _ in range(5)]
        vbs_in = io.BytesIO()
        writer = VbsWriter(vbs_in, blocked=True)
        for message in message_list:
            writer.write(message)
        writer.close()

        # process the ipm encode
        ipm_out = io.BytesIO()
        mci_ipm_encode(vbs_in, ipm_out, in_encoding='ascii', out_encoding='ascii')

        print_stream(vbs_in, "Input")
        vbs_in_value = vbs_in.read()

        print_stream(ipm_out, "Output")
        ipm_out_value = ipm_out.read()

        self.assertEqual(vbs_in_value, ipm_out_value)

    def test_change_ipm_encoding_parser(self):
        args = vars(mci_ipm_encode_cli_parser().parse_args(['file1.ipm']))
        self.assertEqual(
            args,
            {'in_filename': 'file1.ipm', 'out_filename': None, 'in_encoding': 'ascii',
             'out_encoding': 'cp500', 'no1014blocking': False})

    def test_change_param_encoding(self):
        # create test param file
        message_list = [b"Parameter message data" for _ in range(5)]
        vbs_in = io.BytesIO()
        writer = VbsWriter(vbs_in, blocked=True)
        for message in message_list:
            writer.write(message)
        writer.close()

        # process the param encoding
        param_out = io.BytesIO()
        mci_ipm_param_encode(vbs_in, param_out, in_encoding='ascii', out_encoding='ascii')

        print_stream(vbs_in, "Input")
        vbs_in_value = vbs_in.read()

        print_stream(param_out, "Output")
        param_out_value = param_out.read()

        self.assertEqual(vbs_in_value, param_out_value)

    def test_change_param_encoding_parser(self):
        args = vars(mci_ipm_param_encode_cli_parser().parse_args(['file1.ipm']))
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

    def test_mci_ipm_to_csv_cli_parser(self):
        args = vars(mci_ipm_to_csv_cli_parser().parse_args(['file1.ipm']))
        self.assertEqual(
            args,
            {'in_encoding': 'ascii', 'in_filename': 'file1.ipm', 'no1014blocking': False, 'out_filename': None})

    def test_mci_csv_to_ipm_cli_parser(self):
        args = vars(mci_csv_to_ipm_cli_parser().parse_args(['file1.ipm']))
        self.assertEqual(
            args,
            {'out_encoding': 'ascii', 'in_filename': 'file1.ipm', 'no1014blocking': False, 'out_filename': None})


def print_stream(stream, description):
    stream.seek(0)
    data = stream.read()
    print(description)
    print(data)
    stream.seek(0)


if __name__ == '__main__':
    unittest.main()
