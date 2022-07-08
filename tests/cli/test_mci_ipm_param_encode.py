import io
import os
import tempfile
import unittest

from cardutil.cli import mci_ipm_param_encode
from cardutil.mciipm import VbsWriter
from cardutil.vendor.hexdump import hexdump
from tests import print_stream


class MciIpmParamEncodeTestCase(unittest.TestCase):

    def test_mci_ipm_param_encode_input_params_blocked(self):
        """
        Run mci_ipm_param_encode using real files
        """
        # create an ipm file
        with tempfile.NamedTemporaryFile(mode='wb') as in_vbs:
            with VbsWriter(in_vbs, blocked=True) as writer:
                writer.write(b"Parameter message data")
            in_vbs.close()

    def test_mci_ipm_param_encode(self):
        # create test param file
        message_list = [b"Parameter message data" for _ in range(5)]
        vbs_in = io.BytesIO()
        with VbsWriter(vbs_in, blocked=True) as writer:
            for message in message_list:
                writer.write(message)

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
            {'in_filename': 'file1.ipm', 'out_filename': None, 'in_encoding': None,
             'out_encoding': None, 'no1014blocking': False,
             'in_format': '1014', 'out_format': '1014', 'debug': False})

    def test_mci_ipm_param_encode_input_params_variations(self):
        """
        Run mci_ipm_param_encode using real files
        """
        # create an ipm file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as in_vbs:
            with VbsWriter(in_vbs, blocked=True) as writer:
                writer.write(b"Parameter message data")
            in_vbs_name = in_vbs.name
            in_vbs.close()

        output_file_name = in_vbs_name + '.out'

        # run with just input filename
        mci_ipm_param_encode.cli_run(in_filename=in_vbs_name, debug=True)
        with open(in_vbs_name + '.out', 'rb') as output_file:
            hexdump(output_file.read())
            print('*'*20)
        os.remove(output_file_name)

        # with input and output set to vbs (--no1014blocking: input is 1014, but doesn't seem to care)
        mci_ipm_param_encode.cli_run(in_filename=in_vbs_name, out_filename=output_file_name, no1014blocking=True)
        with open(in_vbs_name + '.out', 'rb') as output_file:
            hexdump(output_file.read())
            print('*'*20)
        os.remove(output_file_name)

        # with 1014 input and vbs output
        mci_ipm_param_encode.cli_run(
            in_filename=in_vbs_name, out_filename=output_file_name, in_format='1014', out_format='vbs')
        with open(in_vbs_name + '.out', 'rb') as output_file:
            hexdump(output_file.read())
            print('*'*20)
        os.remove(output_file_name)

        # with cp500 encoding (ebcdic)
        mci_ipm_param_encode.cli_run(in_filename=in_vbs_name, out_filename=output_file_name, out_encoding='cp500')
        with open(in_vbs_name + '.out', 'rb') as output_file:
            hexdump(output_file.read())
            print('*'*20)
        os.remove(output_file_name)

        os.remove(in_vbs_name)


if __name__ == '__main__':
    unittest.main()
