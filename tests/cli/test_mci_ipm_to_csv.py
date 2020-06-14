import io
import os
import tempfile
import unittest

from cardutil.cli import mci_ipm_to_csv
from cardutil.config import config


class MciIpmToCsvTestCase(unittest.TestCase):
    def test_mci_ipm_to_csv_cli_parser(self):
        args = vars(mci_ipm_to_csv.cli_parser().parse_args(['file1.ipm']))
        self.assertEqual(
            args,
            {'in_encoding': None, 'out_encoding': None, 'in_filename': 'file1.ipm', 'no1014blocking': False,
             'out_filename': None, 'config_file': None})

        args = vars(mci_ipm_to_csv.cli_parser().parse_args(['file1.ipm', '--in-encoding', 'latin_1']))
        self.assertEqual(
            args,
            {'in_encoding': 'latin_1', 'out_encoding': None, 'in_filename': 'file1.ipm', 'no1014blocking': False,
             'out_filename': None, 'config_file': None})

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
                in_ipm=in_ipm, out_csv=out_csv, config=config, no1014blocking=True)

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
        mci_ipm_to_csv.cli_run(in_filename=in_ipm_name, out_filename=in_ipm_name + '.csv', out_encoding='latin_1')
        os.remove(in_ipm_name)
        os.remove(in_ipm_name + '.csv')


if __name__ == '__main__':
    unittest.main()
