import binascii
from array import array


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
