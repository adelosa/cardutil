import io
import os
import tempfile
import unittest

from cardutil.cli import mci_ipm_param_encode
from cardutil.mciipm import VbsWriter
from cardutil.vendor.hexdump import hexdump
from tests import print_stream


class MciIpmParamEncodeTestCase(unittest.TestCase):

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
            {'in_filename': 'file1.ipm', 'out_filename': None, 'in_encoding': None,
             'out_encoding': None, 'no1014blocking': False})

    def test_mci_ipm_param_encode_input_params(self):
        """
        Run mci_ipm_param_encode using real files
        """
        # create an ipm file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as in_vbs:
            writer = VbsWriter(in_vbs, blocked=True)
            writer.write(b"Parameter message data")
            writer.close()
            in_vbs_name = in_vbs.name
            in_vbs.close()

        output_file_name = in_vbs_name + '.out'
        mci_ipm_param_encode.cli_run(in_filename=in_vbs_name)
        with open(in_vbs_name + '.out', 'rb') as output_file:
            hexdump(output_file.read())
        os.remove(output_file_name)
        mci_ipm_param_encode.cli_run(in_filename=in_vbs_name, out_filename=output_file_name, no1014blocking=True)
        with open(in_vbs_name + '.out', 'rb') as output_file:
            hexdump(output_file.read())
        os.remove(output_file_name)
        mci_ipm_param_encode.cli_run(in_filename=in_vbs_name, out_filename=output_file_name, out_encoding='cp500')
        with open(in_vbs_name + '.out', 'rb') as output_file:
            hexdump(output_file.read())
        os.remove(output_file_name)
        os.remove(in_vbs_name)


if __name__ == '__main__':
    unittest.main()
