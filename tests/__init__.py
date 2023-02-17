import binascii


def print_stream(stream, description):
    stream.seek(0)
    data = stream.read()
    print('***' + description + '***')
    print(data)
    stream.seek(0)


def test_message(encoding='ascii', hex_bitmap=False):
    binary_bitmap = b'\xF0\x10\x05\x42\x84\x61\x80\x02\x02\x00\x00\x04\x00\x00\x00\x00'
    bitmap = binary_bitmap
    if hex_bitmap:
        bitmap = binascii.hexlify(binary_bitmap)
    return (
        '1144'.encode(encoding) +
        bitmap +
        ('164444555544445555111111000000009999150815171500123456789012333123423579957991200000'
         '012306120612345612345657994211111111149BIG BOBS\\80 KERNDALE ST\\DANERLEY\\3103      '
         'VICAUS0080001001Y99901600000000000000011234567806999999').encode(encoding))


message_ascii_raw = test_message()
message_ebcdic_raw = test_message('cp500')
message_ascii_raw_hex = test_message(hex_bitmap=True)
message_ebcdic_raw_hex = test_message('cp500', hex_bitmap=True)
