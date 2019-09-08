from csv import DictReader

from cardutil.mciipm import IpmReader, IpmWriter, VbsReader, VbsWriter
from cardutil.config import config
from cardutil.outputter import dicts_to_csv


def change_encoding(in_file, out_file, in_encoding='cp500', out_encoding='latin-1', blocked=True):
    """
    Change encoding of IPM file from one encoding scheme to another

    :param in_file: input IPM file object
    :param out_file: output IPM file object
    :param in_encoding: input file encoding string
    :param out_encoding: output file encoding string
    :param blocked: set True if input file is 1014 blocked
    :return: None
    """
    reader = IpmReader(in_file, encoding=in_encoding, blocked=blocked)
    writer = IpmWriter(out_file, encoding=out_encoding, blocked=blocked)

    for record in reader:
        writer.write(record)
    writer.close()  # finalises the file by adding zero length record


def change_param_encoding(in_file, out_file, in_encoding='cp500', out_encoding='latin-1', blocked=True):
    """
    Change encoding of parameter file from one encoding format to another.

    :param in_file: input parameter file object
    :param out_file: output parameter file object
    :param in_encoding: input file encoding string
    :param out_encoding: output file encoding string
    :param blocked: set True if input file is 1014 blocked
    :return: None
    """
    vbs_reader = VbsReader(in_file, blocked=blocked)

    in_records = (record.decode(in_encoding) for record in vbs_reader)
    out_records = (record.encode(out_encoding) for record in in_records)

    vbs_writer = VbsWriter(out_file, blocked=blocked)
    for record in out_records:
        vbs_writer.write(record)
    vbs_writer.close()


def output_csv(in_ipm, out_csv, in_encoding='latin-1', blocked=True):
    """
    Create a csv file given an input Mastercard IPM file

    :param in_ipm: binary input IPM file object
    :param out_csv: output csv file object
    :param in_encoding: input file encoding string
    :param blocked: set True if input file is 1014 blocked
    :return: None
    """
    dicts_to_csv(IpmReader(in_ipm, encoding=in_encoding, blocked=blocked), config['output_data_elements'], out_csv)


def csv_to_ipm(in_csv, out_ipm, out_encoding='latin1', blocked=False):
    """
    Create a Mastercard IPM file given an input csv file object

    :param in_csv: file object containing csv formatted data
    :param out_ipm: file object to receive IPM file
    :param out_encoding: The IPM file encoding. 'cp500' works for EBCDIC
    :param blocked: set True if output file should be 1014 blocked
    :return: None
    """

    reader = DictReader(in_csv)
    writer = IpmWriter(out_ipm, encoding=out_encoding, blocked=blocked)
    for row in reader:
        writer.write(row)
    writer.close()
