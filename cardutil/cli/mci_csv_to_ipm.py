import argparse
import logging
from csv import DictReader

from cardutil.cli import add_version, get_config, print_banner
from cardutil.mciipm import IpmWriter


def cli_entry():
    cli_run(**vars(cli_parser().parse_args()))


def cli_run(**kwargs):
    print_banner('mci_csv_to_ipm', kwargs)

    if kwargs.get('debug'):
        logging.basicConfig(level=logging.DEBUG)

    config = get_config('cardutil.json', cli_filename=kwargs.get('config_file'))

    if not kwargs.get('out_filename'):
        kwargs['out_filename'] = kwargs['in_filename'] + '.ipm'

    with open(kwargs['in_filename'], 'r', encoding=kwargs.get('in_encoding')) as in_csv:
        with open(kwargs['out_filename'], 'wb') as out_ipm:
            mci_csv_to_ipm(in_csv=in_csv, out_ipm=out_ipm, config=config, **kwargs)


def cli_parser():
    parser = argparse.ArgumentParser(prog='mci_csv_to_ipm', description='CSV to Mastercard IPM')
    parser.add_argument('in_filename')
    parser.add_argument('-o', '--out-filename')
    parser.add_argument('--in-encoding')
    parser.add_argument('--out-encoding')
    parser.add_argument('--no1014blocking', action='store_true')
    parser.add_argument('--config-file', help='File containing cardutil configuration - JSON format')
    parser.add_argument('--debug', action='store_true')
    add_version(parser)

    return parser


def mci_csv_to_ipm(in_csv, out_ipm, config, out_encoding=None, no1014blocking=False, **_):
    """
    Create a Mastercard IPM file given an input csv file object

    :param in_csv: file object containing csv formatted data
    :param out_ipm: file object to receive IPM file
    :param config: dict containing cardutil config
    :param out_encoding: The IPM file encoding. 'cp500' works for EBCDIC
    :param no1014blocking: set True 1014 blocking not required
    :return: None
    """
    blocked = not no1014blocking
    with IpmWriter(out_ipm, encoding=out_encoding, blocked=blocked, iso_config=config.get('bit_config')) as writer:
        reader = DictReader(in_csv)
        for row in reader:
            record = {k: v for k, v in row.items() if v}
            writer.write(record)


if __name__ == '__main__':
    cli_entry()
