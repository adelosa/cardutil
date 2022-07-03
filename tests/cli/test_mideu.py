"""
mideu is a command line utility that is part of a deprecated package mciutil
The goal is for this to be compatible with that tool while using the new
engine from cardutil.
"""
import os
import tempfile
import unittest

from cardutil.cli import mideu

CONFIG_DATA = """
{
    "bit_config": {
        "38": {
            "field_name": "Approval code",
            "field_type": "FIXED",
            "field_length": 6
        }
    }
}
"""


class MideuTestCases(unittest.TestCase):
    def test_mideu_no_params(self):
        mideu.cli_run()

    def test_mideu_help(self):
        with self.assertRaises(SystemExit) as ex:
            mideu.cli_entry(['--help'])
        self.assertEqual(ex.exception.code, 0)

    def test_mideu_extract_exception(self):
        in_ipm_data = (b'\x00\x00\x00\x1a0100\x80\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'nXmXlX\xFF\xFF\x00\x00')

        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as in_ipm:
            in_ipm.write(in_ipm_data)
            in_ipm_name = in_ipm.name
            print(in_ipm_name)
            in_ipm.close()

            mideu.cli_run(
                input=in_ipm_name,
                csvoutputfile=in_ipm_name + '.csv',
                sourceformat='ascii',
                debug=True,
                func=mideu.extract
            )

        os.remove(in_ipm_name)
        os.remove(in_ipm_name + '.csv')

    def test_mideu_extract(self):
        """
        Runs mideu extract command from cli_run
        """
        in_ipm_data = (b'\x00\x00\x00\x1a0100\x80\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'nXmXlX\x00\x00\x00\x00')

        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as in_ipm:
            in_ipm.write(in_ipm_data)
            in_ipm_name = in_ipm.name
            print(in_ipm_name)
            in_ipm.close()

        # run with config file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as in_config:
            config_filename = in_config.name
            in_config.write(CONFIG_DATA)
            in_config.close()
            mideu.cli_run(
                config_file=config_filename,
                input=in_ipm_name,
                # csvoutputfile=in_ipm_name + '.csv',
                sourceformat='ascii',
                debug=True,
                func=mideu.extract
            )
            os.remove(config_filename)

        csv_output = open(in_ipm_name + '.csv', 'r').read()
        self.assertEqual(csv_output, "MTI,DE38\n0100,nXmXlX\n")
        os.remove(in_ipm_name)
        os.remove(in_ipm_name + '.csv')

    def test_mideu_extract_with_output(self):
        """
        Runs mideu extract command from cli_run, output file specified
        """
        in_ipm_data = (b'\x00\x00\x00\x1a0100\x80\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'nXmXlX\x00\x00\x00\x00')

        with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as in_ipm:
            in_ipm.write(in_ipm_data)
            in_ipm_name = in_ipm.name
            print(in_ipm_name)
            in_ipm.close()

        # run with config file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as in_config:
            config_filename = in_config.name
            in_config.write(CONFIG_DATA)
            in_config.close()
            mideu.cli_run(
                config_file=config_filename,
                input=in_ipm_name,
                csvoutputfile=in_ipm_name + '.csv',
                sourceformat='ascii',
                debug=True,
                func=mideu.extract
            )
            os.remove(config_filename)

        csv_output = open(in_ipm_name + '.csv', 'r').read()
        self.assertEqual(csv_output, "MTI,DE38\n0100,nXmXlX\n")
        os.remove(in_ipm_name)
        os.remove(in_ipm_name + '.csv')

    def test_mideu_convert(self):
        """
        Run mideu convert from cli_run
        """
        # create an ipm file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as out_ipm:
            out_ipm.write(
                b'\x00\x00\x00\x1a0100\x80\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                b'n\x9cm\x9cl\x9c\x00\x00\x00\x00')
            in_ipm_name = out_ipm.name
            out_ipm.close()

        mideu.cli_run(func=mideu.convert, input=in_ipm_name)
        mideu.cli_run(func=mideu.convert, input=in_ipm_name, no1014blocking=True)
        mideu.cli_run(func=mideu.convert, input=in_ipm_name + '.out', no1014blocking=True, sourceformat='ascii')
        mideu.cli_run(func=mideu.extract, input=in_ipm_name + '.out', no1014blocking=True)

        os.remove(in_ipm_name)
        os.remove(in_ipm_name + '.out')
        os.remove(in_ipm_name + '.out' + '.csv')
        os.remove(in_ipm_name + '.out' + '.out')
