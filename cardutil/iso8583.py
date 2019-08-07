import array
import binascii
import datetime
import decimal
import logging
import re
import struct
from array import array

from cardutil.config import config
from cardutil.hexdump import hexdump

LOGGER = logging.getLogger(__name__)


def dumps(obj, encoding='latin-1', iso_config=None):
    """
    takes dict, returns iso8583 message in provided
    :param obj: dict containing message data
    :param encoding: the encoding to be applied
    :param iso_config:
    :return: bytes containing message
    """
    if not iso_config:
        iso_config = config['bit_config']

    output = dict_to_iso8583(obj, iso_config, encoding)
    return output


def loads(b, encoding='latin-1', iso_config=None):
    """
    take an iso8583 message, returns dict
    :param b: bytes containing message
    :param encoding:
    :param iso_config:
    :return: dict containing message data
    """
    if not iso_config:
        iso_config = config['bit_config']

    return iso8583_to_dict(b, iso_config, encoding)


class BitArray:
    """
    This is a minimal native python replacement for the bitarray module that was used to interpret
    the file bitmap. The bitarray module is written in c and does not provide binary wheels so
    forces users to have compilers installed just to install.
    This small class provides the required functions from that library.
    """
    endian = 'big'
    bytes = b''

    def __init__(self, endian='big'):
        self.endian = endian

    def frombytes(self, array_bytes):
        self.bytes = array_bytes

    def tobytes(self):
        return self.bytes

    def tolist(self):
        swap_bytes = array('B', self.bytes)
        if self.endian == 'little':
            for i, n in enumerate(swap_bytes):
                swap_bytes[i] = int('{:08b}'.format(n)[::-1], 2)
        width = len(self.bytes)*8
        try:
            swapped_bytes = swap_bytes.tobytes()
        except AttributeError:  # 2.7 does not recognise .tobytes method. 2.6 does!
            swapped_bytes = swap_bytes.tostring()
        bit_list = '{bytes:0{width}b}'.format(bytes=int(binascii.hexlify(swapped_bytes), 16), width=width)
        return [bit == '1' for bit in bit_list]

    def fromlist(self, bytelist):
        # https://stackoverflow.com/questions/32675679/convert-binary-string-to-bytearray-in-python-3
        binary_value = ''.join(['1' if val else '0' for val in bytelist])
        self.bytes = self.bitstring_to_bytes(binary_value)
        # Python 3 only..
        # self.bytes = int(binary_value, 2).to_bytes(len(binary_value) // 8, byteorder='big')

    @staticmethod
    def bitstring_to_bytes(s):
        v = int(s, 2)
        b = bytearray()
        while v:
            b.append(v & 0xff)
            v >>= 8
        return bytes(b[::-1])


def iso8583_to_dict(message, bit_config, encoding='latin-1'):
    """
    Convert ISO8583 style message to dictionary

    :param message: The message in ISO8583 based format

    * Message Type indicator - 4 bytes
    * Binary bitmap - 16 bytes (Reads DE1 and DE2)
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
    message_length = len(message)-20
    (message_type_indicator, binary_bitmap, message_data) = struct.unpack("4s16s" + str(message_length) + "s", message)

    return_values = dict()

    # add the message type
    return_values["MTI"] = message_type_indicator.decode(encoding)

    message_pointer = 0
    bitmap_list = get_bitmap_list(binary_bitmap)

    for bit in range(2, 128):
        if bitmap_list[bit]:
            LOGGER.debug("processing bit %s", bit)
            return_message, message_increment = iso8583_to_field(
                bit,
                bit_config[str(bit)],
                message_data[message_pointer:],
                encoding)

            # Increment the message pointer and process next field
            message_pointer += message_increment
            return_values.update(return_message)

    # check that all of message has been consumed, otherwise raise exception
    if message_pointer != len(message_data):
        raise Exception(
            "Message data not correct length. Bitmap indicates len={0}, message is len={1}\n{2}".format(
                message_pointer,
                len(message_data),
                hexdump(message_data, result="return")
            )
        )

    return return_values


def dict_to_iso8583(message, bit_config, encoding='latin-1'):
    """
    Convert dictionary to ISO8583 message

    :param message: dictionary of message elements
    * key = 'MTI' message type indicator
    * key = 'DEx' data elements
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

    # get the pds fields
    de_pds_fields = [key for key in bit_config if bit_config[key].get('field_processor') == 'PDS']
    print(de_pds_fields)
    for de_field in pds_to_de(message):
        message[f'DE{de_pds_fields.pop()}'] = de_field

    for bit in range(2, 128):
        if message.get('DE' + str(bit)):
            LOGGER.debug(f'processing bit {bit}')
            bitmap_values[bit - 1] = True
            LOGGER.debug(message.get('DE' + str(bit)))
            output_data += field_to_iso8583(
                bit_config[str(bit)],
                message.get('DE' + str(bit))
            )

    bitarray = BitArray()
    bitarray.fromlist(bitmap_values)
    binary_bitmap = bitarray.tobytes()

    mti = message['MTI'].encode(encoding) if message.get('MTI') else b''
    output_string = mti + binary_bitmap + output_data
    return output_string


