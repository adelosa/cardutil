import csv
import io
import os
import tempfile
import unittest

from tests import print_stream
from cardutil.cli import mci_csv_to_ipm, mci_ipm_to_csv
from cardutil.config import config


class MciCsvToIpmTestCase(unittest.TestCase):
    def test_mci_csv_to_ipm_to_csv(self):
        """
        create an ipm file from csv, then create csv from ipm. Check that input csv == output csv
        """
        def do_test(no_blocking):
            csv_data = 'MTI,DE2,DE4,DE12\n0100,1111222233334444,100,2020-06-18'
            in_csv = io.StringIO(csv_data)
            print_stream(in_csv, 'in_csv')
            in_csv.seek(0)
            out_ipm = io.BytesIO()

            mci_csv_to_ipm.mci_csv_to_ipm(in_csv=in_csv, out_ipm=out_ipm, no1014blocking=no_blocking, config=config)
            out_ipm.seek(0)
            print_stream(out_ipm, 'out_ipm')
            out_ipm.seek(0)

            out_csv = io.StringIO()
            mci_ipm_to_csv.mci_ipm_to_csv(in_ipm=out_ipm, out_csv=out_csv, config=config, no1014blocking=no_blocking)
            print_stream(out_csv, 'out_csv')
            out_csv.seek(0)

            reader = csv.DictReader(out_csv)
            record = dict(list(reader).pop())
            print(record)
            self.assertEqual(record['MTI'], '0100')
            self.assertEqual(record['DE2'], '1111222233334444')
            self.assertEqual(record['DE4'], '100')
            self.assertEqual(record['DE12'], '2020-06-18 00:00:00')
        do_test(no_blocking=False)
        do_test(no_blocking=True)

    def test_csv_to_ipm_input_params(self):
        """
        Run mci_csv_to_ipm using real files
        :return:
        """
        in_csv_data = 'MTI,DE2,DE4\n0100,1111222233334444,100'

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as in_csv:
            in_csv.write(in_csv_data)
            in_csv_name = in_csv.name
            print(in_csv_name)
            in_csv.close()
        mci_csv_to_ipm.cli_run(in_filename=in_csv_name, out_encoding='ascii')
        mci_csv_to_ipm.cli_run(in_filename=in_csv_name, out_filename=in_csv_name + '.bin', out_encoding='latin_1')
        os.remove(in_csv_name)
        os.remove(in_csv_name + '.ipm')
        os.remove(in_csv_name + '.bin')

    def test_mci_ipm_encode_cli_parser(self):
        args = vars(mci_csv_to_ipm.cli_parser().parse_args(['file1.ipm']))
        self.assertEqual(
            args,
            {'in_filename': 'file1.ipm', 'in_encoding': None, 'out_filename': None, 'out_encoding': None,
             'no1014blocking': False, 'config_file': None})


if __name__ == '__main__':
    unittest.main()
