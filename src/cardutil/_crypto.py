def normalize_tdes_key(binary_key: bytes) -> bytes:
    """
    Expand legacy single-key and double-length TDES keys to 24 bytes.

    cryptography warns on 8-byte and 16-byte inputs even though the equivalent
    24-byte form is well-defined for payment-card workflows.

    :param binary_key: the key bytes
    :return: normalized key bytes
    """
    key_length = len(binary_key)
    if key_length == 8:
        return binary_key * 3
    if key_length == 16:
        return binary_key + binary_key[:8]
    if key_length == 24:
        return binary_key
    raise ValueError("TDES keys must be 8, 16, or 24 bytes long")
