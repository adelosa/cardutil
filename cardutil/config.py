"""
The config module contains the default configuration for the cardutil library.

The config consists of a single dictionary called `config` with a number of keys for different configuration data.

bit_config
==========

The iso8583 module functions require configuration that details how to process the bitmap in a message.

Field definitions in an ISO8583 message are generally the same but there can be variations you may need to cater for
with the different card schemes. The library supports provision of custom ISO8583 configuration.

If a configuration is not provided, the variable ``config['bit_config']`` in ``config.py`` provides a Mastercard
specific ISO8583 configuration.

The config is in the form of a python dictionary structured as follows

.. code-block:: json

    {
        "1": {
            "field_name": "Bitmap secondary",
            "field_type": "FIXED",
            "field_length": 8},
        "2": {
            "field_name": "PAN",
            "field_type": "LLVAR",
            "field_length": 0,
            "field_processor": "PAN",
            "field_processor_config": "",
            "field_python_type": "string",
            "field_date_format": "%y%m%d"}
    }

The config dictionary contains a string key for each valid bit in the bitmap.
For example, the config for bit 1 with have the key "1".

The value for the bit is a dictionary containing the following values:

field_name
    description of the bit field
field_type
    defines the ISO8583 field type
        * FIXED : field with fixed length
        * LLVAR : field with variable length - 2 character length value
        * LLLVAR : field with variable length - 2 character length value
field_length
    length of the field. Use zero for variable length fields.
field_processor
    (optional) a process to apply to a field.
        * ``PAN``: For use with PAN fields. Mask PAN using first 6, last 4 pattern
        * ``PAN-PREFIX``: For use with PAN fields. Only get first 9 PAN numbers -- prefix
        * ``ICC``: Mastercard ICC field. Adds TAGxxxx keys to output
        * ``PDS``: Mastercard PDS field. Processes PDSxxxx fields
        * ``DE43``: Mastercard Merchant details field. Adds DE43 sub fields DE43_*
field_processor_config
     (optional) Where a field processor requires extra config, it can be placed in this field.
     For DE43 processor:
        field should contain a regex to split the DE43 field up into components. The regex
        groups defined will be added to the returned dictionary. Use Python regex variation.

field_python_type
    (optional) When processing between iso and python, determines the python object type.
        * ``string``: default if no type provided
        * ``int``
        * ``decimal``: use if your field has decimal place
        * ``datetime``: use if your field is a date
field_date_format
     (optional) If your field python type is datetime, then you use this to specify
     the format of the date in the iso record.

     Use standard python datetime.strptime see `strftime() and strptime() Behaviour
     <https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior>`_.

     Default format is "%y%m%d"

output_data_elements
====================

This config defines the ISO elements that will be present in CSV file output. Is a list of the field keys

.. code-block:: json

    ["MTI", "DE2", "DE3", "DE4", "DE12", "DE14", "DE22", "DE23", "DE24", "DE25", "DE26"]


mci_parameter_tables
====================

Provides configuration required to extract IPM parameter extracts

.. code-block:: json

    {
        "IP0006T1": {
            "effective_timestamp": {"start": 1, "end": 10},
            "active_inactive_code": {"start": 7, "end": 8},
            "table_id": {"start": 8, "end": 11},
            "card_program_id": {"start": 11, "end": 14},
            "data_element_id": {"start": 14, "end": 17},
            "data_element_name": {"start": 17, "end": 74},
            "data_element_format": {"start": 74, "end": 77}
        },
        "IP0040T1": {}
    }

"""

