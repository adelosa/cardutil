import argparse

from cardutil.cli import add_version
from cardutil.mciipm import IpmReader, IpmWriter


def cli_entry():
    args = vars(cli_parser().parse_args())
    if not args['out_filename']:
        args['out_filename'] = args['in_filename'] + '.out'

    with open(args['in_filename'], 'rb') as in_file, open(args['out_filename'], 'wb') as out_file:
        mci_ipm_encode(in_file, out_file=out_file, **args)


def cli_parser():
    parser = argparse.ArgumentParser(prog='mci_ipm_encode', description='Mastercard IPM file encoder')
    parser.add_argument('in_filename')
    parser.add_argument('-o', '--out-filename')
    parser.add_argument('--in-encoding', default='ascii')
    parser.add_argument('--out-encoding', default='cp500')
    parser.add_argument('--no1014blocking', action='store_true')
    add_version(parser)
    return parser


def mci_ipm_encode(in_file, out_file=None, in_encoding='cp500', out_encoding='ascii', no1014blocking=False, **_):
    """
    Change encoding of IPM file from one encoding scheme to another

    :param in_file: input IPM file object
    :param out_file: output IPM file object
    :param in_encoding: input file encoding string
    :param out_encoding: output file encoding string
    :param no1014blocking: set True if not 1014 blocked file
    :return: None
    """
    blocked = not no1014blocking

    reader = IpmReader(in_file, encoding=in_encoding, blocked=blocked)
    writer = IpmWriter(out_file, encoding=out_encoding, blocked=blocked)

    for record in reader:
        writer.write(record)
    writer.close()  # finalises the file by adding zero length record
