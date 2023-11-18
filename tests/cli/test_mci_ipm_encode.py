import io
import os
import tempfile
import unittest

from tests import message_ascii_raw, print_stream

from cardutil.mciipm import VbsWriter
from cardutil.cli import mci_ipm_encode


class MciIpmEncodeTestCase(unittest.TestCase):
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
            {'in_filename': 'file1.ipm', 'out_filename': None, 'in_encoding': None,
             'out_encoding': None, 'in_format': '1014', 'out_format': '1014',
             'no1014blocking': False, 'debug': False})

    def test_mci_ipm_encode_input_params(self):
        """
        Run mci_ipm_encode using real files
        """
        # create an ipm file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as out_ipm:
            out_ipm.write(
                b'\x00\x00\x00\x1a0100\x80\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'n\x9cm\x9cl\x9c\x00\x00\x00\x00')
            in_ipm_name = out_ipm.name
            out_ipm.close()

        mci_ipm_encode.cli_run(in_filename=in_ipm_name)
        mci_ipm_encode.cli_run(in_filename=in_ipm_name, out_filename=in_ipm_name + '.out')
        mci_ipm_encode.cli_run(in_filename=in_ipm_name, no1014blocking=True)
        mci_ipm_encode.cli_run(in_filename=in_ipm_name, debug=True)
        os.remove(in_ipm_name)
        os.remove(in_ipm_name + '.out')

    def test_get_config_removes_pds_field_processors(self):
        """
        Ensure no field process
        """
        bit_config = mci_ipm_encode.get_config()
        print(bit_config)
        for bit_config_item in bit_config.values():
            print(bit_config_item)
            if bit_config_item.get('field_processor'):
                print(bit_config_item['field_processor'])
                self.assertIsNot('PDS', bit_config_item['field_processor'])
