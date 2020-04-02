from cardutil import __version__


def add_version(parser):
    parser.add_argument('--version', action='version', version=f'%(prog)s (cardutil {__version__})')
