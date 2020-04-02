import argparse
from csv import DictReader

from cardutil.cli import add_version
from cardutil.mciipm import IpmWriter


def cli_entry():
    args = vars(cli_parser().parse_args())
    if not args['out_filename']:
        args['out_filename'] = args['in_filename'] + '.ipm'

    with open(args['in_filename'], 'r') as in_csv, open(args['out_filename'], 'wb') as out_ipm:
        mci_csv_to_ipm(in_csv=in_csv, out_ipm=out_ipm, **args)


def cli_parser():
    parser = argparse.ArgumentParser(prog='mci_csv_to_ipm', description='CSV to Mastercard IPM')
    parser.add_argument('in_filename')
    parser.add_argument('-o', '--out-filename')
    parser.add_argument('--out-encoding', default='ascii')
    parser.add_argument('--no1014blocking', action='store_true')
    add_version(parser)

    return parser


def mci_csv_to_ipm(in_csv, out_ipm, out_encoding='ascii', no1014blocking=False, **_):
    """
    Create a Mastercard IPM file given an input csv file object

    :param in_csv: file object containing csv formatted data
    :param out_ipm: file object to receive IPM file
    :param out_encoding: The IPM file encoding. 'cp500' works for EBCDIC
    :param no1014blocking: set True 1014 blocking not required
    :return: None
    """
    blocked = not no1014blocking
    reader = DictReader(in_csv)
    writer = IpmWriter(out_ipm, encoding=out_encoding, blocked=blocked)
    for row in reader:
        writer.write(row)
    writer.close()