def field_to_iso8583(bit_config, field_value, encoding='latin-1'):

    output = b''
    field_value = pytype_to_string(field_value, bit_config)
    field_length = bit_config['field_length']
    length_size = get_field_length(bit_config)
    if length_size > 0:
        field_length = len(field_value)
        output += format(field_length, '0' + str(length_size)).encode(encoding)
    output += format(field_value[:field_length], '<' + str(field_length)).encode(encoding)
    return output


def iso8583_to_field(bit, bit_config, message_data, encoding='latin-1'):
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

    length_size = get_field_length(bit_config)

    if length_size > 0:
        field_length_string = message_data[:length_size]
        field_length_string = field_length_string.decode(encoding)
        field_length = int(field_length_string)

    field_data = message_data[length_size:length_size + field_length]  # .decode(encoding)
    LOGGER.debug(f'field_data={field_data}')
    field_processor = get_parameter(bit_config, 'field_processor')

    # do ascii conversion except for ICC field
    if field_processor != 'ICC':
        # if source_format == 'ebcdic':
        #     field_data = codecs.decode(field_data, "cp500")  # convert_text_eb2asc(field_data)
        field_data = field_data.decode(encoding)

    # if field is PAN type, mask the card value
    if field_processor == 'PAN':
        field_data = mask_pan(field_data)

    # if field is PAN type, mask the card value
    if field_processor == 'PAN-PREFIX':
        field_data = mask_pan(field_data, prefix_only=True)

    # do field conversion to native python type
    field_data = convert_to_type(field_data, bit_config)

    return_values = dict()

    # add value to return dictionary
    return_values["DE" + str(bit)] = field_data

    # if a PDS field, break it down again and add to results
    if field_processor == 'PDS':
        return_values.update(pds_to_dict(field_data))

    # if a DE43 field, break in down again and add to results
    if field_processor == 'DE43':
        return_values.update(get_de43_fields(field_data))

    # if ICC field, break into tags
    if field_processor == 'ICC':
        return_values.update(icc_to_dict(field_data))

    return return_values, field_length + length_size


def get_parameter(config, parameter):
    """
    Checks for parameter value and sets if present

    :param config: bit configuration list
    :param parameter: the configuration item to set
    :return: string with value of parameter
    """
    return config[parameter] if config.get(parameter) else ""


def mask_pan(field_data, prefix_only=False):
    """
    Mask a pan number string

    :param field_data: unmasked pan
    :return: masked pan
    """
    # if field is PAN type, mask the card value
    if prefix_only:
        return field_data[:9]
    else:
        return field_data[:6] + ("*" * (len(field_data)-9)) + field_data[len(field_data)-3:len(field_data)]


def convert_to_type(field_data, bit_config):
    """
    Field conversion to native python type

    :param field_data: Data to be converted
    :param bit_config: Configuration for bit
    :return: data in required type
    """
    field_python_type = get_parameter(bit_config, 'python_field_type')

    if field_python_type == "int":
        field_data = int(field_data)
    if field_python_type == "decimal":
        field_data = decimal.Decimal(field_data)
    if field_python_type == "long":
        field_data = int(field_data)
    if field_python_type == "datetime":
        field_data = datetime.datetime.strptime(
            field_data, "%y%m%d%H%M%S")
    return field_data


