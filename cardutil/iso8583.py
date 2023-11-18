"""
Parsers for ISO8583 messages.

The iso8583 module provides ISO8583 message parsing functions.
See `ISO8583 Wikipedia page <https://en.wikipedia.org/wiki/ISO_8583>`_. for more details.
Also supports Mastercard |reg| PDS field structures.

The parsing functions are modelled on the python standard json library.
The functions convert raw ISO8583 messages to python dictionaries.

Dictionary keys that represent the elements of an ISO8583 message.

* MTI - Message type indicator
* DE(1-127) - Standard fields
* PDSxxxx - Mastercard PDS fields
* TAGxxxx - ICC tag fields

Import the library::

    from cardutil.iso8583 import dumps, loads

Read an ISO8583 message returning dict::

    >>> import binascii
    >>> binary_bitmap = binascii.unhexlify('c0000000000000000000000000000000')
    >>> message_bytes = b'1144' + binary_bitmap + b'164444555566667777'
    >>> message_dict = loads(message_bytes)
    >>> message_dict
    {'MTI': '1144', 'DE2': '4444555566667777'}

Create an ISO8583 message returning bytes::

    >>> message_dict = {'MTI': '1144', 'DE2': '4444555566667777'}
    >>> message_bytes = dumps(message_dict)
    >>> message_bytes
    b'1144\\xc0\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00164444555566667777'


Add **encoding** parameter if you need different message encoding.
All `standard python encoding codecs
<https://docs.python.org/3/library/codecs.html?highlight=encode#standard-encodings>`_ are available.
Default is **latin_1**.

::

    >>> message_dict = {'MTI': '1144', 'DE2': '4444555566667777'}
    >>> message_bytes = dumps(message_dict, encoding='cp500')
    >>> message_bytes
    b'\\xf1\\xf1\\xf4\\xf4\\xc0\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\xf1\\xf6\\xf4\\xf4\\xf4\\xf4\\xf5\\xf5\\xf5\\xf5\\xf6\\xf6\\xf6\\xf6\\xf7\\xf7\\xf7\\xf7'
    >>> message_dict = loads(message_bytes, encoding='cp500')
    >>> message_dict
    {'MTI': '1144', 'DE2': '4444555566667777'}

Set **hex_bitmap** to True if you require a hex format bitmap::

    >>> message_bytes = dumps(message_dict, hex_bitmap=True)
    >>> message_bytes
    b'1144c0000000000000000000000000000000164444555566667777'
    >>> message_dict = loads(message_bytes, hex_bitmap=True)
    >>> message_dict
    {'MTI': '1144', 'DE2': '4444555566667777'}

"""
import binascii
import datetime
import decimal
import logging
import re
import struct
import sys

from cardutil import CardutilError
from cardutil.BitArray import BitArray
from cardutil.card import mask
from cardutil.config import config
from cardutil.vendor.hexdump import hexdump

LOGGER = logging.getLogger(__name__)
DEFAULT_ENCODING = 'latin_1'


class Iso8583DataError(CardutilError):
    pass


def dumps(obj: dict, encoding=None, iso_config=None, hex_bitmap=False):
    """
    Serialize obj to a ISO8583 message byte string

    :param obj: dict containing message data
    :param encoding: python text encoding scheme
    :param iso_config: iso8583 message configuration dict
    :param hex_bitmap: bitmap in hex format
    :return: byte string containing ISO8583 message

    The default usage will generate a latin_1 encoded message with a binary bitmap::

        import cardutil.iso8583
        message_dict = {'MTI': '1144', 'DE2': '4444555566667777'}
        cardutil.iso8583.dumps(message_dict)

    """
    if not encoding:
        encoding = DEFAULT_ENCODING
    if not iso_config:
        iso_config = config['bit_config']

    output = _dict_to_iso8583(obj, iso_config, encoding, hex_bitmap)
    return output


