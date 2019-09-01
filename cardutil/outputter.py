import csv
import sys


def dicts_to_csv(data_list, field_list, output_file):
    """
    Writes dict data to CSV file

    :param data_list: list of dictionaries that contain the data to be loaded
    :param field_list: list of fields in the dictionary to be loaded
    :param output_filename: filename for output CSV file
    :return: None
    """
    try:
        instance_type = unicode
        file_mode = "wb"
    except NameError:
        instance_type = str
        file_mode = "w"

    filtered_data_list = filter_data_list(data_list, field_list)

    # with open(output_filename, file_mode) as output_file:
    writer = csv.DictWriter(
        output_file,
        fieldnames=field_list,
        extrasaction="ignore",
        lineterminator="\n")

    # python 2.6 does not support writeheader() so skip
    if sys.version_info[0] == 2 and sys.version_info[1] == 6:
        pass
    else:
        writer.writeheader()

    for item in filtered_data_list:
        if file_mode == "w":
            row = dict(
                (k, v.decode('latin1') if not isinstance(v, instance_type) else v)
                for k, v in item.items()
            )
        else:
            row = dict(
                (k, v.encode('utf-8') if isinstance(v, instance_type) else v)
                for k, v in item.items()
            )
        writer.writerow(row)

    # LOGGER.info("%s records written", len(data_list))


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
