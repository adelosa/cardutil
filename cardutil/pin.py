"""
.. note:: This module requires the install of additional modules. Use ``pip install cardutil[pin]``.
"""
from binascii import hexlify, unhexlify

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


def tsp(pin: str, card_number: str, key_table_index: int = 1) -> str:
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


def visa_pvv(tsp: str, pvv_key: bytes) -> str:
    """
    See https://www.ibm.com/support/knowledgecenter/en/linuxonibm/com.ibm.linux.z.wskc.doc/wskc_c_appdpvvgenalg.html

    The algorithm generates a 4-digit PIN verification value (PVV).

    :param tsp: tsp as hex string. See :py:mod:`cardutil.pin.tsp`
    :param pvv_key: the pvv key
    :return: pvv value
    """
    backend = default_backend()
    cipher = Cipher(algorithms.TripleDES(pvv_key), modes.ECB(), backend=backend)
    encryptor = cipher.encryptor()
    ct = encryptor.update(unhexlify(tsp)) + encryptor.finalize()
    values_pass1 = [value for value in hexlify(ct).decode() if value.isdigit()]
    if len(values_pass1) < 4:
        values_pass2 = [str(int(value, 16) - 10) for value in hexlify(ct).decode() if value.isalpha()]
        values_pass1 += values_pass2
    return ''.join(values_pass1[0:4])


def pin_block_0(pin: str, card_number: str):
    """
    Pin block in format 0::

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
    :return: pin block as hex string
    """
    rightmost_12 = card_number[-13:-1]
    p1 = f'{"0" + str(len(pin)) + pin:f<16}'
    p2 = f'0000{rightmost_12}'
    pin_block = int(p1, 16) ^ int(p2, 16)
    return f'{pin_block:016x}'
