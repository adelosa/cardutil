import csv


def dicts_to_csv(data_list, field_list, output_file):
    """
    Writes dict data to CSV file

    :param data_list: list of dictionaries that contain the data to be loaded
    :param field_list: list of fields in the dictionary to be loaded
    :param output_file: output CSV file
    :return: None
    """
    filtered_data_list = filter_data_list(data_list, field_list)

    writer = csv.DictWriter(
        output_file,
        fieldnames=field_list,
        extrasaction="ignore",
        lineterminator="\n")

    writer.writeheader()
    for item in filtered_data_list:
        writer.writerow(item)


def filter_data_list(data_list, field_list):
    """
    Takes list of dictionaries and returns new list filtered to only
    return the field keys provided in field_list and the values
    decoded to unicode.

    :param data_list: the list of dictionaries
    :param field_list: the list of string keys to return
    :return: filtered data list
    """
    return [filter_dictionary(item, field_list) for item in data_list]


def filter_dictionary(dictionary, field_list):
    """
    Takes dictionary and list of elements and returns dictionary with just
    elements specified. Also decodes the items to unicode

    :param dictionary: the dictionary to filter
    :param field_list: list containing keys to keep
    :return: dictionary with just keys from list. All values decoded
    """
    return {item: dictionary[item] for item in dictionary if item in field_list}