def loads(b: bytes, encoding=None, iso_config=None, hex_bitmap=False):
    """
    Deserialise b (byte string) to a python object

    :param b: bytes containing message
    :param encoding: python text encoding scheme
    :param iso_config: iso8583 message configuration dictionary
    :param hex_bitmap: bitmap in hex format
    :return: dict containing message data

    ::

        import cardutil.iso8583
        message_bytes = b'1144... iso message ...'
        cardutil.iso8583.loads(message_bytes)

    """
    if not encoding:
        encoding = DEFAULT_ENCODING
    if not iso_config:
        iso_config = config['bit_config']

    return _iso8583_to_dict(b, iso_config, encoding, hex_bitmap)


def _iso8583_to_dict(message, bit_config, encoding=DEFAULT_ENCODING, hex_bitmap=False):
    """
    Convert ISO8583 style message to dictionary

    :param message: The message in ISO8583 based format

    * Message Type indicator - 4 bytes
    * Binary bitmap - 16 bytes (Reads DE1 and DE2)
    OR if hex_bitmap = True
    * Message Type indicator - 4 bytes
    * Hex bitmap - 32 bytes (Reads DE1 and DE2)
    * Message data - Remainder of record

    :param bit_config: dictionary of bit mapping configuration
    :param encoding: data encoding
    :return: dictionary of message elements

    * key = 'MTI' message type indicator
    * key = 'DEx' data elements
    * key = 'PDSxxxx' private data fields
    * key = 'TAGxxxx' icc fields

    """
    LOGGER.debug("Processing message: len=%s contents:\n%s", len(message), hexdump(message, result="return"))
    # split raw message into components MessageType(4B), Bitmap(16B),
    # Message(l=*)

    try:
        if hex_bitmap:
            message_length = len(message)-36
            message_type_indicator, bitmap, message_data = struct.unpack(
                "4s32s" + str(message_length) + "s", message)
            binary_bitmap = binascii.unhexlify(bitmap)

        else:
            message_length = len(message)-20
            message_type_indicator, binary_bitmap, message_data = struct.unpack(
                "4s16s" + str(message_length) + "s", message)
    except struct.error as ex:
        raise Iso8583DataError('Failed unpacking bitmap values', binary_context_data=message, original_exception=ex)
    return_values = dict()

    # add the message type
    try:
        return_values["MTI"] = message_type_indicator.decode(encoding)
    except UnicodeError as ex:
        raise Iso8583DataError('Failed decoding MTI field', binary_context_data=message, original_exception=ex)

    message_pointer = 0
    bitmap_list = _get_bitmap_list(binary_bitmap)

    for bit in range(2, 128):
        if bitmap_list[bit]:
            LOGGER.debug("processing bit %s", bit)
            return_message, message_increment = _iso8583_to_field(
                bit,
                bit_config[str(bit)],
                message_data[message_pointer:],
                encoding)

            # Increment the message pointer and process next field
            message_pointer += message_increment
            return_values.update(return_message)

    # check that all of message has been consumed, otherwise raise exception
    if message_pointer != len(message_data):
        raise Iso8583DataError(
            f'Message data not correct length. '
            f'Bitmap indicates len={message_pointer}, message is len={len(message_data)}',
            binary_context_data=message
        )

    return return_values


