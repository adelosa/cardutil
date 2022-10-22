import io
import os
import tempfile
import unittest

from cardutil import CardutilError
from cardutil.mciipm import VbsWriter
from cardutil.cli import mci_ipm_param_to_csv
from cardutil.config import config

MCI_PARAMETER_CONFIG = config.get('mci_parameter_tables')


class MciIpmParamToCsvTestCase(unittest.TestCase):
    def test_mci_ipm_param_to_csv_parser(self):
        args = vars(mci_ipm_param_to_csv.cli_parser().parse_args(['file1.ipm', 'IP0000T1']))
        self.assertEqual(
            args,
            {'in_filename': 'file1.ipm', 'out_filename': None, 'in_encoding': None, 'table_id': 'IP0000T1',
             'out_encoding': None, 'no1014blocking': False, 'config_file': None, 'debug': False})

    def test_ipm_to_csv_input_params(self):
        """
        Actually run using real files
        :return:
        """
        param_file_data = (
            b'2011101414AIP0000T1IP0000T1 TABLE LIST                 ' + 188 * b'.' + b'001',
            b'2014101414AIP0000T1IP0040T1 ACCOUNT RANGE TABLE        ' + 188 * b'.' + b'036',
            b'TRAILER RECORD IP0000T1  00000218                                               ',
            b'........xxx....',  # dummy record
            b'1711114A0365116545113000000000MCC5116545113999999999MCC020000000152710084563AUS036CMCC NNYMCC N0000000362'
            b'0000000000000000000000000000 000000NN   000000NNNN0NUNN0N N     ',
        )

        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as in_file:
            with VbsWriter(in_file, blocked=True) as in_file_writer:
                in_file_writer.write_many(param_file_data)
            in_file_name = in_file.name
            print(in_file_name)
            in_file.close()
        mci_ipm_param_to_csv.cli_run(table_id='IP0040T1', in_filename=in_file_name)
        mci_ipm_param_to_csv.cli_run(table_id='IP0040T1', in_filename=in_file_name, in_encoding='latin_1')
        mci_ipm_param_to_csv.cli_run(table_id='IP0040T1', in_filename=in_file_name, out_filename=in_file_name + 'xxx')
        mci_ipm_param_to_csv.cli_run(table_id='IP0040T1', in_filename=in_file_name, debug=True)
        os.remove(in_file_name)
        os.remove(in_file_name + '_IP0040T1.csv')
        os.remove(in_file_name + 'xxx')

    def test_extract_ip0040t1(self):
        param_file_data = [
            b'2011101414AIP0000T1IP0000T1 TABLE LIST                 ' + 188 * b'.' + b'001',
            b'2014101414AIP0000T1IP0040T1 ACCOUNT RANGE TABLE        ' + 188 * b'.' + b'036',
            b'TRAILER RECORD IP0000T1  00000218                                               ',
            b'........xxx....',  # dummy record
            b'1711114A0365116545113000000000MCC5116545113999999999MCC020000000152710084563AUS036CMCC NNYMCC N0000000362'
            b'0000000000000000000000000001 000000NY   000000NNNN',
            b'0000000000000000000000000000 000000NN   000000NNNN0NUNN0N N     ',
        ]

        with io.BytesIO() as test_param_stream, io.StringIO() as test_csv_stream:
            with VbsWriter(test_param_stream, blocked=True) as test_param_vbs:
                test_param_vbs.write_many(param_file_data)

            test_param_stream.seek(0)
            mci_ipm_param_to_csv.mci_ipm_param_to_csv(
                test_param_stream, test_csv_stream, config=MCI_PARAMETER_CONFIG, table_id='IP0040T1')
            test_csv_stream.seek(0)
            test_csv_data = test_csv_stream.read()

        csv_records = test_csv_data.split('\n')

        # check the header
        config_header_keys = list(MCI_PARAMETER_CONFIG.get('IP0040T1').keys())
        csv_header_keys = csv_records[0].split(',')
        self.assertEqual(config_header_keys, csv_header_keys)

        # check the record extracted
        self.assertEqual(csv_records[1], '711114,A,036,5116545113000000000,MCC,5116545113999999999,MCC,02,00000001527,'
                                         '1,0084563,AUS,036,C,MCC, ,N,N,Y,MCC, ,N,000000,036,2,'
                                         '0000000000000000000000000001, ,000000,N,Y,   ,000000,N,N,N,N')

    def test_extract_ip0040t1_no_records(self):
        param_file_data = [
            b'2011101414AIP0000T1IP0000T1 TABLE LIST                 ' + 188 * b'.' + b'001',
            b'2014101414AIP0000T1IP0040T1 ACCOUNT RANGE TABLE        ' + 188 * b'.' + b'036',
            b'TRAILER RECORD IP0000T1  00000218                                               ',
        ]

        with io.BytesIO() as test_param_stream, io.StringIO() as test_csv_stream:
            with VbsWriter(test_param_stream, blocked=True) as test_param_vbs:
                test_param_vbs.write_many(param_file_data)

            test_param_stream.seek(0)
            mci_ipm_param_to_csv.mci_ipm_param_to_csv(
                test_param_stream, test_csv_stream, config=MCI_PARAMETER_CONFIG, table_id='IP0040T1')
            test_csv_stream.seek(0)
            test_csv_data = test_csv_stream.read()

        csv_records = test_csv_data.split('\n')
        print(csv_records)
        self.assertEqual(len(csv_records), 2, msg="Only 2 record returned -- header, dummy")

        # check the header
        config_header_keys = list(MCI_PARAMETER_CONFIG.get('IP0040T1').keys())
        csv_header_keys = csv_records[0].split(',')
        self.assertEqual(config_header_keys, csv_header_keys)

        # check the dummy value
        self.assertEqual(csv_records[1], '')

    def test_extract_ip0040t1_no_table_config(self):
        with io.BytesIO() as test_param_stream, io.StringIO() as test_csv_stream:
            with self.assertRaises(CardutilError):
                mci_ipm_param_to_csv.mci_ipm_param_to_csv(
                    test_param_stream, test_csv_stream, config=MCI_PARAMETER_CONFIG, table_id='BADTABLE')

    def test_extract_ip0040t1_missing_index_trailer(self):
        param_file_data = [
            b'2011101414AIP0000T1IP0000T1 TABLE LIST                 ' + 188 * b'.' + b'001',
            b'2014101414AIP0000T1IP0040T1 ACCOUNT RANGE TABLE        ' + 188 * b'.' + b'036']

        with io.BytesIO() as test_param_stream, io.StringIO() as test_csv_stream:
            with VbsWriter(test_param_stream, blocked=True) as test_param_vbs:
                test_param_vbs.write_many(param_file_data)

            test_param_stream.seek(0)
            with self.assertRaises(CardutilError):
                mci_ipm_param_to_csv.mci_ipm_param_to_csv(
                    test_param_stream, test_csv_stream, config=MCI_PARAMETER_CONFIG, table_id='IP0040T1')


if __name__ == '__main__':
    unittest.main()
