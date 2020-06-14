import argparse

from cardutil.cli import add_version, get_config
from cardutil.mciipm import IpmReader
from cardutil.outputter import dicts_to_csv


def cli_entry():
    cli_run(**vars(cli_parser().parse_args()))


def cli_run(**kwargs):

    config = get_config('cardutil.json', cli_filename=kwargs.get('config_file'))

    if not kwargs.get('out_filename'):
        kwargs['out_filename'] = kwargs['in_filename'] + '.csv'

    with open(kwargs['in_filename'], 'rb') as in_ipm:
        with open(kwargs['out_filename'], 'w', encoding=kwargs.get('out_encoding')) as out_csv:
            mci_ipm_to_csv(in_ipm=in_ipm, out_csv=out_csv, config=config, **kwargs)


def cli_parser():
    parser = argparse.ArgumentParser(prog='mci_ipm_to_csv', description='Mastercard IPM to CSV')
    parser.add_argument('in_filename')
    parser.add_argument('-o', '--out-filename')
    parser.add_argument('--in-encoding')
    parser.add_argument('--out-encoding')
    parser.add_argument('--no1014blocking', action='store_true')
    parser.add_argument('--config-file', help='File containing cardutil configuration - JSON format')
    add_version(parser)

    return parser


def mci_ipm_to_csv(in_ipm, out_csv, config, in_encoding=None, no1014blocking=False, **_):
    """
    Create a csv file given an input Mastercard IPM file

    :param in_ipm: binary input IPM file object
    :param out_csv: output csv file object
    :param config: dict containing cardutil config
    :param in_encoding: input file encoding string
    :param no1014blocking: set True if no 1014 blocking used
    :return: None
    """
    blocked = not no1014blocking
    dicts_to_csv(
        IpmReader(in_ipm, encoding=in_encoding, blocked=blocked, iso_config=config.get('bit_config')),
        config.get('output_data_elements'), out_csv)
