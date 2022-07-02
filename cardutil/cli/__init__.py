import json
import logging
import os

from cardutil.config import config as pkg_config
from cardutil import __version__

LOGGER = logging.getLogger(__name__)


def print_banner(command_name, parms):
    message = (f'{command_name} -- cardutil version {__version__}\n'
               f'(C)Copyright 2019-2022 Anthony Delosa\n'
               f'See https://github.com/adelosa/cardutil')
    print(message)
    print('parameters:')
    for parm_key in parms:
        if parms[parm_key]:
            print(f' -{parm_key}:{parms[parm_key]}')


def add_version(parser):
    parser.add_argument('--version', action='version', version=f'%(prog)s (cardutil {__version__})')


def get_config(config_filename, envvar='CARDUTIL_CONFIG', cli_filename=None):
    # check for json config file provided from command line argument
    if cli_filename:
        if os.path.isfile(cli_filename):
            LOGGER.info('Using cli config at {}'.format(cli_filename))
            with open(cli_filename, 'r') as f:
                config = f.read()
            return json.loads(config)

    # check for json config file from ENVVAR directory
    config_dir = os.environ.get(envvar)
    LOGGER.debug('config_dir={}'.format(config_dir))
    if config_dir:
        config_dir = os.path.abspath(config_dir)
        LOGGER.debug(os.path.join(config_dir, config_filename))
        if os.path.isfile(os.path.join(config_dir, config_filename)):
            LOGGER.info('Using config at {}'.format(config_dir))
            config_filename = os.path.join(config_dir, config_filename)
            with open(config_filename, 'r') as f:
                config = f.read()
            return json.loads(config)

    # Use package config
    return pkg_config
