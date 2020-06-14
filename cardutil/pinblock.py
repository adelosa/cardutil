"""
Pinblock
--------

There are many different pin block formats in use in the payment card industry.
The pinblock module provides functions for working with the various pin blocks formats in a consistent way.

Available pin block formats:

* :py:mod:`cardutil.pinblock.Iso0PinBlock`
* :py:mod:`cardutil.pinblock.Iso4PinBlock`

How to use::

    # create the pinblock instance. Inputs will vary depending on the format
    >>> pb = Iso0PinBlock(pin='1234', card_number='1111222233334444')
    >>> pb.pin
    '1234'

    # output pinblock bytes
    >>> binascii.hexlify(pb.to_bytes())
    b'041226dddccccbbb'

    # create pinblock instance from bytes
    >>> pb2 = Iso0PinBlock.from_bytes(pb.to_bytes(), card_number='1111222233334444')
    >>> pb2.pin
    '1234'


Pinblock mix-ins
----------------

Common operations associated with pin blocks include encryption and calculation of a pin verification value.

This module allows you to add pinblock encryption and pin verification calculators to a pinblock class through
the use of mixins.

Creating pinblock objects
^^^^^^^^^^^^^^^^^^^^^^^^^

How to create pinblock class with encryption and pin verification support::

    # use a predefined pinblock object
    >>> Pinblock = Iso0TDESPinBlockWithVisaPVV

    # or create your own class including required mix-ins
    >>> class PinBlock(Iso0PinBlock, TdesEncryptedPinBlockMixin, VisaPVVPinBlockMixin):
    ...    pass

    # or use the type builtin to create the class
    >>> PinBlock = type('MyPinBlock', (Iso0PinBlock, TdesEncryptedPinBlockMixin, VisaPVVPinBlockMixin), {})

    # create the pinblock instance. Inputs will vary depending on the format
    >>> pb = PinBlock(pin='1234', card_number='1111222233334444')
    >>> pb.pin
    '1234'

Pinblock encryption
^^^^^^^^^^^^^^^^^^^

The encryption mixin's adds pin block encrption and decryption. Adds **from_enc_bytes** constructor and
**to_enc_bytes** method.

.. note:: The use of an encryption mix-in requires the install of additional modules.
          Use ``pip install cardutil[crypto]``.

Available pinblock encryption mix-ins:

* :py:mod:`cardutil.pinblock.TdesEncryptedPinBlockMixin`
* :py:mod:`cardutil.pinblock.AesEncryptedPinBlockMixin`

How to encrypt and decrypt a pinblock::

    # output encrypted pinblock bytes
    >>> epb = pb.to_enc_bytes(key='00' * 16)
    >>> binascii.hexlify(epb)
    b'4c0906d10308871a'

    # create new pinblock from encrypted pinblock bytes
    >>> pb2 = PinBlock.from_enc_bytes(
    ...       enc_pin_block=epb,
    ...       card_number='1111222233334444',
    ...       key='00' * 16)
    >>> pb2.pin
    '1234'

Pin verification values
^^^^^^^^^^^^^^^^^^^^^^^

The pin verification mixin's add pin verification value calculators to the pinblock object. Adds **to_pvv** method.

.. note:: The use of a pin verification mix-in requires the install of additional modules.
          Use ``pip install cardutil[crypto]``.

Available pin verification mix-ins:

* :py:mod:`cardutil.pinblock.VisaPVVPinBlockMixin`

How to generate pin verification value::

    >>> pb.to_pvv(pvv_key='00' * 16)
    '6264'

"""

import abc
import binascii
import secrets
import logging

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

backend = default_backend()
LOGGER = logging.getLogger(__name__)


class AbstractPinBlock(abc.ABC):
    """
    Base PinBlock object class from which implementation will subclass
    """

    def __init__(self, pin: str, *args: any, **kwargs: any):
        """
        Create a pinblock

        :param pin: string containing pin
        """
        self._pin = pin

    @property
    def pin(self) -> str:
        """
        The card pin as a string
        """
        return self._pin

    @classmethod
    @abc.abstractmethod
    def from_bytes(cls, pin_block: bytes, *args: any, **kwargs: any):
        """
        Create pinblock object from pinblock bytes

        :param pin_block: bytes containing pin block
        :return: PinBlock object
        """
        pass

    @abc.abstractmethod
    def to_bytes(self) -> bytes:
        """
        Get the pinblock bytes

        :return: bytes containing pinblock
        """
        pass


