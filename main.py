import sys
from cardutil.mciipm import change_encoding, output_csv


if __name__ == '__main__':
    with open(sys.argv[1], 'rb') as infile, open(sys.argv[2], 'wb') as outfile:
        change_encoding(infile, outfile)

    with open(sys.argv[1], 'rb') as infile, open(sys.argv[1] + '.csv', 'w') as outfile:
        output_csv(infile, outfile, in_encoding='cp500')