def _dict_to_iso8583(message, bit_config, encoding=DEFAULT_ENCODING, hex_bitmap=False):
    """
    Convert dictionary to ISO8583 message

    :param message: dictionary of message elements
    * key = 'MTI' message type indicator
    * key = 'DE(1-127)' data elements
    * key = 'PDSxxxx' private data fields
    * key = 'TAGxxxx' icc fields
    :param bit_config: dictionary of bit mapping configuration
    :param encoding: string indicating encoding of data
    :return: The message in ISO8583 based format
    * Message Type indicator - 4 bytes
    * Binary bitmap - 16 bytes (Reads DE1)
    * Message data - Remainder of record

    """
    output_data = b''
    bitmap_values = [False] * 128
    bitmap_values[0] = True  # set bit 1 on for presence of bitmap

    # get the pds fields from config
    de_pds_fields = sorted(
        [int(key) for key in bit_config if bit_config[key].get('field_processor') == 'PDS'], reverse=True)
    LOGGER.debug(de_pds_fields)

    for de_field_value in _pds_to_de(message):
        de_field_key = de_pds_fields.pop()
        LOGGER.debug(f'de{de_field_key}={de_field_value}')
        message[f'DE{de_field_key}'] = de_field_value

    for bit in range(2, 128):
        if message.get('DE' + str(bit)) or message.get('DE' + str(bit)) == 0:  # 0 evals to false, allow zero values
            LOGGER.debug(f'processing bit {bit}')
            bitmap_values[bit - 1] = True
            LOGGER.debug(message.get('DE' + str(bit)))
            output_data += _field_to_iso8583(
                bit_config[str(bit)],
                message.get('DE' + str(bit)),
                encoding=encoding)

    bitarray = BitArray()
    bitarray.fromlist(bitmap_values)
    binary_bitmap = bitarray.tobytes()
    if hex_bitmap:
        bitmap = binascii.hexlify(binary_bitmap)
    else:
        bitmap = binary_bitmap

    mti = message['MTI'].encode(encoding) if message.get('MTI') else b''
    output_string = mti + bitmap + output_data
    return output_string


def _field_to_iso8583(bit_config, field_value, encoding=DEFAULT_ENCODING):

    output = b''
    LOGGER.debug(f'bit_config={bit_config}, field_value={field_value}, encoding={encoding}')
    field_value = _pytype_to_string(field_value, bit_config)
    field_length = bit_config.get('field_length')
    length_size = _get_field_length(bit_config)  # size of length for llvar and lllvar fields

    if length_size > 0:
        field_length = len(field_value)
        output += format(field_length, '0' + str(length_size)).encode(encoding)

    if isinstance(field_value, bytes):
        output += field_value[:field_length]
    else:
        output += format(field_value[:field_length], '<' + str(field_length)).encode(encoding)

    return output


def _iso8583_to_field(bit, bit_config, message_data, encoding=DEFAULT_ENCODING):
    """
    Processes a message bit element

    :param bit: DE bit
    :param bit_config: message bit configuration
    :param message_data: the data to be processed
    :param encoding: byte encoding
    :returns:
        dictionary: field values
        message incrementer: position of next message
    """

    field_length = bit_config['field_length']

    length_size = _get_field_length(bit_config)

    if length_size > 0:
        field_length_string = message_data[:length_size]
        try:
            field_length_string = field_length_string.decode(encoding)
        except UnicodeDecodeError as ex:
            raise Iso8583DataError(f'Unable to decode DE{bit} field length',
                                   binary_context_data=message_data, original_exception=ex)

        try:
            field_length = int(field_length_string)
        except ValueError as ex:
            raise Iso8583DataError(f'Invalid field length DE{bit}',
                                   binary_context_data=message_data, original_exception=ex)

    field_data = message_data[length_size:length_size + field_length]
    LOGGER.debug(f'field_data={field_data}')
    field_processor = bit_config.get('field_processor')

    # do ascii conversion except for ICC field
    if field_processor != 'ICC':
        try:
            field_data = field_data.decode(encoding)
        except UnicodeDecodeError as ex:
            raise Iso8583DataError(f'Unable to decode DE{bit} field value',
                                   binary_context_data=message_data, original_exception=ex)

    # if field is PAN type, mask the card value
    if field_processor == 'PAN':
        field_data = mask(field_data)

    # if field is PAN type, mask the card value
    if field_processor == 'PAN-PREFIX':
        field_data = _pan_prefix(field_data)

    # do field conversion to native python type
    try:
        field_data = _string_to_pytype(field_data, bit_config)
    except ValueError as ex:
        raise Iso8583DataError(f'Unable to convert DE{bit} field to python type',
                               binary_context_data=message_data, original_exception=ex)
    return_values = dict()

    # add value to return dictionary
    return_values["DE" + str(bit)] = field_data

    # if a PDS field, break it down again and add to results
    if field_processor == 'PDS':
        return_values.update(_pds_to_dict(field_data))

    # if a DE43 field, break in down again and add to results
    if field_processor == 'DE43':
        processor_config = bit_config.get('field_processor_config')
        return_values.update(_get_de43_fields(field_data, processor_config))

    # if ICC field, break into tags
    if field_processor == 'ICC':
        return_values.update(_icc_to_dict(field_data))

    return return_values, field_length + length_size


