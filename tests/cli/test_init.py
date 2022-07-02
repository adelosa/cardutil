import unittest
import io
import contextlib

from cardutil.cli import print_banner


class GetConfigTestCase(unittest.TestCase):

    def test_print_banner(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            print_banner("test_command", {'parm1': 1, 'parm2': None})
        output = f.getvalue().splitlines()
        self.assertRegex(output[0], r'test_command -- cardutil version \d*\.\d*\.\d*')  # don't include version
        self.assertRegex(output[1], r'\(C\)Copyright \d{4}-\d{4} Anthony Delosa')  # don't check years
        assert output[2] == 'See https://github.com/adelosa/cardutil'
        assert output[3] == 'parameters:'
        assert output[4] == ' -parm1:1'
