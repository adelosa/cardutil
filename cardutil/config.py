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

Provides configuration required to extract IPM parameter extracts.

Expanded file format should be used - not compressed.
The effective timestamp, table_id and active inactive code should not
be included here - they are automatically included in the extract.

.. code-block:: json

    {
        "IP0006T1": {
            "card_program_id": {"start": 19, "end": 22},
            "data_element_id": {"start": 22, "end": 25},
            "data_element_name": {"start": 25, "end": 82},
            "data_element_format": {"start": 82, "end": 85}
        },
        "IP0040T1": {}
    }

"""

config = {
    "bit_config": {
        "1": {
            "field_name": "Bitmap secondary",
            "field_type": "FIXED",
            "field_length": 8,
        },
        "2": {
            "field_name": "PAN",
            "field_type": "LLVAR",
            "field_length": 0,
        },  # "field_processor": "PAN"},
        "3": {
            "field_name": "Processing code",
            "field_type": "FIXED",
            "field_length": 6,
        },
        "4": {
            "field_name": "Amount transaction",
            "field_type": "FIXED",
            "field_length": 12,
            "field_python_type": "long",
        },
        "5": {
            "field_name": "Amount, Reconciliation",
            "field_type": "FIXED",
            "field_length": 12,
            "field_python_type": "long",
        },
        "6": {
            "field_name": "Amount, Cardholder billing",
            "field_type": "FIXED",
            "field_length": 12,
            "field_python_type": "long",
        },
        "9": {
            "field_name": "Conversion rate, Reconciliation",
            "field_type": "FIXED",
            "field_length": 8,
            "field_python_type": "long",
        },
        "10": {
            "field_name": "Conversion rate, Cardholder billing",
            "field_type": "FIXED",
            "field_length": 8,
            "field_python_type": "long",
        },
        "12": {
            "field_name": "Date/Time local transaction",
            "field_type": "FIXED",
            "field_length": 12,
            "field_python_type": "datetime",
            "field_date_format": "%y%m%d%H%M%S",
        },
        "14": {
            "field_name": "Expiration date",
            "field_type": "FIXED",
            "field_length": 4,
        },
        "22": {
            "field_name": "Point of service data code",
            "field_type": "FIXED",
            "field_length": 12,
        },
        "23": {
            "field_name": "Card sequence number",
            "field_type": "FIXED",
            "field_length": 3,
        },
        "24": {"field_name": "Function code", "field_type": "FIXED", "field_length": 3},
        "25": {
            "field_name": "Message reason code",
            "field_type": "FIXED",
            "field_length": 4,
        },
        "26": {
            "field_name": "Card acceptor business code",
            "field_type": "FIXED",
            "field_length": 4,
            "field_python_type": "int",
        },
        "30": {
            "field_name": "Amounts, original",
            "field_type": "FIXED",
            "field_length": 24,
        },
        "31": {
            "field_name": "Acquirer reference data",
            "field_type": "LLVAR",
            "field_length": 23,
        },
        "32": {
            "field_name": "Acquiring institution ID code",
            "field_type": "LLVAR",
            "field_length": 0,
        },
        "33": {
            "field_name": "Forwarding institution ID code",
            "field_type": "LLVAR",
            "field_length": 0,
        },
        "37": {
            "field_name": "Retrieval reference number",
            "field_type": "FIXED",
            "field_length": 12,
        },
        "38": {"field_name": "Approval code", "field_type": "FIXED", "field_length": 6},
        "40": {"field_name": "Service code", "field_type": "FIXED", "field_length": 3},
        "41": {
            "field_name": "Card acceptor terminal ID",
            "field_type": "FIXED",
            "field_length": 8,
        },
        "42": {
            "field_name": "Card acceptor Id",
            "field_type": "FIXED",
            "field_length": 15,
        },
        "43": {
            "field_name": "Card acceptor name/location",
            "field_type": "LLVAR",
            "field_length": 0,
            "field_processor": "DE43",
            "field_processor_config": r"(?P<DE43_NAME>.+?) *\\(?P<DE43_ADDRESS>.+?) *\\(?P<DE43_SUBURB>.+?) *\\"
            r"(?P<DE43_POSTCODE>.{10})(?P<DE43_STATE>.{3})(?P<DE43_COUNTRY>\S{3})$",
        },
        "48": {
            "field_name": "Additional data",
            "field_type": "LLLVAR",
            "field_length": 0,
            "field_processor": "PDS",
        },
        "49": {
            "field_name": "Currency code, Transaction",
            "field_type": "FIXED",
            "field_length": 3,
        },
        "50": {
            "field_name": "Currency code, Reconciliation",
            "field_type": "FIXED",
            "field_length": 3,
        },
        "51": {
            "field_name": "Currency code, Cardholder billing",
            "field_type": "FIXED",
            "field_length": 3,
        },
        "54": {
            "field_name": "Amounts, additional",
            "field_type": "LLLVAR",
            "field_length": 0,
        },
        "55": {
            "field_name": "ICC system related data",
            "field_type": "LLLVAR",
            "field_length": 255,
            "field_processor": "ICC",
        },
        "62": {
            "field_name": "Additional data 2",
            "field_type": "LLLVAR",
            "field_length": 0,
            "field_processor": "PDS",
        },
        "63": {
            "field_name": "Transaction lifecycle Id",
            "field_type": "LLLVAR",
            "field_length": 16,
        },
        "71": {
            "field_name": "Message number",
            "field_type": "FIXED",
            "field_length": 8,
            "field_python_type": "int",
        },
        "72": {"field_name": "Data record", "field_type": "LLLVAR", "field_length": 0},
        "73": {"field_name": "Date, Action", "field_type": "FIXED", "field_length": 6},
        "93": {
            "field_name": "Transaction destination institution ID",
            "field_type": "LLVAR",
            "field_length": 0,
        },
        "94": {
            "field_name": "Transaction originator institution ID",
            "field_type": "LLVAR",
            "field_length": 0,
        },
        "95": {
            "field_name": "Card issuer reference data",
            "field_type": "LLVAR",
            "field_length": 10,
        },
        "100": {
            "field_name": "Receiving institution ID",
            "field_type": "LLVAR",
            "field_length": 11,
        },
        "111": {
            "field_name": "Amount, currency conversion assignment",
            "field_type": "LLLVAR",
            "field_length": 0,
        },
        "123": {
            "field_name": "Additional data 3",
            "field_type": "LLLVAR",
            "field_length": 0,
            "field_processor": "PDS",
        },
        "124": {
            "field_name": "Additional data 4",
            "field_type": "LLLVAR",
            "field_length": 0,
            "field_processor": "PDS",
        },
        "125": {
            "field_name": "Additional data 5",
            "field_type": "LLLVAR",
            "field_length": 0,
            "field_processor": "PDS",
        },
        "127": {
            "field_name": "Network data",
            "field_type": "LLLVAR",
            "field_length": 0,
        },
    },
    "output_data_elements": [
        "MTI",
        "DE2",
        "DE3",
        "DE4",
        "DE12",
        "DE14",
        "DE22",
        "DE23",
        "DE24",
        "DE25",
        "DE26",
        "DE30",
        "DE31",
        "DE33",
        "DE37",
        "DE38",
        "DE40",
        "DE41",
        "DE42",
        "DE48",
        "DE49",
        "DE50",
        "DE63",
        "DE71",
        "DE73",
        "DE93",
        "DE94",
        "DE95",
        "DE100",
        "PDS0023",
        "PDS0052",
        "PDS0122",
        "PDS0148",
        "PDS0158",
        "PDS0165",
        "DE43_NAME",
        "DE43_SUBURB",
        "DE43_POSTCODE",
        "ICC_DATA",
    ],
    "mci_parameter_tables": {
        "IP0006T1": {
            "card_program_id": {"start": 19, "end": 22},
            "data_element_id": {"start": 22, "end": 25},
            "data_element_name": {"start": 25, "end": 82},
            "data_element_format": {"start": 82, "end": 85},
            "data_element_minimum_length": {"start": 85, "end": 88},
            "data_element_mastercard_maximum_length": {"start": 88, "end": 91},
            "data_element_iso_maximum_length": {"start": 91, "end": 94},
            "de_lll_size": {"start": 94, "end": 95},
            "data_element_subfields": {"start": 95, "end": 97},
        },
        "IP0040T1": {
            "issuer_account_range_low": {"start": 19, "end": 38},
            "gcms_product_id": {"start": 38, "end": 41},
            "issuer_account_range_high": {"start": 41, "end": 60},
            "card_program_identifier": {"start": 60, "end": 63},
            "issuer_card_program_identifier_priority_code": {"start": 63, "end": 65},
            "member_id": {"start": 65, "end": 76},
            "product_type_id": {"start": 76, "end": 77},
            "endpoint": {"start": 77, "end": 84},
            "card_country_alpha": {"start": 84, "end": 87},
            "card_country_numeric": {"start": 87, "end": 90},
            "region": {"start": 90, "end": 91},
            "product_class": {"start": 91, "end": 94},
            "transaction_routing_indicator": {"start": 94, "end": 95},
            "first_presentment_reassignment_switch": {"start": 95, "end": 96},
            "product_reassignment_switch": {"start": 96, "end": 97},
            "pwcb_opt_in_switch": {"start": 97, "end": 98},
            "licenced_product_id": {"start": 98, "end": 101},
            "mapping_service_ind": {"start": 101, "end": 102},
            "alm_participation_ind": {"start": 102, "end": 103},
            "alm_activation_date": {"start": 103, "end": 109},
            "cardholder_billing_currency_default": {"start": 109, "end": 112},
            "cardholder_billing_currency_exponent_default": {"start": 112, "end": 113},
            "cardholder_bill_primary_currency": {"start": 113, "end": 141},
            "chip_to_magnetic_conversion_service_indicator": {"start": 141, "end": 142},
            "floor_expiration_date": {"start": 142, "end": 148},
            "co_brand_participation_switch": {"start": 148, "end": 149},
            "spend_control_switch": {"start": 149, "end": 150},
            "merchant_cleansing_service_participation": {"start": 150, "end": 153},
            "merchant_cleansing_activation_date": {"start": 153, "end": 159},
            "paypass_enabled_indicator": {"start": 159, "end": 160},
            "regulated_rate_type_indicator": {"start": 160, "end": 161},
            "psn_route_indicator": {"start": 161, "end": 162},
            "cash_back_without_purchase_indicator": {"start": 162, "end": 163},
            "repower_reload_participation_indicator": {"start": 164, "end": 165},
            "moneysend_indicator": {"start": 165, "end": 166},
            "durban_regulated_rate_indicator": {"start": 166, "end": 167},
            "cash_access_only_participating_indicator": {"start": 167, "end": 168},
            "authentication_indicator": {"start": 168, "end": 169},
        },
        "IP0075T1": {
            "card_acceptor_business_code_mcc": {"start": 19, "end": 24},
            "card_acceptor_business_cab_program": {"start": 24, "end": 28},
            "card_acceptor_business_cab_program_life_cycle_indicator": {
                "start": 28,
                "end": 29,
            },
            "card_acceptor_business_cab_type": {"start": 29, "end": 30},
            "card_acceptor_business_cab_life_cycle_indicator": {"start": 30, "end": 31},
        },
        "IP0095T1": {
            "card_program_identifier": {"start": 19, "end": 22},
            "business_service_arrangement_type": {"start": 22, "end": 23},
            "business_service_id_code": {"start": 23, "end": 29},
            "interchange_rate_designator_ird": {"start": 29, "end": 31},
            "card_acceptor_business_cab_program": {"start": 31, "end": 35},
            "life_cycle_indicator": {"start": 35, "end": 36},
        },
    },
}
