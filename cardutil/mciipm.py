"""
Mastercard |reg| IPM clearing file readers and writers

* block and unblock 1014 blocked IPM and parameter files
* process VBS format records

Read an IPM file::

    from cardutil import mciipm
    with open('ipm_in.bin', 'rb') as ipm_in:
        reader = mciipm.IpmReader(ipm_in)
        for record in reader:
            print(record)

Create an IPM file::

    from cardutil import mciipm
    with open('ipm_out.bin', 'wb') as ipm_out:
        writer = mciipm.IpmWriter(ipm_out)
        writer.write({'MTI': '1111', 'DE2': '9999111122221111'})
        writer.close()

MasterCard file formats
-----------------------

VBS file format
^^^^^^^^^^^^^^^

This format is a basic variable record format.

There are no carriage returns or line feeds in the file.
A file consists of records. Each record is prefixed with a 4 byte binary length.

Say you had a file with the following 2 records:

.. code-block:: none

    "This is first record 1234567"  <- length 28
    "This is second record AAAABBBBB123"  <- length 34

Add 4 byte binary length to the start of each record. (x'1C' = 28, x'22' = 34)
with the file finishing with a zero length record length

.. code-block:: hexdump

    00000000: 00 00 00 1C 54 68 69 73  20 69 73 20 66 69 72 73  ....This is firs
    00000010: 74 20 72 65 63 6F 72 64  20 31 32 33 34 35 36 37  t record 1234567
    00000020: 00 00 00 22 54 68 69 73  20 69 73 20 73 65 63 6F  ..."This is seco
    00000030: 6E 64 20 72 65 63 6F 72  64 20 41 41 41 41 42 42  nd record AAAABB
    00000040: 42 42 42 31 32 33 00 00  00 00                    BBB123....

1014 blocked file format
^^^^^^^^^^^^^^^^^^^^^^^^
This is the same as VBS format with 1014 blocking applied.

The VBS data is blocked into lengths of 1012, and an additional
2 x'40' characters are appended at each block.

Finally, the total file length is made a multiple of 1014 with the final
incomplete record being filled with the x'40' character

Taking the above VBS example

.. code-block:: hexdump

    00000000: 00 00 00 1C 54 68 69 73  20 69 73 20 66 69 72 73  ....This is firs
    00000010: 74 20 72 65 63 6F 72 64  20 31 32 33 34 35 36 37  t record 1234567
    00000020: 00 00 00 22 54 68 69 73  20 69 73 20 73 65 63 6F  ..."This is seco
    00000030: 6E 64 20 72 65 63 6F 72  64 20 41 41 41 41 42 42  nd record AAAABB
    00000040: 42 42 42 31 32 33 00 00  00 00                    BBB123....

Block to 1014 by adding 2 * x'40' characters every 1012 characters in the data.
Finally fill with x'40' characters to next 1014 increment.
In this case, there is only one increment

.. code-block:: hexdump

    00000000: 00 00 00 1C 54 68 69 73  20 69 73 20 66 69 72 73  ....This is firs
    00000010: 74 20 72 65 63 6F 72 64  20 31 32 33 34 35 36 37  t record 1234567
    00000020: 00 00 00 22 54 68 69 73  20 69 73 20 73 65 63 6F  ..."This is seco
    00000030: 6E 64 20 72 65 63 6F 72  64 20 41 41 41 41 42 42  nd record AAAABB
    00000040: 42 42 42 31 32 33 00 00  00 00 40 40 40 40 40 40  BBB123....@@@@@@
    00000050: 40 40 40 40 40 40 40 40  40 40 40 40 40 40 40 40  @@@@@@@@@@@@@@@@
    000003E0: 40 40 40 40 40 40 40 40  40 40 40 40 40 40 40 40  @@@@@@@@@@@@@@@@
    000003F0: 40 40 40 40 40 40                                 @@@@@@

"""

import logging
import struct

from cardutil import iso8583

LOGGER = logging.getLogger(__name__)


