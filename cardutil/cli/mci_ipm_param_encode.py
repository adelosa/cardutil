import argparse

from cardutil.cli import add_version
from cardutil.mciipm import VbsReader, VbsWriter


def cli_entry():
    args = vars(cli_parser().parse_args())
    if not args['out_filename']:
        args['out_filename'] = args['in_filename'] + '.out'

    with open(args['in_filename'], 'rb') as in_file, open(args['out_filename'], 'wb') as out_file:
        mci_ipm_param_encode(in_file, out_file=out_file, **args)


def cli_parser():

    parser = argparse.ArgumentParser(prog='mci_ipm_param_encode', description='Mastercard IPM param file encoder')
    parser.add_argument('in_filename')
    parser.add_argument('-o', '--out-filename')
    parser.add_argument('--in-encoding', default='ascii')
    parser.add_argument('--out-encoding', default='cp500')
    parser.add_argument('--no1014blocking', action='store_true')
    add_version(parser)

    return parser


def mci_ipm_param_encode(in_file, out_file, in_encoding='cp500', out_encoding='ascii', no1014blocking=False, **_):
    """
    Change encoding of parameter file from one encoding format to another.

    :param in_file: input parameter file object
    :param out_file: output parameter file object
    :param in_encoding: input file encoding string
    :param out_encoding: output file encoding string
    :param no1014blocking: set if 1014 blocking not required
    :return: None
    """
    blocked = not no1014blocking
    vbs_reader = VbsReader(in_file, blocked=blocked)

    in_records = (record.decode(in_encoding) for record in vbs_reader)
    out_records = (record.encode(out_encoding) for record in in_records)

    vbs_writer = VbsWriter(out_file, blocked=blocked)
    for record in out_records:
        vbs_writer.write(record)
    vbs_writer.close()
