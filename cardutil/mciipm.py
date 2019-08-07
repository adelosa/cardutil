import logging
import struct
import tempfile

from cardutil import iso8583
from cardutil.config import config
from cardutil.outputter import dicts_to_csv

LOGGER = logging.getLogger(__name__)


def change_encoding(in_file, out_file, in_encoding='cp500', out_encoding='latin-1'):
    """
    Change encoding of IPM file from one encoding scheme to another
    :param in_file: input IPM file object
    :param out_file: output IPM file object
    :param in_encoding: input file encoding string
    :param out_encoding: output file encoding string
    :return: None
    """
    # unblock the file (1014 to VBS)
    with tempfile.TemporaryFile() as temp_file1, tempfile.TemporaryFile() as temp_file2:
        unblock_1014(in_file, temp_file1)

        # convert iso messages from in encoding to python dicts (as generator)
        out_dict = (record for record in IpmReader(temp_file1, encoding=in_encoding))

        # convert dicts into iso messages using out encoding (as generator)
        vbs_out_record = (iso8583.dumps(record, encoding=out_encoding) for record in out_dict)

        # write the records into VBS file stream
        vbs_writer = VbsWriter(temp_file2)
        [vbs_writer.write(record) for record in vbs_out_record]  # writes the records
        vbs_writer.close()  # finalises the file by adding zero length record

        # block the file stream (VBS to 1014)
        block_1014(temp_file2, out_file)


def change_param_encoding(in_file, out_file, in_encoding='cp500', out_encoding='latin-1'):
    """
    Change encoding of parameter file from one encoding format to another
    :param in_file: input parameter file object
    :param out_file: output parameter file object
    :param in_encoding: input file encoding string
    :param out_encoding: output file encoding string
    :return: None
    """
    # unblock the file (1014 to VBS)
    with tempfile.TemporaryFile() as temp_file1, tempfile.TemporaryFile() as temp_file2:
        unblock_1014(in_file, temp_file1)
        vbs_reader = VbsReader(temp_file1)

        # decode the records to in_encoding (as generator)
        in_records = (record.decode(in_encoding) for record in vbs_reader)

        # encode the records to out_encoding (as generator)
        vbs_out_record = (record.encode(out_encoding) for record in in_records)

        # write the records to VBS format
        vbs_writer = VbsWriter(temp_file2)

        [vbs_writer.write(record) for record in vbs_out_record]  # writes the records
        vbs_writer.close()  # finalises the file by adding zero length record

        # block the file (VBS to 1014)
        block_1014(temp_file2, out_file)


def output_csv(in_file, out_file, in_encoding='latin-1'):
    """
    Extract IPM file data to csv format
    :param in_file: input IPM file object
    :param out_file: output csv file object
    :param in_encoding: input file encoding string
    :return: None
    """
    temp_file = tempfile.TemporaryFile()
    # unblock_1014(in_file, temp_file)
    # out_dict = (iso8583.loads(record, encoding=in_encoding) for record in VbsReader(temp_file))
    out_dict = (iso8583.loads(record, encoding=in_encoding) for record in VbsReader(Unblock(in_file)))
    dicts_to_csv(out_dict, config['output_data_elements'], out_file)


class Unblock(object):
    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.buffer = b''

    def read(self, bytes_to_read):
        while len(self.buffer) <= bytes_to_read:
            block = self.file_obj.read(1014)
            if not block:  # eof
                break
            self.buffer += block[:1012]
        output = self.buffer[:bytes_to_read]
        self.buffer = self.buffer[bytes_to_read:]
        return output

    def seek(self, pos):
        self.file_obj.seek(pos)

    def close(self):
        self.file_obj.close()


def unblock_1014(input_data, output_data):
    """
    Unblocks a 1014 byte blocked file object
    :param input_data: 1014 blocked IPM file object
    :param output_data: unblocked file object
    """
    pad_char = b'\x40'
    while True:
        record = input_data.read(1014)
        if not record:
            break
        if len(record) != 1014:
            raise ValueError('Invalid file size')
        if record[-2:] != pad_char * 2:
            raise ValueError('Invalid 1014 block line ending')
        output_data.write(record[0:1012])
    output_data.seek(0)
    input_data.seek(0)


def block_1014(input_data, output_data):
    """
    Creates a 1014 byte blocked file object
    :param input_data: file object to be 1014 byte blocked
    :param output_data: 1014 byte blocked file object
    """
    pad_char = b'\x40'

    while True:
        record = input_data.read(1012)
        # end of data
        if not record:
            break
        # incomplete 1012 block
        if len(record) != 1012:
            record += (1012 - len(record)) * pad_char
        output_data.write(record + (pad_char * 2))
    output_data.seek(0)
    input_data.seek(0)


class VbsReader(object):
    """
    The VbsReader class can be used to iterate through a VBS formatted file
    object record by record.

        vbs_reader = VbsReader(vbs_file_object)
        for vbs_record in vbs_reader:
            print(vbs_record)

    """
    def __init__(self, vbs_data):
        """
        Create a VbsReader object
        :param vbs_data: File object with VBS formatted data
        """
        self.vbs_data = vbs_data

    def __getattr__(self, name):
        """
        Attribute proxy for wrapped file object
        """
        try:
            return self.__dict__[name]
        except KeyError:
            if hasattr(self.vbs_data, name):
                return getattr(self.vbs_data, name)
        return None

    def __iter__(self):
        return self

    def __next__(self):
        """
        Unpacks a variable blocked object into records
        """
        record_length_raw = self.vbs_data.read(4)
        record_length = struct.unpack(">i", record_length_raw)[0]
        LOGGER.debug("record_length=%s", record_length)

        # exit if last record (length=0)
        if record_length == 0:
            raise StopIteration

        record = self.vbs_data.read(record_length)
        return record


class IpmReader(VbsReader):
    def __init__(self, vbs_data, encoding='ascii'):
        self.encoding = encoding
        super(IpmReader, self).__init__(vbs_data)

    def __next__(self):
        vbs_record = super(IpmReader, self).__next__()
        print(f'{len(vbs_record)}: {vbs_record}')
        return iso8583.loads(vbs_record, encoding=self.encoding)


class VbsWriter(object):
    def __init__(self, out_file):
        self.out_file = out_file

    def __getattr__(self, name):
        """
        Attribute proxy for wrapped file object
        """
        try:
            return self.__dict__[name]
        except KeyError:
            if hasattr(self.out_file, name):
                return getattr(self.out_file, name)
        return None

    def write(self, record):
        # get the length of the record
        record_length = len(record)
        # convert length to binary
        record_length_raw = struct.pack(">i", record_length)
        # add length to output data
        self.out_file.write(record_length_raw)
        # add data to output
        self.out_file.write(record)

    def close(self):
        # add zero length to end of record
        self.out_file.write(struct.pack(">i", 0))
        self.out_file.seek(0)