config = {
    "bit_config": {
        "1": {"field_name": "Bitmap secondary", "field_type": "FIXED", "field_length": 8},
        "2": {"field_name": "PAN", "field_type": "LLVAR", "field_length": 0},  # "field_processor": "PAN"},
        "3": {"field_name": "Processing code", "field_type": "FIXED", "field_length": 6},
        "4": {"field_name": "Amount transaction", "field_type": "FIXED", "field_length": 12,
              "field_python_type": "long"},
        "5": {"field_name": "Amount, Reconciliation", "field_type": "FIXED", "field_length": 12,
              "field_python_type": "long"},
        "6": {"field_name": "Amount, Cardholder billing", "field_type": "FIXED", "field_length": 12,
              "field_python_type": "long"},
        "9": {"field_name": "Conversion rate, Reconciliation", "field_type": "FIXED", "field_length": 8,
              "field_python_type": "long"},
        "10": {"field_name": "Conversion rate, Cardholder billing", "field_type": "FIXED", "field_length": 8,
               "field_python_type": "long"},
        "12": {"field_name": "Date/Time local transaction", "field_type": "FIXED", "field_length": 12,
               "field_python_type": "datetime", "field_date_format": "%y%m%d%H%M%S"},
        "14": {"field_name": "Expiration date", "field_type": "FIXED", "field_length": 4},
        "22": {"field_name": "Point of service data code", "field_type": "FIXED", "field_length": 12},
        "23": {"field_name": "Card sequence number", "field_type": "FIXED", "field_length": 3},
        "24": {"field_name": "Function code", "field_type": "FIXED", "field_length": 3},
        "25": {"field_name": "Message reason code", "field_type": "FIXED", "field_length": 4},
        "26": {"field_name": "Card acceptor business code", "field_type": "FIXED", "field_length": 4,
               "field_python_type": "int"},
        "30": {"field_name": "Amounts, original", "field_type": "FIXED", "field_length": 24},
        "31": {"field_name": "Acquirer reference data", "field_type": "LLVAR", "field_length": 23},
        "32": {"field_name": "Acquiring institution ID code", "field_type": "LLVAR", "field_length": 0},
        "33": {"field_name": "Forwarding institution ID code", "field_type": "LLVAR", "field_length": 0},
        "37": {"field_name": "Retrieval reference number", "field_type": "FIXED", "field_length": 12},
        "38": {"field_name": "Approval code", "field_type": "FIXED", "field_length": 6},
        "40": {"field_name": "Service code", "field_type": "FIXED", "field_length": 3},
        "41": {"field_name": "Card acceptor terminal ID", "field_type": "FIXED", "field_length": 8},
        "42": {"field_name": "Card acceptor Id", "field_type": "FIXED", "field_length": 15},
        "43": {"field_name": "Card acceptor name/location", "field_type": "LLVAR", "field_length": 0,
               "field_processor": "DE43",
               "field_processor_config": r"(?P<DE43_NAME>.+?) *\\(?P<DE43_ADDRESS>.+?) *\\(?P<DE43_SUBURB>.+?) *\\"
                                         r"(?P<DE43_POSTCODE>.{10})(?P<DE43_STATE>.{3})(?P<DE43_COUNTRY>\S{3})$"},
        "48": {"field_name": "Additional data", "field_type": "LLLVAR", "field_length": 0, "field_processor": "PDS"},
        "49": {"field_name": "Currency code, Transaction", "field_type": "FIXED", "field_length": 3},
        "50": {"field_name": "Currency code, Reconciliation", "field_type": "FIXED", "field_length": 3},
        "51": {"field_name": "Currency code, Cardholder billing", "field_type": "FIXED", "field_length": 3},
        "54": {"field_name": "Amounts, additional", "field_type": "LLLVAR", "field_length": 0},
        "55": {"field_name": "ICC system related data", "field_type": "LLLVAR", "field_length": 255,
               "field_processor": "ICC"},
        "62": {"field_name": "Additional data 2", "field_type": "LLLVAR", "field_length": 0, "field_processor": "PDS"},
        "63": {"field_name": "Transaction lifecycle Id", "field_type": "LLLVAR", "field_length": 16},
        "71": {"field_name": "Message number", "field_type": "FIXED", "field_length": 8, "field_python_type": "int"},
        "72": {"field_name": "Data record", "field_type": "LLLVAR", "field_length": 0},
        "73": {"field_name": "Date, Action", "field_type": "FIXED", "field_length": 6},
        "93": {"field_name": "Transaction destination institution ID", "field_type": "LLVAR", "field_length": 0},
        "94": {"field_name": "Transaction originator institution ID", "field_type": "LLVAR", "field_length": 0},
        "95": {"field_name": "Card issuer reference data", "field_type": "LLVAR", "field_length": 10},
        "100": {"field_name": "Receiving institution ID", "field_type": "LLVAR", "field_length": 11},
        "111": {"field_name": "Amount, currency conversion assignment", "field_type": "LLLVAR", "field_length": 0},
        "123": {"field_name": "Additional data 3", "field_type": "LLLVAR", "field_length": 0, "field_processor": "PDS"},
        "124": {"field_name": "Additional data 4", "field_type": "LLLVAR", "field_length": 0, "field_processor": "PDS"},
        "125": {"field_name": "Additional data 5", "field_type": "LLLVAR", "field_length": 0, "field_processor": "PDS"},
        "127": {"field_name": "Network data", "field_type": "LLLVAR", "field_length": 0}},

    "output_data_elements": [
        "MTI", "DE2", "DE3", "DE4", "DE12", "DE14", "DE22", "DE23", "DE24", "DE25", "DE26",
        "DE30", "DE31", "DE33", "DE37", "DE38", "DE40", "DE41", "DE42", "DE48", "DE49",
        "DE50", "DE63", "DE71", "DE73", "DE93", "DE94", "DE95", "DE100", "PDS0023",
        "PDS0052", "PDS0122", "PDS0148", "PDS0158", "PDS0165", "DE43_NAME", "DE43_SUBURB",
        "DE43_POSTCODE", "ICC_DATA"
    ],
    "mci_parameter_tables": {
        "IP0006T1": {
            "effective_timestamp": {"start": 1, "end": 10},
            "active_inactive_code": {"start": 7, "end": 8},
            "table_id": {"start": 8, "end": 11},
            "card_program_id": {"start": 11, "end": 14},
            "data_element_id": {"start": 14, "end": 17},
            "data_element_name": {"start": 17, "end": 74},
            "data_element_format": {"start": 74, "end": 77}
        },
        "IP0040T1": {
            "effective_timestamp": {"start": 1, "end": 7},
            "active_inactive_code": {"start": 7, "end": 8},
            "table_id": {"start": 8, "end": 11},
            "low_range": {"start": 11, "end": 30},
            "gcms_product": {"start": 30, "end": 33},
            "high_range": {"start": 33, "end": 52},
            "card_program_identifier": {"start": 52, "end": 55},
            "card_program_priority": {"start": 55, "end": 57},
            "member_id": {"start": 57, "end": 68},
            "product_type": {"start": 68, "end": 69},
            "endpoint": {"start": 69, "end": 76},
            "card_country_alpha": {"start": 76, "end": 79},
            "card_country_numeric": {"start": 79, "end": 82},
            "card_region": {"start": 82, "end": 83},
            "product_class": {"start": 83, "end": 86},
            "tran_routing_ind": {"start": 86, "end": 87},
            "first_present_reassign_ind": {"start": 87, "end": 88},
            "product_reassign_switch": {"start": 88, "end": 89},
            "pwcb_optin_switch": {"start": 89, "end": 90},
            "licenced_product_id": {"start": 90, "end": 93},
            "mapping_service_ind": {"start": 93, "end": 94},
            "alm_participation_ind": {"start": 94, "end": 95},
            "alm_activation_date": {"start": 95, "end": 101},
            "cardholder_billing_currency_default": {"start": 101, "end": 104},
            "cardholder_billing_currency_default_exponent": {"start": 104, "end": 105},
            "cardholder_bill_primary_currency": {"start": 105, "end": 133},
            "chip_to_magstripe_conversion_service_indicator": {"start": 133, "end": 134},
            "floor_exp_date": {"start": 134, "end": 140},
            "co_brand_participation_switch": {"start": 140, "end": 141},
            "spend_control_switch": {"start": 141, "end": 142},
            "merchant_cleansing_service_participation": {"start": 142, "end": 145},
            "merchant_cleansing_activation_date": {"start": 145, "end": 151},
            "paypass_enabled_indicator": {"start": 151, "end": 152},
            "rate_type_indicator": {"start": 152, "end": 153},
            "psn_route_indicator": {"start": 153, "end": 154},
            "cash_back_wo_purchase_ind": {"start": 154, "end": 155}
        },
        "IP0075T1": {
            "mcc_code": {"start": 12, "end": 16},
            "cab_code": {"start": 16, "end": 20}
        }
    }
}
