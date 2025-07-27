"""
Provides services related to card numbers.

* check digits
* masking

"""
from itertools import cycle


def calculate_check_digit(card_number: str) -> str:
    """
    calculate luhn 10 check digit.

    :param card_number: number to calculate check digit for excluding check digit.
    :return: check digit value
    """
    digits = [int(digit) for digit in card_number if digit.isdigit()]  # change string to list of integers
    total = sum([sum(divmod(multiplier * digit, 10)) for digit, multiplier in zip(digits[::-1], cycle([2, 1]))])
    return str((total * 9) % 10)


def validate_check_digit(card_number: str) -> str:
    """
    validate luhn 10 check digit

    :param card_number: number with check digit
    :return: None
    :raises AssertionError: Check digit is not valid
    """
    assert calculate_check_digit(card_number[0:-1]) == card_number[-1]


def add_check_digit(card_number: str) -> str:
    """
    adds luhn 10 check digit

    :param card_number: number to add check digit for
    :return: number with check digit
    """
    return card_number + calculate_check_digit(card_number)


def mask(card_number: str, mask_char: str = '*') -> str:
    """
    returns a masked version of a card number
    Format is First 6, last 4 digits.

    :param card_number: the card number to mask
    :param mask_char: the character to use in masking
    :return: masked card number
    """
    return card_number[0:6] + mask_char * (len(card_number)-10) + card_number[-4:]
