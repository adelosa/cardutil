import os
import tempfile
import unittest

from cardutil.cli import get_config


class GetConfigTestCase(unittest.TestCase):
    def test_envvar_config(self):
        with tempfile.NamedTemporaryFile('w+', delete=False) as config_file:
            config_file.write('{"config": "hello"}')
            config_full_filename = config_file.name
            config_dir = os.path.dirname(config_file.name)
            config_filename = os.path.basename(config_file.name)
            config_file.close()
        os.environ['TEST_ENVVAR'] = config_dir
        config = get_config(config_filename, envvar="TEST_ENVVAR")
        print(config)
        os.remove(config_full_filename)
        if os.environ.get('TEST_ENVVAR'):
            del os.environ['TEST_ENVVAR']
        self.assertEqual(config, {"config": "hello"})

    def test_envvar_config_not_found(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ['TEST_ENVVAR'] = temp_dir
            config = get_config("test", envvar="TEST_ENVVAR")
        self.assertIn('bit_config', config.keys())
        print(config)

    def test_cli_config(self):
        with tempfile.NamedTemporaryFile('w+', delete=False) as config_file:
            config_file.write('{"config": "hello2"}')
            config_full_filename = config_file.name
            config_filename = os.path.basename(config_file.name)
            config_file.close()
        if os.environ.get('TEST_ENVVAR'):
            del os.environ['TEST_ENVVAR']
        config = get_config(config_filename, envvar="TEST_ENVVAR", cli_filename=config_full_filename)
        os.remove(config_full_filename)
        self.assertEqual(config, {"config": "hello2"})

    def test_cli_config_not_found(self):
        config = get_config("test", envvar="TEST_ENVVAR", cli_filename="THIS_FILE_DOES_NOT_EXIST")
        self.assertIn('bit_config', config.keys())


if __name__ == '__main__':
    unittest.main()
