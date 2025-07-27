import argparse
import logging

from cardutil import __version__
from cardutil.cli import print_banner, print_exception_details
from cardutil.cli.mideu import add_logging_arg_group, add_source_format_arg
from cardutil.mciipm import MciIpmDataError, VbsReader, VbsWriter


def cli_entry(*args):
    return cli_run(**vars(_get_cli_parser().parse_args(*args)))


def cli_run(**kwargs):

    print_banner('paramconv', kwargs)
    if not len(kwargs):
        print(__name__ + " (" + __version__ + ")")
        print("try --help for information")
        return -1

    logging.basicConfig(
        level=kwargs.get('loglevel'),
        format='%(asctime)s:%(name)s:%(lineno)s:%(levelname)s:%(message)s')

    out_filename = kwargs.get('output', kwargs['input'] + '.out')

    blocked = not kwargs.get('no1014blocking', False)
    kwargs['out_encoding'] = 'utf8'
    if kwargs.get('sourceformat', 'ebcdic') == 'ebcdic':
        in_encoding = 'cp500'
        out_encoding = 'latin1'
    else:
        in_encoding = 'latin1'
        out_encoding = 'cp500'

    try:
        with open(kwargs['input'], 'rb') as in_file, open(out_filename, 'wb') as out_file:
            mci_ipm_param_encode(
                in_file, out_file=out_file, blocked=blocked,
                in_encoding=in_encoding, out_encoding=out_encoding)
    except MciIpmDataError as err:
        print_exception_details(err)
        return -1

    print("Done!")


def _get_cli_parser():
    parser = argparse.ArgumentParser(
        description="MasterCard parameter file conversion utility ({version})".format(
            version=__version__)
    )
    parser.add_argument("input", help="MasterCard parameter file name")
    parser.add_argument("-o", "--output", help="Converted parameter file name")
    parser.add_argument("--version", action="version",
                        version="%(prog)s (" + __version__ + ")",
                        help="Get version information")

    add_source_format_arg(parser)
    add_logging_arg_group(parser)

    return parser


def mci_ipm_param_encode(in_file, out_file, in_encoding, out_encoding, blocked):
    """
    Change encoding of parameter file from one encoding format to another.

    :param in_file: input parameter file object
    :param out_file: output parameter file object
    :param in_encoding: input file encoding string
    :param out_encoding: output file encoding string
    :param blocked: 1014 blocked = True, VBS = False
    :return: None
    """
    vbs_reader = VbsReader(in_file, blocked=blocked)

    in_records = (record.decode(in_encoding) for record in vbs_reader)
    out_records = (record.encode(out_encoding) for record in in_records)

    with VbsWriter(out_file, blocked=blocked) as vbs_writer:
        vbs_writer.write_many(out_records)
