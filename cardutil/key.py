from binascii import unhexlify, hexlify
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

backend = default_backend()


def get_zone_master_key(*key_parts: str) -> (str, str):
    """
    combine keys components to get clear key

    :param key_parts: list of keys components to be combined
    :return: clear key, key check value
    """
    p1 = '00' * 16
    for key_part in key_parts:
        p1 = f'{int(p1, 16) ^ int(key_part, 16):032x}'
    binary_key = unhexlify(p1)
    kcv = calculate_kcv(binary_key)

    return p1, kcv


def get_enc_zone_master_key(master_key: str, *key_parts: str) -> (str, str):
    plain_key, kcv = get_zone_master_key(*key_parts)
    enc_key = encrypt_key(plain_key, master_key)
    return hexlify(enc_key).decode(), kcv


def calculate_kcv(binary_key: bytes) -> str:
    """
    Calculate key check value for given key

    :param binary_key: the key bytes
    :return: key check value
    """
    cipher = Cipher(algorithms.TripleDES(binary_key), modes.ECB(), backend=backend)
    encryptor = cipher.encryptor()
    ct = encryptor.update(b'\x00' * 16) + encryptor.finalize()
    return hexlify(ct)[0:6].decode()


def encrypt_key(key_to_encrypt: str, master_key: str) -> str:
    binary_key = unhexlify(master_key)
    binary_data = unhexlify(key_to_encrypt)
    # cipher = Cipher(algorithms.TripleDES(binary_key), modes.CBC(unhexlify('00' * 8)), backend=backend)
    cipher = Cipher(algorithms.TripleDES(binary_key), modes.ECB(), backend=backend)
    encryptor = cipher.encryptor()
    return encryptor.update(binary_data) + encryptor.finalize()


def load_remote_key(enc_key_zmk, enc_key_lmk):
    pass


if __name__ == '__main__':
    k1 = '6D6BE51F04F76167491554FE25F7ABEF'
    k2 = '67499B2CF137DFCB9EA28FF757CD10A7'
    master_key = '00' * 16
    enc_key, kcv = get_enc_zone_master_key(master_key, k1, k2)

    print(enc_key)
    print(kcv)

    print(calculate_kcv(unhexlify('67C4A7191ADAFD086432CE0DD6384AB8')))
