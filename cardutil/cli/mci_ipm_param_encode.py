import argparse
import logging

from cardutil.cli import add_version, print_banner
from cardutil.mciipm import VbsReader, VbsWriter


def cli_entry():
    cli_run(**vars(cli_parser().parse_args()))


def cli_run(**kwargs):
    print_banner('mci_ipm_param_encode', kwargs)

    if kwargs.get('debug'):
        logging.basicConfig(level=logging.DEBUG)

    if not kwargs.get('out_filename'):
        kwargs['out_filename'] = kwargs['in_filename'] + '.out'

    # if --no1014encoding provided, override new in-format and out-format parms
    if kwargs.get('no1014blocking'):
        kwargs['in_format'] = kwargs['out_format'] = 'vbs'

    with open(kwargs['in_filename'], 'rb') as in_file, open(kwargs['out_filename'], 'wb') as out_file:
        mci_ipm_param_encode(in_file, out_file=out_file, **kwargs)


def cli_parser():

    parser = argparse.ArgumentParser(prog='mci_ipm_param_encode', description='Mastercard IPM param file encoder')
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


def mci_ipm_param_encode(in_file, out_file, in_encoding=None, out_encoding=None,
                         in_format='1014', out_format='1014', **_):
    """
    Change encoding of parameter file from one encoding format to another.

    :param in_file: input parameter file object
    :param out_file: output parameter file object
    :param in_encoding: input file encoding string
    :param out_encoding: output file encoding string
    :param in_format: input file format (vbs/1014)
    :param out_format: output file format (vbs/1014)
    :return: None
    """
    if not in_encoding:
        in_encoding = 'latin_1'
    if not out_encoding:
        out_encoding = in_encoding

    in_blocked = True if in_format == '1014' else False
    vbs_reader = VbsReader(in_file, blocked=in_blocked)

    in_records = (record.decode(in_encoding) for record in vbs_reader)
    out_records = (record.encode(out_encoding) for record in in_records)
    out_blocked = True if out_format == '1014' else False
    with VbsWriter(out_file, blocked=out_blocked) as vbs_writer:
        vbs_writer.write_many(out_records)


if __name__ == '__main__':
    cli_entry()
