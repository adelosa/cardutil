import argparse
from csv import DictReader

from cardutil import __version__
from cardutil.mciipm import IpmReader, IpmWriter, VbsReader, VbsWriter
from cardutil.config import config
from cardutil.outputter import dicts_to_csv


def add_version(parser):
    parser.add_argument('--version', action='version', version=f'%(prog)s (cardutil {__version__})')


def mci_ipm_encode_cli():
    mci_ipm_encode_cli_main(vars(mci_ipm_encode_cli_parser().parse_args()))


def mci_ipm_encode_cli_parser():
    parser = argparse.ArgumentParser(prog='mci_ipm_encode', description='Mastercard IPM file encoder')
    parser.add_argument('in_filename')
    parser.add_argument('-o', '--out-filename')
    parser.add_argument('--in-encoding', default='ascii')
    parser.add_argument('--out-encoding', default='cp500')
    parser.add_argument('--no1014blocking', action='store_true')
    add_version(parser)
    return parser


def mci_ipm_encode_cli_main(args):
    if not args['out_filename']:
        args['out_filename'] = args['in_filename'] + '.out'

    with open(args['in_filename'], 'rb') as in_file, open(args['out_filename'], 'wb') as out_file:
        mci_ipm_encode(in_file, out_file=out_file, **args)


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


def mci_ipm_param_encode_cli():
    mci_ipm_param_encode_cli_main(vars(mci_ipm_param_encode_cli_parser().parse_args()))


def mci_ipm_param_encode_cli_parser():
    parser = argparse.ArgumentParser(prog='mci_ipm_param_encode', description='Mastercard IPM param file encoder')
    parser.add_argument('in_filename')
    parser.add_argument('-o', '--out-filename')
    parser.add_argument('--in-encoding', default='ascii')
    parser.add_argument('--out-encoding', default='cp500')
    parser.add_argument('--no1014blocking', action='store_true')
    add_version(parser)

    return parser


def mci_ipm_param_encode_cli_main(args):

    if not args['out_filename']:
        args['out_filename'] = args['in_filename'] + '.out'

    with open(args['in_filename'], 'rb') as in_file, open(args['out_filename'], 'wb') as out_file:
        mci_ipm_param_encode(in_file, out_file=out_file, **args)


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


def mci_ipm_to_csv_cli():
    mci_ipm_to_csv_cli_main(vars(mci_ipm_to_csv_cli_parser().parse_args()))


def mci_ipm_to_csv_cli_parser():
    parser = argparse.ArgumentParser(prog='mci_ipm_to_csv', description='Mastercard IPM to CSV')
    parser.add_argument('in_filename')
    parser.add_argument('-o', '--out-filename')
    parser.add_argument('--in-encoding', default='ascii')
    parser.add_argument('--no1014blocking', action='store_true')
    add_version(parser)

    return parser


def mci_ipm_to_csv_cli_main(args):
    if not args['out_filename']:
        args['out_filename'] = args['in_filename'] + '.csv'

    with open(args['in_filename'], 'rb') as in_ipm, open(args['out_filename'], 'w') as out_csv:
        mci_ipm_to_csv(in_ipm=in_ipm, out_csv=out_csv, **args)


def mci_ipm_to_csv(in_ipm, out_csv, in_encoding='ascii', no1014blocking=False, **_):
    """
    Create a csv file given an input Mastercard IPM file

    :param in_ipm: binary input IPM file object
    :param out_csv: output csv file object
    :param in_encoding: input file encoding string
    :param no1014blocking: set True if no 1014 blocking used
    :return: None
    """
    blocked = not no1014blocking
    dicts_to_csv(IpmReader(in_ipm, encoding=in_encoding, blocked=blocked), config['output_data_elements'], out_csv)


def mci_csv_to_ipm_cli():
    mci_csv_to_ipm_cli_main(vars(mci_csv_to_ipm_cli_parser().parse_args()))


def mci_csv_to_ipm_cli_parser():
    parser = argparse.ArgumentParser(prog='mci_csv_to_ipm', description='CSV to Mastercard IPM')
    parser.add_argument('in_filename')
    parser.add_argument('-o', '--out-filename')
    parser.add_argument('--out-encoding', default='ascii')
    parser.add_argument('--no1014blocking', action='store_true')
    add_version(parser)

    return parser


def mci_csv_to_ipm_cli_main(args):
    if not args['out_filename']:
        args['out_filename'] = args['in_filename'] + '.ipm'

    with open(args['in_filename'], 'r') as in_csv, open(args['out_filename'], 'wb') as out_ipm:
        mci_csv_to_ipm(in_csv=in_csv, out_ipm=out_ipm, **args)


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