class Block1014(object):
    """
    1014 Blocker for file objects.
    Wrap around a file object. Return 1014 blocked data
    """
    PAD_CHAR = b'\x40'

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.remaining_chars = 1012

    def __getattr__(self, name):
        """
        Attribute proxy for wrapped file object
        """
        try:
            return self.__dict__[name]
        except KeyError:
            if hasattr(self.file_obj, name):
                return getattr(self.file_obj, name)
        return None

    def write(self, bytes_to_write):
        """
        Write requested bytes to the output file object.
        """
        # not enough bytes to complete a block, just write and subtract from remaining
        LOGGER.debug(f'bytes_to_write={bytes_to_write}')
        if len(bytes_to_write) < self.remaining_chars:
            LOGGER.debug(f'len->{len(bytes_to_write)}<{self.remaining_chars}')
            LOGGER.debug(f'write {bytes_to_write}')
            self.file_obj.write(bytes_to_write)
            self.remaining_chars -= len(bytes_to_write)
            return

        # complete the first record
        LOGGER.debug(f'write first: {bytes_to_write[:self.remaining_chars]}')
        self.file_obj.write(bytes_to_write[:self.remaining_chars])
        self.file_obj.write(self.PAD_CHAR * 2)
        bytes_to_write = bytes_to_write[self.remaining_chars:]

        # now write complete blocks
        while len(bytes_to_write) > 1012:
            LOGGER.debug(f'write while: {bytes_to_write[:1012]}')
            self.file_obj.write(bytes_to_write[:1012])
            self.file_obj.write(self.PAD_CHAR * 2)
            bytes_to_write = bytes_to_write[1012:]

        # write whatever is left
        LOGGER.debug(f'write last: {bytes_to_write}')
        self.file_obj.write(bytes_to_write)
        self.remaining_chars = 1012-len(bytes_to_write)
        LOGGER.debug(f'remaining_chars={self.remaining_chars}')

    def seek(self, pos):
        """
        Finalise then seek file object to requested position

        .. note:: Method only partially implemented. Only use to seek start of file (zero)
        """
        self.finalise()
        self.file_obj.seek(pos)

    def close(self):
        """
        Finalise then close the file object
        """
        self.finalise()
        self.file_obj.close()

    def finalise(self):
        """
        Complete the blocking operation by creating final 1014 block.
        Called by ``close`` and ``seek`` methods to ensure completion.
        """
        self.file_obj.write(self.PAD_CHAR * (self.remaining_chars + 2))
        self.remaining_chars = 1012


class Unblock1014(object):
    """
    Unblocks 1014 blocked file objects.
    Wrap around a 1014 blocked file object. Return file like object providing only unblocked data
    """
    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.buffer = b''

    def __getattr__(self, name):
        """
        Attribute proxy for wrapped file object
        """
        try:
            return self.__dict__[name]
        except KeyError:
            if hasattr(self.file_obj, name):
                return getattr(self.file_obj, name)
        return None

    def read(self, bytes_to_read=0):
        """
        Read requested bytes from the file object. Returned data will be unblocked
        """
        read_all = True if not bytes_to_read else False
        while read_all or len(self.buffer) <= bytes_to_read:
            block = self.file_obj.read(1014)
            if not block:  # eof
                break
            self.buffer += block[:1012]
        output = self.buffer[:bytes_to_read]
        self.buffer = self.buffer[bytes_to_read:]
        return output