def _pan_prefix(field_data):
    """
    Get prefix of PAN
    """
    return field_data[:9]


def _string_to_pytype(field_data, bit_config):
    """
    Field conversion to native python type

    :param field_data: Data to be converted
    :param bit_config: Configuration for bit
    :return: data in required type
    """
    field_python_type = bit_config.get('field_python_type')
    field_date_format = bit_config.get('field_date_format', "%y%m%d")

    if field_python_type in ("int", "long"):
        field_data = int(field_data)
    if field_python_type == "decimal":
        field_data = decimal.Decimal(field_data)
    if field_python_type == "datetime":
        field_data = datetime.datetime.strptime(field_data, field_date_format)
    return field_data


def _pytype_to_string(field_data, bit_config):
    """
    convert py type to string for message

    :param field_data: Data to be converted
    :param bit_config: Configuration for bit
    :return: data in required type
    """
    field_python_type = bit_config.get('field_python_type')
    field_date_format = bit_config.get('field_date_format', "%y%m%d")

    return_string = field_data
    if field_python_type in ('int', 'long'):
        return_string = format(int(field_data), '0' + str(bit_config.get('field_length', 0)) + 'd')
    if field_python_type == "decimal":
        return_string = format(decimal.Decimal(field_data), '0' + str(bit_config.get('field_length', 0)) + 'f')
    if field_python_type == "datetime":
        if not isinstance(field_data, datetime.datetime):
            field_data = _get_date_from_string(field_data)
        return_string = format(field_data, field_date_format)
    return return_string


def _get_date_from_string(field_data: str) -> datetime:
    """
    Parse string dates to python datetime object

    Use dateutils library if it is installed, otherwise revert to simple parser
    :param field_data: string containing date
    :return: datetime object
    """
    try:
        import dateutil.parser as parser
        LOGGER.debug('Using dateutil parser')
        return parser.parse(field_data)
    except ImportError:
        pass

    if sys.version_info >= (3, 7):
        LOGGER.debug('Using fromisoformat')
        return datetime.datetime.fromisoformat(field_data)

    # fallback parser -- tries a few different formats until one works
    LOGGER.debug('Using built in date parser')
    date_formats = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")
    output_date = None
    for date_format in date_formats:
        try:
            output_date = datetime.datetime.strptime(field_data, date_format)
            break
        except ValueError:
            continue
    if not output_date:
        raise ValueError("Unrecognised date string format - {}".format(field_data))
    return output_date


def _get_field_length(bit_config):
    """
    Determine length of iso8583 style field

    :param bit_config: dictionary of bit config data
    :return: length of field
    """
    length_size = 0

    if bit_config['field_type'] == "LLVAR":
        length_size = 2
    elif bit_config['field_type'] == "LLLVAR":
        length_size = 3

    return length_size


def _get_bitmap_list(binary_bitmap):
    """
    Get list of bits from binary bitmap

    :param binary_bitmap: the binary bitmap to be returned
    :return: the list containing bit values. Bit 0 contains original binary bitmap
    """
    working_bitmap_list = BitArray(endian='big')
    working_bitmap_list.frombytes(binary_bitmap)

    # Add bit 0 -> original binary bitmap
    bitmap_list = [binary_bitmap]

    # add bits from bitmap
    bitmap_list.extend(working_bitmap_list.tolist())

    return bitmap_list


