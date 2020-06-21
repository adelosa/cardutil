import argparse

from cardutil.cli import add_version
from cardutil.mciipm import VbsReader, VbsWriter


def cli_entry():
    cli_run(**vars(cli_parser().parse_args()))


def cli_run(**kwargs):
    if not kwargs.get('out_filename'):
        kwargs['out_filename'] = kwargs['in_filename'] + '.out'

    with open(kwargs['in_filename'], 'rb') as in_file, open(kwargs['out_filename'], 'wb') as out_file:
        mci_ipm_param_encode(in_file, out_file=out_file, **kwargs)


def cli_parser():

    parser = argparse.ArgumentParser(prog='mci_ipm_param_encode', description='Mastercard IPM param file encoder')
    parser.add_argument('in_filename')
    parser.add_argument('-o', '--out-filename')
    parser.add_argument('--in-encoding')
    parser.add_argument('--out-encoding')
    parser.add_argument('--no1014blocking', action='store_true')
    add_version(parser)

    return parser


def mci_ipm_param_encode(in_file, out_file, in_encoding=None, out_encoding=None, no1014blocking=False, **_):
    """
    Change encoding of parameter file from one encoding format to another.

    :param in_file: input parameter file object
    :param out_file: output parameter file object
    :param in_encoding: input file encoding string
    :param out_encoding: output file encoding string
    :param no1014blocking: set if 1014 blocking not required
    :return: None
    """
    if not in_encoding:
        in_encoding = 'latin_1'
    if not out_encoding:
        out_encoding = in_encoding
    blocked = not no1014blocking
    vbs_reader = VbsReader(in_file, blocked=blocked)

    in_records = (record.decode(in_encoding) for record in vbs_reader)
    out_records = (record.encode(out_encoding) for record in in_records)

    with VbsWriter(out_file, blocked=blocked) as vbs_writer:
        vbs_writer.write_many(out_records)


if __name__ == '__main__':
    cli_entry()
