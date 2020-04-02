"""
.. note:: This module requires the install of additional modules. Use ``pip install cardutil[pin]``.

Class for working with pinblocks including encryption and pin verification value generation.
Pinblock format is ISO 9564-1 format 0, ANSI X9.8, Visa-1 and ECI-0

Structure of pin block::

    P1 = 0LPPPPFFFFFFFFFF
    P2 = 0000CCCCCCCCCCCC
    PIN Block = P1 XOR P2

where::

    * L = Length of pin
    * P = Pin
    * F = Fill, x'F'
    * C = Last 12 digits of card number (excluding check digit)


How to use::

    # create the pinblock object
    >>> pb = PinBlock(pin='1234', card_number='1111222233334444')
    >>> hexlify(pb.to_bytes())
    b'041226dddccccbbb'

    # output encrypted pinblock bytes
    >>> hexlify(pb.to_enc_bytes(key='00' * 16))
    b'4c0906d10308871a'

    # calculate Visa PVV value::
    >>> pb.to_pvv(pvv_key='00' * 16)
    '6264'

    # load from pinblock
    >>> pb2 = PinBlock.from_bytes(pin_block=pb.to_bytes(), card_number='1111222233334444')
    >>> pb2.pin
    '1234'

    # load from encrypted pinblock
    >>> pb3 = PinBlock.from_enc_bytes(
    ...         enc_pin_block=pb.to_enc_bytes('00' * 16),
    ...         card_number='1111222233334444',
    ...         key='00' * 16)
    >>> pb3.pin
    '1234'
"""
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from binascii import hexlify, unhexlify

backend = default_backend()


class PinBlock(object):
    def __init__(self, pin: str, card_number: str):
        """
        Create a pinblock object given a pin and card number

        :param pin: string containing pin
        :param card_number: string containing card number
        """
        self._pin = pin
        self._card_number = card_number

    @classmethod
    def from_bytes(cls, pin_block: bytes, card_number: str):
        """
        Create pinblock object using pinblock and card number

        :param pin_block: bytes containing pin block
        :param card_number: string containing card number
        :return: PinBlock object
        """
        pin = pin_block_0_to_pin(pin_block, card_number)
        return cls(pin, card_number)

    @classmethod
    def from_enc_bytes(cls, enc_pin_block: bytes, card_number: str, key: str):
        """
        Create pinblock object using encrypted pinblock and card number

        :param enc_pin_block: bytes containing encrypted pin block
        :param card_number: string containing card number
        :param key: hex string containing pin protection key (PPK)
        :return: PinBlock object
        """
        pin_block = _decrypt(key, enc_pin_block)
        return cls.from_bytes(pin_block, card_number)

    @property
    def pin(self) -> str:
        """
        The card pin as a string
        """
        return self._pin

    @property
    def card_number(self) -> str:
        """
        The card number as a string
        """
        return self._card_number

    def to_bytes(self) -> bytes:
        """
        Get the pinblock bytes

        :return: bytes containing pinblock
        """
        return pin_block_0(self._pin, self._card_number)

    def to_enc_bytes(self, key: str) -> bytes:
        """
        Get the encrypted pinblock bytes

        :return: bytes containing encrypted pinblock
        """
        return _encrypt(key, self.to_bytes())

    def to_pvv(self, pvv_key: str, pvv_index: int = 1) -> str:
        """
        get the pin verification value (PVV) for the pinblock

        :param pvv_key: the PVV key as a hex string
        :param pvv_index: the PVV index
        :return: string containing PVV
        """
        binary_key = unhexlify(pvv_key)
        t = calculate_tsp(self.pin, self.card_number, key_table_index=pvv_index)
        return calculate_visa_pvv(t, binary_key)


def calculate_tsp(pin: str, card_number: str, key_table_index: int = 1) -> str:
    """
    Create the transformed security parameter (TSP) required for PVV calculations

    From IBM:

        For VISA PVV algorithms, the leftmost 11 digits of the TSP are the personal account number (PAN),
        the leftmost 12th digit is a key table index to select the PVV generation key, and the rightmost
        4 digits are the PIN. The key table index should have a value between 1 and 6, inclusive.

    :param pin: card pin number
    :param card_number: the card number
    :param key_table_index: Index to pvv key to use
    :return: TSP value as hex string
    """
    rightmost_11 = card_number[-12:-1]
    return f'{rightmost_11}{key_table_index}{pin}'


def calculate_visa_pvv(tsp: str, pvv_key: bytes) -> str:
    """
    The algorithm generates a 4-digit PIN verification value (PVV).

    See `IBM documentation
    <https://www.ibm.com/support/knowledgecenter/en/linuxonibm/com.ibm.linux.z.wskc.doc/wskc_c_appdpvvgenalg.html>`_

    :param tsp: tsp as hex string. See :py:mod:`cardutil.pin.tsp`
    :param pvv_key: the pvv key
    :return: pvv value
    """
    cipher = Cipher(algorithms.TripleDES(pvv_key), modes.ECB(), backend=backend)
    encryptor = cipher.encryptor()
    ct = encryptor.update(unhexlify(tsp)) + encryptor.finalize()
    values_pass1 = [value for value in hexlify(ct).decode() if value.isdigit()]
    if len(values_pass1) < 4:
        values_pass2 = [str(int(value, 16) - 10) for value in hexlify(ct).decode() if value.isalpha()]
        values_pass1 += values_pass2
    return ''.join(values_pass1[0:4])


def pin_block_0(pin: str, card_number: str) -> bytes:
    """
    Pin block in ISO format 0::

        P1 = LLPPPPFFFFFFFFFF
        P2 = 0000CCCCCCCCCCCC
        PIN Block = P1 XOR P2

    where:

        * L = Length of pin
        * P = Pin
        * F = Fill, x'F'
        * C = Last 12 digits of card number (excluding check digit)

    :param pin: pin as string
    :param card_number: card number as string
    :return: pin block as bytes
    """
    rightmost_12 = card_number[-13:-1]
    p1 = f'{"0" + str(len(pin)) + pin:f<16}'
    p2 = f'0000{rightmost_12}'
    pin_block = int(p1, 16) ^ int(p2, 16)
    return pin_block.to_bytes(8, byteorder='big')


def pin_block_0_to_pin(pin_block: bytes, card_number) -> str:
    """
    Get the pin from a pin block format 0

    :param pin_block: the pin block in format 0
    :param card_number: the card number
    :return: the pin
    """

    rightmost_12 = card_number[-13:-1]
    p2 = f'0000{rightmost_12}'
    p1_bytes = int.from_bytes(pin_block, byteorder='big') ^ int(p2, 16)
    p1 = f'{p1_bytes:016x}'
    pin_length = int(p1[0:2])
    pin = p1[2:2+pin_length]
    return pin


def _encrypt(key: str, data: bytes) -> bytes:
    binary_key = unhexlify(key)
    cipher = Cipher(algorithms.TripleDES(binary_key), modes.ECB(), backend=backend)
    encryptor = cipher.encryptor()
    return encryptor.update(data) + encryptor.finalize()


def _decrypt(key: str, cipher_data: bytes) -> bytes:
    binary_key = unhexlify(key)
    cipher = Cipher(algorithms.TripleDES(binary_key), modes.ECB(), backend=backend)
    decryptor = cipher.decryptor()
    return decryptor.update(cipher_data) + decryptor.finalize()


if __name__ == '__main__':
    import doctest
    doctest.testmod()
