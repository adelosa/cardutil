import argparse
import logging

import cardutil.config
from cardutil.cli import add_version, print_banner
from cardutil.mciipm import IpmReader, IpmWriter


def cli_entry():
    cli_run(**vars(cli_parser().parse_args()))


def cli_run(**kwargs):
    print_banner('mci_ipm_encode', kwargs)

    if kwargs.get('debug'):
        logging.basicConfig(level=logging.DEBUG)

    if not kwargs.get('out_filename'):
        kwargs['out_filename'] = kwargs['in_filename'] + '.out'

    # if --no1014encoding provided, override new in-format and out-format parms
    if kwargs.get('no1014blocking'):
        kwargs['in_format'] = kwargs['out_format'] = 'vbs'

    with open(kwargs['in_filename'], 'rb') as in_file, open(kwargs['out_filename'], 'wb') as out_file:
        mci_ipm_encode(in_file, out_file=out_file, **kwargs)


def cli_parser():
    parser = argparse.ArgumentParser(prog='mci_ipm_encode', description='Mastercard IPM file encoder')
    parser.add_argument('in_filename')
    parser.add_argument('-o', '--out-filename')
    parser.add_argument('--in-encoding')
    parser.add_argument('--out-encoding')
    parser.add_argument('--no1014blocking', action='store_true')
    parser.add_argument('--in-format', choices=['vbs', '1014'], default='1014')
    parser.add_argument('--out-format', choices=['vbs', '1014'], default='1014')
    parser.add_argument('--debug', action='store_true')
    add_version(parser)
    return parser


def get_config():
    """
    when doing dict to iso conversion, PDS fields generation should be removed.
    This function takes the standard config and removes any PDS field processors
    """
    config = cardutil.config.config
    bit_config = config['bit_config']
    for field, field_config in bit_config.items():
        if field_config.get("field_processor") == 'PDS':
            del field_config['field_processor']
    return bit_config


def mci_ipm_encode(in_file, out_file=None, in_encoding='cp500', out_encoding='latin_1',
                   in_format='1014', out_format='1014', **_):
    """
    Change encoding of IPM file from one encoding scheme to another

    :param in_file: input IPM file object
    :param out_file: output IPM file object
    :param in_encoding: input file encoding string
    :param out_encoding: output file encoding string
    :param in_format: input file format (vbs/1014)
    :param out_format: output file format (vbs/1014)
    :return: None
    """

    in_blocked = True if in_format == '1014' else False
    out_blocked = True if out_format == '1014' else False
    with IpmWriter(out_file, encoding=out_encoding, blocked=out_blocked) as writer:
        reader = IpmReader(in_file, encoding=in_encoding, blocked=in_blocked, iso_config=get_config())
        writer.write_many(reader)


if __name__ == '__main__':
    cli_entry()