def _pds_to_de(dict_values):
    """
    takes all the pds fields values in dict (PDSxxxx) and creates list of DE strings

    :param dict_values: dict containing "PDSxxxx" elements
    :return: list of byte strings containing pds data, or None if no fields
    """
    # get the PDS field keys in order
    LOGGER.debug(f'dict_values={dict_values}')
    keys = sorted([key for key in dict_values if key.startswith('PDS')])
    LOGGER.debug(f'keys={keys}')
    output = ''
    outputs = []
    for key in keys:
        tag = int(key[3:])
        LOGGER.debug(f'tag={tag}')
        length = len(dict_values[key])
        add_output = f'{tag:04}{length:03}{dict_values[key]}'
        if len(output + add_output) > 999:
            outputs.append(output)
            output = ''
        output += add_output
    if output:
        outputs.append(output)
    LOGGER.debug(f'>pds2de: {outputs}')

    return outputs


def _pds_to_dict(field_data):
    """
    Get MasterCard pds fields from iso field

    :param field_data: the ISO8583 field containing pds fields
    :return: dictionary of pds key values. Key in the form PDSxxxx where x is zero filled number of pds
    """
    field_pointer = 0
    return_values = {}

    while field_pointer < len(field_data):
        # get the pds tag id
        pds_field_tag = field_data[field_pointer:field_pointer+4]
        LOGGER.debug("pds_field_tag=[%s]", pds_field_tag)

        # get the pds length
        pds_field_length = int(field_data[field_pointer+4:field_pointer+7])
        LOGGER.debug("pds_field_length=[%i]", pds_field_length)

        # get the pds data
        pds_field_data = field_data[field_pointer+7:field_pointer+7+pds_field_length]
        LOGGER.debug("pds_field_data=[%s]", str(pds_field_data))
        return_values["PDS" + pds_field_tag] = pds_field_data

        # increment the fieldPointer
        field_pointer += 7+pds_field_length

    return return_values


def _icc_to_dict(field_data):
    """
    Get de55 fields from message

    :param field_data: the field containing de55
    :return: dictionary of de55 key values
             key is tag+tagid
    """
    TWO_BYTE_TAG_PREFIXES = [b'\x9f', b'\x5f']

    field_pointer = 0
    return_values = {"ICC_DATA": binascii.b2a_hex(field_data).decode()}

    while field_pointer < len(field_data):
        # get the tag id (one byte)
        field_tag = field_data[field_pointer:field_pointer+1]
        # set to 2 bytes if 2 byte tag
        if field_tag in TWO_BYTE_TAG_PREFIXES:
            field_tag = field_data[field_pointer:field_pointer+2]
            field_pointer += 2
        else:
            field_pointer += 1

        field_tag_display = binascii.b2a_hex(field_tag)
        LOGGER.debug("field_tag_display=%s", field_tag_display)

        # stop processing de55 if low values tag found
        if field_tag_display == b'00':
            break

        field_length_raw = field_data[field_pointer:field_pointer+1]
        field_length = struct.unpack(">B", field_length_raw)[0]

        LOGGER.debug("%s", format(field_tag_display))
        LOGGER.debug(field_length)

        # get the tag data
        de_field_data = field_data[field_pointer+1:field_pointer+field_length+1]
        de_field_data_display = binascii.b2a_hex(de_field_data).decode()
        LOGGER.debug("%s", de_field_data_display)
        return_values["TAG" + field_tag_display.upper().decode()] = de_field_data_display

        # increment the fieldPointer
        field_pointer += 1+field_length

    return return_values


def _get_de43_fields(de43_field, processor_config=None):
    """
    get pds 43 field breakdown

    :param de43_field: data of pds 43
    :return: dictionary of pds 43 sub elements
    """
    LOGGER.debug("de43_field=%s", de43_field)

    # No field config provided, just exit
    if not processor_config:
        return dict()

    # perform regex field matching
    de43_regex = processor_config
    field_match = re.match(de43_regex, de43_field)
    if not field_match:
        return dict()

    # get the dict
    field_dict = field_match.groupdict()
    if field_dict.get('DE43_POSTCODE'):
        field_dict['DE43_POSTCODE'] = field_dict['DE43_POSTCODE'].rstrip()
    return field_dict


if __name__ == '__main__':
    import doctest
    doctest.testmod()