class VbsReader(object):
    """
    The VbsReader class can be used to iterate through a VBS formatted file
    object record by record.

    ::

        from cardutil.mciipm import VbsReader
        with open('vbs_file.bin', 'rb') as vbs_file:
            vbs_reader = VbsReader(vbs_file)
            for vbs_record in vbs_reader:
                print(vbs_record)

    """
    def __init__(self, vbs_file, blocked=False):
        """
        Create a VbsReader object

        :param vbs_file: File object with VBS formatted data
        """
        self.vbs_data = vbs_file
        if blocked:
            self.vbs_data = Unblock1014(vbs_file)

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
    """
    IPM reader can be used to iterate through an IPM file

    The file object must be in VBS format.

    ::

        from cardutil.mciipm import IpmReader
        with open('vbs_in.bin', 'rb') as vbs_in:
            reader = IpmReader(vbs_in)
            for record in reader:
                print(record)

    If the file required 1014 block format, then set the ``blocked`` parameter to True.

    ::

        from cardutil.mciipm import IpmReader
        with open('blocked_in.bin', 'rb') as blocked_in:
            reader = IpmReader(blocked_in, blocked=True)
            for record in reader:
                print(record)

    """
    def __init__(self, ipm_file, encoding='ascii', **kwargs):
        """
        Create a new IpmReader

        :param ipm_file: the file object to read
        :param encoding: the file encoding
        """
        self.encoding = encoding
        super(IpmReader, self).__init__(ipm_file, **kwargs)

    def __next__(self):
        vbs_record = super(IpmReader, self).__next__()
        LOGGER.debug(f'{len(vbs_record)}: {vbs_record}')
        return iso8583.loads(vbs_record, encoding=self.encoding)


class VbsWriter(object):
    """
    Writes VBS formatted files.

    The writer can be used as follows::

        with open('vbs_out.bin', 'wb') as vbs_out:
            writer = VbsWriter(vbs_out)
            writer.write(b'This is the record')
            writer.close()

    The message is a byte string containing the data.

    The `close` method must be issued to finalise the file by adding the zero length record which
    indicated the end of the file.
    """
    def __init__(self, out_file, blocked=False):
        self.out_file = out_file
        if blocked:
            self.out_file = Block1014(out_file)

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
        """
        Add a new record to the VBS output file

        :param record: byte string containing data
        :return: None
        """
        # get the length of the record
        record_length = len(record)
        # convert length to binary
        record_length_raw = struct.pack(">i", record_length)
        # add length to output data
        self.out_file.write(record_length_raw)
        # add data to output
        self.out_file.write(record)

    def close(self):
        """
        Finalise the VBS file output by adding the zero length file record.

        :return: None
        """
        # add zero length to end of record
        self.out_file.write(struct.pack(">i", 0))
        self.out_file.seek(0)


class IpmWriter(VbsWriter):
    """
    IPM writer can be used to write records to a Mastercard IPM file

    ::

        from cardutil.mciipm import IpmWriter
        with open('ipm_out.bin', 'wb') as ipm_out:
            writer = IpmWriter(ipm_out)
            writer.write({'MTI': '1111', 'DE2': '9999111122221111'})
            writer.close()

    If the required file is 1014 block format, then set the ``blocked`` parameter to True.

    ::

        from cardutil.mciipm import IpmWriter
        with open('ipm_out.bin', 'wb') as ipm_out:
            writer = IpmWriter(ipm_out, blocked=True)
            writer.write({'MTI': '1111', 'DE2': '9999111122221111'})
            writer.close()

    By default, the file output is ``ascii`` encoded, but you can provide an alternative
    encoding if required. All standard python encoding schemes are supported.
    Mainframe systems likely use ``cp500``

    ::

       writer = IpmWriter(vbs_out, encoding='cp500')
       writer.write({'MTI': '1111', 'DE2': '9999111122221111'})
       writer.close()

    """
    def __init__(self, file_obj, encoding='ascii', **kwargs):
        """
        Create a new IpmWriter

        :param file_obj: the file object to write to
        :param encoding: the file encoding
        """
        self.encoding = encoding
        super(IpmWriter, self).__init__(file_obj, **kwargs)

    def write(self, obj):
        """
        Writes new record to IPM file

        :param obj: dictionary object containing ISO8583 elements.

        See :py:mod:`cardutil.iso8583` for expected dict object keys.

        :return: None
        """
        record = iso8583.dumps(obj, encoding=self.encoding)
        super(IpmWriter, self).write(record)


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
