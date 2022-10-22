"""
Mastercard |reg| IPM clearing file readers and writers

* VBS file readers and writers
* IPM file readers and writers
* IPM parameter extract reader
* Support for 1014 blocked format


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

.. code-block:: text

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
import io
import logging
import struct
import typing

from cardutil import iso8583, config, CardutilError

LOGGER = logging.getLogger(__name__)


class MciIpmDataError(CardutilError):
    pass


class Block1014(object):
    """
    1014 Blocker for file objects.
    Wrap around a file object. Return 1014 blocked data
    """
    PAD_CHAR = b'\x40'

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.remaining_chars = 1012

    def __getattr__(self, name: str):
        """
        Attribute proxy for wrapped file object
        """
        try:
            return self.__dict__[name]
        except KeyError:
            if hasattr(self.file_obj, name):
                return getattr(self.file_obj, name)
        return None

    def write(self, bytes_to_write: bytes) -> None:
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

    def seek(self, pos: int) -> None:
        """
        Finalise then seek file object to requested position

        .. note:: Method only partially implemented. Only use to seek start of file (zero)
        """
        self.finalise()
        self.file_obj.seek(pos)

    def close(self) -> None:
        """
        Finalise then close the file object
        """
        self.finalise()
        self.file_obj.close()

    def finalise(self) -> None:
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
    def __init__(self, file_obj: typing.BinaryIO):
        self.file_obj = file_obj
        self.buffer = b''

    def __getattr__(self, name: str) -> any:
        """
        Attribute proxy for wrapped file object
        """
        try:
            return self.__dict__[name]
        except KeyError:
            if hasattr(self.file_obj, name):
                return getattr(self.file_obj, name)
        return None

    def read(self, bytes_to_read: int = 0):
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
    record_number = 1
    last_record = None

    def __init__(self, vbs_file: typing.BinaryIO, blocked: bool = False):
        """
        Create a VbsReader object

        :param vbs_file: File object with VBS formatted data
        """
        self.vbs_data = vbs_file
        if blocked:
            self.vbs_data = Unblock1014(vbs_file)

    def __getattr__(self, name) -> any:
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

    def __next__(self) -> bytes:
        """
        Unpacks a variable blocked object into records
        """
        record_length_raw = self.vbs_data.read(4)
        if len(record_length_raw) != 4:
            # this can happen if the VBS does not have a zero length record at end.
            # You can recreate using VbsWriter and not calling close method.
            # The reader will just accept we are at end if this happens.
            LOGGER.warning(f'Unable to read next record length - requested 4 bytes,'
                           f' got {len(record_length_raw)} -- assuming end of data')
            raise StopIteration

        record_length = struct.unpack(">i", record_length_raw)[0]
        LOGGER.debug("record_length=%s", record_length)

        # throw mcipm data error if length is negative or excessively large (indicates bad input)
        if record_length < 0 or record_length > 3000:
            raise MciIpmDataError(f"Invalid record length - value read was {record_length}",
                                  record_number=self.record_number,
                                  binary_context_data=self.last_record)

        # exit if last record (length=0)
        if record_length == 0:
            raise StopIteration

        record = self.vbs_data.read(record_length)
        if len(record) != record_length:
            raise MciIpmDataError(f"Unable to read complete record - record length: {record_length}, "
                                  f"data read: {len(record)}",
                                  record_number=self.record_number,
                                  binary_context_data=record_length_raw + record)

        self.last_record = record_length_raw + record  # save last record read
        self.record_number += 1    # increment record counter
        return record  # get the full record including the record length


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
    def __init__(self, ipm_file: typing.BinaryIO,
                 encoding: str = None, iso_config: dict = None, **kwargs):
        """
        Create a new IpmReader

        :param ipm_file: the file object to read
        :param encoding: the file encoding
        :param config: config dict with key bit_config
        """
        self.encoding = encoding
        self.iso_config = iso_config
        super(IpmReader, self).__init__(ipm_file, **kwargs)

    def __next__(self) -> dict:

        vbs_record = super(IpmReader, self).__next__()
        LOGGER.debug(f'{len(vbs_record)}: {vbs_record}')
        try:
            output = iso8583.loads(vbs_record, encoding=self.encoding, iso_config=self.iso_config)
        except CardutilError as ex:
            raise MciIpmDataError(
                'Error while loading ISO8583 record',
                binary_context_data=self.last_record,
                record_number=self.record_number,
                original_exception=ex
            )
        return output


class IpmParamReader(VbsReader):
    """
    IPM Param reader can be used to iterate through an IPM parameter extract file.
    The record is returned as a dictionary containing the parameter keys.

    ::

        from cardutil.mciipm import IpmParamReader
        with open('param.bin', 'rb') as param_in:
            reader = IpmParamReader(param_in, table_id='IP0040T1')
            for record in reader:
                print(record)

    If the parameter file is 1014 block format, then set the ``blocked`` parameter to True.

    ::

        from cardutil.mciipm import IpmParamReader
        with open('blocked_param.bin', 'rb') as param_in:
            reader = IpmParamReader(param_in, table_id='IP0040T1', blocked=True)
            for record in reader:
                print(record)

    """
    # layout for IP0000T1
    _IP0000T1_KEY = slice(11, 19)
    _IP0000T1_TABLE_ID = slice(19, 27)
    _IP0000T1_TABLE_SUB_ID = slice(243, 246)

    # table type for all except IP0000T1 - get this 3 letter code from self.table_keys
    _TABLE_SUB_ID = slice(8, 11)

    def __init__(self, param_file: typing.BinaryIO, table_id: str, encoding: str = None, param_config: dict = None,
                 **kwargs):
        """
        Create a new IpmParamReader

        :param param_file: the file object to read
        :param table_id: the IPM parameter table to read
        :param encoding: the parameter file encoding
        :param param_config: config dict with key bit_config
        """
        self.encoding = encoding if encoding else 'latin_1'
        self.param_config = param_config if param_config else config.config.get('mci_parameter_tables')
        self.table_id = table_id
        self.table_index = dict()
        super(IpmParamReader, self).__init__(param_file, **kwargs)

        # check if config available for table id
        if not self.param_config.get(table_id):
            raise MciIpmDataError(f'Parameter config not available for table {table_id}')

        # load the table index
        trailer_record_found = False
        while True:
            try:
                vbs_record = super(IpmParamReader, self).__next__()
            except StopIteration:
                break
            record = vbs_record.decode(self.encoding)
            if record[self._IP0000T1_KEY] == 'IP0000T1':
                self.table_index[record[self._IP0000T1_TABLE_SUB_ID]] = record[self._IP0000T1_TABLE_ID]
            if record.startswith('TRAILER RECORD IP0000T1'):
                trailer_record_found = True
                break
        LOGGER.debug('IP0000T1 records: {}'.format(self.table_index))
        if not trailer_record_found:
            raise MciIpmDataError('parameter file missing IP0000T1 trailer record')

    def __next__(self) -> dict:
        while True:
            record = super(IpmParamReader, self).__next__()
            record_table_id = self.table_index.get(record[self._TABLE_SUB_ID].decode(self.encoding))
            if record_table_id == self.table_id:
                record_dict = dict()
                for field in self.param_config[record_table_id]:
                    record_dict[field] = self._get_param_field(record, field)
                return record_dict

    def _get_param_field(self, record, field):
        table_id = self.table_index.get(record[self._TABLE_SUB_ID].decode(self.encoding))
        return record[
               self.param_config[
                   table_id][field]["start"]:self.param_config[table_id][field]["end"]].decode(self.encoding)


class VbsWriter(object):
    """
    Writes VBS formatted files.

    The writer can be used as follows::

        >>> with io.BytesIO() as vbs_out:
        ...     writer = VbsWriter(vbs_out)
        ...     writer.write(b'This is the record')
        ...     writer.close()

    The `close` method must be issued to finalise the file by adding the zero length record which
    indicated the end of the file.
    The message is a byte string containing the data.

    Alternatively, you can use as a context manager which will take care of the writer closure.

        >>> with io.BytesIO() as vbs_out:
        ...     with VbsWriter(vbs_out, blocked=True) as writer:
        ...         writer.write(b'This is the record')

    """
    def __init__(self, out_file: typing.BinaryIO, blocked: bool = False):
        self.out_file = out_file
        if blocked:
            self.out_file = Block1014(out_file)

    def __getattr__(self, name) -> any:
        """
        Attribute proxy for wrapped file object
        """
        try:
            return self.__dict__[name]
        except KeyError:
            if hasattr(self.out_file, name):
                return getattr(self.out_file, name)
        return None

    def write(self, record: bytes) -> None:
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

    def write_many(self, iterable: typing.Iterable[bytes]) -> None:
        """
        Convenience method to write multiple records from an iterable

        :param iterable: iterable providing records as bytes
        :return: None
        """
        for record in iterable:
            self.write(record)

    def close(self) -> None:
        """
        Finalise the VBS file output by adding the zero length file record.

        :return: None
        """
        # add zero length to end of record
        self.out_file.write(struct.pack(">i", 0))
        self.out_file.seek(0)

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


class IpmWriter(VbsWriter):
    """
    IPM writer can be used to write records to a Mastercard IPM file

    ::

        >>> with io.BytesIO() as ipm_out:
        ...    writer = IpmWriter(ipm_out)
        ...    writer.write({'MTI': '1111', 'DE2': '9999111122221111'})
        ...    writer.close()

    If the required file is 1014 block format, then set the ``blocked`` parameter to True.
    ::

        >>> with io.BytesIO() as ipm_out:
        ...     writer = IpmWriter(ipm_out, blocked=True)
        ...     writer.write({'MTI': '1111', 'DE2': '9999111122221111'})
        ...     writer.close()

    You can provide the specific file encoding if required.
    All standard python encoding schemes are supported. Mainframe systems likely use ``cp500``
    ::

       >>> with io.BytesIO() as ipm_out:
       ...     writer = IpmWriter(ipm_out, encoding='cp500')
       ...     writer.write({'MTI': '1111', 'DE2': '9999111122221111'})
       ...     writer.close()

    Alternatively use as a context manager to ensure closure at end of processing
    ::

       >>> with io.BytesIO() as ipm_out:
       ...     with IpmWriter(ipm_out, encoding='cp500') as writer:
       ...         writer.write({'MTI': '1111', 'DE2': '9999111122221111'})

    """
    def __init__(self, file_obj: typing.BinaryIO, encoding: str = None, iso_config: dict = None, **kwargs):
        """
        Create a new IpmWriter

        :param file_obj: the file object to write to
        :param encoding: the file encoding
        """
        self.encoding = encoding
        self.iso_config = iso_config
        super(IpmWriter, self).__init__(file_obj, **kwargs)

    def write(self, obj: dict) -> None:
        """
        Writes new record to IPM file

        :param obj: dictionary object containing ISO8583 elements.

        See :py:mod:`cardutil.iso8583` for expected dict object keys.

        :return: None
        """
        record = iso8583.dumps(obj, encoding=self.encoding, iso_config=self.iso_config)
        super(IpmWriter, self).write(record)

    def write_many(self, iterable: typing.Iterable[dict]) -> None:
        """
        Convenience method to write multiple records from an iterable

        :param iterable: iterable providing records as dict
        :return: None
        """
        for record in iterable:
            self.write(record)


def unblock_1014(input_data: typing.BinaryIO, output_data: typing.BinaryIO):
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
            raise MciIpmDataError('Invalid record size for 1014 blocked')
        if record[-2:] != pad_char * 2:
            raise MciIpmDataError('Invalid line ending for 1014 blocked')
        output_data.write(record[0:1012])
    output_data.seek(0)
    input_data.seek(0)


def block_1014(input_data: typing.BinaryIO, output_data: typing.BinaryIO):
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


def vbs_list_to_bytes(byte_list: iter, **kwargs) -> bytes:
    """
    Convenience function for creating VBS byte strings (optionally blocked) from list of byte strings

    :param byte_list: a list containing byte string records
    :param kwargs: any options to be passed to VbsWriter constructor. See :py:mod:`cardutil.mciipm.VbsWriter`
    :return: single byte string containing VBS data.
    """
    file_out = io.BytesIO()
    vbs_out = VbsWriter(file_out, **kwargs)
    for rec in byte_list:
        vbs_out.write(rec)
    vbs_out.close()
    return file_out.read()


def vbs_bytes_to_list(vbs_bytes: bytes, **kwargs) -> list:
    """
    Convenience function for unpacking VBS byte strings to byte string list

    :param vbs_bytes: single byte string containing VBS data
    :param kwargs: any options to be passed to VbsReader constructor. See :py:mod:`cardutil.mciipm.VbsReader`
    :return: a list containing byte string records
    """
    file_in = io.BytesIO(vbs_bytes)
    return [record for record in VbsReader(file_in, **kwargs)]


if __name__ == '__main__':
    import doctest
    doctest.testmod()
