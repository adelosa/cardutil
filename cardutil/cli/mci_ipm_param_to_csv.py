import argparse
import csv
import logging

from cardutil.cli import add_version, get_config, print_banner
from cardutil import mciipm


def cli_entry():
    cli_run(**vars(cli_parser().parse_args()))


def cli_run(**kwargs):
    print_banner('mci_ipm_param_to_csv', kwargs)

    if kwargs.get('debug'):
        logging.basicConfig(level=logging.DEBUG)

    config = get_config('cardutil.json', cli_filename=kwargs.get('config_file'))
    param_config = config.get('mci_parameter_tables')

    if not kwargs.get('out_filename'):
        kwargs['out_filename'] = kwargs['in_filename'] + '_' + kwargs['table_id'] + '.csv'

    with open(kwargs['in_filename'], 'rb') as in_ipm:
        with open(kwargs['out_filename'], 'w', encoding=kwargs.get('out_encoding')) as out_csv:
            mci_ipm_param_to_csv(in_param=in_ipm, out_csv=out_csv, config=param_config, **kwargs)


def cli_parser():
    parser = argparse.ArgumentParser(prog='mci_ipm_param_to_csv', description='Mastercard IPM parameter file to CSV')
    parser.add_argument('in_filename', help='IPM Parameter file to process')
    parser.add_argument('table_id', help='Parameter table to extract')
    parser.add_argument('-o', '--out-filename')
    parser.add_argument('--in-encoding')
    parser.add_argument('--out-encoding')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--no1014blocking', action='store_true')
    parser.add_argument('--config-file', help='File containing cardutil configuration - JSON format')
    add_version(parser)

    return parser


def mci_ipm_param_to_csv(in_param, out_csv, table_id, config=None, in_encoding=None, no1014blocking=False, **_):
    blocked = not no1014blocking
    vbs_in = mciipm.IpmParamReader(in_param, table_id, param_config=config, blocked=blocked, encoding=in_encoding)
    csv_writer = csv.DictWriter(out_csv, fieldnames=config[table_id].keys(), extrasaction="ignore", lineterminator="\n")
    csv_writer.writeheader()
    csv_writer.writerows(vbs_in)


if __name__ == '__main__':
    cli_entry()
