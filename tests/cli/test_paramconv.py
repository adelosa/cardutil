import os
import tempfile
import unittest

from cardutil.mciipm import VbsWriter
from cardutil.cli import paramconv
from cardutil.vendor.hexdump import hexdump


class MciIpmParamEncodeTestCase(unittest.TestCase):
    def test_paramconv_no_params(self):
        paramconv.cli_run()

    def test_paramconv_help(self):
        with self.assertRaises(SystemExit) as ex:
            paramconv.cli_entry(['--help'])
        self.assertEqual(ex.exception.code, 0)

    def test_paramconv_exception(self):
        in_ipm_data = (b'\x00\x00\x00\x1a0100\x80\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'nXmXlX\xFF\xFF\x00\x00')

        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as in_ipm:
            in_ipm.write(in_ipm_data)
            in_ipm_name = in_ipm.name
            print(in_ipm_name)
            in_ipm.close()

            paramconv.cli_run(
                input=in_ipm_name,
                sourceformat='ascii',
                debug=True,
            )
        os.remove(in_ipm_name)
        os.remove(in_ipm_name + '.out')

    def test_paramconv_ascii_ebcdic_ascii(self):

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as in_vbs:
            with VbsWriter(in_vbs, blocked=True) as writer:
                writer.write(b"Parameter message data")
            in_vbs_name = in_vbs.name
            in_vbs.close()

        output_file_name = in_vbs_name + '.out'

        # run with just input filename
        paramconv.cli_run(input=in_vbs_name, sourceformat='ascii')
        with open(output_file_name, 'rb') as output_file:
            hexdump(output_file.read())
            print('*' * 20)

        # run the output as input
        paramconv.cli_run(input=output_file_name, sourceformat='ebcdic')
        with open(output_file_name + '.out', 'rb') as output_file:
            hexdump(output_file.read())
            print('*' * 20)

        os.remove(in_vbs_name)
        os.remove(output_file_name)
        os.remove(output_file_name + '.out')

    def test_paramconv_output_specified(self):

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as in_vbs:
            with VbsWriter(in_vbs, blocked=True) as writer:
                writer.write(b"Parameter message data")
            in_vbs_name = in_vbs.name
            in_vbs.close()

        output_file_name = in_vbs_name + '.out'

        # run with just input filename
        paramconv.cli_run(input=in_vbs_name, output=in_vbs_name + '.out')
        with open(output_file_name, 'rb') as output_file:
            hexdump(output_file.read())
            print('*' * 20)

        os.remove(in_vbs_name)
        os.remove(output_file_name)

    def test_paramconv_vbs(self):

        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as in_vbs:
            with VbsWriter(in_vbs, blocked=False) as writer:
                writer.write(b"Parameter message data")
            in_vbs_name = in_vbs.name
            in_vbs.close()

        output_file_name = in_vbs_name + '.out'

        # run with just input filename
        paramconv.cli_run(input=in_vbs_name, no1014blocking=True)
        with open(output_file_name, 'rb') as output_file:
            hexdump(output_file.read())
            print('*' * 20)

        os.remove(in_vbs_name)
        os.remove(output_file_name)
