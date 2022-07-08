import unittest
import io
import contextlib

from cardutil.cli import print_banner, print_exception_details
from cardutil.mciipm import MciIpmDataError


class GetConfigTestCase(unittest.TestCase):

    def test_print_banner(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            print_banner("test_command", {'parm1': 1, 'parm2': None})
        output = f.getvalue().splitlines()
        self.assertRegex(output[0], r'test_command \(cardutil \d*\.\d*\.\d*\)')  # don't include version
        assert output[1] == 'parameters:'
        assert output[2] == ' -parm1:1'

    def test_print_mciipmdataerror(self):
        ex = MciIpmDataError("A data error", record_number=1, binary_context_data=b'1234')
        print_exception_details(ex)
        ex = MciIpmDataError("A data error")  # plain error
        print_exception_details(ex)