class Iso0PinBlock(AbstractPinBlock):
    """
    ISO 9564-1 format 0, ANSI X9.8, Visa-1 and ECI-0

    Pin block structure::

        P1 = LLPPPPFFFFFFFFFF
        P2 = 0000CCCCCCCCCCCC
        PIN Block = P1 XOR P2

    where::

        * L = Length of pin
        * P = Pin
        * F = Fill, x'F'
        * C = Last 12 digits of card number (excluding check digit)
    """
    def __init__(self, pin: str, card_number: str = None, **kwargs: any):
        super().__init__(pin, **kwargs)
        self.card_number = card_number

    @classmethod
    def from_bytes(cls, pin_block: bytes, card_number: str = None, *args: any, **kwargs: any):
        """
        Create object from pin block bytes

        :param pin_block: the pin block bytes
        :param card_number: the card number
        :return: the pin
        """
        rightmost_12 = card_number[-13:-1]
        p2 = f'0000{rightmost_12}'
        p1_bytes = int.from_bytes(pin_block, byteorder='big') ^ int(p2, 16)
        p1 = f'{p1_bytes:016x}'
        pin_length = int(p1[1:2])
        pin = p1[2:2 + pin_length]
        return cls(pin, card_number=card_number)

    def to_bytes(self) -> bytes:
        """
        Get the pin block bytes

        :return: pin block as bytes
        """
        rightmost_12 = self.card_number[-13:-1]
        p1 = f'{"0" + str(len(self.pin)) + self.pin:f<16}'
        p2 = f'0000{rightmost_12}'
        pin_block = int(p1, 16) ^ int(p2, 16)
        return pin_block.to_bytes(8, byteorder='big')


class Iso4PinBlock(AbstractPinBlock):
    """
    ISO 9564-1 Format 4 pin block

    https://www.ibm.com/support/knowledgecenter/SSLTBW_2.4.0/com.ibm.zos.v2r4.csfb400/iso4_sum.htm

    This block is 16 bytes long.

    Pinblock structure::

        CLPPPPaaaaaaaaAARRRRRRRRRRRRRRRR
        441234aaaaaaaaaa837c658036105d19

    where::

        * C = type of pinblock, x'4'
        * L = Length of pin, x'4' to x'C'
        * P = Pin
        * a = additional Pin or x'A'
        * A = Fill, x'A'
        * R = Random values, x'0' to x'F'
    """
    def __init__(self, pin: str, random_value: int = None, **kwargs: any):
        super().__init__(pin, **kwargs)
        if random_value:
            self.random_value = random_value
        else:
            self.random_value = secrets.randbits(64)
            LOGGER.debug(f'random_value={self.random_value}')

    def to_bytes(self) -> bytes:
        p1 = binascii.unhexlify(f'{"4" + str(len(self.pin)) + self.pin:a<16}{self.random_value:016x}')
        return p1

    @classmethod
    def from_bytes(cls, pin_block: bytes, *args: any, **kwargs: any) -> AbstractPinBlock:
        p1 = binascii.hexlify(pin_block)
        pin_length = int(p1[1:2])
        pin = p1[2:2+pin_length]
        return cls(pin.decode())


class TdesEncryptedPinBlockMixin(abc.ABC):
    """
    Adds 3DES encryption to pin blocks
    """
    @classmethod
    @abc.abstractmethod
    def from_bytes(cls, *args, **kwargs):
        pass

    @abc.abstractmethod
    def to_bytes(self, *args, **kwargs):
        pass

    @classmethod
    def from_enc_bytes(cls, enc_pin_block: bytes, key: str, *args: any, **kwargs: any):
        """
        Create pinblock object using encrypted pinblock and card number

        :param enc_pin_block: bytes containing encrypted pin block
        :param card_number: string containing card number
        :param key: hex string containing pin protection key (PPK)
        :return: PinBlock object
        """
        pin_block = cls.decrypt(key, enc_pin_block)
        return cls.from_bytes(pin_block, *args, **kwargs)

    def to_enc_bytes(self, key: str) -> bytes:
        """
        Get the encrypted pinblock bytes

        :return: bytes containing encrypted pinblock
        """
        return self.encrypt(key, self.to_bytes())

    @staticmethod
    def encrypt(key: str, data: bytes) -> bytes:
        binary_key = binascii.unhexlify(key)
        cipher = Cipher(algorithms.TripleDES(binary_key), modes.ECB(), backend=backend)
        encryptor = cipher.encryptor()
        return encryptor.update(data) + encryptor.finalize()

    @staticmethod
    def decrypt(key: str, cipher_data: bytes) -> bytes:
        binary_key = binascii.unhexlify(key)
        cipher = Cipher(algorithms.TripleDES(binary_key), modes.ECB(), backend=backend)
        decryptor = cipher.decryptor()
        return decryptor.update(cipher_data) + decryptor.finalize()


