import argparse
import collections
import csv
import logging

from cardutil import __version__
from cardutil.cli import get_config, print_banner, print_exception_details
from cardutil.mciipm import IpmReader, IpmWriter, MciIpmDataError


def cli_entry(*args):
    return cli_run(**vars(_get_cli_parser().parse_args(*args)))


def cli_run(**kwargs):

    print_banner('mideu', kwargs)
    if not len(kwargs):
        print(__name__ + " (" + __version__ + ")")
        print("try --help for information")
        return -1

    config = get_config('cardutil.json', cli_filename=kwargs.get('config_file'))

    logging.basicConfig(
        level=kwargs.get('loglevel'),
        format='%(asctime)s:%(name)s:%(lineno)s:%(levelname)s:%(message)s')

    try:
        kwargs['func'](config=config, **kwargs)
    except MciIpmDataError as err:
        print_exception_details(err)
        return -1


def dicts_to_csv(data_list, output_file, field_list=None):
    """
    Writes dict data to CSV file

    :param data_list: list of dictionaries that contain the data to be loaded
    :param output_file: output CSV file
    :param field_list: (optional) list of fields to output to CSV file
    :return: None
    """

    if not field_list:
        # get the fields present in the dicts
        field_summary = collections.Counter()
        data_list = list(data_list)
        for item in data_list:
            field_summary.update(item.keys())
        field_list = [field_key for field_key in field_summary]

    writer = csv.DictWriter(
        output_file,
        fieldnames=field_list,
        extrasaction="ignore",
        lineterminator="\n")

    writer.writeheader()
    for data_item in data_list:
        writer.writerow({item: data_item[item] for item in data_item if item in field_list})


def _get_cli_parser():
    """
    mideu argparse parser create
    :return: parser
    """
    parser = argparse.ArgumentParser(
        description="MasterCard IPM file formatter ({version})".format(
            version=__version__)
    )
    parser.add_argument("--version", action="version",
                        version="%(prog)s (" + __version__ + ")",
                        help="Get version information")

    subparsers = parser.add_subparsers(help="Sub-command help")

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract help")
    extract_parser.set_defaults(func=extract)
    _add_common_args(extract_parser)
    _add_extract_args(extract_parser)

    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert help")
    convert_parser.set_defaults(func=convert)
    _add_common_args(convert_parser)

    return parser


def _add_common_args(parser):
    """
    mideu add common cli arguments
    :param parser: the argparse parser
    :return: None
    """
    parser.add_argument("input", help="Input IPM file name")
    add_source_format_arg(parser)
    add_logging_arg_group(parser)


def add_source_format_arg(parser):
    """
    Adds source format option to parser
    :param parser: the parser to add the source format option to
    :return: None
    """
    parser.add_argument(
        "-s", "--sourceformat",
        help="encoding format of source file",
        choices=["ebcdic", "ascii"],
        default="ebcdic"
    )

    parser.add_argument(
        "--no1014blocking",
        help="do not use 1014 block format. Just vbs type record",
        dest="no1014blocking",
        action="store_true"
    )


def add_logging_arg_group(parser):
    """
    Adds logging options to parser
    :param parser: the argparse parser to add logging options to
    :return: None
    """
    logging_arg_group = parser.add_argument_group("logging options")
    logging_arg_group.add_argument("-d", "--debug",
                                   help="turn debugging output on",
                                   action="store_const",
                                   dest="loglevel",
                                   const=logging.DEBUG,
                                   default=logging.WARNING)
    logging_arg_group.add_argument("-v", "--verbose",
                                   help="turn information output on",
                                   action="store_const",
                                   dest="loglevel",
                                   const=logging.INFO)


def _add_extract_args(parser):
    """
    mideu add extract subcommand arguments
    :param parser: the argparse parser
    :return: None
    """
    csv_arg_group = parser.add_argument_group("csv output options")
    csv_arg_group.add_argument("--csvoutputfile", help="Output filename")


def extract(config, **kwargs):
    """
    Create a csv file given an input Mastercard IPM file

    :param config: dict containing cardutil config
    :return: None
    """
    blocked = not kwargs.get('no1014blocking', False)
    kwargs['out_encoding'] = 'utf8'
    if kwargs.get('sourceformat', 'ebcdic') == 'ebcdic':
        kwargs['in_encoding'] = 'cp500'
    else:
        kwargs['in_encoding'] = 'latin1'
    if not kwargs.get('csvoutputfile'):
        kwargs['csvoutputfile'] = kwargs['input'] + '.csv'

    with open(kwargs['input'], 'rb') as in_ipm:
        with open(kwargs['csvoutputfile'], 'w', encoding=kwargs.get('out_encoding')) as out_csv:
            dicts_to_csv(
                IpmReader(in_ipm, encoding=kwargs['in_encoding'], blocked=blocked, iso_config=config.get('bit_config')),
                out_csv, field_list=config.get('output_data_elements'))


def convert(config, **kwargs):
    """
    Change encoding of IPM file from one encoding scheme to another

    :return: None
    """
    in_filename = kwargs['input']
    out_filename = in_filename + '.out'
    in_blocked = not kwargs.get('no1014blocking', False)
    out_blocked = in_blocked
    if kwargs.get('sourceformat', 'ebcdic') == 'ebcdic':
        in_encoding = 'cp500'
        out_encoding = 'latin1'
    else:
        in_encoding = 'latin1'
        out_encoding = 'cp500'

    with open(in_filename, 'rb') as in_file:
        with open(out_filename, 'wb') as out_file:
            with IpmWriter(out_file, encoding=out_encoding, blocked=in_blocked) as writer:
                reader = IpmReader(in_file, encoding=in_encoding, blocked=out_blocked)
                writer.write_many(reader)
