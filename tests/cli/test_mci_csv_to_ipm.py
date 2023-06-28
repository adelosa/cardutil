import csv
import io
import os
import tempfile
import unittest

from tests import print_stream
from cardutil.vendor import hexdump
from cardutil.cli import mci_csv_to_ipm, mci_ipm_to_csv
from cardutil.config import config
from cardutil.mciipm import IpmReader


class MciCsvToIpmParserTestCase(unittest.TestCase):
    def test_mci_ipm_encode_cli_parser(self):
        args = vars(mci_csv_to_ipm.cli_parser().parse_args(['file1.ipm']))
        self.assertEqual(
            args,
            {'in_filename': 'file1.ipm', 'in_encoding': None, 'out_filename': None, 'out_encoding': None,
             'no1014blocking': False, 'config_file': None, 'debug': False})


class MciCsvToIpmIOTestCase(unittest.TestCase):
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


class MciCsvToIpmTestCase(unittest.TestCase):

    temp_filenames = []

    def setUp(self) -> None:
        self.temp_filenames = []

    def tearDown(self) -> None:
        for filename in self.temp_filenames:
            if os.path.exists(filename):
                os.remove(filename)

    def run_cli_with_csv(self, csv, **kwargs):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as in_csv:
            in_csv.write(csv)
            in_csv_name = in_csv.name
            print(in_csv_name)
            in_csv.close()
        mci_csv_to_ipm.cli_run(in_filename=in_csv_name, **kwargs)
        self.temp_filenames.append(in_csv_name)
        if 'out_filename' in kwargs:
            outfile = kwargs['out_filename']
        else:
            outfile = in_csv_name + '.ipm'
        self.temp_filenames.append(outfile)
        self.print_hexdump(outfile)
        return self.get_ipm_data(outfile)

    def print_hexdump(self, filename):
        with open(filename, 'rb') as outfile:
            output = outfile.read()
        hexdump.hexdump(output)

    def get_ipm_data(self, filename):
        with open(filename, 'rb') as outfile:
            reader = IpmReader(outfile, blocked=True)
            recs = [record for record in reader]
        return recs

    def test_csv_to_ipm_input_params(self):
        """
        Run mci_csv_to_ipm using real files
        :return:
        """
        in_csv_data = 'MTI,DE2,DE4\n0100,1111222233334444,100'
        # run the conversion
        recs = self.run_cli_with_csv(in_csv_data, out_encoding='latin1')
        # perform the checks
        self.assertEqual(len(recs), 1)  # one record returned
        rec = recs[0]
        print(rec)
        recs = self.run_cli_with_csv(in_csv_data, out_filename='x')

    def test_csv_to_ipm_with_output_filename(self):
        in_csv_data = 'MTI,DE2,DE4\n0100,1111222233334444,100'
        out_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        recs = self.run_cli_with_csv(in_csv_data, out_filename=out_file.name)
        print(recs)

    def test_csv_to_ipm_with_debug(self):
        in_csv_data = 'MTI,DE2,DE4\n0100,1111222233334444,100'
        out_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        recs = self.run_cli_with_csv(in_csv_data, out_filename=out_file.name, debug=True)
        print(recs)

    def test_csv_to_ipm_has_DE48_only(self):
        """
        Run mci_csv_to_ipm test with DE48 only
        In this case, DE written as is
        """
        in_csv_data = ('MTI,DE2,DE3,DE4,DE12,DE14,DE22,DE23,DE24,DE25,DE26,DE30,DE31,DE33,DE37,DE38,DE40,DE41,DE42,'
                       'DE48,DE49,DE50,DE63,DE71,DE73,DE93,DE94,DE95,DE100,DE43_NAME,DE43_SUBURB,DE43_POSTCODE,'
                       'ICC_DATA\n'
                       '1644,,,,,,,,697,,,,,,,,,,,01050250022112070000005167800005011002500221120700000015995000050'
                       '122001T,,,,00000001,,,,,,,,,')

        # run the conversion
        recs = self.run_cli_with_csv(in_csv_data, out_encoding='latin1', debug=True)
        # perform the checks
        self.assertEqual(len(recs), 1)  # one record returned
        rec = recs[0]
        print(rec)
        self.assertEqual(rec['DE48'], '01050250022112070000005167800005011002500221120700000015995000050122001T')

    def test_csv_to_ipm_has_DE48_and_PDS(self):
        """
        Run mci_csv_to_ipm test with DE48 column and PDS
        In this case, PDS overrides DE, and only PDS value placed into PDS fields, DE values dropped
        """
        in_csv_data = ('MTI,DE2,DE3,DE4,DE12,DE14,DE22,DE23,DE24,DE25,DE26,DE30,DE31,DE33,DE37,DE38,DE40,DE41,DE42,'
                       'DE48,DE49,DE50,DE63,DE71,DE73,DE93,DE94,DE95,DE100,DE43_NAME,DE43_SUBURB,DE43_POSTCODE,'
                       'ICC_DATA,PDS0191\n'
                       '1644,,,,,,,,697,,,,,,,,,,,010502500221120700000051678000050110025002211207000000159950000501'
                       '22001T,,,,00000001,,,,,,,,,,2')

        # run the conversion
        recs = self.run_cli_with_csv(in_csv_data, out_encoding='latin1')

        # perform the checks
        self.assertEqual(len(recs), 1)  # one record returned
        rec = recs[0]
        print(rec)
        self.assertEqual(rec['MTI'], '1644')
        self.assertEqual(rec['DE24'], '697')
        self.assertEqual(rec['DE71'], 1)
        # check that only PDS field loaded, prior DE48 values are dropped
        self.assertEqual(rec['DE48'], '01910012')

    def test_csv_to_ipm_has_PDS_only(self):
        """
        Run mci_csv_to_ipm test with PDS fields only
        Check that all provided PDS fields are loaded into DE fields
        :return:
        """
        in_csv_data = ('MTI,DE2,DE3,DE4,DE12,DE14,DE22,DE23,DE24,DE25,DE26,DE30,DE31,DE33,DE37,DE38,DE40,DE41,DE42,'
                       'DE49,DE50,DE63,DE71,DE73,DE93,DE94,DE95,DE100,DE43_NAME,DE43_SUBURB,DE43_POSTCODE,ICC_DATA,'
                       'PDS0191,PDS0122\n1644,,,,,,,,697,,,,,,,,,,,,,,00000001,,,,,,,,,,2,T')
        # run the conversion
        recs = self.run_cli_with_csv(in_csv_data, out_encoding='latin1')
        # perform the checks
        self.assertEqual(len(recs), 1)  # one record returned
        rec = recs[0]
        print(rec)
        # de48 contains all PDS values passed
        self.assertEqual(rec['DE48'], '0122001T01910012')

    def test_csv_to_ipm_exclude_empty(self):
        """
        Run mci_csv_to_ipm test with empty fields
        Check that only provided fields are loaded
        :return:
        """
        in_csv_data = ('MTI,DE2,DE3,DE4,DE12,DE14,DE22,'
                       'PDS0191,PDS0122\n'
                       '1644,123,1,,,,,123,')
        # run the conversion
        recs = self.run_cli_with_csv(in_csv_data, out_encoding='latin1')
        # perform the checks
        self.assertEqual(len(recs), 1)  # one record returned
        rec = recs[0]
        print(rec)
        # de48 contains only PDS fields with values
        expected_dict = {'MTI': '1644', 'DE2': '123', 'DE3': '1     ', 'DE48': '0191003123', 'PDS0191': '123'}
        self.assertDictEqual(rec, expected_dict)


if __name__ == '__main__':
    unittest.main()