class AESEncryptedPinBlockMixin(abc.ABC):
    """
    Adds AES encryption to pin blocks
    """
    @classmethod
    @abc.abstractmethod
    def from_bytes(cls, *args, **kwargs):
        pass

    @abc.abstractmethod
    def to_bytes(self, *args, **kwargs):
        pass

    @classmethod
    def from_enc_bytes(cls, enc_pin_block: bytes, key: str, *args: any, **kwargs: any):
        """
        Create pinblock object using encrypted pinblock and card number

        :param enc_pin_block: bytes containing encrypted pin block
        :param key: hex string containing pin protection key (PPK)
        :return: PinBlock object
        """
        pin_block = cls.decrypt(key, enc_pin_block)
        return cls.from_bytes(pin_block, *args, **kwargs)

    def to_enc_bytes(self, key: str) -> bytes:
        """
        Get the encrypted pinblock bytes

        :return: bytes containing encrypted pinblock
        """
        return self.encrypt(key, self.to_bytes())

    @staticmethod
    def encrypt(key: str, data: bytes) -> bytes:
        binary_key = binascii.unhexlify(key)
        cipher = Cipher(algorithms.AES(binary_key), modes.ECB(), backend=backend)
        encryptor = cipher.encryptor()
        return encryptor.update(data) + encryptor.finalize()

    @staticmethod
    def decrypt(key: str, cipher_data: bytes) -> bytes:
        binary_key = binascii.unhexlify(key)
        cipher = Cipher(algorithms.AES(binary_key), modes.ECB(), backend=backend)
        decryptor = cipher.decryptor()
        return decryptor.update(cipher_data) + decryptor.finalize()


class VisaPVVPinBlockMixin(abc.ABC):
    """
    Adds Visa PVV calculator to pin blocks
    """
    @property
    @abc.abstractmethod
    def pin(self) -> str:
        pass

    def to_pvv(self, pvv_key, key_index=1, card_number=None):
        """
        The algorithm generates a 4-digit PIN verification value (PVV).

        :param pvv_key: the pvv key
        :param key_index: the visa key index
        :param card_number: the card number
        :return: pvv value
        """
        if hasattr(self, 'card_number'):
            card_number = self.card_number
        if not card_number:
            raise ValueError('card_number parameter must be passed')
        return calculate_pvv(self.pin, pvv_key, key_index, card_number)


def _get_tsp(card_number, key_table_index, pin):
    rightmost_11 = card_number[-12:-1]
    return f'{rightmost_11}{key_table_index}{pin}'


def calculate_pvv(pin: str, pvv_key: str, key_index: int, card_number: str):
    """
    The algorithm generates a 4-digit PIN verification value (PVV).

    See `IBM documentation
    <https://www.ibm.com/support/knowledgecenter/en/linuxonibm/com.ibm.linux.z.wskc.doc/wskc_c_appdpvvgenalg.html>`_

    :param pin: the pin to calculate PVV for
    :param pvv_key: the pvv key as a hex formatted string
    :param key_index: the visa key index
    :param card_number: the card number
    :return: pvv value
    """
    tsp = _get_tsp(card_number, key_index, pin)
    bin_pvv_key = binascii.unhexlify(pvv_key)
    cipher = Cipher(algorithms.TripleDES(bin_pvv_key), modes.ECB(), backend=backend)
    encryptor = cipher.encryptor()
    ct = encryptor.update(binascii.unhexlify(tsp)) + encryptor.finalize()
    values_pass1 = [value for value in binascii.hexlify(ct).decode() if value.isdigit()]
    if len(values_pass1) < 4:
        values_pass2 = [str(int(value, 16) - 10) for value in binascii.hexlify(ct).decode() if value.isalpha()]
        values_pass1 += values_pass2
    return ''.join(values_pass1[0:4])


class Iso0TDESPinBlockWithVisaPVV(Iso0PinBlock, TdesEncryptedPinBlockMixin, VisaPVVPinBlockMixin):
    pass


class Iso4AESPinBlockWithVisaPVV(Iso4PinBlock, AESEncryptedPinBlockMixin, VisaPVVPinBlockMixin):
    pass


if __name__ == '__main__':
    import doctest
    doctest.testmod()