def pytype_to_string(field_data, bit_config):
    """
    convert py type to string for message

    :param field_data: Data to be converted
    :param bit_config: Configuration for bit
    :return: data in required type
    """
    field_python_type = get_parameter(bit_config, 'python_field_type')

    return_string = field_data
    if field_python_type == "int":
        return_string = format(field_data, '0' + str(get_parameter(bit_config, 'field_length')))
    if field_python_type == "decimal":
        return_string = format(field_data, '0' + str(get_parameter(bit_config, 'field_length')))
    if field_python_type == "long":
        return_string = format(field_data, '0' + str(get_parameter(bit_config, 'field_length')))
    if field_python_type == "datetime":
        return_string = format(field_data, "%y%m%d%H%M%S")
    return return_string


def get_field_length(bit_config):
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


def get_bitmap_list(binary_bitmap):
    """
    Get list of bits from binary bitmap

    :param binary_bitmap: the binary bitmap to be returned
    :return: the list containing bit values. Bit 0 contains original binary
             bitmap
    """
    working_bitmap_list = BitArray(endian='big')
    working_bitmap_list.frombytes(binary_bitmap)

    # Add bit 0 -> original binary bitmap
    bitmap_list = [binary_bitmap]

    # add bits from bitmap
    bitmap_list.extend(working_bitmap_list.tolist())

    return bitmap_list


def pds_to_de(dict_values):
    """
    takes all the pds fields in dict and builds up pds DE values (usually 48)
    :param dict_values: dict containing "PDSxxxx" elements
    :return: bytes containing pds data
    """
    # get the PDS field keys in order
    keys = sorted([key for key in dict_values if key.startswith('PDS')])
    output = ''
    outputs = []
    for key in keys:
        tag = int(key[3:])
        length = len(dict_values[key])
        add_output = f'{tag:04}{length:03}{dict_values[key]}'
        if len(output + add_output) > 999:
            outputs.append(output)
            output = ''
        output += add_output
    outputs.append(output)
    return outputs


def pds_to_dict(field_data):
    """
    Get MasterCard pds fields from iso field

    :param field_data: the field containing pds fields
    :return: dictionary of pds key values
             key in the form PDSxxxx where x is zero filled number of pds
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


def icc_to_dict(field_data):
    """
    Get de55 fields from message

    :param field_data: the field containing de55
    :return: dictionary of de55 key values
             key is tag+tagid
    """
    TWO_BYTE_TAG_PREFIXES = [b'\x9f', b'\x5f']

    field_pointer = 0
    return_values = {"ICC_DATA": binascii.b2a_hex(field_data)}

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

        field_length_raw = field_data[field_pointer:field_pointer+1]
        field_length = struct.unpack(">B", field_length_raw)[0]

        LOGGER.debug("%s", format(field_tag_display))
        LOGGER.debug(field_length)

        # get the pds data
        de_field_data = field_data[field_pointer+1:field_pointer+field_length+1]
        de_field_data_display = binascii.b2a_hex(de_field_data)
        LOGGER.debug("%s", de_field_data_display)
        return_values["TAG" + field_tag_display.upper().decode()] = de_field_data_display

        # increment the fieldPointer
        field_pointer += 1+field_length

    return return_values


def get_de43_fields(de43_field):
    """
    get pds 43 field breakdown
    :param de43_field: data of pds 43
    :return: dictionary of pds 43 sub elements
    """
    LOGGER.debug("de43_field=%s", de43_field)
    de43_regex = (
        r"(?P<DE43_NAME>.+?) *\\(?P<DE43_ADDRESS>.+?) *\\(?P<DE43_SUBURB>.+?) *\\"
        r"(?P<DE43_POSTCODE>\S{4,10}) *(?P<DE43_STATE>.{3})(?P<DE43_COUNTRY>.{3})"
    )

    field_match = re.match(de43_regex, de43_field)
    if not field_match:
        return dict()

    # get the dict
    field_dict = field_match.groupdict()

    return field_dict
